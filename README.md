# halkliff-skills

Personal Codex skills, including `orchestrate-work` and the dependencies it uses.
The workflow defines a goal, coordinates Astra/Sol/Luna work, passes versioned
artifacts between tasks, and escalates uncertainty to the author. It runs only
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

## Use

Invoke `$orchestrate-work` with the work you want to pursue. It starts through
`define-goal`, requires `unslop` for authored prose, and follows the communication
and uncertainty rules in the [skill](skills/orchestrate-work/SKILL.md).

The orchestration runtime targets Codex: it needs the model, goal, task, and
subagent capabilities described in its runtime reference. Installing Markdown
does not grant unavailable tools or models. Other agent runtimes need a reviewed
runtime adapter before executing this hierarchy.

`orchestrate-work` has `policy.allow_implicit_invocation: false`. Its dependencies
retain their own invocation policies; `unslop` remains an always-applied prose
skill. If the running client has not refreshed its skill inventory, reload it.

## Included skills

| Source | Selected skills |
| --- | --- |
| This collection | `orchestrate-work`, `define-goal` |
| pstack, adapted for Codex | `pstack-principles`, `unslop`, `how`, `why`, `blast-radius`, `no-comments` |
| Matt Pocock, with selected compatibility adaptations | `grilling`, `writing-for-agents`, `domain-modeling`, `codebase-design`, `research` |

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
