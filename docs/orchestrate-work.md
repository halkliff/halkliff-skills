# Orchestrate-work

These diagrams summarize the [skill](../skills/orchestrate-work/SKILL.md).
The [goal lifecycle](../skills/orchestrate-work/references/goals.md),
[uncertainty protocol](../skills/orchestrate-work/references/uncertainty.md), and
[communication protocol](../skills/orchestrate-work/references/communication.md)
define the detailed behavior. Update the affected diagrams when those rules change.

The main view uses one node per role. Each Sol owns a workstream and its own Luna workers. Separate Sol tasks require an explicit request; otherwise the workflow uses subagents. Worker counts follow the actual runtime capacity.

Substantial execution goes to Luna by default. Sol delegates research,
implementation, tests, and documentation while retaining coordination and review.
Astra and Sol record a bounded exception before substantial direct execution;
they queue work when Luna slots are full. See the skill's
[Luna-first execution rule](../skills/orchestrate-work/SKILL.md#luna-first-execution).

## Workflow

```mermaid
flowchart TB
    author([Author])
    definition["define-goal<br/>Scope + acceptance criteria"]
    astra["Astra · GPT-6 High<br/>Contracts · integration · acceptance"]
    sol["Sol · GPT-6 High / xHigh<br/>Coordinate · verify"]
    luna["Luna · GPT-6 Max<br/>Research · summarize · implement · test"]
    acceptance{"Acceptance met?"}
    complete([Complete])

    author -->|Invoke| definition
    definition -->|Defined objective| astra
    astra -->|Task contracts| sol
    sol -->|Bounded briefs| luna
    luna -.->|Artifacts / questions| sol
    sol -.->|Review / escalation| astra
    astra -->|Integration checks| acceptance
    acceptance -->|Yes| complete
    acceptance -->|Remaining work| astra
    astra -.->|Unresolved: hold + ask| author
    author -->|Decision: revise + resume| astra
```

Astra creates or reuses a top-level goal only when explicitly requested. Acceptance means every requirement has current evidence, no questions remain unresolved, and no required child work remains. Until then, Astra dispatches ready work and keeps affected dependencies on hold.

## Uncertainty and scoped holds

```mermaid
flowchart TB
    doubt["Luna is uncertain"]
    localHold["Stop the affected assignment<br/>Preserve work · send question + evidence"]
    sol{"Can Sol resolve it<br/>from the contract + evidence?"}
    astra{"Can Astra resolve it<br/>with accepted decisions + bounded research?"}
    hold["Hold affected work + dependents<br/>Send stop requests · track stopped ACKs"]
    author["Ask the author immediately<br/>Do not wait for every stop ACK"]
    answer["Record the answer + its authority<br/>Revise affected contracts and evidence"]
    resume["Sol applies the revision and briefs workers<br/>Resume only work whose holds are resolved"]
    independent["Continue already-authorized independent work<br/>Only when independence is established"]

    doubt --> localHold --> sol
    sol -->|Yes: evidence-backed answer| answer
    sol -->|No: escalate and hold dependents| astra
    astra -->|Yes: evidence-backed answer| answer
    astra -->|No, or an author choice is missing| hold
    hold --> author
    hold -.-> independent
    author -->|Explicit guidance| answer
    answer --> resume
```

## Artifact handoffs

```mermaid
sequenceDiagram
    participant LA as Luna A
    participant SA as Sol A
    participant A as Astra
    participant SB as Sol B
    participant LB as Luna B

    LA->>SA: Versioned artifacts + checks + questions
    SA->>SA: Inspect artifacts and independently verify
    SA->>A: Reviewed manifest + exact artifact revisions
    A->>A: Check evidence, acceptance and dependency effects
    A->>SB: Relevant artifacts + revision + requested action
    SB->>SB: Check access, authority, revisions and holds
    SB->>LB: Apply relevant changes to the worker brief
    SB-->>A: Applied ACK with evidence
    Note over SA,SB: Markdown is the durable record. Native messages notify recipients
    Note over A,SB: Receipt, application, acceptance and integration are separate states
```

All roles apply pstack-principles and unslop. Published Markdown messages and artifacts are versioned; native notifications point to the exact records. A worker being ready does not mean its work has been accepted or integrated.

Goal continuation remains subject to actual runtime and budget limits. A scoped execution hold is distinct from the goal tool's paused or blocked status. An explicit goal pause stops all goal work, including otherwise independent assignments.

Edit the Mermaid blocks in this document directly. GitHub renders them in the
Markdown preview; no image export or plugin is required. The blocks leave theme
selection to the renderer.
