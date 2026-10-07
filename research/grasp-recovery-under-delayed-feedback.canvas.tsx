import { Button, Card, CardBody, CardHeader, Divider, Grid, H1, H2, H3, Link, Row, Stack, Table, Text, useHostTheme, useState } from "cursor/canvas";

const sources = [
  { name: "YC Paper Club", date: "2 Oct 2026 · supplied video", url: "https://www.youtube.com/watch?v=xc2FTBGRSJo", boundary: "Alternative compute. System overhead and decoder shortcuts motivate full-loop timing and feedback controls." },
  { name: "Physical AI Builders", date: "8 Oct 2026 · upcoming event", url: "https://events.ycombinator.com/yc-oak-happyhour", boundary: "YC, Oak and Physical Intelligence gathering with Quan Vuong. Announcement supplies context, not experimental findings." },
  { name: "FAIL-Detect", date: "RSS 2025", url: "https://www.roboticsproceedings.org/rss21/p073.pdf", boundary: "Success-only runtime monitoring is established." },
  { name: "SAFE", date: "NeurIPS 2025", url: "https://arxiv.org/abs/2506.09937", boundary: "Unseen-task failure detection and accuracy/timing tradeoffs are established." },
  { name: "Real-time chunking", date: "2025 research paper", url: "https://www.physicalintelligence.company/download/real_time_chunking.pdf", boundary: "Asynchronous inference and committed action chunks are existing control methods." },
  { name: "ReflexBench", date: "14 Aug 2026 · preprint", url: "https://arxiv.org/abs/2608.14379", boundary: "Dynamic manipulation with configurable inference latency already exists." },
  { name: "RoboRecover", date: "24 Sep 2026 · preprint", url: "https://arxiv.org/abs/2609.28952", boundary: "Recovery from execution deviations is already a benchmark dimension." },
  { name: "Kintsugi-VLA", date: "25 Sep 2026 · preprint", url: "https://arxiv.org/abs/2609.31048", boundary: "Branch-based, expert-relative and non-monotonic recoverability overlaps directly." },
  { name: "InterveneSim-Value", date: "Public research repository", url: "https://github.com/ethanvillalovoz/intervenesim", boundary: "Matched intervention value and policy-seed holdouts overlap directly; peer review not established." },
  { name: "LeRobot FAR", date: "2026 thesis repository", url: "https://github.com/HyuanTan/lerobot_far", boundary: "Pipeline timing, runtime failure monitoring, and automatic retry already coexist." },
  { name: "Doom neuron", date: "Speaker's public repository", url: "https://github.com/SeanCole02/doom-neuron", boundary: "Zero/random feedback ablations already exist; masking alone is not novel." },
];
const gates = [
  ["01", "Trustworthy evaluator", "Implement held-out evaluation; distinguish loss, timeout, placement and abort; persist complete replay.", "Saved trajectories reproduce physics and policy actions, including queues and RNG."],
  ["02", "Competent nominal controller", "Freeze a learned checkpoint and report closed-loop outcomes with uncertainty.", "A scripted demonstration or short training run cannot substitute for agent competence."],
  ["03", "Interaction pilot", "One geometry, calibrated physics ranges, two remedies, and independently varied observation age and response delay.", "Timing changes useful recovery or supervisor ranking reproducibly; trivial delay degradation is insufficient."],
  ["04", "Research release", "Add seeds, objects, feedback controls and the closest feasible published comparator.", "Versioned protocol, episode records, replay checks, paired videos and a defensible empirical finding."],
  ["05", "Physical validation", "Conditional on confirmed arm access, sensing and control support.", "Matched physical trial blocks; no claim of exact counterfactual restoration."],
];

