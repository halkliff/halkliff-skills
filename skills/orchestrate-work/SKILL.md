---
name: orchestrate-work
description: Explicitly invoked orchestration with author-selected model routes, parallel workstreams, and evidence-based acceptance.
---

# Orchestrate work

Run only on the author's explicit invocation, including bounded assignments within
that run. Apply pstack-principles; optimize for accepted outcomes per unit of model
work. The author owns scope and consequential decisions.
Orchestrator enforces accepted scope across workstreams; apply the
[scope boundary](references/uncertainty.md#scope-and-approval) before expanding work.

## Define and route

If the host is in Plan mode, follow [planning mode](references/runtime.md#planning-mode)
before creating run artifacts or activating helpers.
Follow [setup](references/protocol.md#setup): use `in-your-own-words` to confirm
understanding, `sharpen` with `define-goal` to refine the outcome and approach,
and obtain author confirmation before goal activation or implementation. Editing
this skill creates no goal. Explicitly confirm goal-backed or goal-free execution,
recommending a goal defined with `define-goal`. Establish the compact
[workstream plan](references/protocol.md#workstream-plan) and agreed
[verification process](references/verification.md) before dispatch.
Use [runtime.md](references/runtime.md) for goal and dispatch operations.

Settle the main-chat, coordinator and worker model/effort choices with the author
during setup. Use [model routing](references/runtime.md#model-routing) for defaults,
scoped choices and host readback. Record the settled routes in the plan and keep
the [task-chat roster](references/protocol.md#task-chat-roster) current.

The Orchestrator owns shared contracts, author interaction, integration and final
acceptance. Coordinators decompose and complete workstreams, assign workers and
verify their results. Worker, reviewer and verifier assignments remain leaves.
Model selection leaves these responsibilities with their assigned owners.

Delegate research and summarization through the resolved worker route. A parent may
make one known file read or targeted read-only command for a trivial lookup. Delegate
if unresolved. Research briefs name the question and stop condition. Researchers
return relevant findings, sources, counterevidence and limits.

## Read by role

- Orchestrator: this entrypoint, [protocol.md](references/protocol.md), and runtime;
  [uncertainty.md](references/uncertainty.md) when deciding or holding work.
- Coordinators: this entrypoint and protocol; runtime when dispatching, uncertainty when
  resolving questions. Decompose, implement, review and correct until complete or held.
- Workers: send only [worker.md](references/worker.md) plus a sufficient brief.
  They do not load this manual or coordinator references by default.
- Workspace owners: [git.md](references/git.md) before workspace assignment,
  integration or retirement; the author's workspace choice prevails.
  [CONTEXT.md](CONTEXT.md) resolves workflow-specific terminology when needed.
- Coordinators/verifiers: [verification.md](references/verification.md) when
  defining, executing or reconciling acceptance checks; send leaves only the
  assigned procedure and required inputs.

## Keep execution economical

Delegate coherent, independently checkable chunks; batch related small work and
reuse workers while their context remains relevant. Parents keep decisions, review
and integration. A tightly coupled implementation fix may stay local when dispatch
adds no useful independence; record a bounded reason for substantial parent
implementation. This exception does not expand research routing.

Use as many coordinators as needed within runtime capacity; queue excess work.
Dispatch ready work with usable prerequisites and integrate accepted slices before
growing an avoidable backlog. Protocol owns contracts, status and rollout.
Only load supporting skills when they change the current task: interface design,
domain terminology, regression risk, investigation or agent-document writing.
`grilling` requires the author's request.

Use `chief-of-staff` at setup or recurring friction for bounded environment
improvements: better evidence access, one reusable helper, or a structural guard
that prevents a demonstrated mistake. Do useful in-scope work; propose scope or
contract changes to the author. Reuse this workflow's delegation, communication
and completion rules. Broader cleanup and recurring schedules need their own
authorization.

Use [uncertainty](references/uncertainty.md) for bounded discretion, escalation,
hold acknowledgments, resumption and abandoning an approach.

## Acceptance and cost

Workers run meaningful checks and report evidence. Apply the
[review gate](references/protocol.md#review-gate) to substantial deliverables. The
coordinator reviews the artifact and behavior against the contract, an independent
verifier assesses it, and Orchestrator checks the integrated result. Reuse
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
