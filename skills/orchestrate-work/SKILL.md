---
name: orchestrate-work
description: Explicitly invoked personal workflow for Astra orchestration, Sol workstreams, and Luna workers, with define-goal, uncertainty escalation, artifact handoffs, and unslop.
---

# Orchestrate work

Run only when the author explicitly invokes this skill, including delegated
assignments within that invoked run. Do not select it automatically for an
ordinary task, a complex project, or a generic mention of agents or goals.

Use a small team to deliver the user's outcome. This skill requests delegation
for substantial independent work. It does not expand the user's scope or authorize
external actions. Apply `pstack-principles`; load other skills only at the role
and point where they change the work. Use [CONTEXT.md](CONTEXT.md) when defining
task contracts or resolving terminology; it is the vocabulary, not a second spec.

## Decision authority and uncertainty

Agents must not fill any gap with an assumption. Act only on explicit requirements,
verified evidence, or choices explicitly delegated by the task contract. If an
agent is doubtful about what to do, what a requirement means, or whether evidence
establishes a needed fact, stop the affected work and escalate immediately:
Luna to its Sol, Sol to Astra, and Astra to the author when research cannot resolve
it. Seniority and confidence are not evidence or permission to invent a requirement.

Before dispatch, read [uncertainty.md](references/uncertainty.md). Include the
escalation route, contract revision, and stop/resume protocol in every brief.
At an unresolved Astra escalation, immediately hold affected work and its
dependents, ask the author, and await guidance for those assignments. Continue
unrelated authorized work only when its independence is established and recorded;
uncertain independence means hold and escalate. Cooperative stop requests with
acknowledgment tracking are accepted. Preserve work and report pending stops.

## Begin with define-goal

Before substantive orchestration, Astra must read and execute `define-goal`, then
follow [goals.md](references/goals.md). Establish the outcome, scope, acceptance
evidence, and uncertainty stop rule before implementation assignments. Resolve
definition gaps first; do not substitute an informal plan for this entry step.
If the skill is unavailable, report the missing prerequisite instead of silently
inventing a replacement. Astra alone owns the top-level goal; Sol and Luna receive
bounded assignments. Creating a goal still requires an explicit user request for
goal-backed execution; drafting this workflow is not such a request. Continue
authorized execution until every requirement has current acceptance evidence,
subject to applicable holds and actual runtime limits. An explicit user request
for goal-free work takes precedence.

## Required prose pass

Every role must read and apply `unslop` when authoring prose. Apply it while
drafting and before publishing briefs, messages, research, implementation reports,
documentation, or replies to the author. Preserve quotations, citations, technical
meaning, code, and required schema fields. Parent review includes the prose itself;
an "unslop applied" label is not evidence of readable writing. Correct prose issues
within existing review instead of spawning another reviewer for every message.

## Roles and scale

| Role | Model / effort | Owns |
| --- | --- | --- |
| Orchestrator | GPT-6 Astra / high | Outcome, architecture, shared contracts, workstream boundaries, final acceptance |
| Coordinator | GPT-6 Sol / high | Task briefs, Luna assignments, artifact review, workstream integration and documentation |
| Difficult coordination | GPT-6 Sol / xhigh | Ambiguous interfaces, difficult diagnosis, unresolved contradictory evidence |
| Worker | GPT-6 Luna / max | Bounded research, summaries, implementation, tests, and accompanying documentation |

Keep these model choices unless the user changes them. Treat Luna Max as the
chosen quality baseline, not a measured cost optimum. Workers are leaves.
Coordinators may spawn workers; they do not create more coordinator layers.

When the user explicitly requests separate task threads, use the task-thread
topology: Astra coordinates durable Sol tasks; each Sol delegates to Luna
subagents in its own task. Otherwise use subagents within the current task.
This skill alone is not an explicit user request to create sidebar tasks.

Complete small, tightly coupled work locally when delegation would add no useful
independent work. For substantial work, delegate one coherent workstream to a Sol
coordinator while the root resolves architecture, acceptance, or another useful
independent responsibility. In task-thread mode, start with two independent Sol
workstreams, increasing only when dependencies, integration capacity, and actual
usage permit. This is a tuning baseline, not a product limit. Add coordinators
only when each has separate ownership and enough capacity for its workers.
Explain any departure from a user-requested
mandatory hierarchy.

Before dispatch, read [runtime.md](references/runtime.md) and check the current
tools, model settings, and capacity. Within one subagent tree, count managers and
workers against the same tree limit. Separate tasks must inspect their own runtime
capacity; do not infer unlimited account concurrency. Allocate worker slots to each
coordinator explicitly. On a four-slot tree including the root, one Astra, one Sol,
and two Lunas fit. In a separate four-slot Sol task, Sol can potentially run three
Lunas; verify the actual limit there. Queue work beyond available capacity.

## Define work before dispatch

Astra owns one concise task ledger at the project's existing planning location,
or `work/orchestration/<task>/plan.md` when none exists. Record outcome, constraints,
acceptance criteria, shared interfaces, task dependencies, owners, state, and
evidence pointers, contract revision, open questions, and any execution hold.
In task-thread mode also record each Sol task ID, host, workspace,
base revision, integration owner, and last result cursor. Sol owns its workstream's task records. Workers own their
artifacts and result records. Keep one writer per record.

