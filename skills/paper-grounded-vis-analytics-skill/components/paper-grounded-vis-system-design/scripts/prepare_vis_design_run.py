#!/usr/bin/env python3
"""Prepare a paper-grounded visual analytics system design run.

This script is deterministic by default: it extracts keywords, searches the
local ScholarAIO-style paper index, reads local paper artifacts, and writes
Stage 2/3 design artifacts that an OpenClaw agent can refine or implement.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_EMBED_MODEL = "qwen3-0.6B-embedding"

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "using", "used", "use",
    "are", "was", "were", "will", "can", "our", "their", "paper", "study", "system",
    "visualization", "visual", "analysis", "data", "method", "methods", "results",
    "approach", "design", "user", "users", "model", "models", "interactive",
    "we", "they", "which", "have", "has", "based", "through", "between",
}

CONTROLLED_TERMS = [
    "visual analytics", "coordinated multiple views", "linked brushing", "overview detail",
    "focus context", "semantic interaction", "natural language", "large language model",
    "multi agent", "volume visualization", "3d gaussian splatting", "immersive analytics",
    "augmented reality", "uncertainty visualization", "network visualization", "graph",
    "node link", "matrix", "trajectory", "traffic", "flow", "temporal", "spatial",
    "provenance", "evidence", "segmentation", "classification", "clustering",
    "bayesian neural network", "haptics", "surface visualization", "scientific visualization",
    "explainable ai", "model checking", "recommendation", "annotation",
]


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def slugify(value: str, fallback: str = "run") -> str:
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE).strip().lower()
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip(".-")
    return (value or fallback)[:100]


def normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def compact(value: str, limit: int) -> str:
    value = normalize_ws(value)
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "":
        return '""'
    if re.match(r"^[A-Za-z0-9_./:+-]+$", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def to_yaml(obj: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(obj, dict):
        lines: list[str] = []
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(to_yaml(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(obj, list):
        if not obj:
            return f"{pad}[]"
        lines = []
        for item in obj:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{pad}{yaml_scalar(obj)}"


def write_yaml(path: Path, obj: Any) -> None:
    write_text(path, to_yaml(obj).rstrip() + "\n")


def detect_input(path_or_text: str, description: str) -> dict[str, Any]:
    path = Path(path_or_text)
    if path.exists():
        path = path.resolve()
        if path.is_dir():
            meta_path = path / "meta.json"
            md_path = path / "paper.md"
            if meta_path.exists():
                meta = load_json(meta_path)
                paper_text = read_text(md_path) if md_path.exists() else ""
                return input_from_meta(meta, path, paper_text, description)
            return input_from_dataset_dir(path, description)
        suffix = path.suffix.lower()
        if suffix == ".json" and path.name == "meta.json":
            meta = load_json(path)
            paper_text = read_text(path.parent / "paper.md") if (path.parent / "paper.md").exists() else ""
            return input_from_meta(meta, path.parent, paper_text, description)
        if suffix in {".md", ".txt"}:
            text = read_text(path)
            return input_from_text(text, "paper_or_text", str(path), description)
        if suffix == ".pdf":
            return {
                "input_type": "pdf_requires_mineru",
                "input_path": str(path),
                "description": description,
                "title": path.stem,
                "abstract": "",
                "summary": "Raw PDF input. Use paper-mineru-scholar-index first if paper.md/meta.json is unavailable.",
                "text_for_keywords": f"{path.stem}\n{description}",
                "data_schema": {},
                "source_paper_id": "",
            }
        if suffix in {".csv", ".tsv", ".jsonl", ".json"}:
            return input_from_dataset_file(path, description)
        return input_from_text(read_text(path), "file", str(path), description)
    return input_from_text(path_or_text, "free_text", "", description)


def input_from_meta(meta: dict[str, Any], paper_dir: Path, paper_text: str, description: str) -> dict[str, Any]:
    text = "\n".join(
        [
            str(meta.get("title") or ""),
            str(meta.get("abstract") or ""),
            str(meta.get("l3_conclusion") or ""),
            description,
            compact(paper_text, 6000),
        ]
    )
    return {
        "input_type": "paper",
        "input_path": str(paper_dir),
        "description": description,
        "source_paper_id": meta.get("id") or "",
        "title": meta.get("title") or paper_dir.name,
        "abstract": meta.get("abstract") or "",
        "summary": meta.get("l3_conclusion") or "",
        "authors": meta.get("authors") or [],
        "year": meta.get("year"),
        "doi": meta.get("doi") or "",
        "text_for_keywords": text,
        "data_schema": {},
    }


def input_from_text(text: str, kind: str, source_path: str, description: str) -> dict[str, Any]:
    title = ""
    for line in text.splitlines()[:80]:
        line = line.strip().strip("# ")
        if 8 <= len(line) <= 240:
            title = line
            break
    return {
        "input_type": kind,
        "input_path": source_path,
        "description": description,
        "source_paper_id": "",
        "title": title or compact(text, 80) or "Untitled input",
        "abstract": "",
        "summary": compact(text, 2000),
        "text_for_keywords": f"{text}\n{description}",
        "data_schema": {},
    }


def input_from_dataset_dir(path: Path, description: str) -> dict[str, Any]:
    files = [p for p in path.iterdir() if p.is_file() and not p.name.startswith("._")]
    schema = {"files": [{"name": p.name, "suffix": p.suffix.lower(), "bytes": p.stat().st_size} for p in files[:20]]}
    return {
        "input_type": "dataset_dir",
        "input_path": str(path),
        "description": description,
        "source_paper_id": "",
        "title": path.name,
        "abstract": "",
        "summary": f"Dataset directory with {len(files)} files.",
        "text_for_keywords": f"{path.name}\n{description}\n" + "\n".join(p.name for p in files[:20]),
        "data_schema": schema,
    }


def input_from_dataset_file(path: Path, description: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    schema: dict[str, Any] = {"path": str(path), "format": suffix.lstrip("."), "columns": [], "sample_rows": []}
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            schema["columns"] = list(reader.fieldnames or [])
            for idx, row in enumerate(reader):
                if idx >= 5:
                    break
                schema["sample_rows"].append(row)
    elif suffix == ".jsonl":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            rows = []
            for idx, line in enumerate(handle):
                if idx >= 5:
                    break
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
            schema["sample_rows"] = rows
            keys = sorted({k for row in rows if isinstance(row, dict) for k in row})
            schema["columns"] = keys
    elif suffix == ".json":
        obj = load_json(path)
        sample = obj[:5] if isinstance(obj, list) else obj
        schema["sample_rows"] = sample if isinstance(sample, list) else [sample]
        if isinstance(sample, list):
            schema["columns"] = sorted({k for row in sample if isinstance(row, dict) for k in row})
        elif isinstance(sample, dict):
            schema["columns"] = sorted(sample.keys())
    text = "\n".join([path.stem, description, " ".join(schema.get("columns") or []), json.dumps(schema.get("sample_rows"), ensure_ascii=False)])
    return {
        "input_type": "dataset_file",
        "input_path": str(path),
        "description": description,
        "source_paper_id": "",
        "title": path.stem,
        "abstract": "",
        "summary": f"Dataset file with columns: {', '.join(schema.get('columns') or [])}",
        "text_for_keywords": text,
        "data_schema": schema,
    }


def extract_keywords(text: str, top_n: int) -> dict[str, Any]:
    lowered = text.lower()
    controlled = [term for term in CONTROLLED_TERMS if term in lowered]
    tokens = [
        t for t in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", lowered)
        if t not in STOPWORDS and not t.isdigit()
    ]
    counts = Counter(tokens)
    keywords = []
    for term in controlled:
        keywords.append(term)
    for word, _ in counts.most_common(top_n * 2):
        if word not in keywords:
            keywords.append(word)
        if len(keywords) >= top_n:
            break
    query_terms = keywords[: min(10, len(keywords))]
    return {
        "keywords": keywords,
        "controlled_terms": controlled,
        "query_terms": query_terms,
        "retrieval_query": " ".join(query_terms),
    }


def scan_local_papers(papers_dir: Path) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    if not papers_dir.exists():
        return mapping
    for meta_path in papers_dir.glob("*/meta.json"):
        if meta_path.name.startswith("._"):
            continue
        try:
            meta = load_json(meta_path)
        except Exception:
            continue
        paper_id = str(meta.get("id") or "")
        if paper_id:
            mapping[paper_id] = {"meta": meta, "paper_dir": meta_path.parent}
    return mapping


def fts_query(terms: list[str]) -> str:
    clean = []
    for term in terms:
        parts = re.findall(r"[A-Za-z0-9]{3,}", term.lower())
        clean.extend(parts)
    clean = list(dict.fromkeys(clean))[:12]
    return " OR ".join(clean)


def search_fts(db_path: Path, terms: list[str], limit: int, exclude_id: str) -> list[dict[str, Any]]:
    query = fts_query(terms)
    if not db_path.exists() or not query:
        return []
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    rows: list[dict[str, Any]] = []
    try:
        sql = (
            "select paper_id,title,authors,year,journal,abstract,conclusion,doi,paper_type,citation_count,md_path,"
            "bm25(papers) as rank_score from papers where papers match ? order by rank_score limit ?"
        )
        for row in cur.execute(sql, (query, limit * 3)):
            if row[0] == exclude_id:
                continue
            rows.append(
                {
                    "paper_id": row[0],
                    "title": row[1],
                    "authors": row[2],
                    "year": row[3],
                    "journal": row[4],
                    "abstract": row[5],
                    "conclusion": row[6],
                    "doi": row[7],
                    "paper_type": row[8],
                    "citation_count": row[9],
                    "md_path": row[10],
                    "fts_rank": float(row[11]),
                    "fts_score": 1.0 / (1.0 + len(rows)),
                    "retrieval_modes": ["fts"],
                }
            )
            if len(rows) >= limit:
                break
    finally:
        con.close()
    return rows


def http_json(method: str, url: str, payload: dict[str, Any], api_key: str | None, timeout: int) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def embed_query(args: argparse.Namespace, text: str) -> list[float] | None:
    api_base = args.embedding_api_base or os.getenv("PAPER_EMBED_API_BASE")
    api_key = args.embedding_api_key or os.getenv("PAPER_EMBED_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_base:
        return None
    endpoint = api_base.rstrip("/") + "/embeddings"
    data = http_json("POST", endpoint, {"model": args.embedding_model, "input": [text]}, api_key, args.embedding_timeout)
    return list(map(float, data["data"][0]["embedding"]))


def vector_from_blob(blob: bytes) -> list[float]:
    if len(blob) % 4 != 0:
        return []
    return list(struct.unpack("<" + "f" * (len(blob) // 4), blob))


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    aa = sum(x * x for x in a)
    bb = sum(y * y for y in b)
    if aa <= 0 or bb <= 0:
        return 0.0
    return dot / (math.sqrt(aa) * math.sqrt(bb))


def search_vectors(args: argparse.Namespace, query_text: str, exclude_id: str, limit: int) -> list[dict[str, Any]]:
    vector = embed_query(args, query_text)
    if vector is None:
        return []
    db_path = Path(args.paper_db)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    scored = []
    try:
        for paper_id, blob in cur.execute("select paper_id, embedding from paper_vectors"):
            if paper_id == exclude_id:
                continue
            score = cosine(vector, vector_from_blob(blob))
            scored.append((score, paper_id))
    finally:
        con.close()
    scored.sort(reverse=True)
    return [
        {"paper_id": paper_id, "semantic_score": score, "retrieval_modes": ["semantic"]}
        for score, paper_id in scored[:limit]
    ]


def fuse_results(fts: list[dict[str, Any]], semantic: list[dict[str, Any]], local: dict[str, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for rank, row in enumerate(fts, start=1):
        item = by_id.setdefault(row["paper_id"], dict(row))
        item["fused_score"] = item.get("fused_score", 0.0) + 1.0 / (rank + 10)
    for rank, row in enumerate(semantic, start=1):
        item = by_id.setdefault(row["paper_id"], dict(row))
        item.setdefault("retrieval_modes", [])
        if "semantic" not in item["retrieval_modes"]:
            item["retrieval_modes"].append("semantic")
        item["semantic_score"] = row.get("semantic_score", 0.0)
        item["fused_score"] = item.get("fused_score", 0.0) + 1.0 / (rank + 5)
    results = sorted(by_id.values(), key=lambda r: r.get("fused_score", 0.0), reverse=True)[:limit]
    for row in results:
        local_hit = local.get(row["paper_id"]) or {}
        meta = local_hit.get("meta") or {}
        paper_dir = local_hit.get("paper_dir")
        for key in ("title", "authors", "year", "journal", "abstract", "doi", "paper_type", "citation_count"):
            if meta.get(key):
                row[key] = meta.get(key)
        row["conclusion"] = meta.get("l3_conclusion") or row.get("conclusion") or ""
        row["paper_dir"] = str(paper_dir) if paper_dir else ""
        row["meta_path"] = str(paper_dir / "meta.json") if paper_dir else ""
        row["paper_md_path"] = str(paper_dir / "paper.md") if paper_dir and (paper_dir / "paper.md").exists() else ""
    return results


def infer_borrowed_elements(row: dict[str, Any], input_profile: dict[str, Any]) -> list[dict[str, Any]]:
    text = " ".join(str(row.get(k) or "") for k in ("title", "abstract", "conclusion")).lower()
    title = row.get("title") or "Untitled"
    paper_id = row.get("paper_id") or ""
    elements: list[dict[str, Any]] = []

    def add(element: str, view_ids: list[str], interaction_ids: list[str], confidence: str = "medium") -> None:
        elements.append(
            {
                "source_paper_id": paper_id,
                "source_title": title,
                "evidence_field": "title/abstract/l3_conclusion",
                "borrowed_element": element,
                "adapted_for_current_input": f"Adapt this pattern to the input target: {input_profile.get('title')}",
                "mapped_to_view_ids": view_ids,
                "mapped_to_interaction_ids": interaction_ids,
                "confidence": confidence,
            }
        )

    if any(term in text for term in ("natural language", "llm", "agent", "semantic interaction")):
        add("intent-to-action trace: pair a natural-language/semantic control with an explicit execution/evidence view", ["intent_trace_view", "evidence_panel"], ["intent_updates_workspace"], "high")
    if any(term in text for term in ("volume", "3d", "gaussian", "spatial", "segmentation")):
        add("spatial semantic structure view with selectable regions/components and linked detail evidence", ["primary_structure_view", "component_detail_view"], ["select_component_updates_detail"], "high")
    if any(term in text for term in ("network", "graph", "node", "matrix", "bipartite")):
        add("hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity", ["relation_overview", "primary_structure_view"], ["brush_relation_updates_primary"], "medium")
    if any(term in text for term in ("time", "temporal", "trajectory", "flow", "traffic")):
        add("phase/time strip linked to the primary structure so users can compare temporal states without losing context", ["phase_strip_view", "primary_structure_view"], ["brush_time_updates_structure"], "medium")
    if any(term in text for term in ("uncertainty", "probabilistic", "bayesian", "confidence")):
        add("uncertainty layer as secondary evidence, revealed through selection rather than default KPI summaries", ["uncertainty_evidence_view", "evidence_panel"], ["select_item_reveals_uncertainty"], "medium")
    if any(term in text for term in ("augmented reality", "immersive", "haptic", "tangible")):
        add("embodied/interaction-state companion view that separates spatial exploration from evidence explanation", ["interaction_state_view", "evidence_panel"], ["interaction_state_updates_evidence"], "medium")

    if not elements:
        add("coordinated overview-detail evidence workflow: primary structure plus companion distributions and local evidence panel", ["primary_structure_view", "evidence_panel"], ["select_primary_updates_evidence"], "low")
    return elements[:2]


def build_standard_basis() -> dict[str, Any]:
    return {
        "schema_version": "standard_vis_design_basis_v0.1",
        "patterns": [
            {
                "id": "overview_detail_evidence",
                "borrowed_element": "overview + detail + raw evidence trace",
                "use_when": "input has a primary entity set and users need evidence-backed inspection",
            },
            {
                "id": "focus_context_linked_brush",
                "borrowed_element": "focus + context with linked brushing",
                "use_when": "input requires comparing selected subgroups against global context",
            },
            {
                "id": "phase_structure_workspace",
                "borrowed_element": "time/phase strip linked to a structure view",
                "use_when": "temporal or staged phenomena shape interpretation",
            },
            {
                "id": "relation_evidence_hybrid",
                "borrowed_element": "relation overview linked to detail/evidence panel",
                "use_when": "entities have nontrivial associations or dependencies",
            },
        ],
    }


def build_digest(results: list[dict[str, Any]], input_profile: dict[str, Any], keyword_profile: dict[str, Any], retrieval_mode: str) -> dict[str, Any]:
    selected = []
    for rank, row in enumerate(results, start=1):
        selected.append(
            {
                "rank": rank,
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year": row.get("year"),
                "journal": row.get("journal"),
                "score": round(float(row.get("fused_score", row.get("semantic_score", row.get("fts_score", 0.0))) or 0.0), 6),
                "retrieval_modes": row.get("retrieval_modes") or [],
                "meta_path": row.get("meta_path"),
                "paper_md_path": row.get("paper_md_path"),
                "abstract_snippet": compact(row.get("abstract") or "", 420),
                "l3_snippet": compact(row.get("conclusion") or "", 520),
                "borrowed_elements": infer_borrowed_elements(row, input_profile),
            }
        )
    applied_count = sum(1 for ref in selected if ref.get("borrowed_elements"))
    return {
        "schema_version": "paper_grounded_vis_reference_digest_v0.1",
        "created_by": "paper-grounded-vis-system-design/scripts/prepare_vis_design_run.py",
        "retrieval_status": "ok" if selected else "fallback_standard_basis",
        "retrieval_mode": retrieval_mode,
        "query": keyword_profile.get("retrieval_query"),
        "keywords": keyword_profile.get("keywords"),
        "selected_references": selected,
        "coverage_summary": {
            "selected_reference_count": len(selected),
            "applied_paper_count": applied_count,
            "explicitly_rejected_paper_count": 0,
            "silent_reference_count": 0,
        },
    }


def infer_analysis_target(input_profile: dict[str, Any], keywords: list[str]) -> dict[str, Any]:
    title = input_profile.get("title") or "input"
    core = ", ".join(keywords[:5]) if keywords else title
    entity = "paper concepts" if input_profile.get("input_type") == "paper" else "dataset entities"
    if input_profile.get("data_schema", {}).get("columns"):
        entity = "records described by " + ", ".join(input_profile["data_schema"]["columns"][:4])
    return {
        "name": f"{compact(title, 70)} evidence structure",
        "supporting_patterns": ["input_keywords", "retrieved_reference_patterns"],
        "primary_patterns": ["input_keywords"],
        "evidence_patterns": ["retrieved_reference_patterns"],
        "operational_definition": {
            "entity": entity,
            "grain": "one paper concept, data record, or selected entity group",
            "states": ["selected_reference", "selected_keyword_cluster", "selected_entity_or_record", "selected_evidence_route"],
            "primary_user_actions": ["select keyword cluster", "inspect related reference pattern", "compare evidence routes", "open source evidence"],
            "success_observations": [f"user can explain how {core} shapes the designed analytical workspace"],
            "excluded_interpretations": ["not a KPI dashboard", "not an independent chart gallery", "not a literature list"],
        },
    }


def context_blob(input_profile: dict[str, Any], keywords: list[str]) -> str:
    parts = [
        input_profile.get("title") or "",
        input_profile.get("description") or "",
        input_profile.get("abstract") or "",
        input_profile.get("text_for_keywords") or "",
        " ".join(keywords),
    ]
    return " ".join(parts).lower()


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def evidence_grounding(applied_elements: list[dict[str, Any]], index: int, fallback: str) -> str:
    if applied_elements:
        return applied_elements[min(index, len(applied_elements) - 1)].get("borrowed_element") or fallback
    return fallback


def infer_design_blueprint(
    input_profile: dict[str, Any],
    keywords: list[str],
    applied_elements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Infer a domain-specific VIS system blueprint from the input and references."""

    text = context_blob(input_profile, keywords)
    title = compact(input_profile.get("title") or "current input", 82)
    fallback_target = infer_analysis_target(input_profile, keywords)

    simulation_terms = ["cosmo", "cosmological", "astrophysic", "hydrodynamic", "simulation ensemble", "simulation"]
    if not contains_any(text, simulation_terms) and contains_any(text, ["volume", "volvis", "gaussian splatting", "3d gaussian", "tomographic", "viewpoint navigation"]):
        return {
            "domain_id": "language_driven_volume_vis",
            "analysis_target": {
                "name": f"{title} command-to-volume interpretation workspace",
                "supporting_patterns": ["semantic_commands", "volume_regions", "agent_operations", "source_evidence"],
                "primary_patterns": ["semantic volume regions", "editable operation traces"],
                "evidence_patterns": ["retrieved volume-vis systems", "paper L1-L4 snippets", "operation provenance"],
                "operational_definition": {
                    "entity": "volume region, semantic block, 3D Gaussian component, or natural-language intent",
                    "grain": "one command step, selected volume component, or editable scene operation",
                    "states": ["selected_intent", "selected_region", "selected_agent_step", "selected_evidence_route"],
                    "primary_user_actions": ["issue or select an intent", "inspect affected volume regions", "compare execution steps", "open paper evidence"],
                    "success_observations": ["user can trace how a language intent becomes a volume-view edit with explicit evidence"],
                    "excluded_interpretations": ["not a text chat transcript", "not a static rendering gallery", "not a KPI dashboard"],
                },
            },
            "primary_question": f"How can analysts trace, inspect, and revise the mapping from language intent to volume regions and 3D scene operations in {title}?",
            "primary_visual_object": "An editable volume-scene workspace where semantic regions, command intents, agent operations, and local evidence are linked as one inspectable object.",
            "data_task_encoding_mapping": [
                {
                    "field_or_concept": "natural-language intents",
                    "task": "trace intent parsing and operation planning",
                    "encoding": "intent-to-operation rail with confidence and edit status",
                    "reason": "keeps language interaction inspectable instead of hiding it behind chat output",
                },
                {
                    "field_or_concept": "volume regions or Gaussian components",
                    "task": "localize what each command changes",
                    "encoding": "selectable 3D/2.5D semantic region view with linked highlights",
                    "reason": "the primary analytical object is spatial and cannot be understood through text alone",
                },
                {
                    "field_or_concept": "agent/tool execution steps",
                    "task": "compare planned action, rendered effect, and evidence",
                    "encoding": "step timeline connected to scene highlights and evidence snippets",
                    "reason": "multi-agent workflows need provenance and reversible inspection",
                },
                {
                    "field_or_concept": "retrieved VIS precedents",
                    "task": "adapt proven interaction structures",
                    "encoding": "reference pattern panel mapped to scene, intent rail, and evidence panel",
                    "reason": "the design remains paper-grounded and auditable",
                },
            ],
            "why_not_dashboard": "The core work is command-to-scene interpretation and spatial evidence tracing. KPI cards would hide where an intent acts, how an agent plan changes the scene, and why a reference pattern was applied.",
            "view_graph": [
                {
                    "view_id": "volume_scene_view",
                    "role": "primary",
                    "purpose": "Show semantic volume regions or 3D Gaussian components with current command effects and editable selection handles.",
                    "reference_grounding": evidence_grounding(applied_elements, 0, "spatial semantic structure view"),
                },
                {
                    "view_id": "intent_operation_view",
                    "role": "companion",
                    "purpose": "Show natural-language intents, parsed slots, agent/tool steps, confidence, and reversible edits.",
                    "reference_grounding": evidence_grounding(applied_elements, 1, "intent-to-action trace"),
                },
                {
                    "view_id": "region_state_strip",
                    "role": "companion",
                    "purpose": "Compare region states, edit history, or timestep changes without losing the selected scene context.",
                    "reference_grounding": evidence_grounding(applied_elements, 2, "phase/time strip linked to the primary structure"),
                },
                {
                    "view_id": "evidence_panel",
                    "role": "detail",
                    "purpose": "Show paper snippets, command provenance, caveats, and local evidence for the current scene or intent selection.",
                    "reference_grounding": "standard evidence trace policy",
                },
            ],
            "shared_state": ["selected_intent", "selected_region", "selected_agent_step", "selected_evidence_route"],
            "linked_interactions": [
                {
                    "interaction_id": "select_intent_highlights_scene",
                    "source_view": "intent_operation_view",
                    "target_views": ["volume_scene_view", "region_state_strip", "evidence_panel"],
                    "shared_state": "selected_intent",
                },
                {
                    "interaction_id": "select_region_updates_plan",
                    "source_view": "volume_scene_view",
                    "target_views": ["intent_operation_view", "region_state_strip", "evidence_panel"],
                    "shared_state": "selected_region",
                },
                {
                    "interaction_id": "scrub_region_state",
                    "source_view": "region_state_strip",
                    "target_views": ["volume_scene_view", "intent_operation_view", "evidence_panel"],
                    "shared_state": "selected_agent_step",
                },
            ],
            "exploration_affordance": {
                "model": "guided_open_exploration",
                "default_state": "Show the current volume scene, the strongest intent/operation chain, and the top reference-backed evidence simultaneously.",
                "entry_points": ["start from language intent", "start from volume region", "start from retrieved reference pattern"],
                "analysis_routes": [
                    "intent -> operation step -> affected scene region -> evidence",
                    "region -> command history -> comparable state -> caveat",
                    "reference pattern -> adapted interaction -> current view id",
                ],
                "non_linear_guards": ["clear selection is always visible", "scene and operation rail preserve shared state", "edits are reversible"],
            },
            "visual_style_system": {
                "style_intent": "scientific volume workbench with crisp spatial marks, explicit command provenance, and restrained research-tool density",
                "background_policy": "cool neutral or ink-on-white; avoid dark sci-fi glow and decorative gradients",
                "palette_roles": {
                    "spatial_region": "clear categorical accents",
                    "intent_step": "high-salience interaction accent",
                    "reference_grounding": "secondary cool hue",
                    "uncertainty_or_caveat": "amber warning used sparingly",
                },
            },
        }

    if contains_any(text, simulation_terms):
        return {
            "domain_id": "multiscale_simulation_exploration",
            "analysis_target": {
                "name": f"{title} multiscale simulation evidence workspace",
                "supporting_patterns": ["simulation_snapshots", "spatial_structures", "physical_variables", "parameter_context"],
                "primary_patterns": ["spatial density/structure", "time or scale transitions"],
                "evidence_patterns": ["retrieved scientific-vis systems", "local paper snippets", "selected simulation statistics"],
                "operational_definition": {
                    "entity": "simulation snapshot, spatial cell, halo/feature group, variable field, or parameter run",
                    "grain": "one structure at a scale, one time/redshift state, or one compared simulation condition",
                    "states": ["selected_structure", "selected_snapshot", "selected_variable", "selected_evidence_route"],
                    "primary_user_actions": ["select a spatial structure", "scrub time or scale", "compare variable distributions", "inspect provenance"],
                    "success_observations": ["user can explain which simulation structure changes across scale/time and what evidence supports it"],
                    "excluded_interpretations": ["not an image gallery", "not a static parameter table", "not a KPI dashboard"],
                },
            },
            "primary_question": f"How can analysts identify, compare, and explain multiscale simulation structures in {title} while preserving provenance?",
            "primary_visual_object": "A multiscale simulation workspace where spatial structures, temporal/scale states, variables, and reference evidence stay linked through shared selection.",
            "data_task_encoding_mapping": [
                {
                    "field_or_concept": "simulation structures",
                    "task": "locate and compare meaningful spatial features",
                    "encoding": "selectable structure map or volume projection with variable overlays",
                    "reason": "simulation analysis starts from spatial/physical structure, not isolated metrics",
                },
                {
                    "field_or_concept": "time, redshift, or scale",
                    "task": "track how selected structures change",
                    "encoding": "snapshot/scale strip linked to the primary map",
                    "reason": "temporal and multiscale context prevents false local interpretations",
                },
                {
                    "field_or_concept": "physical variables and parameters",
                    "task": "compare distributions and relationships",
                    "encoding": "relation matrix or compact distribution panel tied to selection",
                    "reason": "domain experts need variable evidence behind spatial patterns",
                },
                {
                    "field_or_concept": "retrieved scientific visualization precedents",
                    "task": "reuse interaction patterns for large simulation data",
                    "encoding": "reference pattern panel with mapped view ids",
                    "reason": "paper grounding keeps the design defensible",
                },
            ],
            "why_not_dashboard": "The key question depends on spatial structure, time/scale continuity, variable relationships, and provenance. Independent charts would break the links needed to explain simulation phenomena.",
            "view_graph": [
                {
                    "view_id": "simulation_structure_view",
                    "role": "primary",
                    "purpose": "Show selected simulation structures across a spatial projection or volume-derived map with variable overlays.",
                    "reference_grounding": evidence_grounding(applied_elements, 0, "spatial semantic structure view"),
                },
                {
                    "view_id": "time_scale_strip",
                    "role": "companion",
                    "purpose": "Scrub snapshots, redshift, scale levels, or run phases while preserving the selected structure.",
                    "reference_grounding": evidence_grounding(applied_elements, 1, "phase/time strip linked to the primary structure"),
                },
                {
                    "view_id": "variable_relation_view",
                    "role": "companion",
                    "purpose": "Expose variable distributions, parameter relationships, or structure similarity for the current selection.",
                    "reference_grounding": evidence_grounding(applied_elements, 2, "hybrid relation overview"),
                },
                {
                    "view_id": "evidence_panel",
                    "role": "detail",
                    "purpose": "Show provenance, source snippets, caveats, and selected simulation statistics.",
                    "reference_grounding": "standard evidence trace policy",
                },
            ],
            "shared_state": ["selected_structure", "selected_snapshot", "selected_variable", "selected_evidence_route"],
            "linked_interactions": [
                {
                    "interaction_id": "select_structure_updates_context",
                    "source_view": "simulation_structure_view",
                    "target_views": ["time_scale_strip", "variable_relation_view", "evidence_panel"],
                    "shared_state": "selected_structure",
                },
                {
                    "interaction_id": "scrub_snapshot_updates_all_views",
                    "source_view": "time_scale_strip",
                    "target_views": ["simulation_structure_view", "variable_relation_view", "evidence_panel"],
                    "shared_state": "selected_snapshot",
                },
                {
                    "interaction_id": "select_variable_recolors_structure",
                    "source_view": "variable_relation_view",
                    "target_views": ["simulation_structure_view", "evidence_panel"],
                    "shared_state": "selected_variable",
                },
            ],
            "exploration_affordance": {
                "model": "guided_open_exploration",
                "default_state": "Show the dominant simulation structure, active time/scale context, and the most relevant variable evidence in one screen.",
                "entry_points": ["start from spatial structure", "start from time/scale state", "start from variable relation"],
                "analysis_routes": [
                    "structure -> time/scale change -> variable evidence",
                    "variable anomaly -> highlighted structures -> provenance",
                    "reference precedent -> adapted simulation interaction -> current caveat",
                ],
                "non_linear_guards": ["clear selection is always visible", "time/scale scrub preserves selected structure", "evidence is bounded and source-linked"],
            },
            "visual_style_system": {
                "style_intent": "scientific simulation analysis surface with dense but legible spatial, temporal, and variable evidence",
                "background_policy": "neutral light or cool slate-light workspace; avoid starfield decoration and generic dark dashboards",
                "palette_roles": {
                    "structure": "categorical structure colors",
                    "variable_value": "perceptually ordered ramp",
                    "reference_grounding": "secondary cool hue",
                    "uncertainty_or_caveat": "amber warning used sparingly",
                },
            },
        }

    if contains_any(text, ["bayesian", "uncertainty", "neural network", "prediction", "classification", "posterior", "error diagnosis"]):
        return {
            "domain_id": "model_uncertainty_diagnosis",
            "analysis_target": {
                "name": f"{title} uncertainty and prediction-error workspace",
                "supporting_patterns": ["predictions", "uncertainty", "model_components", "case_evidence"],
                "primary_patterns": ["uncertain cases", "error clusters", "model comparison"],
                "evidence_patterns": ["retrieved uncertainty-vis systems", "paper snippets", "case-level explanation traces"],
                "operational_definition": {
                    "entity": "sample, class, model/layer, uncertainty estimate, or error cluster",
                    "grain": "one prediction case, one uncertainty group, or one model comparison cell",
                    "states": ["selected_case", "selected_model", "selected_class", "selected_evidence_route"],
                    "primary_user_actions": ["select an uncertain case", "compare model/class behavior", "inspect explanation evidence", "trace error causes"],
                    "success_observations": ["user can identify which cases are uncertain, how errors cluster, and what model evidence explains them"],
                    "excluded_interpretations": ["not a leaderboard", "not a single confusion matrix", "not a KPI dashboard"],
                },
            },
            "primary_question": f"How can analysts compare prediction behavior, uncertainty, and case-level explanations in {title}?",
            "primary_visual_object": "A model-diagnosis workspace where uncertain cases, model/class comparisons, explanation traces, and paper-grounded design patterns are linked.",
            "data_task_encoding_mapping": [
                {
                    "field_or_concept": "prediction cases",
                    "task": "locate errors and ambiguous outcomes",
                    "encoding": "case map or ranked uncertainty strip with selection-linked details",
                    "reason": "model diagnosis begins with concrete cases rather than aggregate scores",
                },
                {
                    "field_or_concept": "uncertainty distributions",
                    "task": "compare confidence, posterior spread, or disagreement",
                    "encoding": "distribution glyphs or interval bands tied to selected class/model",
                    "reason": "uncertainty must be shown as structure, not collapsed into one number",
                },
                {
                    "field_or_concept": "model/class relationships",
                    "task": "diagnose where predictions diverge",
                    "encoding": "model-class matrix or relation overview with error highlighting",
                    "reason": "comparison across model components reveals systematic failure modes",
                },
                {
                    "field_or_concept": "explanation evidence",
                    "task": "connect a selected case to the reason it is uncertain or wrong",
                    "encoding": "bounded evidence panel with feature, layer, or source snippets",
                    "reason": "analysts need traceable evidence before trusting diagnosis",
                },
            ],
            "why_not_dashboard": "The work is model diagnosis: users must move between uncertain cases, class/model relations, distributions, and explanation evidence. A dashboard of aggregate accuracy metrics would hide these links.",
            "view_graph": [
                {
                    "view_id": "case_uncertainty_view",
                    "role": "primary",
                    "purpose": "Show prediction cases or clusters positioned by uncertainty, error type, and selected class/model context.",
                    "reference_grounding": evidence_grounding(applied_elements, 0, "uncertainty layer as secondary evidence"),
                },
                {
                    "view_id": "model_class_matrix",
                    "role": "companion",
                    "purpose": "Compare models, classes, or layers with error and uncertainty highlighting.",
                    "reference_grounding": evidence_grounding(applied_elements, 1, "hybrid relation overview"),
                },
                {
                    "view_id": "case_explanation_view",
                    "role": "companion",
                    "purpose": "Show selected posterior, feature/layer attribution, or disagreement traces for the active case.",
                    "reference_grounding": evidence_grounding(applied_elements, 2, "coordinated overview-detail evidence workflow"),
                },
                {
                    "view_id": "evidence_panel",
                    "role": "detail",
                    "purpose": "Show paper snippets, provenance, caveats, and the current diagnostic rationale.",
                    "reference_grounding": "standard evidence trace policy",
                },
            ],
            "shared_state": ["selected_case", "selected_model", "selected_class", "selected_evidence_route"],
            "linked_interactions": [
                {
                    "interaction_id": "select_case_updates_diagnosis",
                    "source_view": "case_uncertainty_view",
                    "target_views": ["model_class_matrix", "case_explanation_view", "evidence_panel"],
                    "shared_state": "selected_case",
                },
                {
                    "interaction_id": "select_model_class_filters_cases",
                    "source_view": "model_class_matrix",
                    "target_views": ["case_uncertainty_view", "case_explanation_view", "evidence_panel"],
                    "shared_state": "selected_model",
                },
                {
                    "interaction_id": "select_explanation_updates_evidence",
                    "source_view": "case_explanation_view",
                    "target_views": ["case_uncertainty_view", "evidence_panel"],
                    "shared_state": "selected_evidence_route",
                },
            ],
            "exploration_affordance": {
                "model": "guided_open_exploration",
                "default_state": "Show the highest-uncertainty cases, model/class relation overview, and one explanation route for the top selected case.",
                "entry_points": ["start from uncertain case", "start from model/class comparison", "start from explanation evidence"],
                "analysis_routes": [
                    "uncertain case -> model/class context -> explanation evidence",
                    "class anomaly -> case cluster -> uncertainty distribution",
                    "reference pattern -> adapted diagnosis interaction -> caveat",
                ],
                "non_linear_guards": ["clear selection is always visible", "aggregate metrics never replace case-level evidence", "uncertainty encodings stay linked to cases"],
            },
            "visual_style_system": {
                "style_intent": "model-diagnosis workspace with precise uncertainty marks, compact comparison structure, and calm evidence surfaces",
                "background_policy": "neutral light or cool gray; avoid generic ML dashboard styling and purple glow",
                "palette_roles": {
                    "error": "clear warm accent",
                    "uncertainty": "ordered blue-green or viridis-like ramp",
                    "reference_grounding": "secondary cool hue",
                    "evidence": "muted support tone",
                },
            },
        }

    return {
        "domain_id": "paper_grounded_design",
        "analysis_target": fallback_target,
        "primary_question": f"How can analysts explore the evidence structure around {compact(input_profile.get('title') or 'this input', 80)} using paper-grounded visual interaction patterns?",
        "primary_visual_object": "A reference-grounded evidence structure view: input keyword clusters, retrieved VIS precedents, and selected evidence are arranged as a single coordinated object.",
        "data_task_encoding_mapping": [
            {
                "field_or_concept": "input keywords",
                "task": "identify the analytical focus and branch routes",
                "encoding": "keyword-task clusters linked to retrieved references",
                "reason": "keeps the system grounded in the new paper/dataset rather than generic VIS inspiration",
            },
            {
                "field_or_concept": "retrieved reference patterns",
                "task": "adapt proven visual/interaction structures",
                "encoding": "reference pattern cards connected to view graph nodes",
                "reason": "makes paper learning auditable and reusable",
            },
            {
                "field_or_concept": "source evidence snippets",
                "task": "verify current selection and design rationale",
                "encoding": "bounded evidence panel with local scroll",
                "reason": "prevents unsupported design claims",
            },
        ],
        "why_not_dashboard": "The task is to design and inspect an analytical system structure. KPI cards or independent charts would not show how input concepts, retrieved VIS precedents, shared state, and evidence routes interact.",
        "view_graph": [
            {
                "view_id": "primary_structure_view",
                "role": "primary",
                "purpose": "Show the dominant analysis object and its key semantic/data structure.",
                "reference_grounding": evidence_grounding(applied_elements, 0, "coordinated overview-detail evidence workflow"),
            },
            {
                "view_id": "reference_pattern_view",
                "role": "companion",
                "purpose": "Expose which retrieved paper patterns are shaping the design and why.",
                "reference_grounding": evidence_grounding(applied_elements, 1, "paper-grounded reference pattern mapping"),
            },
            {
                "view_id": "keyword_task_view",
                "role": "companion",
                "purpose": "Organize extracted keywords into task and evidence groups.",
                "reference_grounding": "fallback_standard_basis.focus_context_linked_brush",
            },
            {
                "view_id": "evidence_panel",
                "role": "detail",
                "purpose": "Show source snippets, provenance, and current selection evidence.",
                "reference_grounding": "standard evidence trace policy",
            },
        ],
        "shared_state": ["selected_keyword_cluster", "selected_reference", "selected_entity_or_record", "selected_evidence_route"],
        "linked_interactions": [
            {
                "interaction_id": "select_keyword_updates_references",
                "source_view": "keyword_task_view",
                "target_views": ["reference_pattern_view", "evidence_panel"],
                "shared_state": "selected_keyword_cluster",
            },
            {
                "interaction_id": "select_reference_updates_workspace",
                "source_view": "reference_pattern_view",
                "target_views": ["primary_structure_view", "evidence_panel"],
                "shared_state": "selected_reference",
            },
            {
                "interaction_id": "clear_selection_resets_all_views",
                "source_view": "route_controls",
                "target_views": ["primary_structure_view", "reference_pattern_view", "keyword_task_view", "evidence_panel"],
                "shared_state": "selected_entity_or_record",
            },
        ],
        "exploration_affordance": {
            "model": "guided_open_exploration",
            "default_state": "Show the strongest keyword cluster, top retrieved references, and the proposed primary visual object simultaneously.",
            "entry_points": ["start from keyword cluster", "start from retrieved reference", "start from evidence route"],
            "analysis_routes": [
                "keyword -> references -> primary visual object",
                "reference -> borrowed element -> linked interaction",
                "entity/evidence -> companion view -> source trace",
            ],
            "non_linear_guards": ["no forced next/previous flow", "clear selection is always visible", "routes preserve shared state"],
        },
        "visual_style_system": {
            "style_intent": "precise research-system workspace with data/reference marks as the memorable visual object",
            "background_policy": "cool neutral or ink-on-white; no warm-paper or generic dark dashboard",
            "palette_roles": {
                "input_focus": "high-salience accent",
                "reference_grounding": "secondary cool hue",
                "evidence": "muted support tone",
                "uncertainty_or_caveat": "warning tone used sparingly",
            },
        },
    }


