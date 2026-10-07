# Project Separation Record

On 7 October 2026, the materials developed from the supplied YC video and event
were moved into this independent repository at the user's request.

The experimental proposal, interactive brief, and feasibility audit were retained.
The proposal and brief now describe a new implementation rather than an extension
of the existing grasp-failure-prediction repository. The audit is explicitly
historical and links to the separate source revision it inspected.

The existing robot code, data, checkpoints, Git history, and remote remain in
their original repository. Its README was restored to its pre-conversation
content, and the two new research documents were removed from that checkout.
No push to its remote was performed.

The canvas source is versioned under `research/`. Its only import is the
`cursor/canvas` presentation SDK; the research protocol does not depend on that
SDK or on the original project.
