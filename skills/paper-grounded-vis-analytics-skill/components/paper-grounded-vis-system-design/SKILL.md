---
name: paper-grounded-vis-system-design
description: Design and build a runnable paper-grounded visual analytics frontend demo for a new paper, dataset, or research idea. Use when OpenClaw/Codex needs to extract keywords, search the existing MinerU/ScholarAIO paper library created by paper-mineru-scholar-index, read related meta.json and paper.md files, summarize reusable VIS system patterns, produce a Mechanism-E-style idea contract and visual spec, then directly output a coordinated multi-view app under app/ with index.html, style.css, main.js, and paper-derived payload data.
---

# Paper Grounded VIS System Design

## Overview

Use this skill to create a runnable visual analytics demo grounded in the local paper corpus. The skill combines two sources:

1. The current paper library from `$paper-mineru-scholar-index`: `data/index.db`, `data/faiss.index`, `data/faiss_ids.json`, and `data/papers/*/{meta.json,paper.md}`.
2. The Mechanism E prompt flow in this project: data loading, pattern mining, paper-grounded idea design, visual spec, frontend builder, critic, and repair.

The default output is a coordinated analytical workspace under `app/`, not only a design document. Do not stop at `visual_system_spec.json` unless the user explicitly asks for design-only output.

## Quick Start

Create a run directory and run the full pipeline:

```bash
python scripts/run_visual_demo_pipeline.py --input <PAPER_OR_DATA_PATH> --description "<USER_GOAL>" --papers-dir <WORKSPACE>/data/papers --paper-db <WORKSPACE>/data/index.db --run-dir <WORKSPACE>/runs/<RUN_NAME> --top-k 8
```

This writes:

- `stage0_input/input_profile.json`
- `stage0_input/keyword_profile.json`
- `stage2_idea/vis_reference_digest.yaml`
- `stage2_idea/vis_reference_digest.json`
- `stage2_idea/vis_reference_report.md`
- `stage2_idea/standard_vis_design_basis.yaml`
- `stage2_idea/rq_selection.md`
- `stage2_idea/idea.yaml`
- `stage2_idea/e_idea_contract.yaml`
- `stage2_idea/e_idea_contract.json`
- `stage3_visual_spec/visual_system_spec.json`
- `artifacts/design_spec.md`
- `artifacts/frontend_build_report.md`
- `app/index.html`
- `app/style.css`
- `app/main.js`
- `app/data/payload.json`
- `app/data/payload.js`

Optional browser smoke check:

```bash
node scripts/browser_smoke_check.cjs --file <WORKSPACE>/runs/<RUN_NAME>/app/index.html --run-dir <WORKSPACE>/runs/<RUN_NAME>
```

## Required Workflow

### Stage 0: Input Understanding

Accept any of:

- A new paper PDF, Markdown, `meta.json`, or paper directory.
- A dataset path such as CSV, TSV, JSON, JSONL, Parquet, or Excel.
- A natural-language research idea or dataset description.

Extract:

- domain entities
- candidate analytical tasks
- data fields or paper concepts
- 8-20 retrieval keywords
- a compact retrieval query

If the input is a raw PDF and no Markdown exists, first use `$paper-mineru-scholar-index` to create `paper.md` and `meta.json`.

### Stage 1: Retrieve Related VIS Papers

Search the local paper library:

- Prefer semantic search with `qwen3-0.6B-embedding` against `paper_vectors` or `faiss.index` when an embedding endpoint is configured.
- Always run FTS5 keyword search against `data/index.db` as a fallback or fusion signal.
- Map retrieved `paper_id` values back to local `data/papers/*/meta.json` and `paper.md`.

For each selected paper, extract only auditable design evidence:

- system goal or analysis target
- visual encodings and dominant visual object
- coordinated views
- linked interactions
- workflow or exploration pattern
- style and layout cues
- caveats and why the reference may not apply

Do not invent paper-specific design elements. If the evidence is not in `meta.json`, `l3_conclusion`, title/abstract, or nearby `paper.md` snippets, mark it as uncertain.

### Stage 2: Paper-Grounded Idea Contract

Produce `stage2_idea/e_idea_contract.yaml` and `stage2_idea/idea.yaml` with the five Mechanism E contracts:

- `analysis_target`: a named, explorable phenomenon or system object.
- `data_task_encoding_mapping`: core fields/concepts mapped to tasks, encodings, and reasons.
- `why_not_dashboard`: concrete reason KPI cards or independent charts are insufficient.
- `coordinated_workspace`: 2-4 complementary views with shared state and linked interactions.
- `exploration_affordance`: guided open exploration with entry cues, branch routes, reversible selection, and non-linear guards.

Add `reference_learning`:

- applied paper elements mapped to view ids or interaction ids
- unused references with reasons
- fallback standard VIS basis if retrieval is weak
- `silent_reference_count` should be 0 unless the artifact is incomplete

### Stage 3: Visual System Specification

Write `stage3_visual_spec/visual_system_spec.json` before building the frontend. It must specify:

- `analysis_target`
- `primary_question`
- `view_graph`
- `shared_state`
- `linked_interactions`
- `default_state`
- `guided_open_exploration`
- `viewport_contract`
- `visual_style_system`
- `reference_learning_adapted`

The first screen must fit both `1920x1080` and `1440x810` with no page-level scrolling.

### Stage 4: Frontend Demo

Build a real-data single-page app under `app/` by default:

- `app/index.html`
- `app/style.css`
- `app/main.js`
- payload under `app/data/`
- `artifacts/design_spec.md`
- `artifacts/frontend_build_report.md`

Prefer `scripts/build_frontend_demo.py` after Stage 3, or `scripts/run_visual_demo_pipeline.py` for one-command generation. Use real input data or paper-derived data. Do not use mock, synthetic, random, or placeholder analytical data. If the input is a paper rather than a dataset, the analytical payload should be the paper-derived keyword/reference/evidence structure from the local corpus. The first screen must show a primary analytical view, at least two companion views, an evidence/detail panel, branch controls, and provenance.

### Stage 5: Critic And Repair

Use `references/critic-rubric.md` after Stage 2 and Stage 3. For runnable demos, run `scripts/browser_smoke_check.cjs` when Playwright is available. If a gate fails, repair only the failed cause and write a short repair note.

## Non-Negotiables

- Ground all reference claims in local paper artifacts.
- Do not let retrieved papers override the user's data or research target; papers only shape visual structure, interaction, and evidence workflow.
- Do not treat schema profiling, top-N lists, missingness, or generic correlations as data-specific patterns.
- Do not build a dashboard, KPI grid, chart gallery, landing page, poster, or scrollable report as the primary system.
- Do not hide the main analysis behind tabs or button-only modes.
- Preserve file-level provenance for input data, retrieved papers, and borrowed design elements.
- Do not leave the user with only prompts or specifications when they asked for a demo; produce `app/index.html`.

## References

- Read `references/workflow-contracts.md` for the full stage contract distilled from the prompt folder.
- Read `references/retrieval-and-reference-learning.md` before changing paper retrieval or borrowed-element extraction.
- Read `references/visual-system-guidelines.md` before writing Stage 3 specs or frontend code.
- Read `references/critic-rubric.md` before evaluating or repairing outputs.
- Read `references/source-prompt-map.md` to trace this skill back to the original prompt files.
