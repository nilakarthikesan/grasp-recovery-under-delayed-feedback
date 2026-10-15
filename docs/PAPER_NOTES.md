# Paper notes: everything a writer needs, in one place

Written 15 Oct 2026 against commit `d5ab061` and later. Every number below is
in `results/pilot_v1/report.json` or `results/pilot_v1/intervals.md`; every
decision below is defended by a named test, a named script, or a named control.
If a sentence in a manuscript cannot be traced to one of those, do not write it.

Contents

1. Thesis and the three claims
2. Verdicts from the pilot (headline numbers)
3. System design, section by section, with the argument for each decision
4. How every decision is tested (three layers)
5. Positioning against prior work (what we can and cannot claim)
6. Verified reference list
7. The audit of 15 Oct: what was right, what was wrong, what changed
8. Statistics: the bootstrap fix, exactly
9. Data: where it comes from, where it lives, what is in it
10. Submission checklist (double-blind)
11. What is next (the sequel experiment)
12. File map

---

## 1. Thesis and the three claims

**Thesis.** When a grasp starts to fail, the value of each corrective action is
a joint function of the physical state, the remedy, and the age of the evidence
when the remedy takes effect (observation age + response delay). Each remedy
therefore has its own deadline, and the deadlines shift with response delay. A
supervisor that conditions on its own latency should choose differently from
one that does not; whether that becomes more completed tasks at a matched
intervention budget is the empirical question.

**Claims, ordered by strength** (so the paper survives if the strongest fails):

1. Remedy-specific deadlines exist and shift with response delay. A property
   of the task and menu, measured from privileged branches; no learner.
2. Latency-conditioning changes decisions (firing time, remedy mix) given the
   same stale observations and labels.
3. Latency-conditioning improves completion at a matched intervention budget.

**The question in one line:** how do observation age and response delay,
separately, change the value of different recovery actions under hidden
contact dynamics, and does a supervisor that knows its own latency choose
better?

**Why value, not detection.** RESCUE / CheckVLA / PREFAIL already show that
detecting a failure and being able to act on it are different. We take that as
given and ask what sets the width of the gap: remedy x latency.

**Why age and delay are separate axes.** Age changes only what the supervisor
sees; delay changes only the physics after the command. Different causal paths,
so branch outcomes index by (state, remedy, delay) and features by (state, age).
This is what makes the 3 x 4 grid cheap and what produces the finding that
delay costs more than age over our ranges.

**Why hidden physics.** If mass/friction were observable, remedy value would be
computable from state and there would be no evidence race. Hidden parameters
plus the push are what make "identify the failing episode in time" a real
inference problem for deployable sensors.

---

## 2. Verdicts from the pilot

Test split: 94 acquired parent episodes x 12 timing cells (ages 0/100/250 ms x
delays 0/100/250/500 ms). All intervals are 95% episode-clustered paired
bootstrap (2,000 resamples, unit = parent episode).

**Claim 1: supported.** Deadline = smallest lead bin (>= 20 states) with >= 50%
recovery, from 637 lost-state decision states.

| remedy | delay 0 | 100 | 250 | 500 ms |
|---|---|---|---|---|
| squeeze | 50 | 150 | 300 | 550 ms |
| place/regrasp | 350 | 450 | 600 | 850 ms |
| slow | none | none | none | none |

Slow pooled recovery over all lost states: 22 / 19 / 16 / 9 %. It reaches 50%
only in two 10-state bins at 1.15–1.2 s lead. 77 of 100 nominal losses begin
at or after the push, which slowing cannot counter. Oracle completes 100% of
test episodes at every delay by intervening in the 30 nominally lost ones
(31.9%), median lead 1.05 s.

**Claim 2: supported.** Delay-aware intervention rate (mean over ages) falls
0.472 -> 0.429 -> 0.411 -> 0.379 with delay; agnostic is constant by
construction. With 250 ms-old evidence the aware model shifts toward
place/regrasp: 22/44 interventions at delay 0, 17/36 at delay 500 ms, vs 13/43
for agnostic.

**Claim 3: not supported (not refuted).** Pooled completion and gain vs nominal:

