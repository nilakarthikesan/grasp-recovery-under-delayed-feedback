"""Matched-branch data collection.

For every parent episode that acquires the object, every control step in the
decision phases (lift, transport) is a candidate decision state. From each
state the complete system is restored and each remedy is executed after each
response delay, giving the branch table

    outcome[episode, step, remedy, delay]

together with the parent's synchronized logs. Nominal continuation is the
parent's own future, so ``continue`` needs no extra simulation.

Timing bookkeeping per branch (control steps of 50 ms):
    decision step      t      (observation captured at t - age; see dataset.py)
    requested action   t      (remedy requested immediately after the decision)
    effective action   t + d  (remedy begins after the added response delay d)
Nominal continuation is executed between t and t + d (queue-preserving hold).
"""

from __future__ import annotations

import json
import multiprocessing as mp
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .controller import PHASE_ID
from .episode import EpisodeResult, EpisodeRunner

OUTCOME_ID = {o: i for i, o in enumerate(C.OUTCOMES)}
REMEDY_ID = {r: i for i, r in enumerate(C.REMEDIES)}


@dataclass
class EpisodeLog:
    index: int
    condition: Dict[str, float]
    outcome: str
    obs: np.ndarray  # T x OBS_DIM
    ctrl: np.ndarray  # T x 4
    phase: np.ndarray  # T (phase ids)
    obj_pos: np.ndarray  # T x 3 (privileged)
    rel_z: np.ndarray  # T (privileged)
    tilt_deg: np.ndarray  # T (privileged)
    in_hand: np.ndarray  # T (privileged)
    acquisition_step: int
    transport_start_step: int
    lower_start_step: int
    loss_step: int
    first_slip_step: int
    decision_steps: np.ndarray  # D
    branch_outcome: np.ndarray  # D x R x K (outcome ids; remedy 0 = continue)
    branch_end_step: np.ndarray  # D x R x K


def _log_from_result(index: int, res: EpisodeResult) -> Dict:
    T = len(res.records)
    return dict(
        index=index,
        condition=res.condition.to_dict(),
        outcome=res.outcome,
        obs=np.stack([r.obs for r in res.records]).astype(np.float32),
        ctrl=np.stack([r.ctrl for r in res.records]).astype(np.float32),
        phase=np.array([PHASE_ID[r.phase] for r in res.records], dtype=np.int8),
        obj_pos=np.stack([r.obj_pos for r in res.records]).astype(np.float32),
        rel_z=np.array([r.rel_z for r in res.records], dtype=np.float32),
        tilt_deg=np.array([r.tilt_deg for r in res.records], dtype=np.float32),
        in_hand=np.array([r.in_hand for r in res.records], dtype=bool),
        acquisition_step=-1 if res.acquisition_step is None else res.acquisition_step,
        transport_start_step=-1 if res.transport_start_step is None else res.transport_start_step,
        lower_start_step=-1 if res.lower_start_step is None else res.lower_start_step,
        loss_step=-1 if res.loss_step is None else res.loss_step,
        first_slip_step=-1 if res.first_slip_step is None else res.first_slip_step,
    )


def collect_episode(
    index: int,
    condition: C.Condition,
    delays: Sequence[int],
    remedies: Sequence[str] = C.REMEDIES,
    runner: Optional[EpisodeRunner] = None,
) -> Dict:
    """Run one parent episode and its full branch table."""
    runner = runner or EpisodeRunner()
    parent = runner.run(condition, snapshot_steps=set(), snapshot_phases=("lift", "transport"))
    log = _log_from_result(index, parent)
    if parent.outcome == "acquisition_failed" or parent.acquisition_step is None:
        log.update(
            decision_steps=np.zeros(0, dtype=np.int32),
            branch_outcome=np.zeros((0, len(remedies), len(delays)), dtype=np.int8),
            branch_end_step=np.zeros((0, len(remedies), len(delays)), dtype=np.int16),
        )
        return log
    steps = sorted(s for s in parent.snapshots if s >= parent.acquisition_step)
    R, K = len(remedies), len(delays)
    out = np.zeros((len(steps), R, K), dtype=np.int8)
    end = np.zeros((len(steps), R, K), dtype=np.int16)
    parent_end = parent.records[-1].step
    for i, s in enumerate(steps):
        snap = parent.snapshots[s]
        for r, remedy in enumerate(remedies):
            if remedy == "continue":
                out[i, r, :] = OUTCOME_ID[parent.outcome]
                end[i, r, :] = parent_end
                continue
            for k, d in enumerate(delays):
                b = runner.continue_from(snap, remedy, d)
                out[i, r, k] = OUTCOME_ID[b.outcome]
                end[i, r, k] = b.records[-1].step if b.records else -1
    log.update(decision_steps=np.array(steps, dtype=np.int32), branch_outcome=out, branch_end_step=end)
    return log


def _worker(args: Tuple[int, Dict, Tuple[int, ...]]) -> Dict:
    index, cond_dict, delays = args
    cond = C.Condition(**cond_dict)
    return collect_episode(index, cond, delays)


def collect_dataset(
    conditions: Sequence[C.Condition],
    delays: Sequence[int],
    out_dir: Path,
    workers: int = 1,
    verbose: bool = True,
) -> Path:
    """Collect parent episodes and branch tables; save one npz per episode plus
    an index JSON. Returns the output directory."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(i, c.to_dict(), tuple(delays)) for i, c in enumerate(conditions)]
    t0 = time.time()
    logs: List[Dict] = []
    if workers > 1:
        ctx = mp.get_context("spawn")
        with ctx.Pool(workers) as pool:
            for n, log in enumerate(pool.imap_unordered(_worker, jobs, chunksize=2)):
                logs.append(log)
                if verbose and (n + 1) % 25 == 0:
                    print(f"  {n + 1}/{len(jobs)} episodes, {time.time() - t0:.0f}s", flush=True)
    else:
        runner = EpisodeRunner()
        for n, (i, cd, dl) in enumerate(jobs):
            logs.append(collect_episode(i, C.Condition(**cd), dl, runner=runner))
            if verbose and (n + 1) % 25 == 0:
                print(f"  {n + 1}/{len(jobs)} episodes, {time.time() - t0:.0f}s", flush=True)
    logs.sort(key=lambda d: d["index"])
    index = []
    for log in logs:
        path = out_dir / f"episode_{log['index']:05d}.npz"
        arrays = {k: v for k, v in log.items() if isinstance(v, np.ndarray)}
        np.savez_compressed(path, **arrays)
        meta = {k: v for k, v in log.items() if not isinstance(v, np.ndarray)}
        meta["file"] = path.name
        index.append(meta)
    with open(out_dir / "index.json", "w") as f:
        json.dump(
            {
                "delays": list(delays),
                "remedies": list(C.REMEDIES),
                "outcomes": list(C.OUTCOMES),
                "control_dt": C.CONTROL_DT,
                "n_episodes": len(index),
                "elapsed_s": time.time() - t0,
                "episodes": index,
            },
            f,
            indent=1,
        )
    return out_dir


def load_dataset(out_dir: Path) -> Tuple[Dict, List[Dict]]:
    out_dir = Path(out_dir)
    with open(out_dir / "index.json") as f:
        index = json.load(f)
    logs = []
    for meta in index["episodes"]:
        with np.load(out_dir / meta["file"]) as z:
            log = {k: z[k] for k in z.files}
        log.update(meta)
        logs.append(log)
    return index, logs
