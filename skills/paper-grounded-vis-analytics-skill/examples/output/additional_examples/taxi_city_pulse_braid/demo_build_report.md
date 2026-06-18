# Demo Build Report

## Idea Implemented

Implemented `e006_taxi_city_pulse_braid` as a static coordinated analytical workspace in `app/index.html`.

The first screen opens directly into the January taxi pulse braid: a single schematic OD-time visual object with borough and airport anchors, tapered directional corridor glyphs, airport gateway membrane arcs, anomaly sparks, a phase query rail, selected-regime evidence, and aggregate-to-record trace. It is not a landing page, KPI dashboard, card grid, or independent chart collage.

## Real Data Pipeline

- Source parquet: `/home/jyh/scholaraio_vis/MechanismE/experiments/e_mechanism/datasets/cache/e002_nyc_yellow_taxi_2024_01.parquet`
- Zone lookup: `/home/jyh/scholaraio_vis/MechanismE/experiments/e_mechanism/datasets/cache/taxi_zone_lookup.csv`
- Original table: 2,964,624 rows x 19 fields, 47.647 MB.
- Valid core rows: 2,848,026.
- Preprocessing script: `app/prepare_data.py`.
- Browser payload: `app/data/pulse_payload.json`, about 1.7 MB.

The script reads the full measured parquet and lookup. Aggregate counts, hourly profiles, medians, and anomaly counts are not sampled. The only capped data are the raw record trace examples, which are deterministic samples from measured anomaly rows for browser size.

## Visual Grammar

Primary grammar: `City Pulse Braid`.

- Anchors: borough and airport nodes.
- Corridor glyphs: tapered SVG ribbons; width encodes valid trip count, taper/arrow notch encodes direction, hue encodes airport role.
- Anomaly shadow: magenta sparks attached to OD-time states with excluded or anomaly-class rows.
- Progressive evidence: selected corridor updates hour profile, regime evidence, top measured zone strands, anomaly classes, and raw measured rows.

Default primary layers are limited to 3: anchors, valid corridor ribbons, anomaly sparks. Persistent global labels are limited to 8: Manhattan, Brooklyn, Queens, Bronx, Staten Island, JFK, LGA, and EWR.

## Coordinated Workspace

Implemented 4 linked views:

- `primary_structure_view`: OD-time pulse braid.
- `temporal_phase_view`: 24-hour weekday/weekend query rail.
- `regime_evidence_view`: selected-corridor regime evidence strip.
- `record_trace_view`: aggregate-to-record anomaly trace.

Shared state includes selected day type, period/time range, OD pair, origin/destination region, airport role, payment/anomaly conditioning, and selected anomaly class.

Linked interactions implemented:

- Phase rail period/hour click updates the braid, evidence, and trace.
- Corridor selection updates phase profile, regime evidence, and record trace.
- Airport-role chips highlight matching corridor regimes.
- Anomaly sparks/class chips update the trace scope and anomaly highlighting.

## Reference Learning Implementation

- `d20ea353-d6d8-493a-bf12-eeabcf03b2e0`: visual query model for spatio-temporal data, mapped to the phase query rail and phase-to-braid interaction.
- `e6fe70cb-45bc-4503-8f09-7a9c44335dce`: glyph-based commuting flow visualization, mapped to tapered directional corridor glyphs.
- `590b2b63-1e05-455f-8dc5-108da6eb6992`: spatio-temporal movement aggregation, mapped to OD x period x day_type x airport_role preprocessing.
- `standard_vis_design_basis.aggregate_to_record_trace`: fallback evidence workflow, mapped to the record trace.

## QA Results

Browser inspection was run through Python Playwright against `http://127.0.0.1:8899/`.

- Viewports checked: 1920x1080 and 1440x810.
- Console/page errors: none.
- Primary marks detected: 32 corridor ribbons, 31 anomaly sparks, 48 phase bars, 7 trace rows.
- Provenance footer visible: yes.
- Screenshots written to `artifacts/qa/desktop_1920.png` and `artifacts/qa/desktop_1440.png`.

Fixes applied during QA:

- Converted missing credit-tip quantiles to JSON `null` instead of invalid `NaN`.
- Added a schematic anchor for the measured `Unknown` lookup bucket while keeping it unlabeled by default.
- Reworked the right evidence/trace pane for 1440x810 readability.
- Removed overly broad transparent hit paths that could intercept corridor clicks.

## Output Files

- `app/index.html`
- `app/style.css`
- `app/main.js`
- `app/prepare_data.py`
- `app/data/pulse_payload.json`
- `artifacts/design_spec.md`
- `artifacts/visual_quality_review.json`
- `artifacts/demo_metadata.json`
- `artifacts/BUILD_REPORT.md`

## E Demo Status

Pass. The demo uses real measured data, exposes data provenance and preprocessing, preserves a single data-specific primary visual object, implements coordinated linked views, avoids KPI/dashboard framing, conditions tip evidence on payment semantics, separates airport roles from city-internal flow, and keeps anomaly records traceable rather than silently discarded.