| supervisor | completion | gain [95% CI] | rate | rescue |
|---|---|---|---|---|
| nominal | .681 | — | .00 | .00 |
| random @ aware's rate (10 seeds) | .739 | +.058 [.039, .077] | .42 | .19 |
| reactive slip + squeeze | .852 | +.171 [.109, .234] | .43 | .54 |
| future-loss + squeeze | .946 | +.265 [.178, .348] | .48 | .83 |
| value, delay-agnostic | .934 | +.253 [.165, .334] | .45 | .79 |
| value, delay-aware | .930 | +.249 [.162, .329] | .42 | .78 |
| oracle (privileged) | 1.000 | +.319 [.223, .415] | .32 | 1.00 |

Key paired differences (percentage points):

| comparison | diff [95% CI] |
|---|---|
| aware − agnostic | −0.4 [−1.8, +0.8] |
| aware − future-loss | −1.6 [−3.5, −0.2] |
| agnostic − future-loss | −1.2 [−2.9, 0.0] |
| future-loss − reactive | +9.4 [+4.8, +14.4] |
| aware − reactive | +7.8 [+3.1, +12.7] |
| oracle − future-loss | +5.4 [+2.1, +9.6] |
| aware@celltuned − agnostic@celltuned | −0.6 [−1.9, +0.4] |
| aware@celltuned − future-loss@celltuned | −0.4 [−1.9, +1.2] |

Reactive-vs-anticipatory gap grows with delay: future-loss − reactive is
+3.9 [+0.4, +7.8] at 0 ms, +8.5, +11.7, +13.5 [+7.8, +19.5] at 500 ms; and
with age: +5.9 at 0 ms, +9.6, +12.8 at 250 ms. Reactive completion 1.00 at
(age 0, delay 0) -> 0.72 at (250, 500): 28 points. Anticipatory span 11 points
(future-loss 0.99 -> 0.88; aware 0.98 -> 0.87). Median lead: reactive 0.35 s;
future-loss 0.80 s; agnostic 0.90 s; aware 0.85 s; oracle 1.05 s.

Interpretation: squeeze is the fastest remedy and almost always sufficient
within its deadline, so the menu collapses to "squeeze early enough," which a
future-loss predictor already does. The interval on aware vs agnostic excludes
a benefit larger than about one point; it does not exclude zero.

**Feedback nulls** (delay-aware selector, observations replaced at test time,
timing features and labels intact): frozen 0.810 (−12.0 [−17.8, −6.6]);
mismatched 0.838 (−9.2 [−16.8, −1.4]); masked 0.894 (−3.6 [−7.6, +0.7]).
Masked is degenerate: with constant observations the decision depends only on
timing inputs; it fires in every episode in 8 cells and none in 4 (67% rate),
so it is not an equal-budget comparator.

**Held-out friction band** (0.50–0.58, 64 acquired episodes never in
train/val): nominal 0.5625, future-loss 0.814, agnostic 0.829, aware 0.8125,
oracle 1.000 at 44% rate. Agnostic edges out future-loss here, so that ordering
is not stable. Aware − agnostic −1.7 [−3.8, 0.0]; aware − future-loss −0.1
[−1.2, +0.8].

**Budget curves** (test, thresholds swept): anticipatory supervisors within
3.5 points of each other up to 60% intervention; none reaches the oracle below
99% intervention (future-loss hits 1.0 at 99.3%).

**Age vs delay.** For every supervisor the full 0–500 ms delay sweep costs more
completion than the full 0–250 ms age sweep, at either anchor. The ranges
differ, so do not call this a per-millisecond comparison.

**Collection.** 400 episodes (seed 0); 314 acquired; 100 lost (31.8% of
acquired); 86 acquisition failures; 0 misplaced/timeout. 7,394 decision states;
88,728 branches (7,394 x 3 remedies x 4 delays). Slip onset (3 mm in-hand
descent) to loss: 1–19 steps, median 7 (50–950 ms, median 350 ms), 91 of 100
losses had a detectable onset. Losses by phase: transport 73, lower 27.
Collection took 336.6 s with 9 workers on Apple M4. Split 157/63/94.

