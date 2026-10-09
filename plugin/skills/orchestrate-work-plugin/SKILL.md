---
name: orchestrate-work-plugin
description: Explicitly invoked adapter for the bundled orchestrate-work workflow and its session-activated local helpers.
---

# Orchestrate work with local helpers

Use only on the author's explicit invocation, including bounded assignments within
that run. The bundled `orchestrate-work` owns the workflow. Resolve the plugin root
from this file's location.

In host Plan mode, first read the bundled core's `references/runtime.md#planning-mode`
and `references/protocol.md#workstream-plan` (the pinned copies for an existing run).
Settle missing review preferences through `references/protocol.md#review-gate`.
Propose the plan in chat; defer setup until the host transitions to execution.

1. Resolve the author checkout and coordination root through **Current state** in
   `<plugin-root>/support/skills/orchestrate-work/references/protocol.md`. For an
   existing run, use its pinned protocol, recorded root, returned CLI and
   `--run-id <existing-id>`. Create and verify the root before activation; record it
   during goal definition.
2. For helpers, use the host event's canonical `session_id` when available.
   `CODEX_THREAD_ID` can supply an explicit candidate; its hook coverage remains
   unobserved until a matching real event arrives. If neither is available,
   report the capability gap. Run:

   ```text
   python <plugin-root>/scripts/orchestration.py activate --session <explicit-id> --coord-root <absolute-root> --author-repo <absolute-checkout> --plugin-data <absolute-data-root>
   ```

   The host's `PLUGIN_DATA` may supply the data root. Use the returned absolute
   `cli`, `core`, `worker` and `support` paths. Read `core` and its role-required
   references; use `<returned-support>/define-goal/SKILL.md` for goal setup. Follow
   the core's workstream plan, dispatch checks and review gate, including its
   one-time setup question for missing preferences and mandatory requirements.
3. Load supporting skills beneath `support` by absolute path when core calls for
   them, including the completion handoff and optional author-requested `correct`.
   Give leaves only `worker` and a sufficient brief. Explicitly enroll delegated
   coordinator sessions against the existing run when needed.
4. Use the returned CLI's `--help` for mechanical commands. `status --session
   <id>` diagnoses membership. `deactivate --session <id>` revokes that binding;
   `deactivate --run-id <id>` revokes the run's bindings. Continue task holds,
   review, integration, and acceptance through the pinned core instructions.

Installation and activation need separate evidence. Claim hook coverage only for
events observed on this host. Counters do not establish capacity, cost or completion.
Snapshot paths stay pinned until explicit migration through core's hold/resume protocol.