def build_contract(input_profile: dict[str, Any], keyword_profile: dict[str, Any], digest: dict[str, Any]) -> dict[str, Any]:
    keywords = keyword_profile.get("keywords") or []
    applied_elements = []
    for ref in digest.get("selected_references", [])[:4]:
        for elem in ref.get("borrowed_elements") or []:
            applied_elements.append(elem)
    if not applied_elements:
        applied_elements.append(
            {
                "source_paper_id": "standard_basis",
                "source_title": "standard_vis_design_basis.overview_detail_evidence",
                "borrowed_element": "overview + detail + raw evidence trace",
                "adapted_for_current_input": "Fallback because paper retrieval was weak.",
                "mapped_to_view_ids": ["primary_structure_view", "evidence_panel"],
                "mapped_to_interaction_ids": ["select_primary_updates_evidence"],
                "confidence": "fallback",
            }
        )

    blueprint = infer_design_blueprint(input_profile, keywords, applied_elements)
    return {
        "schema_version": "paper_grounded_e_idea_contract_v0.1",
        "created_by": "paper-grounded-vis-system-design",
        "input": {
            "type": input_profile.get("input_type"),
            "title": input_profile.get("title"),
            "path": input_profile.get("input_path"),
            "description": input_profile.get("description"),
        },
        "mechanism_context": {
            "generation": {"mechanism": "E_data_driven_with_paper_grounding"},
            "data_driven": {
                "domain_id": blueprint["domain_id"],
                "analysis_target": blueprint["analysis_target"],
                "primary_question": blueprint["primary_question"],
                "primary_visual_object": blueprint["primary_visual_object"],
                "data_task_encoding_mapping": blueprint["data_task_encoding_mapping"],
                "why_not_dashboard": blueprint["why_not_dashboard"],
                "coordinated_workspace": {
                    "view_graph": blueprint["view_graph"],
                    "shared_state": blueprint["shared_state"],
                    "linked_interactions": blueprint["linked_interactions"],
                },
                "exploration_affordance": blueprint["exploration_affordance"],
                "visual_style_system": blueprint["visual_style_system"],
                "reference_learning": {
                    "retrieval_status": digest.get("retrieval_status"),
                    "retrieval_mode": digest.get("retrieval_mode"),
                    "applied_elements": applied_elements,
                    "unused_references": [],
                    "coverage_summary": digest.get("coverage_summary"),
                },
                "data_provenance": {
                    "input_path": input_profile.get("input_path"),
                    "paper_db": "data/index.db",
                    "papers_dir": "data/papers",
                    "retrieval_query": keyword_profile.get("retrieval_query"),
                    "keywords": keywords,
                },
            },
        },
    }