**Inference** (one M4 core, unoptimised scikit-learn): detectors 2.9–3.3 ms
median (p95 ~7 ms); value selectors 11.6 ms (p95 21–22 ms). All inside one
50 ms control step. Energy not measured.

---

## 3. System design, section by section

### 3.1 Task and simulator (`env.py`, `assets/gripper_transport.xml`)

MuJoCo 3.16. Cartesian carrier (x, z prismatic joints, kp = 2500 position
servos, gravity-compensated own mass) + parallel-jaw gripper, fingers are
force-controlled motors with ctrl range −3..7 N. 4 cm rigid cube. Phase machine:
approach -> close (4 N) -> lift 10 cm -> transport 0.45 m -> lower (support
contact from wrist-load change) -> release -> retreat -> 1 s dwell.

Hidden per episode: mass U(0.15, 0.50) kg (inertia updated consistently),
sliding friction U(0.35, 0.80) (object geom dominates via element-wise max;
effective coefficient read back from `data.contact`), grasp x-offset
U(−8, 8) mm, push = mass x a_p, a_p ~ U(0, 8) m/s², direction (0.6, 0, −0.8),
4 control steps (200 ms), onset 1–10 steps into transport. Plan (known to the
controller): speed {0.8, 1.2} m/s, accel {5, 8, 12} m/s².

Completion = `placed`: |x − target| < 3 cm (per coordinate), tilt < 15°,
speed < 2 cm/s after the 20-step dwell. Other labels: lost, misplaced,
preserved_abort, acquisition_failed, timeout.

20 Hz control, 2 ms physics (25 substeps). Carrier setpoints first-order-held
across substeps.

Decisions and why:
- Grasp line 3 cm above the cube centre (`GRASP_TCP_Z = 0.050`): lateral
  acceleration makes a pendulum torque, so failure develops over hundreds of
  ms instead of instantly. Without this there is no recovery window.
- First-order hold on carrier setpoints: zero-order hold produced servo chatter
  that dominated the slip physics; most early "slips" were artefacts.
- Force bound 7 N (was 10 N): at 10 N squeeze was a free fix and every learned
  selector matched the oracle. The bound makes squeezing insufficient for the
  heaviest/lowest-friction cases.
- The push: added so that losses are not fully determined by the plan (which
  the controller knows). 77/100 losses begin at or after it. It is part of the
  hidden condition and identical across branches, so branches stay matched.
  A one-step 0–20 m/s² impulse was tried first and was too violent.
- Narrow pads (0.008 x 0.0025 x 0.030) and faster plans: the earlier task was
  too benign (nearly everything placed).
- Ideal Cartesian carrier rather than an arm: isolates gripper/contact physics
  from arm dynamics; declared limit.

### 3.2 Observation contract (`env.py`, `dataset.py`)

Deployable (20 values/step, `OBS_NAMES`): carrier joint pos/vel (4), finger
joint pos/vel (4), finger actuator forces (2), wrist force/torque (6), last
command (4). Supervisor features = 4-step window ending at the observed time
(80) + 7 context (finger gap, steps since acquisition, phase id, planned speed,
planned accel, delta wrist fz vs lift reference, delta gap vs lift reference)
= 87. Delay-aware model adds (age, delay, age + delay) = 90.

Privileged (labels, oracle, stratification only): object pose/velocity,
relative in-hand descent, tilt, contact count, effective friction, mass, push.

No RGB in the pilot (declared narrowing).

Decision and why: the privileged/deployable split is what makes the oracle gap
interpretable as an evidence race. `test_observation_excludes_object_state`
and `test_features_are_causal_and_deployable` enforce it.

### 3.3 Timing contract (`dataset.py`, `episode.py`)

Decision at step t: observation captured at t − a; remedy requested at t;
effective at t + d. Between t and t + d the controller keeps executing its
committed plan (queue-preserving hold). Physics never pauses. Grid a ∈ {0, 2, 5}
steps, d ∈ {0, 2, 5, 10} steps at 50 ms.

Decision and why: separating a from d lets branch outcomes be collected once
per (state, remedy, d) and reused across all a. Tests:
`test_delay_spends_nominal_continuation_before_remedy`,
`test_observation_age_shifts_feature_source`.

