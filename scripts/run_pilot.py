"""Fit selectors, choose budgets on validation, evaluate on held-out episodes
across the observation-age x response-delay grid, and write results/figures.

Example:
    python scripts/run_pilot.py --data runs/pilot_v1/branches --out results/pilot_v1
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

from delayed_recovery import config as C
from delayed_recovery.collect import load_dataset
from delayed_recovery.controller import PHASES
from delayed_recovery.dataset import OUT_LOST, OUT_PLACED, R_CONT, build_decision_table, split_episodes, subset
from delayed_recovery.evaluate import (
    CellResult,
    bootstrap_paired,
    budget_curve,
    choose_threshold,
    choose_threshold_per_cell,
    pooled,
    recovery_frontier,
    run_grid,
    run_grid_per_cell,
)
from delayed_recovery.selectors import FixedRemedyDetector, Nominal, OracleMenu, RandomBudget, ValueSelector, feedback_null

BUDGET = 0.40  # max fraction of episodes with an intervention (pooled over the grid)
N_BOOT = 2000


def _mask(table, episodes: np.ndarray) -> np.ndarray:
    return np.isin(table.episode, episodes)


def cell_table(cells: Dict, metric: str) -> Dict[str, Dict[str, float]]:
    return {f"age{a}_delay{d}": {metric: c.metrics()[metric]} for (a, d), c in cells.items()}


def summarize(cells: Dict) -> Dict:
    return {
        "pooled": pooled(cells),
        "cells": {f"age{a}_delay{d}": c.metrics() for (a, d), c in cells.items()},
        "remedy_mix": {
            f"age{a}_delay{d}": {C.REMEDIES[r]: int((c.remedy == r).sum()) for r in range(len(C.REMEDIES)) if r != R_CONT}
            for (a, d), c in cells.items()
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("runs/pilot_v1/branches"))
    ap.add_argument("--out", type=Path, default=Path("results/pilot_v1"))
    ap.add_argument("--split-seed", type=int, default=0)
    ap.add_argument("--budget", type=float, default=BUDGET)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    index, logs = load_dataset(args.data)
    timing = C.TimingGrid()
    ages = timing.observation_ages
    delays = tuple(index["delays"])
    table = build_decision_table(logs, ages, delays)
    splits = split_episodes(logs, args.split_seed)
    train, val, test = (subset(table, _mask(table, splits[k])) for k in ("train", "val", "test"))
    outcomes = {o: int(sum(1 for l in logs if l["outcome"] == o)) for o in C.OUTCOMES}
    acquired = [l for l in logs if len(l["decision_steps"]) > 0]
    print(f"episodes={len(logs)} acquired={len(acquired)} outcomes={outcomes}")
    print(f"decision rows: train={len(train.step)} val={len(val.step)} test={len(test.step)}")

    # Raw collection counts and failure-development statistics (from the
    # per-episode branch files, so they are auditable from report.json alone).
    n_states = int(sum(len(l["decision_steps"]) for l in acquired))
    n_branches = int(sum(l["branch_outcome"][:, 1:, :].size for l in acquired))
    lost = [l for l in acquired if l["outcome"] == "lost"]
    slip_windows = [int(l["loss_step"] - l["first_slip_step"]) for l in lost if l["first_slip_step"] >= 0]
    push_onset = [int(l["transport_start_step"] + l["condition"]["disturb_offset"]) for l in lost]
    collection_stats = {
        "n_decision_states": n_states,
        "n_branches": n_branches,
        "n_lost_with_slip_onset": len(slip_windows),
        "slip_onset_to_loss_steps": {
            "min": int(min(slip_windows)),
            "p25": float(np.percentile(slip_windows, 25)),
            "median": float(np.median(slip_windows)),
            "p75": float(np.percentile(slip_windows, 75)),
            "max": int(max(slip_windows)),
        },
        "n_lost_at_or_after_push_onset": int(sum(l["loss_step"] >= t for l, t in zip(lost, push_onset))),
        "n_lost": len(lost),
        "loss_phase_counts": {ph: int(sum(1 for l in lost if l["phase"][-1] == i)) for i, ph in enumerate(PHASES)},
    }

    report: Dict = {
        "config": {
            "n_episodes": len(logs),
            "n_acquired": len(acquired),
            "nominal_outcomes": outcomes,
            "nominal_loss_rate_acquired": float(np.mean([l["outcome"] == "lost" for l in acquired])),
            "collection": collection_stats,
            "processor": platform.processor(),
            "ages_steps": list(ages),
            "delays_steps": list(delays),
            "control_dt": C.CONTROL_DT,
            "budget": args.budget,
            "split_sizes": {k: int(len(v)) for k, v in splits.items()},
            "split_seed": args.split_seed,
            "feature_window": C.FEATURE_WINDOW,
            "n_obs_features": int(train.x_obs.shape[1]),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "data_elapsed_s": index.get("elapsed_s"),
            "physics_grid": {
                "mass_range": C.PhysicsGrid().mass_range,
                "friction_range": C.PhysicsGrid().friction_range,
                "transport_speeds": C.PhysicsGrid().transport_speeds,
                "transport_accels": C.PhysicsGrid().transport_accels,
                "grasp_x_offset_range": C.PhysicsGrid().grasp_x_offset_range,
            },
        }
    }

    # ---------------------------------------------------------------- fit
    selectors = [
        Nominal(),
        FixedRemedyDetector("slip_now"),
        FixedRemedyDetector("nominal_lost"),
        ValueSelector(aware=False),
        ValueSelector(aware=True),
    ]
    fit_times = {}
    for s in selectors:
        t0 = time.time()
        s.fit(train, seed=args.split_seed)
        fit_times[s.name] = time.time() - t0
        if s.name != "nominal":
            thr, m = choose_threshold(s, val, args.budget)
            s.threshold = thr
            print(f"{s.name}: threshold={thr:.4f} val pooled completion={m.get('completion', float('nan')):.3f} rate={m.get('intervention_rate', float('nan')):.3f}")
    report["thresholds"] = {s.name: float(s.threshold) for s in selectors}
    report["fit_seconds"] = fit_times

    # Inference cost per decision (single row), ms.
    inf = {}
    for s in selectors:
        if s.name == "nominal":
            continue
        one = subset(test, np.arange(len(test.step)) < 1)
        ts = []
        for _ in range(50):
            t0 = time.perf_counter()
            s.decide(one, 0)
            ts.append((time.perf_counter() - t0) * 1000)
        inf[s.name] = {"p50_ms": float(np.percentile(ts, 50)), "p95_ms": float(np.percentile(ts, 95))}
    report["inference_ms_per_decision"] = inf

    # ------------------------------------------------------------ evaluate
    results: Dict[str, Dict] = {}
    cells_by_name: Dict[str, Dict] = {}
    for s in selectors:
        cells = run_grid(s, test)
        cells_by_name[s.name] = cells
        results[s.name] = summarize(cells)
    # Latency-tuned operating points (one threshold per timing cell, chosen on
    # validation): separates "knowing the latency when setting the operating
    # point" from "conditioning the value model on latency".
    cell_thresholds = {}
    for s in selectors:
        if s.name in ("failure_predictor+squeeze", "value_delay_agnostic", "value_delay_aware"):
            thr = choose_threshold_per_cell(s, val, args.budget)
            cell_thresholds[s.name] = {f"age{a}_delay{d}": float(t) for (a, d), t in thr.items()}
            name = s.name + "@celltuned"
            cells_by_name[name] = run_grid_per_cell(s, test, thr)
            results[name] = summarize(cells_by_name[name])
    report["cell_thresholds"] = cell_thresholds
    oracle = OracleMenu()
    cells_by_name["oracle_menu"] = run_grid(oracle, test)
    results["oracle_menu"] = summarize(cells_by_name["oracle_menu"])
    # Random at the realised budget of the delay-aware selector, averaged over seeds.
    realised = results["value_delay_aware"]["pooled"]["intervention_rate"]
    rand_pooled = []
    rand_cells_all = []
    for seed in range(10):
        rc = run_grid(RandomBudget(realised, seed), test)
        rand_cells_all.append(rc)
        rand_pooled.append(pooled(rc))
    results["random_budget"] = {
        "pooled": {k: float(np.mean([m[k] for m in rand_pooled])) for k in rand_pooled[0]},
        "cells": {
            f"age{a}_delay{d}": {k: float(np.mean([rc[(a, d)].metrics()[k] for rc in rand_cells_all])) for k in rand_pooled[0]}
            for (a, d) in rand_cells_all[0]
        },
        "budget": realised,
    }
    cells_by_name["random_budget"] = rand_cells_all[0]

    # Paired cluster bootstrap (unit = parent episode) of completion
    # differences, pooled over cells and per cell.
    def merged(cells: Dict) -> CellResult:
        keys = sorted(cells)
        return CellResult(
            age=-1,
            delay=-1,
            episode=np.concatenate([cells[k].episode for k in keys]),
            outcome=np.concatenate([cells[k].outcome for k in keys]),
            nominal_outcome=np.concatenate([cells[k].nominal_outcome for k in keys]),
            intervened=np.concatenate([cells[k].intervened for k in keys]),
            remedy=np.concatenate([cells[k].remedy for k in keys]),
            fire_step=np.concatenate([cells[k].fire_step for k in keys]),
            steps_before_loss=np.concatenate([cells[k].steps_before_loss for k in keys]),
        )

    comparisons = {}
    base = merged(cells_by_name["nominal"])
    for name in ("reactive_slip+squeeze", "failure_predictor+squeeze", "value_delay_agnostic", "value_delay_aware", "oracle_menu"):
        comparisons[f"{name}_vs_nominal"] = bootstrap_paired(merged(cells_by_name[name]), base, N_BOOT)
    # Random baseline: the per-row completion is averaged over the 10 seeds so
    # that the CI estimates the same quantity as the reported 10-seed mean.
    rand_merged = [merged(rc) for rc in rand_cells_all]
    rand_prob = np.mean([(m.outcome == OUT_PLACED).astype(float) for m in rand_merged], axis=0)
    comparisons["random_budget_vs_nominal"] = bootstrap_paired(rand_merged[0], base, N_BOOT, weights_a=rand_prob)
    comparisons["value_delay_aware_vs_value_delay_agnostic"] = bootstrap_paired(merged(cells_by_name["value_delay_aware"]), merged(cells_by_name["value_delay_agnostic"]), N_BOOT)
    comparisons["value_delay_aware_vs_failure_predictor"] = bootstrap_paired(merged(cells_by_name["value_delay_aware"]), merged(cells_by_name["failure_predictor+squeeze"]), N_BOOT)
    for name in ("failure_predictor+squeeze", "value_delay_agnostic", "value_delay_aware"):
        comparisons[f"{name}@celltuned_vs_pooled"] = bootstrap_paired(merged(cells_by_name[name + "@celltuned"]), merged(cells_by_name[name]), N_BOOT)
        comparisons[f"{name}@celltuned_vs_nominal"] = bootstrap_paired(merged(cells_by_name[name + "@celltuned"]), base, N_BOOT)
    comparisons["aware@celltuned_vs_agnostic@celltuned"] = bootstrap_paired(merged(cells_by_name["value_delay_aware@celltuned"]), merged(cells_by_name["value_delay_agnostic@celltuned"]), N_BOOT)
    comparisons["aware@celltuned_vs_failure_predictor@celltuned"] = bootstrap_paired(merged(cells_by_name["value_delay_aware@celltuned"]), merged(cells_by_name["failure_predictor+squeeze@celltuned"]), N_BOOT)
    per_cell = {}
    for (a, d) in cells_by_name["nominal"]:
        per_cell[f"age{a}_delay{d}"] = {
            "aware_vs_agnostic": bootstrap_paired(cells_by_name["value_delay_aware"][(a, d)], cells_by_name["value_delay_agnostic"][(a, d)], N_BOOT),
            "aware_vs_failure_predictor": bootstrap_paired(cells_by_name["value_delay_aware"][(a, d)], cells_by_name["failure_predictor+squeeze"][(a, d)], N_BOOT),
            "aware_vs_nominal": bootstrap_paired(cells_by_name["value_delay_aware"][(a, d)], cells_by_name["nominal"][(a, d)], N_BOOT),
            "aware@celltuned_vs_agnostic@celltuned": bootstrap_paired(cells_by_name["value_delay_aware@celltuned"][(a, d)], cells_by_name["value_delay_agnostic@celltuned"][(a, d)], N_BOOT),
            "aware@celltuned_vs_failure_predictor@celltuned": bootstrap_paired(cells_by_name["value_delay_aware@celltuned"][(a, d)], cells_by_name["failure_predictor+squeeze@celltuned"][(a, d)], N_BOOT),
        }
    comparisons["per_cell"] = per_cell
    report["comparisons"] = comparisons

    # ------------------------------------------------- feedback-null controls
    aware = next(s for s in selectors if s.name == "value_delay_aware")
    train_mean = train.x_obs.mean(axis=0)
    nulls = {}
    for mode in ("masked", "mismatched", "frozen"):
        t_null = feedback_null(test, mode, train_mean, seed=args.split_seed)
        cells = run_grid(aware, t_null)
        nulls[mode] = summarize(cells)
        nulls[mode]["vs_intact"] = bootstrap_paired(merged(cells), merged(cells_by_name["value_delay_aware"]), N_BOOT)
    report["feedback_null_value_delay_aware"] = nulls

    # ------------------------------------------------- budget curves (test)
    curves = {}
    for s in selectors:
        if s.name == "nominal":
            continue
        curves[s.name] = budget_curve(s, test)
    report["budget_curves_test"] = curves

    # ------------------------------------------------- recovery frontier
    fr = recovery_frontier(test)
    report["recovery_frontier_test"] = {
        "lead_steps": fr["lead_steps"].tolist(),
        "count": fr["count"].tolist(),
        "fraction_placed": fr["fraction_placed"].tolist(),
        "remedies": list(C.REMEDIES),
        "delays": list(delays),
    }
    # Remedy-specific deadlines: smallest lead (steps before nominal loss) whose
    # bin completes in >= 50% of states. Bins with fewer than MIN_BIN states are
    # excluded from the deadline summary; the pooled fraction over all lost
    # states is reported alongside so a sparse long-lead bin cannot masquerade
    # as a deadline.
    MIN_BIN = 20
    deadlines = {}
    pooled_fraction = {}
    counts = fr["count"]
    for r, remedy in enumerate(C.REMEDIES):
        if r == R_CONT:
            continue
        for k, d in enumerate(delays):
            frac = fr["fraction_placed"][:, r, k]
            ok = (frac >= 0.5) & (counts >= MIN_BIN)
            deadlines[f"{remedy}_delay{d}"] = int(fr["lead_steps"][ok].min()) if ok.any() else None
            pooled_fraction[f"{remedy}_delay{d}"] = float(np.nansum(frac * counts) / counts.sum())
    report["remedy_deadline_lead_steps_50pct"] = deadlines
    report["remedy_deadline_min_bin_states"] = MIN_BIN
    report["remedy_pooled_recovery_fraction"] = pooled_fraction

    # ------------------------------------------- held-out friction band variant
    band = (0.50, 0.58)
    fr_of = np.array([logs[e]["condition"]["friction"] for e in range(len(logs))])
    in_band = np.flatnonzero((fr_of >= band[0]) & (fr_of <= band[1]))
    acquired_idx = np.array([e for e, l in enumerate(logs) if len(l["decision_steps"]) > 0])
    band_test = np.intersect1d(in_band, acquired_idx)
    rest = np.setdiff1d(acquired_idx, band_test)
    rng = np.random.default_rng(args.split_seed + 1)
    perm = rng.permutation(rest)
    n_tr = int(0.7 * len(perm))
    b_train, b_val = subset(table, _mask(table, perm[:n_tr])), subset(table, _mask(table, perm[n_tr:]))
    b_test = subset(table, _mask(table, band_test))
    band_results = {}
    b_cells = {}
    for s in [Nominal(), FixedRemedyDetector("nominal_lost"), ValueSelector(aware=False), ValueSelector(aware=True)]:
        s.fit(b_train, seed=args.split_seed)
        if s.name != "nominal":
            s.threshold, _ = choose_threshold(s, b_val, args.budget)
        b_cells[s.name] = run_grid(s, b_test)
        band_results[s.name] = summarize(b_cells[s.name])["pooled"]
    band_results["oracle_menu"] = summarize(run_grid(OracleMenu(), b_test))["pooled"]
    band_results["aware_vs_agnostic"] = bootstrap_paired(merged(b_cells["value_delay_aware"]), merged(b_cells["value_delay_agnostic"]), N_BOOT)
    band_results["aware_vs_failure_predictor"] = bootstrap_paired(merged(b_cells["value_delay_aware"]), merged(b_cells["failure_predictor+squeeze"]), N_BOOT)
    report["held_out_friction_band"] = {"band": band, "n_test_episodes": int(len(band_test)), "n_train_episodes": int(n_tr), "results": band_results}

    report["results"] = results
    with open(args.out / "report.json", "w") as f:
        json.dump(report, f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)

    # Per-episode, per-cell closed-loop outcomes for every supervisor on the
    # test split, so uncertainty can be recomputed independently of this script.
    import csv

    with open(args.out / "episode_cell_outcomes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["supervisor", "age_steps", "delay_steps", "episode", "nominal_outcome", "outcome", "intervened", "remedy", "fire_step", "steps_before_loss"])
        for name, cells in cells_by_name.items():
            for (a, d), c in sorted(cells.items()):
                for i in range(len(c.episode)):
                    w.writerow([
                        name, a, d, int(c.episode[i]), C.OUTCOMES[int(c.nominal_outcome[i])], C.OUTCOMES[int(c.outcome[i])],
                        int(c.intervened[i]), C.REMEDIES[int(c.remedy[i])], int(c.fire_step[i]),
                        "" if np.isnan(c.steps_before_loss[i]) else int(c.steps_before_loss[i]),
                    ])
        for seed, rc in enumerate(rand_cells_all):
            for (a, d), c in sorted(rc.items()):
                for i in range(len(c.episode)):
                    w.writerow([
                        f"random_budget@seed{seed}", a, d, int(c.episode[i]), C.OUTCOMES[int(c.nominal_outcome[i])], C.OUTCOMES[int(c.outcome[i])],
                        int(c.intervened[i]), C.REMEDIES[int(c.remedy[i])], int(c.fire_step[i]),
                        "" if np.isnan(c.steps_before_loss[i]) else int(c.steps_before_loss[i]),
                    ])
    print("saved", args.out / "episode_cell_outcomes.csv")
    print(json.dumps({k: {"pooled_completion": v["pooled"]["completion"], "rate": v["pooled"]["intervention_rate"]} for k, v in results.items()}, indent=1))
    print("feedback nulls:", {k: v["pooled"]["completion"] for k, v in nulls.items()})
    print("saved", args.out / "report.json")


if __name__ == "__main__":
    main()
