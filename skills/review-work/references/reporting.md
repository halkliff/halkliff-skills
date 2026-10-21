# Evidence and report contract

Read this when consolidating findings, rendering the report, or preparing the
work-thread handoff. The reviewers establish claims. The helper validates recorded
consistency and renders escaped content with validated source navigation; it cannot prove evidence, coverage, scores,
agent independence, calibration, or ownership.

## Retain one assessment

Use the recorded absolute artifact root under a reviewer-owned clone or worktree:
`<reviewer-checkout>/.orchestration/<review-id>/`. All code-bearing outputs,
including HTML and temporary report scripts, stay within that owned checkout.
Retain the checkout while the deliverables or their evidence depend on it.

Keep one structured `review.json`, one offline `report.html`, and one concise
`handoff.md` for the assessment. Link existing source and check receipts. Store a
large reproduction only when it supplies necessary evidence. Native messages
carry routine coordination. Do not copy repositories, entire logs, or message
histories into report artifacts.

A separately requested re-review stays in the original review chat. Use new
candidate-specific filenames under the same recorded root, retaining prior
results and their identities. The helper refuses to replace different report
bytes. Reuse still-valid evidence and report what changed in the reassessment.

## Record the evidence

Every evidence string names its claim, source or receipt, relevant candidate,
environment, observed result, and limits as needed. Use exact file paths and line
numbers or immutable source links. To make a source navigable, supply an explicit
HTTP(S) URL or a local `file:///` URI as the complete source or evidence string.
The helper validates supported destinations and escapes the link text and
attribute. Ordinary paths and unsupported destinations remain copyable text.
Remote file shares and executable URI schemes are not source links.
Retain a verified report's supporting reproduction commands in the handoff.

Map every in-scope functional and non-functional requirement. State each adopted
criterion's authority in its description or evidence. Explicitly scoped exclusions
belong in the contract and decisions, not as unverified in-scope requirements.
Account for changed artifacts and relevant ownership/runtime paths in the change
summary and coverage evidence. Keep unrelated findings marked out of scope.

The dataset uses schema version 1. Every field below is required unless marked
optional. Strings are nonblank. Lists may be empty except `change_summary`,
`requirements`, and `dimensions`. Unknown keys, duplicate keys/IDs/names, dangling
requirement references, nonfinite scores, and boolean scores are rejected.

| Top-level field | Value |
| --- | --- |
| `schema_version` | Integer `1` |
| `title`, `candidate`, `baseline` | Strings. Candidate identifies the actual reviewed inputs, including dirty edits. |
| `change_summary` | List of strings describing introduced changes, affected owners, relevant runtime paths, and scope. Explain unavailable information. |
| `calibration` | Object with `status`: `uncalibrated`, `passed`, or `failed`; and `evidence`: list of record pointers. Passed/failed status needs evidence. |
| `verdict` | `Ready`, `Changes required`, or `Incomplete` |
| `overall_score` | Number from 0 to 10, or `null` for not assessed |
| `threshold` | Optional number from 0 to 10; default `9` |
| `requirements`, `dimensions`, `findings`, `checks` | Lists defined below |
| `verification` | Object defined below |
| `limitations`, `decisions` | Lists of strings. Include partial coverage, authority decisions, exceptions, and resource/reliance limits. |

Each requirement has `id`, `description`, `status` (`met`, `unmet`, or `unverified`),
and `evidence` (list of strings). A met requirement needs recorded evidence.

Each quality dimension has `name`, `critical` (boolean), `score` (0 to 10 or
`null`), `rationale`, and `evidence`. Optional `threshold` overrides the review
threshold for that agreed dimension. A numeric score needs evidence. An unassessed
dimension needs an explanation; it may have an empty evidence list. Every critical
dimension must meet its threshold. Advisory dimensions do not gate acceptance.
Explain the overall score in `verification.summary`, linking its rationale to the
dimension assessments and evidence. Scores are judgments, not measured accuracy.

Each finding has:

