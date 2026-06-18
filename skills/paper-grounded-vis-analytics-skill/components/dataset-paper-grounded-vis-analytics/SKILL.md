---
name: dataset-paper-grounded-vis-analytics
description: Build a complete, runnable, real-data visual analytics frontend system from a dataset by orchestrating Mechanism-E AI roles, translated prompt-library instructions, local paper retrieval, and dashboard-collapse criticism. Use when OpenClaw/Codex receives a CSV, TSV, JSON, JSONL, parquet, Excel, directory, or similar dataset and must standardize it, profile it, mine data-specific patterns, retrieve related VIS papers from the local paper-mineru-scholar-index corpus, synthesize a paper-grounded visual analytics idea, then let the model creatively design, implement, critique, repair, and deliver a coordinated multi-view frontend demo instead of a fixed template.
---

# Dataset Paper-Grounded VIS Analytics

## Operating Principle

Use this skill as an AI-role orchestration guide, not as a fixed frontend generator. The bundled scripts may prepare evidence, payloads, retrieval digests, smoke checks, and fallback scaffolds, but the final visual analytics system must be designed and coded by the model from the dataset, mined patterns, retrieved papers, and prompt-library constraints.

The source prompt folder has been embedded into this skill in two forms:

- `references/source-prompts-verbatim/`: exact byte-for-byte copies of every file from `C:\Users\Maxh\Desktop\VisPaper\prompt`; use this for audit and source fidelity.
- `references/source-prompts-english/`: English working translations of the same prompt files; load the relevant stage prompt before performing that role.

Do not load the full prompt library at once. Read only the stage prompt required by the current role.

## Quick Use

Given a dataset and user goal:

1. Create a run directory under `runs/<run_name>/`.
2. Use the roles in `references/roles-and-orchestration.md` in order.
3. Use `scripts/prepare_dataset_vis_brief.py` only as a deterministic evidence-preparation helper when useful.
4. Retrieve related papers from `data/index.db` and `data/papers/`, then adapt their VIS design ideas to the current dataset.
5. Write a bespoke frontend under `app/`:
   - `app/index.html`
   - `app/style.css`
   - `app/main.js`
   - `app/data/*`
6. Run critic and repair gates before final delivery.

Optional evidence-preparation command:

```bash
python scripts/prepare_dataset_vis_brief.py --dataset <DATASET_PATH> --description "<USER_GOAL>" --papers-dir <WORKSPACE>/data/papers --paper-db <WORKSPACE>/data/index.db --run-dir <WORKSPACE>/runs/<RUN_NAME> --top-k 8
```

Optional browser smoke check:

```bash
node scripts/browser_smoke_check.cjs --file <WORKSPACE>/runs/<RUN_NAME>/app/index.html --run-dir <WORKSPACE>/runs/<RUN_NAME> --executable-path <CHROME_OR_EDGE_EXE>
```

## AI Roles

Act as the following roles sequentially. If OpenClaw provides only one model instance, simulate the roles with explicit stage boundaries and artifacts.

1. **Orchestrator**
   - Create the run directory.
   - Select the relevant English source prompts.
   - Keep artifacts staged and auditable.
   - Prevent the workflow from collapsing into a single generic dashboard prompt.

2. **Data Loading and Standardization Agent**
   - Read `references/source-prompts-english/stage1a_load_v0.1.md`.
   - Load only real data.
   - Produce standardized table artifacts and loading manifests.
   - Never fabricate mock or synthetic data.

3. **Data Detective / Profile Agent**
   - Read `references/source-prompts-english/data_profile_v0.1.md`.
   - Also read `references/source-prompts-english/DATA_PATTERN_MINING_PRINCIPLES.md`.
   - Find what the data says, not just what columns exist.
   - Produce data profile, evidence, candidate research questions, and anti-dashboard checks.

4. **Narrow Pattern Mining Agent**
   - Read `references/source-prompts-english/stage1b_mining_narrow_v0.2.md`.
   - If legacy compatibility is needed, compare with `stage1b_mining_narrow_v0.1.md`.
   - Mine data-specific patterns, pattern graph, candidate RQs, and priorities.
   - Treat generic top-N lists, field summaries, missingness, and plain correlations as insufficient by themselves.

5. **Paper Retrieval and Grounding Agent**
   - Use the local `$paper-mineru-scholar-index` result corpus: `data/index.db`, `data/papers/**/meta.json`, and `paper.md`.
   - Retrieve by dataset description, field names, mined patterns, and candidate RQs.
   - Summarize borrowed visual structures, interaction patterns, evidence workflows, and layout lessons.
   - Use papers as design guidance, never as a replacement for the current dataset.

6. **Mechanism-E Idea Architect**
   - Read `references/source-prompts-english/data_profile2idea_v0.1.md`.
   - Convert profile + mined patterns + paper guidance into an idea contract.
   - Include `analysis_target`, `data_task_encoding_mapping`, `why_not_dashboard`, `coordinated_workspace`, and `exploration_affordance`.

7. **Visual System Designer and Frontend Builder**
   - Read `references/source-prompts-english/stage3bc_visual_frontend_builder_v0.1.md`.
   - Read `references/source-prompts-english/demo_builder_e_v0.1.md`.
   - Write `artifacts/design_spec.md` before coding.
   - Invent a dataset-specific dominant visual object and coordinated companion views.
   - Build a runnable static frontend from real data. Do not reuse a fixed layout template unless explicitly requested as an emergency fallback.

8. **Internal E Critic**
   - Read `references/source-prompts-english/e_critic_v0.1.md`.
   - Evaluate stage outputs with hard-fail flags.
   - Check data-pattern fidelity, real-data provenance, coordinated multi-view behavior, first-screen visual quality, viewport fit, and anti-dashboard strength.

9. **Repair Agent**
   - Read `references/source-prompts-english/stage3e_repair_v0.1.md`.
   - Repair only the failed gates.
   - Preserve the idea contract unless real data makes a deviation necessary, in which case record the deviation explicitly.

## Frontend Requirements

The generated frontend must be an analysis workspace, not a page, chart gallery, KPI dashboard, or paper-reference-only demo.

Required qualities:

- Use real dataset rows or real aggregations in the primary marks.
- Present a dominant visual object on the first screen.
- Include at least two linked analytical views; use three or more when the data supports it.
- Share selection, brush, entity, time, or pattern state across views.
- Include evidence/provenance for dataset path, row count, fields, sampling/aggregation, and paper guidance.
- Fit `1920x1080` and `1440x810` without page-level scrolling on first load.
- Use paper guidance for visual idioms and interaction design, while keeping the current dataset as the analysis object.
- Prefer custom data-specific geometry over off-the-shelf chart collections.

## Reference Navigation

- `references/roles-and-orchestration.md`: full role order, inputs, outputs, and prompt mapping.
- `references/prompt-library-inventory.md`: all embedded prompt files, original-copy locations, English translation locations, and usage.
- `references/dataset-workflow-contracts.md`: artifact contracts and failure gates.
- `references/paper-guidance-policy.md`: how retrieved papers may influence the system.
- `references/frontend-contract.md`: frontend quality gates.
- `references/llm-frontend-builder-guidelines.md`: LLM-specific frontend design guidance.
- `references/source-prompt-map.md`: source prompt traceability map.

## Final Delivery

For each completed run, provide:

- runnable frontend path or localhost URL
- `artifacts/design_spec.md`
- `artifacts/visual_quality_review.json` when generated
- `artifacts/frontend_build_report.md` or `BUILD_REPORT.md`
- browser smoke report when available
- a short explanation of which AI roles were used and which paper/design ideas shaped the result
