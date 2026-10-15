"""Episode execution, synchronized logging, outcome scoring and branching.

Outcome labels (mutually exclusive, predeclared in ``config.OUTCOMES``):

* ``placed``             – released inside the target region, upright, at rest
                           after the post-release dwell.
* ``lost``               – object left the hand after acquisition before an
                           intended release.
* ``misplaced``          – released intentionally but not inside tolerance.
* ``preserved_abort``    – controller gave up after a failed regrasp; object
                           remains upright on the support.
* ``acquisition_failed`` – never secured / never lifted.
* ``timeout``            – horizon reached before the controller finished.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from . import config as C
from .controller import NominalController
from .env import GripperTransportEnv, Observation, PhysicsSnapshot, Privileged

SLIP_ONSET_M = 0.003  # relative descent in hand that defines slip onset (label only)
LOSS_CHECK_PHASES = {"lift", "transport", "lower", "rg_stop", "rg_lower", "rg_close", "rg_lift"}


@dataclass
class StepRecord:
    step: int
    time: float
    obs: np.ndarray
    ctrl: np.ndarray
    phase: str
    obj_pos: np.ndarray
    in_hand: bool
    slip_speed: float
    effective_friction: Optional[float]
    tilt_deg: float
    rel_z: float


@dataclass
class SystemSnapshot:
    """Complete executing-system state at one decision point."""

    physics: PhysicsSnapshot
    controller: NominalController
    condition: C.Condition
    step: int


@dataclass
class EpisodeResult:
    outcome: str
    condition: C.Condition
    records: List[StepRecord]
    acquisition_step: Optional[int] = None
    lift_start_step: Optional[int] = None
    transport_start_step: Optional[int] = None
    lower_start_step: Optional[int] = None
    loss_step: Optional[int] = None
    first_slip_step: Optional[int] = None
    max_slip_m: float = 0.0
    applied_remedy: Optional[str] = None
    remedy_effective_step: Optional[int] = None
    decision_step: Optional[int] = None
    requested_remedy: Optional[str] = None  # remedy requested by a live supervisor (may never take effect)
    disturbance_step: Optional[int] = None
    snapshots: Dict[int, SystemSnapshot] = field(default_factory=dict)
    final_obj_pos: Optional[np.ndarray] = None

    @property
    def completed(self) -> int:
        return int(self.outcome == "placed")

    @property
    def n_steps(self) -> int:
        return len(self.records)


def _score_final(priv: Privileged) -> str:
    pos = priv.obj_pos
    inside = abs(pos[0] - C.TARGET_X) < C.PLACE_XY_TOL and abs(pos[1]) < C.PLACE_XY_TOL
    upright = priv.tilt_deg < C.PLACE_MAX_TILT_DEG
    on_table = pos[2] < C.CUBE_HALF + 0.01
    at_rest = float(np.linalg.norm(priv.obj_linvel)) < C.PLACE_MAX_SPEED
    if inside and upright and on_table and at_rest:
        return "placed"
    return "misplaced"


class EpisodeRunner:
    """Runs episodes on one environment instance."""

    def __init__(self, env: Optional[GripperTransportEnv] = None) -> None:
        self.env = env or GripperTransportEnv()

    # ------------------------------------------------------------------ run
    def run(
        self,
        condition: C.Condition,
        remedy: Optional[str] = None,
        remedy_step: Optional[int] = None,
        snapshot_steps: Optional[set] = None,
        snapshot_phases: Tuple[str, ...] = ("lift", "transport"),
        horizon: int = C.HORIZON_STEPS,
        record: bool = True,
        supervisor: Optional[Callable[[int, "NominalController", List[Observation]], Optional[Tuple[str, int]]]] = None,
    ) -> EpisodeResult:
        """Run a full episode from reset.

        ``supervisor(step, controller, observation_history)`` may return
        ``(remedy, delay_steps)`` at a decision step; the remedy is then
        scheduled to take effect ``delay_steps`` later while nominal
        continuation proceeds (live closed-loop evaluation).

        ``remedy`` (if given) is applied when the controller's step counter
        reaches ``remedy_step``. Snapshots of the complete system are stored
        for every step in ``snapshot_steps`` (or all steps in
        ``snapshot_phases`` when ``snapshot_steps`` is None and snapshots are
        requested via an empty set sentinel).
        """
        env = self.env
        obs = env.reset(condition)
        ctl = NominalController(condition.transport_speed, condition.transport_accel)
        return self._run_loop(
            obs,
            ctl,
            condition,
            remedy,
            remedy_step,
            snapshot_steps,
            snapshot_phases,
            horizon,
            record,
            prefix=None,
            supervisor=supervisor,
        )

    def continue_from(
        self,
        snap: SystemSnapshot,
        remedy: str,
        delay_steps: int,
        horizon: int = C.HORIZON_STEPS,
        record: bool = False,
    ) -> EpisodeResult:
        """Restore a complete system snapshot, execute ``delay_steps`` of
        nominal continuation, then apply ``remedy`` and run to the end.

        Nominal continuation is the predeclared hold policy while a decision is
        pending: physics keeps advancing under the already-committed controller.
        """
        env = self.env
        obs = env.restore(snap.physics, snap.condition)
        ctl = copy.deepcopy(snap.controller)
        remedy_step = snap.step + delay_steps
        return self._run_loop(
            obs,
            ctl,
            snap.condition,
            remedy,
            remedy_step,
            None,
            (),
            horizon,
            record,
            prefix=snap,
        )

    # ------------------------------------------------------------ main loop
    def _run_loop(
        self,
        obs: Observation,
        ctl: NominalController,
        condition: C.Condition,
        remedy: Optional[str],
        remedy_step: Optional[int],
        snapshot_steps: Optional[set],
        snapshot_phases: Tuple[str, ...],
        horizon: int,
        record: bool,
        prefix: Optional[SystemSnapshot],
        supervisor=None,
    ) -> EpisodeResult:
        env = self.env
        history: List[Observation] = []
        res = EpisodeResult(outcome="timeout", condition=condition, records=[])
        acquired = False
        max_obj_z = 0.0
        rel_z_ref: Optional[float] = None
        prev_phase = ctl.phase
        remedy_applied = False
        if prefix is not None:
            # Branch bookkeeping: acquisition happened before the snapshot.
            acquired = True
            max_obj_z = float(env.privileged().obj_pos[2])
            rel_z_ref = env.privileged().rel_z

        while env.step_index < horizon:
            step = env.step_index
            phase_before = ctl.phase  # phase in which this observation is consumed
            # Phase transitions are detected on the pre-act phase so that every
            # bookkeeping step is known to a live supervisor at decision time.
            if phase_before != prev_phase:
                if phase_before == "lift":
                    res.acquisition_step = step
                    res.lift_start_step = step
                    acquired = True
                elif phase_before == "transport" and res.transport_start_step is None:
                    res.transport_start_step = step
                elif phase_before == "lower":
                    res.lower_start_step = step
                prev_phase = phase_before
            # Snapshot BEFORE the controller consumes this observation, so a
            # branch restored here sees exactly the same observation.
            want_snap = snapshot_steps is not None and (
                step in snapshot_steps or (len(snapshot_steps) == 0 and phase_before in snapshot_phases)
            )
            if want_snap:
                res.snapshots[step] = SystemSnapshot(
                    physics=env.snapshot(),
                    controller=copy.deepcopy(ctl),
                    condition=condition,
                    step=step,
                )
            history.append(obs)
            if supervisor is not None and remedy is None:
                # Called every step so the supervisor can keep its own
                # bookkeeping; it must only act when ctl.can_intervene().
                decision = supervisor(step, ctl, history)
                if decision is not None and acquired and ctl.can_intervene():
                    remedy, remedy_step = decision[0], step + int(decision[1])
                    res.decision_step = step
                    res.requested_remedy = remedy
            if remedy is not None and not remedy_applied and remedy_step is not None and step >= remedy_step:
                remedy_applied = True
                if ctl.apply_remedy(remedy) and remedy != "continue":
                    res.applied_remedy = remedy
                    res.remedy_effective_step = step
            ctrl = ctl.act(obs)
            # Hidden exogenous disturbance, scheduled relative to the first
            # transport step; identical in the parent and in every branch.
            if (
                condition.disturb_offset >= 0
                and ctl.transport_start_step >= 0
                and 0 <= step - (ctl.transport_start_step + condition.disturb_offset) < C.DISTURB_STEPS
                and condition.disturb_accel > 0.0
            ):
                env.apply_object_impulse(condition.disturb_accel)
                if res.disturbance_step is None:
                    res.disturbance_step = step
            priv = env.privileged()
            if record:
                res.records.append(
                    StepRecord(
                        step=step,
                        time=obs.time,
                        obs=obs.vec.copy(),
                        ctrl=ctrl.copy(),
                        phase=phase_before,
                        obj_pos=priv.obj_pos.copy(),
                        in_hand=priv.in_hand,
                        slip_speed=priv.slip_speed,
                        effective_friction=priv.effective_friction,
                        tilt_deg=priv.tilt_deg,
                        rel_z=priv.rel_z,
                    )
                )
            max_obj_z = max(max_obj_z, float(priv.obj_pos[2]))
            # Loss detection on the state the controller just acted on.
            if acquired and ctl.phase in LOSS_CHECK_PHASES and not priv.in_hand:
                res.loss_step = step
                never_lifted = max_obj_z <= C.CUBE_HALF + 0.02 and prefix is None
                res.outcome = "acquisition_failed" if never_lifted else "lost"
                res.final_obj_pos = priv.obj_pos.copy()
                return res
            if ctl.phase == "lift" and rel_z_ref is None:
                rel_z_ref = priv.rel_z
            if rel_z_ref is not None and ctl.phase in ("lift", "transport"):
                slip = rel_z_ref - priv.rel_z
                res.max_slip_m = max(res.max_slip_m, slip)
                if res.first_slip_step is None and slip > SLIP_ONSET_M:
                    res.first_slip_step = step
            if ctl.acquisition_failed and ctl.phase == "done":
                res.outcome = "acquisition_failed"
                res.final_obj_pos = priv.obj_pos.copy()
                return res
            if ctl.phase == "done":
                if ctl.aborted:
                    res.outcome = "preserved_abort" if (priv.tilt_deg < C.PLACE_MAX_TILT_DEG and priv.obj_pos[2] < C.CUBE_HALF + 0.01) else "lost"
                else:
                    res.outcome = _score_final(priv)
                res.final_obj_pos = priv.obj_pos.copy()
                return res
            obs = env.step(ctrl)
        res.outcome = "timeout"
        res.final_obj_pos = env.privileged().obj_pos.copy()
        return res
