#!/usr/bin/env python3
"""Prepare an LLM design brief for dataset-grounded VIS system generation.

This script intentionally does not build the final frontend. It prepares the
evidence and constraints a model needs to design a creative, dataset-specific,
paper-guided visual analytics system.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_dataset_vis_pipeline as base  # noqa: E402


def write_contract_artifacts(run_dir: Path, profile: dict, patterns: dict, digest: dict, design: dict) -> None:
    contract = {
        "schema_version": "dataset_llm_guided_e_idea_contract_v0.2",
        "created_by": "dataset-paper-grounded-vis-analytics/scripts/prepare_dataset_vis_brief.py",
        "mechanism_context": {
            "generation": {"mechanism": "E_data_driven_llm_guided_with_paper_grounding"},
            "data_driven": design,
        },
    }
    spec_seed = {
        "schema_version": "dataset_visual_system_spec_seed_v0.2",
        "purpose": "Seed constraints for the LLM frontend builder. This is not a fixed implementation template.",
        "analysis_target": design["analysis_target"],
        "primary_question": design["primary_question"],
        "primary_visual_object": design["primary_visual_object"],
        "selected_real_fields": design["selected_fields"],
        "view_graph_seed": design["view_graph"],
        "shared_state": design["shared_state"],
        "linked_interactions_seed": design["linked_interactions"],
        "viewport_contract": {
            "primary_viewport": "1920x1080",
            "validation_viewport": "1440x810",
            "page_level_scroll": "forbidden_on_initial_load",
            "local_scroll": "allowed_inside_bounded_evidence_panels",
        },
        "paper_reference_learning": design["reference_learning"],
    }
    base.write_json(run_dir / "stage2_idea" / "e_idea_contract.json", contract)
    base.write_json(run_dir / "stage3_visual_spec" / "visual_system_spec_seed.json", spec_seed)

    selected_rq = next(
        (
            rq
            for rq in (patterns.get("candidate_research_questions") or [])
            if rq.get("question") == design.get("primary_question")
        ),
        (patterns.get("candidate_research_questions") or [{}])[0],
    )
    base.write_text(
        run_dir / "stage2_idea" / "rq_selection.md",
        "\n".join(
            [
                "# RQ Selection",
                "",
                f"Selected: `{selected_rq.get('rq_id', 'rq1')}`",
                "",
                selected_rq.get("question", design["primary_question"]),
                "",
                "Reason: this question has the strongest current balance of data evidence, anti-dashboard potential, and multi-view coordination needs.",
                "",
                "Builder obligation: preserve this RQ unless the real payload proves the selected fields cannot render.",
            ]
        )
        + "\n",
    )


def build_design_brief(run_dir: Path, profile: dict, patterns: dict, digest: dict, design: dict, payload: dict) -> str:
    cols = profile.get("columns", [])
    numeric = profile.get("field_roles", {}).get("numeric", [])
    categorical = profile.get("field_roles", {}).get("categorical", [])
    temporal = profile.get("field_roles", {}).get("temporal", [])
    text = profile.get("field_roles", {}).get("text", [])
    pattern_lines = []
    for pattern in patterns.get("patterns", [])[:6]:
        evidence = pattern.get("evidence") or {}
        pattern_lines.append(
            f"- `{pattern.get('pattern_id')}` {pattern.get('title')} | fields: {', '.join(pattern.get('fields') or [])} | evidence: `{json.dumps(evidence, ensure_ascii=False)[:360]}`"
        )
    ref_lines = []
    for ref in digest.get("selected_references", [])[:6]:
        borrowed = "; ".join(elem.get("borrowed_element", "") for elem in (ref.get("borrowed_elements") or [])[:2])
        ref_lines.append(f"- `{ref.get('paper_id')}` {ref.get('title')} -> {borrowed}")
    sample_rows = payload.get("rows", [])[:3]
    return "\n".join(
        [
            "# LLM Visual Analytics System Design Brief",
            "",
            "This brief is for the model that will write the final frontend. It is not a fixed app template.",
            "",
            "## Dataset Grounding",
            "",
            f"- Dataset path: `{profile['meta']['path']}`",
            f"- Rows loaded: {profile['meta']['row_count_loaded']}",
            f"- Columns: {profile['meta']['column_count']}",
            f"- Numeric fields: {', '.join(numeric) or 'none'}",
            f"- Categorical fields: {', '.join(categorical) or 'none'}",
            f"- Temporal fields: {', '.join(temporal) or 'none'}",
            f"- Text fields: {', '.join(text) or 'none'}",
            "",
            "## Selected Research Question",
            "",
            design["primary_question"],
            "",
            "## Analysis Target",
            "",
            f"- Name: {design['analysis_target']['name']}",
            f"- Primary visual object seed: {design['primary_visual_object']}",
            f"- Real fields seed: `{json.dumps(design['selected_fields'], ensure_ascii=False)}`",
            "",
            "## Data-Specific Patterns",
            "",
            "\n".join(pattern_lines) if pattern_lines else "- No strong pattern found; use the strongest available real-data structure and mark uncertainty.",
            "",
            "## Paper-Grounded Design Inspiration",
            "",
            "\n".join(ref_lines) if ref_lines else "- No paper references retrieved; use standard VIS basis and mark fallback.",
            "",
            "## Payload For Frontend",
            "",
            "- Use `app/data/payload.js` or `app/data/payload.json`.",
            "- Every analytical mark must be computed from `payload.rows`, `payload.patterns`, or real aggregate counts from those rows.",
            "- Do not use the old fixed template in `run_dataset_vis_pipeline.py` as the final design.",
            f"- Sample rows: `{json.dumps(sample_rows, ensure_ascii=False)[:900]}`",
            "",
            "## Required Frontend Character",
            "",
            "- Build a complete visual analytics workspace with dashboard-level completeness, but not KPI-dashboard form.",
            "- Create a dataset-specific dominant visual object. Avoid a plain off-the-shelf scatter/matrix as the whole idea; transform it into a custom analysis object with layers, glyphs, traces, contours, bands, bundles, or relation scaffolds that represent this dataset's pattern.",
            "- Show multiple coordinated views at once: primary object, distribution/context view, relation/category or pattern view, paper-guided design trace, and evidence/detail panel.",
            "- Provide linked interactions: selecting a data mark updates at least two views and the evidence panel; selecting a category/pattern/reference changes visible state without hiding the main object.",
            "- First screen must fit 1920x1080 and 1440x810 without page-level scrolling.",
            "- Use restrained, mature VIS styling. Avoid beige paper, generic dark dashboards, decorative gradients, blur/glow, and marketing hero layout.",
            "",
            "## Expected Files",
            "",
            "- `stage3_visual_spec/visual_system_spec.json`",
            "- `artifacts/design_spec.md`",
            "- `artifacts/frontend_build_report.md`",
            "- `app/index.html`",
            "- `app/style.css`",
            "- `app/main.js`",
            "- `app/data/payload.json`",
            "- `app/data/payload.js`",
            "",
            "## Builder Reminder",
            "",
            "The final frontend must be created by the model from this brief and the payload. The model may choose SVG, Canvas, D3-like hand-coded geometry, or vanilla DOM/SVG. The deterministic script stops here.",
        ]
    ) + "\n"


def prepare(args: argparse.Namespace) -> dict:
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    rows, profile, patterns = base.profile_dataset(Path(args.dataset).resolve(), args.description or "", args.max_rows)
    digest = base.retrieve_reference_digest(Path(args.paper_db).resolve(), Path(args.papers_dir).resolve(), profile, patterns, args.description or "", args.top_k)
    design = base.choose_design(profile, patterns, digest)
    payload = base.build_payload(rows, profile, patterns, digest, design)

    base.write_json(run_dir / "stage1_data" / "dataset_profile.json", profile)
    base.write_json(run_dir / "stage1_mining" / "data_patterns.json", patterns)
    base.write_json(run_dir / "stage2_references" / "paper_reference_digest.json", digest)
    base.write_reference_report(run_dir / "stage2_references" / "paper_reference_report.md", digest)
    write_contract_artifacts(run_dir, profile, patterns, digest, design)
    base.write_json(run_dir / "app" / "data" / "payload.json", payload)
    base.write_text(run_dir / "app" / "data" / "payload.js", "window.__DATASET_VIS_PAYLOAD__ = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n")
    brief = build_design_brief(run_dir, profile, patterns, digest, design, payload)
    base.write_text(run_dir / "artifacts" / "llm_design_brief.md", brief)
    base.write_json(
        run_dir / "artifacts" / "brief_manifest.json",
        {
            "created_at": base.now_iso(),
            "run_dir": str(run_dir),
            "dataset": str(Path(args.dataset).resolve()),
            "rows_loaded": profile["meta"]["row_count_loaded"],
            "paper_references": len(digest.get("selected_references") or []),
            "frontend_status": "brief_ready_model_must_build_app",
            "brief": "artifacts/llm_design_brief.md",
            "payload": "app/data/payload.js",
        },
    )
    return {
        "run_dir": str(run_dir),
        "brief": str(run_dir / "artifacts" / "llm_design_brief.md"),
        "payload": str(run_dir / "app" / "data" / "payload.js"),
        "rows": profile["meta"]["row_count_loaded"],
        "references": len(digest.get("selected_references") or []),
        "status": "llm_design_brief_ready",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--paper-db", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--max-rows", type=int, default=5000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    result = prepare(parse_args(argv))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
