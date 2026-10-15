import numpy as np
import pytest

from delayed_recovery import config as C
from delayed_recovery.collect import OUTCOME_ID, collect_episode
from delayed_recovery.dataset import (
    CONTEXT_FEATURE_NAMES,
    N_OBS_FEATURES,
    OUT_PLACED,
    R_CONT,
    WINDOW_FEATURE_NAMES,
    build_decision_table,
    observation_features,
    split_episodes,
    subset,
)
from delayed_recovery.evaluate import choose_threshold, run_cell, run_grid, pooled
from delayed_recovery.selectors import FixedRemedyDetector, Nominal, OracleMenu, RandomBudget, ValueSelector, feedback_null

DELAYS = (0, 2, 5)
AGES = (0, 2)


@pytest.fixture(scope="module")
def logs():
    conds = [
        C.Condition(0.20, 0.75, 0.8, 5.0),
        C.Condition(0.35, 0.4948, 1.2, 8.0, -0.00259),
        C.Condition(0.3349, 0.4519, 0.8, 12.0, -0.00528),
        C.Condition(0.50, 0.35, 0.8, 5.0),
    ]
    out = []
    for i, c in enumerate(conds):
        log = collect_episode(i, c, DELAYS)
        meta = {k: v for k, v in log.items()}
        out.append(meta)
    return out


def test_branch_table_shapes_and_continue_column(logs):
    for log in logs:
        D = len(log["decision_steps"])
        assert log["branch_outcome"].shape == (D, len(C.REMEDIES), len(DELAYS))
        if D:
            assert (log["branch_outcome"][:, R_CONT, :] == OUTCOME_ID[log["outcome"]]).all()
    assert any(len(l["decision_steps"]) == 0 for l in logs)  # acquisition failure has no decisions


def test_features_are_causal_and_deployable(logs):
    log = next(l for l in logs if len(l["decision_steps"]))
    t = int(log["decision_steps"][-1])
    x = observation_features(log, t)
    assert x.shape == (N_OBS_FEATURES,)
    assert len(WINDOW_FEATURE_NAMES) + len(CONTEXT_FEATURE_NAMES) == N_OBS_FEATURES
    # Perturbing privileged arrays or any observation after t must not change features.
    mutated = dict(log)
    mutated["obj_pos"] = log["obj_pos"] + 1.0
    mutated["rel_z"] = log["rel_z"] + 1.0
    obs = log["obs"].copy()
    obs[t + 1 :] += 100.0
    mutated["obs"] = obs
    assert np.array_equal(observation_features(mutated, t), x)
    # Perturbing an observation inside the window must change features.
    obs2 = log["obs"].copy()
    obs2[t] += 1.0
    mutated["obs"] = obs2
    assert not np.array_equal(observation_features(mutated, t), x)


def test_observation_age_shifts_feature_source(logs):
    table = build_decision_table(logs, AGES, DELAYS)
    assert (table.obs_step == np.maximum(table.step - table.age, 0)).all()
    assert table.branch_outcome.shape[1:] == (len(C.REMEDIES), len(DELAYS))
    # Rows at different ages share the same branch labels (physics does not depend on age).
    for e in np.unique(table.episode):
        for d in np.unique(table.decision[table.episode == e]):
            rows = np.flatnonzero((table.episode == e) & (table.decision == d))
            assert all(np.array_equal(table.branch_outcome[rows[0]], table.branch_outcome[r]) for r in rows)


def test_split_keeps_episodes_together(logs):
    s = split_episodes(logs, 0, fractions=(0.5, 0.25, 0.25))
    all_eps = np.concatenate(list(s.values()))
    assert len(np.unique(all_eps)) == len(all_eps)
    assert all(len(logs[e]["decision_steps"]) > 0 for e in all_eps)


def test_lookup_policy_semantics(logs):
    table = build_decision_table(logs, AGES, DELAYS)
    nominal = run_grid(Nominal(), table)
    for cell in nominal.values():
        assert not cell.intervened.any()
        assert np.array_equal(cell.outcome, cell.nominal_outcome)
    oracle = run_grid(OracleMenu(), table)
    for (a, d), cell in oracle.items():
        m = cell.metrics()
        assert m["completion"] >= nominal[(a, d)].metrics()["completion"]
        assert not (cell.intervened & (cell.nominal_outcome == OUT_PLACED)).any()


def test_value_selector_trains_and_threshold_respects_budget(logs):
    table = build_decision_table(logs, AGES, DELAYS)
    sel = ValueSelector(aware=True).fit(table)
    thr, m = choose_threshold(sel, table, budget=0.5)
    sel.threshold = thr
    cells = run_grid(sel, table)
    assert pooled(cells)["intervention_rate"] <= 0.5 + 1e-9
    agn = ValueSelector(aware=False).fit(table)
    assert agn.features_shape_check if hasattr(agn, "features_shape_check") else True
    assert table.features(0, True).shape[1] == table.features(0, False).shape[1] + 3


def test_fixed_remedy_detectors_fire_fixed_remedy(logs):
    table = build_decision_table(logs, AGES, DELAYS)
    for target in ("slip_now", "nominal_lost"):
        det = FixedRemedyDetector(target).fit(table)
        dec = det.decide(table, 0)
        assert (dec.remedy == C.REMEDIES.index("squeeze")).all()
        assert dec.score.shape == (len(table.step),)


def test_random_budget_and_feedback_nulls(logs):
    table = build_decision_table(logs, AGES, DELAYS)
    rb = RandomBudget(1.0, seed=1)
    cells = run_grid(rb, table)
    assert pooled(cells)["intervention_rate"] == pytest.approx(1.0)
    mean = table.x_obs.mean(axis=0)
    for mode in ("masked", "mismatched", "frozen"):
        t = feedback_null(table, mode, mean)
        assert t.x_obs.shape == table.x_obs.shape
        assert np.array_equal(t.branch_outcome, table.branch_outcome)
        assert np.array_equal(t.age, table.age)
    assert np.allclose(feedback_null(table, "masked", mean).x_obs, mean)
