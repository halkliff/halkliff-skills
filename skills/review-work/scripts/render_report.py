#!/usr/bin/env python3
"""Validate recorded review consistency and render an offline report with escaped evidence."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import subprocess
import sys
import unicodedata
from urllib.parse import unquote, urlsplit


class InvalidReview(ValueError):
    pass


def fail(path, message):
    raise InvalidReview(f"{path}: {message}")


def fields(value, path, required, optional=()):
    if not isinstance(value, dict):
        fail(path, "expected an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing:
        fail(path, "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        fail(path, "unknown fields: " + ", ".join(sorted(extra)))


def string(value, path):
    if not isinstance(value, str) or not value.strip():
        fail(path, "expected a nonempty string")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        fail(path, "control characters are not allowed")


def boolean(value, path):
    if type(value) is not bool:
        fail(path, "expected a boolean")


def score(value, path):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 10:
        fail(path, "expected a finite number from 0 to 10")


def strings(value, path):
    if not isinstance(value, list):
        fail(path, "expected a list of strings")
    for index, item in enumerate(value):
        string(item, f"{path}[{index}]")


def choice(value, path, options):
    if not isinstance(value, str) or value not in options:
        fail(path, "expected one of: " + ", ".join(options))


def records(value, path, key):
    if not isinstance(value, list):
        fail(path, "expected a list")
    seen = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            fail(f"{path}[{index}]", "expected an object")
        string(item.get(key), f"{path}[{index}].{key}")
        if item[key] in seen:
            fail(path, f"duplicate {key}: {item[key]}")
        seen.add(item[key])
    return value


def validate(data):
    fields(data, "review", (
        "schema_version", "title", "candidate", "baseline", "verdict", "overall_score",
        "change_summary", "calibration", "requirements", "dimensions", "findings", "checks", "verification", "limitations", "decisions",
    ), ("threshold",))
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        fail("schema_version", "expected integer 1")
    for key in ("title", "candidate", "baseline"):
        string(data[key], key)
    strings(data["change_summary"], "change_summary")
    if not data["change_summary"]:
        fail("change_summary", "expected at least one change or an explanation of unavailable baseline context")
    calibration = data["calibration"]
    fields(calibration, "calibration", ("status", "evidence"))
    choice(calibration["status"], "calibration.status", ("uncalibrated", "passed", "failed"))
    strings(calibration["evidence"], "calibration.evidence")
    if calibration["status"] != "uncalibrated" and not calibration["evidence"]:
        fail("calibration", "passed or failed calibration needs recorded evidence pointers")
    choice(data["verdict"], "verdict", ("Ready", "Changes required", "Incomplete"))
    if data["overall_score"] is not None:
        score(data["overall_score"], "overall_score")
    score(data.get("threshold", 9), "threshold")
    threshold = data.get("threshold", 9)
    gaps = []
    if data["overall_score"] is None:
        gaps.append("Overall quality is not assessed.")
    elif data["overall_score"] < threshold:
        gaps.append(f"Overall score {data['overall_score']:g} is below {threshold:g}.")

    requirements = records(data["requirements"], "requirements", "id")
    dimensions = records(data["dimensions"], "dimensions", "name")
    if not requirements or not dimensions:
        fail("review", "requirements and dimensions must each contain at least one record")
    requirement_ids = {item["id"] for item in requirements}
    for index, item in enumerate(requirements):
        path = f"requirements[{index}]"
        fields(item, path, ("id", "description", "status", "evidence"))
        string(item["description"], path + ".description")
        choice(item["status"], path + ".status", ("met", "unmet", "unverified"))
        strings(item["evidence"], path + ".evidence")
        if item["status"] == "met" and not item["evidence"]:
            fail(path, "a met requirement needs recorded evidence")
        if item["status"] != "met":
            gaps.append(f"Requirement {item['id']} is {item['status']}.")
    for index, item in enumerate(dimensions):
        path = f"dimensions[{index}]"
        fields(item, path, ("name", "critical", "score", "rationale", "evidence"), ("threshold",))
        boolean(item["critical"], path + ".critical")
        if item["score"] is not None:
            score(item["score"], path + ".score")
        score(item.get("threshold", threshold), path + ".threshold")
        string(item["rationale"], path + ".rationale")
        strings(item["evidence"], path + ".evidence")
        if item["score"] is not None and not item["evidence"]:
            fail(path, "a dimension score needs recorded evidence")
        if item["critical"] and item["score"] is None:
            gaps.append(f"Critical dimension {item['name']} is not assessed.")
        elif item["critical"] and item["score"] < item.get("threshold", threshold):
            gaps.append(f"Critical dimension {item['name']} is below its threshold.")
    for index, item in enumerate(records(data["findings"], "findings", "id")):
        path = f"findings[{index}]"
        fields(item, path, (
            "id", "title", "kind", "severity", "confidence", "in_scope", "blocking", "verified",
            "requirement_ids", "expected", "observed", "source", "evidence", "counterevidence", "fix", "validation",
        ))
        for key in ("title", "expected", "observed", "source", "fix", "validation"):
            string(item[key], path + "." + key)
        choice(item["kind"], path + ".kind", ("defect", "plan_gap", "risk", "missing_verification", "quality", "advisory"))
        choice(item["severity"], path + ".severity", ("critical", "high", "medium", "low", "info"))
        choice(item["confidence"], path + ".confidence", ("confirmed", "supported", "provisional", "unknown"))
        for key in ("in_scope", "blocking", "verified"):
            boolean(item[key], path + "." + key)
        for key in ("requirement_ids", "evidence", "counterevidence"):
            strings(item[key], path + "." + key)
        if len(set(item["requirement_ids"])) != len(item["requirement_ids"]):
            fail(path, "duplicate requirement references")
        if set(item["requirement_ids"]) - requirement_ids:
            fail(path, "unknown requirement references")
        if item["verified"] and not item["evidence"]:
            fail(path, "a verified finding needs recorded evidence")
        if item["confidence"] == "confirmed" and not item["verified"]:
            fail(path, "confirmed confidence requires verified=true and recorded evidence")
        if item["blocking"] and (item["kind"] == "advisory" or not item["in_scope"]):
            fail(path, "advisory and out-of-scope findings cannot be blocking")
        if item["blocking"]:
            gaps.append(f"Blocking finding {item['id']}: {item['title']}")
    for index, item in enumerate(records(data["checks"], "checks", "name")):
        path = f"checks[{index}]"
        fields(item, path, ("name", "status", "required", "evidence"))
        choice(item["status"], path + ".status", ("passed", "failed", "not_run"))
        boolean(item["required"], path + ".required")
        strings(item["evidence"], path + ".evidence")
        if item["status"] in ("passed", "failed") and not item["evidence"]:
            fail(path, "a completed check needs recorded evidence")
        if item["required"] and item["status"] != "passed":
            gaps.append(f"Required check {item['name']} is {item['status']}.")
    verification = data["verification"]
    fields(verification, "verification", ("complete", "summary", "evidence", "unresolved_material_objections"), ("environment",))
    boolean(verification["complete"], "verification.complete")
    string(verification["summary"], "verification.summary")
    if "environment" in verification:
        string(verification["environment"], "verification.environment")
    for key in ("evidence", "unresolved_material_objections"):
        strings(verification[key], "verification." + key)
    if verification["complete"] and not verification["evidence"]:
        fail("verification", "complete verification needs recorded evidence")
    if not verification["complete"]:
        gaps.append("Verification is incomplete.")
    gaps.extend("Unresolved material objection: " + item for item in verification["unresolved_material_objections"])
    for key in ("limitations", "decisions"):
        strings(data[key], key)
    if data["verdict"] == "Ready" and gaps:
        fail("verdict", "Ready contradicts recorded gates: " + " ".join(gaps))
    return gaps


def reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            fail("JSON", f"duplicate object key: {key}")
        value[key] = item
    return value


def esc(value):
    return html.escape(str(value), quote=True)


def paragraph(value):
    return "<p>" + esc(value) + "</p>"


def reference(value):
    label = esc(value)
    decoded = unquote(value)
    if (any(char.isspace() or char in '<>"{}|^`\\' or unicodedata.category(char).startswith("C") for char in value)
            or any(char == "\\" or unicodedata.category(char).startswith("C") for char in decoded)
            or re.search(r"%(?![0-9a-fA-F]{2})", value)):
        return label
    try:
        uri = urlsplit(value)
        if uri.scheme.lower() in ("http", "https"):
            allowed = bool(uri.hostname)
            uri.port
        else:
            decoded_path = unquote(uri.path)
            allowed = (uri.scheme.lower() == "file" and value.lower().startswith("file:///")
                       and not uri.netloc and uri.path.startswith("/")
                       and not decoded_path.startswith("//")
                       and not any(part in (".", "..") for part in decoded_path.split("/")))
    except ValueError:
        return label
    return '<a href="' + label + '" rel="noreferrer">' + label + '</a>' if allowed else label


def evidence(items, *, links=True):
    return "<ul class=\"evidence\">" + "".join("<li><pre>" + (reference(item) if links else esc(item)) + "</pre></li>" for item in items) + "</ul>" if items else "<p class=\"muted\">None recorded.</p>"


def tag(value):
    return '<span class="tag">' + esc(value.replace("_", " ")) + "</span>"


def score_label(value):
    return "Not assessed" if value is None else esc(f"{value:g}") + '<span> / 10</span>'


def render(data, gaps):
    template = (Path(__file__).resolve().parent.parent / "assets" / "report.html").read_text(encoding="utf-8")
    threshold = data.get("threshold", 9)
    requirement_rows = "".join(
        '<tr><th scope="row">' + esc(item["id"]) + '</th><td>' + esc(item["description"]) + '</td><td>' + tag(item["status"]) + '</td><td>' + evidence(item["evidence"]) + '</td></tr>'
        for item in data["requirements"]
    )
    dimension_cards = "".join(
        '<article class="dimension"><h3>' + esc(item["name"]) + '</h3><p class="score">' + score_label(item["score"]) + '</p>'
        + paragraph(f"{'Critical' if item['critical'] else 'Noncritical'} · threshold {item.get('threshold', threshold):g}")
        + paragraph(item["rationale"]) + evidence(item["evidence"]) + '</article>' for item in data["dimensions"]
    )
    finding_groups = {True: [], False: []}
    for item in data["findings"]:
        attrs = ' '.join(f'data-{key}="{esc(item[key])}"' for key in ("kind", "confidence"))
        attrs += ' data-scope="' + ("in" if item["in_scope"] else "out") + '"'
        card = '<article class="finding" ' + attrs + '><h3>' + esc(item["id"] + " · " + item["title"]) + '</h3><div class="tags">'
        card += ''.join(tag(item[key]) for key in ("kind", "severity", "confidence"))
        card += tag("Blocking" if item["blocking"] else "Non-gating") + tag("Verified evidence recorded" if item["verified"] else "Unverified") + '</div>'
        card += '<dl>'
        for label, value in (("Requirements", ", ".join(item["requirement_ids"]) or "None linked"), ("Expected", item["expected"]), ("Observed", item["observed"]), ("Source pointer", item["source"])):
            card += '<dt>' + label + '</dt><dd><pre>' + (reference(value) if label == "Source pointer" else esc(value)) + '</pre></dd>'
        card += '</dl><details open><summary>Evidence and counterevidence</summary><h4>Evidence</h4>' + evidence(item["evidence"]) + '<h4>Counterevidence</h4>' + evidence(item["counterevidence"]) + '</details>'
        card += '<h4>Possible fix</h4>' + paragraph(item["fix"]) + '<h4>Validation</h4>' + paragraph(item["validation"]) + '</article>'
        finding_groups[item["in_scope"]].append(card)
    check_rows = ''.join('<tr><th scope="row">' + esc(item["name"]) + '</th><td>' + tag(item["status"]) + '</td><td>' + ("Required" if item["required"] else "Optional") + '</td><td>' + evidence(item["evidence"]) + '</td></tr>' for item in data["checks"])
    verification = data["verification"]
    slots = {
        "TITLE": esc(data["title"]), "CANDIDATE": esc(data["candidate"]), "BASELINE": esc(data["baseline"]),
        "CHANGE_SUMMARY": evidence(data["change_summary"], links=False),
        "CALIBRATION_STATUS": esc(data["calibration"]["status"]),
        "CALIBRATION_EVIDENCE": evidence(data["calibration"]["evidence"]),
        "CALIBRATION_LIMIT": paragraph("Detailed author review is required before relying on this report." if data["calibration"]["status"] != "passed" else "Recorded calibration passed. The label and evidence pointers do not independently establish calibration quality or claim truth."),
        "VERDICT": esc(data["verdict"]), "VERDICT_CLASS": {"Ready": "ready", "Changes required": "changes", "Incomplete": "incomplete"}[data["verdict"]],
        "OVERALL": score_label(data["overall_score"]), "THRESHOLD": esc(f"{threshold:g}"),
        "GAPS": evidence(gaps, links=False) if gaps else paragraph("No gating gaps are recorded. This does not establish that the review claims are true."),
        "REQUIREMENTS": requirement_rows, "DIMENSIONS": dimension_cards,
        "IN_SCOPE": ''.join(finding_groups[True]) or paragraph("No findings recorded in scope."),
        "OUT_SCOPE": ''.join(finding_groups[False]) or paragraph("No unrelated findings recorded."),
        "CHECKS": check_rows or '<tr><td colspan="4">No checks recorded.</td></tr>',
        "VERIFICATION": paragraph("Complete" if verification["complete"] else "Incomplete") + paragraph(verification["summary"]) + evidence(verification["evidence"]),
        "ENVIRONMENT": paragraph(verification.get("environment", "Not recorded.")),
        "OBJECTIONS": evidence(verification["unresolved_material_objections"], links=False), "LIMITATIONS": evidence(data["limitations"], links=False), "DECISIONS": evidence(data["decisions"], links=False),
    }
    hashes = []
    for kind in ("style", "script"):
        for content in re.findall(r"<" + kind + r">(.*?)</" + kind + ">", template, re.S):
            digest = base64.b64encode(hashlib.sha256(content.encode("utf-8")).digest()).decode("ascii")
            hashes.append((kind, "'sha256-" + digest + "'"))
    slots["CSP"] = esc("default-src 'none'; base-uri 'none'; form-action 'none'; " + '; '.join(kind + "-src " + digest for kind, digest in hashes))
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: slots[match[1]], template).encode("utf-8")


def reject_links(path):
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            fail("output", f"symlink or reparse point is not allowed: {part}")


def output_path(workspace, relative):
    workspace = Path(os.path.abspath(workspace))
    reject_links(workspace)
    if not workspace.is_dir() or not (workspace / ".git").exists():
        fail("workspace", "expected the root of an existing Git checkout")
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(["git", "--no-optional-locks", "-C", str(workspace), "rev-parse", "--show-toplevel"], env=env, capture_output=True, text=True, check=False)
    if result.returncode or Path(result.stdout.strip()).resolve() != workspace.resolve():
        fail("workspace", "expected the root of an existing Git checkout")
    relative_path = Path(relative)
    windows_path = PureWindowsPath(relative)
    parts = relative.replace("\\", "/").split("/")
    if (relative_path.is_absolute() or windows_path.drive or windows_path.root or ":" in relative
            or any(part.casefold() in ("..", ".git") or part.endswith((".", " "))
                   or PureWindowsPath(part).is_reserved() for part in parts)):
        fail("output", "use a relative HTML path inside the supplied workspace, outside .git")
    target = workspace / relative_path
    if target.suffix.lower() != ".html":
        fail("output", "expected an .html filename")
    reject_links(target)
    if not target.resolve().is_relative_to(workspace.resolve()):
        fail("output", "path escapes the supplied workspace")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog="The caller must establish workspace ownership. Git/path checks do not prove ownership, evidence truth, score calibration, or review completeness.")
    parser.add_argument("review", type=Path)
    parser.add_argument("--check", action="store_true", help="validate only; write nothing")
    parser.add_argument("--workspace", type=Path, help="root of the caller-owned review clone/worktree")
    parser.add_argument("--output", help="HTML output path relative to --workspace")
    args = parser.parse_args(argv)
    if args.check and (args.workspace is not None or args.output is not None):
        parser.error("--check cannot be combined with output options")
    if not args.check and (args.workspace is None or args.output is None):
        parser.error("rendering requires both --workspace and --output")
    try:
        data = json.loads(args.review.read_text(encoding="utf-8-sig"), object_pairs_hook=reject_duplicate_keys,
                          parse_constant=lambda value: fail("JSON", "nonfinite number: " + value))
        gaps = validate(data)
        if args.check:
            print(f"Valid recorded review: {data['verdict']}; {len(gaps)} recorded gating gap(s). Evidence truth and score calibration are not checked.")
            return 0
        target = output_path(args.workspace, args.output)
        if target.resolve() == args.review.resolve():
            fail("output", "cannot replace the input JSON")
        payload = render(data, gaps)
        if target.exists():
            if target.read_bytes() != payload:
                fail("output", "refusing to overwrite an existing report with different content")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            reject_links(target)
            with target.open("xb") as stream:
                stream.write(payload)
        print(f"Rendered {target}. The caller must establish workspace ownership; evidence truth and score calibration are not checked.")
        return 0
    except (InvalidReview, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
