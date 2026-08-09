# ODD description: transport and seasonal exposure slice

Status: implemented reference slice, schema version 0.3.0

This document describes the executable fast transport and relative environmental-exposure layer. It is a policy-comparison surrogate, not a calibrated reconstruction of Haidian mobility or pollution.

## 1. Purpose

The slice qualifies two feedback paths:

1. modal graph + OD demand → capacity pressure → generalized cost → job accessibility;
2. traffic/activity/night light/season/green fraction → relative exposure → household location utility.

It also tests whether transport-capacity and blue-green policies change those paths through explicit intermediate state rather than by writing desired outcomes directly.

## 2. Transport entities

### Directed modal edge

Each edge declares stable ID, endpoints, mode, free-flow minutes, capacity, and optional generalized-cost penalty. The current modes are walk, cycle, road, bus, and rail.

### Aggregate OD pair

Each OD pair carries an origin, destination, and representative-period weighted demand. It does not claim observed trip counts unless the adapter assigns a stronger evidence status upstream.

### Assignment controls

The reference solver declares BPR alpha/beta, modal-logit theta, and a fixed number of MSA iterations. Fixed iteration budgets preserve replay identity.

## 3. Transport process

For each representative season:

1. compute edge time from current flow and BPR capacity pressure;
2. find a shortest path separately for every available mode;
3. assign modal shares with a stabilized multinomial logit;
4. load edge flow;
5. update flows with method of successive averages;
6. compute destination-opportunity accessibility from minimum modal generalized cost.

A transport policy changes declared edge capacity. It does not directly overwrite the resulting accessibility when the transport slice is configured.

## 4. Environmental entities

Each environmental unit declares green fraction, traffic exposure factor, activity intensity, night-light intensity, linked transport edges, and evidence authority. Every campaign declares four unique seasonal profiles and explicit air/noise/light/heat aggregation weights.

## 5. Relative exposure process

For each unit and representative season:

- air exposure is a bounded background plus traffic-pressure potential;
- noise uses logarithmic addition over background dB;
- light is night-light intensity multiplied by seasonal night length;
- heat combines seasonal stress, green cooling, and activity heat;
- the four burdens are combined into a normalized environment-quality proxy.

The annual household relocation phase consumes the mean quality of the four representative seasons. A blue-green policy changes green fraction and therefore heat exposure; it does not directly set quality.

## 6. Current qualification invariants

Automated tests establish that:

- BPR time increases under over-capacity flow;
- low-capacity road pressure shifts modal share toward rail;
- assignment and input-order replay are exact;
- edge-capacity investment lowers generalized cost and raises job accessibility;
- summer heat exceeds winter heat under the frozen synthetic profile;
- green fraction lowers heat and raises quality;
- traffic pressure raises air and logarithmic noise exposure;
- a sensitive household cohort responds to mean seasonal quality;
- strict schemas reject undeclared or incomplete transport/environment configurations.

## 7. Boundaries

Not yet represented:

- observed Haidian networks, OD matrices, schedules, fares, traffic counts, or capacities;
- transfers within one multimodal path, crowding, queue spillback, junction control, or departure-time choice;
- calibrated pollutant dispersion, acoustics, radiative heat, energy, or stormwater physics;
- AequilibraE selected-scenario oracle comparison;
- empirical calibration or predictive validation.

All current inputs and outputs are synthetic mechanism evidence. Formal statistical claims require the planned matched-world qualification campaign and convergence diagnostics.
