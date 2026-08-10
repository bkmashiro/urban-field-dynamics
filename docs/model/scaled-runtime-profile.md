# Scaled runtime profile and exact transport optimisation

Status: measured on 2026-08-10; synthetic engineering workload

## Workload

The profile runs one matched world across all 13 scaled policy/ablation arms from 2026 through 2050. It exercises 1,200 redevelopment cells, 48 zones, 700 transport edges, 16 OD pairs, weighted household and firm cohorts, labor matching, market response, seasonal exposure, services, and public-budget accounting.

Reproduce the current profile with:

```bash
uv run python tools/profile_scaled.py \
  --worlds 1 --end-year 2050 \
  --profile /tmp/ufd-scaled.prof --top 25
```

## Baseline finding

Frozen commit `8501782921e5d852ac98c9528043df441e856044` spent 94.27 of 101.15 profiled seconds in transport assignment. It called the per-destination shortest-path routine 1,144,000 times. The same unprofiled campaign took 39.78 seconds.

The duplicated work came from rebuilding modal adjacency and rerunning Dijkstra for every OD destination, annual transport iteration, arm, and year. Labor matching separately requested a complete 48-by-48 skim despite reading only current household-origin to firm-destination pairs.

## Changes

Commit `64a8e7df522e82e8b0e6ead0edf0063d79955350` makes three bounded changes:

1. build one deterministic shortest-path tree per origin and mode for each assignment iteration;
2. stop each tree after all declared OD destinations are settled, and request only occupied household-to-firm pairs for labor skims;
3. cache at most 64 pure transport results keyed by the complete immutable edge, OD, and assignment contracts, while returning explicit copies of every mutable dictionary layer.

Edge-ID sorting, `TransportMode` order, heap tie-breaking, BPR/MSA equations, logit mode choice, event tapes, and public result schemas are unchanged.

## Exact parity and speed

The baseline and optimised one-world campaigns both produced:

- canonical result size: `130847617` bytes;
- SHA-256: `208bab1b42902ad68503c12f652e45c8140d5df573f22d2a3a1ec3af552f8930`.

Observed unprofiled runtime fell from 39.78 seconds to 2.70 seconds, approximately 14.73 times faster on the same host. The repository profile tool measured 2.927 seconds inside `run_campaign`; the largest remaining item was the transport wrapper at 0.783 seconds. No optional accelerator or new runtime dependency was added.

## Boundary

This profile demonstrates computational equivalence for the frozen synthetic workload. It does not validate empirical assumptions or imply that other graph sizes, OD structures, operating systems, or processors will achieve the same speedup.
