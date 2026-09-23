# No assumptions: escalation and execution holds

## What authorizes a decision

Use an explicit user requirement, an accepted contract decision, verified relevant
evidence, or an explicitly delegated choice with stated constraints. Link the
basis in the task record when it determines behavior or acceptance. Familiarity,
industry convention, silence, time elapsed, and confidence do not authorize a
missing decision. Existing code establishes observed behavior, not necessarily
intended behavior. Conflicting requirements need resolution; do not pick one.

Implementation discretion must be explicit in the brief. Within an explicitly
delegated choice, follow its constraints and required verification; any doubt
still escalates. Do not demand approval for every deterministic step already
specified. Do not reinterpret this discretion as permission to infer requirements.

Evidence gathering can involve named hypotheses. Keep them unconfirmed until the
evidence distinguishes them; an unconfirmed hypothesis cannot authorize product
changes. A missing research finding may be a legitimate result. Unclear research
scope or evidence requirements are a task-definition problem and must escalate.

## Escalation sequence

1. **Luna:** Stop the affected assignment before acting on the uncertainty. Preserve
   current artifacts and send Sol an escalation record. Do not guess, implement
   several assumed behaviors, or quietly broaden the assignment. Await a revised
   brief or an explicit evidence-backed answer.
2. **Sol:** Resolve only if the existing contract and evidence establish the answer.
   Record that basis and send it to Luna. If Sol is also uncertain, immediately
   forward the question to Astra and hold dependent assignments. Do not replace
   uncertainty with the coordinator's preference or launch speculative repairs.
3. **Astra:** Check accepted decisions and perform bounded research that can
   distinguish the alternatives. Check counterevidence and source applicability.
   Research cannot establish the author's missing preferences or business choices;
   ask directly for those. If evidence is absent, conflicting, inapplicable, or
   otherwise insufficient, immediately hold affected work and its dependents and
   ask the author. Continue only established independent work as described below.
   Do not keep searching indefinitely to postpone the question.

Use the smallest decisive research step available. If there is no identifiable
check that could resolve the issue, or that check leaves it unresolved, ask the
author. Request further research instead of performing an open-ended investigation.

## Escalation record

```text
Question ID / task / contract revision:
Uncertainty: The exact missing or contradictory fact/decision.
Evidence: Relevant requirement/source references and checks already performed.
Alternatives: Plausible interpretations, clearly marked unconfirmed.
Impact: What cannot proceed and what already-produced work might be affected.
Requested decision: One specific answer or missing artifact.
Execution state: Last safe step, running operations, and stop acknowledgments.
```

Send the question promptly through the parent route in the brief. Record it before
ending the child turn. Use an explicit `needs-decision` result if communication is
unavailable; do not present the assignment as successful. Escalations are control
messages: concise summaries must retain the actual question and its evidence.

## Dependency holds and resume

When Astra needs the author, record an `awaiting-author` question with the affected
requirements, artifacts, assignments, and transitive dependents. Stop dispatch,
implementation, and integration for that set. Within the current subagent tree,
interrupt affected active agents directly; do not depend on an unresponsive Sol
to relay a stop. For separate Sol tasks, send a scoped stop instruction. Each Sol
interrupts affected Luna agents and acknowledges the last safe state and pending
operations. Preserve existing edits; do not reset or commit them to stop.

The author explicitly permits unrelated work to continue. Establish independence
from task inputs, accepted interfaces, shared files/resources, and transitive
dependencies; absence of a recorded dependency alone is not proof. Record why
each continuing assignment cannot be affected by the unresolved alternatives.
An agent may continue an already authorized assignment with that evidence, while
reporting the boundary to its parent. If independence is uncertain, hold that
assignment and escalate. Do not invent new work to stay busy. If the decision
affects the whole goal, hold the whole goal. Within held work, only preservation,
stopping, and decision communication continue.

Ask the author immediately; do not delay the question until every acknowledgment
arrives. Cooperative stop requests with acknowledgment tracking are accepted by
the author. Report pending acknowledgments honestly; already-running operations
may complete before an interrupt arrives. Mark their results as produced during
a pending hold and withhold acceptance/integration until the decision is resolved.
Use the goal lifecycle mapping in [goals.md](goals.md) when a goal exists. Pausing
the root goal does not by itself stop separate Sol tasks or their workers.

After explicit guidance, Astra records the answer and its authority, revises the
contract, identifies affected artifacts and dependent tasks, and invalidates stale
acceptance evidence. Sol acknowledges the revision and briefs its workers before
resuming held assignments. Send a scoped resume message naming the resolved
question, decision, and revision. Other open holds still apply, and independent
work need not have stopped. Silence or a scheduled wakeup cannot resolve a
question. Preserve unrelated user changes throughout reconciliation. Use
[communication.md](communication.md) for durable messages and acknowledgments.