def build_visual_spec(contract: dict[str, Any], digest: dict[str, Any]) -> dict[str, Any]:
    ctx = contract["mechanism_context"]["data_driven"]
    style = ctx.get("visual_style_system") or {}
    palette_roles = style.get("palette_roles") or {
        "input_focus": "high-salience accent",
        "reference_grounding": "secondary cool hue",
        "evidence": "muted support tone",
        "uncertainty_or_caveat": "warning tone used sparingly",
    }
    return {
        "schema_version": "paper_grounded_visual_system_spec_v0.1",
        "created_by": "paper-grounded-vis-system-design",
        "domain_id": ctx.get("domain_id"),
        "analysis_target": ctx["analysis_target"],
        "primary_question": ctx["primary_question"],
        "primary_visual_object": ctx.get("primary_visual_object"),
        "view_graph": ctx["coordinated_workspace"]["view_graph"],
        "shared_state": ctx["coordinated_workspace"]["shared_state"],
        "linked_interactions": ctx["coordinated_workspace"]["linked_interactions"],
        "default_state": ctx["exploration_affordance"]["default_state"],
        "guided_open_exploration": ctx["exploration_affordance"],
        "viewport_contract": {
            "primary_viewport": "1920x1080",
            "validation_viewport": "1440x810",
            "page_level_scroll": "forbidden_on_initial_load",
            "local_scroll": "allowed_inside_bounded_evidence_panels",
            "required_first_screen_view_ids": [view["view_id"] for view in ctx["coordinated_workspace"]["view_graph"]],
        },
        "visual_style_system": {
            "style_intent": style.get("style_intent") or "precise research-system workspace with data/reference marks as the memorable visual object",
            "background_policy": style.get("background_policy") or "cool neutral or ink-on-white; no warm-paper or generic dark dashboard",
            "palette_roles": palette_roles,
            "forbidden_styles_checked": ["beige/cream/sand", "paper grid", "generic dark KPI dashboard", "purple gradient/glow/blur"],
            "typography_policy": "compact labels, no hero text, stable panel headings",
            "density_policy": "desktop analytical density with bounded local scroll",
        },
        "reference_learning_adapted": ctx["reference_learning"],
        "retrieved_reference_count": len(digest.get("selected_references") or []),
    }


