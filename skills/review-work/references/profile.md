# Personal review profile

This profile supplies review methods. The target project's approved contracts
determine which architecture and style rules apply. Confirm the applicable rubric
during setup; reuse adopted criteria and explicit exceptions. A new preference is
a proposed criterion, not evidence that earlier work violated its contract.

## Portable methods

| Review concern | Evidence to seek |
| --- | --- |
| Plan and decisions | Requirement-to-source mapping, amendments and settled decisions; ask only about the unresolved difference |
| Responsibility | Real state/semantic owner, caller contracts, appropriate adapters and dependency direction |
| Type claims | Information actually available at compile time/runtime; predicates validating the narrowing they promise |
| Defensive checks | Reachable state changes across callbacks, custom iterators, asynchronous work and disposal; rationale for repeated guards |
| Ordinary use | Optional/default inputs, partially entered values, retained state and the supported user syntax |
| Observable behavior | Whole relevant transition and unexpected intermediate states, through the actual user entry point |
| Coverage | Cold outcomes mapped to production owners, existing assertions and platform paths before proposing more checks |
| Proportionate verification | Changed contracts, valid reusable receipts, explicit exceptions and distinct value of each additional check |
| Authored assets | Editable source files for static programs/templates where appropriate; preserved generated, malformed, exact-byte, dynamic and source-location contracts |
| Readability | The project's configured formatting and scoped author conventions, with real conflicts made visible |
| Dependencies | Relevant installed source/types and actual provenance, maintenance, license and transitive exposure; popularity alone proves little |
| Documentation | Public instructions with their contract owner, operational records in their proper home, usable links and public vocabulary |
| Machinery and cost | Existing supported mechanisms, necessary helpers, bounded detail delegation and resource retirement with retained evidence |
| Output consistency | Concrete requested variation and fixed constraints; distinguish a changed preference from a prior violation |
| Exploration | The accepted premise retained while comparing alternatives; new requirements recorded as decisions |

Trace consequences before making architecture judgments. Use `codebase-design` to
ask whether a module hides useful behavior behind a small interface and keeps
knowledge local. A proposed seam needs something that actually varies. A pattern
name alone is not a defect; explain the caller or maintainer burden and the adopted
criterion it violates.

For demonstrated recurring mistake classes, prefer proposed prevention through
single ownership/architecture, then types or actionable checks, then meaningful
behavior proof, with prose reserved for residual judgment. This review proposes
outcomes; it does not implement enforcement. A proposed check needs a real former
failure it would catch and an accepted case it would preserve.

## Scope project architecture

Store adopted rules in the review contract with their source, revision and scope.
For each rule, name the affected package/layer, expected behavior, explicit
exceptions and suitable proof. Examples include transport versus application
authority, compiler/runtime responsibilities, web-standard baselines, golden
behavior expectations, package contracts and required browser/platform matrices.

Historical coverage percentages, release exceptions, formatting preferences and
platform workarounds do not transfer automatically to another project or revision.
Neither private planning names nor this profile's history belong in public product
docs. Link the target's public contract where its reader needs one.

## Quality rubric

Score 0-10 with an evidence-linked rationale, stating each criterion's applicability
and why its observed shortcomings matter. Default acceptance to **9/10 for the
overall score and for each acceptance-critical dimension**. Reuse author-supplied
thresholds. Record a dimension as inapplicable only with a scope reason; missing
proof is unverified, not inapplicable or an invented numeric score.

| Default dimension | What its score assesses |
| --- | --- |
| Correctness | Agreed behavior, edge cases, error paths and relevant lifecycle/integration contracts |
| Clarity and structure | Responsibility, interface depth, locality, complexity and maintainability under the project's adopted rules |
| Documentation | Accurate user/API guidance, ownership and coverage of the changed public contract |
| Testability and verification quality | Meaningful checks through real entry points, independently specified expectations and adequate evidence |
| Lint and formatting compliance | Applicable documented commands/configuration and scoped author conventions |
| Other adopted standards | Applicable security, accessibility, performance, portability or domain criteria agreed for this project |

Treat the applicable defaults as critical unless the approved rubric explicitly
makes one advisory. Add project-specific critical dimensions when an adopted
non-functional requirement needs them. Every requirement still needs a separate
evidenced disposition. A high score cannot conceal an unmet requirement or missing
check, and an overall average cannot hide a failed critical dimension.

Use the scale consistently: 0 means fundamentally absent or unusable; 5 means
substantial demonstrated deficiencies; 9 means the accepted criterion is met with
only optional refinements; 10 needs unusually strong evidence and a clear reason
above 9. Intermediate scores require comparable criterion-linked explanations.
Scores express assessment, not measured correctness or calibrated probabilities.

A below-threshold score needs a demonstrated shortfall against an agreed critical
criterion. Optional polish alone remains advisory and cannot justify a blocking
score. Keep severity, confidence and quality score separate. If evidence cannot
support scoring a critical dimension, record it unverified and issue Incomplete
unless demonstrated shortfalls already require Changes required.

Apply SOLID, DRY, KISS and similar principles according to the project's adopted
rules and concrete consequences. Neither universal abstraction preferences nor a
foreign toolchain are acceptance requirements.
