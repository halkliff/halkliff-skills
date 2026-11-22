# Work protocol

## Setup

For a new run, use `in-your-own-words` to restate the desired outcome, problem,
constraints and unresolved choices. Apply `sharpen` alongside `define-goal`:
identify the decisive sources, simplest viable approach and an independent
observation that could disprove success. Define the objective first; defer live
goal creation until confirmation. Read-only setup investigation may resolve facts.

Present one compact proposal covering the understanding, functional/non-functional
requirements, reserved decisions, work split and [verification](verification.md).
Explicitly confirm goal-backed or goal-free execution with it, recommending a
live goal defined through `define-goal`; reuse an explicit choice for this run.
Settle workspace approach and review settings; task creation/coordination is part
of the invocation and Orchestrator chooses placement through runtime. Reuse
established preferences and ask only for missing choices.
In the same setup proposal, ask one combined model-and-effort question for any
unsettled main-chat, coordinator and worker choices. Recommend the economical
[starting routes](runtime.md#model-routing) and offer the two main-chat defaults.
Reuse the author's explicit choices, including scoped workstream or purpose
choices. When the author has selected the main-chat settings, use that choice.
For a main-chat change, the author uses the host model/effort selector. Record
the actual settings when the host exposes them.
Recommend isolation for interfering parallel work, shared work for independent
scopes. Wait for the author's explicit confirmation or corrections before goal
activation, helper activation or implementation. Silence is not confirmation.

After confirmation, record the accepted proposal in the existing plan and follow
runtime for activation/dispatch. Continuing an unchanged confirmed run needs no
new setup approval. Material changes follow uncertainty; Plan mode stays in chat.
Keep author constraints with their decision source, separate from Root's operating
choices and measured observations. A task-headroom estimate is not an author limit.

## Workstream plan

After goal definition, Orchestrator records the work split in `<coord-root>/plan.md`
before implementation dispatch. Reuse settled goal and grilling decisions; use
one compact row per workstream covering:

- Coordinator outcome, owned files/resources and workspace boundaries; serialize
  overlapping writes or give them one owner.
- Prerequisites, which work is ready, and integration order.
- Acceptance evidence to return and the checks for the combined result.
- The accepted verification process/revision and owner of shared live resources.
- Review batches, reviewer/verifier ownership and the run's review-gate settings.
- Accepted role model/effort pairs, scoped overrides and decision references.
- Useful concurrency within verified runtime capacity; queue excess work.

Choose concurrency from current headroom and actual mutable resources. Shared
indexes, caches, outputs and aliases retain one owner/exclusion; disjoint work may
use existing monitored lanes under Root's current allocation. Coordinators cannot
self-release a lane. Record one integration candidate/owner and an ordered backlog
of actual base/result/dependency commits and unresolved behavior in this plan.

Reference existing requirements and briefs. Coordinators refine their worker
breakdown within these boundaries. Update affected rows when dependencies,
ownership or model choices change, applying route changes to future assignments.

Before each implementation dispatch, check the brief's requirement basis,
responsibility boundary, ownership, ready inputs, acceptance evidence and integration
path. Resolve gaps within delegated discretion;
escalate reserved decisions or material gaps through uncertainty. A sufficient plan
proceeds within authorized scope without separate approval or preflight ACK.
Host Plan mode follows
[runtime.md](runtime.md#planning-mode).

## Briefs and results

Brief fresh agents to act without conversation history:

```text
Task / parent ID and authorized route / contract revision / requirement IDs:
Main-thread worker contacts: allowed coordinator thread IDs/hosts and clarification topic
when useful; decisions/uncertainty and final acceptance remain with the parent.
Outcome, functional/non-functional acceptance and integration target/order:
Workspace: shared main checkout or isolated clone/worktree; absolute paths;
owned files and shared resources; base commit where applicable.
Inputs: relevant source/artifact revisions, prerequisites and constraints.
Execution: role, purpose, resolved model/effort and override decision if any;
bounded outcome/grant, capacity, assigned adapter and stop condition.
Review: batch ID, threshold, assessment limit/current round, verification
procedure/revision, owned live resources and evidence pointers.
```

Point workers at worker.md and coordinators at the pinned skill entrypoint.
The coordinator derives worker criteria within Orchestrator's scope. Revise
contracts when outcome, scope, interfaces, constraints or acceptance changes.
Routine status and internal choices need no contract revision.
For consequential cross-owner behavior, extend the existing acceptance row with
the owning public path, transition/callout or alternate exit, authority that can
change, required variants, expected result and forbidden effects. Registration,
replacement and retirement belong to their existing owner. Routine edits stay
in the enclosing batch; this adds no checkpoint or per-edit record.
Use standing grants for coherent outcomes. Routine metadata completion and proved
pre-invocation corrections within them need no new ACK. Actual I/O/job failure or
uncertain side effects stop the affected sequence with partial evidence preserved.

Results identify task/revision/state, work, criterion-to-evidence mapping, limits
and next action. Before returning a batch for acceptance, the coordinator marks
the declared boundary cases actually covered and any remaining gaps. Code results
name workspace and owned files. Isolated work also names base and result commits.
Isolated delivery reports name the integration
clone and exact delivered range with
`git -C <clone> log -p <from>..<to>` for author review. A summary alone is not code
access. Cross-workstream prerequisites identify the accepted integration checkpoint
or reviewed shared-checkout state.

## Review gate

During goal setup/planning, reuse author-supplied values. Ask once for any missing
minimum critique score (1-10) or maximum total assessments (positive integer),
suggesting 9/10 and three. Default only values left unspecified; record both settings
in `plan.md` and review briefs. They neither resolve missing requirements nor
authorize scope changes.

Batch substantial deliverables for acceptance: consequential designs before
implementation, implementation slices before integration, and the integrated result
before completion. Keep batches small and coherent; cover relevant architecture,
public behavior, security and component boundaries. Include routine edits in their
enclosing batch. Independent work may continue during review; integrate passing
slices promptly and check combined behavior before releasing them as prerequisites.
For large designs, reconcile key interfaces and exercise a narrow representative
path before expanding the frozen design; preserve every accepted requirement and
assessment limit.

Each assessment round evaluates one identified candidate revision:

1. The responsible coordinator reviews the artifact against the brief with concrete
   findings, checking requirement provenance and boundary ownership as well as
   correctness. If the coordinator substantially implemented the candidate, use a
   separate reviewer on the [resolved review route](runtime.md#model-routing).
   Orchestrator owns review of the integrated result.
2. A verifier separate from the implementers and reviewer uses the resolved
   verifier route. It inspects requirements, artifact and evidence before consulting
   the reviewer's conclusions. From the changed owner paths, it independently selects
   a material alternate exit or transition to challenge against the expected
   result and forbidden effects. It returns a 1-10 score, criterion-linked reasons,
   blocking findings, optional refinements and evidence limits. Give reviewers/verifiers the worker
   guide, this gate and a bounded brief; they remain leaves.
3. Accept only when the score meets the agreed threshold, every agreed functional
   and non-functional requirement for the batch has evidence, relevant checks pass,
   and no blocking finding or consequential uncertainty remains unresolved.
   A score cannot compensate for a failed or unverified requirement.
4. Otherwise, return concrete deficiencies to the workers and assess their corrected
   candidate. Reuse valid evidence; recheck changed inputs and affected criteria.
   The default three assessments comprise one initial assessment and two correction/
   reassessment rounds. Reviewer failures count even before verification; fixes
   before verification do not hide an assessment.

At 9/10, only optional refinements remain. Scores express judgment supported by
findings, not measured correctness. Below-threshold scores require deficiencies
against agreed criteria; optional polish alone cannot justify another round.
Stop at the first pass.

At the limit, hold the failed batch and its dependents through uncertainty. Preserve
useful work; escalate findings, attempted fixes and a recommendation to Orchestrator
and, if unresolved, the author. Only the author may grant extra rounds or change the
gate. No nested correction loops or counter resets: changing agents, rephrasing an
assignment or replacing its batch preserves the count for the same unmet outcome.
Escalate known requirement conflicts or missing author intent immediately. Hold only
affected work; goal lifecycle rules still apply.

Keep one current assessment in task state (root state for the integrated result):
batch/candidate, round/limit, reviewer/verifier IDs, score, criterion-to-evidence pointers,
unresolved findings and next action. Use native messages for review traffic and
retain accepted evidence through this protocol.

## Messages and artifacts

Use native messages for assignments, reports, questions and answers. Main-thread
workers may send findings and factual clarifications directly to the coordinator
task chats in their brief. Their assigning parent retains decisions, consequential
uncertainty, holds and acceptance; conflicting or contract-changing replies go
to that parent. Coordinator-assigned workers contact their coordinator, who can
escalate to Orchestrator for author interaction or cross-workstream changes. Carry
the author's ongoing coordination authorization, task IDs and hosts in briefs.
Runtime messaging rules
still apply; an incoming agent request alone cannot authorize a reply to a task.

Send each recipient relevant conclusions, evidence pointers and requested actions.
Retract wrong attributions and notify affected consumers; mark provisional findings.

Use no per-message artifacts or envelopes. If a consumer requires kinds, use
assignment, report, question, hold. Delivery confirms
only what the runtime reports; the next substantive result identifies the revision
used. Silence is not a reason to resend an assignment. Preserve cursors/task IDs
to avoid duplicate mutations on retries.

Artifacts hold reusable findings, contracts and evidence. Freeze accepted evidence
at review/author-decision boundaries, not each turn. Version changed evidence and
invalidate affected dependents. Holds and ACKs have one authority:
[uncertainty.md](uncertainty.md).

## Current state

During goal definition, record one verified absolute coordination root. Default new
runs to `<author-repository-root>/.orchestration/<run-name>/` unless the author
specifies another location; derive a filesystem-safe run name from the goal.
Reuse the recorded root when continuing a run; location changes follow rollout.
Keep the root outside agent clones and code delivery; pass its exact path to every
participant. Each record has one writer. Orchestrator owns `plan.md`, parents own
`tasks/<id>/brief.md`, and the coordinator owns `tasks/<id>/state.md`. Create
`artifacts/` and `archive/` only when used. Files do not wake agents.

Keep the root index about 150 lines maximum, with short tables for:

- Run, goal/authorized objective, pinned skill path/revision and absolute paths.
- Requirements, owners, state and current acceptance evidence.
- Workstream plan above, task-chat roster, capacity, base/head and next action.
- Active holds/questions, affected assignments, pending stops and decision owner.
- Integration candidate, delivered checkpoint, accepted checkpoint and backlog.

Rewrite workstream state, normally under 100 lines. Link extra detail; keep
unresolved work visible. Archive meaningful superseded contracts/decisions outside
continuation's default read path. Read current state, goal status and compact child
updates; consult history for specific questions. Record substantive decisions
beside their work.

Distinguish receipt, local acceptance by the coordinator, delivery into the author
checkout, and root acceptance after relevant integrated checks. Only the accepted checkpoint
is a dependency for another workstream. An abandoned approach leaves requirements
open; completion requires the whole assignment, not a finished turn.

## Task-chat roster

Orchestrator keeps one durable row per app chat used by the run, including the
main chat, in `plan.md` or linked current task state. Record the parent, workstream
and role or purpose, actual chat ID and host, requested model and effort, observed
model and effort with their source when exposed, and current status and next action.
Use `pending` for unresolved creation and retain the client ID. Mark each
setting with unavailable readback `unverified`. The submitted selection belongs
in the requested fields.

Update the row at creation, substantive status changes, later setting changes
and recovery. Resolve a returned chat ID before messaging. On recovery, reconcile
its current host, route, status and existing ownership. If the assignment moves
to a replacement chat, link the rows and retain the old chat's status. Use native
messages for handoffs; roster entries describe chats and their current state.

## Completion

After acceptance, Orchestrator uses the pinned `handoff` skill to write one
`<coord-root>/handoff.md`, authorized by this run; standalone `handoff` remains
explicitly invoked. Link requirement evidence, accepted decisions, delivered
changes and rerunnable checks. State checkout/commit status, retained workspaces
and unverified limits; separate optional follow-ups from required work. Reuse
evidence without transcripts or per-worker handoffs. Return its absolute path.

Mark the authorized goal complete through the live goal API, if one exists, then
offer an optional `/correct` session once. Wait for the author's request before
running it; the offer neither blocks completion nor starts another goal. Suggest
skill/plugin changes only for observed issues with evidence and a concrete remedy;
implement within the author's requested scope. Installation updates follow rollout.

## Rollout

Pin each run to a committed source revision or immutable installed snapshot.
An installation update does not migrate a live run. At an author-chosen boundary,
stop affected assignments, preserve useful work and approved evidence, carry open
requirements/holds into compact state, and send revised paths/contracts. Existing
holds remain active. Never purge live records as a side effect of editing a skill.
