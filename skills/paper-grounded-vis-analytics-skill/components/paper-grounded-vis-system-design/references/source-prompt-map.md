# Source Prompt Map

The skill condenses the prompt files in `C:/Users/Maxh/Desktop/VisPaper/prompt`.

## Mapped Files

- `stage1a_load_v0.1.md`: data loading and standardized object contract.
- `stage1b_mining_brief_json_v0.4.md`: compact evidence-backed mining brief schema.
- `stage1b_mining_json_response_v0.3.md`: full JSON mining result contract.
- `stage1b_mining_narrow_v0.1.md` and `stage1b_mining_narrow_v0.2.md`: targeted mining discipline.
- `DATA_PATTERN_MINING_PRINCIPLES.md`: data-specific pattern rules and banned mining outputs.
- `data_profile_v0.1.md`: Stage 1 data profile contract.
- `data_profile2idea_v0.1.md`: Stage 2 idea contract, ScholarAIO reference learning, five Mechanism E contracts.
- `demo_builder_e_v0.1.md`: full frontend demo builder constraints.
- `stage3bc_visual_frontend_builder_v0.1.md`: visual spec + frontend builder split.
- `e_critic_v0.1.md`: critic rubric for Stage 1/2/3.
- `stage3e_repair_v0.1.md`: targeted repair workflow.

## Additions In This Skill

The original prompt flow assumes retrieval artifacts are already provided. This skill adds a deterministic retrieval-preparation layer:

- extract keywords from a new paper or dataset
- query the existing `paper-mineru-scholar-index` corpus
- read related `meta.json` and `paper.md`
- produce `vis_reference_digest.yaml` and `vis_reference_report.md`
- seed the Stage 2 and Stage 3 artifacts from those references

This revision also adds a deterministic frontend layer so the skill can continue to a runnable demo:

- `scripts/run_visual_demo_pipeline.py`: one-command runner for retrieval, contracts, visual spec, and app generation.
- `scripts/build_frontend_demo.py`: Stage 3bc frontend builder that writes `app/index.html`, `app/style.css`, `app/main.js`, and paper-derived payload files.
- `scripts/browser_smoke_check.cjs`: optional Stage 3 browser smoke check for viewport fit, nonblank marks, visible coordinated panels, and console errors.
