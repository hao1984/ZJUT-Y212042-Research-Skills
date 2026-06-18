# Paper-Grounded Visual Analytics System Design

## Input Target

- Title: BNNVis: Towards Visual Analytics for Bayesian Neural Networks
- Type: paper
- Path: `C:\Users\Maxh\Desktop\VisPaper\data\papers\Appleby-2025-BNNVis-Towards-Visual-Analytics-for-Bayesian-Neural-Networks`

## Retrieval Grounding

- Retrieval status: `ok`
- Retrieval mode: `fts_only`
- Query: `visual analytics uncertainty visualization matrix bayesian neural network bnnvis uncertainty bnns neural how predictions`

- `8cecbf4a-f69f-414b-853f-0c5ebbb9f088` ScatterUQ: Interactive Uncertainty Visualizations for Multiclass Deep Learning Problems
  - Borrow: hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity
  - Borrow: uncertainty layer as secondary evidence, revealed through selection rather than default KPI summaries
- `5c474e6d-da59-47df-9418-63a4116ac0eb` Regularized Multi-Decoder Ensemble for an Error-Aware Scene Representation Network
  - Borrow: spatial semantic structure view with selectable regions/components and linked detail evidence
  - Borrow: hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity
- `5a844ccd-8867-41a4-bd20-cc874c665d5c` <i>GNNLens</i>
                    : A Visual Analytics Approach for Prediction Error Diagnosis of Graph Neural Networks
  - Borrow: hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity
- `ca64b6e6-6f2c-4acf-8a19-64553fd83586` Uncertainty-Aware Deep Neural Representations for Visual Analysis of Vector Field Data
  - Borrow: hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity
  - Borrow: phase/time strip linked to the primary structure so users can compare temporal states without losing context
- `eafe7453-7182-4b6b-ac82-023a45147ae1` ggdist: Visualizations of Distributions and Uncertainty in the Grammar of Graphics
  - Borrow: hybrid relation overview: use a graph/matrix companion to expose entity relations and reduce single-view ambiguity
  - Borrow: phase/time strip linked to the primary structure so users can compare temporal states without losing context

## Analysis Target

BNNVis: Towards Visual Analytics for Bayesian Neural Networks uncertainty and prediction-error workspace

## Primary Visual Object

A model-diagnosis workspace where uncertain cases, model/class comparisons, explanation traces, and paper-grounded design patterns are linked.

## Data-Task-Encoding Mapping

- prediction cases: locate errors and ambiguous outcomes -> case map or ranked uncertainty strip with selection-linked details (model diagnosis begins with concrete cases rather than aggregate scores)
- uncertainty distributions: compare confidence, posterior spread, or disagreement -> distribution glyphs or interval bands tied to selected class/model (uncertainty must be shown as structure, not collapsed into one number)
- model/class relationships: diagnose where predictions diverge -> model-class matrix or relation overview with error highlighting (comparison across model components reveals systematic failure modes)
- explanation evidence: connect a selected case to the reason it is uncertain or wrong -> bounded evidence panel with feature, layer, or source snippets (analysts need traceable evidence before trusting diagnosis)

## View Graph

- `case_uncertainty_view` (primary): Show prediction cases or clusters positioned by uncertainty, error type, and selected class/model context.
- `model_class_matrix` (companion): Compare models, classes, or layers with error and uncertainty highlighting.
- `case_explanation_view` (companion): Show selected posterior, feature/layer attribution, or disagreement traces for the active case.
- `evidence_panel` (detail): Show paper snippets, provenance, caveats, and the current diagnostic rationale.

## Linked Interactions

- `select_case_updates_diagnosis`: case_uncertainty_view updates model_class_matrix, case_explanation_view, evidence_panel
- `select_model_class_filters_cases`: model_class_matrix updates case_uncertainty_view, case_explanation_view, evidence_panel
- `select_explanation_updates_evidence`: case_explanation_view updates case_uncertainty_view, evidence_panel

## Guided Open Exploration

Default state: Show the highest-uncertainty cases, model/class relation overview, and one explanation route for the top selected case.

Entry routes are optional branches, not a forced tutorial. Users can start from keywords, references, or evidence routes, and can clear selection at any time.

## Visual Style System

- Intent: model-diagnosis workspace with precise uncertainty marks, compact comparison structure, and calm evidence surfaces
- Background: neutral light or cool gray; avoid generic ML dashboard styling and purple glow
- Forbidden styles checked: beige/cream/sand, paper grid, generic dark KPI dashboard, purple gradient/glow/blur

## Viewport QA Plan

Fit the initial workspace at `1920x1080` and `1440x810` without page-level scrolling. Put long evidence lists in bounded local scroll panels.

## Provenance And Evidence Policy

Every borrowed design element must point back to a retrieved `meta.json`, `paper.md`, or fallback basis entry. Every data claim in a future frontend must be computed from real input data or explicitly marked unavailable.
