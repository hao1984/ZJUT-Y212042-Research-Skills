# Design Spec

## Workspace Layout
- viewport targets: 1920x1080 primary, 1440x810 validation.
- layout proportions: fixed desktop workspace with a 64px header, a 132px phase query rail, a central 66/34 split, and a 28px provenance footer. The left/center pane holds the dominant pulse braid. The right pane stacks the selected-regime evidence strip above the raw record trace.
- why this layout supports the analysis target: the first screen is one coordinated analytical workspace. The OD pulse braid remains the visual center while the phase rail, evidence strip, and record trace share selection state and explain the currently selected strand instead of becoming independent charts.

## Primary Visual Grammar
- name: `City Pulse Braid`.
- visual object in one sentence: a schematic OD-time braid where borough and airport anchors are connected by tapered, directional corridor glyphs whose thickness, color, texture, and shadow show January 2024 taxi flow regimes.
- glyph vocabulary: region anchors, tapered corridor ribbons, direction arrow notches, airport gateway membrane arcs, sparse anomaly sparks, selected-corridor halo, and credit-tip texture ticks revealed on selection.
- layer order: neutral scaffold; region/airport anchors; valid-trip corridor ribbons; selected/hover corridor halo; anomaly sparks; sparse priority labels.
- default visible layers: 3 primary layers: anchors, valid corridor ribbons, anomaly sparks.
- hidden/progressive layers: credit-card tip texture ticks, top zone-pair annotations, raw-record fields, and metric distribution markers appear only after corridor, phase, regime, or anomaly selection.
- label policy: no more than 8 global labels in the primary object: Manhattan, Brooklyn, Queens, Bronx, Staten Island, JFK, LGA, EWR. Selected corridor and evidence labels are local and replace each other instead of accumulating.
- style discipline: dark neutral cartographic workspace, measured color semantics only. Blue/green marks indicate city-internal movement, amber indicates to-airport, red-orange indicates from-airport, and magenta marks anomaly shadows. No decorative gradients, orbs, glass blur, or poster text.

## Data Encoding Contract
- `tpep_pickup_datetime` -> derive January inclusion, pickup hour, weekday/weekend, and selected period -> phase rail position, active band, and selected-state text -> exposes weekday/weekend rhythm and phase-linked commute reversal.
- `tpep_dropoff_datetime` -> derive duration and temporal anomalies -> evidence strip duration marker and anomaly class -> keeps impossible or long-duration rows auditable.
- `PULocationID` -> origin region and airport origin -> corridor start, origin anchor, selected top pickup zone -> anchors directed origin side.
- `DOLocationID` -> destination region and airport destination -> corridor end, destination anchor, selected top dropoff zone -> anchors directed destination side.
- `trip_distance` -> city vs airport regime and distance anomalies -> corridor evidence marker and anomaly spark -> separates short city circulation from gateway movement.
- `fare_amount` -> fare scale and fare-per-mile -> evidence strip marker and anomaly class -> explains airport/city friction without KPI cards.
- `tip_amount` -> recorded tip texture for credit-card eligible trips -> selected-corridor texture ticks and evidence marker -> avoids reading cash missing tips as zero gratuity.
- `payment_type` -> credit eligibility and no-charge/dispute anomaly strata -> warning text, anomaly class color, record trace fields -> conditions tip interpretation and anomaly review.
- `total_amount` -> charge validation and extreme records -> anomaly class and record trace field -> preserves correction-like records as traceable evidence.

## Coordinated Workspace
- view graph:
- `primary_structure_view`: dominant schematic braid; data grain is OD region x period x day type x airport role; cannot be replaced because it is the only view that preserves the directional flow object.
- `temporal_phase_view`: compact 24-hour weekday/weekend query rail; data grain is hour x day type plus selected OD profile; cannot be replaced because phase brushing drives the shared state.
- `regime_evidence_view`: selected-state evidence strip; data grain is selected corridor plus regime baselines; cannot be replaced because it distinguishes airport gateway, fare-speed, and credit-tip behavior.
- `record_trace_view`: aggregate-to-record trace; data grain is anomaly aggregate plus sampled measured rows; cannot be replaced because it exposes what was excluded and why.
- shared state model: `selected_time_range`, `selected_period`, `selected_day_type`, `selected_od_pair`, `selected_origin_region`, `selected_destination_region`, `selected_airport_role`, `selected_payment_type`, and `selected_anomaly_class`.
- layout: primary braid occupies the large center-left pane; the phase rail spans the workspace above it; evidence and trace occupy the right pane, each tied to selected state.

