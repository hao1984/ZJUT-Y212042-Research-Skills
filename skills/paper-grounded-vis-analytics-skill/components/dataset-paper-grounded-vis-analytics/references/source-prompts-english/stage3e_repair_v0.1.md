# Mechanism E Stage 3e: Targeted Frontend Repair

You are the Stage 3e repair agent for Mechanism E. Your task is to repair a generated visualization demo using the deterministic Stage 3d QA report.

## Scope

Patch only:
- `app/index.html`
- `app/style.css`
- `app/main.js`
- `stage3_visual_spec/visual_system_spec.json` only if the existing spec contradicts the implemented app
- `artifacts/design_spec.md` only if the implementation changed materially

Write one short repair note:
- `artifacts/repair_round_CURRENT.md`

Do not rewrite Stage 1 or Stage 2 artifacts. Do not change the selected research question. Do not change the payload schema unless the QA report proves the current app cannot load the payload.

## Inputs

Read:
- `artifacts/visual_gate_report.json`
- `artifacts/browser_smoke.json`
- `stage3_visual_spec/visual_system_spec.json`
- `artifacts/design_spec.md`
- current app files under `app/`
- Stage 2 contract if needed for default state or workflow intent

## Repair Strategy

Fix only the failed gates and their immediate causes. Preserve working parts.

Common repairs:
- Browser load or console failure: fix JS errors and data path assumptions first.
- Nonblank/data mark failure: ensure SVG/canvas/HTML marks are rendered from real payload arrays.
- Coordinated multi-view failure: place multiple views on screen simultaneously and connect them through shared state.
- Linked interaction failure: make selection/hover/route/clear update at least two views plus the evidence panel.
- Style failure: replace beige/warm-paper/paper-grid/generic dark dashboard/glow/blur/gradient aesthetics with a distinctive, data-specific style system.
- Default-state failure: make the first screen show the Stage 2 default state and primary pattern.
- Workflow failure: add optional entry cues, branch controls, clear controls, and at least one insight checkpoint without turning the app into a linear tutorial.
- Provenance failure: add visible real-data source/row provenance.
- Viewport fit or layout failure: convert the page into a fixed-height desktop workspace that fits at both `1920x1080` and `1440x810` without page-level vertical or horizontal scrolling.

Viewport repair obligations:
- Use a bounded workspace shell, usually `html, body { height: 100%; overflow: hidden; }` and a `100vh` app container.
- Make the first screen show the primary analytical view, at least two companion views, the evidence/detail panel, branch controls, and provenance simultaneously.
- Move long explanations, long evidence lists, and legends into local scroll regions inside bounded panels.
- Use CSS grid/flex tracks with `minmax(0, 1fr)`, `min-height: 0`, and `overflow: hidden` on layout cells.
- Reduce oversized headers, titles, paragraphs, stacked sections, and unnecessary vertical padding before removing analytical views.
- Preserve coordinated multi-view behavior while compacting the layout. Do not "fix" page scrolling by hiding key companion views behind tabs or a button-only route switcher.
- Update `stage3_visual_spec/visual_system_spec.json.viewport_contract` and `artifacts/design_spec.md` if the repair changes the viewport composition.

## Constraints

- Do not add KPI cards as the primary evidence design.
- Do not turn the demo into a landing page.
- Do not hide the main analysis behind tabs or buttons.
- Do not make a forced Next/Previous walkthrough.
- Do not rely on page-level vertical scrolling to reveal key views.
- Do not add mock data.
- Do not use decorative effects that do not encode data or state.
- Do not spend time on unrelated refactors.

After patching, write `artifacts/repair_round_CURRENT.md` with:
- failed gates addressed
- files changed
- why the fix should satisfy Stage 3d
