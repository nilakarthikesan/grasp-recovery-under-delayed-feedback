"""Decision-state features and labels built from parent logs and branch tables.

A decision at parent step ``t`` with observation age ``a`` sees the deployable
observation window ending at step ``t - a``. Features never include object
pose, contact state, hidden parameters, or anything after ``t - a``.

Rows are indexed by (episode, decision index, age index); remedy/delay labels
come from the branch table of the same decision state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

from . import config as C
from .env import OBS_DIM, OBS_NAMES

OUT_PLACED = C.OUTCOMES.index("placed")
OUT_LOST = C.OUTCOMES.index("lost")
R_CONT = C.REMEDIES.index("continue")

WINDOW_FEATURE_NAMES: List[str] = [f"{n}[-{k}]" for k in range(C.FEATURE_WINDOW - 1, -1, -1) for n in OBS_NAMES]
CONTEXT_FEATURE_NAMES: List[str] = [
    "finger_gap",
    "steps_since_acquisition",
    "phase_id",
    "plan_speed",
    "plan_accel",
    "wrist_fz_minus_lift_ref",
    "finger_gap_minus_lift_ref",
]
TIMING_FEATURE_NAMES: List[str] = ["observation_age", "response_delay", "evidence_age"]
N_OBS_FEATURES = len(WINDOW_FEATURE_NAMES) + len(CONTEXT_FEATURE_NAMES)


@dataclass
class DecisionTable:
    """Flat arrays over decision rows (one row per episode x decision x age)."""

    episode: np.ndarray  # row -> episode index (position in logs list)
    decision: np.ndarray  # row -> decision index within the episode
    step: np.ndarray  # parent step t
    age: np.ndarray  # observation age in steps
    obs_step: np.ndarray  # t - age (clipped at 0)
    x_obs: np.ndarray  # row x N_OBS_FEATURES (deployable, stale)
    slip_now: np.ndarray  # privileged label at obs_step: relative descent > onset
    nominal_lost: np.ndarray  # episode-level label: lost under continuation
    steps_to_loss: np.ndarray  # nominal loss step - t (large if never lost)
    branch_outcome: np.ndarray  # row x R x K outcome ids (independent of age)
    delays: Tuple[int, ...]
    ages: Tuple[int, ...]

    def timing_features(self, delay_idx: int) -> np.ndarray:
        d = np.full(len(self.age), self.delays[delay_idx], dtype=np.float32)
        return np.stack([self.age.astype(np.float32), d, self.age + d], axis=1)

    def features(self, delay_idx: int, aware: bool) -> np.ndarray:
        if aware:
            return np.concatenate([self.x_obs, self.timing_features(delay_idx)], axis=1)
        return self.x_obs

    def placed(self, remedy_idx: int, delay_idx: int) -> np.ndarray:
        return (self.branch_outcome[:, remedy_idx, delay_idx] == OUT_PLACED).astype(np.int8)


def _window(obs: np.ndarray, end_step: int, k: int = C.FEATURE_WINDOW) -> np.ndarray:
    idx = np.clip(np.arange(end_step - k + 1, end_step + 1), 0, len(obs) - 1)
    return obs[idx].reshape(-1)


def observation_features(log: Dict, obs_step: int) -> np.ndarray:
    """Deployable feature vector from one parent log at ``obs_step``."""
    obs = log["obs"]
    acq = int(log["acquisition_step"])
    o = obs[obs_step]
    gap = 0.080 - o[OBS_NAMES.index("q_finger_left")] - o[OBS_NAMES.index("q_finger_right")]
    # Lift reference: first transport step if already reached, else current.
    ts = int(log["transport_start_step"])
    ref_step = ts if 0 <= ts <= obs_step else obs_step
    ref = obs[ref_step]
    ref_gap = 0.080 - ref[OBS_NAMES.index("q_finger_left")] - ref[OBS_NAMES.index("q_finger_right")]
    cond = log["condition"]
    ctx = np.array(
        [
            gap,
            obs_step - acq,
            float(log["phase"][obs_step]),
            cond["transport_speed"],
            cond["transport_accel"],
            o[OBS_NAMES.index("wrist_fz")] - ref[OBS_NAMES.index("wrist_fz")],
            gap - ref_gap,
        ],
        dtype=np.float32,
    )
    return np.concatenate([_window(obs, obs_step).astype(np.float32), ctx])


def build_decision_table(logs: Sequence[Dict], ages: Sequence[int], delays: Sequence[int]) -> DecisionTable:
    rows: Dict[str, list] = {k: [] for k in ("episode", "decision", "step", "age", "obs_step", "x_obs", "slip_now", "nominal_lost", "steps_to_loss", "branch_outcome")}
    for e, log in enumerate(logs):
        steps = log["decision_steps"]
        if len(steps) == 0:
            continue
        acq = int(log["acquisition_step"])
        rel_ref = float(log["rel_z"][acq])
        lost = log["outcome"] == "lost"
        loss_step = int(log["loss_step"]) if lost else 10_000
        for i, t in enumerate(steps):
            for a in ages:
                s = max(int(t) - a, 0)
                rows["episode"].append(e)
                rows["decision"].append(i)
                rows["step"].append(int(t))
                rows["age"].append(a)
                rows["obs_step"].append(s)
                rows["x_obs"].append(observation_features(log, s))
                rows["slip_now"].append(int(s >= acq and (rel_ref - float(log["rel_z"][s])) > 0.003))
                rows["nominal_lost"].append(int(lost))
                rows["steps_to_loss"].append(loss_step - int(t))
                rows["branch_outcome"].append(log["branch_outcome"][i])
    return DecisionTable(
        episode=np.array(rows["episode"], dtype=np.int32),
        decision=np.array(rows["decision"], dtype=np.int32),
        step=np.array(rows["step"], dtype=np.int32),
        age=np.array(rows["age"], dtype=np.int32),
        obs_step=np.array(rows["obs_step"], dtype=np.int32),
        x_obs=np.stack(rows["x_obs"]).astype(np.float32),
        slip_now=np.array(rows["slip_now"], dtype=np.int8),
        nominal_lost=np.array(rows["nominal_lost"], dtype=np.int8),
        steps_to_loss=np.array(rows["steps_to_loss"], dtype=np.int32),
        branch_outcome=np.stack(rows["branch_outcome"]).astype(np.int8),
        delays=tuple(int(d) for d in delays),
        ages=tuple(int(a) for a in ages),
    )


def subset(table: DecisionTable, mask: np.ndarray) -> DecisionTable:
    return DecisionTable(
        episode=table.episode[mask],
        decision=table.decision[mask],
        step=table.step[mask],
        age=table.age[mask],
        obs_step=table.obs_step[mask],
        x_obs=table.x_obs[mask],
        slip_now=table.slip_now[mask],
        nominal_lost=table.nominal_lost[mask],
        steps_to_loss=table.steps_to_loss[mask],
        branch_outcome=table.branch_outcome[mask],
        delays=table.delays,
        ages=table.ages,
    )


def split_episodes(logs: Sequence[Dict], seed: int, fractions=(0.5, 0.2, 0.3)) -> Dict[str, np.ndarray]:
    """Split acquired parent episodes (all branches of an episode stay together)."""
    acquired = np.array([e for e, log in enumerate(logs) if len(log["decision_steps"]) > 0])
    rng = np.random.default_rng(seed)
    perm = rng.permutation(acquired)
    n = len(perm)
    n_train = int(round(fractions[0] * n))
    n_val = int(round(fractions[1] * n))
    return {
        "train": np.sort(perm[:n_train]),
        "val": np.sort(perm[n_train : n_train + n_val]),
        "test": np.sort(perm[n_train + n_val :]),
    }
