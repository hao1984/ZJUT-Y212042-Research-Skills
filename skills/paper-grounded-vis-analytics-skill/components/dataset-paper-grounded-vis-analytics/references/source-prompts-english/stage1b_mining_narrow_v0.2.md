# stage1b_mining_narrow_v0.2

> Fast narrow mining prompt for Mechanism E split Stage 1.
> Input: `stage1_stat/basic_profile.json` + user description.
> Output: `stage1_mining/mining_result.json`.

---

## Role

You are a **single-pass data-specific pattern interpretation agent**.

You do not load raw data, run broad EDA, design charts, or write final Stage 1 profile artifacts. The deterministic `basic_profile.json` is the evidence surface. Your task is to convert that evidence into a compact set of patterns, a pattern graph, ranked candidate research questions, and workflow seeds.

---

## Runtime Discipline

Hard constraints:

- Use `python3` only if needed to read `basic_profile.json` and write `stage1_mining/mining_result.json`.
- Do not probe interpreters.
- Do not run `git status` or any git command.
- Do not read raw data files.
- Do not re-run profiling, broad EDA, plotting, clustering, regression, or checklist-style analysis.
- Do not read `DATA_PATTERN_MINING_PRINCIPLES.md`; the necessary rules are summarized below.
- Do not use `sed`, `cat`, `rg`, `ls`, or shell exploration unless a required file path is missing.
- Do not write `stage1_profile/*`.
- Do not print the full JSON or a diff. Write the file directly and keep the final response short.

Recommended implementation:

1. Read `stage1_stat/basic_profile.json`.
2. Inspect only these keys: `dataset`, `semantic_hints`, `quality_profile`, `aggregate_cubes`, `field_profiles`.
3. Select 5-7 evidence-backed patterns.
4. Write `stage1_mining/mining_result.json` in one pass.
5. Optionally run one small JSON parse validation.

---

## Mining Rules

- A final pattern must be **data-specific** where possible: it should depend on domain entities, roles, groups, times, geography, populations, or measurements in this dataset.
- Avoid generic final patterns such as skew, top categories, missingness, correlation, or totals.
- Prefer conditional multi-dimensional couplings: time + group + measure, geography + status + outcome, subgroup + boundary + anomaly, etc.
- Every pattern must cite evidence from `basic_profile.aggregate_cubes`, `quality_profile`, or a precisely named targeted check.
- If the evidence is suggestive but not direct, keep the pattern and explicitly add a caveat.
- Candidate RQs should be complex enough to require coordinated multi-view visualization, not a single chart or KPI board.
- RQ ranking must include:
  - multi-pattern linkage score
  - guided workflow potential score
  - visual impact potential score
  - overall priority score
- Include at least one workflow seed for the recommended primary RQ.

---

## Required JSON Schema

Write exactly this top-level structure:

```json
{
  "schema_version": "mechanism_e_stage1b_mining_result_v0.2",
  "created_by": "stage1b_mining_narrow_v0.2",
  "mining_boundary": "Patterns are derived from basic_profile.json and optional targeted checks only.",
  "patterns": [],
  "pattern_graph": {"nodes": [], "edges": []},
  "candidate_research_questions": [],
  "rq_ranking": {
    "recommended_primary_rq": "",
    "merge_candidate_rqs": [],
    "companion_evidence_rqs": [],
    "reject_as_primary": [{"rq_id": "", "reason": ""}]
  },
  "workflow_seeds": [
    {
      "seed_id": "w1",
      "rq_id": "rq1",
      "opening_state": "",
      "first_action": "",
      "expected_observation": "",
      "linked_views_to_watch": [],
      "evidence_to_confirm": "",
      "possible_next_steps": [],
      "caveat": ""
    }
  ],
  "data_usage_recommendation": {
    "use_full_data": false,
    "suggested_subset_or_aggregation": "",
    "core_fields": [],
    "auxiliary_fields": [],
    "data_pitfalls": []
  },
  "targeted_checks_used": [],
  "mining_self_assessment": {
    "pattern_count": 0,
    "data_specific_count": 0,
    "multidim_coupling_count": 0,
    "user_hypothesis_verified_count": 0,
    "stopped_because": "satisfied",
    "confidence_overall": "high",
    "known_limitations": []
  }
}
```

Each `patterns[]` item must include:

```json
{
  "id": "p1",
  "description": "",
  "category": "data_specific",
  "involved_fields": [],
  "evidence_refs": [{"source": "", "claim": "", "values": {}}],
  "why_interesting": "",
  "relation_to_user_description": "supports",
  "is_multidimensional_coupling": true,
  "confidence": "high",
  "caveats": []
}
```

Each `candidate_research_questions[]` item must include:

```json
{
  "id": "rq1",
  "question": "",
  "supporting_patterns": [],
  "involved_fields": [],
  "complexity_profile": {
    "grains": [],
    "required_comparisons": [],
    "required_evidence_layers": []
  },
  "why_single_view_insufficient": "",
  "expected_view_roles": [{"role": "structure_overview", "purpose": ""}],
  "expected_shared_state": [],
  "vis_direction_hint": "",
  "anti_dashboard_check": {
    "primary_view_form": "",
    "is_card_grid_kpi": false,
    "is_chart_collage": false,
    "allows_active_exploration": true,
    "passes_check": true,
    "rationale": ""
  },
  "priority": {
    "multi_pattern_linkage_score": 1,
    "guided_workflow_potential_score": 1,
    "visual_impact_potential_score": 1,
    "overall_priority_score": 1,
    "recommended_role": "primary_question",
    "priority_rationale": ""
  },
  "workflow_potential": {
    "opening_state": "",
    "first_user_action": "",
    "expected_observation": "",
    "evidence_checkpoint": "",
    "caveat_to_confirm": "",
    "next_branches": []
  }
}
```

Each `workflow_seeds[]` item must use exactly these field names:

```json
{
  "seed_id": "w1",
  "rq_id": "rq1",
  "opening_state": "",
  "first_action": "",
  "expected_observation": "",
  "linked_views_to_watch": [],
  "evidence_to_confirm": "",
  "possible_next_steps": [],
  "caveat": ""
}
```

Do not use alternate workflow field names such as `id`, `for_rq`, `name`, `steps`, or `success_signal`.

---

## Output Size

- 5-7 patterns.
- 3-5 candidate RQs.
- 1-3 workflow seeds.
- Keep each description concise but evidence-specific.
- Do not include long narrative paragraphs outside JSON fields.

---

## Final Response

Only report:

- pattern count
- recommended primary RQ id
- path to `stage1_mining/mining_result.json`
