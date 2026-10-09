# Work protocol

## Workstream plan

After goal definition, Orchestrator records the work split in `<coord-root>/plan.md`
before implementation dispatch. Reuse settled goal and grilling decisions; use
one compact row per workstream covering:

- Coordinator outcome, owned files/resources and workspace boundaries; serialize
  overlapping writes or give them one owner.
- Prerequisites, which work is ready, and integration order.
- Acceptance evidence to return and the checks for the combined result.
- Review batches, reviewer/verifier ownership and the run's review-gate settings.
- Useful concurrency within verified runtime capacity; queue excess work.

Reference existing requirements and briefs. Coordinators refine their worker
breakdown within these boundaries; update affected rows when dependencies or
ownership change.

Before each implementation dispatch, check the brief's ownership, ready inputs,
acceptance evidence and integration path. Resolve gaps within delegated discretion;
escalate reserved decisions or material gaps through uncertainty. A sufficient plan
proceeds within authorized scope without separate approval or preflight ACK.
Host Plan mode follows
[runtime.md](runtime.md#planning-mode).

## Briefs and results

Brief fresh agents to act without conversation history:

```text
Task / parent ID and authorized route / contract revision / requirement IDs:
Outcome, functional/non-functional acceptance and integration target/order:
Workspace: shared main checkout or isolated clone/worktree; absolute paths;
owned files and shared resources; base commit where applicable.
Inputs: relevant source/artifact revisions, prerequisites and constraints.
Execution: role, model/effort, capacity, deliverable and stop condition.
Review: batch ID, threshold, assessment limit/current round and evidence pointers.
```

Point workers at worker.md and coordinators at the pinned skill entrypoint.
Sol derives worker criteria within Orchestrator's scope. Revise contracts when
outcome, scope, interfaces, constraints or acceptance changes; routine status and
internal choices need none.

Results identify task/revision/state, work, criterion-to-evidence mapping, limits
and next action. Code results name workspace and owned files; isolated work also
names base and result commits. Isolated delivery reports name the integration
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

Each assessment round evaluates one identified candidate revision:

1. The responsible Sol reviews the artifact against the brief with concrete
   findings. Use another GPT-6.1 Sol High reviewer if it substantially implemented
   the candidate. Orchestrator owns review of the integrated result.
2. A distinct GPT-6.1 Sol High verifier, who did not implement or review that
   candidate, inspects requirements, artifact and evidence before consulting the
   reviewer's conclusions. It returns a 1-10 score, criterion-linked reasons, blocking findings,
   optional refinements and evidence limits. Give reviewers/verifiers the worker
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

Use native messages for assignments, reports, questions and answers. Workers
contact their parent; Sol escalates to Orchestrator, who handles author interaction
and cross-workstream changes. Carry the author's ongoing
coordination authorization, task IDs and hosts in briefs. Runtime messaging rules
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
participant. Each record has one writer: Orchestrator owns `plan.md`, parents own
`tasks/<id>/brief.md`, and Sol owns `tasks/<id>/state.md`. Create `artifacts/` and
`archive/` only when used. Files do not wake agents.

Keep the root index about 150 lines maximum, with short tables for:

- Run, goal/authorized objective, pinned skill path/revision and absolute paths.
- Requirements, owners, state and current acceptance evidence.
- Workstream plan above, IDs/hosts, model/capacity, base/head and next action.
- Active holds/questions, affected assignments, pending stops and decision owner.
- Integration candidate, delivered checkpoint, accepted checkpoint and backlog.

Rewrite workstream state, normally under 100 lines. Link extra detail; keep
unresolved work visible. Archive meaningful superseded contracts/decisions outside
continuation's default read path. Read current state, goal status and compact child
updates; consult history for specific questions. Record substantive decisions
beside their work.

Distinguish receipt, local acceptance by Sol, delivery into the author checkout,
and root acceptance after relevant integrated checks. Only the accepted checkpoint
is a dependency for another workstream. An abandoned approach leaves requirements
open; completion requires the whole assignment, not a finished turn.

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
