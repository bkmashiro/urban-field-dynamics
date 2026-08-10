# Scaled 2026–2050 stress canary at 8 worlds

Status: replay-verified synthetic engineering canary; not a qualified forecast distribution

## Frozen execution

- Source: signed commit `e0156df0f024076f8f6d6f0bfe08c2429263b45d`.
- Matrix: 8 matched worlds, P0–P3, six scenarios, 25 annual steps.
- Export 14.37 seconds; full replay 12.12 seconds.
- Artifact: `results/scaled-stress-2050-canary-8-e0156df/`, 793,886 bytes.

## Directional checks

- Firm contraction increased P3 final unemployment by `0.497180` on average; all 8 worlds were harmed.
- Heat stress reduced P3 final environment quality by `0.037659`; all 8 worlds were harmed.
- Transport disruption reduced P3 final environment quality by `0.004451`; all 8 worlds were harmed.
- Growth pressure increased P3 unemployment by `0.083787`; 7 of 8 worlds were harmed.

## Interpretation boundary

The first 8 baseline worlds gave a slightly favourable P3 mean rent delta while 5 of 8 worlds were harmed. The 64-world qualification instead gave a positive mean rent delta with 50 of 64 harmed. This is why the stress result remains a canary and does not replace the qualification result.

Scenario magnitudes are one-at-a-time synthetic assumptions, not probabilities, observed shock distributions or policy forecasts.
