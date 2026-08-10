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

## Remaining boundary

The scaled substrate currently exercises redevelopment over all 1,200 units. Weighted agents, transport assignment, and seasonal exposure still use the smaller integrated fixture. Their next scale-up should use explicit zoning/aggregation where justified rather than pretending 1,200 synthetic cells are empirical parcels or OD zones.
