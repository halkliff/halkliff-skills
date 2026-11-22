# Review work

`review-work` performs an independent assessment of delivered code. It builds on
the implementation orchestration's checks and produces a verdict, quality scores,
an HTML evidence report, and a handoff for the work thread. Each invocation runs
one review. Fixes belong to the work thread. Request a re-review in the original
review chat after the fixes are ready.

## Install and invoke

Install the standalone skill and its selected dependencies from this checkout:

```sh
python scripts/install.py --offline
```

The installer preserves customized destinations by refusing conflicts. It does
not update upstream pins. Use `--dry-run` first when checking an existing setup.

For the separate local plugin, build its self-contained package:

```sh
python scripts/build_plugin.py --plugin review --dest work/plugin-package/halkliff-review-0.2.0
```

Register the repository marketplace if it is not already registered, then install:

```sh
codex plugin marketplace add "<absolute-repository-root>" --json
codex plugin add halkliff-review@halkliff-local --json
```

Select the main chat's model and effort in Codex. The review default is GPT-6.2
Astra High. Invoke `$review-work` for the standalone skill or
`$review-work-plugin` for the plugin wrapper. Both entrypoints are explicit-only.
The plugin bundles the core and dependencies as resources under `support/skills`.
It adds no background daemon, MCP server, or automatically activated hooks.

A starting request can identify the repository, comparison baseline, current
candidate including dirty edits, approved plan, and any work-thread handoff.
Explicitly request coordinator chats and their scoped messages when desired;
stored prompts do not authorize task creation or messaging. The reviewer recovers
available context and asks only about material gaps. It agrees the project rubric,
reuses settled decisions, and follows the orchestration's explicit live-goal choice.

The package uses the portable manifest and repository marketplace described in
[OpenAI's plugin packaging documentation](https://developers.openai.com/plugins/build/plugins).
The supported installation commands come from the installed Codex CLI's help.

## Understand the result

| Verdict | Meaning |
| --- | --- |
| Ready | The requirements, required evidence, and every critical quality dimension pass, with no unresolved material objections. |
| Changes required | A verified defect, unmet requirement, or demonstrated quality shortfall prevents acceptance. Evidence gaps remain visible. |
| Incomplete | Missing evidence, access, coverage, or unresolved objections prevent a defensible acceptance decision. |

Quality scores range from 0 to 10. The default acceptance threshold is 9 for the
overall assessment and each agreed acceptance-critical dimension. Criteria cover
correctness, structure, documentation, testability, formatting, and the project's
adopted conventions. Optional improvements remain advisory. An average cannot
compensate for a weak critical dimension or missing required verification.

The review covers the complete change and its relevant blast radius. Unrelated
findings are separate. Meaningful checks and behavioral probes support code and
documentation evidence. Valid existing evidence is reused. The available
`test-audit` skill contributes its test-value assessment; the bundled workflow
contains the required observable-behavior gate for hosts without that extra skill.

Independent verifiers challenge blockers, coverage, quality scores, and missed
problems, including clean initial reviews. The main reviewer and coordinators
resolve disagreements against the rubric and evidence. Material unresolved
objections prevent Ready. The verification summary gives you a chance to weigh in.
The reviewer proceeds by default.
Request a pause after verification when you want an explicit checkpoint.

## Protect the implementation

Reviewers may change code only in their own clones or worktrees. This includes
temporary probes, tests, generated code, and formatting or lint autofixes. The
author's code and existing application data stay protected. An isolated checkout
must reproduce the actual candidate, including relevant uncommitted changes.

Use the least expensive safe isolation. All code-bearing report work remains in
the owned workspace. Retain the workspace while reports or evidence depend on it.
Before running write-capable tools, verify their actual temporary, cache, output,
child-process and browser-profile paths. Use explicit process-scoped settings;
an owned working directory alone is insufficient. If containment cannot be
established, hold that execution and continue source review. The
[execution-isolation gate](../skills/review-work/references/workflow.md#execution-isolation)
defines evidence, escape handling and verifier responsibilities. Environment
redirection does not provide a filesystem sandbox.
Use one recorded artifact root and concise current state. Artifact paths and
report-generation commands are defined in the skill's
[reporting reference](../skills/review-work/references/reporting.md).

The report helper checks data consistency and renders escaped, offline HTML.
It does not establish that evidence is true, discover defects, or assign scores.
The agents perform those judgments. A valid JSON report is not proof of Ready.

## Use the agreed model hierarchy

The review defaults use GPT-6.2 Astra High for main and coordinators, GPT-6.2 Sol
High or xHigh for investigation, and distinct GPT-6.2 Sol High agents for independent
verification. GPT-6.2 Sol authors the HTML report. Luna handles summarization at
any stage, preserving evidence links and unresolved questions.

Review setup groups the open model and effort choices. You can accept the
defaults or name a different model or effort for a role, chat, workstream or
purpose. The review records what was requested and what the host exposes about
the settings in use. A routing change preserves each role's responsibilities,
including independent verification. [Review roles and routing](../skills/review-work/references/workflow.md#assign-focused-roles)

The review goal, when explicitly requested, concerns the completed assessment
and deliverables. A Changes required verdict does not authorize repairs or an
automatic second review. Re-review needs a new request in the same review chat.

## Calibrate before relying on Ready

A new installation is uncalibrated. Installation, package checks, renderer checks,
and instruction review establish their own limited facts. They do not establish
the full reviewer's accuracy or the effective model settings in live reviews.

Before regular reliance, agree fresh representative cases and independent hidden
outcomes. The real review process must find every known acceptance blocker,
accept sound cases, identify missing proof as Incomplete, avoid unsupported
confirmed blockers, and respect scope, candidate identity, and editing boundaries.
Investigate valid unexpected findings. Preserve case-level outcomes and scoring
rationales. Cases used to design the skill are regression examples, not independent
calibration. See [the calibration procedure](../skills/review-work/references/calibration.md).

The [next calibration trial plan](review-work-calibration-plan.md) proposes known
defects, repaired and independently clean controls, and missing-evidence cases.
It is a plan awaiting execution approval, not a calibration result.
