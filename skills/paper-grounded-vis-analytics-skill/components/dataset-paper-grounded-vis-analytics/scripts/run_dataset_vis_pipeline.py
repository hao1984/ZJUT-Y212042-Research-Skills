#!/usr/bin/env python3
"""Dataset-first paper-grounded VIS analytics pipeline.

This runner loads a real tabular dataset, profiles and mines it, retrieves
local VIS paper references from the paper-mineru-scholar-index corpus, and
builds a runnable static coordinated visual analytics frontend.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


MISSING = {"", "na", "n/a", "nan", "null", "none", "missing", "undefined"}
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "data", "dataset", "table",
    "field", "value", "values", "record", "records", "analysis", "visual", "system",
    "chart", "plot", "overview", "summary", "user", "users",
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact(text: Any, limit: int = 160) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def slugify(value: str, fallback: str = "run") -> str:
    value = re.sub(r"[^\w\s.-]+", "", value or "", flags=re.UNICODE).strip().lower()
    value = re.sub(r"[\s_]+", "-", value)
    return value[:80].strip("-") or fallback


def clean_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in MISSING:
            return None
        return stripped
    return value


def to_float(value: Any) -> float | None:
    value = clean_cell(value)
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", ""))
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def parse_rows(dataset_path: Path, max_rows: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    suffix = dataset_path.suffix.lower()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset does not exist: {dataset_path}")
    if dataset_path.is_dir():
        candidates = []
        for pattern in ("*.csv", "*.tsv", "*.jsonl", "*.json"):
            candidates.extend(dataset_path.glob(pattern))
        if not candidates:
            raise ValueError(f"Dataset directory has no supported tabular files: {dataset_path}")
        dataset_path = sorted(candidates, key=lambda p: p.stat().st_size, reverse=True)[0]
        suffix = dataset_path.suffix.lower()

    rows: list[dict[str, Any]] = []
    meta = {
        "path": str(dataset_path.resolve()),
        "format": suffix.lstrip(".") or "unknown",
        "loaded_row_limit": max_rows,
        "truncated": False,
        "file_size_mb": round(dataset_path.stat().st_size / (1024 * 1024), 4),
    }

    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            for index, row in enumerate(reader):
                if index >= max_rows:
                    meta["truncated"] = True
                    break
                rows.append({str(k): clean_cell(v) for k, v in row.items() if k is not None})
    elif suffix == ".jsonl":
        with dataset_path.open("r", encoding="utf-8-sig") as handle:
            for index, line in enumerate(handle):
                if index >= max_rows:
                    meta["truncated"] = True
                    break
                if not line.strip():
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append({str(k): clean_cell(v) for k, v in obj.items()})
    elif suffix == ".json":
        obj = json.loads(dataset_path.read_text(encoding="utf-8-sig"))
        if isinstance(obj, dict):
            for key in ("rows", "data", "records", "items"):
                if isinstance(obj.get(key), list):
                    obj = obj[key]
                    break
        if not isinstance(obj, list):
            raise ValueError("JSON dataset must be a list or a dict containing rows/data/records/items.")
        for index, item in enumerate(obj):
            if index >= max_rows:
                meta["truncated"] = True
                break
            if isinstance(item, dict):
                rows.append({str(k): clean_cell(v) for k, v in item.items()})
    else:
        raise ValueError(f"Unsupported dataset format: {suffix}. Use CSV, TSV, JSON, or JSONL.")

    if not rows:
        raise ValueError("Dataset loaded but contains no rows.")
    return rows, meta


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return values[lo]
    return values[lo] * (hi - pos) + values[hi] * (pos - lo)


def infer_columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_columns = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                all_columns.append(key)
    columns = []
    row_count = len(rows)
    for name in all_columns:
        raw_values = [clean_cell(row.get(name)) for row in rows]
        non_null = [v for v in raw_values if v is not None]
        numbers = [num for v in non_null if (num := to_float(v)) is not None]
        distinct_values = Counter(str(v) for v in non_null)
        distinct_count = len(distinct_values)
        numeric_ratio = len(numbers) / max(1, len(non_null))
        name_lower = name.lower()
        is_id_like = ("id" in name_lower or name_lower.endswith("code")) and distinct_count >= max(8, row_count * 0.55)
        if is_id_like:
            kind = "id"
        elif numeric_ratio >= 0.86 and len(numbers) >= max(3, len(non_null) * 0.5):
            if any(token in name_lower for token in ("year", "date", "time")) and distinct_count <= max(30, row_count * 0.2):
                kind = "temporal"
            else:
                kind = "numeric"
        elif distinct_count <= min(60, max(8, row_count * 0.35)):
            kind = "categorical"
        elif any(token in name_lower for token in ("date", "time")):
            kind = "temporal"
        else:
            kind = "text"

        column: dict[str, Any] = {
            "name": name,
            "type": kind,
            "non_null_count": len(non_null),
            "missing_count": row_count - len(non_null),
            "missing_rate": round((row_count - len(non_null)) / max(1, row_count), 4),
            "distinct_count": distinct_count,
            "sample_values": [v for v, _ in distinct_values.most_common(6)],
        }
        if numbers:
            q1 = quantile(numbers, 0.25)
            q2 = quantile(numbers, 0.5)
            q3 = quantile(numbers, 0.75)
            iqr = (q3 - q1) if q1 is not None and q3 is not None else 0
            outliers = 0
            if iqr:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = sum(1 for v in numbers if v < lower or v > upper)
            column["numeric_stats"] = {
                "min": round(min(numbers), 6),
                "max": round(max(numbers), 6),
                "mean": round(statistics.fmean(numbers), 6),
                "median": round(q2 or 0, 6),
                "q1": round(q1 or 0, 6),
                "q3": round(q3 or 0, 6),
                "outlier_count_iqr": outliers,
            }
        if kind in {"categorical", "text", "id", "temporal"}:
            column["top_values"] = [{"value": k, "count": v} for k, v in distinct_values.most_common(12)]
        columns.append(column)
    return columns


def numeric_fields(columns: list[dict[str, Any]]) -> list[str]:
    fields = [c["name"] for c in columns if c["type"] == "numeric" and c.get("distinct_count", 0) > 5]
    if len(fields) < 2:
        fields.extend(c["name"] for c in columns if c["type"] == "numeric" and c["name"] not in fields)
    return fields


def categorical_fields(columns: list[dict[str, Any]]) -> list[str]:
    fields = [c["name"] for c in columns if c["type"] == "categorical" and 1 < c.get("distinct_count", 0) <= 60]
    if not fields:
        fields = [c["name"] for c in columns if c["type"] in {"text", "temporal"} and 1 < c.get("distinct_count", 0) <= 80]
    return fields


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    if denom == 0:
        return None
    return sum(x * y for x, y in zip(dx, dy)) / denom


def group_numeric_contrast(rows: list[dict[str, Any]], cat: str, num: str) -> dict[str, Any] | None:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        key = row.get(cat)
        val = to_float(row.get(num))
        if key is not None and val is not None:
            groups[str(key)].append(val)
    groups = {k: v for k, v in groups.items() if len(v) >= 2}
    if len(groups) < 2:
        return None
    means = {k: statistics.fmean(v) for k, v in groups.items()}
    high = max(means, key=means.get)
    low = min(means, key=means.get)
    span = means[high] - means[low]
    if span <= 0:
        return None
    return {
        "cat": cat,
        "num": num,
        "high_group": high,
        "low_group": low,
        "high_mean": round(means[high], 4),
        "low_mean": round(means[low], 4),
        "span": round(span, 4),
        "group_count": len(groups),
    }


def category_relation(rows: list[dict[str, Any]], a: str, b: str) -> dict[str, Any] | None:
    counts: Counter[tuple[str, str]] = Counter()
    total = 0
    for row in rows:
        va = row.get(a)
        vb = row.get(b)
        if va is None or vb is None:
            continue
        counts[(str(va), str(vb))] += 1
        total += 1
    if total == 0 or len(counts) < 2:
        return None
    top_pair, top_count = counts.most_common(1)[0]
    return {
        "field_a": a,
        "field_b": b,
        "pair_count": len(counts),
        "top_pair": list(top_pair),
        "top_pair_count": top_count,
        "coverage": round(top_count / max(1, total), 4),
    }


def mine_patterns(rows: list[dict[str, Any]], columns: list[dict[str, Any]]) -> dict[str, Any]:
    nums = numeric_fields(columns)
    cats = categorical_fields(columns)
    patterns: list[dict[str, Any]] = []

    best_contrast = None
    for cat in cats[:6]:
        for num in nums[:8]:
            contrast = group_numeric_contrast(rows, cat, num)
            if contrast and (best_contrast is None or contrast["span"] > best_contrast["span"]):
                best_contrast = contrast
    if best_contrast:
        patterns.append(
            {
                "pattern_id": "p_subgroup_numeric_contrast",
                "type": "subgroup_contrast",
                "title": f"{best_contrast['cat']} separates {best_contrast['num']} into visibly different groups",
                "fields": [best_contrast["cat"], best_contrast["num"]],
                "is_data_specific": True,
                "is_multidimensional_coupling": len(nums) >= 2,
                "evidence": best_contrast,
                "visual_implication": "Use linked row-level marks plus subgroup distribution/evidence views.",
            }
        )

    best_corr = None
    for i, a in enumerate(nums[:8]):
        for b in nums[i + 1 : 8]:
            xs, ys = [], []
            for row in rows:
                x = to_float(row.get(a))
                y = to_float(row.get(b))
                if x is not None and y is not None:
                    xs.append(x)
                    ys.append(y)
            r = pearson(xs, ys)
            if r is not None and (best_corr is None or abs(r) > abs(best_corr["r"])):
                best_corr = {"field_x": a, "field_y": b, "r": r, "n": len(xs)}
    if best_corr:
        patterns.append(
            {
                "pattern_id": "p_numeric_coupling",
                "type": "multivariate_coupling",
                "title": f"{best_corr['field_x']} and {best_corr['field_y']} form the strongest numeric coupling",
                "fields": [best_corr["field_x"], best_corr["field_y"]],
                "is_data_specific": abs(best_corr["r"]) >= 0.35,
                "is_multidimensional_coupling": bool(cats),
                "evidence": {"pearson_r": round(best_corr["r"], 4), "paired_rows": best_corr["n"]},
                "visual_implication": "Use these fields as the primary row-level projection axes.",
            }
        )

    outlier_candidates = []
    for col in columns:
        stats = col.get("numeric_stats")
        if stats and stats.get("outlier_count_iqr", 0) > 0:
            outlier_candidates.append((col["name"], stats["outlier_count_iqr"], stats))
    if outlier_candidates:
        field, count, stats = sorted(outlier_candidates, key=lambda item: item[1], reverse=True)[0]
        patterns.append(
            {
                "pattern_id": "p_outlier_boundary_cases",
                "type": "boundary_cases",
                "title": f"{field} contains boundary cases that need row-level evidence",
                "fields": [field],
                "is_data_specific": True,
                "is_multidimensional_coupling": False,
                "evidence": {"outlier_count_iqr": count, "stats": stats},
                "visual_implication": "Keep outlier records selectable and connected to raw row evidence.",
            }
        )

    if len(cats) >= 2:
        relation = category_relation(rows, cats[0], cats[1])
        if relation:
            patterns.append(
                {
                    "pattern_id": "p_categorical_relation_structure",
                    "type": "categorical_relation",
                    "title": f"{relation['field_a']} x {relation['field_b']} forms a relation structure with {relation['pair_count']} observed cells",
                    "fields": [relation["field_a"], relation["field_b"]],
                    "is_data_specific": True,
                    "is_multidimensional_coupling": True,
                    "evidence": relation,
                    "visual_implication": "Use a relation matrix or category lattice when numeric axes are not central.",
                }
            )

    if not patterns and cats:
        top_col = next(c for c in columns if c["name"] == cats[0])
        patterns.append(
            {
                "pattern_id": "p_category_composition",
                "type": "composition",
                "title": f"{cats[0]} composition provides the strongest available analysis object",
                "fields": [cats[0]],
                "is_data_specific": False,
                "is_multidimensional_coupling": False,
                "evidence": {"top_values": top_col.get("top_values", [])[:8]},
                "visual_implication": "Use composition only as context; preserve raw row evidence.",
            }
        )

    candidate_rqs = build_candidate_rqs(patterns, nums, cats)
    return {
        "schema_version": "dataset_patterns_v0.1",
        "patterns": patterns,
        "candidate_research_questions": candidate_rqs,
        "pattern_graph": build_pattern_graph(patterns),
    }


def build_candidate_rqs(patterns: list[dict[str, Any]], nums: list[str], cats: list[str]) -> list[dict[str, Any]]:
    rqs = []
    for index, pattern in enumerate(patterns[:5], start=1):
        fields = pattern.get("fields") or []
        if pattern["type"] == "multivariate_coupling" and len(fields) >= 2:
            question = f"How do records move through the {fields[0]} x {fields[1]} structure, and which subgroup or boundary cases explain the visible shape?"
            roles = ["row_projection", "subgroup_context", "record_evidence"]
        elif pattern["type"] == "subgroup_contrast":
            question = f"How does {fields[0]} condition the distribution of {fields[1]}, and which records explain the strongest subgroup separation?"
            roles = ["subgroup_distribution", "row_projection", "record_evidence"]
        elif pattern["type"] == "categorical_relation":
            question = f"Which observed {fields[0]} x {fields[1]} relation cells dominate or disappear, and what row evidence explains those category structures?"
            roles = ["relation_matrix", "category_list", "record_evidence"]
        elif pattern["type"] == "boundary_cases":
            question = f"Which records sit at the boundary of {fields[0]}, and how do their companion fields explain why they are exceptional?"
            roles = ["boundary_strip", "field_context", "record_evidence"]
        else:
            question = f"How can analysts explore the structure around {', '.join(fields) or 'the loaded records'} without collapsing it into a dashboard?"
            roles = ["overview", "context", "record_evidence"]
        rqs.append(
            {
                "rq_id": f"rq{index}",
                "question": question,
                "supporting_patterns": [pattern["pattern_id"]],
                "anti_dashboard_check": {
                    "passes_check": True,
                    "why_not_dashboard": "The question needs a selectable analysis object, linked context, and row-level evidence rather than independent summary charts.",
                },
                "expected_view_roles": roles,
                "expected_shared_state": ["selected_record", "selected_category", "selected_pattern", "selected_reference"],
                "vis_direction_hint": "coordinated multi-view workspace with row/aggregate marks, linked brushing, and evidence panel",
            }
        )
    return rqs


def build_pattern_graph(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {
            "pattern_id": p["pattern_id"],
            "grain": "row" if p["type"] in {"multivariate_coupling", "boundary_cases"} else "group",
            "type": p["type"],
        }
        for p in patterns
    ]
    edges = []
    for a in patterns:
        for b in patterns:
            if a["pattern_id"] >= b["pattern_id"]:
                continue
            shared = sorted(set(a.get("fields") or []) & set(b.get("fields") or []))
            if shared:
                edges.append(
                    {
                        "source": a["pattern_id"],
                        "target": b["pattern_id"],
                        "relationship": "shares_state",
                        "shared_fields": shared,
                    }
                )
    return {"nodes": nodes, "edges": edges}


def profile_dataset(dataset_path: Path, description: str, max_rows: int) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    rows, load_meta = parse_rows(dataset_path, max_rows)
    columns = infer_columns(rows)
    profile = {
        "schema_version": "dataset_profile_v0.1",
        "created_at": now_iso(),
        "meta": {
            **load_meta,
            "row_count_loaded": len(rows),
            "column_count": len(columns),
            "description": description,
        },
        "columns": columns,
        "field_roles": {
            "numeric": numeric_fields(columns),
            "categorical": categorical_fields(columns),
            "temporal": [c["name"] for c in columns if c["type"] == "temporal"],
            "text": [c["name"] for c in columns if c["type"] == "text"],
            "id": [c["name"] for c in columns if c["type"] == "id"],
        },
        "sample_rows": rows[:10],
    }
    patterns = mine_patterns(rows, columns)
    return rows, profile, patterns


def tokenize_query(text: str) -> list[str]:
    terms = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower()):
        token = token.replace("_", " ").replace("-", " ").strip()
        for part in token.split():
            if len(part) >= 3 and part not in STOPWORDS:
                terms.append(part)
    seen = set()
    output = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            output.append(term)
    return output


def search_papers(db_path: Path, query_terms: list[str], top_k: int) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    terms = [re.sub(r"[^A-Za-z0-9]+", "", term) for term in query_terms if len(term) >= 3]
    terms = [term for term in terms if term]
    if not terms:
        terms = ["visual", "analytics"]
    rows = []
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        query = " OR ".join(terms[:12])
        try:
            sql = """
                SELECT paper_id, title, year, journal, abstract, conclusion, md_path,
                       bm25(papers) AS rank_score
                FROM papers
                WHERE papers MATCH ?
                ORDER BY rank_score
                LIMIT ?
            """
            rows = [dict(row) for row in conn.execute(sql, (query, top_k)).fetchall()]
        except sqlite3.Error:
            like_terms = terms[:5]
            where = " OR ".join(["title LIKE ? OR abstract LIKE ? OR conclusion LIKE ?" for _ in like_terms])
            params = []
            for term in like_terms:
                params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
            sql = f"SELECT paper_id, title, year, journal, abstract, conclusion, md_path FROM papers WHERE {where} LIMIT ?"
            rows = [dict(row) for row in conn.execute(sql, (*params, top_k)).fetchall()]
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
        row["score"] = round(1 / idx, 6)
    return rows


def infer_borrowed_elements(row: dict[str, Any], profile: dict[str, Any], patterns: dict[str, Any]) -> list[dict[str, Any]]:
    nums = profile["field_roles"]["numeric"]
    cats = profile["field_roles"]["categorical"]
    ptypes = {p["type"] for p in patterns.get("patterns", [])}
    text = " ".join([str(row.get("title") or ""), str(row.get("abstract") or ""), str(row.get("conclusion") or "")]).lower()
    elements = []
    if len(nums) >= 2:
        elements.append(
            {
                "source_paper_id": row.get("paper_id"),
                "source_title": row.get("title"),
                "borrowed_element": "linked row-level projection with companion evidence views",
                "adapted_for_current_data": f"Use {nums[0]} and {nums[1]} as real-data axes and keep selected rows linked to details.",
                "mapped_to_view_ids": ["primary_data_view", "field_context_view", "evidence_panel"],
                "mapped_to_interaction_ids": ["select_mark_updates_evidence", "filter_category_updates_marks"],
                "confidence": "medium" if "scatter" in text or "projection" in text or "visual analytics" in text else "fallback_from_data_shape",
            }
        )
    if len(cats) >= 2 or "matrix" in text or "graph" in text:
        elements.append(
            {
                "source_paper_id": row.get("paper_id"),
                "source_title": row.get("title"),
                "borrowed_element": "relation matrix or category lattice for exposing subgroup structure",
                "adapted_for_current_data": f"Use real {cats[0] if cats else 'category'} relations as a companion or primary categorical view.",
                "mapped_to_view_ids": ["primary_data_view", "field_context_view"],
                "mapped_to_interaction_ids": ["select_category_updates_marks"],
                "confidence": "medium",
            }
        )
    if "boundary_cases" in ptypes or "outlier" in text or "uncertainty" in text:
        elements.append(
            {
                "source_paper_id": row.get("paper_id"),
                "source_title": row.get("title"),
                "borrowed_element": "bounded evidence panel for outliers, caveats, and source records",
                "adapted_for_current_data": "Expose the selected record, source fields, and pattern evidence without turning the system into KPI cards.",
                "mapped_to_view_ids": ["evidence_panel"],
                "mapped_to_interaction_ids": ["select_mark_updates_evidence"],
                "confidence": "high",
            }
        )
    if not elements:
        elements.append(
            {
                "source_paper_id": row.get("paper_id"),
                "source_title": row.get("title"),
                "borrowed_element": "overview-detail linked interaction with visible provenance",
                "adapted_for_current_data": "Use the paper as a general precedent for coordinated evidence flow.",
                "mapped_to_view_ids": ["primary_data_view", "evidence_panel"],
                "mapped_to_interaction_ids": ["select_mark_updates_evidence"],
                "confidence": "fallback",
            }
        )
    return elements


def retrieve_reference_digest(db_path: Path, papers_dir: Path, profile: dict[str, Any], patterns: dict[str, Any], description: str, top_k: int) -> dict[str, Any]:
    pattern_text = " ".join(p.get("title", "") + " " + " ".join(p.get("fields", [])) for p in patterns.get("patterns", []))
    field_text = " ".join(c["name"] for c in profile.get("columns", []))
    query_terms = tokenize_query(f"{description} {field_text} {pattern_text} visual analytics coordinated views linked brushing matrix scatterplot evidence")
    rows = search_papers(db_path, query_terms, top_k)
    selected = []
    for row in rows:
        md_path = row.get("md_path")
        if md_path and not Path(str(md_path)).is_absolute():
            md_path = str((papers_dir.parent / md_path).resolve())
        selected.append(
            {
                "rank": row.get("rank"),
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year": row.get("year"),
                "journal": row.get("journal"),
                "score": row.get("score"),
                "abstract_snippet": compact(row.get("abstract"), 420),
                "l3_snippet": compact(row.get("conclusion"), 420),
                "paper_md_path": md_path,
                "borrowed_elements": infer_borrowed_elements(row, profile, patterns),
            }
        )
    return {
        "schema_version": "dataset_paper_reference_digest_v0.1",
        "retrieval_status": "ok" if selected else "fallback_standard_basis",
        "retrieval_mode": "index_db_keyword",
        "query_terms": query_terms[:24],
        "selected_references": selected,
        "coverage_summary": {
            "selected_reference_count": len(selected),
            "applied_paper_count": sum(1 for ref in selected if ref.get("borrowed_elements")),
            "silent_reference_count": 0,
        },
    }


def choose_design(profile: dict[str, Any], patterns: dict[str, Any], digest: dict[str, Any]) -> dict[str, Any]:
    nums = profile["field_roles"]["numeric"]
    cats = profile["field_roles"]["categorical"]
    patterns_list = patterns.get("patterns", [])
    candidate_rqs = patterns.get("candidate_research_questions") or [{}]
    selected_rq = next((rq for rq in candidate_rqs if "p_numeric_coupling" in (rq.get("supporting_patterns") or [])), candidate_rqs[0])
    numeric_coupling = next((p for p in patterns_list if p.get("pattern_id") == "p_numeric_coupling"), None)
    if len(nums) >= 2:
        primary_type = "scatter"
        if numeric_coupling and len(numeric_coupling.get("fields") or []) >= 2:
            x_field, y_field = numeric_coupling["fields"][:2]
        else:
            x_field, y_field = nums[0], nums[1]
        color_field = cats[0] if cats else None
        primary_object = f"row-level {x_field} x {y_field} structure"
    elif len(cats) >= 2:
        primary_type = "category_matrix"
        x_field, y_field = cats[0], cats[1]
        color_field = cats[0]
        primary_object = f"{x_field} x {y_field} category relation structure"
    elif nums:
        primary_type = "numeric_strip"
        x_field, y_field = nums[0], None
        color_field = cats[0] if cats else None
        primary_object = f"{x_field} boundary and distribution strip"
    else:
        primary_type = "record_lattice"
        x_field = cats[0] if cats else profile["columns"][0]["name"]
        y_field = cats[1] if len(cats) > 1 else None
        color_field = cats[0] if cats else None
        primary_object = "record/category evidence lattice"

    applied = []
    unused = []
    for ref in digest.get("selected_references", []):
        if ref.get("borrowed_elements") and len(applied) < 6:
            applied.extend(ref["borrowed_elements"][:2])
        else:
            unused.append(
                {
                    "paper_id": ref.get("paper_id"),
                    "title": ref.get("title"),
                    "reason_not_used": "No concrete borrowed element matched the selected data field structure.",
                }
            )

    return {
        "primary_view_type": primary_type,
        "selected_fields": {
            "x": x_field,
            "y": y_field,
            "color": color_field,
            "numeric": nums[:6],
            "categorical": cats[:6],
        },
        "analysis_target": {
            "name": primary_object,
            "supporting_patterns": [p["pattern_id"] for p in patterns_list[:3]],
            "operational_definition": {
                "entity": "dataset row, subgroup, category relation cell, or boundary record",
                "grain": "one real row or one real aggregate cell",
                "states": ["selected_record", "selected_category", "selected_pattern", "selected_reference"],
                "excluded_interpretations": ["not a KPI dashboard", "not a chart gallery", "not a paper-only reference demo"],
            },
        },
        "primary_question": selected_rq.get("question") or f"How can analysts explore {primary_object} with linked evidence?",
        "primary_visual_object": primary_object,
        "data_task_encoding_mapping": build_mapping(primary_type, x_field, y_field, color_field),
        "why_not_dashboard": "The task requires analysts to move between real marks, subgroup context, pattern evidence, and paper-guided interaction precedents. Independent KPI cards or static summaries would hide the selected row/cell and its evidence trail.",
        "view_graph": [
            {"view_id": "primary_data_view", "role": "primary", "purpose": f"Render real data as {primary_object}."},
            {"view_id": "pattern_reference_view", "role": "companion", "purpose": "Show mined data patterns and retrieved VIS precedents that shape the design."},
            {"view_id": "field_context_view", "role": "companion", "purpose": "Expose fields, categories, distributions, or selected subgroup context."},
            {"view_id": "evidence_panel", "role": "detail", "purpose": "Show selected row/cell evidence, pattern provenance, and paper reference evidence."},
        ],
        "shared_state": ["selected_record", "selected_category", "selected_pattern", "selected_reference"],
        "linked_interactions": [
            {"interaction_id": "select_mark_updates_evidence", "source_view": "primary_data_view", "target_views": ["field_context_view", "evidence_panel"], "shared_state": "selected_record"},
            {"interaction_id": "select_category_updates_marks", "source_view": "field_context_view", "target_views": ["primary_data_view", "evidence_panel"], "shared_state": "selected_category"},
            {"interaction_id": "select_reference_updates_design_trace", "source_view": "pattern_reference_view", "target_views": ["primary_data_view", "evidence_panel"], "shared_state": "selected_reference"},
        ],
        "exploration_affordance": {
            "default_state": "Show the strongest data pattern, real primary marks, top retrieved references, and row evidence together.",
            "entry_points": ["start from data mark", "start from subgroup/category", "start from mined pattern", "start from paper reference"],
            "non_linear_guards": ["clear selection is always visible", "no hidden primary view", "paper references remain evidence, not data"],
        },
        "reference_learning": {
            "retrieval_status": digest.get("retrieval_status"),
            "retrieval_mode": digest.get("retrieval_mode"),
            "applied_elements": applied,
            "unused_references": unused,
            "coverage_summary": digest.get("coverage_summary"),
        },
    }


def build_mapping(primary_type: str, x: str | None, y: str | None, color: str | None) -> list[dict[str, Any]]:
    mapping = []
    if primary_type == "scatter":
        mapping.append({"field_or_concept": f"{x} and {y}", "task": "inspect row-level coupling and shape", "encoding": "two-axis point projection", "reason": "the axes are real numeric fields from the dataset"})
    elif primary_type == "category_matrix":
        mapping.append({"field_or_concept": f"{x} x {y}", "task": "inspect observed category relationships", "encoding": "count matrix cells sized by real row counts", "reason": "the data has categorical relation structure rather than stable metric axes"})
    elif primary_type == "numeric_strip":
        mapping.append({"field_or_concept": x or "numeric field", "task": "inspect boundary cases", "encoding": "ranked strip of real row values", "reason": "the dataset has one dominant numeric field"})
    else:
        mapping.append({"field_or_concept": x or "record identity", "task": "inspect row/category evidence", "encoding": "deterministic record lattice", "reason": "the dataset has weak numeric structure but still has real rows and categories"})
    if color:
        mapping.append({"field_or_concept": color, "task": "compare subgroups", "encoding": "color/highlight and category filter", "reason": "selection must preserve subgroup context"})
    mapping.append({"field_or_concept": "retrieved VIS papers", "task": "adapt interaction/evidence precedents", "encoding": "reference trace list linked to design and evidence", "reason": "paper guidance is auditable without replacing dataset marks"})
    return mapping


def write_reference_report(path: Path, digest: dict[str, Any]) -> None:
    lines = ["# Paper Reference Report", "", f"Retrieval mode: `{digest.get('retrieval_mode')}`", "", "## Query Terms", "", ", ".join(digest.get("query_terms") or []), "", "## Selected References", ""]
    for ref in digest.get("selected_references", []):
        lines.extend([f"### {ref.get('rank')}. {ref.get('title')}", "", f"- Paper id: `{ref.get('paper_id')}`", f"- Abstract: {ref.get('abstract_snippet')}", "- Borrowed elements:"])
        for elem in ref.get("borrowed_elements") or []:
            lines.append(f"  - {elem.get('borrowed_element')} -> {', '.join(elem.get('mapped_to_view_ids') or [])}")
        lines.append("")
    write_text(path, "\n".join(lines).rstrip() + "\n")


def build_payload(rows: list[dict[str, Any]], profile: dict[str, Any], patterns: dict[str, Any], digest: dict[str, Any], design: dict[str, Any]) -> dict[str, Any]:
    fields = design["selected_fields"]
    max_payload_rows = 1200
    display_rows = rows[:max_payload_rows]
    row_payload = []
    for index, row in enumerate(display_rows):
        item = {"__row_index": index}
        for col in profile["columns"]:
            name = col["name"]
            item[name] = row.get(name)
            if col["type"] in {"numeric", "temporal"}:
                item[f"__num__{name}"] = to_float(row.get(name))
        row_payload.append(item)
    return {
        "schema_version": "dataset_vis_frontend_payload_v0.1",
        "created_at": now_iso(),
        "dataset": {
            "path": profile["meta"]["path"],
            "description": profile["meta"].get("description", ""),
            "row_count_loaded": profile["meta"]["row_count_loaded"],
            "column_count": profile["meta"]["column_count"],
            "truncated": profile["meta"].get("truncated"),
        },
        "profile": profile,
        "patterns": patterns.get("patterns", []),
        "candidate_research_questions": patterns.get("candidate_research_questions", []),
        "references": digest.get("selected_references", []),
        "design": design,
        "rows": row_payload,
        "selected_fields": fields,
    }


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dataset Paper-Grounded VIS Analytics</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app">
    <header class="topbar">
      <div class="titleBlock">
        <div class="kicker">Dataset-grounded VIS system</div>
        <h1 id="datasetTitle">Loading dataset...</h1>
      </div>
      <div class="question" id="primaryQuestion"></div>
      <div class="controls">
        <button class="routeButton active" data-route="data" type="button">Data</button>
        <button class="routeButton" data-route="patterns" type="button">Patterns</button>
        <button class="routeButton" data-route="references" type="button">Papers</button>
        <button class="routeButton" id="clearBtn" type="button">Clear</button>
      </div>
    </header>
    <main class="workspace">
      <section class="panel primaryPanel">
        <div class="panelHead">
          <div>
            <span class="eyebrow" id="primaryEyebrow">Primary data view</span>
            <h2 id="primaryTitle">Real Data Marks</h2>
          </div>
          <div class="fieldBadge" id="fieldBadge"></div>
        </div>
        <div id="primaryView" class="primaryView"></div>
      </section>
      <section class="panel referencePanel">
        <div class="panelHead compactHead">
          <div>
            <span class="eyebrow">Patterns and papers</span>
            <h2>Design Grounding</h2>
          </div>
        </div>
        <div id="groundingList" class="scrollArea"></div>
      </section>
      <section class="panel contextPanel">
        <div class="panelHead compactHead">
          <div>
            <span class="eyebrow">Field context</span>
            <h2 id="contextTitle">Subgroup State</h2>
          </div>
        </div>
        <div id="contextView" class="contextView"></div>
      </section>
      <section class="panel evidencePanel">
        <div class="panelHead compactHead">
          <div>
            <span class="eyebrow">Evidence detail</span>
            <h2>Selection Evidence</h2>
          </div>
        </div>
        <div id="evidenceBody" class="scrollArea"></div>
      </section>
    </main>
    <footer id="provenanceBar" class="provenance"></footer>
  </div>
  <script src="data/payload.js"></script>
  <script src="main.js"></script>
</body>
</html>
"""