## Per-View Spec
- `primary_structure_view`: input `flows`, `anomaly_groups`, and `regions`; visual form SVG custom braid; channels are width=count, taper=direction, hue=airport_role, spark count=excluded rows, halo=selected/hover. Interactions: hover/select corridor and click anomaly sparks. Role: reveal commute reversal and airport gateway detachment.
- `temporal_phase_view`: input `hourly_overall` and `hourly_corridors`; visual form aligned hour bars with weekday/weekend rows and brushed period bands. Interactions: click day type or period band. Role: query the pulse by time and show selected corridor hour profile.
- `regime_evidence_view`: input `regime_baselines`, selected flow, and top zone examples; visual form small horizontal distribution bands for distance, duration, fare-per-mile, speed, and credit-card tip rate. Interactions: click airport-role chips or metric rows. Role: test whether the selected strand is city-internal or airport gateway and whether tip texture is interpretable.
- `record_trace_view`: input `anomaly_groups` and `anomaly_samples`; visual form filter-boundary ledger plus compact real-row trace. Interactions: click anomaly class and payment condition. Role: make excluded rows auditable without turning quality issues into the primary object.

## Linked Interaction Spec
- `brush_phase_updates_pulse_braid`: temporal phase rail -> updates `selected_time_range`, `selected_period`, and `selected_day_type` -> braid corridor widths, evidence baselines, and anomaly trace update -> reveals phase-dependent reversal.
- `select_corridor_updates_phase_and_evidence`: primary braid corridor click -> updates OD pair and airport role -> phase rail highlights the corridor hour profile, evidence strip shows selected metrics, record trace scopes the filter boundary -> preserves corridor identity across views.
- `choose_regime_metric_updates_corridor_texture`: evidence role/metric click -> updates airport role or payment conditioning -> braid highlights matching corridors and phase rail dims nonmatching profiles -> separates airport gateway from city-internal strands.
- `inspect_anomaly_shadow_opens_record_trace`: primary spark or trace class click -> updates anomaly class -> trace rows and evidence warning update, primary sparks for that class are highlighted -> keeps anomalies attached to the same OD-time object.

## Reference Adaptation
- `d20ea353-d6d8-493a-bf12-eeabcf03b2e0`, ScholarAIO paper, visual query model for spatio-temporal data: implemented as the phase query rail and `brush_phase_updates_pulse_braid`.
- `e6fe70cb-45bc-4503-8f09-7a9c44335dce`, ScholarAIO paper, glyph-based commuting flow visualization: implemented as directional tapered corridor glyphs in `primary_structure_view` and the corridor selection workflow.
- `590b2b63-1e05-455f-8dc5-108da6eb6992`, ScholarAIO paper, spatio-temporal movement aggregation: implemented in the OD x period x day_type x airport_role preprocessing grain and the primary/phase linked updates.
- `standard_vis_design_basis.aggregate_to_record_trace`, fallback standard basis: implemented as `record_trace_view` and `inspect_anomaly_shadow_opens_record_trace`; it is explicitly labeled as fallback, not paper precedent.

## Detail / Evidence Panel
- allowed evidence: selected filter boundary, aggregate counts for selected state, median/quantile markers within metric bands, payment-conditioning notes, top real zone pairs, anomaly class counts, and sampled measured rows.
- forbidden dashboard/KPI elements: no KPI cards, no ranked borough tables, no total-revenue summaries, no unrelated operational performance tiles, and no standalone chart grid.

## Viewport QA Plan
- 1920x1080 expected composition: header is small, phase rail spans the top, the pulse braid is visibly dominant, right evidence/trace pane is readable, and the provenance footer is visible without page scroll.
- 1440x810 expected composition: same workspace remains within viewport, with smaller but readable labels, no major text clipping, and local scroll only inside the record trace if necessary.
