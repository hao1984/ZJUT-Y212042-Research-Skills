# Prompt Library Inventory

All files from `C:\Users\Maxh\Desktop\VisPaper\prompt` are embedded in this skill.

## Storage Layout

- Verbatim source copies: `references/source-prompts-verbatim/`
- English working translations: `references/source-prompts-english/`

Use the English working translations during normal OpenClaw execution. Use the verbatim copies for audit, source comparison, or when the user explicitly asks for the original prompt text.

## File Map

| Source prompt | Verbatim copy | English working prompt | Primary use |
|---|---|---|---|
| `DATA_PATTERN_MINING_PRINCIPLES.md` | `source-prompts-verbatim/DATA_PATTERN_MINING_PRINCIPLES.md` | `source-prompts-english/DATA_PATTERN_MINING_PRINCIPLES.md` | Pattern-mining standards, banned outputs, data-specific pattern definition |
| `data_profile_v0.1.md` | `source-prompts-verbatim/data_profile_v0.1.md` | `source-prompts-english/data_profile_v0.1.md` | Data detective/profile agent |
| `stage1a_load_v0.1.md` | `source-prompts-verbatim/stage1a_load_v0.1.md` | `source-prompts-english/stage1a_load_v0.1.md` | Data loading and standardization agent |
| `stage1b_mining_narrow_v0.1.md` | `source-prompts-verbatim/stage1b_mining_narrow_v0.1.md` | `source-prompts-english/stage1b_mining_narrow_v0.1.md` | Legacy narrow mining prompt |
| `stage1b_mining_narrow_v0.2.md` | `source-prompts-verbatim/stage1b_mining_narrow_v0.2.md` | `source-prompts-english/stage1b_mining_narrow_v0.2.md` | Preferred narrow mining prompt |
| `stage1b_mining_brief_json_v0.4.md` | `source-prompts-verbatim/stage1b_mining_brief_json_v0.4.md` | `source-prompts-english/stage1b_mining_brief_json_v0.4.md` | Mining brief JSON contract |
| `stage1b_mining_json_response_v0.3.md` | `source-prompts-verbatim/stage1b_mining_json_response_v0.3.md` | `source-prompts-english/stage1b_mining_json_response_v0.3.md` | Mining JSON response schema |
| `data_profile2idea_v0.1.md` | `source-prompts-verbatim/data_profile2idea_v0.1.md` | `source-prompts-english/data_profile2idea_v0.1.md` | Convert data profile and paper guidance into Mechanism-E idea contract |
| `stage3bc_visual_frontend_builder_v0.1.md` | `source-prompts-verbatim/stage3bc_visual_frontend_builder_v0.1.md` | `source-prompts-english/stage3bc_visual_frontend_builder_v0.1.md` | Stage 3 visual spec and frontend builder |
| `demo_builder_e_v0.1.md` | `source-prompts-verbatim/demo_builder_e_v0.1.md` | `source-prompts-english/demo_builder_e_v0.1.md` | Full real-data demo builder constraints |
| `e_critic_v0.1.md` | `source-prompts-verbatim/e_critic_v0.1.md` | `source-prompts-english/e_critic_v0.1.md` | Internal E critic |
| `stage3e_repair_v0.1.md` | `source-prompts-verbatim/stage3e_repair_v0.1.md` | `source-prompts-english/stage3e_repair_v0.1.md` | Stage 3 repair prompt |

## Loading Policy

Load prompts by role:

- Loading role: `stage1a_load_v0.1.md`
- Profile role: `data_profile_v0.1.md` plus `DATA_PATTERN_MINING_PRINCIPLES.md`
- Mining role: `stage1b_mining_narrow_v0.2.md`; use JSON contract prompts when producing strict JSON
- Idea role: `data_profile2idea_v0.1.md`
- Design/build role: `stage3bc_visual_frontend_builder_v0.1.md` plus `demo_builder_e_v0.1.md`
- Critic role: `e_critic_v0.1.md`
- Repair role: `stage3e_repair_v0.1.md`

Do not load all prompt files into the model context at once unless the user asks for a full audit.
