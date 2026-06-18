#!/usr/bin/env python3
"""Create or refresh ScholarAIO-style meta.json files for paper directories."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(read_text(path))


def normalize_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{4,}", "\n\n\n", value).strip()


def compact_for_prompt(value: str, limit: int) -> str:
    value = normalize_text(value)
    if len(value) <= limit:
        return value
    head = int(limit * 0.65)
    tail = limit - head
    return value[:head].rstrip() + "\n\n...[middle omitted]...\n\n" + value[-tail:].lstrip()


def slugify(value: str, fallback: str = "paper") -> str:
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE).strip()
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip(".-")
    return (value or fallback)[:180]


def parse_author_lastname(author: str) -> str:
    author = author.strip()
    if not author:
        return ""
    if "," in author:
        return author.split(",", 1)[0].strip()
    parts = author.split()
    return parts[-1] if parts else author


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines()[:160]:
        stripped = line.strip()
        if not stripped or stripped.startswith(("!", "|", "```")):
            continue
        heading = re.match(r"^#{1,3}\s+(.+?)\s*$", stripped)
        if heading:
            title = re.sub(r"\s+", " ", heading.group(1)).strip()
            if 4 <= len(title) <= 300 and title.lower() not in {"abstract", "introduction"}:
                return title
        if 12 <= len(stripped) <= 260 and not re.match(r"^(abstract|keywords|doi)\b", stripped, re.I):
            return re.sub(r"\s+", " ", stripped).strip("# ").strip()
    return fallback


def extract_section(text: str, names: list[str], max_chars: int) -> str:
    escaped = "|".join(re.escape(name) for name in names)
    heading = re.compile(
        rf"(?ims)^#{{1,6}}\s*(?:{escaped})\s*:?\s*$\n(?P<body>.*?)(?=^\s*#{{1,6}}\s+\S|\Z)"
    )
    match = heading.search(text)
    if match:
        return normalize_text(match.group("body"))[:max_chars].strip()
    plain = re.compile(
        rf"(?ims)^\s*(?:{escaped})\s*:?\s*$\n(?P<body>.*?)(?=^\s*(?:keywords|introduction|1\.|#)\b|\Z)"
    )
    match = plain.search(text)
    if match:
        return normalize_text(match.group("body"))[:max_chars].strip()
    return ""


def extract_abstract(text: str, max_chars: int) -> str:
    abstract = extract_section(text, ["Abstract", "ABSTRACT", "Summary", "SUMMARY"], max_chars)
    if abstract:
        return abstract
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for paragraph in paragraphs[:20]:
        if paragraph.startswith(("#", "!", "|")):
            continue
        if 120 <= len(paragraph) <= max_chars:
            return paragraph[:max_chars].strip()
    return ""


def extract_doi(text: str) -> str:
    match = DOI_RE.search(text)
    if not match:
        return ""
    return match.group(0).rstrip(").,;]")


def extract_toc(text: str) -> list[dict[str, Any]]:
    toc: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if not match:
            continue
        title = re.sub(r"\s+", " ", match.group(2)).strip()
        if title.lower() in {"abstract"}:
            continue
        toc.append({"line": line_no, "level": len(match.group(1)), "title": title})
    return toc


def http_json(method: str, url: str, payload: dict[str, Any] | None = None, api_key: str | None = None, timeout: int = 120) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def crossref_by_doi(doi: str, timeout: int) -> dict[str, Any]:
    if not doi:
        return {}
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    data = http_json("GET", url, timeout=timeout)
    msg = data.get("message") or {}
    authors = []
    for item in msg.get("author") or []:
        given = item.get("given") or ""
        family = item.get("family") or ""
        name = " ".join(part for part in (given, family) if part).strip()
        if name:
            authors.append(name)
    year = None
    for key in ("published-print", "published-online", "issued"):
        parts = (((msg.get(key) or {}).get("date-parts") or [[]])[0] or [])
        if parts:
            year = parts[0]
            break
    return {
        "title": (msg.get("title") or [""])[0],
        "authors": authors,
        "year": year,
        "journal": (msg.get("container-title") or [""])[0],
        "paper_type": msg.get("type") or "",
        "volume": msg.get("volume") or "",
        "issue": msg.get("issue") or "",
        "pages": msg.get("page") or "",
        "publisher": msg.get("publisher") or "",
        "issn": (msg.get("ISSN") or [""])[0],
        "citation_count": {"crossref": int(msg.get("is-referenced-by-count") or 0)},
        "references": [
            ref.get("DOI", "").lower()
            for ref in (msg.get("reference") or [])
            if ref.get("DOI")
        ],
    }


def semantic_scholar_by_doi(doi: str, timeout: int) -> dict[str, Any]:
    if not doi:
        return {}
    fields = "paperId,url,citationCount,references.externalIds"
    url = "https://api.semanticscholar.org/graph/v1/paper/DOI:" + urllib.parse.quote(doi, safe="") + "?fields=" + fields
    data = http_json("GET", url, timeout=timeout)
    refs = []
    for ref in data.get("references") or []:
        doi_ref = ((ref.get("externalIds") or {}).get("DOI") or "").lower()
        if doi_ref:
            refs.append(doi_ref)
    return {
        "ids": {
            "semantic_scholar": data.get("paperId") or "",
            "semantic_scholar_url": data.get("url") or "",
        },
        "citation_count": {"semantic_scholar": int(data.get("citationCount") or 0)},
        "references": refs,
    }


def openalex_by_doi(doi: str, timeout: int) -> dict[str, Any]:
    if not doi:
        return {}
    url = "https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi, safe="/:")
    data = http_json("GET", url, timeout=timeout)
    return {
        "ids": {
            "openalex": data.get("id") or "",
            "openalex_url": data.get("id") or "",
        },
        "citation_count": {"openalex": int(data.get("cited_by_count") or 0)},
    }


def call_chat(args: argparse.Namespace, messages: list[dict[str, str]]) -> str | None:
    if not args.llm_api_base or not args.llm_model:
        return None
    api_key = args.llm_api_key or os.getenv("PAPER_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    endpoint = args.llm_api_base.rstrip("/") + "/chat/completions"
    payload = {"model": args.llm_model, "messages": messages, "temperature": args.llm_temperature}
    for attempt in range(args.max_retries):
        try:
            data = http_json("POST", endpoint, payload=payload, api_key=api_key, timeout=args.llm_timeout)
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            if attempt + 1 >= args.max_retries:
                print(f"[warn] LLM call failed: {exc}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)
    return None


def build_l3(args: argparse.Namespace, title: str, abstract: str, toc: list[dict[str, Any]], full_text: str) -> tuple[str, str]:
    source = compact_for_prompt(full_text, args.summary_max_chars)
    prompt = (
        "Generate a grounded academic paper summary/evaluation for retrieval. "
        "Use only the supplied paper text. Cover contribution, method, evidence, findings, limitations, and why it matters. "
        "Return one concise paragraph in English unless the paper is Chinese.\n\n"
        f"Title: {title}\n\n"
        f"Abstract:\n{abstract or 'not found'}\n\n"
        f"TOC:\n{json.dumps(toc[:30], ensure_ascii=False)}\n\n"
        f"Paper Markdown:\n{source}"
    )
    content = call_chat(
        args,
        [
            {"role": "system", "content": "Ground every claim in the supplied paper text."},
            {"role": "user", "content": prompt},
        ],
    )
    if content:
        return content, "llm"
    conclusion = extract_section(full_text, ["Conclusion", "Conclusions", "CONCLUSION", "CONCLUSIONS"], 3000)
    if conclusion:
        return conclusion, "toc"
    return abstract[:2000], "heuristic"


def merge_dict(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    for key, value in update.items():
        if value in ("", None, [], {}):
            continue
        if key == "citation_count":
            existing = base.get(key) if isinstance(base.get(key), dict) else {}
            merged = dict(existing)
            merged.update(value)
            base[key] = merged
        elif key == "ids":
            existing = base.get(key) if isinstance(base.get(key), dict) else {}
            merged = dict(existing)
            merged.update(value)
            base[key] = merged
        elif key == "references":
            existing = [str(x).lower() for x in base.get(key, [])]
            for ref in value:
                ref = str(ref).lower()
                if ref and ref not in existing:
                    existing.append(ref)
            base[key] = existing
        else:
            base[key] = value
    return base


def default_meta(existing: dict[str, Any]) -> dict[str, Any]:
    meta = dict(existing)
    meta.setdefault("id", str(uuid.uuid4()))
    meta.setdefault("title", "")
    meta.setdefault("authors", [])
    meta.setdefault("first_author", "")
    meta.setdefault("first_author_lastname", "")
    meta.setdefault("year", None)
    meta.setdefault("doi", "")
    meta.setdefault("journal", "")
    meta.setdefault("abstract", "")
    meta.setdefault("paper_type", "")
    meta.setdefault("volume", "")
    meta.setdefault("issue", "")
    meta.setdefault("pages", "")
    meta.setdefault("publisher", "")
    meta.setdefault("issn", "")
    meta.setdefault("citation_count", {})
    meta.setdefault("ids", {})
    meta.setdefault("source_file", "paper.md")
    meta.setdefault("extraction_method", "heuristic")
    meta.setdefault("api_sources", [])
    meta.setdefault("references", [])
    meta.setdefault("extracted_at", "")
    meta.setdefault("toc", [])
    meta.setdefault("l3_conclusion", "")
    meta.setdefault("l3_extraction_method", "")
    meta.setdefault("l3_extracted_at", "")
    return meta


def enrich_external(meta: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.no_external_api or not meta.get("doi"):
        return meta
    sources = list(meta.get("api_sources") or [])
    for name, fn in (
        ("crossref", crossref_by_doi),
        ("semantic_scholar", semantic_scholar_by_doi),
        ("openalex", openalex_by_doi),
    ):
        try:
            update = fn(str(meta["doi"]), args.api_timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {name} failed for {meta.get('doi')}: {exc}", file=sys.stderr)
            continue
        if update:
            merge_dict(meta, update)
            if name not in sources:
                sources.append(name)
    meta["api_sources"] = sources
    return meta


def final_fill(meta: dict[str, Any], paper_dir: Path) -> dict[str, Any]:
    authors = meta.get("authors") or []
    if isinstance(authors, str):
        authors = [a.strip() for a in re.split(r",|;|\band\b", authors) if a.strip()]
    meta["authors"] = authors
    if authors and not meta.get("first_author"):
        meta["first_author"] = authors[0]
    if meta.get("first_author") and not meta.get("first_author_lastname"):
        meta["first_author_lastname"] = parse_author_lastname(str(meta["first_author"]))
    doi = str(meta.get("doi") or "").lower()
    meta["doi"] = doi
    ids = meta.get("ids") if isinstance(meta.get("ids"), dict) else {}
    ids.setdefault("doi", doi)
    ids.setdefault("doi_url", f"https://doi.org/{doi}" if doi else "")
    ids.setdefault("semantic_scholar", "")
    ids.setdefault("semantic_scholar_url", "")
    ids.setdefault("openalex", "")
    ids.setdefault("openalex_url", "")
    meta["ids"] = ids
    if not meta.get("extracted_at"):
        meta["extracted_at"] = now_iso()
    meta["source_file"] = "paper.md"
    meta["_paper_dir"] = str(paper_dir)
    return meta


def target_dir_name(meta: dict[str, Any], fallback: str) -> str:
    author = meta.get("first_author_lastname") or parse_author_lastname(meta.get("first_author") or "")
    year = str(meta.get("year") or "unknown")
    title = meta.get("title") or fallback
    return slugify("-".join(part for part in (author, year, title) if part), fallback=fallback)


def process_paper(paper_dir: Path, args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    md_path = paper_dir / "paper.md"
    full_text = normalize_text(read_text(md_path))
    existing = load_json(paper_dir / "meta.json")
    meta = default_meta(existing)
    if not meta.get("title"):
        meta["title"] = extract_title(full_text, paper_dir.name)
    if not meta.get("abstract"):
        meta["abstract"] = extract_abstract(full_text, args.abstract_max_chars)
    if not meta.get("doi"):
        meta["doi"] = extract_doi(full_text)
    if not meta.get("toc"):
        meta["toc"] = extract_toc(full_text)
    if not meta.get("l3_conclusion") or args.force_l3:
        l3, method = build_l3(args, meta.get("title") or "", meta.get("abstract") or "", meta.get("toc") or [], full_text)
        meta["l3_conclusion"] = l3
        meta["l3_extraction_method"] = method
        meta["l3_extracted_at"] = now_iso()
    meta = enrich_external(meta, args)
    meta = final_fill(meta, paper_dir)
    if meta.get("doi") and meta.get("extraction_method") == "heuristic":
        meta["extraction_method"] = "doi"
    write_json(paper_dir / "meta.json", {k: v for k, v in meta.items() if not k.startswith("_")})
    return paper_dir, meta


def maybe_rename(paper_dir: Path, meta: dict[str, Any], args: argparse.Namespace) -> Path:
    if not args.rename_dirs:
        return paper_dir
    root = Path(args.papers_dir).resolve()
    wanted = target_dir_name(meta, paper_dir.name)
    target = root / wanted
    if target == paper_dir:
        return paper_dir
    if target.exists():
        target = root / f"{wanted}-{str(meta['id'])[:8]}"
    if target.exists():
        raise FileExistsError(target)
    shutil.move(str(paper_dir), str(target))
    return target


def iter_paper_dirs(root: Path) -> list[Path]:
    return sorted(
        [
            path for path in root.iterdir()
            if path.is_dir() and not path.name.startswith("._") and (path / "paper.md").exists()
        ],
        key=lambda p: p.name.lower(),
    )


def run(args: argparse.Namespace) -> int:
    root = Path(args.papers_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    processed = []
    for paper_dir in iter_paper_dirs(root):
        print(f"[meta] {paper_dir.name}")
        new_dir, meta = process_paper(paper_dir, args)
        final_dir = maybe_rename(new_dir, meta, args)
        if final_dir != new_dir:
            meta["_paper_dir"] = str(final_dir)
            write_json(final_dir / "meta.json", {k: v for k, v in meta.items() if not k.startswith("_")})
        processed.append(str(final_dir))
    print(json.dumps({"paper_count": len(processed), "paper_dirs": processed}, ensure_ascii=False, indent=2))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--llm-api-base", default=os.getenv("PAPER_LLM_API_BASE"))
    parser.add_argument("--llm-api-key", default=None)
    parser.add_argument("--llm-model", default=os.getenv("PAPER_LLM_MODEL"))
    parser.add_argument("--llm-temperature", type=float, default=0.2)
    parser.add_argument("--llm-timeout", type=int, default=180)
    parser.add_argument("--summary-max-chars", type=int, default=30000)
    parser.add_argument("--abstract-max-chars", type=int, default=5000)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--api-timeout", type=int, default=30)
    parser.add_argument("--no-external-api", action="store_true")
    parser.add_argument("--force-l3", action="store_true")
    parser.add_argument("--rename-dirs", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv or sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
