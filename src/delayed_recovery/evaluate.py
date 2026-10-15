"""Closed-loop evaluation of selectors by exact branch-table lookup.

Because a selector cannot change the world before it fires and at most one
intervention is allowed per episode, the closed-loop outcome of a selector at
(age a, delay d) is exactly the branch outcome of the first decision state at
which it fires. ``scripts/verify_lookup.py`` re-simulates a sample of
selector-driven episodes end to end to confirm this equivalence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .dataset import OUT_LOST, OUT_PLACED, R_CONT, DecisionTable
from .selectors import Decision, Selector


@dataclass
class CellResult:
    """Per-episode closed-loop results of one selector in one timing cell."""

    age: int
    delay: int
    episode: np.ndarray
    outcome: np.ndarray  # outcome id
    nominal_outcome: np.ndarray
    intervened: np.ndarray  # bool
    remedy: np.ndarray  # remedy id or R_CONT
    fire_step: np.ndarray  # parent step, -1 if none
    steps_before_loss: np.ndarray  # nominal loss step - fire step (nan if n/a)

    def metrics(self) -> Dict[str, float]:
        n = len(self.episode)
        placed = self.outcome == OUT_PLACED
        nom_placed = self.nominal_outcome == OUT_PLACED
        nom_lost = self.nominal_outcome == OUT_LOST
        inter = self.intervened
        return {
            "n": int(n),
            "completion": float(placed.mean()),
            "nominal_completion": float(nom_placed.mean()),
            "paired_gain": float((placed.astype(int) - nom_placed.astype(int)).mean()),
            "loss_rate": float((self.outcome == OUT_LOST).mean()),
            "intervention_rate": float(inter.mean()),
            "rescue_rate": float((placed & nom_lost).sum() / max(nom_lost.sum(), 1)),
            "harm_rate": float((inter & nom_placed & ~placed).sum() / max((inter & nom_placed).sum(), 1)),
            "unnecessary_rate": float((inter & nom_placed).sum() / max(inter.sum(), 1)),
            "harmful_per_episode": float((inter & nom_placed & ~placed).mean()),
            "median_lead_steps": float(np.nanmedian(self.steps_before_loss)) if np.isfinite(self.steps_before_loss).any() else float("nan"),
        }


def _episode_groups(table: DecisionTable, age: int) -> Dict[int, np.ndarray]:
    mask = table.age == age
    rows = np.flatnonzero(mask)
    groups: Dict[int, List[int]] = {}
    for r in rows:
        groups.setdefault(int(table.episode[r]), []).append(int(r))
    return {e: np.array(sorted(v, key=lambda r: table.step[r])) for e, v in groups.items()}


def run_cell(
    selector: Selector,
    table: DecisionTable,
    age: int,
    delay_idx: int,
    threshold: Optional[float] = None,
    decision: Optional[Decision] = None,
) -> CellResult:
    thr = selector.threshold if threshold is None else threshold
    dec = decision or selector.decide(table, delay_idx)
    groups = _episode_groups(table, age)
    eps, outs, noms, inters, rems, fires, leads = [], [], [], [], [], [], []
    for e, rows in groups.items():
        nominal = int(table.branch_outcome[rows[0], R_CONT, delay_idx])
        fire = rows[dec.score[rows] >= thr]
        if len(fire) and dec.remedy[fire[0]] != R_CONT:
            r0 = fire[0]
            rem = int(dec.remedy[r0])
            outs.append(int(table.branch_outcome[r0, rem, delay_idx]))
            inters.append(True)
            rems.append(rem)
            fires.append(int(table.step[r0]))
            leads.append(float(table.steps_to_loss[r0]) if nominal == OUT_LOST else np.nan)
        else:
            outs.append(nominal)
            inters.append(False)
            rems.append(R_CONT)
            fires.append(-1)
            leads.append(np.nan)
        eps.append(e)
        noms.append(nominal)
    return CellResult(
        age=age,
        delay=table.delays[delay_idx],
        episode=np.array(eps),
        outcome=np.array(outs),
        nominal_outcome=np.array(noms),
        intervened=np.array(inters),
        remedy=np.array(rems),
        fire_step=np.array(fires),
        steps_before_loss=np.array(leads),
    )


def run_grid(selector: Selector, table: DecisionTable, threshold: Optional[float] = None) -> Dict[Tuple[int, int], CellResult]:
    out = {}
    for k, d in enumerate(table.delays):
        dec = selector.decide(table, k)
        for a in table.ages:
            out[(a, d)] = run_cell(selector, table, a, k, threshold, decision=dec)
    return out


def pooled(cells: Dict[Tuple[int, int], CellResult]) -> Dict[str, float]:
    """Pool episode-level results across all cells (each episode x cell counts once)."""
    merged = CellResult(
        age=-1,
        delay=-1,
        episode=np.concatenate([c.episode for c in cells.values()]),
        outcome=np.concatenate([c.outcome for c in cells.values()]),
        nominal_outcome=np.concatenate([c.nominal_outcome for c in cells.values()]),
        intervened=np.concatenate([c.intervened for c in cells.values()]),
        remedy=np.concatenate([c.remedy for c in cells.values()]),
        fire_step=np.concatenate([c.fire_step for c in cells.values()]),
        steps_before_loss=np.concatenate([c.steps_before_loss for c in cells.values()]),
    )
    return merged.metrics()


def choose_threshold(selector: Selector, val: DecisionTable, budget: float, n_grid: int = 60) -> Tuple[float, Dict[str, float]]:
    """Pick the threshold maximizing pooled validation completion subject to
    the pooled intervention rate not exceeding ``budget``. Ties prefer the
    lower intervention rate."""
    decisions = {k: selector.decide(val, k) for k in range(len(val.delays))}
    scores = np.concatenate([d.score[np.isfinite(d.score)] for d in decisions.values()])
    if len(scores) == 0:
        return np.inf, {}
    cands = np.unique(np.quantile(scores, np.linspace(0.0, 1.0, n_grid)))
    cands = np.concatenate([cands, [np.inf]])
    best: Tuple[float, float, float] = (-1.0, 2.0, np.inf)  # completion, rate, thr
    best_metrics: Dict[str, float] = {}
    for thr in cands:
        cells = {}
        for k, d in enumerate(val.delays):
            for a in val.ages:
                cells[(a, d)] = run_cell(selector, val, a, k, thr, decision=decisions[k])
        m = pooled(cells)
        if m["intervention_rate"] <= budget + 1e-9:
            key = (m["completion"], -m["intervention_rate"])
            if key > (best[0], -best[1]):
                best = (m["completion"], m["intervention_rate"], float(thr))
                best_metrics = m
    return best[2], best_metrics


def choose_threshold_per_cell(selector: Selector, val: DecisionTable, budget: float, n_grid: int = 60) -> Dict[Tuple[int, int], float]:
    """Latency-tuned operating point: one threshold per (age, delay) cell,
    each chosen on validation under the same per-cell budget. Models a
    deployment that knows its own measured latency."""
    out: Dict[Tuple[int, int], float] = {}
    for k, d in enumerate(val.delays):
        dec = selector.decide(val, k)
        finite = dec.score[np.isfinite(dec.score)]
        cands = np.concatenate([np.unique(np.quantile(finite, np.linspace(0, 1, n_grid))), [np.inf]]) if len(finite) else np.array([np.inf])
        for a in val.ages:
            best = (-1.0, 2.0, np.inf)
            for thr in cands:
                m = run_cell(selector, val, a, k, thr, decision=dec).metrics()
                if m["intervention_rate"] <= budget + 1e-9 and (m["completion"], -m["intervention_rate"]) > (best[0], -best[1]):
                    best = (m["completion"], m["intervention_rate"], float(thr))
            out[(a, d)] = best[2]
    return out


def run_grid_per_cell(selector: Selector, table: DecisionTable, thresholds: Dict[Tuple[int, int], float]) -> Dict[Tuple[int, int], CellResult]:
    out = {}
    for k, d in enumerate(table.delays):
        dec = selector.decide(table, k)
        for a in table.ages:
            out[(a, d)] = run_cell(selector, table, a, k, thresholds[(a, d)], decision=dec)
    return out


def budget_curve(selector: Selector, table: DecisionTable, n_grid: int = 40) -> List[Dict[str, float]]:
    """Pooled (intervention_rate, completion) curve over thresholds."""
    decisions = {k: selector.decide(table, k) for k in range(len(table.delays))}
    scores = np.concatenate([d.score[np.isfinite(d.score)] for d in decisions.values()])
    if len(scores) == 0:
        return []
    cands = np.unique(np.quantile(scores, np.linspace(0.0, 1.0, n_grid)))
    curve = []
    for thr in np.concatenate([cands, [np.inf]]):
        cells = {}
        for k, d in enumerate(table.delays):
            for a in table.ages:
                cells[(a, d)] = run_cell(selector, table, a, k, thr, decision=decisions[k])
        m = pooled(cells)
        curve.append({"threshold": float(thr), "intervention_rate": m["intervention_rate"], "completion": m["completion"], "harmful_per_episode": m["harmful_per_episode"]})
    return curve


def bootstrap_paired(a: CellResult, b: CellResult, n_boot: int = 2000, seed: int = 0) -> Dict[str, float]:
    """Paired bootstrap over episodes of completion(a) - completion(b)."""
    assert np.array_equal(a.episode, b.episode)
    rng = np.random.default_rng(seed)
    da = (a.outcome == OUT_PLACED).astype(float)
    db = (b.outcome == OUT_PLACED).astype(float)
    diff = da - db
    n = len(diff)
    boots = np.array([diff[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    return {"mean": float(diff.mean()), "ci_low": float(np.quantile(boots, 0.025)), "ci_high": float(np.quantile(boots, 0.975))}


def recovery_frontier(table: DecisionTable, age: int = 0) -> Dict[str, np.ndarray]:
    """From privileged branch labels: for nominal-lost episodes, the fraction
    of decision states at each lead time (steps before nominal loss) where
    each remedy x delay completes. Analysis only."""
    rows = np.flatnonzero((table.age == age) & (table.nominal_lost == 1))
    leads = table.steps_to_loss[rows]
    uniq = np.unique(leads)
    R, K = table.branch_outcome.shape[1:]
    frac = np.full((len(uniq), R, K), np.nan)
    count = np.zeros(len(uniq), dtype=int)
    for i, L in enumerate(uniq):
        sel = rows[leads == L]
        count[i] = len(sel)
        frac[i] = (table.branch_outcome[sel] == OUT_PLACED).mean(axis=0)
    return {"lead_steps": uniq, "fraction_placed": frac, "count": count}
