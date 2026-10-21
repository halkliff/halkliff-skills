# Review workflow

## Reuse the orchestration machinery

Resolve pinned dependencies from sibling skill directories in a standalone install,
or `support/skills/<name>/` in the review plugin. Read only the referenced material
needed for the current role. A missing dependency is a setup limitation to resolve;
do not pretend an installed helper or runtime capability exists.

Reuse these `orchestrate-work` references without invoking another run:

| Read when | Reference and retained behavior | Review override |
| --- | --- | --- |
| Starting or continuing | `references/protocol.md`: setup, workstream plan, compact briefs/results, current state | One review contract and candidate; no repair batches or repeated assessment gate |
| Assigning work or using a goal | `references/runtime.md`: host modes, actual human authority, dispatch, capacity, waits and goal lifecycle | Astra coordinators; Sol review and verification; Luna summarization at any stage |
| Holding a decision or affected work | `references/uncertainty.md` | Consequential uncertainty follows parents; main asks the author |
| Owning or retiring a workspace | `references/git.md`: ownership, isolation and cleanup | All reviewer code writes stay in owned clones/worktrees; no delivery into the author's code |
| Defining or running checks | `references/verification.md`: real entry points, procedures, resource ownership and evidence reuse | Verification serves this review; it does not authorize product repairs or creating a new skill |

These imports retain ordinary goal choice and resource lifecycle, not conflicting
role defaults, automatic commits, helper activation, installation, three-round
correction loops or product integration. Existing plugin hooks are optional and
are not prerequisites. Use native tools; add no daemon, MCP server or message bus.

## Recover and freeze the contract

An initial review normally begins in a fresh chat. Retrieve the work chat and
author-provided handoff, approved plan and amendments, repository instructions,
applicable contracts and existing receipts. Keep authority explicit: author
decisions and normative contracts establish expectations; source and observations
establish behavior. Tests and implementation claims cannot amend the plan.

Record a compact contract with:

- Review ID, original review chat, work chat and repository roots; source snapshot
  of the skill/dependencies; authorized coordination routes and reserved decisions.
- Baseline, actual candidate and captured dirty/untracked inputs; exclusions and
  required dependencies, configuration, generated inputs and environment identity.
- Every functional/non-functional requirement with its source, authority and ID;
  adopted project rules, explicit exceptions and unresolved material conflicts.
- Applicable quality dimensions, criteria and thresholds, required checks and
  target environments; resource ownership, output paths and permitted side effects.
- Domain split, model/effort, useful capacity, review depth, any author-supplied
  budget, goal mode, current uncertainty and next action.

Use `in-your-own-words` and `sharpen` for a compact understanding/approach/verification
proposal. Reuse settled approvals. Confirm only missing material setup; no repeated
design interview. For a new run explicitly settle goal-backed or goal-free mode,
recommending `define-goal`; create a goal only on explicit author request. A
continuing run reuses its confirmed mode and matching authorized live goal.
Editing this skill is not a new review run or a request for another goal.
The review goal is a completed assessment, report and handoff, not a repaired
implementation. Do not ask for an assessment-iteration cap: this invocation has
one assessment and no correction cycle.

Discover the documented lint, formatting, type, build and test entry points and
their relevant configuration. Before check execution, settle any missing resource
authority; routine equivalent checks within established authority need no new
permission. A budget or access limit leaves uncovered requirements visible.

Finish setup when the baseline, candidate, scope, criteria and usable evidence path
are known. If an unresolved material choice prevents that, ask with concrete
alternatives and consequences while continuing independent work.

## Candidate and workspace ownership

Read-only source inspection may use the author's checkout. Any command expected to
write code, tests, probes, build output, generated HTML/code or autofixes must run
inside a reviewer-owned clone or worktree, with isolated mutable resources. That
code-write boundary has no temporary-probe exception. Never repair the candidate.

Choose the least expensive safe environment: source-only reading when sufficient;
an owned worktree for a clean candidate when safe; an owned clone or equivalent
snapshot capture when dirty files, index state, submodules or shared refs make a
worktree unsuitable. Copy only required candidate inputs, preserving bytes and
relevant metadata. Include relevant untracked/ignored inputs deliberately; exclude
secrets and author application data from casual copying. Honor permitted access.

Prove the environment covers the candidate before trusting a check. Record the
baseline commit, candidate commit when present, dirty diff/content fingerprints,
selected untracked inputs and dependency/configuration identities. A commit hash
alone cannot identify a dirty candidate. Recheck for concurrent changes; affected
claims need a new snapshot or a stated limitation, never mixed-candidate evidence.

