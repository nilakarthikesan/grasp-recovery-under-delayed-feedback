"""Declared experimental constants.

Everything that defines the task, the timing contract, and the sampled physics
lives here so that a run can be reproduced from a single versioned module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import numpy as np

PHYSICS_DT = 0.002  # MuJoCo integration step [s]
CONTROL_DT = 0.050  # 20 Hz control / decision rate [s]
SUBSTEPS = int(round(CONTROL_DT / PHYSICS_DT))

CUBE_HALF = 0.020  # 4 cm cube
PAD_HALF_HEIGHT = 0.030  # finger pad half height [m]
TCP_Z_AT_ZERO = 0.225  # world z of the tcp site when carrier_z = 0
TABLE_Z = 0.0
TARGET_X = 0.45

# Grasp geometry: the pad centre sits 3 cm above the cube centre (grasp above
# the centre of mass), so lateral acceleration produces a pendulum torque that
# the friction patch must resist. The pad bottom (tcp - 0.030) clears the table
# by 2 cm.
GRASP_TCP_Z = 0.050
LIFT_HEIGHT = 0.10
RETREAT_HEIGHT = 0.08

GRIP_FORCE_NOMINAL = 4.0  # N per finger
GRIP_FORCE_MAX = 7.0  # N per finger (actuator ctrlrange upper bound)
OPEN_FORCE = -3.0

HORIZON_STEPS = 260  # 13 s at 20 Hz

# Placement tolerance and dwell (predeclared).
PLACE_XY_TOL = 0.03
PLACE_MAX_TILT_DEG = 15.0
PLACE_MAX_SPEED = 0.02
POST_RELEASE_DWELL_STEPS = 20  # 1.0 s


@dataclass(frozen=True)
class Condition:
    """Hidden physical condition of one episode.

    The evaluated agent never observes these values. They are evaluation
    metadata used only to define regimes and to stratify results.
    """

    mass: float  # kg
    friction: float  # sliding coefficient (object geom, dominates every contact)
    transport_speed: float  # m/s peak carrier speed during transport
    transport_accel: float  # m/s^2 carrier acceleration/deceleration
    grasp_x_offset: float = 0.0  # m, initial object offset along x (off-centre grasp)
    disturb_offset: int = -1  # control steps after transport start at which a hidden contact impulse hits (-1: none)
    disturb_accel: float = 0.0  # magnitude of that push as an acceleration of the object [m/s^2], sustained for DISTURB_STEPS
    seed: int = 0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class TimingGrid:
    """Observation ages and added response delays, in control steps."""

    observation_ages: Tuple[int, ...] = (0, 2, 5)  # 0, 100, 250 ms
    response_delays: Tuple[int, ...] = (0, 2, 5, 10)  # 0, 100, 250, 500 ms

    @property
    def max_age(self) -> int:
        return max(self.observation_ages)


@dataclass(frozen=True)
class PhysicsGrid:
    """Pilot physics grid. Values chosen so that nominal transport spans
    always-holds, marginal, and always-slips regimes (see docs/SYSTEM_DESIGN.md).
    """

    mass_range: Tuple[float, float] = (0.15, 0.50)
    friction_range: Tuple[float, float] = (0.35, 0.80)
    transport_speeds: Tuple[float, ...] = (0.8, 1.2)
    transport_accels: Tuple[float, ...] = (5.0, 8.0, 12.0)
    grasp_x_offset_range: Tuple[float, float] = (-0.008, 0.008)
    disturb_offset_range: Tuple[int, int] = (1, 10)  # steps after transport start
    disturb_accel_range: Tuple[float, float] = (0.0, 8.0)  # m/s^2, sustained for DISTURB_STEPS

    def sample(self, n: int, seed: int) -> List[Condition]:
        """Uniformly sample hidden conditions. Continuous mass/friction/offset,
        discrete speed/acceleration settings of the nominal transport plan."""
        rng = np.random.default_rng(seed)
        out: List[Condition] = []
        for i in range(n):
            out.append(
                Condition(
                    mass=round(float(rng.uniform(*self.mass_range)), 4),
                    friction=round(float(rng.uniform(*self.friction_range)), 4),
                    transport_speed=float(rng.choice(self.transport_speeds)),
                    transport_accel=float(rng.choice(self.transport_accels)),
                    grasp_x_offset=round(float(rng.uniform(*self.grasp_x_offset_range)), 5),
                    disturb_offset=int(rng.integers(self.disturb_offset_range[0], self.disturb_offset_range[1] + 1)),
                    disturb_accel=round(float(rng.uniform(*self.disturb_accel_range)), 3),
                    seed=i,
                )
            )
        return out


# Direction of the hidden contact impulse (unit vector): mostly downward shear
# with a lateral component, like brushing an unseen obstacle during transport.
DISTURB_DIRECTION = (0.6, 0.0, -0.8)
DISTURB_STEPS = 4  # duration of the hidden push in control steps (200 ms)

REMEDIES: Tuple[str, ...] = ("continue", "slow", "squeeze", "place_regrasp")
OUTCOMES: Tuple[str, ...] = (
    "placed",
    "lost",
    "misplaced",
    "preserved_abort",
    "acquisition_failed",
    "timeout",
)

FEATURE_WINDOW = 4  # number of past control steps in each selector feature window