### 3.4 Matched branching and exact closed-loop evaluation (`episode.py`, `collect.py`, `evaluate.py`)

At every control step in lift/transport of an acquired episode, save MuJoCo
`mjSTATE_INTEGRATION` (incl. warm-start), the latched observation, and a deep
copy of the controller. From each snapshot run slow / squeeze / place_regrasp
after each delay to a persistent outcome. Continuation = parent's own future.

Restore must NOT call `mj_forward` (it rewrote `qacc_warmstart` and broke
exactness); derived quantities are refreshed with `mj_fwdPosition` +
`mj_fwdVelocity` only when privileged state is read.

One intervention per episode, so a supervisor's closed-loop outcome at (a, d)
is the branch outcome of the first state where it fires. `verify_lookup.py`
re-simulates 60 (episode, cell) pairs live with the trained aware selector:
60/60 identical outcome, firing step, requested remedy.

Decision and why: exactness is the methodological core; it turns "value of
intervention" from an estimate into a measurement and makes budget curves and
feedback nulls free. Tests: `test_snapshot_restore_is_bit_exact`,
`test_branch_restore_from_fresh_environment`,
`test_controller_state_is_deepcopyable_and_independent`,
`test_remedy_ignored_outside_decision_phases`,
`test_branch_table_shapes_and_continue_column`, `test_lookup_policy_semantics`.

### 3.5 Remedy menu (`controller.py`)

| remedy | action | expected sensitivity |
|---|---|---|
| continue | none | — |
| slow | remaining speed and accel x 0.4 | only while acceleration remains ahead |
| squeeze | finger force 4 -> 7 N | fast, most delay-tolerant |
| place/regrasp | decelerate, lower to support contact (wrist-load change, gated by height band, load re-referenced at descent step 4, 1.5 N threshold), open, re-close at 7 N, re-lift, resume at x 0.5; aborts if re-close captures nothing | slow; needs object still in hand |

Decision and why: fast/cheap, slow/decisive, preventive: three remedies with
different physics so deadlines can differ. place/regrasp originally released
mid-air because inertial transients triggered the contact detector; fixed with
the re-referenced load and height gate. Tests:
`test_remedies_change_outcome_when_early_enough`,
`test_remedy_ignored_outside_decision_phases`.

### 3.6 Selectors (`selectors.py`)

All learned components: scikit-learn HistGradientBoosting, fit on train,
threshold chosen on validation to maximise pooled completion subject to
pooled intervention rate <= 0.40 (loss prevalence is 0.32), then frozen.

- Nominal. Random at the aware selector's realised rate (10 seeds).
- Reactive slip + squeeze: predicts privileged current slip label at the
  observed time; fires squeeze.
- Future-loss + squeeze: predicts loss under continuation; fires squeeze.
- Value, delay-agnostic: per-remedy completion models on stale features;
  fires argmax_r [p_r − p_cont] >= tau.
- Value, delay-aware: same + (a, d, a + d).
- Oracle: earliest (state, remedy) whose branch completes at this delay, in
  nominally lost episodes.
- `@celltuned` variants: one validation threshold per cell. Separates "knowing
  latency when setting the operating point" from "conditioning the model."
- Feedback nulls on the aware model: masked (training mean), mismatched (other
  episode same step), frozen (first decision state repeated).

Decision and why: each selector isolates one ingredient (reactive vs
anticipatory; fixed remedy vs menu; agnostic vs aware; learned vs random;
deployable vs privileged). Tests:
`test_value_selector_trains_and_threshold_respects_budget` (aware has exactly 3
more inputs), `test_fixed_remedy_detectors_fire_fixed_remedy`,
`test_random_budget_and_feedback_nulls`.

### 3.7 Splits and statistics (`dataset.py`, `evaluate.py`, `run_pilot.py`)

Episode-level split 50/20/30 of acquired episodes (157/63/94); all ages,
decisions, branches of an episode stay together. Held-out friction band
0.50–0.58 as a second split. Uncertainty: paired cluster bootstrap, unit =
parent episode, 2,000 resamples. Random baseline CI on the 10-seed-averaged
per-row completion. Metrics: completion, paired gain, loss rate, intervention
rate, rescue rate, harm rate, unnecessary rate, median lead.

