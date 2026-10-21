---
name: review-work-plugin
description: Explicitly invoked adapter for the bundled review-work workflow and its local HTML report renderer.
---

# Review work

Use only when the author explicitly invokes this skill, including delegated
assignments within that review. Resolve `<plugin-root>` from this file's location:
it is the directory containing `plugin.json`, two directories above this skill
directory.

1. Read `<plugin-root>/support/skills/review-work/SKILL.md` and the references it
   calls for. Follow its setup, profile, review process, calibration, stopping
   rules, and acceptance requirements. Complete the core's execution-isolation
   gate before write-capable tools, including dependency setup and browser QA.
2. Load named dependencies from `<plugin-root>/support/skills/<name>/` by absolute
   path. Give delegated reviewers the bundled review core and their sufficient
   brief. The review profile takes precedence over any bundled orchestration
   defaults, including Luna assignments and the three-assessment limit.
3. Render the agreed report using the bundled helper. Read its usage with:

   ```text
   python <plugin-root>/support/skills/review-work/scripts/render_report.py --help
   ```

   Follow the core's reporting reference for the input schema, rendering command,
   output location, and verification. Link the resulting report and evidence.

The review core owns the workflow and any goal-mode choice. Do not create a goal
without the author's explicit request. The renderer runs directly; this workflow
does not require orchestration session activation or hook enrollment.
