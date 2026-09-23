# Task brief and result

Write only fields relevant to the task, but always make the outcome, ownership,
constraints, and acceptance evidence unambiguous. Paths must resolve from the
worker's actual workspace. Include relevant repository instructions and the
exact skill paths needed by a fresh worker.
Before implementation dispatch, the root goal definition gate must have passed
(unless the user explicitly requested goal-free work). Each brief includes the
`unslop` skill path as a mandatory publishing instruction, plus only the domain
skills needed for that assignment. Apply `unslop` to the brief itself.

## Dispatch brief

```text
ID / role / parent: Include the parent's callable task/agent ID and host if needed.
Contract revision / root ledger / coordination directory / requirement IDs:
Goal reference: Accepted goal record, or explicitly authorized goal-free task objective.
Outcome: Observable user behavior or the question to answer.
Workspace / base state: Absolute path; revision and dirty prerequisites if relevant.
Inputs: Specific files, symbols, decisions, source URLs, or prior result paths.
Constraints: Relevant user decisions, compatibility, excluded changes.
Ownership: Files or areas this agent may edit; shared files owned elsewhere.
Dependencies: Accepted prerequisites, exact artifact revisions, and interface contracts.
Consumers: Known downstream tasks and which outputs they need.
Acceptance: Concrete examples, edge cases, checks, and required documentation.
Deliverable: Artifact paths and the concise result expected by the parent.
Decision basis: Accepted decisions and verified facts with their evidence pointers.
Delegated choices: Explicit implementation discretion and its constraints, if any.
Escalation: Stop on any doubt; exact parent route and uncertainty protocol path.
Hold/resume: Check applicable question holds; acknowledge revised briefs before resuming.
Independent work: Evidence for any authorized assignment continuing during a hold.
Capacity: Coordinator worker slots; worker is a leaf.
```

State implementation latitude explicitly inside the contract. Omitted behavior
is not delegated discretion. Explain a necessary design constraint; do not dictate
a solution merely because the parent imagined one. Require a preflight response
of either clear-to-start with the contract revision, or a concrete escalation;
reading the brief is not evidence that its gaps have been resolved.
For research, name the decision being informed and require claim-to-source
references, dates for changing facts, and conflicting evidence. For summaries,
specify the audience and which distinctions must survive compression.

## Result record

```text
ID / contract revision / state: ready, needs changes, needs-decision, or blocked;
accepted is a parent decision.
Outcome: What actually changed or was established.
Artifacts: Versioned manifest per communication.md, actual output locations, and scope.
Evidence: Criterion -> command/observation/source -> result -> artifact version.
Limitations: Failed or unrun checks, uncertainty, missing sources, remaining scope.
Decisions needed: Open question IDs and basis for any resolved question.
Hold acknowledgment: Last safe state and any running operations, when applicable.
```

Parents add their acceptance/rejection and independent evidence. Keep raw logs
behind paths. If no clean revision exists, identify the files/state tested and
whether later edits occurred; never attribute pre-edit test results to new edits.

Use the task ledger to track queued, running, ready, needs changes, needs-decision,
accepted, and blocked work, with per-question awaiting-author holds and explicit
affected/dependent assignments. These are workflow states, not goal-tool statuses.
Blocked means missing
required input or external capability;
it does not mean difficult. Requeue affected dependents when a shared contract
changes, and send only the contract change and newly required checks.
