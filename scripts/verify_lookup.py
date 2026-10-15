"""Verify that branch-table lookup equals live closed-loop simulation.

Fits the delay-aware value selector on the training split, then re-simulates
sampled test episodes end to end with the selector in the loop (stale
observations, scheduled remedy after the response delay) and compares the
outcome, decision step and remedy with the table lookup.

Example:
    python scripts/verify_lookup.py --data runs/pilot_v1/branches --n 40
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from delayed_recovery import config as C
from delayed_recovery.collect import OUTCOME_ID, load_dataset
from delayed_recovery.controller import PHASE_ID
from delayed_recovery.dataset import DecisionTable, build_decision_table, observation_features, split_episodes, subset
from delayed_recovery.episode import EpisodeRunner
from delayed_recovery.evaluate import choose_threshold, run_cell
from delayed_recovery.selectors import ValueSelector


def live_supervisor(selector: ValueSelector, age: int, delay_idx: int, delays, condition: C.Condition):
    """Build a supervisor closure that recomputes features from the live
    observation history (never from the parent log)."""
    state = {"phases": [], "acq": -1, "ts": -1}

    def sup(step, ctl, history):
        state["phases"].append(PHASE_ID[ctl.phase])
        if state["acq"] < 0 and ctl.phase == "lift":
            state["acq"] = step
        if state["ts"] < 0 and ctl.phase == "transport":
            state["ts"] = step
        if not ctl.can_intervene() or state["acq"] < 0:
            return None
        obs_step = max(step - age, 0)
        live_log = {
            "obs": np.stack([o.vec for o in history]).astype(np.float32),
            "acquisition_step": state["acq"],
            "transport_start_step": state["ts"],
            "phase": np.array(state["phases"], dtype=np.int8),
            "condition": condition.to_dict(),
        }
        x = observation_features(live_log, obs_step)[None]
        row = DecisionTable(
            episode=np.zeros(1, dtype=np.int32),
            decision=np.zeros(1, dtype=np.int32),
            step=np.array([step]),
            age=np.array([age]),
            obs_step=np.array([obs_step]),
            x_obs=x,
            slip_now=np.zeros(1, dtype=np.int8),
            nominal_lost=np.zeros(1, dtype=np.int8),
            steps_to_loss=np.zeros(1, dtype=np.int32),
            branch_outcome=np.zeros((1, len(C.REMEDIES), len(delays)), dtype=np.int8),
            delays=tuple(delays),
            ages=(age,),
        )
        dec = selector.decide(row, delay_idx)
        if dec.score[0] >= selector.threshold:
            return C.REMEDIES[int(dec.remedy[0])], delays[delay_idx]
        return None

    return sup


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("runs/pilot_v1/branches"))
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", type=Path, default=Path("results/pilot_v1/lookup_verification.json"))
    args = ap.parse_args()
    index, logs = load_dataset(args.data)
    ages = C.TimingGrid().observation_ages
    delays = tuple(index["delays"])
    table = build_decision_table(logs, ages, delays)
    splits = split_episodes(logs, 0)
    train = subset(table, np.isin(table.episode, splits["train"]))
    val = subset(table, np.isin(table.episode, splits["val"]))
    test = subset(table, np.isin(table.episode, splits["test"]))
    sel = ValueSelector(aware=True).fit(train)
    sel.threshold, _ = choose_threshold(sel, val, 0.40)
    rng = np.random.default_rng(0)
    runner = EpisodeRunner()
    checks = []
    mismatches = 0
    for _ in range(args.n):
        e = int(rng.choice(splits["test"]))
        age = int(rng.choice(ages))
        k = int(rng.integers(len(delays)))
        cond = C.Condition(**logs[e]["condition"])
        # Lookup prediction for this single episode.
        cell = run_cell(sel, test, age, k)
        i = int(np.flatnonzero(cell.episode == e)[0])
        pred = {"outcome": C.OUTCOMES[int(cell.outcome[i])], "remedy": C.REMEDIES[int(cell.remedy[i])], "fire_step": int(cell.fire_step[i])}
        res = runner.run(cond, supervisor=live_supervisor(sel, age, k, delays, cond))
        live = {"outcome": res.outcome, "remedy": res.requested_remedy or "continue", "fire_step": -1 if res.decision_step is None else int(res.decision_step)}
        ok = pred == live
        mismatches += int(not ok)
        checks.append({"episode": e, "age": age, "delay": delays[k], "lookup": pred, "live": live, "match": ok})
        print(f"ep {e:3d} age {age} delay {delays[k]:2d}  lookup={pred}  live={live}  {'OK' if ok else 'MISMATCH'}")
    summary = {"n": args.n, "mismatches": mismatches, "checks": checks}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=1)
    print(f"{args.n - mismatches}/{args.n} episodes match; saved {args.out}")


if __name__ == "__main__":
    main()
