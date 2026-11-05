# Selected runtime controls

Read when using a plugin package that exposes policy selection and `operation`.
The standalone workflow and older pins retain their actual capabilities. These
controls do not replace the author-confirmed requirements, review gate or holds.

## One current authority

Root selects one versioned policy input during new-run activation with `--policy`.
Use the returned pinned CLI thereafter. The runtime records its path/hash/revision
and selecting Root session; only that owner may select the next revision:

```text
python <cli> policy-select --session <root-session> --expected-revision <current> --policy <new-absolute-file> --plugin-data <data-root>
```

Keep old input files and evidence. A replacement has a new path and revision;
directly editing a selected file makes its hash stale. Selection is prospective
and cannot reset invocation counts, failed grants or assessment allowances.
Ordinary grant-bound metadata/method completion needs no new author ACK. Reserved
scope/resource changes and assessment extensions still follow the protocol.

Policy schema version 1 supplies these mechanical facts:

| Field | Meaning |
| --- | --- |
| `revision` | Current integer revision. |
| `author_constraints` | Optional `resource_floor` with `bytes` and `basis_ref`. |
| `root_controls` | Optional `resource_headroom` with `bytes` and `basis_ref`. |
| `roles` | Role to explicit `model`/`effort` route, within accepted run decisions. |
| `resources` | Named exclusions and their owners under Root's current allocation. |
| `grants` | Outcome ID to `owner`, permitted `roles`/`adapters`/`resources`, `workspace`, `basis_ref` and `max_invocations`. |
| `adapters` | ID to `command` (absolute executable/script pair), matching `sha256` pair and permitted `claim_kinds`. |
| `integration` | One selected workspace/owner, or null when unused. |

Author constraints, Root estimates and measured observations have different
provenance. The helper cannot authenticate human approval from a citation or prove
safe peak memory from a declared number. The approved adapter retains actual
resource monitoring and cleanup. This workflow has no universal RAM floor.

Define resource groups only after checking mutable paths and physical aliases.
Operations sharing an index, cache, output or live instance use the same exclusion.
Different resource names alone do not prove isolation. Root owns lane changes;
coordinators obey the current allocation. The helper applies cooperative exclusion
to the selected groups within one plugin data root. Use canonical scope names;
separate data roots and unknown physical aliases are outside this guarantee.
This is not a scheduler or filesystem sandbox. Once registered, this version
keeps the selected integration owner/path fixed for the run; it supplies no
automatic transfer or retirement route.

## Dispatch and recovery

Put one marker in the existing assignment message; create no message artifact:

```text
ORCHESTRATION role=worker grant=<grant-id> revision=<selected-revision>
```

The active selected-policy hook checks the grant, current revision and actual
model/effort/fork arguments. A role name does not select a model. Keep Sol as the
default coordinator and Luna/xHigh as the default worker; an explicit run override
does not change other runs or permit an Astra fallback.

Enroll a recovery/coordinator chat with the existing `activate --run-id` route and
the same recorded roots/data directory. It reuses the run's pin and selection;
it cannot silently replace them. Check `status` for binding, policy validity and
observed host events separately. Empty observation counters do not prove hooks
never ran, and file presence does not prove interception. A legacy pin cannot
gain these commands by editing its state. Use the actual nested Git checkout as
the author root, not an administrative parent folder.

## Selected execution and evidence

Use one owned checked request for the assigned procedure, reusing existing task
inputs rather than copying command strings or path/count lists:

```text
python <cli> operation --session <session> --request <absolute-request> --plugin-data <data-root>
python <cli> operation --session <session> --request <absolute-request> --reuse <receipt> --plugin-data <data-root>
```