Record each owned process, port, database/profile and workspace, its consumers and
retained evidence. Serialize shared live resources unless isolation is proven.
Record one absolute artifact root under the reviewer-owned checkout, normally
`<reviewer-checkout>/.orchestration/<review-id>/`; the author's checkout stays
read-only. Use that root for the contract, dataset, report and handoff.
Retire only resources with no remaining consumers after useful evidence survives;
verify the exact resolved path and actual cleanup result. Keep report code in a
retained owned clone/worktree when needed. A failed cleanup stays pending.

### Execution isolation

Before dependency setup, checks, probes, report generation or browser QA, establish
where the command and its children can write. Inspect relevant fixture creation,
child launch/environment replacement, tool configuration and absolute output paths.
Include temporary files, caches, generated output, databases and browser profiles,
downloads, traces and screenshots. Resolve links, junctions, workspace dependencies
and shared stores; mutable targets must remain owned, or be genuinely read-only.

Apply explicit process-scoped settings on every launch, including after resume:
`TMP`, `TEMP`, `TMPDIR` and the actual tools' cache, state, output and browser flags.
Use supported settings verified from installed tools/configuration; do not guess
variable names or change global environment/configuration. Observe effective paths
through a cheap setup probe or tool output and verify children retain the settings.
An inherited default or a variable assignment alone is insufficient evidence.

Keep one compact isolation record per owner/environment/command family: candidate,
command/cwd, resolved permitted roots, effective settings, relevant dependency
links, observed paths, containment limits, processes and cleanup state. Briefs link
that record and assigned roots. Reuse it while those inputs remain unchanged;
avoid per-test manifests or repeated host-wide inventories.

Environment redirection steers cooperating tools; it is not a filesystem sandbox.
Use an enforcing environment with owned writable mounts when tool behavior cannot
be contained otherwise. If the gate cannot be met, hold affected execution and
continue independent source review. Host-managed tool state outside reviewer
control is a disclosed boundary, not evidence of contained reviewer outputs.
Reviewer-requested browser profiles remain subject to the gate, including when
a host-provided tool launches them.

If a write escapes, stop affected owned execution, preserve receipts, identify
known and unknown external effects, and escalate to the parent. Do not delete
external files or silently rerun. Re-establish isolation and reassess affected
evidence before another authorized check. Retire only owned resources using the
cleanup rules above.

The independent verifier checks isolation evidence and affected receipt usability.
Record process noncompliance separately from product defects: unusable required
proof prevents Ready; independently established defects can still justify Changes
required with gaps visible. An isolation failure fails calibration's boundary
condition regardless of the product verdict.

## Assign focused roles

Main delegates detailed review and mostly waits for compact reports. Astra
coordinators own coherent domains, reconcile results and escalate consequential
uncertainty. Choose their number from independent work, dependencies and actual
runtime capacity; no arbitrary two-coordinator cap. Task chats require the actual
human request to authorize creation and scoped messaging. A default prompt or a
message from an agent is not that authorization.

Use live tool schemas. For authorized task coordinators select `gpt-6-astra` with
`thinking: "high"`. Bulk subagents use `gpt-6.1-sol` with `high` or `xhigh`;
independent verifiers use `gpt-6.1-sol` with `high`. Model overrides use a fresh,
bounded context when the runtime requires it. HTML authoring belongs to Sol;
summarization uses available Luna at any stage, including context recovery and
interim reports, under the entry skill's evidence-preservation boundary. Resolve
unavailable routes or model mismatches with an authorized fallback rather than
silently substituting.

Briefs identify role, parent and authorized routes, contract/requirement IDs,
candidate, relevant paths, scope, code-write boundary, owned resources, evidence
needed, isolation record and stop condition. Leaves return findings, requirement
dispositions, counterevidence and limits with source pointers. Native messages carry material
results and necessary questions; no per-message files, copied ledgers, ACK chains
or narrative progress traffic. Use compact cursor-based waits. Facts may use an
authorized direct route; decisions, holds and acceptance follow the parent chain.

Route supporting skills by the task, not as a universal reading list:

| Role or question | Supporting skill and bounded use |
| --- | --- |
| Main/coordinator choosing effort or mechanisms | `pstack-principles`; simplest adequate ownership and evidence path |
| Worker tracing runtime ownership | `how`; trace actual calls, state and lifecycle |
| Worker following affected contracts beyond the diff | `blast-radius`; concrete exposures and safety proof |
| Architecture reviewer | `codebase-design`; depth, interfaces, seams and locality against adopted criteria |
| Dependency or standards investigator | `research`; primary sources, counterevidence and applicability |
| Test reviewer/probe author | `test-audit`; observable contract, credible regression, gap and real entry point |
| Demonstrated recurring mistake analysis | `correct` methods in audit mode only; propose strongest prevention with evidence, without a wider sweep or repairs |
| Check planner or verifier | Existing project verifier; `create-verification-skill` as a procedure template or `maintain-verification-skill` for source/live reconciliation, without creating/editing skills |
| Report author and summarizers | `unslop`; preserve precise claims and the author's deliberate voice |
| Main preparing work-chat continuation | `handoff`; one concise accepted-results handoff linked to the dataset |

