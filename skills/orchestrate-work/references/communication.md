# Communication and artifact handoff

Markdown is the durable record. Native task/agent messaging is the notification
channel. Read this before creating a coordinator or worker brief. Read
[task-contract.md](task-contract.md) for brief/result contents and
[uncertainty.md](uncertainty.md) for decision authority and dependency holds.

## Shared location and ownership

Astra establishes one coordination directory for the run, normally the parent
directory of the root ledger. Give every participant its absolute path and verify
access from each workspace/host. Separate Git worktrees do not share relative
paths. If hosts cannot access the same directory, arrange and verify an authorized
artifact transfer before making a recipient depend on a file. Escalate unavailable
transport; do not claim that a local path delivered content to a remote host.

Use this small structure, creating only directories needed by actual work:

```text
<coordination-directory>/
  plan.md                       Astra-owned outcome, task registry, decisions, holds
  tasks/<task-id>/brief-r1.md     Written by the assigning parent
  tasks/<task-id>/state.md        Written by that task's owning agent
  messages/<sender-id>/<id>.md    Written only by that sender
  artifacts/<producer-id>/       Versioned outputs written only by that producer
```

The registry maps logical IDs to real task/agent IDs, host, parent route, workspace,
contract revision, dependencies, consumers, and last applied message IDs. Astra
owns the cross-task registry; Sol records its workers in its own state file.
Agents send updates rather than editing the root ledger. Give each Luna its own
artifact directory. Sol may reference Luna artifacts without copying them, but
publishes its own review and workstream manifest.

These records are working state, not automatically committed product documentation.
Keep code in its assigned workspace and user-facing deliverables in the requested
output location. The manifest can point to both. Published message and artifact
revisions are immutable: write a new revision for corrections and identify what
it supersedes. Single-writer draft files may change before publication.

## Who communicates with whom

| Route | Purpose and authority |
| --- | --- |
| Astra -> Sol | Assignment, accepted decisions, scoped hold/resume, relevant cross-task updates |
| Sol -> Luna | Bounded assignment, evidence-backed answers, corrections, scoped hold/resume |
| Luna -> its Sol | Results, evidence, questions, acknowledgments |
| Sol -> Astra | Reviewed result manifest, unresolved questions, proposed dependency changes, acknowledgments |
| Sol A -> Astra -> Sol B/C | Astra routes relevant artifacts and specifies whether to read, review, or apply them |
| Astra <-> author | Astra asks unresolved questions in the main conversation and records the author's answer |

The author should not have to monitor child tasks or mailbox files to discover a
question. Astra presents the exact decision, necessary evidence, and consequences
in chat. Source the recorded answer to that user message, with an exact quotation
when useful; preserve ambiguity by asking a follow-up rather than interpreting it.
If the author directly steers a Sol task, Sol records and forwards that instruction
to Astra so dependent work can be reconciled. Conflicting directions escalate.

Route cross-workstream changes through Astra; workers do not assign work to peers
or reinterpret another task's contract. A research finding is evidence, not a
user decision. Forwarding an artifact does not make it authoritative or integrated.

## Message envelope

Use a short Markdown file with YAML frontmatter. Each sender allocates a unique
monotonic ID within the run, such as `sol-a-0007`; include the run identity. On
retry, reuse the same ID and content. Change content under a new ID with
`supersedes`. Omit optional fields when irrelevant.

```yaml
---
id: sol-a-0007
run: feature-run-01
from: sol-a
to: [astra]
kind: report
task: task-a
contract: task-a-r3
reply_to: astra-0002
required_ack: none
---
```

Kinds are `assignment`, `report`, `question`, `decision`, `update`, `hold`,
`resume`, and `ack`. The body states the requested action, affected requirement/
task/artifact IDs, relevant evidence or manifest, and remaining questions.
For holds, include the question ID, hold ID, dependency scope, and current contract
revision. For resume, reply to the exact hold ID and include the resolved question,
accepted decision, new revision, and still-active holds. Track each hold separately;
a delayed resume cannot clear a newer hold or a hold for a different question.
Reject stale control messages against the current decision/contract record and
request missing predecessors instead of guessing an order from delivery time.
Record the latest applied control message per sender and affected task/question;
an older control message for that scope cannot overwrite its newer state. A resume
requires a registered matching hold, a recorded accepted resolution, and the current
contract revision. If any is missing, request that record and keep dependent work
held. Sequence gaps for unrelated messages do not themselves imply a missing hold.

Use `required_ack: applied` for assignments, decisions, resumes, and updates that change
dependent work; `stopped` for holds; `none` for information-only messages. If a
receipt alone is needed, use `received`. Send acknowledgments as new messages
with `reply_to`, actual state (`received`, `applied`, `stopped`, `pending`, or
`rejected`), and evidence or reason. A receipt is not application; stopped means
affected work actually stopped, with unfinished external operations listed as
pending. Never acknowledge a stronger state than observed. `pending` and `rejected`
do not satisfy an applied/stopped requirement. Acknowledgments require no further
acknowledgment. One message can acknowledge several IDs to reduce traffic.

