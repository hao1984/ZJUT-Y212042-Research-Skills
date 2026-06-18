#!/usr/bin/env python3
"""Parse local PDFs with MinerU Precision Extract batch upload.

The script normalizes each completed MinerU zip into:

  <out-dir>/<paper_id>/paper.pdf
  <out-dir>/<paper_id>/paper.md
  <out-dir>/<paper_id>/images/
  <out-dir>/<paper_id>/mineru_raw/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


PRECISION_BASE = "https://mineru.net/api/v4"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp"}


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


def slugify(value: str, fallback: str = "paper") -> str:
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE).strip().lower()
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip(".-")
    return (value or fallback)[:120]


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:10]


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "*/*"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def require_success(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("code") != 0:
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    return response.get("data") or {}


def put_file(upload_url: str, path: Path, timeout: int) -> None:
    data = path.read_bytes()
    req = urllib.request.Request(upload_url, data=data, method="PUT")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"upload failed for {path}: HTTP {resp.status}")


def download(url: str, path: Path, timeout: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        path.write_bytes(resp.read())


def safe_extract(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    root = out_dir.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (out_dir / member.filename).resolve()
            if not str(target).startswith(str(root)):
                raise RuntimeError(f"zip member escapes output dir: {member.filename}")
            archive.extract(member, out_dir)


def collect_pdfs(args: argparse.Namespace) -> list[Path]:
    paths = [Path(p).resolve() for p in args.pdf]
    if args.input_dir:
        paths.extend(Path(args.input_dir).resolve().rglob("*.pdf"))
    unique: dict[str, Path] = {}
    for path in paths:
        if path.name.startswith("._"):
            continue
        if not path.exists():
            raise FileNotFoundError(path)
        unique[str(path)] = path
    return sorted(unique.values(), key=lambda p: str(p).lower())


def data_id_for(path: Path) -> str:
    return f"{slugify(path.stem)}-{stable_hash(str(path.resolve()))}"


def chunked(items: list[Path], size: int) -> list[list[Path]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def extract_upload_url(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for key in ("url", "file_url", "upload_url"):
            if entry.get(key):
                return str(entry[key])
    raise RuntimeError(f"cannot find upload URL in {entry!r}")


def submit_batch(paths: list[Path], args: argparse.Namespace, token: str) -> tuple[str, list[str]]:
    payload: dict[str, Any] = {
        "files": [{"name": path.name, "data_id": data_id_for(path)} for path in paths],
        "model_version": args.model_version,
        "enable_formula": args.enable_formula,
        "enable_table": args.enable_table,
        "language": args.language,
    }
    if args.is_ocr:
        payload["is_ocr"] = True
    if args.extra_formats:
        payload["extra_formats"] = args.extra_formats.split(",")
    data = require_success(
        http_json("POST", f"{PRECISION_BASE}/file-urls/batch", payload=payload, token=token, timeout=args.timeout)
    )
    urls = [extract_upload_url(item) for item in data.get("file_urls", [])]
    if len(urls) != len(paths):
        raise RuntimeError(f"expected {len(paths)} upload URLs, got {len(urls)}")
    return str(data["batch_id"]), urls


def poll_batch(batch_id: str, args: argparse.Namespace, token: str) -> list[dict[str, Any]]:
    deadline = time.time() + args.poll_timeout
    terminal = {"done", "failed"}
    last: list[dict[str, Any]] = []
    while time.time() < deadline:
        data = require_success(
            http_json("GET", f"{PRECISION_BASE}/extract-results/batch/{batch_id}", token=token, timeout=args.timeout)
        )
        results = list(data.get("extract_result") or [])
        last = results
        states = [str(item.get("state")) for item in results]
        print(f"[poll] batch={batch_id} states={dict((s, states.count(s)) for s in sorted(set(states)))}")
        if results and all(state in terminal for state in states):
            return results
        time.sleep(args.poll_interval)
    raise TimeoutError(f"MinerU batch timed out: {batch_id}; last={last}")


def choose_full_md(raw_extract_dir: Path) -> Path:
    matches = sorted(raw_extract_dir.rglob("full.md"))
    if matches:
        return matches[0]
    md_files = [p for p in raw_extract_dir.rglob("*.md") if not p.name.startswith("._")]
    if not md_files:
        raise FileNotFoundError(f"no Markdown file found in {raw_extract_dir}")
    return max(md_files, key=lambda p: p.stat().st_size)


def copy_images_and_rewrite(md_text: str, full_md: Path, paper_dir: Path) -> tuple[str, list[dict[str, str]]]:
    image_dir = paper_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, str]] = []
    mapping: dict[str, str] = {}

    image_files = [
        p for p in full_md.parent.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith("._")
    ]
    used_names: set[str] = set()
    for src in image_files:
        name = src.name
        if name in used_names:
            name = f"{src.stem}-{stable_hash(str(src))}{src.suffix.lower()}"
        used_names.add(name)
        dst = image_dir / name
        shutil.copy2(src, dst)
        rel_from_md = src.relative_to(full_md.parent).as_posix()
        normalized = f"images/{name}"
        mapping[rel_from_md] = normalized
        mapping[src.name] = normalized
        copied.append({"source": str(src), "path": normalized})

    def rewrite_path(raw: str) -> str:
        clean = raw.strip().strip('"').strip("'")
        if re.match(r"^[a-z]+://", clean, flags=re.I):
            return raw
        key = clean.replace("\\", "/")
        if key in mapping:
            return mapping[key]
        base = Path(key).name
        if base in mapping:
            return mapping[base]
        return raw

    md_text = re.sub(
        r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)",
        lambda m: f"![{m.group('alt')}]({rewrite_path(m.group('path'))})",
        md_text,
    )
    md_text = re.sub(
        r"(<img\b[^>]*?\bsrc=[\"'])(?P<path>[^\"']+)([\"'][^>]*>)",
        lambda m: f"{m.group(1)}{rewrite_path(m.group('path'))}{m.group(3)}",
        md_text,
        flags=re.I,
    )
    return md_text, copied


def normalize_result(pdf: Path, result: dict[str, Any], args: argparse.Namespace) -> Path:
    data_id = str(result.get("data_id") or data_id_for(pdf))
    paper_dir = Path(args.out_dir).resolve() / data_id
    if paper_dir.exists() and not args.force:
        raise FileExistsError(f"{paper_dir} exists; pass --force to overwrite generated files")
    paper_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = paper_dir / "mineru_raw"
    raw_extract = raw_dir / "extracted"
    zip_path = raw_dir / "result.zip"
    download(str(result["full_zip_url"]), zip_path, args.timeout)
    safe_extract(zip_path, raw_extract)

    full_md = choose_full_md(raw_extract)
    md_text = read_text(full_md)
    md_text, copied_images = copy_images_and_rewrite(md_text, full_md, paper_dir)
    write_text(paper_dir / "paper.md", md_text.strip() + "\n")
    shutil.copy2(pdf, paper_dir / "paper.pdf")
    write_json(
        paper_dir / "mineru_manifest.json",
        {
            "data_id": data_id,
            "file_name": result.get("file_name") or pdf.name,
            "source_pdf": str(pdf),
            "state": result.get("state"),
            "full_zip_url": result.get("full_zip_url"),
            "raw_markdown": str(full_md),
            "images": copied_images,
        },
    )
    return paper_dir


def resolve_token(args: argparse.Namespace) -> str:
    token = args.token
    if not token and args.token_env:
        token = os.getenv(args.token_env)
    token = token or os.getenv("MINERU_TOKEN") or os.getenv("MINERU_API_KEY")
    if not token:
        raise RuntimeError("missing MinerU token; set MINERU_TOKEN/MINERU_API_KEY or pass --token")
    return token


def run(args: argparse.Namespace) -> int:
    pdfs = collect_pdfs(args)
    if not pdfs:
        raise FileNotFoundError("no PDF files found")
    if args.batch_size < 1 or args.batch_size > 50:
        raise ValueError("MinerU local batch upload supports 1..50 files per batch")
    token = resolve_token(args)
    out_dirs: list[str] = []
    for batch_paths in chunked(pdfs, args.batch_size):
        print(f"[batch] submitting {len(batch_paths)} files")
        batch_id, urls = submit_batch(batch_paths, args, token)
        for path, upload_url in zip(batch_paths, urls):
            print(f"[upload] {path.name}")
            put_file(upload_url, path, args.timeout)
        results = poll_batch(batch_id, args, token)
        by_key: dict[str, dict[str, Any]] = {}
        for item in results:
            if item.get("data_id"):
                by_key[str(item["data_id"])] = item
            if item.get("file_name"):
                by_key[str(item["file_name"])] = item
        for pdf in batch_paths:
            item = by_key.get(data_id_for(pdf)) or by_key.get(pdf.name)
            if not item:
                print(f"[warn] no result for {pdf}", file=sys.stderr)
                continue
            if item.get("state") != "done":
                print(f"[warn] MinerU failed for {pdf}: {item.get('err_msg')}", file=sys.stderr)
                continue
            out_dirs.append(str(normalize_result(pdf, item, args)))
    print(json.dumps({"paper_dirs": out_dirs}, ensure_ascii=False, indent=2))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=None, help="Directory containing local PDFs.")
    parser.add_argument("--pdf", action="append", default=[], help="A single local PDF. May be repeated.")
    parser.add_argument("--out-dir", required=True, help="Destination papers directory.")
    parser.add_argument("--token", default=None, help="MinerU token. Prefer environment variables.")
    parser.add_argument("--token-env", default=None, help="Environment variable containing the MinerU token.")
    parser.add_argument("--model-version", default="vlm", choices=["pipeline", "vlm", "MinerU-HTML"])
    parser.add_argument("--language", default="ch")
    parser.add_argument("--enable-table", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-formula", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--is-ocr", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--extra-formats", default=None, help="Comma-separated optional formats: docx,html,latex.")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--poll-timeout", type=int, default=1800)
    parser.add_argument("--poll-interval", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv or sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
