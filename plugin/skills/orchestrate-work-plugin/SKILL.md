---
name: orchestrate-work-plugin
description: Explicitly invoked adapter for the bundled orchestrate-work workflow and its session-activated local helpers.
---

# Orchestrate work with local helpers

Use this adapter only on the author's explicit invocation, including bounded
assignments within that run. The bundled `orchestrate-work` remains the workflow
authority. Resolve the plugin root from this file's location and use its bundled
instructions directly.

1. Resolve the author checkout and coordination root using the **Current state**
   rule in `<plugin-root>/support/skills/orchestrate-work/references/protocol.md`.
   When joining an existing run, use its pinned protocol and recorded root, returned
   CLI, and `--run-id <existing-id>`; preserve its pinned instructions. Create and
   verify the chosen directory before activation; record it during goal definition.
2. For helpers, use the host event's canonical `session_id` when available.
   `CODEX_THREAD_ID` can supply an explicit candidate; its hook coverage remains
   unobserved until a matching real event arrives. If neither is available,
   report the capability gap. Run:

   ```text
   python <plugin-root>/scripts/orchestration.py activate --session <explicit-id> --coord-root <absolute-root> --author-repo <absolute-checkout> --plugin-data <absolute-data-root>
   ```

   `PLUGIN_DATA` can supply the data root when the host provides it. Use the
   returned absolute `cli`, `core`, `worker`, and `support` paths for this run.
   Read the returned `core` entrypoint and references required for your role.
   Load `define-goal` from `<returned-support>/define-goal/SKILL.md` to establish
   the authorized outcome and acceptance evidence before dispatch or implementation.
3. Load supporting skills by absolute path beneath the returned `support` root
   when the core workflow calls for them, including its completion handoff and
   optional, author-requested `correct` session. Pass leaf workers only the returned
   `worker` guide and a sufficient task brief. Explicitly enroll a delegated
   coordinator session against the existing run when the authorized run needs one.
4. Use the returned CLI's `--help` for mechanical commands. `status --session
   <id>` diagnoses membership. `deactivate --session <id>` revokes that binding;
   `deactivate --run-id <id>` revokes the run's bindings. Continue task holds,
   review, integration, and acceptance through the pinned core instructions.

Installation and activation have separate evidence. Claim host hook coverage
only for events observed on the current host. Runtime counters describe observed
events; they do not establish live capacity, cost, or completion. Snapshot paths
remain pinned until an explicit migration through the core hold/resume protocol.