An applied acknowledgment means the recipient has updated its brief/state and
affected worker instructions to the cited revision, not merely read the message.
Artifact acceptance is a separate parent review decision naming evidence and
scope. A successful tool send is only dispatch, not an acknowledgment.

## Publish, deliver, and consume

1. Apply `unslop` to agent-authored prose and inspect the complete artifact files.
   Preserve exact quotations, code, citations, and schema fields. Verify references exist
   and identify the state actually tested. Finalize the manifest and message in
   temporary files, then publish complete Markdown files under their final names.
   Notify only after publication; recipients ignore temporary/unpublished files.
2. Send a short native notification containing the message ID, absolute message
   path, action, and affected scope. Put bulky evidence behind artifact paths.
   Include the message ID/path in the task result so a missed notification remains
   discoverable through normal task-result collection.
3. The recipient reads the addressed message, checks run, sender, task, revision,
   active holds, and referenced artifacts. Act on each ID at most once; record it
   in the recipient-owned state. A duplicate notification may repeat the existing
   acknowledgment but must not repeat a mutation or integration.
4. A missing artifact, unexpected sender, incompatible revision, or unclear action
   produces a question/rejection and a hold on dependent work. Do not substitute
   the newest file silently. Apply relevant updates before beginning a dependent
   step and at natural task boundaries; inspect outstanding holds then too.
5. Send any required acknowledgment and a concise result. The sender/parent tracks
   pending recipients. Silence, elapsed time, and a worker's completion elsewhere
   do not establish receipt or application. Retry uncertain delivery with the same
   published ID; investigate missing acknowledgments rather than starting a resend
   loop. If the sender restarts, read its published IDs before allocating another.

Delivery is cooperative. There is no filesystem watcher or guaranteed interruption
at every edit. Use immediate native notifications for questions, holds, and contract
changes, and the runtime adapter's interruption controls when applicable. Do not
repeatedly reread unchanged directories or load every research file into every
agent. The notification and manifest select what each recipient needs.

## Result manifest and selective distribution

A Sol report lists separate artifacts. Each entry has an ID, revision, type,
location, purpose, dependency/consumer information, review state, and evidence
pointer. Research outputs retain claim-to-source references, applicable dates,
counterevidence, and uncertainty. A code summary points to actual code/diff or an
authorized commit, base/workspace state, new files, checks, and integration status.
A summary alone does not transfer implementation. Pin code evidence to an exact
commit or immutable scoped change snapshot that includes new files. For uncommitted
work, preserve the base and reviewed file/diff contents or content digests sufficient
to detect later edits; a mutable worktree path alone is insufficient. Creating a handoff does not
authorize a commit or staging unrelated user changes.

Use explicit review states such as `proposed`, `sol-reviewed`, `astra-accepted`,
or `superseded`, plus a separate implementation state (`unintegrated`/`integrated`)
when relevant. Astra records acceptance in its own decision message, referencing
the exact artifact revision; it does not edit Sol's report. An accepted research
result may still document unknowns that prevent dependent implementation.

Example: Sol A produces two studies and an implementation. Paths below are
illustrative and relative to the verified coordination directory; notifications
provide absolute paths.

```text
Message: sol-a-0007; task-a-r3; report to Astra

R1 r1 | research | artifacts/sol-a/research-lifecycle-r1.md
  Finding: lifecycle ordering; sources and counterevidence in the file.
  Consumers proposed: Sol B. State: sol-reviewed.
R2 r1 | research | artifacts/sol-a/research-storage-r1.md
  Finding: persistence constraints; evidence in the file.
  Consumers proposed: Sol C. State: sol-reviewed.
I1 r1 | implementation | artifacts/sol-a/implementation-r1.md
  Actual code: exact workspace/base/change manifest in the summary.
  Evidence: verification record tied to that change state.
  Consumers proposed: Sol B and Sol C. State: sol-reviewed, unintegrated.

Requested action: Review the findings and implementation, decide acceptance,
then distribute applicable evidence/contracts and coordinate code integration.
```

Astra checks consequential evidence and dependency effects. It may send Sol B an
update referencing R1 and I1, and Sol C one referencing R2 and I1. Each update says
why those artifacts matter and distinguishes awareness, review, contract changes,
and an integration assignment. Informational routing may precede acceptance if
clearly labeled provisional and prohibited as an implementation prerequisite.
Application requires accepted evidence/contracts and verified access to required
code. Recipients acknowledge required updates and pass only relevant changes to
their Lunas. They continue established independent work while a prerequisite is
unavailable, and hold dependent work.

When R1 is corrected, publish R1 r2 and a superseding message. Astra uses the
consumer registry to notify all affected tasks, invalidate stale acceptance or
dependent results, and obtain applied acknowledgments before dependent work
resumes. Preserve the earlier record to explain which version each task used.
