# Codex runtime

Read live tool schemas before dispatch. A skill cannot change its running model,
create unavailable tools, enforce unexposed budgets or guarantee termination.
Disclose a known model mismatch; use only an author-approved fallback.

## Planning mode

The workstream plan is part of ordinary execution; `/plan` is optional. If the
author selected Plan mode, use permitted read-only investigation to define the
goal and propose the workstream plan in chat. Defer run-directory creation,
ledger writes, helper activation and implementation dispatch until the host
transitions to execution. Then persist the settled plan and continue; do not
repeat settled questions. Follow the host's mode restrictions and never claim
to switch modes through this skill.

## Dispatch and workspace

Separate Sol tasks require an explicit author request. Use `create_thread` with
`model: "gpt-6.1-sol"`, `thinking: "high"` or `"xhigh"`; list projects first for a
project target. Otherwise use subagents. Pass the role, compact protocol brief,
pinned instruction path, authorized parent route and actual capacity.

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

Store returned task IDs/hosts. Pending `clientThreadId` is not `threadId`; resolve
creation before APIs requiring the latter and emit required creation directives.

For worker subagents use `spawn_agent`, `model: "gpt-6-luna"`,
`reasoning_effort: "xhigh"`, `fork_turns: "none"`. Sol implementation exceptions
use `gpt-6.1-sol` with high/xhigh; independent reviewers/verifiers use
`gpt-6.1-sol` with `high` and a bounded review brief, per the protocol's review gate.
The spawn message supplies the absolute
`references/worker.md` path and task-specific brief, not the whole skill.
Full-history forks inherit model/effort and cannot take overrides in this runtime.
Use `send_message` for active agents, `followup_task` for idle ones. Count live
capacity; interrupts do not prove a slot was released. Queue excess work.

## Progress and stops

Use `wait_threads` with saved cursors and bounded waits for compact task progress;
eight targets is a wait batch size, not parallel capacity. Read full task history
only for a specific missing result. Use native task messaging under the author’s
ongoing coordination authorization, including replies. Tasks are app peers;
a parent ID alone grants no messaging permission.

Sol continues its accepted assignment within the current execution. If a task
ends incomplete, Orchestrator evaluates its report and sends a scoped continuation;
a finished turn is not task acceptance. While active, Orchestrator collects meaningful
results, integrates and dispatches ready work without polling unchanged history.
Ending Orchestrator's turn does not guarantee a wakeup from child completion. Later
monitoring needs author-requested automation; files are not watchers.

Separate-task stops are cooperative when no direct interrupt exists. Send a hold;
Sol interrupts affected subagents where supported. Track external operations still
running using [uncertainty.md](uncertainty.md). Wait timeouts and task archiving
are not cancellation. Keep waits short enough to answer the author.

## Goals

Run define-goal first. Call `get_goal`; reuse a matching goal. Creating a goal or
setting its token budget requires the author's explicit request. Respect an
explicit goal-free run. Follow live lifecycle rules, including the host's blocked
threshold and author-only pause authority. A hold is not a goal-tool status.

Continue until acceptance, a real blocker, author stop or runtime/budget boundary.
Propagate a whole-goal stop to child assignments and report pending operations.
Never mark complete merely to stop, create replacement goals to bypass limits,
or manufacture work while awaiting input. Continue useful independent work, then
wait honestly. Resume held work only after its resolution; a wakeup is insufficient.
