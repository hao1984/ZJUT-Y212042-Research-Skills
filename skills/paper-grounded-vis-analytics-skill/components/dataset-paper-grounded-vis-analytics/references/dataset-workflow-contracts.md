# Dataset Workflow Contracts

## Run Directory

Use one run directory per dataset:

```text
stage1_data/
stage1_mining/
stage2_references/
stage2_idea/
stage3_visual_spec/
app/
  data/
artifacts/
```

## Stage 1 Outputs

Required:

- `stage1_data/dataset_profile.json`
- `stage1_mining/data_patterns.json`

The profile must describe real loaded data: row count, column count, inferred column types, missingness, distinctness, numeric stats, categorical top values, and representative sample rows.

Patterns must be evidence-backed. Favor subgroup contrast, multivariate coupling, outliers, temporal change, or categorical relation structure. Schema profiling alone is not a pattern.

## Stage 2 Outputs

Required:

- `stage2_references/paper_reference_digest.json`
- `stage2_references/paper_reference_report.md`
- `stage2_idea/rq_selection.md`
- `stage2_idea/e_idea_contract.json`

The selected research question must come from mined data patterns, not from generic domain stereotypes. Paper references must be used or rejected explicitly.

## Stage 3 Outputs

Required:

- `stage3_visual_spec/visual_system_spec.json`
- `artifacts/design_spec.md`

The deterministic preparation script writes `stage3_visual_spec/visual_system_spec_seed.json`; the model must transform that seed into a final `visual_system_spec.json`. The final spec must bind real dataset fields to view roles, shared state, linked interactions, paper-guided design elements, style system, and viewport constraints.

## Stage 4 Outputs

Required:

- `app/index.html`
- `app/style.css`
- `app/main.js`
- `app/data/payload.json`
- `app/data/payload.js`
- `artifacts/frontend_build_report.md`

The app must render real rows or real aggregations from `payload`. For paper inputs or empty data, use another skill; this skill is for datasets.

The final app should be written by the model from the design brief. Do not use a fixed Python frontend generator as the final result unless the user explicitly asks for a baseline scaffold.

## Hard-Fail Gates

Fail and repair if:

- the dataset cannot load and the app still pretends to have data
- the primary view is blank
- visible marks are not derived from loaded data rows or aggregates
- the first screen hides companion views or evidence behind tabs
- the page needs vertical scroll to reveal the workspace
- retrieved papers replace the dataset's analysis target
- the result is a dashboard, chart gallery, landing page, or report
- the result reads as a fixed scaffold that ignores dataset-specific patterns and paper-derived design guidance
