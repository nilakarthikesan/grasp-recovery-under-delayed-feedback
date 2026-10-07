# Historical Grasp Recovery Implementation Audit

**Assessment date:** October 7, 2026

**Audited project:** `grasp-failure-prediction`, a separate repository at `https://github.com/nilakarthikesan/grasp-failure-recovery`, local revision `737c4ca49169d0769f6069893184f84a099e8028`. This document preserves reference findings; it does not describe the implementation status or assets of this new repository.

The repository can support a controlled evaluation of grasp failure anticipation
and recovery under hidden physical variation. Its strongest assets are an
instrumented Panda manipulation task, demonstration collection, ACT training,
and a MuJoCo state capture primitive. The first research milestone is a measured
nominal policy and a complete replay mechanism. Existing artifacts establish
pipeline execution and a narrow grasp controller diagnostic; they do not yet
establish learned policy competence, recovery performance, or physical robot
results.

## Observed implementation and artifacts

[WeightedContainerTask](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/environment.py)
wraps robosuite's `Lift` environment with a Panda arm and parallel-jaw gripper.
It adds a placement target 0.15 m from the starting position, separates policy
observations from privileged physics metadata, and records task phases,
object loss, collisions, excessive contact force, and controller faults. Object
mass, inertia, and friction can be overridden.

The [configuration](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/config.py) sets a
20 Hz control rate, a 200-step horizon, two 84 by 84 RGB cameras, a 0.18 kg
object, and a 42 mm cube. Policy inputs contain images, joint state,
end-effector pose, and gripper state. Object pose, mass, friction, and contacts
are classified as privileged. Training and validation use disjoint starting
condition seeds; the present configuration does not define physical condition
or object holdouts.

The [scripted demonstrator](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/scripted.py),
[collector](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/collect.py),
[HDF5 recorder](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/record.py),
[LeRobot exporter](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/lerobot_export.py), and
[ACT trainer](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/train_act.py) provide the
nominal learning pipeline. Local saved datasets contain six demonstrations and
562 frames in one smoke run, and five demonstrations and 469 frames in another.
All five episodes in the latter have successful terminal labels at nominal
mass and friction. Both runs contain saved ACT checkpoints. These are local
artifacts under ignored `runs/` directories, rather than a published dataset or
held-out policy evaluation.

The [HUG pilot](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/docs/HUG_SIMULATION_PILOT.md) provides a separate integration path
through official inference, dexterous retargeting, and Shadow Hand execution.
A saved report records six successes among ten proposals on one cube
observation with a fixed 0.1 rad closing adjustment, compared with one success
for those proposals without the adjustment. The experiment demonstrates an
execution rule effect on that observation. It does not establish robustness
across objects, scenes, mass, or friction. The arm carrier and independently
actuated hand remain experimental simulation components.

## Blockers to a defensible evaluation

**Closed-loop evaluation is missing from this checkout.** The
[README](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/README.md) described held-out evaluation as implemented, but the
`part1.evaluate` module registered by [pyproject.toml](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/pyproject.toml) is
absent. The [pipeline runner](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/scripts/run_part1_pipeline.py) catches the
import failure and skips evaluation; corresponding
[tests](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/tests/test_part1_pipeline.py) also skip. A saved training checkpoint
therefore cannot substantiate learned manipulation capability.

**Snapshots preserve physics but not the complete executing system.**
[snapshot.py](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/src/grasp_failure_prediction/part1/snapshot.py) stores MuJoCo
`mjSTATE_INTEGRATION` plus tracked mass, inertia, and friction. Its `extra`
dictionary is omitted from array serialization. The environment's `restore`
method restores physics without restoring task phase, counters, target,
controller state, RNG, or policy action history. The pipeline runner disables
snapshot collection, and the inspected second smoke dataset contains no
snapshots. Matched intervention trials need the additional state before they
can support causal comparisons.

**Task failure is not a future-drop label.** The Panda wrapper combines object
loss and timeout in its failure flag. The HUG scorer can call a height shortfall
“failed acquisition” even when the object remains held for two seconds.
Acquisition failure, inadequate lift, post-acquisition loss, timeout, successful
placement, and object-preserving abort need distinct definitions. Future-loss
windows must exclude incomplete follow-up and split by episode.

**The documentation and reproduction contract need reconciliation.** The
referenced `PART_I_TRAINING_SPEC.md` is absent. Configuration names
`PickPlaceCan`, while the environment instantiates `Lift`. HUG execution uses
an optional partner package and downloaded assets in local directories; a
base installation does not reproduce the full pilot. A public release needs
dependency provenance and setup instructions without redistributing restricted
assets.

## Hardware and compute scope

The [hardware audit](https://github.com/nilakarthikesan/grasp-failure-recovery/blob/737c4ca49169d0769f6069893184f84a099e8028/docs/HARDWARE_AUDIT.md) describes possible collaborator-built,
lab, and funding-dependent robots. Access, embodiment, sensing, and control
interfaces remain unresolved. Quantitative physical claims require a selected
platform with measured timing and actuation limits. Simulator contact features
remain privileged measurements until a corresponding hardware sensor is
available.

The inspected process uses arm64 Python 3.12.13 and PyTorch 2.11.0 and reports
neither MPS nor CUDA available. Repository comments alternately describe Intel
CPU and Apple Silicon MPS execution. Training budgets should follow a measured
throughput check in the intended execution environment.

## First milestone and acceptance criteria

**Milestone: reproducible closed-loop evaluation with persisted complete
replay.** A checkpoint must produce saved held-out episodes with independently
calculated outcomes; training completion alone does not pass this milestone.

1. Implement the evaluation entry point, save checkpoint and configuration
   identifiers, and report acquisition, lift, placement, loss, timeout,
   collision, and excessive force separately. Validate labels against selected
   successful and failed traces. Freeze evaluation seeds independently of
   training and model selection.
2. Persist and restore environment bookkeeping, controller state, RNG, changed
   model parameters, and policy action queues alongside MuJoCo state. Specify
   which fields every controller requires.
3. Save a state during transport, reload it through the persisted format, and
   continue the same commands in the same and a fresh compatible environment.
   Compare state trajectories and outcomes using declared numerical tolerances;
   include an ACT continuation check when ACT is the evaluated agent.
4. Produce a reproducible report with episode counts, uncertainty intervals,
   failure examples, and a competent nominal baseline. Keep smoke checkpoints
   labeled as smoke artifacts.

After this milestone, the research question becomes whether observations and
action history identify a useful intervention before object loss under hidden
mass and friction changes. Matched continuation, slowing, bounded grip
adjustment, and support/regrasp trials can test that question across response
delays. Compare reactive detection, temporal prediction, fixed recovery, and
intervention selection under identical action limits. Publication depends on
a controlled empirical finding and reproducible protocol; a single grasp task
supports an embodied capability evaluation rather than a general AGI claim.
