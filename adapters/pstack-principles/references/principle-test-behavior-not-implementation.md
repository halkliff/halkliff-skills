# Test Behavior, Not Implementation

A test is a claim about what users of the code can observe through its interface: return values, errors, state they can read back, and effects on outside systems. Private helpers, internal call order, and intermediate data are implementation.

Judge each test against two imagined edits:

- **Break the behavior** (a wrong value, a skipped or doubled effect). If the test still passes, it proves nothing. The usual causes are a loose assertion, an expected value computed by the code under test, and an assertion on data the test built itself.
- **Change the internals** and keep every observable result. If the test fails, it is pinned to the implementation.

Keep tests that catch the first edit and survive the second. Drive the code through its public interface with a concrete input and derive the expected value from the requirement. What an external service receives is observable behavior. Pair "this never happens" with a case that shows the check can observe it happening. Assert the error properties callers rely on.

An exact empty result, initialization effect, public threshold, cross-record invariant, or compile-time type check may be the contract. Follow `test-audit` when rewriting or removing tests, and preserve meaningful coverage.
