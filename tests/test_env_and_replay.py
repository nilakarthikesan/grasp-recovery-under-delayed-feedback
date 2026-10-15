import copy

import numpy as np
import pytest

from delayed_recovery import config as C
from delayed_recovery.controller import NominalController
from delayed_recovery.env import OBS_DIM, GripperTransportEnv, hidden_margin
from delayed_recovery.episode import EpisodeRunner

EASY = C.Condition(mass=0.20, friction=0.75, transport_speed=0.8, transport_accel=5.0)
MARGINAL = C.Condition(mass=0.35, friction=0.4948, transport_speed=1.2, transport_accel=8.0, grasp_x_offset=-0.00259)
HEAVY = C.Condition(mass=0.50, friction=0.35, transport_speed=0.8, transport_accel=5.0)


def test_hidden_parameters_are_applied_and_effective_friction_matches():
    env = GripperTransportEnv()
    env.reset(EASY)
    assert env.model.body_mass[env.obj_body] == pytest.approx(EASY.mass)
    side = 2 * C.CUBE_HALF
    assert np.allclose(env.model.body_inertia[env.obj_body], EASY.mass * side * side / 6)
    runner = EpisodeRunner(env)
    res = runner.run(EASY)
    mus = {r.effective_friction for r in res.records if r.effective_friction is not None}
    assert len(mus) == 1 and next(iter(mus)) == pytest.approx(EASY.friction)


def test_observation_excludes_object_state():
    env = GripperTransportEnv()
    obs = env.reset(EASY)
    assert obs.vec.shape == (OBS_DIM,)
    # Moving the object must not change the deployable observation.
    env.data.qpos[env.obj_qpos_adr] += 0.1
    import mujoco

    mujoco.mj_forward(env.model, env.data)
    assert np.allclose(env.observe().vec, obs.vec)


def test_outcome_regimes():
    runner = EpisodeRunner()
    assert runner.run(EASY).outcome == "placed"
    assert runner.run(HEAVY).outcome == "acquisition_failed"
    res = runner.run(MARGINAL)
    assert res.outcome == "lost"
    assert res.loss_step is not None and res.acquisition_step is not None


def test_placed_requires_target_region_and_dwell():
    runner = EpisodeRunner()
    res = runner.run(EASY)
    assert res.outcome == "placed"
    assert abs(res.final_obj_pos[0] - C.TARGET_X) < C.PLACE_XY_TOL
    phases = [r.phase for r in res.records]
    assert phases.count("dwell") >= C.POST_RELEASE_DWELL_STEPS - 1


def test_snapshot_restore_is_bit_exact():
    runner = EpisodeRunner()
    parent = runner.run(MARGINAL, snapshot_steps=set())
    by_step = {r.step: r for r in parent.records}
    for step in list(parent.snapshots)[::4]:
        branch = runner.continue_from(parent.snapshots[step], "continue", 0, record=True)
        assert branch.outcome == parent.outcome
        for rec in branch.records:
            assert np.array_equal(rec.obs, by_step[rec.step].obs)
            assert np.array_equal(rec.obj_pos, by_step[rec.step].obj_pos)


def test_branch_restore_from_fresh_environment():
    """A snapshot restored in a different environment instance continues identically."""
    r1 = EpisodeRunner()
    parent = r1.run(MARGINAL, snapshot_steps=set())
    step = sorted(parent.snapshots)[5]
    r2 = EpisodeRunner()
    r2.run(EASY)  # dirty the second environment with another condition
    b = r2.continue_from(parent.snapshots[step], "continue", 0, record=True)
    by_step = {r.step: r for r in parent.records}
    assert b.outcome == parent.outcome
    assert all(np.array_equal(rec.obs, by_step[rec.step].obs) for rec in b.records)


def test_delay_spends_nominal_continuation_before_remedy():
    runner = EpisodeRunner()
    parent = runner.run(MARGINAL, snapshot_steps=set())
    step = sorted(parent.snapshots)[3]
    b = runner.continue_from(parent.snapshots[step], "squeeze", 5, record=True)
    assert b.remedy_effective_step == step + 5
    by_step = {r.step: r for r in parent.records}
    for rec in b.records:
        if rec.step < step + 5:
            assert np.array_equal(rec.obs, by_step[rec.step].obs)
    at = {r.step: r for r in b.records}
    assert at[step + 4].ctrl[2] == pytest.approx(C.GRIP_FORCE_NOMINAL)
    assert at[step + 5].ctrl[2] == pytest.approx(C.GRIP_FORCE_MAX)


def test_remedies_change_outcome_when_early_enough():
    runner = EpisodeRunner()
    parent = runner.run(MARGINAL, snapshot_steps=set())
    assert parent.outcome == "lost"
    first = sorted(parent.snapshots)[0]
    outcomes = {r: runner.continue_from(parent.snapshots[first], r, 0).outcome for r in ("slow", "squeeze", "place_regrasp")}
    assert "placed" in outcomes.values()


def test_remedy_ignored_outside_decision_phases():
    ctl = NominalController(0.8, 5.0)
    assert ctl.phase == "approach"
    assert ctl.apply_remedy("squeeze") is False
    ctl.phase = "transport"
    assert ctl.apply_remedy("squeeze") is True
    assert ctl.apply_remedy("slow") is False  # one intervention per episode


def test_controller_state_is_deepcopyable_and_independent():
    ctl = NominalController(0.8, 5.0)
    env = GripperTransportEnv()
    obs = env.reset(EASY)
    for _ in range(30):
        obs = env.step(ctl.act(obs))
    clone = copy.deepcopy(ctl)
    ctl.act(obs)
    assert clone.step == ctl.step - 1


def test_hidden_margin_orders_regimes():
    assert hidden_margin(EASY) > hidden_margin(MARGINAL) > hidden_margin(HEAVY)
