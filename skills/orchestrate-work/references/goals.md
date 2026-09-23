# Top-level goal lifecycle

## Definition gate before orchestration

Astra owns the goal. Read and execute `define-goal` as the required entry step
for substantive orchestration. Reuse its definition workflow rather than copying
or replacing it in each role. Before assigning implementation, establish an
explicit outcome, scope, requirement IDs, evidence required for each, and the
uncertainty stop rule. Resolve missing requirements through the author rather
than supplying assumed success criteria. Definition may use bounded inspection
or explicitly scoped research to establish a fact; it does not authorize work
under the still-undefined objective.

The gate is satisfied when every requirement has an authoritative basis and a
verifiable completion criterion, known definition questions are resolved, and
the user has requested goal-backed execution so a matching goal can be reused
or created. Do not require a separate ritual approval when the user's request
already supplies those facts. If execution is requested but goal creation is
not authorized, present the concrete objective and ask that missing question
before launch. Merely discussing or editing this skill creates no goal. An
explicit user instruction to work without goals overrides the default workflow.

## Create or reuse the authorized goal

Call `get_goal` before `create_goal`. Reuse an existing matching goal. If an
unfinished goal conflicts, ask the user; do not overwrite or falsely complete it.
Create only on an explicit request to start a goal, not when discussing support
for goals. Set `token_budget` only when the user explicitly requests one.

Keep the objective concise and verifiable, referencing the accepted requirements
artifact when needed. The orchestration ledger, not the goal definition skill,
owns ongoing task state, decision records, and evidence. Include the required
final verification and stop-on-unresolved-uncertainty condition in the objective.
For goal-backed execution, each Sol brief names the accepted goal objective/record
and the requirement IDs it serves. In explicitly goal-free work, reference the
accepted task objective and contract requirements without inventing a goal record.
Sol's Luna briefs preserve the applicable mapping. Refinement that changes the
outcome, scope, or acceptance criteria returns to Astra and `define-goal`; do not
silently reinterpret an active goal. Use only lifecycle operations supported by
the current goal tools when reconciling a changed objective.

## Pursue and accept

Astra repeatedly dispatches ready work, collects Sol results, verifies acceptance,
integrates compatible changes, and checks remaining requirements. Milestone
completion and a child's final response do not establish goal completion.
For each requirement track its contract revision, artifact state, verification
result, and accepting role. A goal is complete only when all required work and
final integration checks pass with current evidence and no unresolved question.
Do not weaken a requirement to make completion possible.

On continuation, inspect `get_goal`, the root ledger, holds, questions, and child
task status before dispatch. A runtime continuation or automation must respect an
existing hold. It is not authority to resume held work pending an author decision.
Continue established independent assignments while a question is pending. Ask
the author promptly, using the available in-turn input channel when useful, rather
than waiting until unrelated work finishes. The open question still prevents goal
completion.

## Execution holds versus tool status

The ledger's per-question `awaiting-author` state is separate from the goal tool's
statuses. A dependency hold does not pause the entire goal while independent work
remains. Keep the goal active and coordinate that work under the uncertainty rules.
Read current tool instructions before changing lifecycle state:

- `complete`: Only when the full objective has been achieved. If a token budget
  was set, report final usage from the tool result as required.
- `paused`: Requires an explicit user instruction to pause this particular goal.
  A generic skill stop rule is not enough. If the user explicitly instructed this
  goal to pause upon an unresolved escalation, preserve that instruction in the
  root brief and call the tool when the condition occurs. Otherwise maintain the
  execution hold and ask for the decision; ask for a goal pause only if needed
  when the whole goal must wait. Do not misrepresent the tool status as paused.
- `blocked`: Under the currently available tool, requires the same external or
  input dependency to recur for at least three consecutive goal turns with no
  meaningful progress possible. Do not mark blocked immediately just because
  the ledger is awaiting an answer. Once that threshold genuinely occurs, set
  blocked rather than leave an active goal repeatedly reporting the same impasse.
  Do not manufacture turns to reach the threshold. After a user resumes a blocked
  goal, begin a fresh three-turn blocked audit, as the current tool requires.

At an uncertainty stop, initiate the scoped stop protocol and ask the author.
Record paused only on an explicit goal-level pause request under the tool's rules;
first initiate stop requests for all goal assignments and report any pending
acknowledgments. A goal-level pause ends all goal work, including otherwise
independent assignments. Without
such a request, continue established independent work, or maintain the full
execution hold if none remains. Budget limits take precedence. State the actual
status. Never mark complete merely to stop automatic continuation.

An explicit user request to resume revokes their pause. The current `update_goal`
tool has no resume status; use the host's supported user-controlled resume flow
and verify the resulting status. Record the answer and revised contract before
restarting children. A clarifying answer resolves the question; verify lifecycle
state rather than assuming the host also resumed a paused goal.

## Persistence limits

A goal expresses continued pursuit; it does not guarantee indefinite availability,
unlimited budget, automatic recovery after app shutdown, or an atomic stop across
tasks. Respect actual limits and preserve enough state to continue honestly.
Scheduled later checks require the user's scheduling/monitoring request and the
automation tool. Do not create duplicate goals or child automations to bypass a
hold, exhaustion, or missing author decision.