Decision and why: budget 0.40 because prevalence is 0.32 and the comparison is
meaningless if supervisors cannot afford to rescue most losses plus some false
alarms. Realised test rates 0.43–0.48; reported, not re-tuned. Tests:
`test_split_keeps_episodes_together`,
`test_bootstrap_resamples_parent_episodes_not_rows`.

### 3.8 Limits (state all of them)

Simulation only; soft contacts for friction; one rigid cube; ideal Cartesian
carrier; scripted controller and remedies; deterministic physics with a single
push (paired outcomes binary, not calibrated probabilities); synthetic fixed
delays, not measured latency traces; proprioception + wrist force only; 94
test episodes; validation-set budget rather than matched realised budgets; a
menu in which squeezing is cheap. Snapshot fidelity is not robustness evidence.
No energy, damage, hardware or field claims.

---

## 4. How every decision is tested

**Layer 1: unit/property tests** (`tests/`, 20 tests, ~12 s). Defend protocol
validity: counterfactuals are exact, the supervisor cannot cheat, labels mean
what we say. Mapped to decisions in section 3.

**Layer 2: end-to-end verification.**
- `scripts/verify_lookup.py`: live re-simulation of the trained selector vs
  table lookup, 60/60 (`results/pilot_v1/lookup_verification.json`).
- `scripts/export_intervals.py`: recomputes every interval from the
  per-episode CSV with no simulator or models; matches `report.json` exactly.
- Determinism: `run_pilot.py` reproduces every point estimate exactly on
  rerun; collection is seeded.

**Layer 3: experimental controls.** Oracle (upper bound); random at matched
rate (gain is not from frequency); feedback nulls (model uses observations);
per-cell thresholds (negative result is not an operating-point artefact);
held-out friction band (not interpolation); cluster bootstrap (cells not
independent).

**Not tested, declared:** the 3 mm slip-onset definition; sim-to-real; the
"earliest successful" oracle definition (only that it is an upper bound);
budget overshoot on test; inference timing (measured only).

---

## 5. Positioning against prior work

**Already established, concede it in the first paragraph:**
- Detection accuracy does not imply intervention value: RESCUE (explicit;
  128,340 counterfactual branches, recoverability horizon conditional on the
  intervention repertoire, break-even false-alarm rate); CheckVLA
  (intervention-relative irreversibility time against a fixed repair set).
- Counterfactual branching from restored states: RESCUE; Kintsugi-VLA
  (expert-relative recoverability); RoboRecover (replayed deviation states).
- Latest actionable intervention time: PREFAIL (lift-and-place).
- Latency benchmarks for policies: ReflexBench; latency-aware policy
  execution: real-time chunking.
- Squeeze and slow as remedies: slip-prediction literature.

**What we add, defensible:**
1. Observation age and response delay as separate orthogonal axes with
   different causal paths.
2. Per-remedy deadline shift as a function of delay from bit-exact matched
   states; squeeze and place/regrasp shift by roughly the delay, slow has no
   deadline.
3. A learned selector with its own latency as an input, tested; the negative
   result with intervals.
4. Deployable-only sensing in a contact-rich task with hidden physics and a
   push (RESCUE/CheckVLA are vision-based VLA on LIBERO-style tasks; PREFAIL is
   non-prehensile).
5. Lookup-exact closed-loop evaluation, verified live.

**Vulnerabilities:** a RESCUE-aware reviewer will read the frontier as a
special case of their horizon with a two-parameter latency model (true; our
value is the per-remedy shift and the selector test). Simulation with a
scripted controller is a weaker setting than real VLAs (we trade realism for
exactness). Older haptics/teleoperation work on grip control under delay is
not cited (survivable at 4 pages; a gap for a journal version).

**Chosen stance:** lead with RESCUE, concede the frame, state the narrower
addition in one sentence.

---

## 6. Verified reference list

All arXiv pages fetched 15 Oct 2026. Titles are exact.

- RESCUE — D. Ahmedt-Aristizabal, A. Khamis, M. A. Armin, L. Petersson
  (CSIRO). "RESCUE: Is This Alarm Worth Acting On? Counterfactual Evaluation of
  VLA Runtime Monitors." arXiv:2610.13516. https://arxiv.org/abs/2610.13516
