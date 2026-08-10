# Pre-PR review packet

Status: local review-ready; no push or PR action has been performed

## Review boundary

- Companion repository: `bkmashiro/urban-field-dynamics`.
- Reviewed implementation HEAD: signed `518110263155b67295a2e31359cbb9a9cbdd0750`.
- Base: `origin/main` at `39901ff76dac9a9654d450776a4997cc8ef2590c`.
- Implementation range: 15 signed local commits; 57 files; 4,165 insertions and 134 deletions.
- The packet itself is a later documentation-only commit; verify live branch status before external action.

## Delivered slices

1. Replayable matched policy-intensity sweeps and discrete threshold brackets.
2. Weighted labor matching, wage/vacancy/employment feedback and labor equity observers.
3. Fail-closed annual/cumulative public budgets plus transport/service capacity ledgers.
4. Bounded annual rent-response solver with explicit convergence diagnostics.
5. One-at-a-time matched stress matrices, objective leverage and group tail harm.
6. Frozen provenance, canonical manifests and byte-for-byte replay for all evidence classes.
7. Exact transport optimisation at `64a8e7d` with an unchanged 130,847,617-byte campaign result hash; the later `5181102` correctness fix intentionally changes only the public MSA mode-share diagnostic.

## Verified artifacts

| Evidence | Source | Size | Manifest SHA-256 |
|---|---|---:|---|
| 32-world qualification | `5181102` | 25,243,317 B | `972383e823db3cace81b37764907a7e95b68ede4422d9f38554350ce5fe04b35` |
| 64-world qualification | `64a8e7d` | 25,265,721 B | `b5662bb670132178ce59feaa9d10562ea7aeb89c6ebaa9fe67f9212900b52b90` |
| 8-world policy sweep | `5181102` | 1,183,947 B | `b9648021994bdc01ebbc11710c041e5df3a602a1ab09b1b01e51efd667029f31` |
| 8-world stress canary | `5181102` | 793,886 B | `7849b5e7665dc2534da1ecc09e24d3850c6ddb4c37fcc046e74aa77012cca3d5` |

All four packages completed full simulation replay and byte comparison.

## Quality gates

- 138 pytest tests passed on Python 3.12.
- Ruff check and format check passed; `git diff --check` passed.
- Markdown relative-link audit passed.
- Wheel and sdist built; fresh wheel environment installed only 7 packages and completed CLI export/replay.
- Wheel/sdist contain no results, Git metadata, profiles or environment files.
- Diff scan found no credential, dynamic-exec, shell-process or network-client additions.
- Every commit in the review range has a good Git signature.

## Decision evidence

- P1 accessibility effect remained positive at 64 worlds: `+0.002726`, 3/64 harmed.
- P2 environment effect remained positive: `+0.017122`, 0/64 harmed.
- P3 rent effect was adverse: `+0.010796`, 95% descriptive interval `[+0.002564,+0.019027]`, 50/64 harmed.
- P3 unemployment was higher than P0 by `0.002582` in the 64-world means.
- P0–P3 were all non-dominated across 13 explicit objectives; no hidden scalar ranking exists.
- 128 worlds were not run because 32→64 caused no directional reversal; more synthetic worlds cannot repair structural or data uncertainty.

## Review findings resolved

1. Stress exports previously allowed stale undeclared files. `e0156df` now rejects non-empty destinations, undeclared files and pre-replay hash mismatch.
2. A 32-world sweep was previously labelled canary. `e0156df` now labels fewer than 32 worlds canary and 32 or more qualification.
3. Four unused scientific/geospatial packages were mandatory runtime dependencies. `62f2818` removed them from the core wheel.
4. Architecture text described future adapters as implemented. `62f2818` corrected the implementation boundary.
5. Terminal-cost mode shares could contradict MSA edge flows under severe congestion. `5181102` now reports the same MSA-averaged shares used to form edge flows while retaining terminal costs separately.

The delegated read-only reviewer timed out without a final verdict and is not counted as a passed independent review. Its two experimental signals were independently checked: the transport signal produced finding 5; the market signal was the documented distinction between pre-update residual history and final post-update `max_residual`.

No known P0 or P1 correctness/security finding remains.

## Hard limitations

- No observed Haidian OD, capacity, traffic-count, building, parcel, firm, wage, rent, environment, public-service, public-finance, planning-control or ownership dataset has been integrated.
- Budget amounts, policy intensities and stress magnitudes are synthetic units.
- The market is a bounded annual shadow-rent response, not a transaction or same-year equilibrium market.
- Labor matching uses divisible weighted cohorts and a deterministic greedy surrogate.
- More Monte Carlo worlds reduce only simulation error, not empirical or structural error.

## External action gate

Upstream Haidian PR [#1126](https://github.com/open-city-ai/haidian/pull/1126) is currently merged and is not draft. This work has not reopened, edited, commented on or otherwise changed it.

No companion push, release, deployment or new PR has been performed. Any companion push and any Haidian incremental PR remain separate reviewer decisions. In particular, an incremental Haidian PR must not imply gallery publication, award selection, government endorsement, calibration, prediction or implementation approval.