def write_reference_report(path: Path, input_profile: dict[str, Any], keyword_profile: dict[str, Any], digest: dict[str, Any]) -> None:
    lines = [
        "# VIS Reference Report",
        "",
        f"Input: {input_profile.get('title')}",
        f"Retrieval mode: {digest.get('retrieval_mode')}",
        f"Query: `{keyword_profile.get('retrieval_query')}`",
        "",
        "## Keywords",
        "",
        ", ".join(keyword_profile.get("keywords") or []),
        "",
        "## Selected References",
        "",
    ]
    for ref in digest.get("selected_references") or []:
        lines.append(f"### {ref.get('rank')}. {ref.get('title')}")
        lines.append("")
        lines.append(f"- Paper id: `{ref.get('paper_id')}`")
        lines.append(f"- Score: `{ref.get('score')}`")
        lines.append(f"- Meta: `{ref.get('meta_path')}`")
        lines.append(f"- Abstract: {ref.get('abstract_snippet')}")
        lines.append(f"- L3: {ref.get('l3_snippet')}")
        lines.append("- Borrowed elements:")
        for elem in ref.get("borrowed_elements") or []:
            lines.append(f"  - {elem.get('borrowed_element')} -> views {elem.get('mapped_to_view_ids')}")
        lines.append("")
    write_text(path, "\n".join(lines).rstrip() + "\n")


