"""Declared exogenous stress transforms and matched matrix evidence."""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.campaign import (
    CampaignResult,
    CampaignSpec,
    run_campaign,
    run_campaign_parallel,
)

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
BoundedDelta = Annotated[float, Field(ge=-1.0, le=1.0)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")]


class StressScenario(BaseModel):
    """One policy-independent exogenous transform."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    scenario_id: Identifier
    household_growth_rate_delta: BoundedDelta = 0.0
    firm_growth_rate_delta: BoundedDelta = 0.0
    firm_death_probability_delta: BoundedDelta = 0.0
    firm_birth_probability_multiplier: NonNegativeFloat = 1.0
    transport_capacity_multiplier: PositiveFloat = 1.0
    heat_stress_delta: BoundedDelta = 0.0
    service_capacity_multiplier: PositiveFloat = 1.0
    annual_budget_multiplier: PositiveFloat = 1.0
    cumulative_budget_multiplier: PositiveFloat = 1.0


class StressMatrixSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    matrix_id: Identifier
    base_campaign: CampaignSpec
    scenarios: tuple[StressScenario, ...]

    @model_validator(mode="after")
    def validate_scenarios(self) -> StressMatrixSpec:
        ids = [scenario.scenario_id for scenario in self.scenarios]
        if not ids or ids[0] != "baseline":
            raise ValueError("first stress scenario must be baseline")
        if len(ids) != len(set(ids)):
            raise ValueError("stress scenario IDs must be unique")
        if self.scenarios[0] != StressScenario(scenario_id="baseline"):
            raise ValueError("baseline stress scenario must be neutral")
        return self


def _clamp_unit(value: float) -> float:
    return min(1.0, max(0.0, value))


def apply_stress(base: CampaignSpec, scenario: StressScenario) -> CampaignSpec:
    """Clone one campaign with only declared exogenous inputs transformed."""

    updates: dict[str, object] = {
        "campaign_id": f"{base.campaign_id}-s-{scenario.scenario_id}",
    }
    if base.household_dynamics is None:
        if scenario.household_growth_rate_delta != 0.0:
            raise ValueError("household growth stress requires household dynamics")
    else:
        updates["household_dynamics"] = base.household_dynamics.model_copy(
            update={
                "mean_growth_rate": (
                    base.household_dynamics.mean_growth_rate + scenario.household_growth_rate_delta
                )
            }
        )
    if base.firm_dynamics is None:
        if (
            scenario.firm_growth_rate_delta != 0.0
            or scenario.firm_death_probability_delta != 0.0
            or scenario.firm_birth_probability_multiplier != 1.0
        ):
            raise ValueError("firm stress requires firm dynamics")
    else:
        prototypes = tuple(
            prototype.model_copy(
                update={
                    "annual_birth_probability": _clamp_unit(
                        prototype.annual_birth_probability
                        * scenario.firm_birth_probability_multiplier
                    )
                }
            )
            for prototype in base.firm_dynamics.birth_prototypes
        )
        updates["firm_dynamics"] = base.firm_dynamics.model_copy(
            update={
                "mean_employee_growth_rate": (
                    base.firm_dynamics.mean_employee_growth_rate + scenario.firm_growth_rate_delta
                ),
                "annual_death_probability": _clamp_unit(
                    base.firm_dynamics.annual_death_probability
                    + scenario.firm_death_probability_delta
                ),
                "birth_prototypes": prototypes,
            }
        )
    updates["transport_edges"] = tuple(
        edge.model_copy(update={"capacity": edge.capacity * scenario.transport_capacity_multiplier})
        for edge in base.transport_edges
    )
    updates["seasonal_environment"] = tuple(
        season.model_copy(
            update={"heat_stress": _clamp_unit(season.heat_stress + scenario.heat_stress_delta)}
        )
        for season in base.seasonal_environment
    )
    updates["locations"] = tuple(
        location.model_copy(
            update={
                "service_capacity": (
                    location.service_capacity * scenario.service_capacity_multiplier
                    if location.service_capacity is not None
                    else None
                )
            }
        )
        for location in base.locations
    )
    if base.infrastructure_ledger is None:
        if scenario.annual_budget_multiplier != 1.0 or scenario.cumulative_budget_multiplier != 1.0:
            raise ValueError("budget stress requires an infrastructure ledger")
    else:
        updates["infrastructure_ledger"] = base.infrastructure_ledger.model_copy(
            update={
                "annual_budget": (
                    base.infrastructure_ledger.annual_budget * scenario.annual_budget_multiplier
                ),
                "cumulative_budget": (
                    base.infrastructure_ledger.cumulative_budget
                    * scenario.cumulative_budget_multiplier
                ),
            }
        )
    values = base.model_dump(mode="python")
    values.update(updates)
    return CampaignSpec.model_validate(values)


class StressMetric(StrEnum):
    REDEVELOPMENTS = "redevelopments"
    FINAL_ACCESSIBILITY = "final_accessibility"
    FINAL_ENVIRONMENT_QUALITY = "final_environment_quality"
    FINAL_RENT = "final_rent"
    FINAL_POPULATION = "final_population"
    FINAL_EMPLOYMENT = "final_employment"
    FINAL_UNEMPLOYMENT = "final_unemployment"
    FINAL_SERVICE_UNMET = "final_service_unmet"
    CUMULATIVE_PUBLIC_SPEND = "cumulative_public_spend"


HIGHER_IS_BETTER = {
    StressMetric.REDEVELOPMENTS: True,
    StressMetric.FINAL_ACCESSIBILITY: True,
    StressMetric.FINAL_ENVIRONMENT_QUALITY: True,
    StressMetric.FINAL_RENT: False,
    StressMetric.FINAL_POPULATION: True,
    StressMetric.FINAL_EMPLOYMENT: True,
    StressMetric.FINAL_UNEMPLOYMENT: False,
    StressMetric.FINAL_SERVICE_UNMET: False,
    StressMetric.CUMULATIVE_PUBLIC_SPEND: False,
}


class StressEvidenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    matrix: StressMatrixSpec
    metrics: tuple[StressMetric, ...]

    @model_validator(mode="after")
    def unique_metrics(self) -> StressEvidenceSpec:
        if not self.metrics or len(self.metrics) != len(set(self.metrics)):
            raise ValueError("stress metrics must be non-empty and unique")
        return self


class StressDeltaSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    baseline_id: str
    comparator_id: str
    arm_id: str
    metric: StressMetric
    higher_is_better: bool
    world_count: int = Field(gt=0)
    mean_raw_delta: float
    mean_improvement: float
    harmed_world_count: int = Field(ge=0)
    harmed_fraction: float = Field(ge=0.0, le=1.0)
    worst_harm: NonNegativeFloat


class StressMatrixEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    matrix_id: str
    scenario_campaign_ids: dict[str, str]
    scenario_arm_means: dict[str, dict[str, dict[str, float]]]
    scenario_shifts: dict[str, StressDeltaSummary]
    policy_effects: dict[str, StressDeltaSummary]


def _metric_value(run: object, metric: StressMetric) -> float:
    world = run.world
    if metric is StressMetric.REDEVELOPMENTS:
        return float(sum(year is not None for year in world.redevelopment_years.values()))
    if metric is StressMetric.FINAL_ACCESSIBILITY:
        return sum(world.final_accessibility.values()) / len(world.final_accessibility)
    if metric is StressMetric.FINAL_ENVIRONMENT_QUALITY:
        return sum(world.final_environment_quality.values()) / len(world.final_environment_quality)
    if metric is StressMetric.FINAL_RENT:
        return sum(world.final_rents.values()) / len(world.final_rents)
    if metric is StressMetric.FINAL_POPULATION:
        return sum(world.final_household_populations.values())
    if metric is StressMetric.FINAL_EMPLOYMENT:
        return sum(world.final_firm_employees.values())
    if metric is StressMetric.FINAL_UNEMPLOYMENT:
        if not world.labor_traces:
            raise ValueError("unemployment stress metric requires labor traces")
        return world.labor_traces[max(world.labor_traces)].unemployment_rate
    if not world.infrastructure_traces:
        raise ValueError(f"{metric.value} requires infrastructure traces")
    infrastructure = world.infrastructure_traces[max(world.infrastructure_traces)]
    if metric is StressMetric.FINAL_SERVICE_UNMET:
        return sum(infrastructure.service_unmet_demand_by_location.values())
    if metric is StressMetric.CUMULATIVE_PUBLIC_SPEND:
        return infrastructure.cumulative_public_spend
    raise AssertionError(f"unsupported stress metric: {metric}")


def _common_entity_identity(left: dict[int, dict], right: dict[int, dict]) -> bool:
    for year in set(left) & set(right):
        left_values = left[year]
        right_values = right[year]
        for entity_id in set(left_values) & set(right_values):
            if left_values[entity_id] != right_values[entity_id]:
                return False
    return True


def assert_matched_stress_random_identity(
    results: dict[str, CampaignResult],
    scenario_ids: tuple[str, ...],
) -> None:
    """Reject stress matrices that shift common-entity random streams."""

    baseline = results[scenario_ids[0]]
    baseline_runs = {(run.arm_id, run.world.world_id): run.world for run in baseline.runs}
    fields = (
        "development_shocks",
        "household_taste_shocks",
        "firm_taste_shocks",
        "household_growth_shocks",
        "firm_death_shocks",
        "firm_expansion_shocks",
        "firm_birth_shocks",
    )
    for scenario_id in scenario_ids[1:]:
        comparator_runs = {
            (run.arm_id, run.world.world_id): run.world for run in results[scenario_id].runs
        }
        if set(comparator_runs) != set(baseline_runs):
            raise ValueError("stress matrix changed arm/world identity")
        for key, baseline_world in baseline_runs.items():
            comparator_world = comparator_runs[key]
            for field in fields:
                if not _common_entity_identity(
                    getattr(baseline_world, field),
                    getattr(comparator_world, field),
                ):
                    raise ValueError(
                        f"stress random identity mismatch: scenario={scenario_id} "
                        f"arm={key[0]} world={key[1]} field={field}"
                    )


def run_stress_matrix(
    spec: StressMatrixSpec,
    *,
    max_workers: int | None = None,
) -> dict[str, CampaignResult]:
    results: dict[str, CampaignResult] = {}
    for scenario in spec.scenarios:
        campaign = apply_stress(spec.base_campaign, scenario)
        results[scenario.scenario_id] = (
            run_campaign(campaign)
            if max_workers is None
            else run_campaign_parallel(campaign, max_workers=max_workers)
        )
    assert_matched_stress_random_identity(
        results,
        tuple(scenario.scenario_id for scenario in spec.scenarios),
    )
    return results


def _values_by_arm(
    result: CampaignResult,
    metrics: tuple[StressMetric, ...],
) -> dict[str, dict[StressMetric, tuple[float, ...]]]:
    values: dict[str, dict[StressMetric, tuple[float, ...]]] = {}
    for arm_id in result.summary.arms:
        runs = sorted(
            (run for run in result.runs if run.arm_id == arm_id),
            key=lambda run: run.world.world_id,
        )
        values[arm_id] = {
            metric: tuple(_metric_value(run, metric) for run in runs) for metric in metrics
        }
    return values


def _delta_summary(
    *,
    baseline_id: str,
    comparator_id: str,
    arm_id: str,
    metric: StressMetric,
    baseline: tuple[float, ...],
    comparator: tuple[float, ...],
) -> StressDeltaSummary:
    if len(baseline) != len(comparator) or not baseline:
        raise ValueError("stress delta inputs must be non-empty and matched")
    raw = tuple(right - left for left, right in zip(baseline, comparator, strict=True))
    higher = HIGHER_IS_BETTER[metric]
    improvements = raw if higher else tuple(-value for value in raw)
    harms = tuple(max(0.0, -value) for value in improvements)
    return StressDeltaSummary(
        baseline_id=baseline_id,
        comparator_id=comparator_id,
        arm_id=arm_id,
        metric=metric,
        higher_is_better=higher,
        world_count=len(raw),
        mean_raw_delta=sum(raw) / len(raw),
        mean_improvement=sum(improvements) / len(improvements),
        harmed_world_count=sum(value > 0.0 for value in harms),
        harmed_fraction=sum(value > 0.0 for value in harms) / len(harms),
        worst_harm=max(harms),
    )


def summarize_stress_matrix(
    spec: StressEvidenceSpec,
    results: dict[str, CampaignResult],
    *,
    policy_arm_ids: tuple[str, ...] = ("p0", "p1", "p2", "p3"),
) -> StressMatrixEvidence:
    scenario_ids = tuple(scenario.scenario_id for scenario in spec.matrix.scenarios)
    if set(results) != set(scenario_ids):
        raise ValueError("stress results do not match declared scenarios")
    values = {
        scenario_id: _values_by_arm(results[scenario_id], spec.metrics)
        for scenario_id in scenario_ids
    }
    means = {
        scenario_id: {
            arm_id: {
                metric.value: sum(metric_values) / len(metric_values)
                for metric, metric_values in arm_values.items()
            }
            for arm_id, arm_values in scenario_values.items()
        }
        for scenario_id, scenario_values in values.items()
    }
    baseline_scenario = scenario_ids[0]
    shifts: dict[str, StressDeltaSummary] = {}
    for scenario_id in scenario_ids[1:]:
        for arm_id in values[baseline_scenario]:
            for metric in spec.metrics:
                key = f"{scenario_id}:{arm_id}:{metric.value}"
                shifts[key] = _delta_summary(
                    baseline_id=baseline_scenario,
                    comparator_id=scenario_id,
                    arm_id=arm_id,
                    metric=metric,
                    baseline=values[baseline_scenario][arm_id][metric],
                    comparator=values[scenario_id][arm_id][metric],
                )
    policy_effects: dict[str, StressDeltaSummary] = {}
    baseline_arm = policy_arm_ids[0]
    for scenario_id in scenario_ids:
        for arm_id in policy_arm_ids[1:]:
            for metric in spec.metrics:
                key = f"{scenario_id}:{arm_id}:{metric.value}"
                policy_effects[key] = _delta_summary(
                    baseline_id=baseline_arm,
                    comparator_id=arm_id,
                    arm_id=arm_id,
                    metric=metric,
                    baseline=values[scenario_id][baseline_arm][metric],
                    comparator=values[scenario_id][arm_id][metric],
                )
    return StressMatrixEvidence(
        matrix_id=spec.matrix.matrix_id,
        scenario_campaign_ids={
            scenario_id: results[scenario_id].campaign_id for scenario_id in scenario_ids
        },
        scenario_arm_means=means,
        scenario_shifts=shifts,
        policy_effects=policy_effects,
    )


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def _payloads(
    spec: StressEvidenceSpec,
    results: dict[str, CampaignResult],
) -> dict[str, bytes]:
    evidence = summarize_stress_matrix(spec, results)
    return {
        "stress-config.json": _canonical_json(spec.model_dump(mode="json")),
        "stress-evidence.json": _canonical_json(evidence.model_dump(mode="json")),
    }


def _manifest(payloads: dict[str, bytes]) -> bytes:
    return _canonical_json(
        {
            "format_version": 1,
            "package_version": version("urban-field-dynamics"),
            "files": {
                name: {"bytes": len(content), "sha256": sha256(content).hexdigest()}
                for name, content in sorted(payloads.items())
            },
        }
    )


def export_stress_matrix(
    spec: StressEvidenceSpec,
    output_dir: str | Path,
    *,
    max_workers: int | None = None,
) -> StressMatrixEvidence:
    """Run and write a bounded deterministic stress matrix."""

    results = run_stress_matrix(spec.matrix, max_workers=max_workers)
    payloads = _payloads(spec, results)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        (target / name).write_bytes(content)
    (target / "manifest.json").write_bytes(_manifest(payloads))
    return summarize_stress_matrix(spec, results)


def verify_stress_export(
    output_dir: str | Path,
    *,
    max_workers: int | None = None,
) -> StressMatrixEvidence:
    """Replay a frozen stress config and byte-compare every derived file."""

    target = Path(output_dir)
    config_bytes = (target / "stress-config.json").read_bytes()
    spec = StressEvidenceSpec.model_validate_json(config_bytes)
    results = run_stress_matrix(spec.matrix, max_workers=max_workers)
    rebuilt = _payloads(spec, results)
    if rebuilt["stress-config.json"] != config_bytes:
        raise ValueError("stress config is not canonical or changed during replay")
    for name, content in rebuilt.items():
        if (target / name).read_bytes() != content:
            raise ValueError(f"stress derived artifact differs on replay: {name}")
    if (target / "manifest.json").read_bytes() != _manifest(rebuilt):
        raise ValueError("stress manifest differs on replay")
    return summarize_stress_matrix(spec, results)
