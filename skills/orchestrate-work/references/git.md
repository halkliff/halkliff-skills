# Git ownership and delivery

Orchestrator chooses workspace mode for each phase, subject to the author's
instructions. Workers may share the main checkout with explicit nonoverlapping
scopes, or use isolated clones/worktrees when isolation helps parallel work.
Record mode, absolute path and ownership in the brief. The author's choice prevails.

Agents may commit in their owned isolated checkouts; worktrees must respect the
author's rules for shared refs. Orchestrator owns integration in either mode.
Never commit, create branches, fetch into refs or push in the author's repository;
deliver accepted slices there as uncommitted changes. The author reviews/commits.
An explicit author instruction can change this boundary. For non-Git work use
scoped versioned artifacts with one integration owner.
In a shared checkout, leave worker changes uncommitted and coordinate operations
that affect shared files or resources. A completed task never releases the main
checkout for removal.

## Helper

For isolated clone capture and delivery, use the packaged Python helper;
run `--help` for options:

```sh
python <skill>/scripts/git_workflow.py prepare --author <author-repo> --clone <new-integration-clone> --allow src --untracked src/new-file
python <skill>/scripts/git_workflow.py status --clone <integration-clone>
python <skill>/scripts/git_workflow.py deliver --clone <integration-clone> --candidate <commit>
```

Choose explicit delivery paths and initial untracked inputs. Keep coordination
records outside the selection. The helper captures dirty tracked content using
private index/object storage, commits that baseline only in the fresh clone,
and checks author state and permitted scope before plain working-tree delivery.
The helper refuses linked worktrees, submodules, sparse/assume-unchanged indexes,
custom filters, symlink deliveries and attribute-control changes. Stale state
also fails closed. Inspect the error,
preserve author work and reconcile in an owned clone; never force a patch/reset.
One integration owner serializes delivery. External author edits are not locked;
postchecks detect races but cannot promise rollback of concurrent work.

## Slices

Start workstream clones from the committed baseline; remove their push destination.
Retain source commits. Sol reviews base-to-result diffs and evidence. Orchestrator fetches
explicit source refs into its clone and integrates small accepted slices, recording
source-to-integration commit mapping. It reopens local review only for an integration
issue or evidence gap. Avoid ZIPs, whole-repo evidence copies and manual file transfers.

Delivery reports include clone and commit range for
`git -C <clone> log -p <from>..<to>`, preserving slice review in a dirty checkout.
Delivery is not behavioral acceptance: Orchestrator runs relevant integrated checks before
publishing that checkpoint as a dependency. Candidate/delivered/accepted state
lives in [protocol.md](protocol.md).

Workstreams fetch the accepted integration commit and rebase only their unaccepted
suffix using the recorded accepted source cutoff, or cherry-pick that suffix onto
a fresh branch. Checkpoint local work first. Reconcile conflicts within accepted
requirements or escalate; never treat dirty author files as a rebase target.

## Cleanup

Coordinator verifies when workers have finished their assigned work and reports readiness
to Orchestrator with the changes, evidence, remaining operations and any further
need for the isolated checkout. Worker completion alone does not release it.

Orchestrator releases an isolated checkout after confirming correct integration
and that no further task, operation or dependency needs it. Preserve required base
and result commits under retained refs in the integration clone, and useful
artifacts outside the retiring checkout. Update evidence pointers to those
retained locations. Account for remaining uncommitted and ignored files before
removal; preserve useful work and resolve undelivered changes first.

The assigned owner removes a released clone only after verifying its exact
absolute path against the recorded workspace. Codex-managed worktrees use
`archive_worktree`; preserve needed ignored files separately. Report cleanup or
the retention reason in the existing result/state, without a separate ACK.

Retain the integration clone and delivery state until the run no longer needs
them and the author has committed the delivered work or explicitly authorized
earlier retirement. Preserve required review evidence before retiring them.
