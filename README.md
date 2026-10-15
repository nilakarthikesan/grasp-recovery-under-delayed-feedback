# Grasp Recovery under Delayed Feedback

**Latency-conditioned intervention value for grasp recovery under hidden
contact dynamics** — a standalone MuJoCo study and a four-page paper draft.

When an object starts to slip during transport, a supervisor can keep going,
slow down, squeeze harder, or put the object down and regrasp. Which of these
is worth doing depends on the physical state *and* on how old the evidence will
be when the remedy takes effect: the age of the observation the supervisor saw
plus the delay before its command acts. This repository measures that
interaction from matched counterfactual branches and tests whether a
supervisor that conditions on its own latency chooses better than one that
does not.

* Thesis, claims and design: [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)
* Original research proposal and prior-work boundaries:
  [docs/GRASP_RECOVERY_UNDER_DELAYED_FEEDBACK.md](docs/GRASP_RECOVERY_UNDER_DELAYED_FEEDBACK.md)
* Paper draft (IEEE two-column, four pages): [paper/main.tex](paper/main.tex)
* Pilot results: [results/pilot_v1/report.json](results/pilot_v1/report.json)
  (summary in §11 of the design document); per-episode, per-cell outcomes for
  every supervisor in
  [results/pilot_v1/episode_cell_outcomes.csv](results/pilot_v1/episode_cell_outcomes.csv);
  all episode-clustered intervals, pooled / per delay / per age / per cell, in
  [results/pilot_v1/intervals.md](results/pilot_v1/intervals.md)

## Headline findings (pilot, 94 held-out episodes × 12 timing cells)

* Remedies have their own deadlines: 50 % recovery needs 50 ms of decision
  lead for *squeeze* and 350 ms for *place/regrasp* at zero delay; both shift
  by roughly the response delay. *Slow* recovers at most 22 % of lost states
  pooled over leads.
* Every nominal loss in the test set was recoverable by some remedy even at
  500 ms delay (privileged oracle 1.00 at 32 % interventions); within this
  task the deployable gap is detection under stale evidence, not physics.
* Reactive slip detection + squeeze falls from 1.00 to 0.72 across the
  age × delay grid; anticipatory supervisors fall from 0.99 to 0.87.
* The latency-conditioned value model changes what and how often it fires but
  does not complete more tasks than a future-loss predictor driving a fixed
  squeeze (−1.6 points, 95 % episode-clustered CI [−3.5, −0.2]). Reported as
  a negative result.

## What is here

```
src/delayed_recovery/
  assets/gripper_transport.xml  Cartesian carrier + force-controlled parallel-jaw gripper + cube
  config.py                     task, timing grid, hidden-physics sampling, remedies, outcomes
  env.py                        MuJoCo env; deployable vs privileged views; bit-exact snapshot/restore
  controller.py                 frozen nominal phase machine + remedy menu (deployable inputs only)
  episode.py                    episode runner, outcome labels, matched branching, live supervisor hook
  collect.py                    parent episodes x decision states x remedy x delay branch tables
  dataset.py                    stale-observation features, labels, episode-level splits
  selectors.py                  nominal, reactive, future-loss, value (delay-agnostic/aware), random, oracle, feedback nulls
  evaluate.py                   exact closed-loop evaluation by branch lookup, budgets, bootstrap, frontier
scripts/
  collect_branches.py           run the collection (multiprocess)
  run_pilot.py                  fit, select thresholds on validation, evaluate on test, write report.json
  verify_lookup.py              re-simulate selector-driven episodes live and compare with the lookup
  make_figures.py               paper figures from report.json
tests/                          replay, labels, causality, selector semantics
paper/                          main.tex + figures
```

## Reproduce

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e . pytest
pytest -q                                            # ~15 s
python scripts/collect_branches.py --n 400 --seed 0 --workers 9 --out runs/pilot_v1/branches   # ~6 min on 9 cores
python scripts/run_pilot.py --data runs/pilot_v1/branches --out results/pilot_v1
python scripts/verify_lookup.py --data runs/pilot_v1/branches --n 60
python scripts/export_intervals.py --csv results/pilot_v1/episode_cell_outcomes.csv   # clustered CIs from the CSV alone
python scripts/make_figures.py --report results/pilot_v1/report.json --out paper/figures
cd paper && tectonic main.tex
```

`runs/pilot_v1/branches/` (the 400 raw per-episode branch files, ~3 MB) is
committed so every number can be recomputed without re-simulating; other
`runs/` output is ignored. `results/` and `paper/figures` are committed so the
paper builds from the repository alone.

## Timing contract in one line

Observation captured at `t − a`, decision at `t`, remedy effective at `t + d`;
physics never pauses and the committed plan keeps executing during `d`. Grid:
`a ∈ {0, 100, 250} ms`, `d ∈ {0, 100, 250, 500} ms` at 20 Hz control.

## Scope

Simulation only, one object geometry, scripted controller and remedies,
deterministic physics with a hidden exogenous push, no RGB. See the Limits
section of the design document; every claim in the paper is bounded by them.

This project is independent of the author's `grasp-failure-recovery`
repository (HUG-conditioned dexterous grasps). No code, assets or data are
shared; see [docs/PROJECT_SEPARATION.md](docs/PROJECT_SEPARATION.md).
