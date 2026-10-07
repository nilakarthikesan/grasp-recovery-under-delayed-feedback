# Grasp Recovery under Delayed Feedback

**Measuring intervention value under observation staleness and hidden contact dynamics**

Research proposal · 7 October 2026 · Independent project · Implementation pending

The proposed project estimates when slowing transport, adjusting grip, or returning an object to support improves grasp-and-place completion relative to continuing. It measures how stale observations and delayed execution change that intervention value under hidden mass and friction. The practical output is a recovery selector that can distinguish a useful action from an unnecessary or harmful intervention, evaluated against matched continuation. Publication depends on demonstrating a finding beyond the closest existing work.

This repository is independent of the existing grasp-failure-prediction project. The manipulation protocol below is a researched candidate, and its platform selection remains open. No source code, checkpoints, or datasets from the separate project were imported.

The central question is:

> How do observation age and intervention delay change the value of different recovery actions under hidden contact dynamics?

This is an evaluation of embodied reliability and generalization. One manipulation task cannot establish general intelligence. The initial study needs a competent frozen controller, trustworthy replay, and measured outcomes before it needs a larger model.

## What the supplied resources establish

YC's [What If We Stopped Using GPUs?](https://www.youtube.com/watch?v=xc2FTBGRSJo), published 2 October 2026, discusses zero-order optimization, optical computing, neuromorphic systems, and biological computing. Its English automatic transcript was read; audiovisual demonstrations were not independently assessed.

