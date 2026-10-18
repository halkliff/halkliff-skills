# Guard the Context Window

Keep bulk outputs outside the main conversation when possible; use bounded queries and summaries. Route separable work to available workers only within the assignment's delegation permissions. Keep context needed on every invocation in the entrypoint and disclose branch-specific detail through references.

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