- CheckVLA — Y. Liu, P. Sun, X. Chao, Z. Yang, Y. Xie, L. Zhang, S. Li,
  C. Tang, F. Chen, X.-P. Zhang, W. Ding. "CheckVLA: Execution-Time
  Verification with Action-Conditioned World Model for Long-Horizon Mobile
  Manipulation." arXiv:2607.26789. https://arxiv.org/abs/2607.26789
- PREFAIL — Z. Shangguan, R. Chitale, R. Patel, S. K. Gupta, D. Seita (USC).
  "PREFAIL: Identifying Precursors to Failures in Robotic Lift-and-Place Tasks
  to Improve Task Execution Performance." arXiv:2607.16921.
  https://arxiv.org/abs/2607.16921
- Kintsugi-VLA — I. Snegirev, E. Semenyakina, D. Maliukov, M. Altamirano,
  D. Tsetserukou (Skoltech). "Kintsugi-VLA: Turning Failed Robot Rollouts into
  Recovery Data through Interventional Recoverability." arXiv:2609.31048.
  https://arxiv.org/abs/2609.31048
- RoboRecover — Y. Li, C. Zhao, Z. Wang, J. Wang, C. Shao, Y. Lin, H. Shen,
  J. Zhang (Renmin Univ. / USTC). "RoboRecover: Benchmarking Robot Policy
  Recovery under Execution Deviations." arXiv:2609.28952.
  https://arxiv.org/abs/2609.28952 (code: github.com/RUCKBReasoning/RoboRecover)
- Reflex / ReflexBench — Y. Chen, W. Zhang, X. Li (SJTU). "Reflex: Enabling
  Fast and Predictive Vision-Language-Action Models for Reaction-Critical
  Manipulation." arXiv:2608.14379. https://arxiv.org/abs/2608.14379
  (project: reflexvla.github.io)
- Real-time chunking — K. Black, M. Y. Galliker, S. Levine. "Real-Time
  Execution of Action Chunking Flow Policies." NeurIPS 2025. arXiv:2506.07339.
- FAIL-Detect — C. Xu et al. "Can We Detect Failures Without Failure Data?
  Uncertainty-Aware Runtime Failure Detection for Imitation Learning
  Policies." RSS 2025.
- SAFE — Q. Gu et al. "SAFE: Multitask Failure Detection for
  Vision-Language-Action Models." NeurIPS 2025.
- F. Veiga, B. Edin, J. Peters. "Grip Stabilization of Novel Objects Using
  Slip Prediction." IEEE Trans. Haptics 11(4), 2018.
- (optional) R. Calandra et al. "The Feeling of Success: Does Touch Sensing
  Help Predict Grasp Outcomes?" CoRL 2017.
- (used by the CoRL draft) S. Vats et al. "RecoveryChaining." IROS 2025.
  K. Nazari et al. "Bioinspired trajectory modulation for effective slip
  control." Nature Machine Intelligence 2025.

Note: the three "disputed" references (Reflex, RoboRecover, Kintsugi-VLA) are
real; earlier drafts had paraphrased titles and no authors, which is why a
title search failed. Search by arXiv id.

Not used, dropped: InterveneSim-Value (GitHub repo), lerobot_far (GitHub repo);
unreviewed repositories, removed on audit.

---

## 7. The audit of 15 Oct: what was right, what was wrong, what changed

The author's own verification pass audited commit `b8f8c61`. Resolution:

Correct, fixed in code and data (`d342c73`):
1. Bootstrap resampled 1,128 episode x cell rows instead of 94 parents; pooled
   CIs were ~sqrt(12) too narrow. Fixed (cluster bootstrap); regression test
   added; all intervals recomputed. Point estimates unchanged.
2. Random-baseline CI used seed 0 while the mean used 10 seeds. Fixed.
3. "Slow never exceeds a third" was false (two 10-state bins hit 50%).
   Deadlines now require >= 20 states per bin; pooled fractions reported;
   figure shows sparse bins dotted and legend moved out of the data.
