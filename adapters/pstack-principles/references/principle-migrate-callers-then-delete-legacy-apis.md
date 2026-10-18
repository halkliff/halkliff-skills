# Migrate Callers Then Delete Legacy APIs

When introducing a replacement internal API, migrate its callers and delete the old API in the same change wave. Avoid compatibility layers that preserve both paths when no external consumer needs them. Coordinate the migration within the user's authorized scope.

- Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details

**When this applies:**
- No external users depend on backward compatibility
- The project can absorb coordinated breaking changes
- The new API is part of a simplification or refactor initiative
