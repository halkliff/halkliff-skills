---
name: maintain-formal-verification-skill
description: "Bring a project's formal verification back in line with the code after the code changes: find the commits that touched verified code, update the model, harness, or properties to describe the code as it is now, rerun, and say whether each failure is drift in the verification or a bug in the code. Use for /maintain-formal-verification-skill, \"is the model still true to the code\", or after merges and refactors that touched verified code without rechecking it."
---

# Maintain a formal verification skill

A formal check proves a property of what it describes. When the code changes and the verification does not, the check can keep passing while it describes code that no longer exists. That pass is the dangerous case, because it looks like a proof. This skill is the upkeep loop for a verify skill that `/create-formal-verification-skill` generated, or for any project-local skill that runs a model checker, prover, or code-level verifier against named code. The project-local skill handles a change that an agent makes while it uses that skill. This skill handles the changes that skipped it: merges, edits made without the skill, and drift that builds up across many commits.

## Outcomes

Give each check one outcome, and say which:

- **in sync**: no change since the last sync alters what the check describes, and the check passes.
- **updated**: the code changed, the verification now describes the new code, and the check passes.
- **bug**: the verification describes the current code, and the code breaks the property. This is a finding about the code. It is not drift.
- **blocked**: the check could not be brought back in line or could not run. Say exactly why.

A check can be both updated and bug: the update makes the verification describe the code again, and then the property fails on it.

## Edit scope

For requested maintenance, edit only verification-owned models, helpers, property files, and skill instructions. For an audit, record findings and proposed changes. Keep accepted properties and frozen bounds. When a property fails, report the failure before proposing any change to the contract or product code. Read `skill-creator` and `writing-for-agents` when editing a skill, and `test-audit` when editing tests.

On Windows follow the existing project runner and use PowerShell with resolved paths, separate run directories, and immediate exit-code capture. For TLA+ consult the [statechart Windows reference](../statechart/references/windows.md). Preserve the pinned tools. If a dependency or target is unavailable, record which check could not run and retain the last verified revision.

## Pass

1. **Find the checks.** Inspect the named skill or the relevant repository skill directories, normally `.agents/skills/` in Codex. For each check, collect its property, code coverage, bounds, assumptions, command, tool version, and verified revision. If no verifier exists, point to [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md). If no sync commit exists, use the last verifier change as a history lead and establish what was actually checked.

2. **Run it as it is.** Run each check once before you change anything, and record the result. A pass here does not tell you that the code is correct. It tells you that the old description still holds. A failure here can be drift or a bug. Do not decide which until step 5.

3. **Read every change to covered code.** Diff the covered files from the sync commit to the revision under review, including relevant working-tree changes when in scope. Read relevant commit messages. Follow moved, split, or renamed code and look for new paths that write guarded state. For each change, decide which of these it is:
   - **No effect.** The change does not alter anything the verification describes, such as formatting, comments, or code paths that the verification does not cover. Check this against the model or harness, not against the commit message.
   - **The verification no longer describes the code.** A step that was one indivisible action is now two, a branch was added or removed, a check moved, a new path reaches the guarded state, or a value now has a different range. The model or harness must change.
   - **The promise changed on purpose.** The change alters what the code promises, and evidence in the change says that this is intended: the doc comment, the tests, the changelog, or the commit message. The property must change, and you must cite that evidence.
   - **The promise may be broken.** The code changed, and no evidence says that the promise changed. Treat a failure that follows as a bug candidate.

4. **Update from the code.** Trace each changed model transition to a code location and preserve the implementation's atomicity. Adapt properties only to confirmed contract changes, with the old wording, new wording, and evidence. Preserve frozen expectations and bounds unless the user authorizes a change. Report any proposed scope reduction and the evidence it would forfeit.

5. **Rerun and judge each result.**
   - **Pass:** for a changed check, confirm it still catches a deliberate break. Use isolated code for a code-level checker and an independently checked model mutation for a standalone model. Rerun the original afterward.
   - **Fail:** map each action to a real transition and replay a safe, authorized trace when feasible. Classify impossible steps as model drift, observed product violations as bugs, and unresolved correspondence as model findings. Report the user impact and the introducing revision when established.

6. **Update the verify skill.** For authorized maintenance, record coverage, commands, bounds, assumptions, and the checked revision. Advance the sync commit only when you established correspondence with that specific committed revision. For a dirty or blocked run, record the review evidence separately. Follow the resulting skill once and retain the outputs.

## Report

Tell the user, for each check:

- the outcome, and the commits that you read;
- what changed in the verification and why, with a short reason for each change: the code changed shape, or the promise changed on purpose (with the evidence);
- the rerun result, and the break that you used to show the updated check can still fail;
- each bug, in plain words: the counterexample as steps in the code's words, the harm, and the commit that introduced it;
- what the verification still does not cover, including new code that it should cover and does not.

Say outright which failures were drift in the verification and which were bugs in the code. For a check that passed before you updated it and fails after, say that the old pass was on a stale description.

Put the verification updates in a change of their own, separate from any product fix.
