"""Command-line entry points for qualified campaign artifacts."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from urban_field_dynamics.export import export_campaign, verify_export
from urban_field_dynamics.smoke import smoke_campaign_spec


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="urban-field")
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke", help="run and export smoke-v1")
    smoke.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify", help="verify and replay an export")
    verify.add_argument("export_dir", type=Path)
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
    raise AssertionError(f"unhandled command: {args.command}")
