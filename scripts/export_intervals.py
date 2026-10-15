"""Recompute every episode-clustered paired bootstrap interval from the released
per-episode, per-cell outcome table, independently of the simulator and of
run_pilot.py.

Input : results/pilot_v1/episode_cell_outcomes.csv  (written by run_pilot.py)
Output: results/pilot_v1/intervals.json and intervals.md

The resampling unit is the parent episode: all timing cells of a resampled
episode are drawn together. For a single cell this is an ordinary paired
bootstrap over the 94 test episodes. The random baseline is compared on its
10-seed-averaged per-row completion.

    python scripts/export_intervals.py --csv results/pilot_v1/episode_cell_outcomes.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

N_BOOT = 2000
SEED = 0
DT_MS = 50

SUPERVISORS = {
    "nominal": "Nominal",
    "reactive_slip+squeeze": "Reactive slip + squeeze",
    "failure_predictor+squeeze": "Future-loss + squeeze",
    "value_delay_agnostic": "Value, delay-agnostic",
    "value_delay_aware": "Value, delay-aware",
    "oracle_menu": "Oracle (privileged)",
    "random_budget": "Random @ budget (10-seed mean)",
    "failure_predictor+squeeze@celltuned": "Future-loss + squeeze (per-cell thr.)",
    "value_delay_agnostic@celltuned": "Value, delay-agnostic (per-cell thr.)",
    "value_delay_aware@celltuned": "Value, delay-aware (per-cell thr.)",
}

# (a, b): interval on completion(a) - completion(b)
COMPARISONS = [
    ("reactive_slip+squeeze", "nominal"),
    ("failure_predictor+squeeze", "nominal"),
    ("value_delay_agnostic", "nominal"),
    ("value_delay_aware", "nominal"),
    ("oracle_menu", "nominal"),
    ("random_budget", "nominal"),
    ("value_delay_aware", "value_delay_agnostic"),
    ("value_delay_aware", "failure_predictor+squeeze"),
    ("value_delay_agnostic", "failure_predictor+squeeze"),
    ("failure_predictor+squeeze", "reactive_slip+squeeze"),
    ("value_delay_agnostic", "reactive_slip+squeeze"),
    ("value_delay_aware", "reactive_slip+squeeze"),
    ("value_delay_aware", "random_budget"),
    ("oracle_menu", "value_delay_aware"),
    ("oracle_menu", "failure_predictor+squeeze"),
    ("failure_predictor+squeeze@celltuned", "failure_predictor+squeeze"),
    ("value_delay_agnostic@celltuned", "value_delay_agnostic"),
    ("value_delay_aware@celltuned", "value_delay_aware"),
    ("value_delay_aware@celltuned", "value_delay_agnostic@celltuned"),
    ("value_delay_aware@celltuned", "failure_predictor+squeeze@celltuned"),
]


def load(csv_path: Path):
    """Return {supervisor: {(age, delay): {episode: completion_prob}}}."""
    rows = defaultdict(lambda: defaultdict(dict))
    seeds = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            key = (int(r["age_steps"]), int(r["delay_steps"]))
            ep = int(r["episode"])
            placed = 1.0 if r["outcome"] == "placed" else 0.0
            name = r["supervisor"]
            if name.startswith("random_budget@seed"):
                seeds["random_budget"][key][ep].append(placed)
            elif name == "random_budget":
                continue  # seed-0 copy; replaced by the seed average below
            else:
                rows[name][key][ep] = placed
    for key, eps in seeds["random_budget"].items():
        for ep, vals in eps.items():
            rows["random_budget"][key][ep] = float(np.mean(vals))
    return rows


def cluster_bootstrap(diff_by_ep: dict[int, list[float]], rng) -> dict:
    eps = sorted(diff_by_ep)
    tot = np.array([sum(diff_by_ep[e]) for e in eps])
    cnt = np.array([len(diff_by_ep[e]) for e in eps], dtype=float)
    idx = rng.integers(0, len(eps), size=(N_BOOT, len(eps)))
    boots = tot[idx].sum(axis=1) / cnt[idx].sum(axis=1)
    return {
        "mean": float(tot.sum() / cnt.sum()),
        "ci_low": float(np.quantile(boots, 0.025)),
        "ci_high": float(np.quantile(boots, 0.975)),
        "n_episodes": len(eps),
        "n_rows": int(cnt.sum()),
    }


def compare(rows, a: str, b: str, cells) -> dict:
    rng = np.random.default_rng(SEED)
    diff = defaultdict(list)
    for key in cells:
        ra, rb = rows[a][key], rows[b][key]
        assert set(ra) == set(rb), (a, b, key)
        for ep in ra:
            diff[ep].append(ra[ep] - rb[ep])
    return cluster_bootstrap(diff, rng)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=Path("results/pilot_v1/episode_cell_outcomes.csv"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out_dir = args.out or args.csv.parent
    rows = load(args.csv)
    cells = sorted(rows["nominal"])
    ages = sorted({a for a, _ in cells})
    delays = sorted({d for _, d in cells})

    result = {
        "method": "paired cluster bootstrap over parent episodes; 2000 resamples; seed 0; "
        "percentile 95% interval of completion(a) - completion(b)",
        "source_csv": str(args.csv),
        "n_test_episodes": len(rows["nominal"][cells[0]]),
        "cells": [f"age{a}_delay{d}" for a, d in cells],
        "completion": {},
        "pooled": {},
        "per_cell": {},
        "per_delay_pooled_over_ages": {},
        "per_age_pooled_over_delays": {},
    }
    for name in SUPERVISORS:
        if name in rows:
            result["completion"][name] = {
                "pooled": float(np.mean([np.mean(list(rows[name][k].values())) for k in cells])),
                "cells": {f"age{a}_delay{d}": float(np.mean(list(rows[name][(a, d)].values()))) for a, d in cells},
            }
    for a, b in COMPARISONS:
        if a not in rows or b not in rows:
            continue
        key = f"{a}__minus__{b}"
        result["pooled"][key] = compare(rows, a, b, cells)
        result["per_cell"][key] = {f"age{x}_delay{y}": compare(rows, a, b, [(x, y)]) for x, y in cells}
        result["per_delay_pooled_over_ages"][key] = {
            f"delay{d}": compare(rows, a, b, [(x, y) for x, y in cells if y == d]) for d in delays
        }
        result["per_age_pooled_over_delays"][key] = {
            f"age{x0}": compare(rows, a, b, [(x, y) for x, y in cells if x == x0]) for x0 in ages
        }

    with open(out_dir / "intervals.json", "w") as f:
        json.dump(result, f, indent=1)

    # Markdown summary in percentage points.
    def fmt(c):
        return f"{100*c['mean']:+.1f} [{100*c['ci_low']:+.1f}, {100*c['ci_high']:+.1f}]"

    lines = [
        "# Episode-clustered paired bootstrap intervals (test split)",
        "",
        f"Completion differences in percentage points, 95% percentile intervals, {N_BOOT} resamples, "
        f"resampling unit = parent episode (n = {result['n_test_episodes']}). "
        "Recomputed by `scripts/export_intervals.py` from `episode_cell_outcomes.csv`.",
        "",
        "## Pooled over the 12 timing cells",
        "",
        "| a − b | difference [95% CI] |",
        "|---|---|",
    ]
    for key, c in result["pooled"].items():
        a, b = key.split("__minus__")
        lines.append(f"| {SUPERVISORS[a]} − {SUPERVISORS[b]} | {fmt(c)} |")
    lines += ["", "## Per response delay (pooled over observation ages)", ""]
    hdr = "| a − b | " + " | ".join(f"delay {d*DT_MS} ms" for d in delays) + " |"
    lines += [hdr, "|---|" + "---|" * len(delays)]
    for key, per in result["per_delay_pooled_over_ages"].items():
        a, b = key.split("__minus__")
        lines.append(f"| {SUPERVISORS[a]} − {SUPERVISORS[b]} | " + " | ".join(fmt(per[f"delay{d}"]) for d in delays) + " |")
    lines += ["", "## Per observation age (pooled over response delays)", ""]
    hdr = "| a − b | " + " | ".join(f"age {a*DT_MS} ms" for a in ages) + " |"
    lines += [hdr, "|---|" + "---|" * len(ages)]
    for key, per in result["per_age_pooled_over_delays"].items():
        a, b = key.split("__minus__")
        lines.append(f"| {SUPERVISORS[a]} − {SUPERVISORS[b]} | " + " | ".join(fmt(per[f"age{x}"]) for x in ages) + " |")
    lines += ["", "## Per cell", ""]
    for key, per in result["per_cell"].items():
        a, b = key.split("__minus__")
        lines += [f"### {SUPERVISORS[a]} − {SUPERVISORS[b]}", "", "| | " + " | ".join(f"delay {d*DT_MS}" for d in delays) + " |", "|---|" + "---|" * len(delays)]
        for x in ages:
            lines.append(f"| age {x*DT_MS} ms | " + " | ".join(fmt(per[f"age{x}_delay{d}"]) for d in delays) + " |")
        lines.append("")
    (out_dir / "intervals.md").write_text("\n".join(lines))
    print(f"wrote {out_dir/'intervals.json'} and {out_dir/'intervals.md'}")
    for key, c in result["pooled"].items():
        a, b = key.split("__minus__")
        print(f"{SUPERVISORS[a]:40s} − {SUPERVISORS[b]:40s} {fmt(c)}")


if __name__ == "__main__":
    main()