4. Raw counts (7,394 / 88,728), slip-window distribution, push-onset count
   were only in docs; now in `report.json["config"]["collection"]`.

Correct wording problems, fixed in the paper:
- aware rate "0.48 -> 0.37" -> 0.472 -> 0.379.
- "holdout ordering unchanged" -> agnostic overtakes future-loss on the band.
- "age costs less than delay at every operating point" -> full-sweep statement
  with the range caveat.
- "all reach oracle only at 100%" -> none below 99%.
- "40% budget" -> validation cap; realised 0.43–0.48.
- oracle result scoped to test set and declared menu.
- "differences below 2 points unresolved" -> actual interval width.
- 3 cm "box" -> per-coordinate tolerance.

Audit was wrong on one point: Reflex, RoboRecover, Kintsugi-VLA are real
papers (section 6). The three it added (RESCUE, CheckVLA, PREFAIL) are real
and RESCUE is the closest prior work; the paper was repositioned around it.

Everything the ledger said was needed for independent recomputation is now in
the repo: raw branches (`runs/pilot_v1/branches`), per-episode outcomes
(`results/pilot_v1/episode_cell_outcomes.csv`), standalone recomputation
(`scripts/export_intervals.py`).

---

## 8. Statistics: the bootstrap fix, exactly

`evaluate.bootstrap_paired(a, b)`: diff = placed(a) − placed(b) per row (row =
episode x cell). Group rows by parent episode; per-episode total and count.
Resample episodes with replacement 2,000 times; statistic = sum of resampled
totals / sum of resampled counts. Percentile 2.5/97.5. For a single cell this
is the ordinary paired bootstrap over 94 episodes. Seed 0.

Random baseline: `weights_a` = per-row mean completion over the 10 seeds, so
the CI estimates the same quantity as the reported 10-seed mean.

Consequences: aware − future-loss −1.6 [−3.5, −0.2] still excludes zero;
aware − agnostic [−1.8, +0.8] and masked null [−7.6, +0.7] now include zero;
frozen and mismatched nulls remain clearly negative; reactive-vs-anticipatory
gaps remain far from zero.

Write "episode-clustered" or "cluster bootstrap over parent episodes" every
time an interval appears. Do not write "significant" for aware vs agnostic.

---

## 9. Data

**Source.** Entirely generated by the MuJoCo simulation in this repository.
No external dataset. `scripts/collect_branches.py --n 400 --seed 0 --workers 9`
reproduces it in ~6 min.

**Raw** (`runs/pilot_v1/branches/`, committed, 3 MB): one `.npz` per episode
+ `index.json`. Per episode: condition (mass, friction, speed, accel, offset,
push offset/accel, seed), per-step deployable obs (T x 20), ctrl, phase,
privileged obj_pos / rel_z / tilt / contacts, outcome, loss_step,
acquisition_step, first_slip_step, transport_start_step, decision_steps (D),
branch_outcome (D x 4 remedies x 4 delays), branch_loss_step, etc.

**Derived** (`results/pilot_v1/`, committed):
- `report.json`: config incl. collection stats; thresholds; fit/inference
  times; per-selector pooled + per-cell metrics + remedy mix; all comparisons
  with clustered CIs; feedback nulls; budget curves; recovery frontier; 50%
  deadlines (min-bin 20) and pooled recovery fractions; held-out friction
  band.
- `episode_cell_outcomes.csv` (1.3 MB): supervisor, age, delay, episode,
  nominal outcome, outcome, intervened, remedy, fire step, steps before loss;
  for every supervisor and every random seed.
- `intervals.json` / `intervals.md`: 20 comparisons; pooled, per delay, per
  age, per cell.
- `lookup_verification.json`: 60 live-vs-lookup records.

**Features** (`dataset.py`): 87 obs features (+3 timing for aware). Labels:
branch outcomes; `nominal_lost`; `slip_now` (rel_z descent >= 3 mm at the
observed time); `steps_to_loss`.

Platform string in `report.json` and home-directory paths in `index.json` are
identifying; do not upload `results/` or `runs/` as anonymous supplementary
material without scrubbing.

---

## 10. Submission checklist (double-blind)

