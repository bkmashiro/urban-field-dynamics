# Scaled 2026–2050 stress canary at 8 worlds

Status: replay-verified synthetic engineering canary; not a qualified forecast distribution

## Frozen execution

- Source: signed commit `518110263155b67295a2e31359cbb9a9cbdd0750`.
- Matrix: 8 matched worlds, P0–P3, six scenarios, 25 annual steps.
- Export 12.08 seconds; full replay 12.01 seconds.
- Artifact: `results/scaled-stress-2050-canary-8-5181102/`, 793,886 bytes.
- Manifest SHA-256: `7849b5e7665dc2534da1ecc09e24d3850c6ddb4c37fcc046e74aa77012cca3d5`.

The stress config and derived evidence are byte-identical to the earlier `e0156df`
canary; only source provenance and the manifest changed.

## Directional checks

- Firm contraction increased P3 final unemployment by `0.497180` on average; all 8 worlds were harmed.
- Heat stress reduced P3 final environment quality by `0.037659`; all 8 worlds were harmed.
- Transport disruption reduced P3 final environment quality by `0.004451`; all 8 worlds were harmed.
- Growth pressure increased P3 unemployment by `0.083787`; 7 of 8 worlds were harmed.

## Interpretation boundary

The first 8 baseline worlds gave a slightly favourable P3 mean rent delta while 5 of 8 worlds were harmed. The 64-world qualification instead gave a positive mean rent delta with 50 of 64 harmed. This is why the stress result remains a canary and does not replace the qualification result.

Scenario magnitudes are one-at-a-time synthetic assumptions, not probabilities, observed shock distributions or policy forecasts.
