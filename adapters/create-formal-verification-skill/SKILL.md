---
name: create-formal-verification-skill
description: "Generate a project-local skill that formally verifies the code where a bug costs the most and tests reach the least, in any language, with whichever verification tool fits. Use for /create-formal-verification-skill, \"model-check this race\", \"prove this invariant\", or when concurrency, retries, state machines, parsers, or unsafe code need more than tests."
---

# Create a formal verification skill

A test checks the cases that someone thought to write. Formal verification checks every case in a stated scope: every order of steps in a model, every input up to a bound, or every input. This skill finds the part of the repo where that matters most, verifies one property of it, and leaves a project-local skill that lets the next agent check a change against that property. Write that skill for an agent who reads it cold, mid-change, and has never seen your work. The user must be able to trust the result and act on it without learning the verification language.

## Choose the target from the code

Answer from the codebase, and ask the user only what you cannot observe. If the user named an area or a bug, start there.

A good target is a promise the code makes, where a break harms users and tests rarely reach the case that breaks it. Choose the strongest such target in the repo, not the one that is easiest to verify.

## Let the question choose the tool

Pick the tool that answers the question at the lowest cost: a model checker, a proof assistant, an SMT-backed verifier, or another tool. Whether events can happen in a bad order usually suits a model checker over a small model of the design, and TLA+ is the default for that in any language. Whether the code itself behaves for every input, as with memory safety, overflow, or a data-structure invariant, usually suits a verifier that runs on the code. If no verifier runs on this language, say so, and test the real code with generated inputs, not a hand model of the function. A property that must hold at every size, where a bound is not enough, can need a proof. Prefer a tool that the repo's developers can install and run, and tell the user why you chose it.

## What makes it good

- **True to the code.** Every part of the model or proof points to code that a reviewer can open. What the verification treats as one indivisible step is one indivisible step in the code. Names come from this repo.
- **Able to fail.** A check that you have never seen fail proves nothing. Show each property failing on a broken variant of the code it guards, such as a removed check or a reordered step.
- **Findings stay findings.** When the current code breaks the property, report it with the counterexample in the code's terms. Do not weaken the property or the model until it passes, and do not change product code unless the user asks.
- **Honest about scope.** Say what is verified, under which bounds and assumptions, and what is left out. A pass covers the model or the bound, not the whole system.
- **Readable without the tool.** State the property and the harm in one plain sentence each. Tell a counterexample as a short sequence of steps in the code's words.
- **Cheap to rerun.** One command, a reproducible tool version, and a run short enough that the next agent will use it on every relevant change.
- **Kept in step with the code.** Record which files and functions each check covers, and the commit at which you last confirmed that the verification describes them. When the covered code changes after that commit, the next agent can see that the verification needs another look.

## Generate the verify skill

Read the installed `skill-creator` and `writing-for-agents` guidance. Use the repository's existing Codex skill layout or `.agents/skills/verify-<area>/SKILL.md`. Keep models, configurations and rerun helpers in the repo's established verification area or alongside the skill. Use valid Codex frontmatter. Document the property, source paths and symbols, assumptions, bounds, tool versions, runnable command, outcomes and evidence locations. Record the verified revision. If verification used dirty files, record that fact and the reviewed diff or hashes. Advance a sync commit only after checking that committed revision.

For TLA+, use [statechart](../statechart/SKILL.md) to interpret TLC outcomes, view counterexamples, and render state graphs. Follow its [PowerShell command and runtime reference](../statechart/references/windows.md). In the generated skill, refer to `$statechart` by name and record the model and config paths relative to the repo. Keep the direct checker command or repo runner reproducible alongside that reference. Do not embed a user-specific global install path in repository files.

### Windows execution

Prefer a pinned checker that runs natively with the repository's existing tools. Use PowerShell call operators and argument arrays for paths with spaces. Check the actual executable and version, and capture `$LASTEXITCODE` immediately. Work in a uniquely named scratch directory or isolated worktree for baseline and broken variants. Keep logs, models, commands, and traces outside temporary directories owned by the checker. If a tool requires WSL or a container, verify it exists and label the environment used. Keep dependency provisioning within the requested scope.

## Prove it before you hand off

Run the baseline first. Prove each property can fail by supplying a deliberately broken variant in isolation, then rerun the original and preserve both outcomes. For a checker that reads code directly, break the real code in the isolated copy. For a standalone model, break the corresponding modeled transition, then independently check that the original and mutated transitions accurately represent the code changes they claim to represent. Changing code alone cannot change a standalone model's verdict. Replay a safe, authorized counterexample on the real interface where feasible. Follow `test-audit` when adding or adjusting tests. A verifier that has not run remains a draft. Preserve accepted properties and bounds, and report product defects separately.

## Hand off

Tell the user what you verified, which tool you used and why, the bounds, the observed verdicts, the rerun command, and what remains unverified. Point to [maintain-formal-verification-skill](../maintain-formal-verification-skill/SKILL.md) for upkeep. Keep product changes, commits, publication, and recurring execution within their own authorized scope.