- Manuscript: no name, affiliation, repo URL, acknowledgements. Repo
  `paper/main.tex` is already anonymised ("Anonymous submission"); CoRL draft
  uses `\author{}`.
- PDF metadata: check /Author, /Creator with `strings main.pdf | grep Author`.
- Supplementary code: must go via an anonymising service (anonymous.4open.science)
  or a fresh unlinked account; the public repo URL identifies the author.
  Scrub `report.json` platform string and `index.json` paths first.
- Do not upload: the audit zip, the verification ledger, anything naming the
  repo.
- Every interval must say episode-clustered. Table caption must say random is
  the 10-seed mean.
- If citing the three disputed refs, use the exact titles in section 6.
- Figures: `paper/figures/fig_frontier.pdf` (dotted sparse bins), `fig_grid.pdf`,
  `fig_budget.pdf`, `fig_nulls.pdf`, `fig_remedy_mix.pdf`; regenerate with
  `scripts/make_figures.py` from `report.json`.
- Two drafts exist (repo IEEEtran 4 pp; CoRL anonymous 4 pp + refs). Delete or
  mark the one not submitted so the repo does not carry two versions with
  different numbers.

---

## 11. What is next (sequel, not deadline day)

The thesis is under-tested because squeeze dominates. The regime where a
latency-aware menu selector should matter:

1. Make squeezing costly: hidden crush limit (object fragility) or a gripper
   already near its force bound, so squeeze can fail or damage.
2. Weaker or slower squeeze (force ramp rate), so its deadline moves toward
   place/regrasp's.
3. Measured latency traces from a real inference stack instead of fixed d.
4. More geometries (cylinder, off-centre mass), a second disturbance type,
   contact noise.
5. A fixed always-squeeze-at-acquisition baseline at matched budgets, and an
   intervention duration/cost analysis (regrasp takes time).
6. Then matched (not counterfactual-exact) blocks on a physical arm.

---

## 12. File map

```
src/delayed_recovery/
  config.py        constants, Condition, TimingGrid, PhysicsGrid, REMEDIES, OUTCOMES
  env.py           MuJoCo env; Observation/Privileged; snapshot/restore; OBS_NAMES
  controller.py    NominalController phase machine; remedies; PHASES
  episode.py       EpisodeRunner.run / continue_from; labels; supervisor hook
  collect.py       collect_episode / collect_dataset / load_dataset
  dataset.py       DecisionTable; observation_features; build_decision_table; split_episodes
  selectors.py     Nominal, FixedRemedyDetector, ValueSelector, RandomBudget, OracleMenu, feedback_null
  evaluate.py      CellResult.metrics; run_grid; choose_threshold(_per_cell); budget_curve;
                   bootstrap_paired (cluster); recovery_frontier
scripts/
  collect_branches.py   collection (multiprocess)
  run_pilot.py          fit, thresholds, evaluate, report.json + episode_cell_outcomes.csv
  verify_lookup.py      live re-simulation vs lookup
  export_intervals.py   clustered CIs from the CSV alone -> intervals.{json,md}
  make_figures.py       figures from report.json
tests/                  20 tests
docs/
  SYSTEM_DESIGN.md      design + §11 pilot verdicts
  PAPER_NOTES.md        this file
  GRASP_RECOVERY_UNDER_DELAYED_FEEDBACK.md   original proposal and prior-work scan
  PROJECT_SEPARATION.md independence from grasp-failure-recovery
paper/                  main.tex (IEEEtran, anonymised), main.pdf, figures/
results/pilot_v1/       report.json, episode_cell_outcomes.csv, intervals.{json,md}, lookup_verification.json
runs/pilot_v1/branches/ raw per-episode branch files (401)
```

Reproduce everything:

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install -e . pytest
pytest -q
python scripts/collect_branches.py --n 400 --seed 0 --workers 9 --out runs/pilot_v1/branches
python scripts/run_pilot.py --data runs/pilot_v1/branches --out results/pilot_v1
python scripts/verify_lookup.py --data runs/pilot_v1/branches --n 60
python scripts/export_intervals.py --csv results/pilot_v1/episode_cell_outcomes.csv
python scripts/make_figures.py --report results/pilot_v1/report.json --out paper/figures
cd paper && tectonic main.tex
```
