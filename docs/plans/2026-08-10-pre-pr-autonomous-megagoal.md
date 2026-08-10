# Urban Field Dynamics Pre-PR Autonomous Mega-Goal

> **For Hermes:** This is the active long-running execution source. Read it fully, trust live Git state over historical chat, and continue through multiple verified slices until all locally executable pre-PR work is complete or a real blocker applies.

**Goal:** Complete the companion engine's locally executable modelling, evidence, qualification, performance, package, and documentation work before any new Haidian PR is considered.

**Repository:** `/Users/yuzhe/projects/urban-field-dynamics`

**Authoritative runtime:** Python 3.12. Browser/TypeScript code may only replay derived evidence.

## User intent and unattended authority

Yuzhe is AFK and asked Hermes to complete all work before a PR. This is unattended execution:

- continue automatically after every verified slice;
- use small signed **local** commits;
- never push, create/update/comment/merge/close a PR, publish, deploy, modify Haidian upstream/fork, or use production accounts/data;
- do not treat credentials present on the machine as permission;
- do not stop for milestone reporting while a safe executable slice remains.

## Value filter

Prefer high-evidence mechanisms and auditability that directly strengthen the scientific and engineering case:

1. matched randomness and fail-closed state contracts;
2. missing feedback loops that materially alter policy interpretation;
3. distributional/equity/tail-risk evidence;
4. bounded replay-verifiable evidence packages;
5. measured performance and sample-size qualification;
6. public package and documentation correctness.

Do not add speculative GPU/JAX/Numba paths, heavy transport dependencies, high-fidelity claims, or broad rewrites without profile/data evidence. Do not tune seeds or parameters to manufacture desirable policy signs.

## Non-negotiable scientific boundaries

- All current spatial, household, firm, market, transport, service, and environmental inputs are synthetic/stylised unless an explicit public/observed source proves otherwise.
- No Haidian empirical calibration, parcel forecast, implementation recommendation, gallery/award claim, or government endorsement.
- Eight worlds are only canary evidence. Thirty-two to sixty-four worlds are qualification evidence. Larger runs require convergence evidence.
- Policies and ablations must use mechanism-scoped Philox tapes; dynamic membership must use stable entity identity.
- Morphology remains an observer output. Do not force TOD, three centres, green corridors, or any preferred form into the objective.
- Policy comparison must report trade-offs, uncertainty, harmed worlds/groups, and non-dominance. No hidden scalar score.
- Bounded artifacts must be hash-manifested and fully replay-verifiable from one immutable source revision.

## Current state discovered

At commit `39901ff76dac9a9654d450776a4997cc8ef2590c`:

- 1,200 stylised cells and 48 agent/market/transport/environment zones;
- P0–P3 plus eight matched mechanism ablations (12 arms total);
- weighted households/firms, lifecycle dynamics, annual market feedback, multimodal accessibility, seasonal exposure, public service capacity/crowding, rolling triggers, redevelopment, morphology observers;
- entity-stable Philox event tapes and exact serial/parallel world execution;
- cohort-weighted equity, Pareto, tail-harm, threshold-bracket, and policy-intensity sweep utilities;
- deterministic bounded export and full replay verification;
- 107 tests plus Ruff/format/diff gates green;
- current 32-world × 12-arm × 2026–2050 qualification completed with 384 runs and verified bounded artifacts;
- no current PR operation is authorized.

Known scientific gaps that are locally executable:

- labor supply/demand matching is implicit rather than explicit;
- infrastructure capacity and public budget constraints are not first-class annual ledgers;
- rent feedback is a deterministic pressure surrogate, not a bounded iterative clearing diagnostic;
- policy-intensity sweeps lack a bounded multi-world evidence exporter/runner;
- decision evidence lacks explicit leverage/cost accounting and group-level tail harm;
- robustness lacks declared exogenous stress scenarios and sensitivity matrix;
- current HEAD qualification needs frozen documentation and convergence/sample-size interpretation;
- public CLI/package/release gates do not expose the newer campaign/evidence workflows.

External-resource or permission-gated gaps:

- real OD, network capacities/counts, buildings, firms, households, rents, environment, service, ownership, and planning-control data;
- empirical calibration/validation and any geographic policy conclusion;
- AequilibraE real-network oracle without a credible network/OD fixture;
- Haidian submission refresh and any PR/remote write.

## Desired pre-PR state

The engine should have:

1. explicit matched labor matching and wage/commute mismatch observers;
2. explicit infrastructure and public-budget ledgers with fail-closed constraints and policy cost traces;
3. stable bounded market-clearing diagnostics with non-convergence surfaced, not hidden;
4. replay-verifiable multi-world intensity and stress/sensitivity evidence;
5. group-level tail harm, explicit policy cost, leverage, Pareto, and robustness diagnostics without hidden weights;
6. measured profile and only evidence-justified performance changes;
7. a frozen current-HEAD 32/64/128-world qualification ladder selected by convergence/runtime evidence;
8. CLI/package/build/readme/docs that execute as written;
9. a clean sequence of signed local commits and a final pre-PR review packet/checklist, with no PR created.

## Global gates

Run after each coherent block and before every local commit:

```bash
uv run pytest -q
uv run ruff check src tests tools
uv run ruff format --check src tests tools
git diff --check
```

Release closeout also requires:

