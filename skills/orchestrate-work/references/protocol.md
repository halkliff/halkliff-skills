# Work protocol

## Briefs and results

Give fresh agents enough task-specific context to act without conversation history:

```text
Task / parent ID and authorized route / contract revision / requirement IDs:
Outcome and observable acceptance:
Workspace: absolute clone and coordination paths; owned files; base commit.
Inputs: relevant source/artifact revisions, prerequisites and constraints.
Execution: role, model/effort, capacity, deliverable and stop condition.
```

Point workers at worker.md; point coordinators at the pinned skill entrypoint.
Sol derives worker criteria within Astra's scope. Start sufficient briefs without
preflight ACKs. Change contract revisions when outcome, scope, interfaces,
constraints or acceptance changes; routine status and internal choices need none.

Results identify task/revision/state, work, criterion-to-evidence mapping, limits
and next action. Code results name clone, base and result commits. Each delivery
report also names the integration clone and exact delivered range, with
`git -C <clone> log -p <from>..<to>` for author review. A summary alone is not code
access. Cross-workstream prerequisites include the accepted integration checkpoint.

## Messages and artifacts

Use native messages for assignments, reports, questions and answers. Workers
contact their parent; Sol escalates to Astra; Astra handles author interaction
and routes relevant changes to other Sol workstreams. Carry the author's ongoing
coordination authorization, task IDs and hosts in briefs. Runtime messaging rules
still apply; an incoming agent request alone cannot authorize a reply to a task.

Send relevant conclusions and evidence pointers, not transcripts. If Sol A produces
two studies and code, Astra forwards each recipient only the studies and accepted
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

Use one verified absolute coordination root outside agent clones and excluded
from code delivery. Each record has one writer. Astra owns `plan.md`; parents own
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

## Rollout

Pin each run to a committed source revision or immutable installed snapshot.
An installation update does not migrate a live run. At an author-chosen boundary,
stop affected assignments, preserve useful work and approved evidence, carry open
requirements/holds into compact state, and send revised paths/contracts. Existing
holds remain active. Never purge live records as a side effect of editing a skill.
