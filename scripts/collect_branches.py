"""Collect parent episodes and matched remedy/delay branch tables.

Example:
    python scripts/collect_branches.py --n 400 --seed 0 --workers 8 --out runs/pilot_v1/branches
"""

from __future__ import annotations

import argparse
from pathlib import Path

from delayed_recovery import config as C
from delayed_recovery.collect import collect_dataset


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("runs/pilot_v1/branches"))
    args = ap.parse_args()
    conditions = C.PhysicsGrid().sample(args.n, args.seed)
    delays = C.TimingGrid().response_delays
    print(f"collecting {args.n} episodes, delays={delays}, workers={args.workers}")
    out = collect_dataset(conditions, delays, args.out, workers=args.workers)
    print("saved to", out)


if __name__ == "__main__":
    main()
