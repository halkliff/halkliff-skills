# Git ownership and delivery

Agents work and commit in separate local clones. Astra owns the integration clone.
Never commit, create branches, fetch into refs or push in the author's repository;
deliver accepted slices there as uncommitted changes. The author reviews/commits.
An explicit author instruction can change this boundary. For non-Git work use
scoped versioned artifacts with one integration owner.

## Helper

Use the packaged Python helper; run `--help` for options:

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
Retain source commits. Sol reviews base-to-result diffs and evidence. Astra fetches
explicit source refs into its clone and integrates small accepted slices, recording
source-to-integration commit mapping. It reopens local review only for an integration
issue or evidence gap. Avoid ZIPs, whole-repo evidence copies and manual file transfers.

Delivery reports include clone and commit range for
`git -C <clone> log -p <from>..<to>`, preserving slice review in a dirty checkout.
Delivery is not behavioral acceptance: Astra runs relevant integrated checks before
publishing that checkpoint as a dependency. Candidate/delivered/accepted state
lives in [protocol.md](protocol.md).

Workstreams fetch the accepted integration commit and rebase only their unaccepted
suffix using the recorded accepted source cutoff, or cherry-pick that suffix onto
a fresh branch. Checkpoint local work first. Reconcile conflicts within accepted
requirements or escalate; never treat dirty author files as a rebase target.