CSS = """
:root {
  --bg: #eef3f5;
  --panel: #ffffff;
  --ink: #17232d;
  --muted: #657683;
  --line: #cbd9df;
  --teal: #087f8c;
  --blue: #2367a8;
  --green: #4e8c45;
  --amber: #b87317;
  --red: #b84b44;
  --soft: #e9f4f4;
  --shadow: 0 8px 18px rgba(34, 54, 66, .08);
}
* { box-sizing: border-box; }
html, body {
  width: 100%;
  height: 100%;
  margin: 0;
  overflow: hidden;
  background: var(--bg);
  color: var(--ink);
  font: 13px/1.35 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: 0;
}
button { font: inherit; }
#app {
  height: 100vh;
  min-height: 0;
  display: grid;
  grid-template-rows: 66px minmax(0, 1fr) 24px;
}
.topbar {
  min-height: 0;
  padding: 9px 14px 8px;
  display: grid;
  grid-template-columns: minmax(340px, .9fr) minmax(420px, 1.25fr) auto;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid var(--line);
  background: #f8fbfc;
}
.titleBlock { min-width: 0; }
.kicker, .eyebrow {
  color: var(--teal);
  font-size: 10px;
  font-weight: 780;
  text-transform: uppercase;
}
h1, h2, p { margin: 0; }
h1 {
  overflow: hidden;
  font-size: 17px;
  font-weight: 780;
  line-height: 1.18;
  text-overflow: ellipsis;
  white-space: nowrap;
}
h2 { font-size: 13px; line-height: 1.15; }
.question {
  min-width: 0;
  color: #31444f;
  font-size: 12px;
  line-height: 1.25;
}
.controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 7px;
}
.routeButton {
  height: 30px;
  min-width: 76px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: #243741;
  cursor: pointer;
}
.routeButton.active {
  border-color: var(--teal);
  background: #dff1f2;
  color: #064f59;
  font-weight: 780;
}
.workspace {
  min-height: 0;
  padding: 10px;
  display: grid;
  grid-template-columns: minmax(540px, 1.45fr) minmax(330px, .84fr) minmax(360px, .92fr);
  grid-template-rows: minmax(0, 1fr) minmax(182px, .43fr);
  gap: 10px;
  overflow: hidden;
}
.panel {
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: var(--shadow);
}
.primaryPanel { grid-row: 1 / 3; }
.evidencePanel { grid-column: 3; grid-row: 1 / 3; }
.panelHead {
  min-height: 48px;
  padding: 10px 11px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border-bottom: 1px solid #dde8ec;
}
.compactHead { min-height: 44px; }
.fieldBadge {
  max-width: 260px;
  overflow: hidden;
  color: var(--muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.primaryView, .contextView, .scrollArea {
  min-height: 0;
  overflow: hidden;
}
.primaryView { padding: 8px; }
.primaryView svg { width: 100%; height: 100%; display: block; }
.scrollArea {
  overflow-y: auto;
  padding: 8px;
}
.contextView {
  padding: 8px;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 8px;
}
.chipWrap {
  min-height: 0;
  overflow: auto;
  display: flex;
  align-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
}
.chip {
  border: 1px solid #c8d8de;
  border-radius: 6px;
  padding: 4px 7px;
  background: #f8fbfc;
  color: #273b46;
  cursor: pointer;
}
.chip.active {
  border-color: var(--blue);
  background: #e2edf8;
  color: #173f67;
  font-weight: 760;
}
.checkpoint {
  min-height: 42px;
  padding: 7px;
  border: 1px solid #d8e4e8;
  border-radius: 6px;
  background: #f3f8f9;
}
.groundItem {
  margin: 0 0 7px;
  padding: 8px;
  border: 1px solid #d8e3e8;
  border-left: 4px solid #a8bbc2;
  border-radius: 6px;
  background: #fbfdfe;
  cursor: pointer;
}
.groundItem.active {
  border-left-color: var(--teal);
  background: #e9f5f5;
}
.groundTitle {
  font-size: 12px;
  font-weight: 780;
  line-height: 1.2;
}
.smallText {
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
}
.evidenceBlock {
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid #dce6ea;
}
.evidenceBlock:last-child { border-bottom: 0; }
.evidenceTitle {
  margin-bottom: 5px;
  font-size: 13px;
  font-weight: 780;
}
.evidenceLine {
  margin-top: 5px;
  color: #334751;
  font-size: 12px;
}
.tagLine {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 6px;
}
.tag {
  border: 1px solid #d3e0e5;
  border-radius: 5px;
  padding: 2px 5px;
  background: #f8fbfc;
  color: #36515f;
  font-size: 10px;
}
.provenance {
  min-width: 0;
  overflow: hidden;
  padding: 4px 12px;
  border-top: 1px solid var(--line);
  background: #f8fbfc;
  color: #60717c;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.axis { stroke: #9fb3bc; stroke-width: 1; }
.gridLine { stroke: #e2ebee; stroke-width: 1; }
.markLabel { fill: #21343e; font-size: 11px; font-weight: 650; pointer-events: none; }
.mutedLabel { fill: #647783; font-size: 10px; pointer-events: none; }
.dataMark, .matrixCell, .stripMark { cursor: pointer; transition: opacity .12s ease, stroke-width .12s ease; }
.dimmed { opacity: .26; }
.selectedStroke { stroke: #111f27; stroke-width: 3; }
@media (max-width: 1500px) {
  #app { grid-template-rows: 62px minmax(0, 1fr) 22px; }
  .topbar { grid-template-columns: minmax(300px, .9fr) minmax(340px, 1fr) auto; gap: 9px; padding: 7px 10px; }
  h1 { font-size: 15px; }
  .question { font-size: 11px; }
  .workspace {
    padding: 8px;
    gap: 8px;
    grid-template-columns: minmax(470px, 1.36fr) minmax(285px, .82fr) minmax(310px, .9fr);
    grid-template-rows: minmax(0, 1fr) minmax(160px, .42fr);
  }
  .panelHead { min-height: 40px; padding: 7px 8px 6px; }
  .routeButton { min-width: 66px; padding: 0 8px; }
}
"""


