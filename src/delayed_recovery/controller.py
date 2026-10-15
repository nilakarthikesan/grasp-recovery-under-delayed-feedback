"""Frozen nominal controller and the bounded remedy menu.

The controller is a deterministic phase machine that consumes only deployable
observations (``env.Observation``). Its complete state is plain Python data so
that ``copy.deepcopy`` captures it for matched branching.

Remedies
--------
* ``continue``        – no change.
* ``slow``            – scale remaining transport/lowering speed and
                        acceleration by ``SLOW_FACTOR``.
* ``squeeze``         – raise finger force to the actuator bound.
* ``place_regrasp``   – decelerate, lower until wrist load indicates support
                        contact, open, re-close at the force bound, re-lift and
                        resume transport slowly. If the re-close does not
                        capture the object the controller retreats (an
                        object-preserving abort if the object is still upright).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from . import config as C
from .env import Observation

SLOW_FACTOR = 0.4
REGRASP_SPEED_FACTOR = 0.5
CONTACT_FORCE_DELTA = 1.5  # N change in wrist fz that signals support contact
LOAD_REFERENCE_STEP = 4  # descent step at which the wrist load reference is taken
CONTACT_SEARCH_BAND = 0.045  # m above the nominal grasp height where support contact is plausible
GAP_HELD_MIN = 0.030  # finger gap below this after closing => nothing captured

PHASES = (
    "approach",
    "close",
    "lift",
    "transport",
    "lower",
    "release",
    "retreat",
    "dwell",
    "done",
    "rg_stop",
    "rg_lower",
    "rg_open",
    "rg_close",
    "rg_lift",
    "rg_abort",
)
PHASE_ID = {p: i for i, p in enumerate(PHASES)}
DECISION_PHASES = ("lift", "transport")


@dataclass
class Axis:
    """Online trapezoidal setpoint generator for one carrier axis."""

    pos: float
    vel: float = 0.0

    def advance(self, target: float, v_max: float, a_max: float, dt: float = C.CONTROL_DT) -> None:
        d = target - self.pos
        if abs(d) < 1e-6 and abs(self.vel) < 1e-6:
            self.pos, self.vel = target, 0.0
            return
        direction = 1.0 if d >= 0 else -1.0
        # Discrete-time stopping speed: v^2/(2a) + v*dt/2 = |d|.
        v_stop = -0.5 * a_max * dt + math.sqrt(0.25 * a_max * a_max * dt * dt + 2.0 * a_max * abs(d))
        v_des = direction * min(v_max, v_stop, abs(d) / dt)
        dv = float(np.clip(v_des - self.vel, -a_max * dt, a_max * dt))
        self.vel += dv
        new_pos = self.pos + self.vel * dt
        if (target - new_pos) * direction <= 1e-9:
            # Reached (or would cross) the target this step: land exactly.
            self.pos, self.vel = target, 0.0
        else:
            self.pos = new_pos

    def at(self, target: float, tol: float = 1e-4) -> bool:
        return abs(self.pos - target) < tol and abs(self.vel) < 1e-3


@dataclass
class NominalController:
    transport_speed: float
    transport_accel: float
    phase: str = "approach"
    x: Axis = field(default_factory=lambda: Axis(0.0))
    z: Axis = field(default_factory=lambda: Axis(0.0))
    grip_force: float = C.GRIP_FORCE_NOMINAL
    speed_factor: float = 1.0
    phase_steps: int = 0
    settle: int = 0
    load_fz: Optional[float] = None
    acquisition_failed: bool = False
    aborted: bool = False
    applied_remedy: Optional[str] = None
    remedy_step: Optional[int] = None
    regrasp_count: int = 0
    transport_start_step: int = -1  # controller step at which transport first began
    step: int = 0

    # ------------------------------------------------------------- helpers
    @property
    def grasp_qz(self) -> float:
        return C.GRASP_TCP_Z - C.TCP_Z_AT_ZERO

    @property
    def lift_qz(self) -> float:
        return self.grasp_qz + C.LIFT_HEIGHT

    def _enter(self, phase: str) -> None:
        self.phase = phase
        self.phase_steps = 0
        self.settle = 0

    def _fingers_settled(self, obs: Observation) -> bool:
        if abs(obs["dq_finger_left"]) < 2e-3 and abs(obs["dq_finger_right"]) < 2e-3:
            self.settle += 1
        else:
            self.settle = 0
        return self.settle >= 3 or self.phase_steps >= 14

    def _support_contact(self, obs: Observation) -> bool:
        """Support contact while lowering: wrist load changes by more than
        ``CONTACT_FORCE_DELTA`` once the tcp is within the band where an object
        (possibly slipped down in the hand) can first touch the table."""
        if self.phase_steps == LOAD_REFERENCE_STEP:
            # Re-reference the carried load once the descent is at cruise speed
            # so acceleration transients cannot masquerade as contact.
            self.load_fz = obs["wrist_fz"]
        if self.load_fz is None or self.phase_steps <= LOAD_REFERENCE_STEP:
            return False
        near_table = obs.tcp_z < C.GRASP_TCP_Z + CONTACT_SEARCH_BAND
        return near_table and abs(obs["wrist_fz"] - self.load_fz) > CONTACT_FORCE_DELTA

    # ----------------------------------------------------------- remedies
    def can_intervene(self) -> bool:
        return self.phase in DECISION_PHASES and self.applied_remedy is None

    def apply_remedy(self, name: str) -> bool:
        """Apply a remedy now. Returns False if ignored (ineligible phase)."""
        if name not in C.REMEDIES:
            raise ValueError(name)
        if name == "continue":
            return True
        if not self.can_intervene():
            return False
        self.applied_remedy = name
        self.remedy_step = self.step
        if name == "slow":
            self.speed_factor = SLOW_FACTOR
        elif name == "squeeze":
            self.grip_force = C.GRIP_FORCE_MAX
        elif name == "place_regrasp":
            self._enter("rg_stop")
        return True

    # ------------------------------------------------------------- policy
    def act(self, obs: Observation) -> np.ndarray:
        """Return the 4-d command for this control step."""
        self.step += 1
        self.phase_steps += 1
        p = self.phase
        finger = self.grip_force
        v_t = self.transport_speed * self.speed_factor
        a_t = self.transport_accel * self.speed_factor

        if p == "approach":
            finger = C.OPEN_FORCE
            self.z.advance(self.grasp_qz, 0.30, 2.0)
            if self.z.at(self.grasp_qz) and abs(obs["q_carrier_z"] - self.grasp_qz) < 2e-3:
                self.settle += 1
                if self.settle >= 4:
                    self._enter("close")
        elif p == "close":
            if self._fingers_settled(obs):
                if obs.finger_gap < GAP_HELD_MIN:
                    self.acquisition_failed = True
                    self._enter("retreat")
                else:
                    self._enter("lift")
        elif p == "lift":
            self.z.advance(self.lift_qz, 0.20, 1.0)
            if self.z.at(self.lift_qz):
                self.load_fz = obs["wrist_fz"]
                if self.transport_start_step < 0:
                    self.transport_start_step = self.step
                self._enter("transport")
        elif p == "transport":
            self.x.advance(C.TARGET_X, v_t, a_t)
            if self.x.at(C.TARGET_X):
                if self.load_fz is None:
                    self.load_fz = obs["wrist_fz"]
                self._enter("lower")
        elif p == "lower":
            self.z.advance(self.grasp_qz + 0.002, 0.12 * max(self.speed_factor, 0.5), 1.0)
            if self.z.at(self.grasp_qz + 0.002) or self._support_contact(obs):
                self._enter("release")
        elif p == "release":
            finger = C.OPEN_FORCE
            if self.phase_steps >= 6:
                self._enter("retreat")
        elif p == "retreat":
            finger = C.OPEN_FORCE
            self.z.advance(self.grasp_qz + C.RETREAT_HEIGHT, 0.25, 2.0)
            if self.z.at(self.grasp_qz + C.RETREAT_HEIGHT):
                self._enter("dwell")
        elif p == "dwell":
            finger = C.OPEN_FORCE
            if self.phase_steps >= C.POST_RELEASE_DWELL_STEPS:
                self._enter("done")
        elif p == "done":
            finger = C.OPEN_FORCE
        # ---- place / regrasp remedy ----
        elif p == "rg_stop":
            # Decelerate the x axis to rest where it is.
            self.x.advance(self.x.pos + 0.5 * self.x.vel * abs(self.x.vel) / max(a_t, 1e-6), v_t, a_t)
            if abs(self.x.vel) < 1e-3:
                self.x.vel = 0.0
                self.load_fz = obs["wrist_fz"] if self.load_fz is None else self.load_fz
                self._enter("rg_lower")
        elif p == "rg_lower":
            self.z.advance(self.grasp_qz + 0.002, 0.12, 1.0)
            if self.z.at(self.grasp_qz + 0.002) or self._support_contact(obs):
                self._enter("rg_open")
        elif p == "rg_open":
            finger = C.OPEN_FORCE
            if self.phase_steps >= 6:
                self.grip_force = C.GRIP_FORCE_MAX
                self._enter("rg_close")
        elif p == "rg_close":
            finger = C.GRIP_FORCE_MAX
            if self._fingers_settled(obs):
                if obs.finger_gap < GAP_HELD_MIN:
                    self.aborted = True
                    self._enter("rg_abort")
                else:
                    self.regrasp_count += 1
                    self._enter("rg_lift")
        elif p == "rg_lift":
            self.z.advance(self.lift_qz, 0.20, 1.0)
            if self.z.at(self.lift_qz):
                self.load_fz = obs["wrist_fz"]
                self.speed_factor = REGRASP_SPEED_FACTOR
                self._enter("transport")
        elif p == "rg_abort":
            finger = C.OPEN_FORCE
            self.z.advance(self.grasp_qz + C.RETREAT_HEIGHT, 0.25, 2.0)
            if self.z.at(self.grasp_qz + C.RETREAT_HEIGHT):
                self._enter("done")
        else:  # pragma: no cover
            raise RuntimeError(p)

        return np.array([self.x.pos, self.z.pos, finger, finger], dtype=np.float64)

    @property
    def phase_id(self) -> int:
        return PHASE_ID[self.phase]
