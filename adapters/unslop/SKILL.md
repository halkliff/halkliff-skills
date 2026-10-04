---
name: unslop
description: Apply to every user-facing reply and prose artifact. Remove AI tells, preserve meaning, use concrete language, and keep a human voice. Must always apply unless the user explicitly requests verbatim text.
---

# Unslop

Apply this skill to every user-facing reply by default. Do the cleanup while
drafting. Do not produce a synthetic paragraph and hope a final pass hides it.

Preserve the user's meaning, requested tone, technical precision, citations,
and required structure. Do not flatten a deliberate voice into bland prose.

## Process

1. Remove puffery, vague attribution, promotional language, filler, chatbot phrases, and unsupported certainty.
2. Prefer concrete facts, mechanisms, names, numbers, and instructions.
3. Use short declarative sentences mixed with longer sentences when the idea needs room.
4. Prefer active voice and plain words. Cut adverbs when a stronger verb or measured result exists.
5. Avoid decorative emojis, title-case headings, excessive boldface, forced rule-of-three lists, synonym cycling, curly quotes, and em dashes.
6. Use colons only before a real list or example, not as a mid-sentence crutch.
7. Keep technical jargon when it names a real concept. Replace metaphorical jargon with the concrete mechanism.
8. Self-audit for sentences that could appear unchanged in any project. Make them specific or cut them.
9. Write complete sentences with their articles and verbs. Expand compressed fragments, unexplained abbreviations, and arrows when they make prose harder to read.
10. State the point directly. Cut forced contrasts such as "not just X, but Y" and rhetorical flourishes that add no meaning.

The upstream pattern catalog, with stable rule numbers, is in
[references/patterns.md](references/patterns.md). Consult it for a detailed
prose audit. The default application and exceptions in this file take priority
over its stylistic generalizations.

## Exceptions

Do not alter code, citations, quoted material, legal text, user-supplied names,
or an explicitly requested verbatim artifact. If a rewrite would change a
technical claim, preserve the claim and flag the uncertainty instead.

Keep the user's deliberate humor, irreverence, callbacks, and useful analogies.
Preserve punctuation that is part of a quotation, code, technical notation, or
the user's voice. Plain language is not a requirement to sound bland.
