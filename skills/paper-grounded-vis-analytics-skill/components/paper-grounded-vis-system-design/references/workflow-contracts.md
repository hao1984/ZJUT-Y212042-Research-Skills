# Workflow Contracts

This reference condenses the prompt folder into a single paper-grounded VIS system workflow.

## Run Directory

Use one run directory per design attempt:

```text
stage0_input/
stage1_load/
stage1_stat/
stage1_mining/
stage2_idea/
stage3_payload/
stage3_visual_spec/
app/
  data/
artifacts/
```

## Stage 0: Input And Keyword Profile

Inputs may be a paper, dataset, or natural-language idea.

Outputs:

- `stage0_input/input_profile.json`
- `stage0_input/keyword_profile.json`

The keyword profile must include domain terms, visualization terms, task terms, and a retrieval query. If the input is a dataset, include basic schema and sample values; if it is a paper, include title, abstract, L3 summary, and likely system goals.

## Stage 1: Data/Paper Profiling

For datasets, follow the Mechanism E Stage 1 contract:

- Load real data only.
- Build basic schema profiling.
- Mine evidence-backed data-specific patterns, not generic statistics.
- Produce 3-7 anti-dashboard research questions.
- Record why a single view is insufficient.

For papers, convert the paper's claimed problem/method/evidence into a paper profile:

- analysis domain
- key data or phenomenon
- candidate system goals
- expected users
- task vocabulary
- possible data requirements

## Stage 2: Reference Learning And Idea Contract

Retrieve related papers from the local ScholarAIO-style library. Reference papers can ground:

- layout pattern
- visual encoding
- interaction pattern
- evidence workflow
- evaluation/provenance style
- visual style constraints

Reference papers cannot replace the input's data patterns or research target.

Write:

- `stage2_idea/vis_reference_digest.yaml`
- `stage2_idea/vis_reference_digest.json`
- `stage2_idea/vis_reference_report.md`
- `stage2_idea/standard_vis_design_basis.yaml`
- `stage2_idea/rq_selection.md`
- `stage2_idea/idea.yaml`
- `stage2_idea/e_idea_contract.yaml`
- `stage2_idea/e_idea_contract.json`

The idea contract must include:

- `analysis_target`
- `data_task_encoding_mapping`
- `why_not_dashboard`
- `coordinated_workspace`
- `exploration_affordance`
- `reference_learning`
- `data_provenance`

## Stage 3: Visual System Spec

Before building the app, write `stage3_visual_spec/visual_system_spec.json` and `artifacts/design_spec.md`.

Required content:

- analysis target and primary question
- primary visual object
- view graph with at least 3 views unless explicitly justified
- shared state
- linked interactions
- default first-look state
- guided open exploration routes
- visual style system
- viewport contract for `1920x1080` and `1440x810`
- reference-learning adaptation map

## Stage 4: Frontend Demo

Build a desktop analytical workspace by default. The skill is incomplete if a user asked for a demo and only received Stage 2/3 artifacts.

- primary analytical view
- at least two companion views
- evidence/detail panel
- route controls
- provenance
- `app/index.html`
- `app/style.css`
- `app/main.js`
- `app/data/payload.json`
- `app/data/payload.js`
- `artifacts/frontend_build_report.md`

No page-level scroll on first load. Use local scroll inside bounded panels if needed.

Use `scripts/run_visual_demo_pipeline.py` for one-command generation. Use `scripts/build_frontend_demo.py` when Stage 0-3 artifacts already exist.

## Stage 5: Critic And Repair

Evaluate with the critic rubric. Hard-fail if:

- the system is a dashboard, chart collage, landing page, or report
- references are not auditable
- real data is replaced by mock data
- the first screen does not show a coordinated workspace
- there is no shared state or linked interaction
- visual style falls into generic AI/dashboard aesthetics
- `app/index.html` cannot load or render data marks
