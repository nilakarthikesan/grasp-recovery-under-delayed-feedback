"""Recovery selectors (supervisors) and comparators.

Every selector maps decision rows to (remedy choice, score). The closed-loop
policy fires the chosen remedy at the first decision state of an episode whose
score reaches the selector's threshold; one intervention per episode.

Selectors with learned components are fitted on training rows only. The
threshold is chosen on validation rows to meet an intervention budget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from . import config as C
from .dataset import OUT_PLACED, R_CONT, DecisionTable

N_REMEDIES = len(C.REMEDIES)
R_SQUEEZE = C.REMEDIES.index("squeeze")


def _gbm(seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.06,
        max_leaf_nodes=15,
        min_samples_leaf=40,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=seed,
    )


def _fit_binary(x: np.ndarray, y: np.ndarray, seed: int):
    if y.min() == y.max():
        return _Constant(float(y.mean()))
    model = _gbm(seed)
    model.fit(x, y)
    return model


class _Constant:
    def __init__(self, p: float) -> None:
        self.p = p

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        return np.stack([np.full(len(x), 1 - self.p), np.full(len(x), self.p)], axis=1)


@dataclass
class Decision:
    remedy: np.ndarray  # row -> remedy index
    score: np.ndarray  # row -> firing score (higher = more inclined to act)


class Selector:
    name: str = "base"
    threshold: float = np.inf
    uses_privileged: bool = False

    def fit(self, table: DecisionTable, seed: int = 0) -> "Selector":
        return self

    def decide(self, table: DecisionTable, delay_idx: int) -> Decision:
        raise NotImplementedError


class Nominal(Selector):
    name = "nominal"

    def decide(self, table: DecisionTable, delay_idx: int) -> Decision:
        n = len(table.step)
        return Decision(np.full(n, R_CONT), np.full(n, -np.inf))


class FixedRemedyDetector(Selector):
    """A detector (reactive slip or future-loss) driving one fixed remedy."""

    def __init__(self, target: str, remedy: int = R_SQUEEZE) -> None:
        assert target in ("slip_now", "nominal_lost")
        self.target = target
        self.remedy = remedy
        self.name = ("reactive_slip" if target == "slip_now" else "failure_predictor") + f"+{C.REMEDIES[remedy]}"
        self.model = None

    def fit(self, table: DecisionTable, seed: int = 0) -> "FixedRemedyDetector":
        y = getattr(table, self.target)
        self.model = _fit_binary(table.x_obs, y, seed)
        return self

    def decide(self, table: DecisionTable, delay_idx: int) -> Decision:
        p = self.model.predict_proba(table.x_obs)[:, 1]
        return Decision(np.full(len(p), self.remedy), p)


class ValueSelector(Selector):
    """Per-remedy completion models; acts on estimated intervention value.

    ``aware=True`` conditions on observation age and response delay
    (latency-conditioned); ``aware=False`` sees only the stale observation
    features and is trained on the same mixture of timings.
    """

    def __init__(self, aware: bool) -> None:
        self.aware = aware
        self.name = "value_delay_aware" if aware else "value_delay_agnostic"
        self.models: Dict[int, object] = {}

    def fit(self, table: DecisionTable, seed: int = 0) -> "ValueSelector":
        for r in range(N_REMEDIES):
            xs, ys = [], []
            for k in range(len(table.delays)):
                xs.append(table.features(k, self.aware))
                ys.append(table.placed(r, k))
            x = np.concatenate(xs)
            y = np.concatenate(ys)
            if not self.aware:
                # Delay-agnostic: identical rows repeated per delay would only
                # reweight; keep them so both selectors see the same labels.
                pass
            self.models[r] = _fit_binary(x, y, seed + r)
        return self

    def value_matrix(self, table: DecisionTable, delay_idx: int) -> np.ndarray:
        x = table.features(delay_idx, self.aware)
        p = np.stack([self.models[r].predict_proba(x)[:, 1] for r in range(N_REMEDIES)], axis=1)
        return p

    def decide(self, table: DecisionTable, delay_idx: int) -> Decision:
        p = self.value_matrix(table, delay_idx)
        value = p - p[:, [R_CONT]]
        value[:, R_CONT] = -np.inf
        remedy = value.argmax(axis=1)
        return Decision(remedy, value.max(axis=1))


class RandomBudget(Selector):
    """Intervenes in a fixed fraction of episodes at a random eligible state
    with a random remedy. Averaged over seeds by the evaluator."""

    name = "random_budget"

    def __init__(self, budget: float, seed: int = 0) -> None:
        self.budget = budget
        self.seed = seed
        self.threshold = 0.5

    def decide(self, table: DecisionTable, delay_idx: int) -> Decision:
        rng = np.random.default_rng(self.seed * 1000 + delay_idx)
        n = len(table.step)
        remedy = np.full(n, R_CONT)
        score = np.zeros(n)
        keys = np.stack([table.episode, table.age], axis=1)
        _, first = np.unique(keys, axis=0, return_index=True)
        for start in first:
            mask = (table.episode == table.episode[start]) & (table.age == table.age[start])
            rows = np.flatnonzero(mask)
            if rng.random() < self.budget:
                row = rng.choice(rows)
                remedy[row] = rng.integers(1, N_REMEDIES)
                score[row] = 1.0
        return Decision(remedy, score)


class OracleMenu(Selector):
    """Privileged upper bound: in episodes that nominal continuation loses,
    fire the earliest remedy whose branch completes at this delay."""

    name = "oracle_menu"
    uses_privileged = True
    threshold = 0.5

    def decide(self, table: DecisionTable, delay_idx: int) -> Decision:
        placed = table.branch_outcome[:, :, delay_idx] == OUT_PLACED
        placed[:, R_CONT] = False
        any_ok = placed.any(axis=1)
        remedy = np.where(any_ok, placed.argmax(axis=1), R_CONT)
        score = (any_ok & (table.nominal_lost == 1)).astype(float)
        return Decision(remedy, score)


def feedback_null(table: DecisionTable, mode: str, train_mean: np.ndarray, seed: int = 0) -> DecisionTable:
    """Return a copy of ``table`` whose observation features are uninformative
    while timing, phase bookkeeping and labels are unchanged.

    * ``masked``     – every observation feature replaced by its training mean.
    * ``mismatched`` – observation features taken from a different episode at
                       the same decision index and age.
    * ``frozen``     – observation features frozen at the first decision state
                       of the episode (stale forever).
    """
    from .dataset import subset

    t = subset(table, np.ones(len(table.step), dtype=bool))
    x = t.x_obs.copy()
    if mode == "masked":
        x[:] = train_mean
    elif mode == "mismatched":
        rng = np.random.default_rng(seed)
        episodes = np.unique(t.episode)
        perm = rng.permutation(episodes)
        mapping = dict(zip(episodes, perm))
        lookup = {(e, d, a): i for i, (e, d, a) in enumerate(zip(t.episode, t.decision, t.age))}
        for i, (e, d, a) in enumerate(zip(t.episode, t.decision, t.age)):
            j = lookup.get((mapping[e], d, a))
            if j is None:  # donor episode shorter: use its last decision
                cand = [idx for (ee, dd, aa), idx in lookup.items() if ee == mapping[e] and aa == a]
                j = max(cand, key=lambda idx: t.decision[idx])
            x[i] = table.x_obs[j]
    elif mode == "frozen":
        for e in np.unique(t.episode):
            for a in t.ages:
                rows = np.flatnonzero((t.episode == e) & (t.age == a))
                x[rows] = table.x_obs[rows[np.argmin(t.decision[rows])]]
    else:
        raise ValueError(mode)
    t.x_obs = x
    return t
