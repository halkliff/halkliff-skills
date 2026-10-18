# Consistent verification

## Agree the process

During setup, Orchestrator and coordinators derive verification from the accepted
requirements and actual repository entry points. Reuse an existing verifier and
documented commands where sufficient. Use `create-verification-skill` as a
procedure template and `maintain-verification-skill` for source/live reconciliation;
in this workflow the deliverable is a verification process, not a new skill.
Generators' skill-authoring steps apply only to an explicit skill-creation request.

Present the proposed user journeys, observable pass conditions, independent
evidence, target environments, coverage limits and resource/side-effect boundaries
with the setup proposal. Obtain the author's confirmation before implementation
or executing the new process. Already approved equivalent verification needs no
separate approval. Record detailed procedures once in
`<coord-root>/verification.md`, owned by Orchestrator with coordinator input;
link it from `plan.md` and briefs. For a small
run, the plan's acceptance rows suffice; create no duplicate map or message files.

Methods may be refined within the confirmed criteria and resource authority.
Changing required journeys, expected behavior, pass thresholds, environments or
resource permissions requires Orchestrator reconciliation and author confirmation
when reserved. Hold only affected work. Preserve frozen expectations.

## Define each procedure

Use one compact row or recipe per distinct requirement/journey:

- **Entry and expectation:** real user/API/CLI/library path, accepted behavior,
  independently specified result and the defect the check could detect.
- **Launch and doctor:** observed host-native command, supported initialization,
  auth/seed prerequisites and a readiness check for the correct build/instance.
- **Drive and observe:** concrete actions, visible output and persisted effects;
  name the check's owner, exact commands, evidence location and coverage limits.
- **Resources and cleanup:** owned process/port/data/profile, shared-resource
  serialization or verified isolation, teardown and retained evidence.

API/CLI/library procedures need no UI harness. A useful procedure may be drafted
before the app runs; label it unexecuted until observed. Verify a new launch/drive/
capture/cleanup recipe on a real journey before relying on it. A stand-in proves
only its exercised behavior; disclose target differences and blocked prerequisites.

Apply `test-audit` when available for test changes. Every check needs an observable
contract, credible failure, distinct coverage and a real production boundary.
Use existing fixtures and commands; a test-only production seam or source-mirroring
assertion does not prove the user's result. Installing dependencies, migrations on
user data or external writes require their own authority.

## Execute and reconcile

Workers execute assigned meaningful checks once. Sol reconciles their evidence;
independent verifiers inspect the candidate and evidence, then address a specific
gap or contradictory claim. Orchestrator checks combined behavior. Reuse valid
results for unchanged inputs; required integration checks still exercise the
integrated candidate. A review score never substitutes for missing proof.

One named owner drives each shared live instance; source inspection can fan out.
Parallel drives require demonstrated isolation of mutable data, ports and profiles.
Doctor before driving and after a surprising result. Reset a broken session to a
known state instead of continuing on uncertain state. Keep ownership in the plan.

Reconcile affected procedures with source changes before acceptance, then exercise
the affected required journeys live. Treat a verifier/harness mismatch separately
from a product failure. Correct the owned procedure within approved expectations
and re-drive it; escalate conflicting contracts instead of rewriting the expected
result. Verification-only assignments report proposed procedure corrections;
the assigned edit owner applies them within scope. Unreachable or unattempted
required paths remain blocked, not passing.

Reports map criteria to source, executed evidence and limits; identify failures,
unmet prerequisites and unverified environments. Teardown exact owned resources,
check path containment before cleanup, and confirm evidence survives. Preserve the
author's instances/data. Freeze accepted procedure/evidence at existing review
boundaries; changed inputs invalidate only affected claims. Use the existing
handoff rather than an additional verification completion report.
