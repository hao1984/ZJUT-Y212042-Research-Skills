# Visual System Guidelines

## Coordinated Workspace

The first screen must be a runnable tool-like analytical workspace. It should show:

- primary visual object
- at least two companion views
- evidence/detail panel
- route or branch controls
- provenance

The views must share state. Selection, hover, brushing, or route changes should update at least two views and the evidence panel.

## Anti-Dashboard Rules

Avoid:

- KPI cards as the main evidence design
- independent chart galleries
- generic bar/line/scatter dashboards
- field browsers
- landing pages or hero sections
- tabs that hide the main analysis
- forced Next/Previous tutorials

Prefer:

- data-specific geometry
- overview + detail
- focus + context
- phase/time + structure
- spatial context + relation
- aggregate + raw evidence trace
- optional evidence routes

## Viewport Contract

Target:

- primary: `1920x1080`
- secondary: `1440x810`

Initial load must fit without page-level horizontal or vertical scrolling. Use a fixed-height shell and local scroll regions:

```css
html, body {
  height: 100%;
  overflow: hidden;
}

#app {
  height: 100vh;
  min-height: 0;
}
```

## Visual Style

Do not use:

- dominant beige/cream/sand/tan/warm-paper backgrounds
- paper-grid aesthetics
- generic black/slate dashboard cards
- decorative purple gradients
- blur/glow/glassmorphism without data meaning
- tutorial text that explains the UI

Use:

- restrained distinctive palette
- stable dimensions
- readable typography
- meaningful annotation
- selection-aware evidence design
- data mark geometry as the memorable visual element

## Data Fidelity And Static App Outputs

Use real input data or paper-derived data. Do not use mock, synthetic, placeholder, random, or hand-entered analytical data.

For paper inputs without a separate dataset, the valid real payload is the paper-derived structure produced by the skill: extracted keywords, retrieved references, borrowed design elements, L1-L4 snippets, local file provenance, and the Stage 2/3 contracts. Do not invent model samples, simulation records, or volume measurements that are not present; derive visual marks from the retrieved paper/reference evidence.

The demo should be runnable from `app/index.html` without a build step:

- `app/index.html`
- `app/style.css`
- `app/main.js`
- `app/data/payload.json`
- `app/data/payload.js`

Use `payload.js` to support direct `file://` opening; keep `payload.json` for inspection and QA.

## Design Spec Required Sections

`artifacts/design_spec.md` should include:

- input target
- retrieved reference grounding
- analysis target
- primary visual object
- data-task-encoding mapping
- view graph
- linked interactions
- guided open exploration
- visual style system
- viewport QA plan
- provenance and evidence policy
