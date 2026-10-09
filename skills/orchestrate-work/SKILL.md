---
name: orchestrate-work
description: Explicitly invoked orchestration with selectable Astra/Sol leadership, Sol workstreams, Luna-first execution, and evidence-based acceptance.
---

# Orchestrate work

Run only on the author's explicit invocation, including bounded assignments within
that run. Apply pstack-principles; optimize for accepted outcomes per unit of model
work. The author owns scope and consequential decisions.

## Define and route

If the host is in Plan mode, follow [planning mode](references/runtime.md#planning-mode)
before creating run artifacts or activating helpers.
Before implementation, Orchestrator runs `define-goal` to establish scope,
requirements, evidence and reserved decisions. Editing this skill creates no goal.
During setup, settle the [review gate](references/protocol.md#review-gate), including
its one-time question about missing preferences, and record the absolute
[coordination root](references/protocol.md#current-state).
Describe the work and agree on its workspace approach: recommend isolation for
complex parallel work that risks interference, or the shared main worktree for
simpler independent work. Establish the compact
[workstream plan](references/protocol.md#workstream-plan) before implementation
dispatch. Use [runtime.md](references/runtime.md) for goal and dispatch operations.

Select the Orchestrator's model in the main thread before invocation; the skill
does not switch it.

| Role | Model / effort | Responsibility |
| --- | --- | --- |
| Orchestrator | GPT-6 Astra / high or GPT-6.1 Sol / xhigh | Architecture, goal, shared contracts, author interaction, integration, final acceptance |
| Coordinator | GPT-6.1 Sol / high or xhigh | Decompose and complete a workstream; assign workers and verify results |
| Default worker | Luna / xhigh | Research, claim checks, summaries, implementation, tests, documentation |
| Complex implementation worker | GPT-6.1 Sol / high or xhigh | Bounded implementation too complex for Luna; remains a leaf |

Route research and summarization, including Orchestrator's fact-finding, to Luna
xHigh. A parent may make one known file read or targeted read-only command for a
trivial lookup; delegate if unresolved. Repeated lookups or a command wrapping an
investigation do not qualify. Sol implementation workers receive no research
assignments. Researchers return complete relevant findings, sources, counterevidence and
limits without search transcripts.

Sol uses High normally and xHigh for difficult coordination. Record a short reason
for using a Sol implementation worker. Queue work when slots are occupied; worker
promotion is not a capacity workaround. Workers remain leaves. xHigh is not a
termination guarantee.

## Read by role

- Orchestrator: this entrypoint, [protocol.md](references/protocol.md), and runtime;
  [uncertainty.md](references/uncertainty.md) when deciding or holding work.
- Sol: this entrypoint and protocol; runtime when dispatching, uncertainty when
  resolving questions. Decompose, implement, review and correct until complete or held.
- Workers: send only [worker.md](references/worker.md) plus a sufficient brief.
  They do not load this manual or coordinator references by default.
- Workspace owners: [git.md](references/git.md) before workspace assignment,
  integration or retirement; the author's workspace choice prevails.
  [CONTEXT.md](CONTEXT.md) resolves workflow-specific terminology when needed.

## Keep execution economical

Delegate coherent, independently checkable chunks; batch related small work and
reuse workers while their context remains relevant. Parents keep decisions, review
and integration. A tightly coupled implementation fix may stay local when dispatch
adds no useful independence; record a bounded reason for substantial parent
implementation. This exception does not expand research routing.

Use as many Sol coordinators as needed within runtime capacity; queue excess work.
Dispatch ready work with usable prerequisites and integrate accepted slices before
growing an avoidable backlog. Protocol owns contracts, status and rollout.
Only load supporting skills when they change the current task: interface design,
domain terminology, regression risk, investigation or agent-document writing.
`grilling` requires the author's request.

Use [uncertainty](references/uncertainty.md) for bounded discretion, escalation,
hold acknowledgments, resumption and abandoning an approach.

## Acceptance and cost

Workers run meaningful checks and report evidence. Apply the
[review gate](references/protocol.md#review-gate) to substantial deliverables: Sol
reviews the artifact and behavior against the contract, independent GPT-6.1 Sol
High verifiers assess it, and Orchestrator checks the integrated result. Reuse
valid checks; repeat only for changed inputs, conflicting evidence or a specific
gap. Run mechanical inventories once by script. Protocol defines acceptance states.

Complete only with every requirement evidenced, relevant integrated checks
passing and no required child work or blocking question outstanding.
Follow [completion](references/protocol.md#completion) for the single handoff,
goal completion and optional author-requested `/correct` session.

Apply `unslop` to author-facing prose, deliverables and product documentation.
Routine native messages need concise facts, not a separate prose pass.

Measure messages per accepted requirement, hold ACK share, assignments affected
per hold, ledger/artifact size, author questions, integration backlog, retries and
wall time. Record usage/cost only when exposed. Prefer useful independent work
while waiting; an unchanged blocker warrants no invented progress or extra tests.
