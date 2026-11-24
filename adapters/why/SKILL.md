---
name: why
description: Investigate why code or a design was built this way. Use for design rationale, historical decisions, regressions, postmortems, rejected alternatives, and data-backed thresholds. Use how for runtime mechanics.
---

# Why

Investigate motivation and intent from evidence. Code explains what it does,
but usually cannot prove why it exists.

## Operating posture

- Collect evidence before writing the story.
- Cite every claim about intent with a commit, pull request, issue, document, chat message, code comment, metric, or other source.
- Label inference as inference. Prefer "appears to" or "suggests" when the evidence is indirect.
- Surface contradictions instead of smoothing them over.
- Report empty and unavailable sources as gaps.
- Do not invent access to an app, connector, or historical record.

## Workflow

1. Parse the target and the actual why-question.
2. Establish a code anchor with files and symbols. Read the introducing commit and PR discussion, then trace material later changes and their linked decisions.
3. Use issue trackers, documents, team chat, observability, error tracking, or analytics to fill gaps, resolve contradictions, or corroborate the record.
4. For a broad investigation, track the sources you searched and distinguish unavailable, searched-and-empty, and irrelevant sources. A null result does not prove a discussion never happened.
5. Compare the evidence against competing explanations.
6. Present what is directly supported, what is inferred, what remains unknown, and what constraints the next change should preserve.

## Output

- The question.
- The code in question.
- What we found, with direct citations.
- What we can reasonably infer.
- Competing hypotheses when needed.
- What we do not know.
- Sources consulted, including gaps and null results.
- Confidence summary, tied to the actual evidence rather than a numeric guess.

If the answer will guide a code change, finish with a concise Preserve,
Change, Avoid, and Risk constraint set.

Read the focused files under references/ only for the evidence source or
confidence framework needed by the current investigation.

Treat tool names in imported playbooks as examples. Discover the actual
available tools and use read-only queries. Investigators and synthesis do not
authorize repository or external writes. Prefer tracing older decisions over
assuming the newest commit explains the entire design.
