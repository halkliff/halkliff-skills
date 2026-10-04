---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Use the user's requested destination; otherwise save a uniquely named Markdown file in the OS temporary directory, not the workspace. On Windows, resolve it with `[System.IO.Path]::GetTempPath()`. Return a clickable absolute path.

Include a "suggested skills" section naming relevant installed skills and why the next agent should use them. Use native `$skill-name` invocations and paths to their `SKILL.md` when useful; do not invent a Skill tool or assume unavailable skills are installed.

Capture the user's goal and permissions, accepted decisions, rejected alternatives with load-bearing reasons, current workspace and dirty-file boundaries, completed versus unverified work, exact verification commands and observed results, blockers, and the next concrete steps. Do not invent decisions or call a worker's report verified without checking it. Tailor the level of detail to what the next agent actually needs.

Creating a handoff does not authorize starting or messaging another chat, sharing it externally, scheduling work, staging, committing, or publishing.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact API keys, passwords, tokens, and unnecessary personal information. Retain only the context needed for the authorized handoff; never reproduce secrets from logs or environment files.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
