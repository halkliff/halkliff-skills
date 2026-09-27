---
name: research
description: Investigate a question against high-trust primary sources and return complete cited findings. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Investigate the assigned question and return a complete, cited answer.

If you are already the assigned research worker, investigate directly. Otherwise,
delegate a bounded investigation only when the runtime and parent assignment
permit it and useful independent work can continue. Respect model, leaf-worker
and capacity constraints; loading this skill does not create recursive agents.

1. Use primary sources: official docs, source code, specifications, or first-party
   interfaces. Follow each claim to the source that owns it.
2. Return findings, citations, counterevidence, uncertainty and practical limits.
   Use a native reply for a bounded answer. Write one Markdown report when the
   findings are substantial/reusable or the task contract requests an artifact;
   give the parent the conclusion and absolute report path. Do not create a file
   merely to pass a message.
3. For reports, use the contract's output path or the established research location.
   Apply `unslop` to research deliverables and author-facing prose; routine internal
   exchanges need no separate prose pass.

An unclear assignment or evidence standard follows the parent's escalation
protocol. Research does not authorize a change in product requirements.