def write_rq_selection(path: Path, input_profile: dict[str, Any], contract: dict[str, Any]) -> None:
    ctx = contract["mechanism_context"]["data_driven"]
    text = f"""# RQ Selection

Selected primary question:

{ctx["primary_question"]}

Reason:

The input target is better served by a coordinated workspace than by a single chart because the system must connect input keywords, retrieved VIS references, design adaptations, and source evidence.

Rejected alternatives:

- Pure literature list: rejected because it does not produce an analytical system.
- KPI dashboard: rejected because the task is not metric monitoring.
- Independent chart collage: rejected because reference learning and evidence routes need shared state.
"""
    write_text(path, text)


def write_design_spec(path: Path, input_profile: dict[str, Any], contract: dict[str, Any], visual_spec: dict[str, Any], digest: dict[str, Any]) -> None:
    ctx = contract["mechanism_context"]["data_driven"]
    lines = [
        "# Paper-Grounded Visual Analytics System Design",
        "",
        "## Input Target",
        "",
        f"- Title: {input_profile.get('title')}",
        f"- Type: {input_profile.get('input_type')}",
        f"- Path: `{input_profile.get('input_path')}`",
        "",
        "## Retrieval Grounding",
        "",
        f"- Retrieval status: `{digest.get('retrieval_status')}`",
        f"- Retrieval mode: `{digest.get('retrieval_mode')}`",
        f"- Query: `{digest.get('query')}`",
        "",
    ]
    for ref in (digest.get("selected_references") or [])[:5]:
        lines.append(f"- `{ref.get('paper_id')}` {ref.get('title')}")
        for elem in ref.get("borrowed_elements") or []:
            lines.append(f"  - Borrow: {elem.get('borrowed_element')}")
    lines.extend(
        [
            "",
            "## Analysis Target",
            "",
            ctx["analysis_target"]["name"],
            "",
            "## Primary Visual Object",
            "",
            ctx.get("primary_visual_object") or "A reference-grounded evidence structure view with linked references, tasks, and evidence.",
            "",
            "## Data-Task-Encoding Mapping",
            "",
        ]
    )
    for mapping in ctx["data_task_encoding_mapping"]:
        lines.append(f"- {mapping['field_or_concept']}: {mapping['task']} -> {mapping['encoding']} ({mapping['reason']})")
    lines.extend(["", "## View Graph", ""])
    for view in visual_spec["view_graph"]:
        lines.append(f"- `{view['view_id']}` ({view['role']}): {view['purpose']}")
    lines.extend(["", "## Linked Interactions", ""])
    for interaction in visual_spec["linked_interactions"]:
        lines.append(f"- `{interaction['interaction_id']}`: {interaction['source_view']} updates {', '.join(interaction['target_views'])}")
    lines.extend(
        [
            "",
            "## Guided Open Exploration",
            "",
            f"Default state: {visual_spec['default_state']}",
            "",
            "Entry routes are optional branches, not a forced tutorial. Users can start from keywords, references, or evidence routes, and can clear selection at any time.",
            "",
            "## Visual Style System",
            "",
            f"- Intent: {visual_spec['visual_style_system']['style_intent']}",
            f"- Background: {visual_spec['visual_style_system']['background_policy']}",
            f"- Forbidden styles checked: {', '.join(visual_spec['visual_style_system']['forbidden_styles_checked'])}",
            "",
            "## Viewport QA Plan",
            "",
            "Fit the initial workspace at `1920x1080` and `1440x810` without page-level scrolling. Put long evidence lists in bounded local scroll panels.",
            "",
            "## Provenance And Evidence Policy",
            "",
            "Every borrowed design element must point back to a retrieved `meta.json`, `paper.md`, or fallback basis entry. Every data claim in a future frontend must be computed from real input data or explicitly marked unavailable.",
        ]
    )
    write_text(path, "\n".join(lines).rstrip() + "\n")


