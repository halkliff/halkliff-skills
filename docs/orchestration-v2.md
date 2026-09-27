# Workflow revision 2

The milestone-2 assessment identified coordination overhead despite useful
engineering work. Revision 2 introduces autonomous Sol workstreams, Luna xHigh
execution, bounded internal discretion, native messages, hold-only ACKs and small
continuous deliveries. The supplied run measurements were not independently audited.

## Tightening after the second audit

Workers receive [worker.md](../skills/orchestrate-work/references/worker.md) plus
their brief. Coordinators use the [entrypoint](../skills/orchestrate-work/SKILL.md)
and load references for the current operation. Repeated topics now have one
coordinator reference: decisions/holds in uncertainty, messages/state/rollout in
protocol, host operations/goals in runtime, and repository delivery in Git.
The worker guide repeats only the local boundaries needed to execute independently.

The packaged Python Git helper replaces per-run command construction. Delivery
reports retain the integration clone and exact commit range so the author can
review individual slices even when the working checkout is already dirty.

The author approved a bounded lookup exception: one known file read or targeted
read-only command can stay with a parent; larger investigation remains Luna work.
The model/effort table, consequential escalation, unslop scope, Git ownership,
hold status and honest waiting rules remain in force.

## Size

Word counts include the entrypoint, references and glossary, excluding executable
code, tests and repository documentation. This is instruction size, not measured
runtime tokens or weekly allowance savings. Workers previously loaded the
1,352-word entrypoint before task-specific references.

| File | Before | After |
| --- | ---: | ---: |
| `SKILL.md` | 1352 | 657 |
| `CONTEXT.md` | 476 | 144 |
| `git.md` | 1058 | 345 |
| `protocol.md` | 1487 | 604 |
| `runtime.md` | 1518 | 570 |
| `uncertainty.md` | 632 | 360 |
| `worker.md` | 0 | 263 |
| **Total** | **6,523** | **2,943** |

The runtime before-count includes goals; protocol includes the former communication,
state and task-contract files.

## Runtime evidence and limits

On 2026-09-27 a throwaway projectless Sol High task used an explicit absolute
working directory to read and write one file in a separate synthetic clone.
Its default task directory remained distinct. It ran with unrestricted filesystem
access and approval policy never; no permission escalation, branch or commit was
needed. Task ID: `01a0e168-9980-7030-879c-6d94acb3c6dc`.
This validates that workspace route on this host, not automatic UI rebinding or
other sandbox profiles. The runtime guide requires a fresh access check there.

The review process uses a separate Sol High verifier followed by a Sol High
reviewer, with up to three rounds for this revision. This is an author-requested
editing check, not an extra mandatory verification hierarchy for every future run.
Actual allowance savings and unattended end-to-end completion remain unmeasured.

| Round | Verifier score | Finding and response |
| --- | ---: | --- |
| 1 | 7/10 | Interrupted add/delete delivery could report success with a deleted file still present. The helper now checks deleted paths and preserves the pending checkpoint on partial application. |
| 2 | 8/10 | The fix handled the original failure, but an unrelated fixture edit masked it in one regression test. Removed that edit. |
| 3 | 8.5/10 | The corrected regression fails on the old installed helper for false success and passes on the repaired installed helper. No remaining material blocker was found. |

The 11 helper tests passed after the code repair. After the fixture correction,
only the affected test was rerun against both installed versions. The 14 installer
tests passed earlier; unchanged checks were reused. The isolated installation's
82 files matched the manifest, skill validation passed, and the existing user
installation's 81 files across 13 skills were unchanged. These checks cover the
executable Git helper and packaging, not an unattended orchestration run.

## Adoption and next-run measurements

Installed skills and live runs remain unchanged. The package stays explicit-only;
upstream pins and notices remain unchanged. Migration has one authority in
[protocol.md](../skills/orchestrate-work/references/protocol.md#rollout).

Measure accepted outcomes, messages per accepted requirement, hold ACK share,
assignments affected per hold, ledger/artifact size, author questions, integration
backlog, retries and wall time. Report zero accepted requirements as counts rather
than an undefined ratio. Record usage/cost only when exposed; a smaller document
or a review score does not establish runtime savings.