The request has `schema_version: 1` and identifies `policy_revision`, `grant`, `role`, `adapter`,
`consumer`, `claim_kind`, `procedure`, `workspace` and actual `expected_head`.
`inputs` maps names to file, JSON-array or Git inputs; the helper derives their
identities/counts. Optional `dependencies` identify actual Git prerequisites.
Git inputs/dependencies identify clean checkouts, including tracked, staged and
nonignored untracked state; HEAD alone is insufficient. Ignored/generated files,
provider bytes and outside-writer races are not proved by clean Git status and
need their own named inputs or domain evidence. The helper never cleans or resets
a checkout to make admission pass.
An optional broad `scan` names `changed_input`, `contradiction`, `first_admission`
or `new_claim` and its existing `basis_ref`. Review its justification; a marker
alone cannot establish that a broad scan is necessary.
Named inputs/dependencies are stable evidence inputs. Put writable profiles and
outputs in adapter evidence instead. The workspace may advance through an owned
operation; the receipt records its registered base, actual before/result HEADs
and range. Narrow claims may reuse unchanged named inputs across an unrelated
commit; commit/integrated/hosted claims remain candidate-bound. Whole-project
builds and installed callers must name their actual complete source/package/tool
inputs, including a Git input when that claim depends on the whole candidate.
Cached commit/integrated/hosted claims require a named Git input for the operation
workspace. Its clean admission and stable post-operation identity must match the
producer receipt. Adding this input only when reusing a JSON-only receipt cannot
qualify that receipt. Ordinary owned mutations and narrow named-file/source work
remain supported.

The command validates before invoking the approved adapter once through argv,
without shell interpolation. It checks the selected owner/workspace and real Git
HEAD, using the granted exclusions before Git/input observation. The grant's
`max_invocations` bounds adapter calls, not review assessments or child lifetimes.
Read-only grants may have empty adapter/resource lists. A typed pre-invocation
rejection invokes nothing and leaves the invocation count unchanged; that alone
does not establish that contradictory input identity is a harmless typo.
An actual observation error returns `preflight_failed`, retains evidence and
fails the grant even with zero adapter invocations. A real adapter failure also
stops the grant and retains its result/partials. No automatic retry or claim of
successful cleanup follows. Resolve observed drift through the owning contract;
never silently repair an expected hash to match new inputs.

The adapter result has `schema_version: 1` and matching `consumer`, `claim_kind`,
`procedure`, `outcome` (`pass` or `fail`) and existing absolute `evidence` paths.
The wrapper reports actual invocation/exit and the receipt path. It observes only
the named direct inputs/dependencies and Git state; it does not certify every
provider byte or nested process settlement from the adapter's exit status.
The adapter receives `--request <checked-manifest>` and `--result <result-file>`.
The checked manifest carries run/session and request identity, selected policy,
grant/role/adapter, consumer/claim/procedure, workspace/candidate, actual named
`inputs`/`dependencies`, `scan` and distinct `resource_attribution.author_floor`
and `resource_attribution.root_headroom`. It is not the original request file;
use its named input paths/data instead of recopying code or manual counts.
The approved adapter validates domain path relationships and initializes owned
temp/cache resources before profile writes, product imports or launch.
Unknown required post-observations or changed stable inputs fail the wrapper
while preserving the adapter's actual outcome and exit separately. Pending
attempts and failed bookkeeping are not proof that a product started or settled.

CLI exit codes are 0 for a successful operation or valid reuse, 1 for an actual
adapter/observation failure or rejected reuse, and 2 for validation, policy or
busy rejection. Failure JSON/receipts remain available where they could be
written. If the receipt write itself fails, it is not invented: the result has
`receipt: null` and the unresolved state stays fail-closed. A finalization error
does not erase the actual adapter result or establish successful bookkeeping.

Reuse compares consumer, claim, procedure, adapter and named actual inputs.
Relevant drift invalidates that evidence; unrelated drift does not mandate a
whole-provider rescan. The receipt's observed scope is its limit. It cannot prove
post-test provider bytes that were not observed or turn a build into installed,
integrated, hosted or publication acceptance. Require the real public caller and
every remaining agreed journey through the existing verification process.
Reuse does not clear a failed grant, unresolved hold or assessment obligation.

The backend does not intercept arbitrary shell/REPL execution or establish
coverage of app-created chats. Supplying a session ID is not authentication.
Source tests, package execution, installation and real desktop hook delivery are
separate evidence. Keep these limits in the handoff.
