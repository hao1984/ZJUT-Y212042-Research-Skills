# Frontend Contract

## Workspace

The first screen must be a fixed-height analytical workspace with dashboard-level completeness but VIS-system structure:

- primary data view
- pattern/reference companion view
- field/category companion view
- evidence/detail panel
- route controls
- dataset provenance footer

When the dataset supports it, add extra coordinated surfaces such as a distribution strip, relation atlas, pattern rail, paper precedent trace, outlier lane, or temporal/state strip. Avoid stopping at one chart plus an evidence list.

Use:

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

## LLM-Created Visual Grammar

The final frontend should be authored by the model from `artifacts/llm_design_brief.md`. Do not let the deterministic preparation script define the whole UI.

The model should name and implement a dataset-specific visual grammar:

- glyph vocabulary
- layer order
- state/selection styling
- layout hierarchy
- evidence/provenance treatment
- paper-inspiration mapping

## Real-Data Rendering Rules

Render real data:

- If at least two numeric fields exist, draw row-level marks using real numeric values.
- If one numeric field and categorical fields exist, draw real grouped distributions or sorted strips.
- If mostly categorical fields exist, draw category relationship matrices and row lists from real counts.
- If temporal fields exist, use real time bins or ordered states.

Never invent:

- coordinates not implied by data fields or deterministic layout of real categories
- random samples
- placeholder rows
- simulated model outputs

Static label text and deterministic layout coordinates are allowed when they organize real data marks.

## Linked Interaction

At minimum:

- selecting a primary mark updates the evidence panel and companion state
- selecting a category/field filters or highlights primary marks and updates evidence
- selecting a reference or pattern updates the evidence panel and design provenance

Selections must be reversible with a visible clear/reset control.

## Style

Avoid:

- KPI cards as the main content
- beige/warm-paper backgrounds
- generic dark dashboard cards
- decorative gradients, blur, or glow
- landing-page hero copy

Prefer:

- data-specific geometry
- compact research-tool layout
- restrained but distinctive palette
- source-row evidence
- visible paper-reference provenance

## Anti-Template Check

Reject and redesign if:

- the app is only a plain scatter/matrix/table/list
- companion views do not share state
- paper references are only listed and do not shape views/interactions
- the first screenshot could be mistaken for a generic dashboard product
- the primary visual object is not customized to the mined data pattern
