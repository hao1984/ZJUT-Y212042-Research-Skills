# stage1b_mining_brief_json_v0.4

> Compact no-tools mining prompt for Mechanism E split Stage 1.
> Input: compact mining packet embedded in prompt.
> Output: one concise JSON brief. The deterministic runner expands it to full `mining_result.json`.

---

## No-Tools Contract

- Do not use shell tools.
- Do not read files.
- Do not write files.
- Do not run Python.
- Return only one valid JSON object.
- Do not use markdown fences.
- Do not include prose outside JSON.

---

## Task

Read the mining packet and produce a compact evidence-backed mining brief:

- exactly 5 data-specific patterns
- exactly 3 candidate research questions
- exactly 1 workflow seed for the primary RQ
- concise wording; no report-style narrative
- every pattern must cite evidence source paths from the packet
- avoid KPI/dashboard questions

---

## Output Schema

```json
{
  "schema_version": "mechanism_e_stage1b_mining_brief_v0.4",
  "created_by": "stage1b_mining_brief_json_v0.4",
  "patterns": [
    {
      "id": "p1",
      "description": "",
      "fields": [],
      "evidence": [
        {"source": "mining_packet.aggregate_cubes.example", "claim": "", "values": {}}
      ],
      "why_interesting": "",
      "relation": "supports",
      "confidence": "high",
      "caveats": []
    }
  ],
  "pattern_edges": [
    {"source": "p1", "target": "p2", "relation": "contextualizes", "why": ""}
  ],
  "research_questions": [
    {
      "id": "rq1",
      "question": "",
      "supporting_patterns": [],
      "fields": [],
      "grains": [],
      "comparisons": [],
      "evidence_layers": [],
      "why_single_view_insufficient": "",
      "view_roles": [
        {"role": "structure_overview", "purpose": ""}
      ],
      "shared_state": [],
      "vis_direction_hint": "",
      "priority": {
        "multi_pattern_linkage_score": 5,
        "guided_workflow_potential_score": 5,
        "visual_impact_potential_score": 5,
        "overall_priority_score": 5,
        "recommended_role": "primary_question",
        "rationale": ""
      }
    }
  ],
  "rq_ranking": {
    "recommended_primary_rq": "rq1",
    "merge_candidate_rqs": [],
    "companion_evidence_rqs": [],
    "reject_as_primary": [{"rq_id": "", "reason": ""}]
  },
  "workflow_seed": {
    "seed_id": "w1",
    "rq_id": "rq1",
    "opening_state": "",
    "first_action": "",
    "expected_observation": "",
    "linked_views_to_watch": [],
    "evidence_to_confirm": "",
    "possible_next_steps": [],
    "caveat": ""
  },
  "data_usage": {
    "use_full_data": false,
    "suggested_subset_or_aggregation": "",
    "core_fields": [],
    "auxiliary_fields": [],
    "data_pitfalls": []
  },
  "limitations": []
}
```
