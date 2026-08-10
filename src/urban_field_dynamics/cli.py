"""Command-line entry points for qualified campaign artifacts."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from urban_field_dynamics.bounded_export import export_bounded_campaign, verify_bounded_export
from urban_field_dynamics.export import export_campaign, verify_export
from urban_field_dynamics.scaled_integrated import (
    scaled_integrated_campaign,
    scaled_stress_evidence_spec,
)
from urban_field_dynamics.smoke import smoke_campaign_spec
from urban_field_dynamics.stress import export_stress_matrix, verify_stress_export
from urban_field_dynamics.sweep import PolicySweepSpec, SweepMetric, build_policy_intensity_sweep
from urban_field_dynamics.sweep_export import (
    SweepThresholdSpec,
    export_bounded_sweep,
    verify_bounded_sweep,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="urban-field")
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke", help="run and export smoke-v1")
    smoke.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify", help="verify and replay an export")
    verify.add_argument("export_dir", type=Path)

    qualification = subparsers.add_parser(
        "scaled-qualification", help="run a bounded scaled synthetic campaign"
    )
    qualification.add_argument("--output", required=True, type=Path)
    qualification.add_argument("--worlds", type=int, default=32)
    qualification.add_argument("--end-year", type=int, default=2050)
    qualification.add_argument("--workers", type=int, default=4)
    qualification.add_argument("--source-revision", default="unspecified")

    verify_bounded = subparsers.add_parser(
        "verify-bounded", help="verify and replay bounded campaign evidence"
    )
    verify_bounded.add_argument("export_dir", type=Path)
    verify_bounded.add_argument("--workers", type=int, default=4)

    sweep = subparsers.add_parser("scaled-sweep", help="run a bounded synthetic P3 intensity sweep")
    sweep.add_argument("--output", required=True, type=Path)
    sweep.add_argument("--worlds", type=int, default=8)
    sweep.add_argument("--end-year", type=int, default=2050)
    sweep.add_argument("--workers", type=int, default=4)
    sweep.add_argument("--source-revision", default="unspecified")

    verify_sweep = subparsers.add_parser(
        "verify-sweep", help="verify and replay bounded sweep evidence"
    )
    verify_sweep.add_argument("export_dir", type=Path)
    verify_sweep.add_argument("--workers", type=int, default=4)

    stress = subparsers.add_parser("scaled-stress", help="run bounded synthetic stress evidence")
    stress.add_argument("--output", required=True, type=Path)
    stress.add_argument("--worlds", type=int, default=8)
    stress.add_argument("--end-year", type=int, default=2050)
    stress.add_argument("--workers", type=int, default=4)
    stress.add_argument("--source-revision", default="unspecified")

    verify_stress = subparsers.add_parser(
        "verify-stress", help="verify and replay bounded stress evidence"
    )
    verify_stress.add_argument("export_dir", type=Path)
    verify_stress.add_argument("--workers", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected command and return a process-style exit code."""

    args = _parser().parse_args(argv)
    if args.command == "smoke":
        spec = smoke_campaign_spec()
        output = export_campaign(spec, args.output)
        print(f"exported {spec.campaign_id} to {output}")
        return 0
    if args.command == "verify":
        result = verify_export(args.export_dir)
        print(f"verified {result.campaign_id} in {args.export_dir}")
        return 0
    if args.command == "scaled-qualification":
        if args.worlds <= 0:
            raise ValueError("worlds must be positive")
        if args.workers <= 0:
            raise ValueError("workers must be positive")
        spec = scaled_integrated_campaign(
            world_count=args.worlds,
            end_year=args.end_year,
        )
        output = export_bounded_campaign(
            spec,
            args.output,
            max_workers=None if args.workers == 1 else args.workers,
            source_revision=args.source_revision,
        )
        print(f"exported bounded {spec.campaign_id} to {output}")
        return 0
    if args.command == "verify-bounded":
        if args.workers <= 0:
            raise ValueError("workers must be positive")
        result = verify_bounded_export(
            args.export_dir,
            max_workers=None if args.workers == 1 else args.workers,
        )
        print(f"verified bounded {result.campaign_id} in {args.export_dir}")
        return 0
    if args.command == "scaled-sweep":
        if args.worlds <= 0:
            raise ValueError("worlds must be positive")
        if args.workers <= 0:
            raise ValueError("workers must be positive")
        stage = "canary" if args.worlds < 32 else "qualification"
        sweep_id = f"scaled-p3-intensity-{stage}-{args.worlds}"
        built = build_policy_intensity_sweep(
            scaled_integrated_campaign(world_count=args.worlds, end_year=args.end_year),
            PolicySweepSpec(
                sweep_id=sweep_id,
                source_arm_id="p3",
                intensities=(0.0, 0.25, 0.5, 0.75, 1.0),
            ),
        )
        output = export_bounded_sweep(
            built,
            args.output,
            metrics=(
                SweepMetric.FINAL_ACCESSIBILITY,
                SweepMetric.FINAL_ENVIRONMENT_QUALITY,
                SweepMetric.FINAL_RENT,
            ),
            thresholds=(
                SweepThresholdSpec(
                    metric=SweepMetric.FINAL_ACCESSIBILITY,
                    threshold=0.524,
                    threshold_status="synthetic-engineering-demo",
                ),
            ),
            max_workers=None if args.workers == 1 else args.workers,
            source_revision=args.source_revision,
        )
        print(f"exported {sweep_id} to {output}")
        return 0
    if args.command == "verify-sweep":
        if args.workers <= 0:
            raise ValueError("workers must be positive")
        evidence = verify_bounded_sweep(
            args.export_dir,
            max_workers=None if args.workers == 1 else args.workers,
        )
        print(f"verified sweep {evidence.sweep_id} in {args.export_dir}")
        return 0
    if args.command == "scaled-stress":
        if args.worlds <= 0:
            raise ValueError("worlds must be positive")
        if args.workers <= 0:
            raise ValueError("workers must be positive")
        evidence_spec = scaled_stress_evidence_spec(
            world_count=args.worlds,
            end_year=args.end_year,
        )
        evidence = export_stress_matrix(
            evidence_spec,
            args.output,
            max_workers=None if args.workers == 1 else args.workers,
            source_revision=args.source_revision,
        )
        print(f"exported stress matrix {evidence.matrix_id} to {args.output}")
        return 0
    if args.command == "verify-stress":
        if args.workers <= 0:
            raise ValueError("workers must be positive")
        evidence = verify_stress_export(
            args.export_dir,
            max_workers=None if args.workers == 1 else args.workers,
        )
        print(f"verified stress matrix {evidence.matrix_id} in {args.export_dir}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
