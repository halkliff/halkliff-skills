# Type System Discipline

Make the compiler reject impossible states, mismatched primitives, and unhandled variants. Prefer defining errors and special cases out of existence over proliferating handlers. This reference is self-contained; it does not require the uninstalled `typescript-best-practices` skill.

- **Construct valid states.** Model alternatives explicitly instead of using contradictory optional fields. Build a non-empty list from a head and a rest, or a valid time range from a start and a duration. Strengthen types where an operation would otherwise be partial, not merely for precision.
- **Prove rather than assert.** Validate and narrow external values. Do not bypass a missing proof with an unchecked cast. A semantic brand should come from validation, not an assertion that assumes the invariant.
- **Exhaust alternatives.** Make a new variant produce a compile-time error at unhandled matches. Derive types from the source that owns the shape.

- **Brand semantic primitives.** `UserId` and `OrderId` are strings underneath but should not be interchangeable. Give each its own type, such as a branded intersection in TypeScript or a newtype elsewhere. Validate once at creation, trust the type downstream. If two arguments share a primitive type but mean different things, brand them.
- **External data is untyped until parsed.** RPC payloads, JSON, IPC messages, CLI args, config files, environment variables, database rows. Have a parse function at every boundary that turns unstructured input into the typed model. [Boundary discipline](principle-boundary-discipline.md) says where to put validation.
- **Derive types from authoritative schemas.** When a protocol buffer, OpenAPI spec, GraphQL schema, database migration, design-token file, or another file owns a shape, derive from it instead of hand-rolling a parallel type. See [Encode lessons in structure](principle-encode-lessons-in-structure.md).
