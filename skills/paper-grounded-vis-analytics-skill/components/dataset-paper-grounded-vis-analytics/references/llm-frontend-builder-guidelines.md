# LLM Frontend Builder Guidelines

Use these guidelines after `scripts/prepare_dataset_vis_brief.py` has produced `artifacts/llm_design_brief.md` and `app/data/payload.js`.

## Role

Act as a visual analytics system designer and frontend engineer. Your job is not to fill a fixed chart template. Your job is to invent a dataset-specific coordinated workspace using:

- the real dataset payload
- mined data patterns
- paper-retrieved VIS design precedents
- Mechanism E constraints from the prompt folder

## Design First

Before writing frontend code, create:

- `stage3_visual_spec/visual_system_spec.json`
- `artifacts/design_spec.md`

The design spec must name the visual grammar:

- dominant visual object
- glyph vocabulary
- view layout
- layer order
- shared state
- linked interaction states
- label and annotation budget
- visual style system
- paper inspiration mapping

## Complete Workspace, Not Simple View

The final app should feel as complete as a serious analytical dashboard in density and coverage, but it must not become a KPI dashboard.

First screen should include:

- one dominant primary data object
- 3-5 coordinated support surfaces when the data supports it
- evidence/detail inspector
- pattern/reference trace
- compact route or state controls
- provenance footer

Good companion surfaces:

- subgroup distribution strips
- category relation matrix
- pattern graph or pattern rail
- paper precedent trace
- raw record/evidence inspector
- temporal/state strip
- outlier or boundary case queue
- field role legend that changes with selection

Avoid:

- one primary chart plus a list
- independent small charts with no shared state
- generic x/y/color selectors as the main experience
- route buttons that merely swap panels
- KPI cards as the evidence surface

## Paper Design Inspiration

Use retrieved papers as design precedents. The model should inspect `paper_reference_digest.json` and `paper_reference_report.md`, then adapt concrete elements:

- overview/detail evidence workflow
- linked brushing patterns
- relation matrix or graph scaffolds
- spatial/temporal context strips
- uncertainty or caveat overlays
- annotation/provenance styles
- multi-panel workspace composition

Never claim a paper used a visual element unless it appears in the digest/brief. If the paper evidence is weak, say the element is a fallback or inferred VIS precedent.

## Real Data Rules

Every analytical mark must come from:

- `payload.rows`
- real aggregates computed from `payload.rows`
- `payload.patterns`
- `payload.references`

Static layout coordinates are allowed when arranging real marks. Random, synthetic, placeholder, or invented measurements are not allowed.

## Primary Object Ideas

Choose according to data shape, but make it custom:

- Numeric + categorical: morphology field, coupling terrain, contour-backed row cloud, subgroup silhouette, boundary case lane.
- Mostly categorical: relation atlas, category cell map, membership lattice, borough/zone scaffold, grouped row strips.
- Temporal: phase strip plus event bundles and local evidence.
- Spatial/geographic: map-like analytical atlas only if real coordinates/regions are available; otherwise use relation geography, not fake maps.

Plain scatter/matrix can be a base layer, but the system should add meaningful overlays, linked context, labels, evidence routes, or glyph layers so it reads as a VIS system figure.

## Interaction Contract

At least three interactions should be implemented:

- primary mark selection updates evidence plus at least one companion view
- category/pattern selection highlights or filters primary marks
- paper/reference selection shows how its design element maps to the current app
- clear/reset restores default state

Interactions should preserve context rather than hide views.

## Viewport Contract

Initial load must fit:

- `1920x1080`
- `1440x810`

Use a fixed-height shell. Long evidence lists can scroll locally. Do not require page-level vertical scroll to see the main workspace.

## Style System

Use mature, restrained VIS styling:

- cool neutral or ink-on-white base
- clear palette roles for categories, selection, evidence, caveat
- stable panel dimensions
- readable compact typography
- no hero section
- no beige/warm-paper dominance
- no generic dark dashboard
- no decorative gradient/glow/blur

Visual quality should come from data geometry, not decoration.

## Required QA

After building:

- run the browser smoke check when possible
- inspect screenshots at `1440x810` and `1920x1080`
- repair if the app looks like a simple chart template, chart collage, or KPI dashboard

Write `artifacts/frontend_build_report.md` with:

- files created
- real-data marks used
- paper precedents adapted
- interactions implemented
- known limitations