export default function GraspRecoveryResearch() {
  const theme = useHostTheme();
  const [section, setSection] = useState("Decision");
  const [age, setAge] = useState(100);
  const [delay, setDelay] = useState(250);
  const repo = "/Users/nilakarthikesan/grasp-recovery-under-delayed-feedback";
  const rule = { borderTop: `1px solid ${theme.stroke.tertiary}`, paddingTop: 16 };
  return <Stack gap={20} style={{ padding: 24, maxWidth: 1080, margin: "0 auto", lineHeight: 1.6 }}>
    <Text size="small" tone="secondary">RESEARCH DIRECTION · 7 OCTOBER 2026 · PROPOSED EXPERIMENT</Text>
    <H1>Grasp Recovery under Delayed Feedback</H1>
    <Text>When does slowing transport, adjusting grip, or returning to support improve grasp-and-place completion under stale observations and hidden mass and friction?</Text>
    <Row wrap gap={8}>{["Decision", "Sources", "Protocol", "Build gates"].map(label => <Button key={label} variant={section === label ? "primary" : "secondary"} onClick={() => setSection(label)}>{label}</Button>)}</Row>
    <Divider />
    {section === "Decision" && <Stack gap={18}>
      <Grid columns="repeat(auto-fit, minmax(260px, 1fr))" gap={24}>
        <Stack gap={10}>
          <H2>Recommended research question</H2>
          <Text weight="semibold">How do observation age and intervention delay change recovery value under hidden mass and friction?</Text>
          <Text>Evaluate matched continuation and remedy branches, then test whether a supervisor selects the remedy that changes the outcome. Measure stable placement, object loss and preserved-object abort separately.</Text>
          <Text tone="secondary">The candidate contribution is an empirical interaction and an audited protocol. Novelty remains conditional on a pilot and a refreshed literature comparison.</Text>
        </Stack>
        <Card>
          <CardHeader>First implementation milestone</CardHeader>
          <CardBody><Stack gap={12}>
            <Text weight="semibold">Independent evaluation and complete persisted replay</Text>
            <Text>This independent repository contains research materials. Implement its own task, evaluator, synchronized logging and complete replay before collecting benchmark results. The historical audit records pitfalls from a separate codebase.</Text>
            <Link href={`${repo}/docs/reference/GRASP_RECOVERY_FEASIBILITY.md`}>Read the historical reference audit</Link>
          </Stack></CardBody>
        </Card>
      </Grid>
      <Stack gap={8} style={rule}>
        <H2>What makes the study relevant</H2>
        <Text>A detector may identify failure accurately after a useful intervention is no longer possible. A faster supervisor may outperform a more accurate one, depending on stale inputs, action commitment and contact dynamics. This is a hypothesis to test.</Text>
        <Text>Feedback controls connect the study to the video's decoder shortcut: verify that recovery depends on informative observations, with timing and nominal control held fixed.</Text>
      </Stack>
      <Table headers={["Direction", "Assessment"]} rows={[
        ["Delayed intervention evaluation", "Researched candidate. Requires a standalone implementation and a result beyond existing latency and recovery work."],
        ["Cross-substrate compute evaluation", "Closer to optical/neuromorphic hardware; comparable system access is unconfirmed."],
        ["Broad embodied AGI benchmark", "Multiple tasks and embodiments required. One grasp task supports a narrower claim."],
        ["Generic failure detector", "Substantial overlap with FAIL-Detect, SAFE and newer monitors."],
      ]} />
      <Text size="small" tone="secondary">Project status: independent research repository with proposal and source analysis. Implementation and experiments have not started. The earlier code and smoke artifacts belong to a separate project.</Text>
    </Stack>}
    {section === "Sources" && <Stack gap={16}>
      <H2>Primary sources and novelty boundaries</H2>
      <Text>Read the video's full automatic transcript; audiovisual claims were not independently verified. The event is upcoming. Publication labels below distinguish papers, preprints and implementation repositories.</Text>
      <Table headers={["Source", "Date or status", "What already exists / implication"]} rows={sources.map(source => [<Link key={source.name} href={source.url}>{source.name}</Link>, source.date, source.boundary])} />
      <Row wrap gap={16}>
        <Link href="https://www.youtube.com/watch?v=xc2FTBGRSJo&t=1215s">20:15 · optical system overhead</Link>
        <Link href="https://www.youtube.com/watch?v=xc2FTBGRSJo&t=4254s">1:10:54 · decoder shortcut</Link>
      </Row>
      <Text tone="secondary">These sources support a project direction. They do not establish that the proposed combination is the first of its kind or guarantee publication.</Text>
    </Stack>}
    {section === "Protocol" && <Stack gap={18}>
      <H2>Timing contract</H2>
      <Text>Timestamp capture, inference start/finish, command request and effective action. Continue stepping physics during inference. Declare queued-action cancellation and hold behavior.</Text>
      <Grid columns="repeat(auto-fit, minmax(250px, 1fr))" gap={24}>
        <Stack gap={8}>
          <label htmlFor="observation-age">Observation age at decision start: {age} ms</label>
          <input id="observation-age" type="range" min={0} max={500} step={50} value={age} onChange={(event: { target: { value: string } }) => setAge(Number(event.target.value))} style={{ accentColor: theme.accent.primary }} />
          <label htmlFor="response-delay">Decision start to effective action: {delay} ms</label>
          <input id="response-delay" type="range" min={0} max={1000} step={50} value={delay} onChange={(event: { target: { value: string } }) => setDelay(Number(event.target.value))} style={{ accentColor: theme.accent.primary }} />
        </Stack>
        <Stack gap={8} style={{ padding: 16, background: theme.fill.tertiary }}>
          <Text weight="semibold">Evidence age at effective action: {age + delay} ms</Text>
          <Text>{(age + delay) / 50} control steps at the proposed 20 Hz rate.</Text>
          <Text size="small" tone="secondary">Illustrative timing arithmetic only. This does not predict recovery success or display measured runtime.</Text>
        </Stack>
      </Grid>
      <Stack gap={10} style={rule}>
        <H3>Matched interventions</H3>
        <Text>Restore physics, controller memory, action queue, observation buffer, RNG and event schedule. Compare continue, slow, bounded grip adjustment, and support/regrasp from the same decision state. Both selector and remedy must use permitted inputs; privileged execution is oracle-assisted.</Text>
        <Text>Measure paired completion differences over matched repeats. Keep all branches of a parent episode in the same split. Preserve non-monotonic recovery islands instead of assuming a single deadline.</Text>
      </Stack>
      <Table headers={["Control", "Question it resolves"]} rows={[
        ["Same decision rule + injected delay", "Does timing itself change recovery outcome?"],
        ["Different models + measured runtime", "Which deployed system performs best under its actual timing?"],
        ["Frozen selector + feedback nulls", "Does the selector depend on informative feedback? Nominal control remains fixed."],
        ["Matched intervention budgets", "Is improvement explained by more frequent assistance?"],
        ["Hidden physics held out", "Does performance transfer beyond fitted conditions?"],
        ["Persistent release and placement", "Does the original task finish and remain stable?"],
      ]} />
      <Text tone="secondary">Deployable inputs: RGB, proprioception, executed actions and timestamps. Simulator pose/contact/physics values remain offline labels or oracle inputs. Energy claims require measurement.</Text>
    </Stack>}
    {section === "Build gates" && <Stack gap={16}>
      <H2>Progress depends on evidence</H2>
      {gates.map(([number, title, action, criterion]) => <Grid key={number} columns="40px 1fr" gap={14} style={rule}>
        <Text tone="tertiary">{number}</Text>
        <Stack gap={6}><H3>{title}</H3><Text>{action}</Text><Text size="small" tone="secondary">Pass criterion: {criterion}</Text></Stack>
      </Grid>)}
      <Text>No hardware purchase or training-scale commitment is needed to settle the initial evaluator and replay milestone. Policy training throughput and hardware access still need to be established.</Text>
    </Stack>}
    <Divider />
    <Row wrap gap={16}>
      <Link href={`${repo}/docs/GRASP_RECOVERY_UNDER_DELAYED_FEEDBACK.md`}>Full experimental proposal</Link>
      <Link href={`${repo}/docs/reference/GRASP_RECOVERY_FEASIBILITY.md`}>Historical reference audit</Link>
    </Row>
    <Text size="small" tone="tertiary">No new benchmark measurements are represented here. Scope: the value of grasp recovery under delayed feedback and hidden contact dynamics.</Text>
  </Stack>;
}
