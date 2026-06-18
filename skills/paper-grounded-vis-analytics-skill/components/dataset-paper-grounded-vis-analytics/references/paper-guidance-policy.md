# Paper Guidance Policy

This skill borrows from the existing paper library created by `$paper-mineru-scholar-index`.

## Compatible Inputs

Expected local corpus:

- `data/index.db`
- `data/papers/*/meta.json`
- `data/papers/*/paper.md`
- optional vector files such as `data/faiss.index`

The current deterministic runner uses `data/index.db` FTS/LIKE search. If an embedding endpoint is added later, semantic search may be fused with keyword search.

## What Papers Can Guide

Retrieved papers may guide:

- primary view form
- companion view roles
- linked interactions
- evidence/provenance workflow
- visual style constraints
- viewport/workspace composition
- figure-level ideas such as how panels are arranged, how selections propagate, how uncertainty/caveats are shown, and how visual hierarchy is established

Retrieved papers must not:

- create fake dataset rows
- override mined data patterns
- define the analysis target without dataset evidence
- be shown as the only analytical content

## Borrowed Element Format

Each applied element should record:

- `source_paper_id`
- `source_title`
- `borrowed_element`
- `adapted_for_current_data`
- `mapped_to_view_ids`
- `mapped_to_interaction_ids`
- `confidence`

References not used should be listed with a concrete reason.

## LLM Builder Use

The deterministic script only prepares `paper_reference_digest.json` and `paper_reference_report.md`. The model should use those artifacts to decide how to design the final visual analytics system. It may adapt paper-guided design ideas creatively, but it must record the mapping in `artifacts/design_spec.md` and `stage3_visual_spec/visual_system_spec.json`.
