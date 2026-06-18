# MinerU API Reference Notes

Use this reference when converting PDFs or debugging MinerU responses. It summarizes the official docs at https://mineru.net/apiManage/docs and the MinerU output file docs at https://opendatalab.github.io/MinerU/reference/output_files/.

## API choice

Use Precision Extract API by default for this skill:

- Token required.
- Supports single URL tasks and batch local-file upload.
- Supports `pipeline`, `vlm`, and `MinerU-HTML`; use `vlm` for academic PDFs unless the user requests otherwise.
- PDF/file limits in the official docs: up to 200 MB and 200 pages.
- Returns a zip that includes Markdown, JSON, and image assets.

Use Agent Lightweight API only as a fallback:

- No token required.
- Single file only.
- Smaller limits in the official docs: up to 10 MB and 20 pages.
- Returns Markdown only through `markdown_url`; not enough when image folders and structured JSON are required.

## Precision local batch upload

1. Request upload URLs:

```http
POST https://mineru.net/api/v4/file-urls/batch
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "files": [
    {"name": "paper.pdf", "data_id": "stable-paper-id"}
  ],
  "model_version": "vlm",
  "enable_formula": true,
  "enable_table": true,
  "language": "ch"
}
```

2. Upload every file with `PUT` to the returned signed URL. Do not set `Content-Type` for the upload.

3. Poll batch results:

```http
GET https://mineru.net/api/v4/extract-results/batch/{batch_id}
Authorization: Bearer <TOKEN>
```

Each item in `data.extract_result` has:

- `file_name`
- `data_id`
- `state`: `waiting-file`, `pending`, `running`, `converting`, `done`, or `failed`
- `full_zip_url` when `state=done`
- `err_msg` when `state=failed`
- optional `extract_progress`

4. Download `full_zip_url` for completed files and extract it.

## Precision single URL task

Submit:

```http
POST https://mineru.net/api/v4/extract/task
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "url": "https://example.com/paper.pdf",
  "model_version": "vlm",
  "enable_formula": true,
  "enable_table": true,
  "language": "ch"
}
```

Poll:

```http
GET https://mineru.net/api/v4/extract/task/{task_id}
Authorization: Bearer <TOKEN>
```

When `data.state=done`, download `data.full_zip_url`.

## Agent lightweight file flow

Submit:

```http
POST https://mineru.net/api/v1/agent/parse/file
Content-Type: application/json

{
  "file_name": "paper.pdf",
  "language": "ch",
  "enable_table": true,
  "is_ocr": false,
  "enable_formula": true
}
```

Upload bytes with `PUT` to `data.file_url`, then poll:

```http
GET https://mineru.net/api/v1/agent/parse/{task_id}
```

When `data.state=done`, download `data.markdown_url`.

## MinerU zip normalization

The Precision zip usually contains:

- `full.md`: main Markdown.
- `*_content_list.json`: content blocks in reading order.
- `*_middle.json`: intermediate structured parsing output.
- `*_model.json`: model inference output.
- `images/`: extracted image/table/equation assets.

Normalize for this skill:

```text
papers/<paper_dir>/
  paper.pdf
  paper.md
  images/
  mineru_raw/
    result.zip
    extracted/
```

`paper.md` should preserve links like `images/<filename>`. Copy all discovered image assets from the raw extraction into the normalized `images/` directory.

## Error handling

- Token errors: check `Authorization: Bearer <TOKEN>` and rotate expired tokens.
- File size/page limit errors: split PDFs or lower page range.
- URL timeout: use local upload instead of URL mode.
- Missing formulas/tables: ensure `enable_formula` and `enable_table` are true; prefer Precision API.
- Scanned PDFs: set `is_ocr=true`.
