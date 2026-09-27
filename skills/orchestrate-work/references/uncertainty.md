# Decisions, holds and escalation

## Authority

Reversible internal choices within accepted behavior, scope, compatibility and
security constraints are delegated. Choose a testable approach, record a short
reason and continue. Existing code may establish an internal baseline; it cannot
override author intent. Escalate consequential uncertainty, conflicting requirements,
or an unclear boundary between internal choice and reserved decision.

Workers ask their Sol; Sol resolves from contract/evidence or escalates to Astra;
Astra resolves shared architecture or asks the author. Direct Astra workers report
to Astra. Research routing is defined in [SKILL.md](../SKILL.md#define-and-route).
Research must target a missing fact with a discriminating question and stop
condition. Repeating an investigation at each tier adds no authority. Missing
author intent and known conflicts go promptly to the author, naming incompatible
clauses and what each option gives up.

## Hold

Hold the affected step and transitive dependents. Establish independence against
inputs, interfaces and shared resources before continuing other authorized work;
a missing dependency entry is not proof. Uncertain independence means hold.

Send a native hold with stable ID, reason, affected tasks and contract revision.
Coordinators stop affected dispatch and interrupt workers where supported. Each
recipient reports stopped or pending, identifying remaining operations; batch
multiple holds in one reply. These are the only mandatory ACKs. Track pending
recipients in current state. Runtime interruption alone does not establish that
external operations stopped. Ask the author without waiting for every stop ACK.
Results produced during a pending stop remain unaccepted until reconciled.

## Resolve or abandon

Record the authoritative answer, revise affected contracts and invalidate stale
evidence. Resume names the exact hold, resolution and applicable revision. Apply
the revised brief before restarting its scope; older/duplicate messages cannot
clear newer or unrelated holds. Missing or contradictory resolution keeps the
scope held. Other holds remain active. The next report identifies the applied
revision; no separate resume ACK is required. Time and wakeups resolve nothing.

Astra may abandon an approach after evidence or author input shows it cannot usefully
continue. Stop it, track pending operations, preserve useful commits/findings and
replan unmet requirements. Only the author changes goal scope. A dependency hold
is distinct from a goal pause; use live goal-tool rules through runtime.md.
