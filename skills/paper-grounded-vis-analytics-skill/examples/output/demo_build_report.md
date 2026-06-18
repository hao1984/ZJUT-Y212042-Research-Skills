# Demo Build Report

## Idea Implemented

- idea_id: `e001_penguins_morphospace_reversal_boundary`
- analysis_target: ecological scaling reversal boundary in penguin morphospace
- primary visual object: a single PCA-grounded four-dimensional morphology map with row points, species hulls, reversal vectors, an Adelie-Chinstrap boundary band, leakage tethers, a decluttering boundary lens, sex displacement vectors, island nesting marks, year ticks, singular anchors, and explicit missing-data badges.

The first screen opens directly into the morphospace workspace. It is not a landing page, KPI grid, field browser, or chart collage.

## Data Used

- path: `/home/jyh/scholaraio_vis/MechanismE/experiments/e_mechanism/datasets/cache/e001_palmer_penguins_morphology.csv`
- browser payloads:
  - `app/data/prepared.json`
  - `app/data/source.csv`
- size: 0.0145 MB
- original shape: 344 rows x 8 fields
- plotted morphology rows: 342 rows with complete numeric morphology
- missing morphology rows: 2 rows, retained as explicit missing-row badges
- missing sex rows: 11 rows, retained with unknown-sex marks
- sampling: none
- aggregation: no aggregation removes individual points; overlays are computed from the full real dataset.

Preprocessing is auditable in `app/prepare_data.py`. It standardizes the four numeric morphology fields, computes PCA coordinates/loadings, reproduces the flipper-depth correlations, computes leave-one-out LDA leakage rows, projects sex displacement vectors, computes cross-species boundary tethers, and marks singular rows by within-species standardized distance.

## Real-Data Evidence Preserved

- Pooled `flipper_length_mm` vs `bill_depth_mm` correlation: r = -0.5839 over 342 complete morphology rows.
- Within-species correlations are positive:
  - Adelie: r = 0.3076 over 151 rows
  - Chinstrap: r = 0.5801 over 68 rows
  - Gentoo: r = 0.7066 over 123 rows
- Four-dimensional leave-one-out LDA leakage rows: 5 total, source rows 73, 129, 296, 306, and 330.
- All LDA leakage is between Adelie and Chinstrap; Gentoo has no four-dimensional confusion in this run.
- PC1 and PC2 explain 88.15% of standardized four-field morphology variance.
- Island interpretation is constrained in the UI because Gentoo appears only on Biscoe and Chinstrap only on Dream in this file.

## Visual Design Inspiration Applied

- Interactive Visual Cluster Analysis by Contrastive Dimensionality Reduction: applied as direct link/tether geometry between ambiguous boundary records and nearest cross-species neighbors.
- A Decluttering Lens for Scatterplots: applied as an interactive boundary lens that spreads real points near the Adelie-Chinstrap leaky band while preserving global anchors.
- Classes are not Clusters: applied by treating species colors as ecological context, not as proof of clean classification; the visual emphasis is on reversal vectors, boundary tethers, and singular records.

## Anti-Dashboard Self-Check

- primary view form: one dominant SVG morphospace object
- primary user action: trace reversal vectors and inspect boundary/anomaly records in the same morphospace
- card grid or KPI dashboard: no
- chart collage: no
- only filtering/slicing: no
- if companion views were removed, the core research question would still be explorable from the morphospace: yes
- passes check: yes

Rationale: The controls toggle layers on the same analysis object. The right-side inspector only explains selected rows and active evidence; it does not become a table-first view or independent chart panel.

## Deviations from Idea

- No deviations from the Stage 2 E-specific contract were introduced.
- The Adelie-Chinstrap boundary band is a projected LDA boundary in PC1/PC2 space, with exact 4D LDA leakage rows preserved as tethered records. This follows the contract while keeping the primary object in the PCA morphospace.

## Validation

- Ran `python3 app/prepare_data.py`; output contained 342 plotted rows and 2 missing morphology rows.
- Started local static server with `python3 -m http.server 4053 --directory app`.
- Ran Playwright Chromium smoke checks at 1440x810 and 1920x1080.
- Observed 342 SVG point circles in both browser checks.
- Observed no JavaScript console errors or page errors.
- Confirmed the data provenance panel reports the no-sampling strategy.
- Screenshots written:
  - `artifacts/playwright_1440.png`
  - `artifacts/playwright_1920.png`

## Known Limitations

- The LDA decision boundary is projected into the PC1/PC2 plane for visual continuity, while the leakage records are computed from the full four-dimensional morphology vectors.
- The boundary lens is designed for inspection of local real rows, not for changing the embedding or recomputing the model.
- Year is intentionally a lightweight row tick, not a temporal trend claim, because the data cover only 2007-2009.
