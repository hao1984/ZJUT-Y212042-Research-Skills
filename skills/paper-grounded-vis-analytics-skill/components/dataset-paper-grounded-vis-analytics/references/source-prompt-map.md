# Source Prompt Map

This skill now embeds the complete prompt library from:

```text
C:\Users\Maxh\Desktop\VisPaper\prompt
```

The prompt files are included in two forms:

- `references/source-prompts-verbatim/`: exact source copies, byte-for-byte identical to the original prompt folder.
- `references/source-prompts-english/`: English working translations used during normal OpenClaw execution.

See `prompt-library-inventory.md` for the complete file-by-file map.

## Pipeline Mapping

| Pipeline responsibility | English prompt files |
|---|---|
| Pattern standards | `DATA_PATTERN_MINING_PRINCIPLES.md` |
| Data loading | `stage1a_load_v0.1.md` |
| Data detective profile | `data_profile_v0.1.md` |
| Narrow pattern mining | `stage1b_mining_narrow_v0.2.md`, with `stage1b_mining_narrow_v0.1.md` for compatibility |
| Mining JSON contracts | `stage1b_mining_brief_json_v0.4.md`, `stage1b_mining_json_response_v0.3.md` |
| Profile-to-idea synthesis | `data_profile2idea_v0.1.md` |
| Visual spec and frontend build | `stage3bc_visual_frontend_builder_v0.1.md`, `demo_builder_e_v0.1.md` |
| Internal criticism | `e_critic_v0.1.md` |
| Targeted repair | `stage3e_repair_v0.1.md` |

## Skill Additions

The prompt library defines AI roles and constraints. This skill adds OpenClaw/Codex integration around those prompts:

- `roles-and-orchestration.md`: the role sequence and artifact handoff logic.
- `prompt-library-inventory.md`: source and English prompt inventory.
- `scripts/prepare_dataset_vis_brief.py`: deterministic helper for initial data profile, pattern seed, paper retrieval digest, payload preparation, and LLM design brief.
- `scripts/browser_smoke_check.cjs`: optional browser check for nonblank marks, viewport fit, and coordinated workspace signals.
- `scripts/run_dataset_vis_pipeline.py`: legacy fallback scaffold only; do not use as the default final generator.

## Non-Negotiable Interpretation

The embedded prompts are design and reasoning contracts. They should guide the model to create a bespoke VIS system from the current dataset and retrieved paper precedents.

They are not permission to:

- hard-code one dashboard layout,
- render paper summaries instead of real dataset marks,
- use a fixed Python generator as the final app,
- treat generic profiling facts as mined patterns,
- claim visual quality without screenshot or viewport evidence.
