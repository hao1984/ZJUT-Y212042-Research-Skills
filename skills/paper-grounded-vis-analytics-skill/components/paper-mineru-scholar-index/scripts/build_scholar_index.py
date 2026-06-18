#!/usr/bin/env python3
"""Build a ScholarAIO-style SQLite/FAISS paper index from meta.json files."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_EMBED_MODEL = "qwen3-0.6B-embedding"


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hash_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:12]


def citation_display(value: Any) -> str:
    if isinstance(value, dict):
        nums = []
        for item in value.values():
            try:
                nums.append(int(item))
            except Exception:  # noqa: BLE001
                pass
        return str(max(nums) if nums else 0)
    if value in (None, ""):
        return "0"
    return str(value)


def authors_display(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item)
    return str(value or "")


def embedding_text(meta: dict[str, Any]) -> str:
    return (
        f"Title: {meta.get('title') or ''}\n\n"
        f"Abstract:\n{meta.get('abstract') or ''}\n\n"
        f"Summary:\n{meta.get('l3_conclusion') or ''}"
    ).strip()


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


def embed_openai(args: argparse.Namespace, texts: list[str]) -> list[list[float]]:
    api_base = args.embedding_api_base or os.getenv("PAPER_EMBED_API_BASE")
    api_key = args.embedding_api_key or os.getenv("PAPER_EMBED_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_base:
        raise RuntimeError("missing --embedding-api-base or PAPER_EMBED_API_BASE")
    endpoint = api_base.rstrip("/") + "/embeddings"
    vectors: list[list[float]] = []
    for start in range(0, len(texts), args.embedding_batch_size):
        batch = texts[start : start + args.embedding_batch_size]
        payload = {"model": args.embedding_model, "input": batch}
        for attempt in range(args.max_retries):
            try:
                data = http_json("POST", endpoint, payload, api_key=api_key, timeout=args.embedding_timeout)
                items = sorted(data["data"], key=lambda item: item.get("index", 0))
                vectors.extend([list(map(float, item["embedding"])) for item in items])
                break
            except Exception as exc:  # noqa: BLE001
                if attempt + 1 >= args.max_retries:
                    raise
                print(f"[warn] embedding batch failed: {exc}", file=sys.stderr)
                time.sleep(2 ** attempt)
    return vectors


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm <= 0:
        return vector
    return [x / norm for x in vector]


def vector_blob(vector: list[float]) -> bytes:
    return struct.pack("<" + "f" * len(vector), *vector)


def iter_papers(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    rows = []
    for meta_path in sorted(root.glob("*/meta.json"), key=lambda p: str(p).lower()):
        if meta_path.name.startswith("._"):
            continue
        paper_dir = meta_path.parent
        if not (paper_dir / "paper.md").exists():
            continue
        meta = load_json(meta_path)
        if not meta.get("id"):
            raise RuntimeError(f"missing id in {meta_path}")
        rows.append((paper_dir, meta))
    return rows


def recreate_schema(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    for table in ("papers", "paper_vectors", "papers_hash", "papers_registry", "citations"):
        cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute(
        """
        CREATE TABLE citations (
            source_id   TEXT NOT NULL,
            target_doi  TEXT NOT NULL,
            target_id   TEXT,
            PRIMARY KEY (source_id, target_doi)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE paper_vectors (
            paper_id     TEXT PRIMARY KEY,
            embedding    BLOB NOT NULL,
            content_hash TEXT NOT NULL DEFAULT ''
        )
        """
    )
    cur.execute(
        """
        CREATE VIRTUAL TABLE papers USING fts5(
            paper_id       UNINDEXED,
            title,
            authors,
            year,
            journal,
            abstract,
            conclusion,
            doi            UNINDEXED,
            paper_type     UNINDEXED,
            citation_count UNINDEXED,
            md_path        UNINDEXED,
            tokenize       = 'unicode61'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE papers_hash (
            paper_id     TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE papers_registry (
            id                   TEXT PRIMARY KEY,
            dir_name             TEXT NOT NULL UNIQUE,
            title                TEXT,
            doi                  TEXT,
            publication_number   TEXT,
            year                 INTEGER,
            first_author         TEXT
        )
        """
    )
    cur.execute("CREATE INDEX idx_cit_target_doi ON citations(target_doi)")
    cur.execute("CREATE INDEX idx_cit_target_id ON citations(target_id) WHERE target_id IS NOT NULL")
    cur.execute("CREATE UNIQUE INDEX idx_registry_doi ON papers_registry(doi) WHERE doi IS NOT NULL AND doi != ''")
    cur.execute(
        "CREATE UNIQUE INDEX idx_registry_publication_number ON papers_registry(publication_number) "
        "WHERE publication_number IS NOT NULL AND publication_number != ''"
    )
    con.commit()


def insert_rows(
    con: sqlite3.Connection,
    paper_rows: list[tuple[Path, dict[str, Any]]],
    vectors: list[list[float]] | None,
    hashes: list[str],
) -> None:
    cur = con.cursor()
    for idx, (paper_dir, meta) in enumerate(paper_rows):
        paper_id = str(meta["id"])
        md_path = str((paper_dir / "paper.md").resolve())
        cur.execute(
            """
            INSERT INTO papers (
                paper_id, title, authors, year, journal, abstract, conclusion, doi,
                paper_type, citation_count, md_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id,
                meta.get("title") or "",
                authors_display(meta.get("authors")),
                "" if meta.get("year") is None else str(meta.get("year")),
                meta.get("journal") or "",
                meta.get("abstract") or "",
                meta.get("l3_conclusion") or "",
                meta.get("doi") or "",
                meta.get("paper_type") or "",
                citation_display(meta.get("citation_count")),
                md_path,
            ),
        )
        cur.execute(
            "INSERT INTO papers_hash (paper_id, content_hash) VALUES (?, ?)",
            (paper_id, hashes[idx]),
        )
        cur.execute(
            """
            INSERT INTO papers_registry (
                id, dir_name, title, doi, publication_number, year, first_author
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id,
                paper_dir.name,
                meta.get("title") or "",
                meta.get("doi") or "",
                (meta.get("ids") or {}).get("publication_number", ""),
                meta.get("year"),
                meta.get("first_author") or "",
            ),
        )
        for target_doi in meta.get("references") or []:
            target_doi = str(target_doi).lower().strip()
            if target_doi:
                cur.execute(
                    "INSERT OR IGNORE INTO citations (source_id, target_doi, target_id) VALUES (?, ?, ?)",
                    (paper_id, target_doi, None),
                )
        if vectors is not None:
            cur.execute(
                "INSERT INTO paper_vectors (paper_id, embedding, content_hash) VALUES (?, ?, ?)",
                (paper_id, sqlite3.Binary(vector_blob(vectors[idx])), hashes[idx]),
            )
    con.commit()


def write_faiss(args: argparse.Namespace, ids: list[str], vectors: list[list[float]]) -> bool:
    try:
        import faiss  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] faiss/numpy not available; skipped FAISS output: {exc}", file=sys.stderr)
        return False
    matrix = np.asarray(vectors, dtype="float32")
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, str(args.faiss_index))
    write_json(Path(args.faiss_ids), ids)
    return True


def run(args: argparse.Namespace) -> int:
    papers_dir = Path(args.papers_dir).resolve()
    db_path = Path(args.db).resolve()
    faiss_index = Path(args.faiss_index or db_path.with_name("faiss.index")).resolve()
    faiss_ids = Path(args.faiss_ids or db_path.with_name("faiss_ids.json")).resolve()
    args.faiss_index = str(faiss_index)
    args.faiss_ids = str(faiss_ids)
    if db_path.exists() and not args.rebuild:
        raise FileExistsError(f"{db_path} exists; pass --rebuild")

    paper_rows = iter_papers(papers_dir)
    if not paper_rows:
        raise FileNotFoundError(f"no meta.json + paper.md pairs under {papers_dir}")
    texts = [embedding_text(meta) for _, meta in paper_rows]
    hashes = [hash_text(text) for text in texts]

    vectors: list[list[float]] | None = None
    if not args.skip_embeddings:
        print(f"[embed] model={args.embedding_model} papers={len(texts)}")
        vectors = embed_openai(args, texts)
        if len(vectors) != len(texts):
            raise RuntimeError(f"embedding count mismatch: got {len(vectors)}, expected {len(texts)}")
        if args.normalize:
            vectors = [normalize_vector(vector) for vector in vectors]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    recreate_schema(con)
    insert_rows(con, paper_rows, vectors, hashes)
    con.close()

    faiss_written = False
    if vectors is not None and not args.no_faiss:
        faiss_written = write_faiss(args, [str(meta["id"]) for _, meta in paper_rows], vectors)
    manifest = {
        "paper_count": len(paper_rows),
        "db": str(db_path),
        "embedding_model": args.embedding_model,
        "vectors_written": vectors is not None,
        "vector_dim": len(vectors[0]) if vectors else None,
        "faiss_written": faiss_written,
        "faiss_index": str(faiss_index) if faiss_written else "",
        "faiss_ids": str(faiss_ids) if faiss_written else "",
    }
    write_json(db_path.with_name("index_manifest.json"), manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--embedding-api-base", default=os.getenv("PAPER_EMBED_API_BASE"))
    parser.add_argument("--embedding-api-key", default=None)
    parser.add_argument("--embedding-model", default=os.getenv("PAPER_EMBED_MODEL", DEFAULT_EMBED_MODEL))
    parser.add_argument("--embedding-batch-size", type=int, default=16)
    parser.add_argument("--embedding-timeout", type=int, default=180)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--normalize", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--no-faiss", action="store_true")
    parser.add_argument("--faiss-index", default=None)
    parser.add_argument("--faiss-ids", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv or sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
