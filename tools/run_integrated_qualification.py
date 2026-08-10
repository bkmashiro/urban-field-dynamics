#!/usr/bin/env python3
"""Run and replay-verify the integrated qualification campaign."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from urban_field_dynamics.analysis import integrated_qualification_diagnostics
from urban_field_dynamics.export import export_campaign, verify_export
from urban_field_dynamics.integrated import integrated_smoke_campaign


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worlds", type=int, default=64)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.worlds < 8:
        parser.error("--worlds must be at least 8")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error(f"--output must be new or empty: {args.output}")

    args.output.mkdir(parents=True, exist_ok=True)
    checkpoints = tuple(size for size in (8, 16, 32, 64, 128, 256, 512) if size <= args.worlds)
    started = time.perf_counter()
    campaign_dir = args.output / "campaign"
    export_campaign(integrated_smoke_campaign(world_count=args.worlds), campaign_dir)
    result = verify_export(campaign_dir)
    diagnostics = integrated_qualification_diagnostics(result, checkpoints=checkpoints)
    diagnostics_path = args.output / "qualification-diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            diagnostics.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - started
    print(
        f"verified {result.campaign_id}: {result.summary.run_count} runs, "
        f"{args.worlds} matched worlds, {elapsed:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
