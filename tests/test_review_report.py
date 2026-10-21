from __future__ import annotations

from copy import deepcopy
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "review-work" / "scripts" / "render_report.py"


def review():
    return {
        "schema_version": 1, "title": "Review", "candidate": "candidate SHA", "baseline": "baseline SHA",
        "verdict": "Ready", "overall_score": 9,
        "change_summary": ["Persist submitted records and reload them after navigation."],
        "calibration": {"status": "uncalibrated", "evidence": []},
        "requirements": [{"id": "R1", "description": "Persist a submitted record", "status": "met", "evidence": ["HTTP and storage receipt"]}],
        "dimensions": [{"name": "Correctness", "critical": True, "score": 9, "rationale": "Observed the required persisted result.", "evidence": ["storage receipt"]}],
        "findings": [],
        "checks": [{"name": "Submit and reload", "status": "passed", "required": True, "evidence": ["receipt.txt:1"]}],
        "verification": {"complete": True, "summary": "Submitted and reloaded the record.", "environment": "Temporary test checkout", "evidence": ["receipt.txt:1"], "unresolved_material_objections": []},
        "limitations": [], "decisions": [],
    }


def finding():
    return {
        "id": "F1", "title": "Repeated submission", "kind": "risk", "severity": "low",
        "confidence": "supported", "in_scope": True, "blocking": False, "verified": False,
        "requirement_ids": ["R1"], "expected": "One persisted result", "observed": "Retries were not exercised",
        "source": "src/submit.py:12", "evidence": [], "counterevidence": [],
        "fix": "Consider an idempotency key", "validation": "Repeat a request after disconnect",
    }


class ParsedReport(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []
        self.executable_text = []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))
        if tag == "script":
            self.in_script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False

    def handle_data(self, data):
        (self.executable_text if self.in_script else self.text).append(data)


class ReviewReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="review-report-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "owned-review"
        self.workspace.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        subprocess.run(["git", "init", str(self.workspace)], env=self.env, capture_output=True, check=True)
        self.source = self.root / "review.json"

    def run_cli(self, data, *args):
        self.source.write_text(json.dumps(data), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(self.source), *args], env=self.env, capture_output=True, text=True, check=False)

    def test_ready_consistency_gates_and_invalid_claims_through_cli(self):
        mutations = {
            "unmet requirement": lambda d: d["requirements"][0].update(status="unmet"),
            "unverified requirement": lambda d: d["requirements"][0].update(status="unverified"),
            "missing requirement evidence": lambda d: d["requirements"][0].update(evidence=[]),
            "overall below threshold": lambda d: d.update(overall_score=8.9),
            "critical score below threshold": lambda d: d["dimensions"][0].update(score=8.9),
            "check failed": lambda d: d["checks"][0].update(status="failed"),
            "check skipped": lambda d: d["checks"][0].update(status="not_run", evidence=[]),
            "verification incomplete": lambda d: d["verification"].update(complete=False),
            "verification lacks evidence": lambda d: d["verification"].update(evidence=[]),
            "open material objection": lambda d: d["verification"].update(unresolved_material_objections=["Result not reconciled"]),
            "blocking risk": lambda d: d.update(findings=[dict(finding(), blocking=True)]),
            "false confirmation": lambda d: d.update(findings=[dict(finding(), confidence="confirmed")]),
            "blocking advisory": lambda d: d.update(findings=[dict(finding(), kind="advisory", blocking=True)]),
            "out-of-scope blocker": lambda d: d.update(findings=[dict(finding(), in_scope=False, blocking=True)]),
            "boolean score": lambda d: d.update(overall_score=True),
            "infinite score": lambda d: d.update(overall_score=float("inf")),
            "duplicate requirement": lambda d: d["requirements"].append(deepcopy(d["requirements"][0])),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                data = review()
                mutate(data)
                result = self.run_cli(data, "--check")
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("error:", result.stderr)
        data = review()
        data["findings"] = [dict(finding(), in_scope=False)]
        self.assertEqual(self.run_cli(data, "--check").returncode, 0)
        data["verdict"] = "Incomplete"
        data["verification"]["complete"] = False
        result = self.run_cli(data, "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 recorded gating gap", result.stdout)
        self.assertEqual(list(self.workspace.iterdir()), [self.workspace / ".git"])

    def test_hostile_text_is_inert_and_output_is_deterministic_and_protected(self):
        payload = '</script><script>globalThis.reviewPayloadExecuted=1</script><img src=x onerror="alert(1)"><a href="javascript:alert(1)">click</a>{{TITLE}}'
        data = review()
        data["title"] = payload
        data["requirements"][0]["evidence"] = [payload]
        data["findings"] = [dict(finding(), title=payload, source="javascript:alert(1)", observed=payload)]
        args = ("--workspace", str(self.workspace), "--output", "reports/review.html")
        result = self.run_cli(data, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.workspace / "reports" / "review.html"
        original = target.read_bytes()
        parsed = ParsedReport()
        parsed.feed(original.decode("utf-8"))
        self.assertIn(payload, "".join(parsed.text))
        self.assertNotIn("reviewPayloadExecuted", "".join(parsed.executable_text))
        self.assertFalse(any(tag == "img" or any(key.startswith("on") for key in attrs) for tag, attrs in parsed.elements))
        self.assertFalse(any(attrs.get("href", "").startswith("javascript:") for _, attrs in parsed.elements))
        self.assertTrue(any(tag == "meta" and attrs.get("http-equiv") == "Content-Security-Policy" and "default-src 'none'" in attrs.get("content", "") for tag, attrs in parsed.elements))
        self.assertEqual(self.run_cli(data, *args).returncode, 0)
        self.assertEqual(target.read_bytes(), original)
        data["title"] = "Changed report"
        self.assertNotEqual(self.run_cli(data, *args).returncode, 0)
        self.assertEqual(target.read_bytes(), original)

    def test_unassessed_quality_remains_unknown_and_blocks_ready(self):
        data = review()
        data.update(verdict="Incomplete", overall_score=None)
        data["dimensions"][0].update(score=None, evidence=[], rationale="Storage receipt could not be obtained.")
        args = ("--workspace", str(self.workspace), "--output", "unknown.html")
        result = self.run_cli(data, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = ParsedReport()
        parsed.feed((self.workspace / "unknown.html").read_text(encoding="utf-8"))
        text = "".join(parsed.text)
        self.assertIn("Not assessed", text)
        self.assertIn("Overall quality is not assessed.", text)
        self.assertIn("Critical dimension Correctness is not assessed.", text)
        self.assertIn("Recorded calibration: uncalibrated", text)
        self.assertIn("Detailed author review is required", text)
        self.assertIn("Persist submitted records and reload them after navigation.", text)
        data["verdict"] = "Ready"
        self.assertNotEqual(self.run_cli(data, "--check").returncode, 0)
        data["overall_score"] = 9
        data["dimensions"][0]["critical"] = False
        self.assertEqual(self.run_cli(data, "--check").returncode, 0)

    def test_change_summary_and_calibration_disclosure_through_cli(self):
        for status in ("passed", "failed"):
            with self.subTest(status=status):
                data = review()
                data["calibration"] = {"status": status, "evidence": []}
                result = self.run_cli(data, "--check")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("calibration:", result.stderr)
                data["calibration"]["evidence"] = ["calibration-receipt.txt:12"]
                result = self.run_cli(data, "--workspace", str(self.workspace), "--output", status + ".html")
                self.assertEqual(result.returncode, 0, result.stderr)
                parsed = ParsedReport()
                parsed.feed((self.workspace / (status + ".html")).read_text(encoding="utf-8"))
                text = "".join(parsed.text)
                self.assertIn("Recorded calibration: " + status, text)
                self.assertIn("calibration-receipt.txt:12", text)
                self.assertIn("Ready", text)
                if status == "failed":
                    self.assertIn("Detailed author review is required", text)
        data = review()
        data["change_summary"] = []
        result = self.run_cli(data, "--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("change_summary:", result.stderr)

    def test_explicit_source_and_evidence_links_allow_only_safe_navigation(self):
        source = "https://github.com/example/project/blob/abcdef/src/submit.py#L12"
        https = "https://example.test/receipt?name=O'Reilly&result=passed"
        local = "file:///C:/review%20evidence/receipt.txt#L12"
        unsafe = [
            "javascript:alert(1)", "data:text/html,<script>alert(1)</script>",
            "file://server/share/receipt.txt", "file:////server/share/receipt.txt",
            "file:///%2Fserver/share/receipt.txt", "file:///C:/%5C%5Cserver/share.txt",
            "file:///..//server/share/receipt", "file:///%2e%2e//server/share/receipt",
            "file:///a/..//server/share/receipt", "file:///a/%2e/receipt.txt",
            "https://example.test/receipt\nhttps://elsewhere.test/", "https://example.test/%0Areceipt",
            "https://example.test/receipt\tonclick=alert(1)", "https://", "https://example.test:invalid/",
            "Receipt at https://example.test/receipt", r"C:\review\receipt.txt:12",
            'https://example.test/\" onclick=\"alert(1)',
        ]
        data = review()
        data["findings"] = [dict(finding(), source=source, evidence=[https, local, *unsafe])]
        data["requirements"][0]["evidence"] = [local]
        result = self.run_cli(data, "--workspace", str(self.workspace), "--output", "links.html")
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = ParsedReport()
        parsed.feed((self.workspace / "links.html").read_text(encoding="utf-8"))
        hrefs = [attrs["href"] for tag, attrs in parsed.elements if tag == "a" and "href" in attrs]
        for value in (source, https, local):
            self.assertIn(value, hrefs)
        for value in unsafe:
            self.assertNotIn(value, hrefs)
            self.assertIn(value, "".join(parsed.text))
        self.assertFalse(any(key.startswith("on") for _, attrs in parsed.elements for key in attrs))
        self.assertFalse(any(tag in ("img", "iframe", "link") for tag, _ in parsed.elements))

    def test_output_containment_and_checkout_requirement(self):
        invalid = ("../escape.html", str(self.root / "absolute.html"), ".git/report.html", ".GIT/report.html", "nested/../../escape.html", "report.html:stream", "NUL.html", "trailing./report.html")
        for output in invalid:
            with self.subTest(output=output):
                result = self.run_cli(review(), "--workspace", str(self.workspace), "--output", output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("output:", result.stderr)
        result = self.run_cli(review(), "--workspace", str(self.root), "--output", "report.html")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("workspace:", result.stderr)
        self.assertFalse((self.root / "escape.html").exists())
        outside = self.root / "outside"
        outside.mkdir()
        link = self.workspace / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cli(review(), "--workspace", str(self.workspace), "--output", "linked/report.html")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reparse point", result.stderr)
        self.assertFalse((outside / "report.html").exists())


if __name__ == "__main__":
    unittest.main()
