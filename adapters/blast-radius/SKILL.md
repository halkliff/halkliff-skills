---
name: blast-radius
description: Find what a change could break beyond the diff and prove the key safety fact with real code. Use for blast-radius questions, small diffs you do not trust, and pre-merge risk review.
---

# Blast radius

Find the breakage that a caller search will miss. The deliverable is not a
long list of plausible risks. It is the one or two facts the change is safe
because of, plus the risks that survive real inspection.

## Workflow

1. Read the diff, changed symbols, deleted behavior, and the behavior the diff does not spell out.
2. Find the central safety fact. If it holds, most scary cases should disappear.
3. Follow what symbol search misses: dependency source, pinned versions, wire formats, database columns, feature flags, teardown timing, and downstream consumers.
4. Give each remaining risk a real failure path, likelihood, cost, and evidence.
5. Prove the central safety fact with a focused test, script, or runtime reproduction that exercises the real code. Mark it unproven if you cannot reach that level.
6. Separate cleared risks from open risks.

Report the level reached for each decisive fact: a claim, a cited implementation,
a traced failure path, an executed check of real code, or a running-app
reproduction. A cited line or convincing trace is not executed proof.

## Output

- What changed, including non-obvious effects.
- The central safety fact and the strongest proof reached.
- Real risks with file and line evidence.
- Risks checked and cleared.
- The cheapest pre-merge test or reproduction.

Use the how workflow for mechanics and the why workflow for history or
intent when those questions are part of the review. Keep private information
out of any public writeup.
