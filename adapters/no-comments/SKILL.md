---
name: no-comments
description: Review comments in a diff and remove comments that restate code, narrate phases, or defend our implementation. Keep only comments that encode a real external constraint or non-obvious reason.
---

# No comments

Review comments in the requested files or current diff. Do not delete comments
merely because they are short. Delete comments that become misleading,
duplicate the code, narrate obvious steps, or preserve a workaround that the
code can express directly.

## Workflow

1. Establish scope from the user's files, diff, or working tree.
2. Classify each comment as explanatory, constraint-bearing, stale, redundant, or misleading.
3. Keep comments only when the reason cannot be made clear through types, names, structure, tests, or a narrow runtime check.
4. For a claimed external constraint, verify it with the relevant source, type, runtime behavior, test, or CI rule when practical.
5. Remove the smallest set of comments that no longer earn their place.
6. If the review reveals a code defect, report it separately. Change code only when the user requested implementation or the surrounding workflow authorizes it.

## Report

Give the scope, deletion count, comments retained and why, comments restored
and why, constraints that remain unenforced, and any open code work. Do not
pretend a comment review proved runtime correctness.
