# Local orchestration plugin

The plugin packages the existing `orchestrate-work` workflow as one explicit
entrypoint. Its bundled dependencies live under `support/skills/`; they are
resources loaded by that workflow and do not add more discoverable skills.
The standalone skill installation remains available separately.

## Build offline

From the repository root, run:

```powershell
python scripts/build_plugin.py --dest work/plugin-package/halkliff-orchestration-0.1.2
```

To validate sources and destination safety without writing the package, add
`--dry-run`. The builder reads the exact selected files from `dependencies.json`
and stores each upstream file from the manifest-pinned Git commit. It does not
fetch, change submodule checkouts, run setup scripts, or install anything.

The result is self-contained. `build-info.json` records the repository revision,
upstream pins, SHA-256 for every package file except itself, and a package
fingerprint derived from the sorted hash map. An identical destination is safe
to rebuild. A conflicting destination is left untouched; choose a fresh output
directory when package inputs change.

The repository's local marketplace entry points to
`work/plugin-package/halkliff-orchestration`. Build first, then install that
local marketplace plugin through Codex. Plugin installation and hook trust are
separate host actions; building or installing alone does not establish that
hooks are trusted or that the host has delivered events to them.

After building the default destination, register this repository and install
its available local plugin:

```powershell
codex plugin marketplace add "<repository-root>" --json
codex plugin list --marketplace halkliff-local --available --json
codex plugin add halkliff-orchestration@halkliff-local --json
```

Use the absolute repository root for `<repository-root>`. On 2026-09-30, Codex
CLI 0.159 accepted the portable root `plugin.json`, discovered the marketplace
entry, and installed version 0.1.0. No compatibility overlay was required.
The assembled package contained 90 files and 13 support skills. Its pinned
coordinator enrollment, simulated dispatch guard, 772-byte recovery output,
and refusal to register the author checkout passed package checks.

Live desktop hook coverage remains unverified by those checks. Complete the
host's hook trust review and any required reload, then observe a real event for
an explicitly activated session before reporting live coverage.

For an update, build into a fresh directory beneath `work/`, then change that
plugin's `source.path` in `.agents/plugins/marketplace.json` to the new
repository-relative directory before reloading or reinstalling it through
Codex. Updating the package or marketplace leaves active runtime snapshots pinned.

## Invoke and activate explicitly

Invoke `$orchestrate-work-plugin` when you want this workflow. The plugin does
not infer orchestration intent or start a run by itself. Before helpers can use
the pinned workflow, explicitly activate the real host session with the absolute
coordination root, author checkout, and chosen plugin data directory:

