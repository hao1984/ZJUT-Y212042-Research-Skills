# Critic Rubric

Evaluate Stage 2 and Stage 3 with explicit evidence.

## Stage 2: Idea Contract

Score 1-5:

- analysis target specificity
- data-task-encoding mapping completeness
- why-not-dashboard strength
- reference learning grounding
- coordinated workspace contract
- guided open exploration
- upstream input fidelity

Hard-fail if:

- no named analysis target
- no reference-learning audit
- retrieved papers are listed but not mapped to views/interactions
- coordinated workspace lacks shared state
- idea is just KPI cards or independent charts

## Stage 3: Visual Spec / Demo

Score 1-5:

- data fidelity
- idea fidelity
- specialization
- insight strength
- anti-dashboard compliance
- visual research strength
- coordinated multiview implementation
- data provenance explicitness
- viewport fit

Hard-fail if:

- mock/synthetic data replaces real data
- first screen is a dashboard, chart collage, landing page, or report
- no linked interactions
- main analysis is hidden behind tabs or buttons
- page-level scrolling is needed to see key views
- visual style is generic AI/dashboard decoration

Repair only failed gates and immediate causes.
