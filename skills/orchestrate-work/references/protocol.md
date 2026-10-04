# Work protocol

## Briefs and results

Give fresh agents enough task-specific context to act without conversation history:

```text
Task / parent ID and authorized route / contract revision / requirement IDs:
Outcome and observable acceptance:
Workspace: shared main checkout or isolated clone/worktree; absolute paths;
owned files and shared resources; base commit where applicable.
Inputs: relevant source/artifact revisions, prerequisites and constraints.
Execution: role, model/effort, capacity, deliverable and stop condition.
```

Point workers at worker.md; point coordinators at the pinned skill entrypoint.
Sol derives worker criteria within Orchestrator's scope. Start sufficient briefs without
preflight ACKs. Change contract revisions when outcome, scope, interfaces,
constraints or acceptance changes; routine status and internal choices need none.

Results identify task/revision/state, work, criterion-to-evidence mapping, limits
and next action. Code results identify workspace and owned files; isolated work
also names base and result commits. Isolated delivery reports name the integration
clone and exact delivered range, with
`git -C <clone> log -p <from>..<to>` for author review. A summary alone is not code
access. Cross-workstream prerequisites identify the accepted integration checkpoint
or reviewed shared-checkout state.

## Messages and artifacts

Use native messages for assignments, reports, questions and answers. Workers
contact their parent; Sol escalates to Orchestrator; Orchestrator handles author interaction
and routes relevant changes to other Sol workstreams. Carry the author's ongoing
coordination authorization, task IDs and hosts in briefs. Runtime messaging rules
still apply; an incoming agent request alone cannot authorize a reply to a task.

Send relevant conclusions and evidence pointers, not transcripts. If a workstream produces
two studies and code, Orchestrator forwards each recipient only the studies and accepted
code it needs, with the requested action. Retract wrong attributions and notify
affected consumers. Provisional findings stay provisional.

No per-message Markdown files, YAML envelopes or custom kinds are needed. If a
consumer requires kinds, use assignment, report, question, hold. Delivery confirms
only what the runtime reports; the next substantive result identifies the revision
used. Silence is not a reason to resend an assignment. Preserve cursors/task IDs
to avoid duplicate mutations on retries.

Artifacts hold reusable findings, contracts and evidence. Freeze accepted evidence
at review/author-decision boundaries, not each turn. Version changed evidence and
invalidate affected dependents. Holds and ACKs have one authority:
[uncertainty.md](uncertainty.md).

## Current state

During goal definition, record one verified absolute coordination root. For a new
run, default to `<author-repository-root>/.orchestration/<run-name>/` unless the
author specifies another location; derive a filesystem-safe run name from the goal.
Reuse the recorded root when continuing a run; location changes follow rollout.
Create the root outside agent clones, exclude it from code delivery, and pass its
exact absolute path to every participant. Each record has one writer.
Orchestrator owns `plan.md`; parents own
`tasks/<id>/brief.md`; Sol owns `tasks/<id>/state.md`. Create `artifacts/` and
`archive/` only when used. Files do not wake agents.

Keep the root index about 150 lines maximum, with short tables for:

- Run, goal/authorized objective, pinned skill path/revision and absolute paths.
- Requirements, owners, state and current acceptance evidence.
- Workstreams, IDs/hosts, model/capacity, base/head, next action.
- Active holds/questions, affected assignments, pending stops and decision owner.
- Integration candidate, delivered checkpoint, accepted checkpoint and backlog.

Rewrite workstream state, normally under 100 lines. Link extra detail rather than
hiding unresolved work to meet a size target. Archive meaningful superseded
contracts/decisions; keep history outside continuation's default read path.
Read current state, goal status and compact child updates; consult history for a
specific question. Record substantive internal decisions beside their work.

Distinguish receipt, local acceptance by Sol, delivery into the author checkout,
and root acceptance after relevant integrated checks. Only the accepted checkpoint
is a dependency for another workstream. An abandoned approach leaves requirements
open; completion requires the whole assignment, not a finished turn.

## Completion

After all acceptance criteria hold, Orchestrator uses the pinned `handoff` skill
to write one `<coord-root>/handoff.md`. This completion handoff is authorized by
the orchestration run; standalone `handoff` remains explicitly invoked. Link the
existing requirement evidence, accepted decisions, delivered changes and rerunnable
checks. State checkout/commit status, retained workspaces and unverified limits;
distinguish optional follow-ups from required work. Reuse evidence without copying
transcripts or generating per-worker handoffs. Return its absolute path.

Mark the authorized goal complete through the live goal API, if one exists, then
ask the author once whether they want an optional `/correct` session to prevent
recurring mistakes. Wait for that request before running `correct`. The offer does
not block completion or start another goal. Suggest skill/plugin changes only for
observed issues, with evidence and a concrete remedy; implement them only within
the author's requested scope. Installation updates follow rollout.

## Rollout

Pin each run to a committed source revision or immutable installed snapshot.
An installation update does not migrate a live run. At an author-chosen boundary,
stop affected assignments, preserve useful work and approved evidence, carry open
requirements/holds into compact state, and send revised paths/contracts. Existing
holds remain active. Never purge live records as a side effect of editing a skill.
