# Codex runtime

Read live tool schemas before dispatch. A skill cannot change its running model,
create unavailable tools, enforce unexposed budgets or guarantee termination.
Disclose a known model mismatch; use only an author-approved fallback.

## Model routing

Use the following starting choices for new runs. The author's confirmed selection
in the host model/effort selector controls main-chat execution.

| Role | Model and effort | When |
| --- | --- | --- |
| Main Orchestrator | GPT-6.2 Astra / High (`gpt-6.2-astra`, `high`) or GPT-6.2 Sol / xHigh (`gpt-6.2-sol`, `xhigh`) | Author selects the active pair |
| Coordinator | GPT-6.2 Sol / High (`gpt-6.2-sol`, `high`) | Use xHigh for difficult coordination when selected |
| Worker | GPT-6 Luna / xHigh (`gpt-6-luna`, `xhigh`) | Research, claim checks, summaries, implementation, tests and documentation |
| Complex implementation worker | GPT-6.2 Sol / High or xHigh | Bounded implementation requiring that route. Record the reason in the brief |
| Independent reviewer or verifier | GPT-6.2 Sol / High | Follow the existing review gate |

Resolve each assignment against the settled role default and the latest applicable
explicit author choice for its workstream, purpose or chat. A scoped choice applies
only to matching work. Copy the resolved request and decision pointer into the brief.
In a policy-controlled run, encode guarded routes using scoped role IDs and
the authorized grants in [controls.md](controls.md). Set actual tool parameters.

For example, Data can use GPT-6.2 Sol/High as coordinator, GPT-6.1 Terra/High
for implementation, GPT-6 Luna/xHigh for summarization and GPT-6 Luna/Low for
simple bulk work. The Data coordinator assigns all three purposes from the same
task chat. Another workstream without a worker override keeps GPT-6 Luna/xHigh,
including for implementation. Ownership and escalation stay with the assigned parents.

Full-history subagent forks inherit model/effort. Explicit role routing requires
`fork_turns: "none"`. App-created chats need their own readback. Selected-policy
subagent guards apply only to supported hook events.

Compare requested and effective execution model/effort where exposed before
releasing child implementation. Record host readback as the observation and mark
unavailable fields unverified. Source-chat settings and instruction provenance
describe inputs. On mismatch, unsupported identifier or dispatch failure, hold
affected work and resolve an authorized route supported by the host and active hook.

Ordinary `send_message_to_thread` continuations omit `model` and `thinking` to
preserve current author-selected chat settings. For an author-approved change,
record the new scoped choice prospectively and update the chat's roster row with
the request and fresh readback. Recover in the same chat when possible, preserving
source and worker ownership. Keep live writers on their existing assignments.

## Guarded operations

When selecting a policy-controlled plugin run, use [controls.md](controls.md) for
the canonical inputs, dispatch marker and checked adapter command. Use the pinned
CLI's actual capabilities; an older pin or an unbound chat has not acquired new
guards. Keep unsupported execution paths and unobserved hook delivery explicit.

## Planning mode

The workstream plan is part of ordinary execution; `/plan` is optional. If the
author selected Plan mode, use permitted read-only investigation to define the
goal and propose the workstream plan in chat. When the host permits, use bounded
read-only workers on the applicable research route or worker default. Return
findings natively without run artifacts. Defer
run-directory creation, ledger writes, goal mutations, helper activation,
user-owned coordinator task-thread creation and implementation dispatch
until the host transitions to execution. Then persist the settled plan and continue; do not
repeat settled questions. Follow the host's mode restrictions and never claim
to switch modes through this skill. If research delegation is unavailable, disclose
the gap and resolve the route with the author before a larger investigation;
the trivial-lookup exception still applies.

## Dispatch and workspace

Treat explicit invocation as a request for substantial parallel orchestration.
Orchestrator chooses coordinator placement and useful concurrency from independent
workstreams, dependencies and verified runtime capacity. Use separate coordinator
task chats for substantial autonomous workstreams, with worker subagents. For
light or tightly coupled work, use subagents alone. Queue
work that exceeds capacity. Record the choice in the existing plan; no placement
confirmation is required. An explicit author override takes precedence.

Task-thread creation and scoped coordination are part of the requested workflow;
there is no separate task-creation setup question. Suggested invocation prompts
explicitly request those actions when submitted. Carry the actual human invocation,
its authorization and the
placement choice into launch briefs, covering assignments, questions, replies and
scoped continuations. A stored default prompt grants no permission until sent by
the author. Pass the role, compact contract, pinned instructions, actual parent
route and capacity. Follow the host's creation/messaging schemas: ordinary work
requests or stored instructions alone do not authorize user-owned chats. Resolve
an unavailable or host-disallowed route before dispatch; the workflow cannot
override that boundary.

