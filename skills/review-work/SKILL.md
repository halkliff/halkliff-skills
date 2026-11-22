---
name: review-work
description: Explicitly requested independent implementation review with requirement evidence, verified findings, quality scores, and an offline report.
---

# Review work

Run once per explicit invocation. Assess the delivered implementation; explain
required fixes in a handoff. Perform no repairs. A re-review requires a separate
explicit request in this same original review chat.

## Establish the review

Read [workflow.md](references/workflow.md) before setup or dispatch. Recover the
approved plan, amendments, repository instructions, work-chat context and supplied
handoff. Check claims against source. Identify the baseline and actual candidate,
including dirty changes, before using implementation evidence. Ask only about
material gaps or contradictions that the available records cannot resolve.

Use [profile.md](references/profile.md) to confirm applicable review methods and
project criteria. Cover the whole change, every functional and non-functional
requirement, and its relevant blast radius. Keep unrelated discoveries separate.
Reuse accepted criteria; obtain author agreement before changing acceptance.

Reuse `orchestrate-work` setup, dispatch, uncertainty and resource lifecycle as
scoped in workflow.md. Apply the review's own defaults, workspace boundary and
single-assessment process. Loading those references starts no separate run.
Create a goal only on the author's explicit request.

## Route the work

Settle model and effort together during setup using the
[review roles and defaults](references/workflow.md#assign-focused-roles). Apply
explicit author choices within their scope. Create or message user-owned chats
only under actual human authorization. Keep the role's responsibility when its
model changes. Summaries preserve source pointers, candidate identity, evidence
limits and unresolved objections. Main and coordinators retain consequential
uncertainty and decisions.

## Review and challenge

Reviewers may write code only in their own clones or worktrees. This absolute
boundary includes temporary tests, probes, generated code and lint/format fixes.
Use the cheapest safe isolation that reproduces the candidate and protects the
author's checkout, application data and concurrent work.
Before any write-capable tool, complete the
[execution isolation gate](references/workflow.md#execution-isolation).
An owned working directory alone does not contain tool or child-process writes.

Trace real entry points, ownership, contracts and observable transitions. Apply
targeted skills by role using workflow.md; workers need only their brief and
relevant procedures. Use `test-audit` for meaningful tests/probes, reuse valid
evidence, and run focused checks when a material claim remains unsettled.

An independent verifier must verify every proposed blocker. It establishes the
expectation and tries to disprove the claim. Independent verifiers also challenge
coverage, scores and missed blockers, including a review with no findings. Complete
this challenge before Ready. Main and coordinators resolve disagreements from
evidence and agreed criteria. Preserve material objections and their resolution.

## Decide and report

Give every requirement an evidenced disposition. Score applicable critical quality
dimensions and overall quality from 0 to 10, defaulting each threshold to 9/10.
Every critical dimension and the overall score must pass. Advisory improvements
remain nonblocking; scores cannot compensate for unmet or unverified requirements.

| Verdict | Required basis |
| --- | --- |
| Ready | All requirements evidenced, required checks pass, critical scores pass, and no material objection remains |
| Changes required | A verified defect, unmet requirement or demonstrated critical quality shortfall prevents acceptance |
| Incomplete | Missing evidence, access, coverage or an unresolved material objection prevents a defensible decision |

Report shortfalls and evidence gaps together when both exist. No findings alone
does not establish Ready. Verdicts authorize no edits, commits, merge or release.

Publish a concise verification summary before the final report: proposed verdict,
scores, coverage, significant findings, objections, gaps and decisions. Continue
without waiting for acknowledgment unless the author requested a pause or a
material decision blocks completion. Investigate input received while verifying.

Follow [reporting.md](references/reporting.md) for the shared dataset, rich offline
HTML, source/requirement evidence and accepted-findings handoff. Explain possible
fix outcomes without implementing them. Send the handoff to another chat only
when the author authorized delivery.

Read [calibration.md](references/calibration.md) before calibration or any claim of
unattended reliability. Until a qualifying record exists, disclose **uncalibrated**;
Ready still requires the author's detailed re-review before reliance.
