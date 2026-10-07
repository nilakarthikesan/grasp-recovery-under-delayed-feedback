# Grasp Recovery under Delayed Feedback

**Measuring intervention value under observation staleness and hidden contact dynamics**

Research project developed from the supplied YC Paper Club video
on alternative computing and the YC, Oak, and Physical Intelligence builder event.
The initial candidate asks when a physical recovery action improves task
completion once observations are stale and execution is delayed.

This repository currently contains research and an experimental proposal.
Platform selection, implementation, datasets, and measured results remain open.

## Research materials

- [Experimental proposal and prior work](docs/GRASP_RECOVERY_UNDER_DELAYED_FEEDBACK.md)
- [Interactive research brief source](research/grasp-recovery-under-delayed-feedback.canvas.tsx)
- [Historical audit of a separate grasp repository](docs/reference/GRASP_RECOVERY_FEASIBILITY.md)
- [Project separation record](docs/PROJECT_SEPARATION.md)

## Starting resources

- [What If We Stopped Using GPUs? — YC Paper Club](https://www.youtube.com/watch?v=xc2FTBGRSJo)
- [Physical AI Builders with YC, Oak, and Physical Intelligence](https://events.ycombinator.com/yc-oak-happyhour)

## Initial implementation gate

Choose a standalone manipulation task, implement synchronized observations and
action timing, establish independent outcome scoring, and verify complete
environment/controller/policy replay. Only then collect matched intervention
trials and compare recovery decisions under timing and contact-physics changes.