Two passages are particularly relevant. At [20:15](https://www.youtube.com/watch?v=xc2FTBGRSJo&t=1215s), optical-computing discussion identifies system overheads; at [1:10:54](https://www.youtube.com/watch?v=xc2FTBGRSJo&t=4254s), Sean Cole describes a decoder that could perform without informative neural spikes. These motivate measuring the complete feedback loop and testing which inputs actually contribute.

The [Physical AI Builders event](https://events.ycombinator.com/yc-oak-happyhour) is scheduled for 8 October at 5 pm in San Francisco, hosted by YC, Oak, and Physical Intelligence, with Quan Vuong. As of this proposal, it is an event announcement, not a technical talk available for analysis. It signals interest in robotics and intelligent hardware but supplies no benchmark evidence.

The connection between these resources and the proposed experiment is an inference: physical agents offer a setting where computation, sensing, and timely action can be evaluated together. This project would compare software systems on existing hardware; it would not demonstrate a new computing substrate.

## Closest work and the contribution boundary

- [FAIL-Detect, RSS 2025](https://www.roboticsproceedings.org/rss21/p073.pdf), develops runtime failure detection using successful demonstrations and conformal prediction. A generic failure detector is already established research.
- [SAFE, NeurIPS 2025](https://proceedings.nips.cc/paper_files/paper/2025/hash/392d0d05e2f514063e6ce6f8b370834c-Abstract-Conference.html), evaluates multitask VLA failure detection, including unseen tasks and detection timing. An accuracy/early-warning comparison alone is insufficient differentiation.
- [Physical Intelligence's real-time chunking paper](https://www.physicalintelligence.company/download/real_time_chunking.pdf), addresses asynchronous inference and action-chunk continuity. Latency-aware policy execution is an existing capability.
- [Reflex, August 2026 preprint](https://arxiv.org/abs/2608.14379), introduces ReflexBench with dynamic tasks and configurable synchronous/asynchronous latency. A configurable inference-delay benchmark is already available.
- [RoboRecover, September 2026 preprint](https://arxiv.org/abs/2609.28952), evaluates recovery from execution-induced intermediate states across RoboTwin and LIBERO. Intermediate-state recovery is already a benchmark dimension.
- [Kintsugi-VLA, September 2026 preprint](https://arxiv.org/abs/2609.31048), measures expert-relative recoverability through state restoration and branching, including non-monotonic recovery structure and shifted physics. Neither branching nor a recoverability frontier is a new contribution by itself.
- [InterveneSim-Value, public research repository](https://github.com/ethanvillalovoz/intervenesim), compares matched continuation and expert intervention, including intervention budgets and unseen policy seeds. Intervention value over failure risk is also a direct novelty overlap; this repository is a primary implementation source, not evidence of peer review.
- [Failure recovery in remote VLA deployment, 2026 thesis repository](https://github.com/HyuanTan/lerobot_far), already combines pipeline latency measurement with runtime slip/empty-grasp monitoring and recovery on LIBERO and SO-101.
- [Sean Cole's Doom repository](https://github.com/SeanCole02/doom-neuron), already includes zero/random spike controls. Basic input ablations alone would not establish novelty.
- [Reward-DAgger, October 2026 preprint](https://arxiv.org/abs/2610.04054), studies progress-based intervention gating and accuracy/latency tradeoffs. It belongs in the full-paper baseline comparison.
- [VLCP, August 2026 preprint](https://arxiv.org/abs/2608.16978), compares closed-loop VLM replanning with an open-loop counterpart. Feedback controls are validation, not a new evaluation category.

The candidate extension is the joint interaction of **observation age, response delay, recovery choice, and hidden contact physics**, measured from matched states with persistent task outcomes and sensor-dependence controls. The sources above establish substantial overlaps. They do not prove that this exact combination is absent from all prior work; a submission needs a refreshed full-paper comparison.

## Experimental contract

### Task and observations

The initial candidate platform is a simulated Panda arm with a parallel-jaw gripper. Its environment and evaluation code must be implemented in this repository. The task is to acquire, lift, transport, release, and leave a rigid object stably inside the target region. Predeclare placement tolerance, release criterion, post-release dwell, collision limits, and episode timeout. A lift or momentary target crossing cannot count as completion.

Vary mass, friction, initial grasp geometry, and transport acceleration. Pilot ranges must produce successful, recoverable, and irrecoverable cases without relying on numerical instability. Mass changes must update inertia consistently. Verify effective contact friction rather than assuming a configured coefficient is the coefficient used by every contact.

The evaluated agent receives RGB, proprioception, executed actions, and timestamps. Simulator object pose, mass, friction, contact forces, task phase, future outcomes, and branch labels are evaluation metadata or privileged-oracle inputs. Exclude them from deployable-agent features. Simulated contacts cannot be presented as measured tactile sensing.

### Three different times

For each decision, record the sensor capture time, decision start/finish, requested action time, and effective action time. Observation age is capture-to-decision-start; response delay is decision-start-to-effective-action. Their sum is the age of the evidence when the action takes effect. Record queue position and cancelled commands as well.

For a proposed 20 Hz control rate, use a pilot grid of observation ages {0, 100, 250 ms} and added response delays {0, 100, 250, 500 ms}. These are proposed experimental settings, not measured hardware latencies. Implement them as 50 ms control-step multiples and record actual values. Later replay measured latency distributions separately from fixed synthetic delays.

The simulator continues advancing while inference is pending, using a predeclared queue/hold policy. Pausing physics during inference would remove the phenomenon being tested. Compare queue-preserving and queue-cancelling intervention interfaces explicitly; cancellation can itself explain a recovery improvement.

### Matched branches and recovery menu

Restore the full environment, controller, policy memory, action queue, observation buffer, RNG, and event schedule at each candidate decision state. Apply identical exogenous perturbations to all branches. Delay is spent executing the same nominal continuation before a remedy begins.

Compare continuing, slowing transport, bounded grip adjustment where the actuator supports it, and placing the object onto support before regrasping. An object-preserving abort is a distinct result from completing the original task. A privileged scripted teacher supplies an oracle comparison, not evidence that the learned agent recovered autonomously.

Every non-oracle remedy must execute using permitted observations and actuator interfaces as well. A selector with sensor-only inputs driving a scripted recovery that reads true object pose is an oracle-assisted system and must be reported separately.

For a state s, remedy r, and delay d, define intervention value as the paired difference between completion under r after d and completion under nominal continuation. For stochastic policies or disturbances, estimate the difference over matched repeats; a deterministic pair supplies two outcomes, not a calibrated probability. Observation age affects the selector's choice; privileged branch labels describe the physical state independently of the selector's stale information.

Estimate the set of tested states/delays where each remedy remains useful. Do not assume recoverability decreases monotonically or infer a continuous deadline from a sparse grid. Every conclusion is relative to the task, remedy menu, execution semantics, and tested physics.

### Comparators and feedback controls

Use a nominal controller, a reactive threshold with fixed recovery, a temporal failure predictor with that same recovery, and a delay-aware remedy selector. Include matched-budget random interventions and a privileged menu oracle. Begin with logistic/MLP or small temporal baselines; add a larger VLA only when its checkpoint, training requirements, and runtime are feasible.

Freeze each evaluated controller. Compare fresh feedback with delayed, masked, and temporally or episode-mismatched feedback for the recovery selector while keeping nominal control and perturbations fixed. Preserve sampling rate, preprocessing cost, timing, and plausible input distributions where possible. If controls change nominal control too, report that as a separate experiment. A performance collapse under masking demonstrates input dependence; it does not alone prove online adaptation or a faithful internal model of physics.

Separate two experiments: identical decision rules with injected delay identify timing effects; different model sizes with measured runtime compare deployed systems. Their results cannot isolate model capacity from latency without the first control. Record CPU/GPU, preprocessing, inference p50/p95, misses, and actuator timing. Report energy only with suitable measurement; parameter count or estimated FLOPs cannot establish an energy saving.

## Splits and analysis

Split by complete parent episode before extracting frames or branches. All derivatives of a snapshot stay in one split. Separate monitor-fitting, calibration, and final test data. Predeclare physics interpolation, held-out mass/friction combinations, extrapolation, and held-out controller seeds. Geometry generalization requires additional objects; physics variation of one cube cannot support that claim.

Keep natural failure prevalence in final evaluation even if training is balanced. Report completion, object loss, preserved-object abort, interventions per episode, and collision/force-limit violations separately. Predictor metrics include episode-level false alarms, warning lead time, Brier score/reliability, and recall at a fixed alarm budget. Intervention metrics include paired completion differences and harm relative to continuation.

For the initial predictor, predeclare a 500 ms future object-loss horizon after acquisition under frozen nominal continuation. Evaluate Brier score and reliability against that binary outcome; exclude windows without complete follow-up. Warning lead time is the nominal loss timestamp minus the first eligible warning timestamp. Intervention success does not relabel a nominal failure as a false warning. Other horizons and task-failure targets are separate analyses.

Report uncertainty by resampling parent episodes, with controller seeds treated as another source of variation. Branches and adjacent windows are not independent samples. Select thresholds and budgets on validation data. Preserve every final test episode, including failures and timeouts, and publish complete curves rather than a favorable operating point.

## Build sequence and decision gates

1. **Establish trustworthy evaluation.** Implement a standalone task, synchronized episode logging, and an independent closed-loop evaluator; separate drop, failed acquisition, timeout, placement, and abort labels; complete persisted replay. Verify both replay of a saved action sequence and regeneration of policy actions. The [historical feasibility audit](reference/GRASP_RECOVERY_FEASIBILITY.md) records lessons from a separate repository; its implementation and assets are not dependencies of this project.
2. **Demonstrate a competent nominal policy.** Publish held-out nominal results and uncertainty for a frozen checkpoint. Scripted demonstrations and short training smoke runs are infrastructure evidence. Set a nominal competence target before scaling, and explain any shortfall.
3. **Run the interaction pilot.** Use one geometry, a compact calibrated physics grid, two remedies, and the timing grid above. Continue only if multiple regimes exist and delay/staleness alters useful recovery or system ranking reproducibly. If the result is solely that arbitrary large delay hurts, the pilot has not justified a research paper.
4. **Scale the confirmed finding.** Add independent controller seeds, objects, recovery choices, stronger feedback controls, and the closest feasible published baseline. Choose sample size from pilot variance and a predeclared practically meaningful effect. Reserve final test conditions before inspecting outcomes.
5. **Validate physically if access is confirmed.** Use matched blocks of mass, surface, motion, and timing conditions on a supported arm. Physical repeats cannot restore exact counterfactual states. Report their uncertainty and never describe them as simulator-exact pairs.

The first release should contain the protocol, dataset/model cards, versioned configurations, checkpoint hashes, per-episode records, replay verification, paired recovery videos, and a technical report. A simulation-only result can support an initial workshop/preprint submission; a stronger robotics submission needs convincing baseline coverage and generalization, with physical validation strengthening the claim. No acceptance or novelty is guaranteed.

## Alternatives considered

A cross-substrate compute benchmark matches the video but would require reliable access to optical, neuromorphic, or biological systems and comparable interfaces. A broad embodied AGI suite would require far more tasks and embodiments. A generic VLA failure detector has substantial established competition. The proposed study requires its own implementation and asks a narrower question whose answer can change how a physical agent is deployed.

Professional presentation follows from the evidence: precise claims, traceable sources, documented failed experiments, independent replication, and explicit limits. The eventual project's credibility depends on understanding, running, and defending the experiments.
