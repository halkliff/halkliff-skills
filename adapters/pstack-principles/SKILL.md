---
name: pstack-principles
description: Apply the pstack engineering principles to non-trivial code, architecture, debugging, review, migration, and verification work. Use these principles to shape decisions, not as a generic checklist.
---

# pstack principles

Use the principles below as decision rules when they genuinely apply. Do not
recite the whole catalog in a reply. Name the principle only when it changed
the choice you made.

Apply them within the user's task and permissions. They do not authorize
commits, rebases, publishing, external messages, deletion, or wider changes.
Use available Codex tools and workers rather than another client's model rules
or named agents. When a worker is unavailable, do the bounded work directly.

## Core

- Bias toward deletion and the smallest change that solves the problem.
- Choose the data structures and ownership model before writing branching logic.
- Integrate new requirements as if they had been present from the beginning.
- Remove dead weight and compatibility clutter before adding new behavior.
- Minimize the reader's path from question to answer and reduce hidden state.
- Converge on the target architecture instead of preserving throwaway phases.
- Prefer a smaller number of polished user-facing capabilities.
- When a design is novel, compare structurally different alternatives before committing.
- Build the script, check, codemod, or other lever that makes repeated work reliable.
- After two fixes fail the same check under one assumption, write down that assumption and measure the imbalance per actor before trying another fix. If the same actors repeatedly carry it, investigate the assignment rather than adding recurring compensation.
- Judge interfaces from the caller's and maintainer's experience, not only implementation convenience.

## Architecture

- Model the domain in types, state machines, tables, registries, reducers, or boundaries instead of scattered conditionals.
- Concentrate validation and error handling at system boundaries. Keep internal logic simple and typed.
- Make illegal states difficult or impossible to represent. Parse external data at the boundary.
- Make commands and lifecycle steps safe to retry.
- Migrate callers and delete legacy APIs in the same change wave when practical.
- Separate shared mutable state before reaching for serialization or locks.
- Hide meaningful domain decisions behind module boundaries. Collapse pass-through layers and organize ownership around domain knowledge rather than execution phases.
- Construct valid states from their parts. Strengthen a type where an operation would otherwise be partial, not just for extra precision.

## Verification

- Explain a measured number before trusting, reporting, or acting on it: establish what limits it, rule out errors or skipped work, and keep run count, spread, and evidence with the claim. Use [Explain the number](references/principle-explain-the-number.md) for the principle and `benchmark-checklist` for performance measurements; label requested one-run ballparks as such.
- Prove the real artifact works. A build or an agent's report is not enough when a narrower runtime check is possible.
- Reproduce symptoms and trace them to root causes instead of adding guards that hide them.
- Break multi-step work into units that each end in a verifiable state.
- Test through the user's entry point against independently specified results or effects. Keep a test only when it detects a concrete defect or protects a real contract; use `test-audit` when available, or the [behavior-testing note](references/principle-test-behavior-not-implementation.md).
- Keep rerunnable verification visible in the handoff. An imported principle's suggestion to commit a check is not authorization to commit.

## Delegation

- Protect the main context by routing large, independent work to available workers and keeping summaries in the main thread.
- Do not ask the human to choose between reversible approaches that can be tested cheaply. Test the fork and report the result.

## Meta

- When a lesson repeats, encode it in a check, type, test, metadata flag, or script instead of repeating prose.

## Supporting references

The original principle notes are preserved under `references/`. Read the
relevant note when a decision depends on a particular principle's edge cases.
