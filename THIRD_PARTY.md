# Upstream sources and adaptations

## pstack

Source: [cursor/plugins, pstack](https://github.com/cursor/plugins/tree/main/pstack),
checked out at `upstream/cursor-plugins`. Its pinned commit is recorded in
`dependencies.json` and the Git submodule entry.

The pstack directory includes an MIT license, copyright 2026 Lauren Tan.
The installer includes that exact text as `LICENSE.upstream.txt` in every
installed pstack-derived skill. The source notice remains at
`upstream/cursor-plugins/pstack/LICENSE`.

The collection preserves the previously reviewed Codex adaptations of `how`,
`why`, `blast-radius`, `unslop`, and `no-comments`. `pstack-principles` is a
consolidated entry point with selected principle notes, not the upstream Cursor
router. Cursor-specific agents, model settings, setup commands, and automations
are not part of this installation.
The consolidated principle notes use sibling Markdown links so their references
resolve in the installed aggregate rather than the upstream directory layout.

## Matt Pocock skills

Source: [mattpocock/skills](https://github.com/mattpocock/skills), checked out at
`upstream/mattpocock-skills`. The repository includes an MIT license, copyright
2026 Matt Pocock. The installer includes that exact text as `LICENSE.upstream.txt`
in each installed skill derived from this repository. The source notice remains
at `upstream/mattpocock-skills/LICENSE`.

Selected skill contents were previously installed and reviewed against commit
`3cca18b368ae95cdbdebbff572ccafa662551015`. This collection preserves those reviewed
semantics through explicit file mappings and overlays. Its current submodule pin
is a separate source snapshot; pulling upstream does not silently replace the
reviewed adaptations.

The earlier `grill-me` and `grill-with-docs` wrapper adaptations are not included:
they are not dependencies of `orchestrate-work`. Only the reusable `grilling`
skill is needed here. Likewise, the package excludes upstream issue-tracker setup
and publishing workflows.

Two narrow compatibility changes are maintained in this collection: an assigned
research worker performs its own investigation instead of recursively spawning
another agent, and the writing-for-agents invocation reference describes Codex's
`agents/openai.yaml` policy. The latter preserves the required skill description
and does not treat another client's frontmatter as Codex configuration.

## define-goal

`skills/define-goal` preserves the local skill and its supplied Apache-2.0
`LICENSE.txt`. It is packaged directly because it is not supplied by either of
these upstream repositories. No additional provenance or copyright ownership
is inferred from the presence of that license file.

## Review and update policy

The earlier local adaptation work is the behavioral baseline. A manifest entry
uses an upstream file directly only when it matches that reviewed baseline, or
when an explicit compatibility change has been reviewed. Local overlays are
maintained here; upstream submodules remain separate Git repositories.

License texts for upstream work continue to apply regardless of the license
chosen for this collection's original work. Retain the included notices when
redistributing installed skills.

The author chose MIT for this collection's original work; see the root `LICENSE`.
This does not replace `define-goal`'s supplied Apache-2.0 license or upstream notices.