- `id`, `title`, `expected`, `observed`, `source`, `fix`, and `validation`: strings.
  Describe the minimum responsible fix outcome without implementing it.
- `kind`: `defect`, `plan_gap`, `risk`, `missing_verification`, `quality`, or
  `advisory`.
- `severity`: `critical`, `high`, `medium`, `low`, or `info`. Explain impact in the
  finding evidence; severity does not determine confidence.
- `confidence`: `confirmed`, `supported`, `provisional`, or `unknown`.
- `in_scope`, `blocking`, and `verified`: booleans. Confirmed confidence requires
  verification and evidence. Record the independent verifier's result and source.
- `requirement_ids`, `evidence`, and `counterevidence`: lists of strings. Refer only
  to existing requirements. Use evidence to retain the causal proof and rejected
  alternatives. An unrelated finding may have no requirement references.

Advisory and unrelated findings cannot be blocking. A risk is not a confirmed
defect. An unverified material concern prevents Ready while required evidence is
missing. Record rejected claims and resolved disagreements in verification
evidence or decisions; do not relabel them as confirmed findings.

Each check has `name`, `status` (`passed`, `failed`, or `not_run`), `required`
(boolean), and `evidence`. Completed checks need evidence identifying their target,
environment, result, and covered behavior. Keep local, browser, hosted, and release
claims separate.

Execution receipts follow the [isolation gate](workflow.md#execution-isolation),
including effective-path evidence and limits. Keep review-process noncompliance
separate from product findings and identify required proof it makes unusable.

`verification` has `complete` (boolean), `summary`, `evidence` (list of strings),
and `unresolved_material_objections` (list of strings). Optional `environment`
adds the actual verification environment. Complete verification needs evidence of
the independent blocker, coverage, score, and missed-problem challenges. Preserve
each material disagreement and the evidence for its resolution.

Record calibration honestly. A new installation is `uncalibrated`. A passed record
must cover the profile, models, runtime, and scope actually used. Renderer and
package checks do not establish calibration. Uncalibrated/failed reports require
the author's detailed re-review before reliance, including when the recorded
candidate verdict is Ready.

## Validate and render

Run the core helper using the actual installed skill path. In the plugin, the
core is `<plugin-root>/support/skills/review-work/`.

```text
python <core>/scripts/render_report.py <artifact-root>/review.json --check
python <core>/scripts/render_report.py <artifact-root>/review.json --workspace <owned-reviewer-checkout> --output .orchestration/<review-id>/report.html
```

`--check` writes nothing. Rendering needs an existing Git checkout root and a
relative `.html` output path inside it. The caller must establish ownership;
recognizing a Git checkout does not grant permission to modify it. The helper
rejects path escapes, `.git` output, symlinks/junctions, and conflicting files.
Identical bytes are safe to render again.

The helper refuses Ready when recorded requirements, scores, required checks,
verification, objections, or blocking findings contradict it. It preserves either
negative verdict and displays all recorded gaps. It cannot detect an omitted
requirement or false evidence. Main and the independent verifiers own that check.

Sol renders the accepted dataset and checks fidelity in a browser: overview and
candidate identity, three verdict labels, calibration limit, requirement evidence,
quality dimensions, findings and possible fixes, unrelated findings, filters,
keyboard access, light/dark appearance, narrow layout, and print output. Escape
all source content. The included template has no remote resources. Verify the
actual output after changing it; renderer tests alone do not establish usability.

## Hand off once

After the verification summary and any requested author checkpoint, finalize the
dataset and report. Write one handoff containing the candidate/baseline, verdict
and scores, covered/uncovered requirements, verified findings and responsible
owners, smallest useful outcomes, focused validation, dependencies, unresolved
decisions, calibration status, and retained resources. Link the report and evidence.

Send the handoff to a work chat only with established author authorization. The
handoff proposes fixes. It does not authorize edits, commits, merge, publication,
or an automatic re-review. Luna summarizes these settled results without changing
the assessment. A negative verdict still produces the report and handoff.