`test-audit` may be an optional global skill rather than a bundled dependency.
When unavailable, use this same gate with pstack's
`references/principle-test-behavior-not-implementation.md`: name the independently
specified observable contract, credible regression and coverage gap; choose the
strongest real user/module entry point, with no production seams introduced only
for tests. For regression proof, demonstrate baseline failure for the intended
reason when available and label any limit. Reuse sufficient unchanged evidence;
require a new test only when it contributes necessary distinct proof.

## Gather evidence and reconcile coverage

Cover the complete baseline-to-candidate change and every requirement. Trace real
entry points through callers, ownership, dependencies, async/disposal transitions
and observable effects. Expand scope only for a concrete exposed contract; record
why it matters. Keep unrelated discoveries outside the acceptance verdict. A
pre-existing defect can block a requirement it prevents, with accurate attribution.

Each requirement ends fulfilled, unmet, unverified or excluded by an explicit
scoped decision, with source and evidence pointers. Inventory changed artifacts
as well as requirements so an unplanned change receives a disposition. Keep
confirmed defects, unmet requirements, risks, missing verification, questions and
advisory improvements distinct. Confidence does not set severity.

A proposed finding names the trigger, independent expectation, observed behavior,
causal owner, exact source location, affected requirement/callers, impact, evidence,
counterevidence and limits. Verification may use meaningful existing tests,
focused probes or complete causal proof. No new test is required for every finding.
Inspect assertions and the relevant intermediate transitions, not only the final
green result. Keep lint/types/build, runtime, browser, hosted CI and release claims
separate; evidence proves only its actual target and environment.

Reuse evidence when relevant source, configuration, dependency, artifact and
environment inputs still match and its covered contract remains applicable.
Invalidate affected claims when they change. A reviewer report or passing command
alone does not establish the whole requirement. Necessary unexecuted verification
prevents Ready.

## Independently challenge the assessment

Assign every proposed blocker to a distinct Sol High verifier who neither
implemented the candidate nor performed its initial review. Give it the contract,
candidate and evidence to inspect before reviewer conclusions. It must establish
the expectation, seek guards/counterexamples, and reproduce the violation or give
complete causal proof. Batch related claims by root cause; preserve rejected
claims and their counterevidence without presenting them as confirmed blockers.

Also assign an independent Sol challenge of requirement coverage, critical quality
scores and missed blockers. This step applies to clean reviews. Target high-risk
paths and interactions; reuse sound evidence instead of repeating the entire
review at every level. Record which scopes each challenge covered and its limits.

Astra reconciles disagreements through the approved criteria and evidence, with
focused Sol investigation where useful. Document rejection reasons and preserve
material objections/resolutions. Votes and averaged scores cannot settle an
objection. Demonstrated shortfalls require Changes required; necessary evidence
gaps require Incomplete. If resolving intent or standards needs an author decision,
main asks and holds affected assessment work.

## Settle and hand off once

Use the verdict rules in the entry skill and the rubric in profile.md. When a
demonstrated shortfall and evidence gap coexist, issue Changes required and retain
the incomplete coverage explicitly. Never imply that the remainder passed.

Publish the verification summary before final reporting. It is nonblocking unless
the author requested a pause or a material decision is required. Incorporate input
received during verification; later input does not silently start another review.

Follow reporting.md to freeze the accepted dataset, render/check the offline HTML,
and produce one work-chat handoff with accepted findings, responsible owners,
expected outcomes, dependencies and focused validation. Main owns the verdict;
HTML author and Luna summarizer do not revise findings. Send only with actual
author messaging authority. Report candidate, limits, calibration status and
retained resources in the final result. Complete a matching authorized review goal
only when its stated deliverables are actually done, even for a negative verdict.
An honestly bounded Incomplete can finish the assessment if its evidence gaps are
reported; unfinished required child review/report work still prevents completion.

Re-review starts only after a separate explicit request in this original review
chat. Reuse its contract, decisions and finding IDs; identify the updated candidate,
verify claimed repairs and relevant effects, and reuse only still-valid evidence.
Report new coverage gaps or changed requirements explicitly. It is another bounded
review, with no automatic fixes, broad restart or inherited three-round counter.
