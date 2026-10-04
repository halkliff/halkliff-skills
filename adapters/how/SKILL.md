---
name: how
description: Explain how a subsystem works, trace runtime flow, or decide where code belongs. Use for code walkthroughs, ownership, layering, and architecture questions. Use why for motivation and history.
---

# How

Explore the actual codebase and produce a working mental model for a senior
engineer joining the area. Explain enough to build or change the subsystem,
not an annotated copy of the source.

## Workflow

1. State your best interpretation of the question and its scope. Do not stop for clarification when the repository can answer it.
2. Anchor the investigation in real entry points, symbols, types, and files.
3. For a simple question, trace one complete path from input or trigger to output or effect.
4. For a complex question, divide exploration into two to four distinct slices such as data model, request path, configuration, and side effects. Use available parallel workers when they materially help. If they are unavailable, explore the slices sequentially. When uncertain, start with the simple path.
5. Read the actual callers, callees, type definitions, tests, and relevant configuration. Do not infer behavior from filenames.
6. Reconcile the evidence yourself. Do not pass through raw worker reports.

## Output

Adapt the sections to the question:

- Overview. What the subsystem does and why the reader should care.
- Key concepts. The types, services, boundaries, and state that matter.
- How it works. The trigger, call path, data flow, decisions, and effects.
- Where things live. The smallest useful map of files and directories.
- Gotchas. Surprising behavior, lifecycle edges, and common misconceptions.

Reference real file paths, line numbers, and symbols when available. Separate
observed behavior from inference. If the repository does not establish a
claim, say so.

## Critique mode

This is a retained local extension. Upstream how now focuses on explanation.
Use critique only when the user asks for architectural evaluation.

When the user asks whether the architecture is good or what should change,
explain the current design first. Then inspect it from independent angles such
as ownership, lifecycle, data flow, failure handling, and maintainability.
Categorize findings as act on, consider, noted, or dismissed. Do not turn a
style preference into a defect.

Read the supporting prompt references only when the corresponding detailed
exploration or critique mode needs them.
