---
name: correct
description: "When explicitly asked to use correct or prevent recurring agent mistakes, find repeated mistake classes in a repo and enforce prevention through architecture, types, actionable checks, or behavior tests."
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent can't make them.

Run only when the user requests this workflow. An ordinary correction is not permission to launch a repo-wide sweep, edit global instructions, or store a memory. If asked for an audit, report findings without implementing them. If asked to fix recurring mistakes, implement only the agreed scope. Never stage, commit, publish, or run remote CI merely because this skill recommends enforcement.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

First, read recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds. Group the mistakes into classes. A class counts once it has happened twice.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint or CI check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Use `test-audit` when available for authoring, changing, or removing tests. Demonstrate the concrete defect a test detects; do not delete tests merely because they lack a particular assertion syntax.
4. **Write docs or agent rules last, only for judgment calls.** Nothing fails when an agent skips them.

## Fix and prove

For an authorized implementation, fix the most frequent in-scope classes in separately reviewable changes. Prove each new check fails on a real past mistake using an isolated fixture or recoverable temporary mutation, then restore it and prove the accepted state passes. Preserve the user's dirty files. Run the relevant command locally; report remote CI as unverified unless its result was actually observed. Do not weaken frozen expectations or add restrictions beyond accepted behavior without approval. Exceptions need a reason and the user's approval; add an expiry where it is meaningful.

## Keep the rule table

If the user requested repository instruction changes, keep a small table in the existing agent instruction file that pairs judgment rules with their enforcement. Otherwise include that mapping in the handoff. Do not silently add global rules. Remove redundant prose rules only within the authorized scope once enforcement makes them unnecessary.

**Reply:** each class with its evidence, the level you picked, and why a higher level didn't work.
