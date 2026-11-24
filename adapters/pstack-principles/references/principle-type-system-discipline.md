# Type System Discipline

Make the compiler reject impossible states, mismatched primitives, and unhandled variants.

- **Construct valid states.** Build a non-empty list from a head and a rest, or a valid range from a start and a duration. Strengthen the type where an operation would otherwise be partial.
- **Prove facts at the boundary.** Validate and narrow external values before giving them a semantic brand. Use an exhaustive check that exposes unhandled variants at compile time.

- **Brand semantic primitives.** If two arguments share a primitive type but mean different things, give each its own type. Validate once at creation.
- **External data is untyped until parsed.** JSON, RPC payloads, CLI args, config, environment variables, and database rows go through a parse function at the boundary that returns the typed model.
- **Derive types from authoritative schemas.** When a schema file owns a shape, derive the type from it instead of hand-rolling a parallel one.

For boundary parsing and ownership, see [Boundary discipline](principle-boundary-discipline.md).
