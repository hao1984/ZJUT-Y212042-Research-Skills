# Output Schema

## Paper directory

Each ingested paper should be stored as:

```text
data/papers/<dir_name>/
  paper.pdf
  paper.md
  images/
  meta.json
```

Optional MinerU raw outputs may be kept under `mineru_raw/`.

## Layer contract

The layer names are conceptual and map to existing files/fields:

```json
{
  "L1": "meta.title",
  "L2": "meta.abstract",
  "L3": "meta.l3_conclusion",
  "L4": "paper.md"
}
```

Embed only `L1 + L2 + L3` for the paper-level vector.

## meta.json fields

Use this structure. Unknown values should be empty strings, empty arrays, or empty objects instead of fabricated values.

```json
{
  "id": "uuid",
  "title": "Paper title",
  "authors": ["Author A", "Author B"],
  "first_author": "Author A",
  "first_author_lastname": "Author",
  "year": 2026,
  "doi": "10.xxxx/yyyy",
  "journal": "Venue",
  "abstract": "Original or extracted abstract",
  "paper_type": "journal-article",
  "volume": "",
  "issue": "",
  "pages": "",
  "publisher": "",
  "issn": "",
  "citation_count": {
    "crossref": 0,
    "semantic_scholar": 0,
    "openalex": 0
  },
  "ids": {
    "doi": "",
    "doi_url": "",
    "semantic_scholar": "",
    "semantic_scholar_url": "",
    "openalex": "",
    "openalex_url": ""
  },
  "source_file": "paper.md",
  "extraction_method": "doi|title_search|llm|heuristic",
  "api_sources": ["crossref", "semantic_scholar", "openalex"],
  "references": ["10.xxxx/ref"],
  "extracted_at": "2026-06-03T00:00:00",
  "toc": [
    {"line": 10, "level": 1, "title": "1 INTRODUCTION"}
  ],
  "l3_conclusion": "LLM-generated grounded summary/evaluation.",
  "l3_extraction_method": "llm|toc|heuristic",
  "l3_extracted_at": "2026-06-03T00:00:00"
}
```

## SQLite schema

`data/index.db` should contain:

```sql
CREATE TABLE citations (
    source_id   TEXT NOT NULL,
    target_doi  TEXT NOT NULL,
    target_id   TEXT,
    PRIMARY KEY (source_id, target_doi)
);

CREATE TABLE paper_vectors (
    paper_id     TEXT PRIMARY KEY,
    embedding    BLOB NOT NULL,
    content_hash TEXT NOT NULL DEFAULT ''
);

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
);

CREATE TABLE papers_hash (
    paper_id     TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL
);

CREATE TABLE papers_registry (
    id                   TEXT PRIMARY KEY,
    dir_name             TEXT NOT NULL UNIQUE,
    title                TEXT,
    doi                  TEXT,
    publication_number   TEXT,
    year                 INTEGER,
    first_author         TEXT
);
```

The FTS `citation_count` field should store a displayable text count. When `meta.citation_count` is a dict, use the highest available source count.

## Vector storage

- `paper_vectors.paper_id` must equal `meta.id`.
- `paper_vectors.embedding` is a little-endian float32 BLOB.
- `paper_vectors.content_hash` is a stable hash of the L1+L2+L3 embedding text.
- `faiss_ids.json` is a JSON list of paper ids in the same order used to add vectors to `faiss.index`.
