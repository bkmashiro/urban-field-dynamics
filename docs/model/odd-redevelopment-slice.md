# ODD description: redevelopment qualification slice

Status: implemented vertical slice, schema version 0.1.0

This document follows the Overview, Design concepts and Details structure. It describes only the code currently implemented; planned household, firm, transport and environmental modules are excluded until executable.

## 1. Purpose and patterns

The slice tests whether accessibility value and transition inertia can produce distinguishable redevelopment timing under matched stochastic worlds.

It is qualified against synthetic patterns rather than Haidian observations:

- a hard-pinned unit never redevelops;
- lowering transition inertia cannot increase the effective transition cost;
- an older otherwise-identical asset has a lower effective soft-pin cost;
- in the frozen smoke fixture, accessibility investment and no-inertia ablation produce more redevelopment than baseline;
- policy arms for the same world consume identical development event tapes.

These are mechanism-qualification patterns, not empirical calibration targets or planning forecasts.

## 2. Entities, state variables and scales

### Spatial unit

Each unit has:

- stable ID and area;
- current and candidate land use;
- hard, soft or free pin;
- asset age and design life;
- keep NPV, candidate base NPV and transition cost;
- normalized accessibility and its candidate-value factor;
- evidence status.

### Public policy

The implemented policy has an intervention year and normalized accessibility delta. It is applied once at a declared rolling-planning year.

### World

A world is identified by root seed and world ID. It runs over an inclusive annual horizon with four representative seasonal operations per year. Seasonal operations are currently scheduled but do not yet mutate state.

### Campaign arm

An arm combines one policy with the transition-inertia mechanism state. The first smoke campaign includes baseline, accessibility investment and baseline-without-inertia.

## 3. Process overview and scheduling

For each year the runner executes:

1. public policy when the year is a replanning year;
2. spring representative operations;
3. summer representative operations;
4. autumn representative operations;
5. winter representative operations;
6. household relocation placeholder;
7. firm dynamics placeholder;
8. market clearing placeholder;
9. development decision;
10. infrastructure aging;
11. observation placeholder.

Only policy, development and aging currently mutate state. Explicit placeholders preserve intended ordering without pretending that unimplemented mechanisms exist.

## 4. Design concepts

### Basic principles

Redevelopment occurs only when:

```text
candidate NPV > keep NPV + effective transition cost
```

Candidate NPV is candidate base value plus accessibility value plus a world/year development shock.

### Adaptation

Soft-pin transition cost falls linearly with consumed design life. Age beyond design life is allowed and yields zero remaining soft-pin cost. Hard pins remain immutable even when the inertia ablation is disabled.

### Objectives

Private development uses the local NPV rule. No public social-welfare objective or optimiser is implemented in this slice.

### Prediction

The model produces distributions under declared synthetic assumptions. It does not predict parcel-specific Haidian development.

### Sensing

A developer evaluates current accessibility, asset age, keep value and candidate value. No global future knowledge is provided.

### Interaction

Accessibility policy affects candidate value. Household, firm, market and transport feedbacks are not yet implemented.

### Stochasticity

NumPy Philox event tapes are derived from root seed, world ID, year and mechanism. Policy and ablation identities are deliberately excluded, so matched arms consume the same exogenous development shocks.

### Observation

Each world records redevelopment year, final accessibility, final use and development shock trace. Campaign summaries report world count, worlds with redevelopment, total redevelopment and mean redevelopment per world.

## 5. Initialization

`smoke-v1` initializes three synthetic units:

- an innovation soft pin;
- a community-renewal soft pin;
- a heritage hard pin.

It runs world IDs 0–7 from 2026 through 2030 with a frozen root seed. All fixture values are marked synthetic.

## 6. Input data

The qualification slice uses no empirical Haidian data. Inputs are strict Pydantic models and reject unknown fields, duplicate unit IDs, duplicate world IDs, duplicate arm IDs, invalid horizons and policies outside declared replanning years.

Future Haidian adapters must preserve evidence status and may not upgrade provisional or synthetic values through computation.

## 7. Submodels

### Accessibility intervention

At the intervention year, the policy delta is added once to every unit and clamped to the normalized interval `[0, 1]`.

### Effective transition cost

- hard pin: redevelopment forbidden;
- free pin: zero transition cost;
- soft pin: `transition_cost × max(0, 1 - age / design_life)`;
- no-inertia ablation: zero transition cost for non-hard pins.

### Candidate value

```text
candidate base NPV
+ accessibility × accessibility value factor
+ matched development shock
```

### Development shock

For each year and unit, the Philox tape supplies a value in `[0, 1)`, transformed symmetrically into the configured shock interval.

### Campaign execution

World IDs are the outer deterministic loop and campaign arms are the inner loop. Every run carries explicit arm ID and world result. Exports include config, full result, summary and an integrity manifest; verification checks hashes, parses contracts and replays the complete campaign.