During goal definition, record one absolute coordination root. For new runs, use
`<author-repository-root>/.orchestration/<run-name>/` unless the author chooses
another location. Reuse the recorded root on continuation and pass that exact
path to every participant. Create the directory before activation, outside agent
clones and excluded from code delivery. The core
[protocol](../skills/orchestrate-work/references/protocol.md#current-state) owns
this convention. Task records and evidence live there; plugin runtime data stays
in its separate data root.

```text
python "<plugin-root>/scripts/orchestration.py" activate --session "<session_id>" --coord-root "<absolute-path>" --author-repo "<absolute-path>" --plugin-data "<absolute-path>"
```

Use a dedicated data root outside the author checkout and coordination root.
The recommended location is `<user-home>/.codex/orchestration-plugin/data`,
resolved to an absolute path and supplied through `--plugin-data`. It keeps
session bindings and retained runtime snapshots together across shell commands.

Use the exact `session_id` from a real host hook event when available. A
`CODEX_THREAD_ID` value is only a candidate; do not treat it as observed hook
coverage until a matching event arrives. The activation result returns the
selected run ID, package fingerprint, plugin data path, pinned CLI, core
instructions, worker guide, and support-skill directory. Use those returned
paths for the run.

To join an existing run, activate another session with its existing run ID and
the same coordination root, author checkout, and plugin data path:

```text
python "<pinned-cli>" activate --session "<coordinator-session-id>" --run-id "<existing-run-id>" --coord-root "<absolute-path>" --author-repo "<absolute-path>" --plugin-data "<absolute-path>"
```

Omit `--run-id` to start a new run. A run keeps the package snapshot selected
at activation. Follow the core workflow's hold/resume protocol at an
author-chosen migration boundary before deactivating and enrolling sessions
against a new package. Preserve current work, evidence, and unresolved holds.

## Inspect and deactivate

The CLI supports `status --session <id>`, `status --run-id <id>`,
`deactivate --session <id>`, and `deactivate --run-id <id>`. Deactivation
removes the corresponding active bindings and keeps content-addressed runtime
snapshots. The local locator maps an explicitly activated session ID to the
selected data root, so session status and deactivation can resolve it without
scanning the working directory. Set `ORCHESTRATE_WORK_LOCATOR` only for an
isolated test or an intentionally separate locator file.

Deactivation revokes helper bindings. Worker stops and external operations
still follow the core workflow's hold protocol.

Ordinary shell processes may not inherit the hook's `PLUGIN_DATA` setting.
Supply `--plugin-data <absolute-path>` to direct commands when needed; the
activation result includes the chosen path. The default user locator is
`<CODEX_HOME>/orchestration-plugin/locator.json` when `CODEX_HOME` is set, or
`~/.codex/orchestration-plugin/locator.json` otherwise.

## Observed events

Status reports `session_observed`, `observed_events`, `guard_denials`,
`observation_incomplete`, and the deduplication window size. `session_observed`
means the runtime received an event for that registered session. Record whether
the event came from the real host when reporting live coverage.

Counters cover events with stable IDs that the runtime received. Missing or
oversized IDs leave the observation incomplete. Recent duplicate IDs are
deduplicated in a bounded window; duplicates outside that window may count
again. These observations do not establish live worker capacity, tokens, cost,
or task completion.

## Retirement preflight

Register an isolated workspace explicitly with the pinned CLI:

```text
python "<pinned-cli>" workspace-register --session "<id>" --path "<absolute-workspace>" --kind <worker-or-integration> --base-commit <full-commit-id>
```

When integration and retained evidence justify release, the orchestrator writes
one release statement and references it with `workspace-release --session <id>
--path <absolute-workspace> --attestation <absolute-json-file>`. The statement
contains absolute `integration_result`, `evidence` paths, and `retained_repo`;
full `base_ref` and `result_ref`; the `result_commit`; and the attested booleans
`delivery_resolved`, `operations_clear`, and `reports_resolved`. These pointers
refer to the core workflow's authoritative result and evidence. Retain the
integration result and evidence outside the retiring workspace.

For an integration workspace, also provide either `author_commit` with `repo`,
`commit`, and `delivery_association_attested: true`, or an
`early_retirement_author_ref` pointing to an existing author decision document.
The helper checks commit and reference existence; the release statement attests
delivery association and reported operation status.

Run `workspace-preflight --session <id> --path <absolute-workspace>` before the
assigned owner's cleanup operation. The result is `retain` with reasons or
`ready`. It checks the exact registered path, retained references and evidence,
reported active use, and uncommitted or ignored files. It does not stop
processes or delete or archive the workspace. Core acceptance and the owner's
cleanup authority still govern retirement.

The retained repository's Git common directory and object directory must also
be outside the retiring workspace. A repository with nonempty object alternates
returns `retain` because the helper cannot prove independent object retention.
The helper does not repack, copy, or repair Git objects.

## Current hook behavior and evidence

The installed hook bootstrap is read-only until an exact active session binding
is found. It then verifies the pinned package before routing to the pinned CLI.
For supported local `spawn_agent` and `Agent` events it requires explicit
Luna/xHigh or GPT-6.1 Sol/High or xHigh, and denies omitted or full-history forks.
Separate-chat dispatches remain a core workflow responsibility. Resume and
compact session starts can receive a recovery pointer whose complete hook
output stays within 1 KiB. Inactive or unrelated sessions receive no injected
context and cause no state writes.

Only observed real host events establish that this host delivered the corresponding
hook. Installation does not prove trust review, desktop interception, or live
workflow behavior. Report those separately from source tests, package build,
marketplace discovery, and installation results. The wrapper and core workflow
remain responsible for explicit invocation, work authorization, holds, review,
and acceptance; hooks do not replace those decisions.

See the [Codex plugin build documentation](https://developers.openai.com/plugins/build/plugins)
and [Codex hooks documentation](https://learn.chatgpt.com/docs/hooks) for the
host-managed plugin and hook lifecycle.

## Completion resources in version 0.1.2

The package includes the refreshed pinned pstack and Matt Pocock dependencies,
`benchmark-checklist`, `handoff`, and `correct`. The core protocol owns completion:
one handoff under the recorded coordination root, then goal completion and an
optional `/correct` offer. These support resources are loaded only when needed;
the plugin still exposes one explicit orchestration entrypoint. Publishing this
update does not migrate active runs or execute a correction session.
