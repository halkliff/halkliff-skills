# Skill mechanics in Codex

The skill-specific branch of [SKILL.md](SKILL.md): discovery, invocation policy,
and splitting workflows. Keep the general writing guidance in the main file.

## Invocation

Keep a valid `name` and `description` in every `SKILL.md`. The description tells
the agent or author what the skill does. For automatically discoverable skills,
make it a concise pointer to the actual circumstances that require the workflow.

When the author explicitly wants a user-invoked skill, set its policy in
`agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: false
```

This is the Codex invocation setting. Keep existing interface metadata and other
policy fields. Do not rely on another client's `disable-model-invocation` field
to control Codex, or remove the required description. Use the current
`skill-creator` guidance when authoring metadata.

A user-invoked orchestrator can delegate bounded assignments that follow its
instructions within that explicitly requested run. This does not authorize an
unrelated agent to launch the orchestrator automatically. Distinguish loading a
shared reference from invoking a new workflow with its own side effects.

## Splitting workflows

Create a separate discoverable skill only when it has a distinct use that the
agent should recognize independently. Shared reference can live in a Markdown
file linked from the skills that need it; it does not need its own skill trigger.

If several explicit workflows need a common entry point, a small router can help
the author choose one. Preserve each workflow's authorization and invocation
policy. A router is not permission to launch every workflow it mentions.
