# Frontend Demo Build Report

- Built at: 2026-06-04T00:36:56
- Domain: `model_uncertainty_diagnosis`
- Input: BNNVis: Towards Visual Analytics for Bayesian Neural Networks
- References: 6
- Keywords: 18
- Retrieval mode: `fts_only`

## Outputs

- `app/index.html`
- `app/style.css`
- `app/main.js`
- `app/data/payload.json`
- `app/data/payload.js`

## Frontend Contract

- Static, dependency-free single-page app.
- Data payload is derived from local paper/index artifacts, not random data.
- Initial screen includes a primary view, reference pattern view, companion state rail, evidence panel, route controls, and provenance.
- `html, body` use fixed-height hidden overflow; long evidence uses bounded local scroll.
