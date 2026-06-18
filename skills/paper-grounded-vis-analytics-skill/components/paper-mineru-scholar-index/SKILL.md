---
name: paper-mineru-scholar-index
description: Convert batches of academic paper PDFs into a ScholarAIO-style local paper knowledge base. Use when OpenClaw/Codex needs to call MinerU official APIs to parse PDFs into Markdown plus extracted images, normalize each paper into paper.pdf/paper.md/images/meta.json, create L1-L4 paper layers where L1=title, L2=abstract, L3=LLM summary/evaluation, L4=full Markdown, embed L1+L2+L3 with qwen3-0.6B-embedding, and build or rebuild data/index.db, data/faiss.index, and data/faiss_ids.json for retrieval.
---

# Paper MinerU Scholar Index

## Overview

Use this skill to turn raw academic PDFs into the same retrieval-ready paper library shape used in this workspace:

```text
data/
  papers/<Author-Year-Title>/
    paper.pdf
    paper.md
    images/
    meta.json
  index.db
  faiss.index
  faiss_ids.json
```

The core contract is:

- `L1`: paper title, stored in `meta.json.title`.
- `L2`: paper abstract, stored in `meta.json.abstract`.
- `L3`: LLM-generated paper summary/evaluation, stored in `meta.json.l3_conclusion`.
- `L4`: full paper Markdown, stored as `paper.md`.
- Embed only `L1 + L2 + L3` for each paper-level vector record unless the user explicitly asks for full-text chunk embeddings.

## Quick Start

For local PDFs, prefer the MinerU Precision Extract batch-upload API because it returns a zip with Markdown, JSON, and images:

```bash
python scripts/mineru_parse_batch.py --input-dir <PDF_DIR> --out-dir <WORKSPACE>/data/papers --token-env MINERU_TOKEN --model-version vlm
```

Then create or refresh per-paper metadata:

```bash
python scripts/build_meta.py --papers-dir <WORKSPACE>/data/papers --llm-api-base <CHAT_BASE_URL> --llm-model <CHAT_MODEL>
```

Then rebuild the ScholarAIO-style index:

```bash
python scripts/build_scholar_index.py --papers-dir <WORKSPACE>/data/papers --db <WORKSPACE>/data/index.db --embedding-api-base <EMBED_BASE_URL> --embedding-model qwen3-0.6B-embedding --rebuild
```

Keep API keys in environment variables:

- `MINERU_TOKEN` or `MINERU_API_KEY` for MinerU Precision Extract.
- `PAPER_LLM_API_KEY` or `OPENAI_API_KEY` for LLM metadata generation.
- `PAPER_EMBED_API_KEY` or `OPENAI_API_KEY` for embeddings.

Never write tokens into `SKILL.md`, manifests, `meta.json`, or shell history examples.

## Workflow

1. Inspect the input.
   - If the user already has `paper.md` and `images/`, skip MinerU and start at metadata.
   - If the input is local PDFs, use `scripts/mineru_parse_batch.py`.
   - If the input is remote URLs, use MinerU Precision URL mode manually from `references/mineru-api.md` or adapt the script.
   - Use Agent Lightweight API only for small, single-file, Markdown-only parsing; it is not the default for this project because it does not provide the complete zip/image output.

2. Parse PDFs with MinerU.
   - Use Precision Extract API for normal papers, batch work, formula/table-heavy papers, or files above lightweight limits.
   - Upload at most 50 local files per batch.
   - Poll until every file reaches `done` or `failed`.
   - Download each `full_zip_url`, preserve the raw zip/extraction under `mineru_raw/`, copy `full.md` to `paper.md`, copy extracted assets into `images/`, and copy the original PDF to `paper.pdf`.

3. Normalize each paper directory.
   - The final paper directory must contain `paper.md`; `paper.pdf` and `images/` are expected when available.
   - Keep Markdown image links relative to `images/`. If a link changes, update `paper.md` and record the path mapping.
   - Ignore macOS resource fork files such as `._*`.

4. Build `meta.json`.
   - Use `scripts/build_meta.py` for a first pass.
   - Extract or infer bibliographic fields: `id`, `title`, `authors`, `first_author`, `first_author_lastname`, `year`, `doi`, `journal`, `paper_type`, `volume`, `issue`, `pages`, `publisher`, `issn`, `citation_count`, `ids`, `source_file`, `extraction_method`, `api_sources`, `references`, `extracted_at`, `toc`, `l3_conclusion`, `l3_extraction_method`, `l3_extracted_at`.
   - Prefer DOI-based enrichment when a DOI is present. Crossref, Semantic Scholar, and OpenAlex may be used when available; record successful services in `api_sources`.
   - Generate `l3_conclusion` with an LLM from the abstract, table of contents, and full Markdown. Ground it in the paper; do not invent unsupported claims.

5. Rebuild retrieval indexes.
   - Use `scripts/build_scholar_index.py`.
   - The SQLite database must include the FTS5 `papers` table plus `paper_vectors`, `papers_hash`, `papers_registry`, and `citations`.
   - Store one vector per paper in `paper_vectors`, keyed by `meta.json.id`.
   - Embed this exact text shape:

```text
Title: <L1>

Abstract:
<L2>

Summary:
<L3>
```

   - Store embedding bytes as little-endian float32 BLOBs.
   - If `faiss` is installed, also write `faiss.index` and `faiss_ids.json` in the same order as the SQLite vectors.

6. Validate the result.
   - Count paper directories containing `meta.json`.
   - Confirm `data/index.db` has matching counts in `papers`, `paper_vectors`, `papers_hash`, and `papers_registry`.
   - Confirm `faiss_ids.json` length matches `paper_vectors` when FAISS is written.
   - Spot-check one paper: title, abstract, `l3_conclusion`, `paper.md`, and image paths.

## Retrieval Behavior

For search tasks after indexing:

- Use FTS5 `papers` for keyword search over title, authors, year, journal, abstract, and conclusion.
- Use `paper_vectors` or `faiss.index` for semantic search over L1+L2+L3.
- Use `paper.md` only when answering detailed evidence questions, figure/table context, equations, or full-text follow-up.

## References

- Read `references/mineru-api.md` before modifying MinerU calls or choosing between Precision and Agent APIs.
- Read `references/output-schema.md` when validating `meta.json`, paper directory layout, and `index.db` schema.