When work merits a separate coordinator chat, use the applicable chat or
workstream coordinator override. Otherwise use the agreed run coordinator pair,
including an approved coordinator default. A pair that matches the main chat or
host default still requires a separate coordinator selection. Use
`create_thread` with both `model` and `thinking` set to the resolved pair. Route
through creation, since `fork_thread` exposes neither setting. Hold affected work
if the route is unsettled, unsupported or mismatched. List projects first for a
project target. Use coordinator subagents when Orchestrator selects that placement
or the author overrides it. Workers and leaf reviewers/verifiers remain subagents.

The task schema has no arbitrary checkout-path field. For isolated clones, a
projectless task can run commands with the clone's absolute `workdir`; verify
`git rev-parse --show-toplevel` and a bounded write/read in its owned workspace
before dispatching implementation. Respect filesystem permissions; a prompt does
not rebind the UI checkout or grant access. If this fails, resolve access with
the host/author instead of editing the author's checkout.

Tested 2026-09-27: a projectless GPT-6 Sol High task successfully read/wrote a separate
local clone outside its default task directory through explicit `workdir`.
Its profile was unrestricted, approval policy never. This verifies that route
on this host, not sandboxed profiles or automatic clone registration. The probe
created one untracked file and changed no branch/commit. Each deployment needs
its own access check; repository-wide clones follow [git.md](git.md).

Store returned task IDs and hosts in the [task-chat roster](protocol.md#task-chat-roster).
A queued `clientThreadId` stays pending until the host returns the real `threadId`.
Resolve it before APIs that require a `threadId` and emit required creation directives.

For all role subagents use `spawn_agent` with the resolved `model`,
`reasoning_effort` and `fork_turns: "none"`. Give leaf subagents the absolute
`references/worker.md` path and a bounded brief. Give coordinator subagents the
pinned skill entrypoint and their workstream brief.
Use `send_message` for active agents, `followup_task` for idle ones. Count live
capacity; interrupts do not prove a slot was released. Queue excess work.

## Progress and stops

Use `wait_threads` with saved cursors and bounded waits for compact task progress;
eight targets is a wait batch size, not parallel capacity. Read full task history
only for a specific missing result. Use native task messaging under the author’s
ongoing coordination authorization, including replies. Tasks are app peers;
a parent ID alone grants no messaging permission.

Orchestrator-assigned subagents may contact coordinator task chats named in their
brief for findings and factual clarifications. Use `send_message_to_thread` with the
thread ID/host and the run's human authorization. Include task/revision and a
topic label, concise evidence and the requested clarification. The coordinator answers
in its own chat. The worker retrieves the reply with a targeted `read_thread` or a
bounded `wait_threads` for a completed response. These are visible thread messages,
not private cross-tree subagent delivery. Do not poll unchanged history. Report an
unresolved prerequisite to the assigning parent instead of waiting indefinitely.
Decisions, consequential uncertainty, holds and acceptance stay with that parent.
Return conclusions/pointers to it without relaying every exchange.

The coordinator continues its accepted assignment within the current execution.
If a task ends incomplete, Orchestrator evaluates its report and sends a scoped continuation;
a finished turn is not task acceptance. While active, Orchestrator collects meaningful
results, integrates and dispatches ready work without polling unchanged history.
Ending Orchestrator's turn does not guarantee a wakeup from child completion. Later
monitoring needs author-requested automation; files are not watchers.

Separate-task stops are cooperative when no direct interrupt exists. Send a hold;
The coordinator interrupts affected subagents where supported. Use
[uncertainty.md](uncertainty.md) to track running operations. Wait timeouts and task archiving
are not cancellation. Keep waits short enough to answer the author.

## Goals

For each new run, explicitly confirm live-goal versus goal-free execution before
activation or implementation. Recommend goal-backed execution, defined with
`define-goal`. Reuse an explicit choice already supplied for this run; otherwise
ask once in the setup proposal and wait. General approval of other setup details
or invocation alone does not settle goal mode. Continuing a confirmed run reuses
its mode.

After [setup confirmation](protocol.md#setup), for live-goal execution call
`get_goal`; reuse an authorized matching active
goal, or use `define-goal` to create one only on the author's explicit request.
Confirm active state through the live goal tool before dispatch. Resolve
unavailable tools, failed activation or conflicting state before implementation;
never silently fall back to goal-free execution. Include a token budget only
when explicitly requested. Follow planning-mode restrictions above.

Record the chosen mode and confirmed live state, when applicable, in the existing
plan; a written objective alone is not activation.

Follow live lifecycle rules, including the host's blocked threshold and
author-only pause authority. A hold is not a goal-tool status.

Continue until acceptance, a real blocker, author stop or runtime/budget boundary.
Propagate a whole-goal stop to child assignments and report pending operations.
Never mark complete merely to stop, create replacement goals to bypass limits,
or manufacture work while awaiting input. Continue useful independent work, then
wait honestly. Resume held work only after its resolution; a wakeup is insufficient.
