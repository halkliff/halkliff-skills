# halkliff-skills

Personal Codex skills, including `orchestrate-work` and the dependencies it uses.
The workflow defines a goal, coordinates an orchestrator, Sol workstreams and Luna workers, uses native task messages and versioned work products, and escalates consequential
uncertainty to the author. It runs only
when explicitly invoked.

Original work is [MIT licensed](LICENSE). Upstream adaptations retain their
notices, and `define-goal` retains its supplied Apache-2.0 license.

The upstream [pstack skills](https://github.com/cursor/plugins/tree/main/pstack)
and [Matt Pocock skills](https://github.com/mattpocock/skills) are Git submodules.
Their revisions are pinned. The installer combines selected upstream files with
reviewed Codex adaptations; it does not install either entire plugin or run their
setup scripts.

## Install

Requirements: Git and Python 3.10 or later. Run from a Git checkout of this
repository, not a source archive that omits the submodules and Git metadata.

```sh
git clone --recurse-submodules <repository-url> halkliff-skills
cd halkliff-skills
python scripts/install.py
```

Replace `<repository-url>` with the location where this repository is hosted.
A plain Git clone also works: the installer initializes missing submodules at
their pinned revisions. It does not advance them to the latest upstream commit.

The destination is `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME`
is unset. You can inspect the plan or choose an isolated destination:

```sh
python scripts/install.py --dry-run
python scripts/install.py --dest ./work/installed-skills
python scripts/install.py --offline --dest ./work/installed-skills
```

Dry-run performs no installation or download. If dependencies are missing, it
reports what must be initialized. Offline mode requires them to be present.
Existing identical skills are skipped. A different existing skill stops the
installation before any skill is changed. There is no force-overwrite option;
compare or back up an existing customization before choosing to replace it.

To ask an agent to do the installation, give it this repository and say:

> Install orchestrate-work and its dependencies from this repository. Follow its
> README and use the bundled installer. Preserve existing customized skills and
> report any conflicts.

The installer is the dependency entry point. Copying only the `orchestrate-work`
folder through a generic single-skill downloader does not install its dependencies.
`AGENTS.md` directs installation agents to the same procedure.

## Local plugin

Build the local plugin with its selected dependency resources:

```sh
python scripts/build_plugin.py --dest work/plugin-package/halkliff-orchestration-0.1.2
```

The plugin exposes `$orchestrate-work-plugin`, a small adapter to the existing
workflow. Its dependency instructions are bundled as resources and loaded by
path. Your standalone skills remain available under their existing names.

Explicitly activated runs use pinned runtime snapshots, dispatch checks,
compact recovery context, observed event counters and checkout retirement
preflight. The existing skill retains goal definition, coordination, holds and
acceptance. Retirement preflight reports whether a checkout can be retired;
cleanup remains its owner's action.

Follow the [plugin setup and verification guide](docs/orchestration-plugin.md)
for local marketplace installation, session registration and hook trust.
Installation, hook trust and observed desktop interception are separate checks.

## Use

Invoke `$orchestrate-work` with the work you want to pursue. It starts through
`define-goal`, requires `unslop` for author-facing prose and deliverables, and follows the communication
and uncertainty rules in the [skill](skills/orchestrate-work/SKILL.md).

Before invoking, select GPT-6 Astra High or GPT-6.1 Sol xHigh for the main
orchestrator in the model selector. Sol coordinators and complex implementation
workers use GPT-6.1 Sol High/xHigh.

Execution is Luna-first: research, claim checks and summaries use Luna xHigh,
including research assigned directly by the orchestrator. Parents may resolve a trivial lookup
with one known file read or targeted read-only command; larger investigations remain
delegated. Autonomous GPT-6.1 Sol High/xHigh
coordinators decompose work, dispatch workers and verify until their assignment
is complete or held. They normally use Luna xHigh for implementation and may use
a GPT-6.1 Sol High/xHigh leaf worker when complexity warrants it. Full worker slots mean
queueing work. Model effort does not guarantee termination.

Reversible internal decisions stay with the responsible agent. Questions about
public behavior, scope, compatibility, security, irreversible actions or conflicting
requirements escalate. Native messages carry routine coordination; only holds
require explicit ACKs. Current-state ledgers stay compact. The orchestrator chooses
shared main-checkout work or isolated clones/worktrees for each phase; the author's
choice prevails. Shared workers have explicit nonoverlapping scopes. Agents commit
in owned isolated checkouts and leave main-checkout changes uncommitted. The author
owns commits, branches and pushes there. Coordinators report completed isolated
work; the orchestrator confirms integration and releases checkouts for cleanup
once no further work needs them.

Workflow revision 2 is a repository update. Existing installations and live runs
are not migrated automatically. See the [revision and rollout notes](docs/orchestration-v2.md)
before adopting it in an existing run. Workers load a compact worker guide and
their brief. Packaged Git helpers handle dirty baseline capture and scoped delivery;
run their `--help` through the skill's Git reference.

See the [workflow diagrams](docs/orchestrate-work.md) for the goal loop,
uncertainty escalation, and artifact handoffs. The editable Mermaid blocks render
directly in GitHub's Markdown preview.

The orchestration runtime targets Codex: it needs the model, goal, task, and
subagent capabilities described in its runtime reference. Installing Markdown
does not grant unavailable tools or models. Other agent runtimes need a reviewed
runtime adapter before executing this hierarchy.

`orchestrate-work` has `policy.allow_implicit_invocation: false`. Its dependencies
retain their own invocation policies; `unslop` remains an always-applied prose
skill. If the running client has not refreshed its skill inventory, reload it.

## Completion

Accepted runs end with one `<coord-root>/handoff.md`, linked to the existing
evidence and delivered changes. After completing the goal, the Orchestrator asks
whether you want an optional `/correct` session. Declining leaves the goal complete;
accepting authorizes only the correction scope you choose. Skill/plugin improvements
remain proposals until you request their implementation. Existing runs keep their
pinned instructions until you explicitly migrate them.

## Included skills

| Source | Selected skills |
| --- | --- |
| This collection | `orchestrate-work`, `define-goal` |
| pstack, adapted for Codex | `pstack-principles`, `unslop`, `how`, `why`, `blast-radius`, `no-comments`, `benchmark-checklist`, `correct` |
| Matt Pocock, with selected compatibility adaptations | `grilling`, `writing-for-agents`, `domain-modeling`, `codebase-design`, `research`, `handoff` |

The exact file list and pinned revisions live in [dependencies.json](dependencies.json).
Unchanged files come directly from submodules. Adapted files live under `adapters/`.
Each imported skill receives its upstream license text. See
[THIRD_PARTY.md](THIRD_PARTY.md) for provenance and attribution.

## Maintain

Run the installer tests with:

```sh
python -m unittest discover -s tests -v
```

Update dependencies deliberately: inspect upstream changes, update the submodule
gitlink and its matching manifest commit, review affected overlays and file
mappings, then run the tests and an isolated installation. Include both gitlinks
and `dependencies.json` in the same change. Do not use `git submodule update --remote`
as part of ordinary installation.

Keep contributor guidance in [AGENTS.md](AGENTS.md). The installer has no package
dependencies and runs no upstream build scripts.