```bash
uv build
uv run urban-field smoke --output /tmp/urban-field-release-smoke
uv run urban-field verify /tmp/urban-field-release-smoke
```

For bounded campaign work, execute the real exporter and verifier, not only unit tests.

## Autonomous execution queue

### Track A — Sweep evidence completion

- [x] Add strict sweep campaign/result contracts with world-level responses and matched identity checks.
- [x] Add bounded sweep export, manifest hashes, full replay verification, CLI/tool entry, and 8-world real canary.
- [x] Record threshold brackets as declared engineering thresholds only; never infer a planning standard.

### Track B — Labor matching

- [x] Add household labor supply and firm labor demand contracts without individual-level fiction.
- [x] Implement deterministic capacity-constrained matching with commute/generalized-cost and skill compatibility.
- [x] Integrate annual employment mismatch/wage-pressure feedback and a matched mechanism ablation.
- [x] Add world/equity observers for unemployment, vacancies, commute burden, and group disparity.

### Track C — Infrastructure and budget ledgers

- [x] Add annual infrastructure utilisation/overload traces for transport and public service demand.
- [x] Add policy capital/operating costs plus annual/cumulative budget constraints.
- [x] Fail closed unless proportional capital rationing is explicitly declared.
- [x] Export cost, overload, and unmet-demand traces into bounded evidence.

### Track D — Market clearing hardening

- [x] Replace one-step rent update with a bounded relaxed annual target solve.
- [x] Preserve the prior occupancy-pressure semantics rather than claim a same-year equilibrium.
- [x] Prove convergence/non-convergence and export annual/aggregate diagnostics.

### Track E — Robustness and decision evidence

- [ ] Add declared exogenous stress scenarios (growth, firm shock, transport disruption, heat/exposure, service constraint) whose identity is separate from policy.
- [ ] Add multi-world stress/sensitivity matrix and replay-verifiable bounded export.
- [ ] Add group-level tail harm, explicit policy cost, leverage ratios with denominator provenance, and no-score Pareto diagnostics.
- [ ] Add threshold/tipping sweep evidence across matched worlds with brackets and stability diagnostics.

### Track F — Performance and qualification

- [ ] Profile current long-horizon scaled workload and save a reproducible profile summary.
- [ ] Apply only measured, semantics-preserving CPU optimisations with exact serial/parallel parity.
- [ ] Freeze current-HEAD 32-world qualification documentation.
- [ ] Run 64-world current-HEAD qualification; inspect convergence, harmed worlds/groups, Pareto stability, runtime, and artifact size.
- [ ] Run 128-world qualification only if 32→64 diagnostics or uncertainty justify it and runtime/storage stay bounded; otherwise document why 64 is sufficient for this synthetic phase.

### Track G — Public package and pre-PR closeout

- [ ] Expose integrated/scaled/sweep/stress bounded workflows through stable CLI commands.
- [ ] Execute README/public CLI examples in a clean temporary output root.
- [ ] Build wheel/sdist and install-smoke the wheel in a temporary environment.
- [ ] Add provenance fields needed to pin source commit/config without reading Git during replay.
- [ ] Update ODD, limitations, data requirements, qualification, and reproduction docs.
- [ ] Produce a local pre-PR review packet/checklist identifying exact companion commits/artifacts and permission-gated Haidian changes.
- [ ] Run final full gates, verify all local commit signatures, and stop before push/PR.

## Per-slice protocol

1. Inspect live state and the governing contracts.
2. Write a RED behavior test and observe the expected failure, or record why a docs/profile-only slice has no semantic RED.
3. Implement the minimum coherent behavior.
4. Run focused tests and a real smoke where applicable.
5. Update this roadmap checkboxes and completion log.
6. Run global gates.
7. Make a signed local commit; do not push while unattended.
8. Verify signature and clean status.
9. Continue immediately to the next executable slice.

## Stop conditions

Stop only when:

- every locally executable checkbox above is complete;
- the remaining work requires real data, product/scientific policy, remote permission, or user review;
- gates repeatedly fail in a way that requires a user choice;
- continuing would require an unsafe broad rewrite or unapproved heavy dependency.

A clean commit, successful canary, completed qualification, or context boundary is not a stop condition.

If blocked, record the blocker here and report exact modified files, tests, Git status, and the safest next step.

## Completion log

- 2026-08-10: Roadmap created from live commit `39901ff`; current 32-world/384-run long-horizon bounded qualification and 107-test gate already verified. Next: Track A sweep evidence completion.
- 2026-08-10: Track A complete. Added per-world matched sweep responses, random-identity validation, bounded hash/replay evidence, stable CLI, and a real 8-world × 5-level × 2026–2050 export/replay canary (1.1 MiB). Next: Track B labor matching.
- 2026-08-10: Track B complete. Added deterministic weighted labor flow, complete congested transport skims without extra demand, wage and vacancy-retention feedback, firm/location job-state consistency, equity observers, a P3 matched ablation, bounded evidence, and long-horizon execution. Next: Track C infrastructure and budget ledgers.

## Short prompt

Read `docs/plans/2026-08-10-pre-pr-autonomous-megagoal.md` fully and execute it in `/Users/yuzhe/projects/urban-field-dynamics`. This is unattended: never push, publish, deploy, modify Haidian, or create/update a PR. Do not stop after one successful slice; continue until all locally executable pre-PR work is done or a real blocker is recorded.
