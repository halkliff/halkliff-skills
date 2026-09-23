# Native runtime adapter

Inspect live tool schemas first. The entries below describe this Codex desktop
runtime as checked on 2026-09-22, not a promise about every client.

## Main task and separate coordinator tasks

The root model is selected by the host or user. A skill cannot switch its own
running model. If the root is not Astra High, disclose the mismatch and resolve it
with the author before executing this hierarchy, unless the author already
authorized the actual model as a fallback. Do not spawn a second nominal root
just to hide a mismatch.

When the user explicitly asks to create separate coordinator tasks, use
`mcp__codex_app__create_thread` with `model: "gpt-6-sol"` and `thinking: "high"`
or `"xhigh"`. This creates durable user-visible tasks. Skill instructions alone
do not authorize creating them. Do not create tasks for a hypothetical design
discussion or use them to evade a runtime restriction.

For repository work, call `list_projects` first. Use its project ID and default
to a worktree for a Git repository. Omit a starting ref unless the user specified
one; if work depends on an uncommitted state or a nondefault branch, resolve that
base choice before dispatch. Follow an explicit request to use the saved checkout.
For work without a repository, use a projectless task and explicit artifact paths.

Include the coordinator role, skill path, complete workstream brief, root ledger
path, communication protocol and coordination directory, root task ID/host,
contract revision, uncertainty protocol, any goal stop instruction from the
author, and permitted worker capacity in the initial prompt. Separate tasks have
separate conversations and may have separate filesystem roots. Verify access to
any shared brief rather than assuming a relative path exists in both workspaces.

Creation is asynchronous. Store returned `threadId` and `hostId`. A pending
`clientThreadId` is not usable with APIs requiring `threadId`; resolve the created
task using the current app tools before sending messages or waiting on it.
Emit the required created-task directive in the user-facing final response after
actual creation, using the tool-returned identifier.

Use `wait_threads` for compact progress or completion, with up to eight targets
per call and each target's last cursor. Eight is a wait-call batch size, not a
parallel-task limit. Use bounded waits that preserve user responsiveness.
Use `read_thread` only when a result needs deeper inspection and
`send_message_to_thread` for a scoped correction or contract change. Preserve
the chosen model/effort on follow-ups unless a deliberate change is warranted.

These tasks are peers in the app. Astra is their coordinator by workflow, not a
special parent runtime. It must collect outcomes and resolve integration. Ending
the Astra turn is not a guarantee that it wakes when a Sol task finishes. For
later monitoring, use the automation capability only when the user requests it.
Do not treat archiving as cancellation; use available lifecycle controls and
verify child activity when stopping work.

For an escalation from a Sol task, send the root a structured `needs-decision`
message using `send_message_to_thread` and put the same question in the task result
and ledger. This follow-up can trigger a root turn; the message must identify any
affected hold and forbid treating the wakeup as permission to resume held work.
If immediate messaging is unavailable, record the question for Astra's next
`wait_threads` result. Do not claim delivery until a tool confirms it.

The tools inspected here do not expose a direct interrupt for a separate task.
Send stop instructions to Sol through task messaging; each Sol can interrupt its
own Luna agents. Delivery and acknowledgment are cooperative, not an atomic stop.
Track pending acknowledgments and any already-running operations. The author has
accepted cooperative stops with acknowledgment tracking and permits unrelated
work with established independence to continue. Do not ask for that approval
again. Apply the dependency hold rules in [uncertainty.md](uncertainty.md).

Use [communication.md](communication.md) for the durable record. Native messages
carry its ID, absolute path, requested action, and affected scope. Within a local
subagent tree use `send_message` for an active recipient and `followup_task` for
an idle recipient when a turn is needed. Across Sol tasks use
`send_message_to_thread`. Verify actual receipt/application through acknowledgments;
a successful send alone does not establish either. A Markdown file or folder
does not create a watcher or wake up an idle agent by itself.

## Luna workers within a Sol task

With `collaboration.spawn_agent`, set both `model` and `reasoning_effort` explicitly:

```json
{
  "task_name": "coordinate_feature",
  "model": "gpt-6-sol",
  "reasoning_effort": "high",
  "fork_turns": "none",
  "message": "ROLE: coordinator. Read the supplied skill path and task brief. Own the assigned workstream. You have the explicitly allocated worker slots. Spawn bounded Luna workers only while doing useful independent coordination or review. Return acceptance evidence."
}
```

This is a shape example; replace the message with the actual outcome, absolute
paths, permissions, and acceptance criteria before dispatch. Coordinators spawn
workers with `model: "gpt-6-luna"`, `reasoning_effort: "max"`, and
`fork_turns: "none"`, supplying the complete bounded brief.

Full-history forks (`all`, including the default) inherit the parent model and
effort and cannot accept overrides in this runtime. A positive bounded turn
count also permits overrides, but use it only when the selected history is useful.

Use `send_message` for steering an active agent and `followup_task` to resume an
idle one. Both preserve its context. Observe `list_agents` when capacity or
lifecycle state is uncertain. An interrupt is not a close operation and does not
prove a slot was released. Count available slots from current runtime evidence;
reuse an appropriate idle agent or queue work when no slot is available.

If nested spawning is unavailable, propose having the root dispatch Luna workers
and route results to Sol for review. Use this flat execution tree only when the
author has authorized it. If requested models are unavailable, escalate the
mismatch and use only an explicitly permitted fallback; never claim the preferred
hierarchy ran.

Use subagents for bounded work inside each coordinator task. In the fallback
single-task topology, Astra spawns Sol subagents using the shape above instead
of separate tasks. Avoid forking the entire main conversation by default.

This skill provides behavioral routing, not a hard scheduler, token budget, or
filesystem sandbox. Enforced budgets and file isolation require runtime support.
Keep inherited authorization boundaries and make read-only assignments explicit.
Recheck tool support before adding custom agent TOML or editing global settings;
the currently exposed spawn API is sufficient for this workflow.

Official background: [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Build skills](https://learn.chatgpt.com/docs/build-skills).
