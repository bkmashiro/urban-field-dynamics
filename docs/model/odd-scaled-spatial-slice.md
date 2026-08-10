# ODD description: scaled stylised spatial substrate

Status: implemented structural slice, schema version 0.4.0

## Purpose

The substrate tests whether the authoritative world runner and morphology observers can operate on 1,000–2,000 policy-independent synthetic spatial units without encoding a preferred TOD, centre, corridor, or green-network outcome.

## Implemented grid

The frozen structural test uses a 40 × 30 grid:

- 1,200 cells;
- 100 m synthetic cell width and 10,000 m² cell area;
- stable row-major IDs;
- symmetric four-neighbour adjacency;
- local metric coordinates with no asserted CRS or real-world parcel identity.

A mechanism-scoped Philox `spatial-bootstrap` tape initializes land use, candidate use, Pin class, asset age, design life, keep value, candidate value, transition cost, and accessibility. The tape identity contains the root seed but no policy identity.

## Observer-only labels

Three circular focus-zone labels and one north–south corridor band are attached after physical/economic initialization. Tests regenerate the same seed with all focus labels removed and require every `SpatialUnitSpec` and every adjacency list to remain exactly equal.

The labels can therefore subset outcomes for reporting, but cannot cause development, accessibility, environmental quality, or value changes.

## Morphology observers

One completed world can be summarized by:

- redevelopment share;
- normalized land-use entropy;
- adjacency mixing rate;
- corridor redevelopment share;
- focus-zone redevelopment shares.

These are observers, not optimization objectives.

## Decision categories

Cross-world, cross-policy transition probabilities support three transparent classes:

- Commitment: robust keep or robust transition across all declared arms;
- Trigger: transition probability changes materially across arms;
- Optionality: neither robust nor sufficiently policy-sensitive under declared thresholds.

Classification thresholds and arm IDs are explicit inputs. Eight-world classifications remain engineering canaries; formal spatial decisions require a qualified ensemble and sensitivity analysis.

## Executed structural test

A 1,200-unit one-year P0/P1 matched-world test ran through the authoritative `run_world` path. It verified complete terminal state, identical development event tapes, policy divergence, and bounded morphology outputs. The local pytest invocation took approximately 0.58 seconds including process startup; this is an engineering measurement, not a portable performance guarantee.

## Scaled integrated canary

The scaled campaign now couples:

- 1,200 redevelopment cells;
- 48 explicit 5 × 5-cell agent, market, transport, and environment zones;
- six weighted household cohorts and six weighted firm cohorts;
- walk, cycle, road, bus, and corridor-rail edges;
- P0–P3 and six independent mechanism ablations;
- a 2026–2028 canary horizon.

A zone membership contract covers every cell exactly once and propagates transport-derived zone accessibility back to every member cell. Environment IDs match zones rather than pretending zones are parcels.

The frozen 8-world × 10-arm canary completed 80 runs. Full JSON export and replay took approximately 56.6 seconds and occupied 129 MiB. This demonstrated exact replay but failed the bounded-artifact requirement.

A bounded exporter therefore retains full config, aggregate summary, paired diagnostics, 1,200-unit decision classifications, and one representative terminal world per arm. Verification reruns the full campaign and rebuilds every derived artifact byte. The verified bounded package occupied approximately 2.8 MiB and took approximately 55 seconds to export and replay-verify.

After adding explicit cycle/bus/rail service-time and capacity interventions, the P1-minus-P0 mean final accessibility delta in the 8-world canary was `+0.0032406`, with no harmed canary worlds. This is a mechanism-observability result, not a statistical policy claim.

## Remaining boundary

The 48-zone network and all 1,200 cell states remain synthetic. Eight matched worlds are insufficient for robust spatial classification. A 64-world short-horizon qualification has been completed separately; its evidence boundary is documented in `scaled-qualification-64.md`.

World-level process parallelism preserves exact scalar results. On the same 8-world 2026–2028 spec, scalar execution took 26.71 seconds and four workers took 9.10 seconds, with identical summary SHA-256, a measured 2.94× wall-clock speedup.

A 2026–2050 canary uses rolling schedule nodes 2026/2030/2035/2040/2045. Eight worlds × ten arms exported and replay-verified in approximately 2 minutes 39 seconds with four workers; the bounded package remained 2.9 MiB. P0/P3 averaged about 1,015 transitions of 1,200 cells and no-inertia about 1,061.5, so the long horizon did not fully saturate the transition observer. The next step is a 32-world long-horizon qualification with convergence and harmed-world diagnostics.

None of these measurements or results upgrade the synthetic cells, zones, cohorts, OD, or environmental fields to empirical Haidian evidence.
