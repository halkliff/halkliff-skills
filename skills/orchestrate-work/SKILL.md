---
name: orchestrate-work
description: Explicitly invoked workflow for Astra orchestration, autonomous Sol workstreams, and Luna-first execution with defined goals, bounded decisions, and evidence-based acceptance.
---

# Orchestrate work

Run on the author's explicit invocation, including bounded assignments within
that run. Optimize for accepted outcomes per unit of model work. Apply
pstack-principles; the author owns scope and consequential decisions.

## Define and route

Astra runs `define-goal` before implementation: establish scope, requirements,
acceptance evidence and reserved decisions. Editing this skill creates no goal.
Use [runtime.md](references/runtime.md) for goal and dispatch operations.

| Role | Model / effort | Responsibility |
| --- | --- | --- |
| Orchestrator | Astra / high | Architecture, goal, shared contracts, author interaction, integration, final acceptance |
| Coordinator | Sol / high or xhigh | Decompose and complete a workstream; assign workers and verify results |
| Default worker | Luna / xhigh | Research, claim checks, summaries, implementation, tests, documentation |
| Complex implementation worker | Sol / high or xhigh | Bounded implementation too complex for Luna; remains a leaf |

Research and summarization go to Luna xHigh, including Astra's fact-finding.
A parent may resolve a trivial lookup with one known file read or one targeted
read-only command. If unresolved, delegate; repeated lookups or a command wrapping
an investigation do not qualify. Sol implementation workers receive implementation
assignments, never research assignments. Researchers return complete relevant
findings, sources, counterevidence and limits, without raw search transcripts.

Sol selects High normally and xHigh for difficult coordination. Use a Sol worker
for complex implementation with a short reason. Occupied slots mean queueing,
not promotion. Workers remain leaves. xHigh is not a termination guarantee.

## Read by role

- Astra: this entrypoint, [protocol.md](references/protocol.md), and runtime;
  [uncertainty.md](references/uncertainty.md) when deciding or holding work.
- Sol: this entrypoint and protocol; runtime when dispatching, uncertainty when
  resolving questions. Continue through decomposition, implementation, review and
  correction until the assignment is complete or held.
- Workers: send only [worker.md](references/worker.md) plus a sufficient brief.
  They do not load this manual or coordinator references by default.
- Git owners: [git.md](references/git.md) before repository setup or delivery.
  [CONTEXT.md](CONTEXT.md) resolves workflow-specific terminology when needed.

## Keep execution economical

Delegate coherent, independently checkable chunks. Batch related small work into
one assignment; reuse a suitable worker while its context remains relevant.
Start fresh when unrelated history outweighs reuse. Parents keep decisions,
review and integration; a tightly coupled implementation fix may stay local when
dispatch adds no useful independence. Record a bounded reason for substantial
parent implementation. This exception does not expand research routing.

Allocate actual worker capacity and queue excess work. Dispatch only ready work
with usable prerequisites; integrate accepted slices before growing an avoidable
backlog. Task contracts and status use protocol; rollout policy lives there too.
Only load supporting skills when they change the current task: interface design,
domain terminology, regression risk, investigation or agent-document writing.
`grilling` requires the author's request.

Use [uncertainty](references/uncertainty.md) for bounded discretion, escalation,
hold acknowledgments, resumption and abandoning an approach.

## Acceptance and cost

Workers run meaningful checks and report evidence. Sol reviews the actual diff
and behavior against the parent contract and its derived criteria. Astra checks
the integrated result against the goal. Reuse valid lower-level checks; repeat
only for changed inputs, conflicting evidence or a specific gap. Mechanical
inventories run once by script. Acceptance states live in protocol.

After two failed corrections, Sol changes the method, refines the brief or
escalates. Known requirement conflicts need the author's decision immediately.
Complete only with every requirement evidenced, relevant integrated checks
passing and no required child work or blocking question outstanding.

Apply `unslop` to author-facing prose, deliverables and product documentation.
Routine native messages need concise facts, not a separate prose pass.

Measure messages per accepted requirement, hold ACK share, assignments affected
per hold, ledger/artifact size, author questions, integration backlog, retries and
wall time. Record usage/cost only when exposed. Prefer useful independent work
while waiting; an unchanged blocker warrants no invented progress or extra tests.