Before dispatch, read [communication.md](references/communication.md). Establish
one accessible coordination directory and a registry of task IDs, parent routes,
workspaces, dependencies, and artifact consumers. Publish immutable Markdown
messages and versioned artifacts there; use native agent/task messages to notify
recipients. Astra routes relevant Sol outputs to other Sol tasks with explicit
context, authority, and requested action. Files alone do not deliver notifications.

Use [task-contract.md](references/task-contract.md) to dispatch and accept work.
Split by independently verifiable outcomes, not arbitrary file counts or roles
such as "all tests" versus "all implementation." Each implementation task includes
the tests and documentation needed to establish its behavior.

Resolve shared interfaces before parallel implementation. Assign one owner for
shared configuration, lockfiles, public types, and integration edits. Preserve
existing dirty changes. Give separate Git task threads separate worktrees by
default, with an agreed starting state and integration owner. For overlapping edits, serialize work or use isolated
checkouts with an explicit integration owner and base revision. Isolation does
not resolve incompatible interfaces or copy uncommitted prerequisites for you.

For genuinely unknown design facts, Astra may dispatch an explicit research task.
State the question, evidence standard, and decision owner. A research assignment
authorizes gathering evidence, not acting on an unconfirmed hypothesis. Uncertainty
about the research assignment itself follows the same escalation protocol. Convert
accepted findings into a revised implementation brief before work resumes.

## Keep context small and sufficient

Start workers with a compact brief and exact artifact paths, using a fresh
conversation when the runtime supports it. Include relevant user decisions,
constraints, dependencies, and instructions explicitly. A fresh conversation still
has runtime overhead; do not describe it as zero context.

Give each role only the skills it needs. Read authoritative artifacts once per
decision, then send paths, findings, and changes rather than transcripts or full
logs. Reuse an agent for a correction or closely related task; start fresh when
the old context would obscure unrelated work. Keep result summaries short enough
to inspect, with full evidence on disk. Concision must preserve failures,
uncertainty, and instructions needed to reproduce the result.

For separate tasks, pass the outcome and contract explicitly; task creation does
not imply shared conversation history or automatic upward result delivery. Keep
the main task active to collect results, or use an authorized follow-up automation
when the user requests later monitoring. Use meaningful follow-ups and completion events. Avoid repeated status polling,
duplicate investigation, and idle narration. Target brief/results at roughly
300-600 words when practical; this is a reporting heuristic, not a token cap or
a reason to omit necessary evidence.

## Verify different things at each level

Luna proves its local behavior and returns artifacts, exact checks and outcomes,
source references for research, and unresolved issues. A worker's `ready` result
starts review; it is not acceptance.

Sol inspects the actual artifact against the brief. Check behavior, edge cases,
ownership, relevant callers, tests, and documentation. Run an independent check
that could disprove a material claim; reusing the worker's summary is insufficient.
For summaries and research, inspect consequential source passages and preserve
counterevidence. Mark the workstream accepted only when every criterion has
evidence and no unresolved assumptions, or explicitly report what remains unmet.

Astra verifies Sol's acceptance decisions against the user outcome, shared
contracts, and integrated behavior. Inspect consequential or risky changes
directly and run the required final integration checks. Avoid mechanically
repeating every local check when the existing evidence remains valid. Repeat
checks when integration or later edits invalidate them. If Sol materially changes
an implementation during review, Astra or an independent reviewer checks that
change before acceptance.

For corrections, return the failed criterion, concrete evidence, and required
behavior. After two unsuccessful corrections to the same issue, Sol diagnoses or
implements the fix, or escalates a contract decision to Astra. This changes the
method; it does not abandon required work. This retry rule applies only when the
contract and required behavior are already clear. Any doubt invokes the uncertainty
protocol immediately, without waiting for retries. Parent agents own finishing
failed or interrupted tasks once the relevant hold is resolved.

## Compose existing skills

- Astra: `define-goal` for the required entry step; `codebase-design` for module interfaces; `domain-modeling` for terminology
  and durable decisions; `grilling` only when the user requests that interview.
- Sol: `blast-radius` for concrete regression risks; `how` or `why` when runtime
  flow or historical intent matters; `writing-for-agents` for agent documents.
- Luna: `research` for sourced investigations and the relevant domain skill for
  implementation. `no-comments` when comment review is useful.
- `unslop` is mandatory at every role's publication step as defined above.

Read the selected skill through its available path. Do not load the whole catalog
or assume a separate Skill tool exists.

## Completion and tuning

Record delivered artifacts, acceptance evidence, unresolved limitations, and
decisions needed for continuation. Update canonical product/contributor docs where
behavior changed; keep orchestration logs out of permanent product documentation.
Complete a top-level goal only after Astra accepts the integrated result, resolves
every open question, and confirms no required child work remains active or unverified.

When tuning efficiency, compare completed tasks at the same acceptance bar.
Record wall time, agents spawned, retries, failed acceptance checks, and actual
per-agent usage when the runtime exposes it. Otherwise mark token/cost data
unavailable. Account usage percentages and word counts are not per-task token
measurements. Prefer the simplest topology that meets the quality bar. Change
the user's model/effort baseline only after proposing a measured alternative.