JS = r"""
const payload = window.__DATASET_VIS_PAYLOAD__;
const state = {
  route: "data",
  selectedRow: 0,
  selectedCategory: null,
  selectedPattern: payload.patterns[0]?.pattern_id || null,
  selectedReference: payload.references[0]?.paper_id || null
};

function byId(id) { return document.getElementById(id); }
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}
function num(row, field) { return Number(row[`__num__${field}`]); }
function validNum(value) { return Number.isFinite(value); }
function selectedRow() { return payload.rows[state.selectedRow] || payload.rows[0] || null; }
function selectedRef() { return payload.references.find(ref => ref.paper_id === state.selectedReference) || payload.references[0] || null; }
function selectedPattern() { return payload.patterns.find(p => p.pattern_id === state.selectedPattern) || payload.patterns[0] || null; }
function palette(index) { return ["#087f8c", "#2367a8", "#4e8c45", "#b87317", "#b84b44", "#6e7f8f", "#805f9f"][index % 7]; }
function categoryValues(field) {
  if (!field) return [];
  const counts = new Map();
  payload.rows.forEach(row => {
    const value = row[field];
    if (value !== null && value !== undefined && value !== "") counts.set(String(value), (counts.get(String(value)) || 0) + 1);
  });
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 24);
}
function categoryColor(value, field) {
  const values = categoryValues(field).map(item => item[0]);
  const index = Math.max(0, values.indexOf(String(value)));
  return palette(index);
}
function extent(field) {
  const values = payload.rows.map(row => num(row, field)).filter(validNum);
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (!validNum(min) || !validNum(max)) return [0, 1];
  if (min === max) { min -= 1; max += 1; }
  return [min, max];
}
function scale(value, min, max, lo, hi) {
  if (!validNum(value)) return null;
  return lo + ((value - min) / (max - min)) * (hi - lo);
}
function renderHeader() {
  const pathParts = String(payload.dataset.path || "dataset").split(/[\\/]/);
  byId("datasetTitle").textContent = pathParts[pathParts.length - 1];
  byId("primaryQuestion").textContent = payload.design.primary_question;
  document.querySelectorAll(".routeButton[data-route]").forEach(button => {
    button.classList.toggle("active", button.dataset.route === state.route);
    button.onclick = () => { state.route = button.dataset.route; renderAll(); };
  });
  byId("clearBtn").onclick = () => {
    state.route = "data";
    state.selectedRow = 0;
    state.selectedCategory = null;
    state.selectedPattern = payload.patterns[0]?.pattern_id || null;
    state.selectedReference = payload.references[0]?.paper_id || null;
    renderAll();
  };
  byId("provenanceBar").textContent = `Dataset: ${payload.dataset.path} | rows loaded: ${payload.dataset.row_count_loaded} | columns: ${payload.dataset.column_count} | papers: ${payload.references.length} | marks from real dataset payload`;
}
function svg(width, height, body) {
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="real dataset visualization">${body}</svg>`;
}
function renderScatter() {
  const fields = payload.selected_fields;
  const xField = fields.x;
  const yField = fields.y;
  const colorField = fields.color;
  const [xmin, xmax] = extent(xField);
  const [ymin, ymax] = extent(yField);
  const rows = payload.rows.filter(row => validNum(num(row, xField)) && validNum(num(row, yField)));
  const marks = rows.map(row => {
    const x = scale(num(row, xField), xmin, xmax, 64, 660);
    const y = scale(num(row, yField), ymin, ymax, 430, 58);
    const active = state.selectedRow === row.__row_index;
    const categoryMatch = !state.selectedCategory || String(row[colorField]) === String(state.selectedCategory);
    const color = colorField ? categoryColor(row[colorField], colorField) : "#087f8c";
    return `<circle data-mark="true" class="dataMark ${active ? "selectedStroke" : ""} ${categoryMatch ? "" : "dimmed"}" data-row="${row.__row_index}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${active ? 7 : 4.5}" fill="${color}" opacity="${categoryMatch ? .84 : .22}" />`;
  }).join("");
  return svg(720, 500, `
    <rect x="14" y="14" width="692" height="472" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    ${[0,1,2,3,4].map(i => `<line class="gridLine" x1="64" x2="660" y1="${58 + i * 93}" y2="${58 + i * 93}" />`).join("")}
    <line class="axis" x1="64" x2="660" y1="430" y2="430" />
    <line class="axis" x1="64" x2="64" y1="58" y2="430" />
    ${marks}
    <text class="markLabel" x="64" y="34">${esc(xField)} x ${esc(yField)}</text>
    <text class="mutedLabel" x="530" y="462">${esc(xField)}</text>
    <text class="mutedLabel" x="18" y="66">${esc(yField)}</text>
    <text class="mutedLabel" x="368" y="482">each point = one real dataset row</text>
  `);
}
function renderMatrix() {
  const fields = payload.selected_fields;
  const xField = fields.x;
  const yField = fields.y || fields.categorical?.[1] || fields.x;
  const xs = categoryValues(xField).slice(0, 10).map(item => item[0]);
  const ys = categoryValues(yField).slice(0, 9).map(item => item[0]);
  const counts = new Map();
  payload.rows.forEach(row => {
    const x = String(row[xField] ?? "");
    const y = String(row[yField] ?? "");
    if (x && y) counts.set(`${x}|||${y}`, (counts.get(`${x}|||${y}`) || 0) + 1);
  });
  const maxCount = Math.max(1, ...counts.values());
  const cellW = 540 / Math.max(1, xs.length);
  const cellH = 320 / Math.max(1, ys.length);
  let cells = "";
  ys.forEach((y, yi) => {
    xs.forEach((x, xi) => {
      const count = counts.get(`${x}|||${y}`) || 0;
      const active = state.selectedCategory === `${x}|||${y}`;
      const alpha = .18 + .75 * (count / maxCount);
      cells += `<rect data-mark="true" class="matrixCell ${active ? "selectedStroke" : ""}" data-cat="${esc(`${x}|||${y}`)}" x="${118 + xi * cellW}" y="${58 + yi * cellH}" width="${Math.max(8, cellW - 5)}" height="${Math.max(8, cellH - 5)}" rx="5" fill="#087f8c" opacity="${alpha}" />`;
      if (count) cells += `<text class="mutedLabel" x="${124 + xi * cellW}" y="${75 + yi * cellH}">${count}</text>`;
    });
  });
  const xLabels = xs.map((x, i) => `<text class="mutedLabel" x="${118 + i * cellW}" y="44">${esc(String(x).slice(0, 10))}</text>`).join("");
  const yLabels = ys.map((y, i) => `<text class="mutedLabel" x="26" y="${75 + i * cellH}">${esc(String(y).slice(0, 16))}</text>`).join("");
  return svg(720, 500, `
    <rect x="14" y="14" width="692" height="472" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    <text class="markLabel" x="26" y="34">${esc(xField)} x ${esc(yField)} relation matrix</text>
    ${xLabels}${yLabels}${cells}
    <text class="mutedLabel" x="380" y="480">cell opacity = real row count</text>
  `);
}
function renderStrip() {
  const fields = payload.selected_fields;
  const xField = fields.x || fields.numeric?.[0];
  const colorField = fields.color;
  const [min, max] = extent(xField);
  const rows = payload.rows.filter(row => validNum(num(row, xField))).sort((a, b) => num(a, xField) - num(b, xField)).slice(0, 500);
  const marks = rows.map((row, i) => {
    const x = scale(num(row, xField), min, max, 70, 660);
    const y = 72 + (i % 12) * 28;
    const active = state.selectedRow === row.__row_index;
    return `<circle data-mark="true" class="stripMark ${active ? "selectedStroke" : ""}" data-row="${row.__row_index}" cx="${x.toFixed(1)}" cy="${y}" r="${active ? 7 : 4.5}" fill="${colorField ? categoryColor(row[colorField], colorField) : "#087f8c"}" opacity=".82" />`;
  }).join("");
  return svg(720, 500, `
    <rect x="14" y="14" width="692" height="472" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    <line class="axis" x1="70" x2="660" y1="420" y2="420" />
    ${marks}
    <text class="markLabel" x="30" y="34">${esc(xField)} boundary strip</text>
    <text class="mutedLabel" x="70" y="446">${min.toFixed(2)}</text>
    <text class="mutedLabel" x="620" y="446">${max.toFixed(2)}</text>
  `);
}
function renderPrimary() {
  const type = payload.design.primary_view_type;
  byId("primaryTitle").textContent = payload.design.primary_visual_object;
  byId("primaryEyebrow").textContent = type === "scatter" ? "Row-level numeric structure" : type === "category_matrix" ? "Categorical relation structure" : "Record evidence structure";
  byId("fieldBadge").textContent = Object.values(payload.selected_fields).filter(v => typeof v === "string").join(" / ");
  let markup = type === "category_matrix" ? renderMatrix() : type === "scatter" ? renderScatter() : renderStrip();
  byId("primaryView").innerHTML = markup;
  byId("primaryView").querySelectorAll("[data-row]").forEach(el => {
    el.onclick = () => { state.selectedRow = Number(el.dataset.row); state.route = "data"; renderAll(); };
  });
  byId("primaryView").querySelectorAll("[data-cat]").forEach(el => {
    el.onclick = () => { state.selectedCategory = el.dataset.cat; state.route = "data"; renderAll(); };
  });
}
function renderGrounding() {
  const patternItems = payload.patterns.map(p => `
    <div class="groundItem ${state.selectedPattern === p.pattern_id ? "active" : ""}" data-pattern="${esc(p.pattern_id)}">
      <div class="groundTitle">${esc(p.title)}</div>
      <div class="smallText">${esc(p.type)} | fields: ${esc((p.fields || []).join(", "))}</div>
      <div class="smallText">${esc(p.visual_implication || "")}</div>
    </div>
  `).join("");
  const refItems = payload.references.slice(0, 6).map(ref => `
    <div class="groundItem ${state.selectedReference === ref.paper_id ? "active" : ""}" data-ref="${esc(ref.paper_id)}">
      <div class="groundTitle">${esc(ref.rank)}. ${esc(ref.title)}</div>
      <div class="smallText">${esc((ref.borrowed_elements || [])[0]?.borrowed_element || "paper design evidence")}</div>
    </div>
  `).join("");
  byId("groundingList").innerHTML = (state.route === "references" ? refItems + patternItems : patternItems + refItems);
  byId("groundingList").querySelectorAll("[data-pattern]").forEach(el => {
    el.onclick = () => { state.selectedPattern = el.dataset.pattern; state.route = "patterns"; renderAll(); };
  });
  byId("groundingList").querySelectorAll("[data-ref]").forEach(el => {
    el.onclick = () => { state.selectedReference = el.dataset.ref; state.route = "references"; renderAll(); };
  });
}
function renderContext() {
  const catField = payload.selected_fields.color || payload.selected_fields.categorical?.[0];
  const chips = categoryValues(catField).map(([value, count]) => `
    <button class="chip ${String(state.selectedCategory) === String(value) ? "active" : ""}" data-cat-value="${esc(value)}" type="button">${esc(value)} (${count})</button>
  `).join("");
  const nums = payload.selected_fields.numeric || [];
  const numericTags = nums.map(field => `<span class="tag">${esc(field)}</span>`).join("");
  byId("contextTitle").textContent = catField ? `${catField} filter and field state` : "Field state";
  byId("contextView").innerHTML = `
    <div class="chipWrap">${chips || numericTags}</div>
    <div class="checkpoint">Checkpoint: ${esc(selectedPattern()?.title || "Select a pattern")} | selected rows/cells update the evidence panel and primary highlights.</div>
  `;
  byId("contextView").querySelectorAll("[data-cat-value]").forEach(el => {
    el.onclick = () => { state.selectedCategory = el.dataset.catValue; renderAll(); };
  });
}
function rowEvidence(row) {
  if (!row) return "<div class='evidenceLine'>No selected row.</div>";
  return payload.profile.columns.slice(0, 14).map(col => `<div class="evidenceLine"><strong>${esc(col.name)}:</strong> ${esc(row[col.name])}</div>`).join("");
}
function renderEvidence() {
  const row = selectedRow();
  const pattern = selectedPattern();
  const ref = selectedRef();
  const selectedCategory = state.selectedCategory;
  const refBorrow = ref?.borrowed_elements?.map(elem => `<div class="evidenceLine">- ${esc(elem.borrowed_element)}</div>`).join("") || "<div class='evidenceLine'>No paper reference selected.</div>";
  byId("evidenceBody").innerHTML = `
    <div class="evidenceBlock">
      <div class="evidenceTitle">Selected data evidence</div>
      <div class="evidenceLine">Row index: ${esc(row?.__row_index ?? "none")} ${selectedCategory ? `| Category: ${esc(selectedCategory)}` : ""}</div>
      ${rowEvidence(row)}
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">Mined pattern</div>
      <div class="evidenceLine">${esc(pattern?.title || "No pattern selected.")}</div>
      <div class="tagLine">${(pattern?.fields || []).map(f => `<span class="tag">${esc(f)}</span>`).join("")}</div>
      <div class="evidenceLine">${esc(pattern?.visual_implication || "")}</div>
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">Paper-guided design precedent</div>
      <div class="evidenceLine"><strong>${esc(ref?.title || "No retrieved paper")}</strong></div>
      ${refBorrow}
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">Why this is not a dashboard</div>
      <div class="evidenceLine">${esc(payload.design.why_not_dashboard)}</div>
    </div>
  `;
}
function renderAll() {
  renderHeader();
  renderPrimary();
  renderGrounding();
  renderContext();
  renderEvidence();
}
if (!payload) {
  document.body.innerHTML = "<p>Missing dataset payload.</p>";
} else {
  renderAll();
  window.__DATASET_VIS_DEMO_READY__ = true;
}
"""


