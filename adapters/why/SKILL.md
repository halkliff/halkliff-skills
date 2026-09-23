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
2. Establish a code anchor with files, symbols, relevant history, and linked change records.
3. Search the evidence sources available in this environment. These may include git history, pull requests, issue trackers, documents, team chat, observability, error tracking, and analytics.
4. Keep a coverage map. For every unavailable or searched-and-empty source, record that fact.
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

If the answer will guide a code change, finish with a concise Preserve,
Change, Avoid, and Risk constraint set.

Read the focused files under references/ only for the evidence source or
confidence framework needed by the current investigation.