def run(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    papers_dir = Path(args.papers_dir).resolve()
    db_path = Path(args.paper_db).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    input_profile = detect_input(args.input, args.description or "")
    keyword_profile = extract_keywords(input_profile["text_for_keywords"], args.keyword_count)
    local = scan_local_papers(papers_dir)

    fts = search_fts(db_path, keyword_profile.get("query_terms") or [], args.top_k, input_profile.get("source_paper_id") or "")
    semantic: list[dict[str, Any]] = []
    retrieval_mode = "fts_only"
    if args.embedding_api_base or os.getenv("PAPER_EMBED_API_BASE"):
        try:
            semantic = search_vectors(args, keyword_profile["retrieval_query"], input_profile.get("source_paper_id") or "", args.top_k)
            retrieval_mode = "hybrid_fts_semantic" if fts else "semantic_only"
        except Exception as exc:  # noqa: BLE001
            retrieval_mode = f"fts_only_semantic_failed:{type(exc).__name__}"
            print(f"[warn] semantic search failed: {exc}", file=sys.stderr)

    results = fuse_results(fts, semantic, local, args.top_k)
    digest = build_digest(results, input_profile, keyword_profile, retrieval_mode)
    standard_basis = build_standard_basis()
    contract = build_contract(input_profile, keyword_profile, digest)
    visual_spec = build_visual_spec(contract, digest)

    write_json(run_dir / "stage0_input" / "input_profile.json", input_profile)
    write_json(run_dir / "stage0_input" / "keyword_profile.json", keyword_profile)
    write_yaml(run_dir / "stage2_idea" / "vis_reference_digest.yaml", digest)
    write_json(run_dir / "stage2_idea" / "vis_reference_digest.json", digest)
    write_reference_report(run_dir / "stage2_idea" / "vis_reference_report.md", input_profile, keyword_profile, digest)
    write_yaml(run_dir / "stage2_idea" / "standard_vis_design_basis.yaml", standard_basis)
    write_rq_selection(run_dir / "stage2_idea" / "rq_selection.md", input_profile, contract)
    write_yaml(run_dir / "stage2_idea" / "idea.yaml", contract)
    write_yaml(run_dir / "stage2_idea" / "e_idea_contract.yaml", contract)
    write_json(run_dir / "stage2_idea" / "e_idea_contract.json", contract)
    write_json(run_dir / "stage3_visual_spec" / "visual_system_spec.json", visual_spec)
    write_design_spec(run_dir / "artifacts" / "design_spec.md", input_profile, contract, visual_spec, digest)
    write_json(
        run_dir / "artifacts" / "run_manifest.json",
        {
            "created_at": now_iso(),
            "run_dir": str(run_dir),
            "paper_db": str(db_path),
            "papers_dir": str(papers_dir),
            "retrieval_mode": retrieval_mode,
            "selected_reference_count": len(digest.get("selected_references") or []),
            "outputs": [
                "stage0_input/input_profile.json",
                "stage0_input/keyword_profile.json",
                "stage2_idea/vis_reference_digest.yaml",
                "stage2_idea/vis_reference_digest.json",
                "stage2_idea/vis_reference_report.md",
                "stage2_idea/standard_vis_design_basis.yaml",
                "stage2_idea/rq_selection.md",
                "stage2_idea/idea.yaml",
                "stage2_idea/e_idea_contract.yaml",
                "stage2_idea/e_idea_contract.json",
                "stage3_visual_spec/visual_system_spec.json",
                "artifacts/design_spec.md",
            ],
        },
    )
    print(json.dumps({"run_dir": str(run_dir), "retrieval_mode": retrieval_mode, "references": len(results)}, ensure_ascii=False, indent=2))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Paper meta/dir/md, dataset file/dir, or free-text idea.")
    parser.add_argument("--description", default="")
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--paper-db", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--keyword-count", type=int, default=18)
    parser.add_argument("--embedding-api-base", default=os.getenv("PAPER_EMBED_API_BASE"))
    parser.add_argument("--embedding-api-key", default=None)
    parser.add_argument("--embedding-model", default=os.getenv("PAPER_EMBED_MODEL", DEFAULT_EMBED_MODEL))
    parser.add_argument("--embedding-timeout", type=int, default=180)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv or sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
