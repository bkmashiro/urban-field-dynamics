"""Profile one authoritative scaled campaign and print a canonical result hash."""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import json
import pstats
import time
from pathlib import Path

from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.scaled_integrated import scaled_integrated_campaign


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worlds", type=int, default=1)
    parser.add_argument("--end-year", type=int, default=2050)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--top", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worlds <= 0:
        raise ValueError("worlds must be positive")
    spec = scaled_integrated_campaign(world_count=args.worlds, end_year=args.end_year)
    profiler = cProfile.Profile()
    started = time.perf_counter()
    result = profiler.runcall(run_campaign, spec)
    elapsed = time.perf_counter() - started
    args.profile.parent.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(args.profile)
    payload = json.dumps(
        result.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    print(
        f"{result.campaign_id} runs={result.summary.run_count} elapsed={elapsed:.3f}s "
        f"bytes={len(payload)} sha256={hashlib.sha256(payload).hexdigest()}"
    )
    pstats.Stats(profiler).strip_dirs().sort_stats("cumtime").print_stats(args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