def write_frontend(run_dir: Path, payload: dict[str, Any]) -> None:
    app = run_dir / "app"
    write_text(app / "index.html", HTML)
    write_text(app / "style.css", CSS.lstrip())
    write_text(app / "main.js", JS.lstrip())
    write_json(app / "data" / "payload.json", payload)
    write_text(app / "data" / "payload.js", "window.__DATASET_VIS_PAYLOAD__ = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n")


def write_design_artifacts(run_dir: Path, profile: dict[str, Any], patterns: dict[str, Any], digest: dict[str, Any], design: dict[str, Any]) -> None:
    contract = {
        "schema_version": "dataset_e_idea_contract_v0.1",
        "created_by": "dataset-paper-grounded-vis-analytics",
        "mechanism_context": {
            "generation": {"mechanism": "E_data_driven_with_paper_grounding"},
            "data_driven": design,
        },
    }
    spec = {
        "schema_version": "dataset_visual_system_spec_v0.1",
        "analysis_target": design["analysis_target"],
        "primary_question": design["primary_question"],
        "primary_visual_object": design["primary_visual_object"],
        "selected_real_fields": design["selected_fields"],
        "view_graph": design["view_graph"],
        "shared_state": design["shared_state"],
        "linked_interactions": design["linked_interactions"],
        "viewport_contract": {
            "primary_viewport": "1920x1080",
            "validation_viewport": "1440x810",
            "page_level_scroll": "forbidden_on_initial_load",
            "local_scroll": "allowed_inside_bounded_evidence_panels",
        },
        "reference_learning_adapted": design["reference_learning"],
    }
    write_json(run_dir / "stage2_idea" / "e_idea_contract.json", contract)
    write_json(run_dir / "stage3_visual_spec" / "visual_system_spec.json", spec)
    selected_rq = next(
        (
            rq
            for rq in (patterns.get("candidate_research_questions") or [])
            if rq.get("question") == design.get("primary_question")
        ),
        (patterns.get("candidate_research_questions") or [{}])[0],
    )
    write_text(
        run_dir / "stage2_idea" / "rq_selection.md",
        f"# RQ Selection\n\nSelected: {selected_rq.get('rq_id', 'rq1')}\n\n{selected_rq.get('question', design['primary_question'])}\n\nReason: strongest available data-backed pattern with coordinated workspace potential.\n",
    )
    lines = [
        "# Dataset-Grounded Visual Analytics System Design",
        "",
        "## Dataset",
        "",
        f"- Path: `{profile['meta']['path']}`",
        f"- Rows loaded: {profile['meta']['row_count_loaded']}",
        f"- Columns: {profile['meta']['column_count']}",
        "",
        "## Analysis Target",
        "",
        design["analysis_target"]["name"],
        "",
        "## Primary Visual Object",
        "",
        design["primary_visual_object"],
        "",
        "## Real Field Mapping",
        "",
    ]
    for mapping in design["data_task_encoding_mapping"]:
        lines.append(f"- {mapping['field_or_concept']}: {mapping['task']} -> {mapping['encoding']} ({mapping['reason']})")
    lines.extend(["", "## Mined Patterns", ""])
    for pattern in patterns.get("patterns", [])[:5]:
        lines.append(f"- `{pattern['pattern_id']}` {pattern['title']}")
    lines.extend(["", "## Paper Guidance", ""])
    for ref in digest.get("selected_references", [])[:5]:
        lines.append(f"- `{ref.get('paper_id')}` {ref.get('title')}")
        for elem in ref.get("borrowed_elements", [])[:2]:
            lines.append(f"  - Borrow: {elem.get('borrowed_element')}")
    lines.extend(
        [
            "",
            "## Frontend Contract",
            "",
            "- Primary marks come from real dataset rows or real category aggregations.",
            "- Companion views expose mined patterns, retrieved paper precedents, fields, and category state.",
            "- Evidence panel shows selected row/cell evidence and provenance.",
            "- Initial load must fit 1920x1080 and 1440x810 without page-level scrolling.",
        ]
    )
    write_text(run_dir / "artifacts" / "design_spec.md", "\n".join(lines).rstrip() + "\n")
    write_text(
        run_dir / "artifacts" / "frontend_build_report.md",
        "\n".join(
            [
                "# Frontend Build Report",
                "",
                f"- Built at: {now_iso()}",
                f"- Primary view type: `{design['primary_view_type']}`",
                f"- Rows in payload: {profile['meta']['row_count_loaded']}",
                f"- Paper references: {len(digest.get('selected_references', []))}",
                "",
                "Outputs:",
                "",
                "- `app/index.html`",
                "- `app/style.css`",
                "- `app/main.js`",
                "- `app/data/payload.json`",
                "- `app/data/payload.js`",
            ]
        )
        + "\n",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    dataset_path = Path(args.dataset).resolve()
    papers_dir = Path(args.papers_dir).resolve()
    db_path = Path(args.paper_db).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    rows, profile, patterns = profile_dataset(dataset_path, args.description or "", args.max_rows)
    digest = retrieve_reference_digest(db_path, papers_dir, profile, patterns, args.description or "", args.top_k)
    design = choose_design(profile, patterns, digest)
    payload = build_payload(rows, profile, patterns, digest, design)

    write_json(run_dir / "stage1_data" / "dataset_profile.json", profile)
    write_json(run_dir / "stage1_mining" / "data_patterns.json", patterns)
    write_json(run_dir / "stage2_references" / "paper_reference_digest.json", digest)
    write_reference_report(run_dir / "stage2_references" / "paper_reference_report.md", digest)
    write_design_artifacts(run_dir, profile, patterns, digest, design)
    write_frontend(run_dir, payload)
    write_json(
        run_dir / "artifacts" / "run_manifest.json",
        {
            "created_at": now_iso(),
            "run_dir": str(run_dir),
            "dataset": str(dataset_path),
            "app": str(run_dir / "app" / "index.html"),
            "primary_view_type": design["primary_view_type"],
            "row_count_loaded": profile["meta"]["row_count_loaded"],
            "references": len(digest.get("selected_references", [])),
        },
    )
    return {
        "run_dir": str(run_dir),
        "app": str(run_dir / "app" / "index.html"),
        "primary_view_type": design["primary_view_type"],
        "rows": profile["meta"]["row_count_loaded"],
        "references": len(digest.get("selected_references", [])),
        "status": "dataset_frontend_demo_ready",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--paper-db", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--max-rows", type=int, default=5000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    result = run(parse_args(argv))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
