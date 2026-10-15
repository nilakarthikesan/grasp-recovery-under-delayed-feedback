"""Standalone MuJoCo grasp-lift-transport-place environment.

The environment exposes two strictly separated views of the world:

* ``Observation`` – deployable signals: proprioception, finger actuator force,
  wrist force/torque, the last command, and the simulator clock.
* ``Privileged`` – object pose/velocity, contact state, effective friction and
  hidden parameters. Used only for outcome scoring, labels and oracles.

Complete physics state can be captured and restored through MuJoCo's
``mjSTATE_INTEGRATION`` specification, which includes the warm-start
accelerations needed for bit-exact continuation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import mujoco
import numpy as np

from . import config as C

ASSET = Path(__file__).parent / "assets" / "gripper_transport.xml"

OBS_NAMES = (
    "q_carrier_x",
    "q_carrier_z",
    "dq_carrier_x",
    "dq_carrier_z",
    "q_finger_left",
    "q_finger_right",
    "dq_finger_left",
    "dq_finger_right",
    "f_finger_left",
    "f_finger_right",
    "wrist_fx",
    "wrist_fy",
    "wrist_fz",
    "wrist_tx",
    "wrist_ty",
    "wrist_tz",
    "ctrl_x",
    "ctrl_z",
    "ctrl_finger_left",
    "ctrl_finger_right",
)
OBS_DIM = len(OBS_NAMES)


@dataclass
class Observation:
    """Deployable observation at one control step."""

    step: int
    time: float  # simulator clock at capture
    vec: np.ndarray  # OBS_DIM floats, ordered as OBS_NAMES

    def __getitem__(self, name: str) -> float:
        return float(self.vec[OBS_NAMES.index(name)])

    @property
    def finger_gap(self) -> float:
        """Inner-face separation, derived from joint positions only."""
        return 0.080 - self["q_finger_left"] - self["q_finger_right"]

    @property
    def tcp_z(self) -> float:
        return C.TCP_Z_AT_ZERO + self["q_carrier_z"]

    @property
    def tcp_x(self) -> float:
        return self["q_carrier_x"]


@dataclass
class Privileged:
    """Evaluation-only state. Never a model feature."""

    obj_pos: np.ndarray
    obj_quat: np.ndarray
    obj_linvel: np.ndarray
    tilt_deg: float
    in_hand: bool
    pad_contacts: int
    effective_friction: Optional[float]
    slip_speed: float  # |object velocity relative to tcp| along z [m/s]
    rel_z: float  # object centre height relative to the tcp [m]


@dataclass
class PhysicsSnapshot:
    state: np.ndarray  # mjSTATE_INTEGRATION (includes warm-start accelerations)
    step: int
    observation: Observation  # latched sensor values at this control boundary


class GripperTransportEnv:
    def __init__(self) -> None:
        self.model = mujoco.MjModel.from_xml_path(str(ASSET))
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.obj_body = m.body("object").id
        self.obj_geom = m.geom("object_geom").id
        self.pad_geoms = (m.geom("pad_left").id, m.geom("pad_right").id)
        self.table_geom = m.geom("table").id
        self.obj_qpos_adr = m.jnt_qposadr[m.joint("object_free").id]
        self.obj_qvel_adr = m.jnt_dofadr[m.joint("object_free").id]
        self.tcp_site = m.site("tcp").id
        self._sensor_adr = {
            name: (m.sensor(name).adr[0], m.sensor(name).dim[0])
            for name in (
                "q_carrier_x",
                "q_carrier_z",
                "dq_carrier_x",
                "dq_carrier_z",
                "q_finger_left",
                "q_finger_right",
                "dq_finger_left",
                "dq_finger_right",
                "f_finger_left",
                "f_finger_right",
                "wrist_force",
                "wrist_torque",
            )
        }
        self._state_spec = mujoco.mjtState.mjSTATE_INTEGRATION
        self._state_size = mujoco.mj_stateSize(m, self._state_spec)
        self.step_index = 0
        self.condition: Optional[C.Condition] = None
        self._impulse_pending = False

    # ------------------------------------------------------------------ reset
    def reset(self, condition: C.Condition) -> Observation:
        m, d = self.model, self.data
        mujoco.mj_resetData(m, d)
        self.condition = condition
        # Hidden mass with consistent cube inertia (I = m s^2 / 6 per axis).
        m.body_mass[self.obj_body] = condition.mass
        side = 2.0 * C.CUBE_HALF
        m.body_inertia[self.obj_body] = condition.mass * side * side / 6.0
        m.geom_friction[self.obj_geom] = (condition.friction, 0.005, 0.0001)
        mujoco.mj_setConst(m, d)
        # Object pose: on the table, optional x offset relative to the gripper.
        d.qpos[self.obj_qpos_adr : self.obj_qpos_adr + 3] = (
            condition.grasp_x_offset,
            0.0,
            C.CUBE_HALF,
        )
        d.qpos[self.obj_qpos_adr + 3 : self.obj_qpos_adr + 7] = (1.0, 0.0, 0.0, 0.0)
        # Carrier starts at home; fingers open.
        d.ctrl[:] = (0.0, 0.0, C.OPEN_FORCE, C.OPEN_FORCE)
        d.qpos[m.joint("finger_left").qposadr[0]] = 0.0
        d.qpos[m.joint("finger_right").qposadr[0]] = 0.0
        mujoco.mj_forward(m, d)
        self.step_index = 0
        return self.observe()

    # ------------------------------------------------------------------- step
    def apply_object_impulse(self, accel: float) -> None:
        """Hidden exogenous disturbance: an external force on the object for the
        next control step, equal to ``accel`` times the object's mass along
        ``config.DISTURB_DIRECTION``. Cleared automatically after the step."""
        f = np.asarray(C.DISTURB_DIRECTION) * accel * self.model.body_mass[self.obj_body]
        self.data.xfrc_applied[self.obj_body, :3] = f
        self._impulse_pending = True

    def step(self, ctrl: np.ndarray) -> Observation:
        """Apply one 20 Hz command and advance physics by one control step.

        Carrier position setpoints are linearly interpolated across the
        physics substeps from the previously held command (a first-order hold,
        as a 500 Hz arm-level interpolator would do); finger force commands
        take effect immediately. The previous command is part of ``d.ctrl``
        and therefore of the saved integration state.
        """
        d = self.data
        prev = d.ctrl.copy()
        target = np.asarray(ctrl, dtype=np.float64)
        n = C.SUBSTEPS
        for k in range(1, n + 1):
            alpha = k / n
            d.ctrl[0] = prev[0] + (target[0] - prev[0]) * alpha
            d.ctrl[1] = prev[1] + (target[1] - prev[1]) * alpha
            d.ctrl[2] = target[2]
            d.ctrl[3] = target[3]
            mujoco.mj_step(self.model, d)
        if self._impulse_pending:
            d.xfrc_applied[self.obj_body, :] = 0.0
            self._impulse_pending = False
        self.step_index += 1
        return self.observe()

    # ------------------------------------------------------------ observation
    def _sensor(self, name: str) -> np.ndarray:
        adr, dim = self._sensor_adr[name]
        return self.data.sensordata[adr : adr + dim]

    def observe(self) -> Observation:
        s = self._sensor
        vec = np.concatenate(
            [
                s("q_carrier_x"),
                s("q_carrier_z"),
                s("dq_carrier_x"),
                s("dq_carrier_z"),
                s("q_finger_left"),
                s("q_finger_right"),
                s("dq_finger_left"),
                s("dq_finger_right"),
                s("f_finger_left"),
                s("f_finger_right"),
                s("wrist_force"),
                s("wrist_torque"),
                self.data.ctrl,
            ]
        ).astype(np.float64)
        return Observation(step=self.step_index, time=float(self.data.time), vec=vec)

    def refresh_derived(self) -> None:
        """Recompute position/velocity-dependent quantities (kinematics,
        contacts, body velocities) from the current generalized state without
        running the constraint solver, so the warm-start used by the next
        ``mj_step`` is untouched and parent/branch physics stay bit-exact."""
        mujoco.mj_fwdPosition(self.model, self.data)
        mujoco.mj_fwdVelocity(self.model, self.data)

    def privileged(self) -> Privileged:
        self.refresh_derived()
        d = self.data
        pos = d.xpos[self.obj_body].copy()
        quat = d.xquat[self.obj_body].copy()
        linvel = d.qvel[self.obj_qvel_adr : self.obj_qvel_adr + 3].copy()
        # Tilt: angle between object z axis and world z.
        rot = np.empty(9)
        mujoco.mju_quat2Mat(rot, quat)
        cos_tilt = float(np.clip(rot.reshape(3, 3)[2, 2], -1.0, 1.0))
        tilt_deg = float(np.degrees(np.arccos(cos_tilt)))
        tcp = d.site_xpos[self.tcp_site]
        in_hand = (
            abs(pos[2] - tcp[2]) < C.PAD_HALF_HEIGHT + C.CUBE_HALF
            and abs(pos[0] - tcp[0]) < 0.03
            and abs(pos[1] - tcp[1]) < 0.03
        )
        pad_contacts = 0
        mu: Optional[float] = None
        for i in range(d.ncon):
            con = d.contact[i]
            pair = (con.geom1, con.geom2)
            if self.obj_geom in pair and (pair[0] in self.pad_geoms or pair[1] in self.pad_geoms):
                pad_contacts += 1
                mu = float(con.friction[0])
        # Relative vertical speed between object and tcp.
        tcp_vel = np.zeros(6)
        mujoco.mj_objectVelocity(self.model, d, mujoco.mjtObj.mjOBJ_SITE, self.tcp_site, tcp_vel, 0)
        slip_speed = float(abs(linvel[2] - tcp_vel[5])) if in_hand else 0.0
        return Privileged(
            obj_pos=pos,
            obj_quat=quat,
            obj_linvel=linvel,
            tilt_deg=tilt_deg,
            in_hand=bool(in_hand),
            pad_contacts=pad_contacts,
            effective_friction=mu,
            slip_speed=slip_speed,
            rel_z=float(pos[2] - tcp[2]),
        )

    # ------------------------------------------------------- snapshot/restore
    def snapshot(self) -> PhysicsSnapshot:
        state = np.empty(self._state_size)
        mujoco.mj_getState(self.model, self.data, state, self._state_spec)
        obs = self.observe()
        return PhysicsSnapshot(state=state, step=self.step_index, observation=Observation(obs.step, obs.time, obs.vec.copy()))

    def restore(self, snap: PhysicsSnapshot, condition: C.Condition) -> Observation:
        """Restore physics state. ``condition`` re-applies hidden model
        parameters, which are not part of MjData."""
        m = self.model
        if self.condition != condition:
            m.body_mass[self.obj_body] = condition.mass
            side = 2.0 * C.CUBE_HALF
            m.body_inertia[self.obj_body] = condition.mass * side * side / 6.0
            m.geom_friction[self.obj_geom] = (condition.friction, 0.005, 0.0001)
            mujoco.mj_setConst(m, self.data)
            self.condition = condition
        mujoco.mj_setState(m, self.data, snap.state, self._state_spec)
        # Do NOT call mj_forward here: it would overwrite qacc_warmstart and
        # break bit-exact continuation. Derived quantities are refreshed lazily
        # by refresh_derived(); the latched observation is returned as-is.
        self.data.sensordata[:] = 0.0
        self._impulse_pending = bool(np.any(self.data.xfrc_applied[self.obj_body]))
        self.step_index = snap.step
        return Observation(snap.observation.step, snap.observation.time, snap.observation.vec.copy())

    # ---------------------------------------------------------------- render
    def render(self, width: int = 640, height: int = 480) -> np.ndarray:
        renderer = mujoco.Renderer(self.model, height=height, width=width)
        renderer.update_scene(self.data, camera="side")
        img = renderer.render().copy()
        renderer.close()
        return img


def hidden_margin(cond: C.Condition, grip_force: float = C.GRIP_FORCE_NOMINAL) -> float:
    """Quasi-static friction margin of the nominal grasp during transport.

    capacity / load, where capacity = 2 * mu * F and load combines weight and
    peak inertial shear. >1 means the grasp should hold quasi-statically.
    This is an analysis quantity only (uses hidden values).
    """
    capacity = 2.0 * cond.friction * grip_force
    load = cond.mass * float(np.hypot(9.81, cond.transport_accel))
    return capacity / load
