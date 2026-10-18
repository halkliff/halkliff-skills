---
name: create-verification-skill
description: "Create a repository-local skill to launch, health-check, drive, and verify the real app, with a user-facing feature map and retained evidence. Use when the user requests a verification or control skill for a project."
---

# Create a verification skill

Generate a project-local skill that drives the real app through its users' entry points and captures evidence. Use `.agents/skills/verify-<app>/` for a new Codex repository skill, or the user's requested supported destination. Inspect existing skill locations and conventions first; preserve an established location rather than creating a duplicate. Write for an agent reading the procedure cold, mid-task, without prior app knowledge.

This request authorizes the verification skill, its feature map, and scoped verification helpers, not unrelated product fixes, migrations, dependency installs, commits, publication, new chats, or schedules. Preserve dirty files and frozen expectations. Inspect a conflicting existing verifier before proposing edits. Read the installed `skill-creator` and `writing-for-agents` guidance before authoring; use `test-audit` when authoring or modifying tests. Discover native tools rather than assuming another client's commands exist.

## 1. Interview the repo, not the user

Answer these from the codebase and only ask the user what you cannot observe:

- **Surface:** what does a user actually touch? A web UI, a CLI/TUI, a desktop app, an API, a mobile app, a library? A repo can have several; pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (package scripts, Makefile, README quickstart). Note ports, env vars, seed data, auth.
- **Drive:** how can an agent interact with it programmatically? Existing Playwright/Cypress specs, PTY helpers, HTTP endpoints, or documented debug interfaces first. Then choose an available native browser, terminal, or HTTP tool. Verify tool availability; do not require tmux, Bash, or a particular browser helper on Windows.
- **Observe:** what evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, DB state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to double-drive a shared instance beats corrupting the user's session.

If the checkout does not build or start as-is, report the exact blocker. Repair product code or dependencies only when the user authorizes that scope. Clearly owned disposable verification fixtures may be created and cleaned up when safe; record them and preserve all user data. Never teach an unexecuted workaround as a verified launch procedure. A useful incomplete skill may be handed off as a draft with the blocked steps named.

## 2. Generate the skill

Write the chosen repository-local `verify-<app>/SKILL.md` with native YAML frontmatter (`name: verify-<app>` and a discriminating description) and the sections below. Read any needed supporting authoring references yourself. Use concrete observed procedures, not unresolved placeholders or invented commands; identify missing facts as blockers.

- **Launch:** the exact host-native command and observable readiness check. Reach a usable disposable instance, including supported initialization and seed data; a process answering is not enough. If an empty data directory is unsupported, document the actual isolated setup and unmet assumptions rather than adding product behavior. Include teardown. For a short-lived CLI/TUI, prepare its runnable artifact once and use a separate isolated terminal invocation per drive. Installing dependencies or running migrations outside disposable state requires the corresponding authority.
- **Doctor:** one read-only check that answers "is this instance worth driving?" — process up, right version/build, port owned by us, auth valid. An agent runs this first whenever anything looks off.
- **Drive:** the harness recipe with real selectors/commands from this repo, not examples. Prefer stable handles (ARIA labels, data attributes, prompt strings, route paths) over coordinates and tab order.
- **Evidence:** what to capture for a proof and where it goes. State the proof standards: exercise the real user path, not internal setters or test-only endpoints; capture the action and the resulting state, not just the final screen; verify side effects (files written, rows inserted, messages sent) alongside what's visible; mocks only where a production boundary already isolates the external system. When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name: some dry-runs still touch the network or open a browser.
- **Cleanup:** identify the exact processes and scratch paths owned by the run, verify path containment before recursive cleanup, and tear down only those resources. Never kill by process name or terminate the user's existing instance. Keep evidence outside removable scratch state and confirm it survives cleanup.
- **Helpers:** any script the skill ships is executable and its invocation is shown in the skill body. A helper the reader has to reverse-engineer is not a helper.

## 3. Seed the feature map

Create `features/README.md` and feature files inside the chosen verifier directory. Start with the most important identifiable user-facing features, often three to five, and state that initial coverage scope. Follow the shape in [the feature-map example](references/feature-map-example/README.md), adapting its fictional app, commands, and paths to this repository. Each file describes the feature, user entry points, actual driving commands, observable results, prerequisites, and gotchas. Keep its four H2 sections: `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. Missing prerequisites are recorded as blocked or unreachable with evidence; never weaken a frozen journey or expectation to make a run pass. One convenient entry point does not prove the others.

## 4. Prove the generated skill before handing it over

Within authorized resources, execute launch, doctor, one mapped user journey, evidence capture, and cleanup. One journey proves that procedure, not the whole feature map. Confirm the evidence still exists afterward. Repair only the verifier's own procedures and helpers; report product failures separately. Clean up each failed iteration's owned resources. Run native structural validation and check resource links, but do not substitute those checks for driving the real app. An unexecuted generated procedure remains a draft. If a stand-in differs from the real target, list the differences and leave target-specific steps unverified. Redact secrets from captured output and artifacts.

## 5. Offer the maintenance loop

Point the user at [maintain-verification-skill](../maintain-verification-skill/SKILL.md) for keeping the map honest. Scheduling or recurring runs require the user's request and native automation tools; installing or invoking this generator creates no schedule.
