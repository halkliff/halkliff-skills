from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

from test_plugin_runtime import RuntimeFixture


class OperationPolicyTests(RuntimeFixture, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.head = self.init_repository(self.author)
        self.workspace = self.root / "integration"
        self.git(self.root, "clone", "--quiet", str(self.author), str(self.workspace))
        (self.workspace / ".git" / "info" / "exclude").write_text(
            "invoked\nwait\nrelease\nfail\npromote\npost-observation\npost-checkout\n"
            "lock-finalization\nreceipt-block\npartial-profile/\n", encoding="utf-8")
        self.adapter = self.root / "adapter.py"
        self.adapter.write_text(
            "import argparse,json,pathlib,time,sys,subprocess\n"
            "p=argparse.ArgumentParser();p.add_argument('--request');p.add_argument('--result');a=p.parse_args()\n"
            "r=json.loads(pathlib.Path(a.request).read_text());w=pathlib.Path(r['workspace'])\n"
            "m=w/'invoked';m.write_text(str(int(m.read_text())+1 if m.exists() else 1))\n"
            "if (w/'wait').exists():\n"
            " while not (w/'release').exists(): time.sleep(.02)\n"
            "e=pathlib.Path(a.result).with_name('observed.json');e.write_text(json.dumps(r))\n"
            "if (w/'lock-finalization').exists(): pathlib.Path((w/'lock-finalization').read_text()).write_text('fixture-held')\n"
            "if (w/'fail').exists():\n"
            " d=w/'partial-profile';d.mkdir(exist_ok=True);e.write_text(json.dumps({'product_started':False,'partial_profile':str(d)}))\n"
            " pathlib.Path(a.result).write_text(json.dumps({'schema_version':1,'consumer':r['consumer'],'claim_kind':r['claim_kind'],'procedure':r['procedure'],'outcome':'fail','evidence':[str(e)]}));sys.exit(7)\n"
            "pathlib.Path(a.result).write_text(json.dumps({'schema_version':1,'consumer':r['consumer'],'claim_kind':((w/'promote').read_text() if (w/'promote').exists() else r['claim_kind']),"
            "'procedure':r['procedure'],'outcome':'pass','evidence':[str(e)]}))\n"
            "if (w/'post-observation').exists():\n"
            " mode=(w/'post-observation').read_text();i=pathlib.Path(r['inputs']['items']['path'])\n"
            " if mode=='delete': i.unlink()\n"
            " elif mode=='change': i.write_text('[1]')\n"
            " elif mode=='head': (w/'.git'/'HEAD').write_text('ref: refs/heads/missing-after\\n')\n"
            "if (w/'post-checkout').exists():\n"
            " c=json.loads((w/'post-checkout').read_text());p=pathlib.Path(c['path'])\n"
            " if c['mode']=='untracked': (p/'new.txt').write_text('new')\n"
            " else: (p/'tracked.txt').write_text('modified')\n"
            " if c['mode']=='staged': subprocess.run(['git','-C',str(p),'add','tracked.txt'],check=True)\n"
            "if (w/'receipt-block').exists(): pathlib.Path(a.result).with_name('receipt.json').mkdir()\n",
            encoding="utf-8",
        )
        self.input_file = self.root / "items.json"
        self.input_file.write_text('["first","second"]', encoding="utf-8")
        self.policy_value = {
            "schema_version": 1, "revision": 1,
            "author_constraints": {"resource_floor": {"bytes": 1073741824, "basis_ref": "brief.md#author"}},
            "root_controls": {"resource_headroom": {"bytes": 10200547328, "basis_ref": "plan.md#headroom"}},
            "roles": {}, "resources": {"native": {"owner": "enrolled"}},
            "grants": {"build": {"owner": "enrolled", "roles": ["worker"], "adapters": ["fixture"],
                                    "resources": ["native"], "workspace": str(self.workspace),
                                    "basis_ref": "brief.md#need", "max_invocations": 1}},
            "adapters": {"fixture": {"command": [sys.executable, str(self.adapter)],
                                      "sha256": [self.digest(Path(sys.executable)), self.digest(self.adapter)],
                                      "claim_kinds": ["build"]}},
            "integration": {"workspace": str(self.workspace), "owner": "enrolled"},
        }
        self.policy_value["grants"]["review"] = {
            "owner": "enrolled", "roles": ["worker"], "adapters": [], "resources": [],
            "workspace": str(self.workspace), "basis_ref": "brief.md#review", "max_invocations": 1,
        }
        self.policy_file = self.write_json("policy-1.json", self.policy_value)
        self.request_value = {
            "schema_version": 1, "policy_revision": 1, "grant": "build", "role": "worker",
            "adapter": "fixture", "consumer": "fixture.cli", "claim_kind": "build", "procedure": "verify-v1",
            "workspace": str(self.workspace), "expected_head": self.head,
            "inputs": {"items": {"kind": "json-array", "path": str(self.input_file),
                                  "sha256": self.digest(self.input_file)}},
        }
        self.request_file = self.write_json("request.json", self.request_value)

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_json(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def start(self) -> dict:
        active = self.activate(policy=str(self.policy_file))
        self.cli("workspace-register", "--session", "enrolled", "--path", str(self.workspace),
                 "--kind", "integration", "--base-commit", self.head, "--expected-head", self.head,
                 "--plugin-data", str(self.data))
        return active

    def operation(self, *, ok: bool = True, reuse: str | None = None, request: Path | None = None,
                  expected_exit: int | None = None) -> dict:
        args = ["operation", "--session", "enrolled", "--request", str(request or self.request_file),
                "--plugin-data", str(self.data)]
        if reuse:
            args.extend(["--reuse", reuse])
        return self.cli(*args, ok=ok, exit_code=expected_exit)

    def update_policy(self, value: dict, *, session: str = "enrolled", expected: int = 1, ok: bool = True) -> dict:
        path = self.write_json(f"policy-{value['revision']}.json", value)
        return self.cli("policy-select", "--session", session, "--expected-revision", str(expected),
                        "--policy", str(path), "--plugin-data", str(self.data), ok=ok)

    def test_active_hook_checks_selected_revision_grant_and_latest_role(self) -> None:
        active = self.start()
        args = {"model": "gpt-6-luna", "reasoning_effort": "xhigh", "fork_turns": "none",
                "message": "ORCHESTRATION role=worker grant=build revision=1"}
        self.assertEqual(self.hook(self.spawn("enrolled", **args)).stdout, b"")
        for change, reason in (({"message": "task"}, "marker"),
                               ({"message": "ORCHESTRATION role=worker grant=build revision=9"}, "revision"),
                               ({"model": "gpt-6-astra"}, "model")):
            with self.subTest(change=change):
                denial = json.loads(self.hook(self.spawn("enrolled", **(args | change))).stdout)
                self.assertEqual(denial["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn(reason, denial["hookSpecificOutput"]["permissionDecisionReason"].lower())
        updated = copy.deepcopy(self.policy_value)
        updated["revision"] = 2
        updated["roles"]["worker"] = {"model": "gpt-6.1-sol", "effort": "high"}
        updated["roles"]["coordinator"] = {"model": "gpt-6.1-terra", "effort": "high"}
        updated["grants"]["review"]["roles"].append("coordinator")
        self.update_policy(updated)
        args["message"] = "ORCHESTRATION role=worker grant=build revision=2"
        self.assertTrue(self.hook(self.spawn("enrolled", **args)).stdout)
        args.update(model="gpt-6.1-sol", reasoning_effort="high")
        self.assertEqual(self.hook(self.spawn("enrolled", **args)).stdout, b"")
        self.assertEqual(self.hook(self.spawn("enrolled", model="gpt-6.1-terra", reasoning_effort="high",
                                             fork_turns="none", message="ORCHESTRATION role=coordinator grant=review revision=2")).stdout, b"")
        recovered = self.activate("recovery", run_id=active["run_id"])
        self.assertEqual(recovered["cli"], active["cli"])
        status = self.cli("status", "--session", "recovery")
        self.assertTrue(status["active"])
        self.assertFalse(status["session_observed"])
        self.assertEqual(status["policy"]["revision"], 2)
        self.assertFalse(self.cli("status", "--session", "unbound")["active"])

    def test_policy_selection_has_one_root_cas_and_immutable_hash(self) -> None:
        active = self.start()
        self.activate("worker", run_id=active["run_id"])
        updated = copy.deepcopy(self.policy_value)
        updated["revision"] = 2
        self.assertIn("Root", self.update_policy(updated, session="worker", ok=False)["stderr"])
        self.assertIn("revision", self.update_policy(updated, expected=0, ok=False)["stderr"])
        self.policy_file.write_text(self.policy_file.read_text() + "\n", encoding="utf-8")
        status = self.cli("status", "--session", "enrolled")
        self.assertFalse(status["policy_valid"])
        self.assertTrue(self.operation(ok=False)["stderr"])
        self.assertTrue(self.hook(self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh",
                                             fork_turns="none", message="ORCHESTRATION role=worker grant=build revision=1")).stdout)
        self.assertFalse((self.workspace / "invoked").exists())
        rebound = self.cli("activate", "--session", "worker", "--run-id", active["run_id"],
                           "--coord-root", str(self.coord), "--author-repo", str(self.author),
                           "--plugin-data", str(self.data), "--policy", str(self.policy_file), ok=False)
        self.assertIn("reuses", rebound["stderr"])

    def test_source_update_cannot_add_policy_or_commands_to_an_old_pin(self) -> None:
        active = self.activate()
        pinned_cli = Path(active["cli"])
        original = pinned_cli.read_bytes()
        package_cli = self.package / "scripts" / "orchestration.py"
        package_cli.write_bytes(package_cli.read_bytes() + b"\n# prospective package revision\n")
        self.rebuild_manifest()
        recovered = self.activate("recovery", run_id=active["run_id"])
        self.assertEqual(recovered["cli"], str(pinned_cli))
        self.assertEqual(pinned_cli.read_bytes(), original)
        denied = self.cli("policy-select", "--session", "enrolled", "--expected-revision", "0",
                          "--policy", str(self.policy_file), "--plugin-data", str(self.data), ok=False)
        self.assertIn("pinned CLI", denied["stderr"])
        selected = self.cli("policy-select", "--session", "enrolled", "--expected-revision", "0",
                            "--policy", str(self.policy_file), "--plugin-data", str(self.data), script=str(pinned_cli))
        self.assertTrue(selected["selected"])

    def test_preinvocation_rejections_leave_grant_unused_and_derive_actual_counts(self) -> None:
        self.start()
        for change, reason in (({"claim_kind": "hosted"}, "claim"),
                               ({"expected_head": "0" * 40}, "HEAD"),
                               ({"count": 500}, "count")):
            with self.subTest(change=change):
                path = self.write_json("invalid.json", self.request_value | change)
                self.assertIn(reason.lower(), self.operation(ok=False, request=path)["stderr"].lower())
                self.assertFalse((self.workspace / "invoked").exists())
        result = self.operation()
        self.assertTrue(result["invoked"])
        self.assertEqual(result["outcome"], "pass")
        observed = json.loads(Path(result["receipt"]).with_name("observed.json").read_text())
        self.assertEqual(observed["inputs"]["items"]["count"], 2)
        attribution = {"author_floor": {"bytes": 1073741824, "basis_ref": "brief.md#author"},
                       "root_headroom": {"bytes": 10200547328, "basis_ref": "plan.md#headroom"}}
        self.assertEqual(observed["resource_attribution"], attribution)
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["resource_attribution"], attribution)
        self.assertEqual(receipt["git_range"], {"registered_base": self.head, "before": self.head,
                                               "result": self.head, "range": f"{self.head}..{self.head}"})
        self.assertTrue(self.operation(ok=False)["stderr"])
        self.assertEqual(self.hook(self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh",
                                             fork_turns="none", message="ORCHESTRATION role=worker grant=build revision=1")).stdout, b"")

    def test_invoked_failure_retains_evidence_and_stops_same_grant_across_revision(self) -> None:
        self.start()
        (self.workspace / "fail").write_text("fail", encoding="utf-8")
        result = self.operation(expected_exit=1)
        self.assertTrue(result["invoked"])
        self.assertEqual(result["outcome"], "fail")
        self.assertTrue(Path(result["receipt"]).is_file())
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["exit_code"], 7)
        self.assertTrue((self.workspace / "partial-profile").is_dir())
        partial = json.loads(Path(receipt["evidence"][0]["path"]).read_text())
        self.assertFalse(partial["product_started"])
        self.assertEqual(partial["partial_profile"], str(self.workspace / "partial-profile"))
        self.assertTrue(Path(result["receipt"]).with_name("stderr.log").is_file())
        self.assertEqual(self.hook(self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh",
                                             fork_turns="none", message="ORCHESTRATION role=worker grant=review revision=1")).stdout, b"")
        (self.workspace / "fail").unlink()
        updated = copy.deepcopy(self.policy_value)
        updated["revision"] = 2
        updated["grants"]["build"]["max_invocations"] = 5
        self.update_policy(updated)
        self.request_value["policy_revision"] = 2
        self.write_json("request.json", self.request_value)
        self.assertIn("fail", self.operation(ok=False)["stderr"].lower())

    def test_adapter_cannot_promote_build_output_to_installed_or_hosted_claims(self) -> None:
        for kind in ("installed_caller", "hosted"):
            self.policy_value["grants"][kind] = copy.deepcopy(self.policy_value["grants"]["build"])
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        for kind in ("installed_caller", "hosted"):
            with self.subTest(claim_kind=kind):
                (self.workspace / "promote").write_text(kind, encoding="utf-8")
                request = self.write_json("promote.json", self.request_value | {"grant": kind})
                result = self.operation(request=request, expected_exit=1)
                self.assertTrue(result["invoked"])
                self.assertEqual(result["outcome"], "fail")
                self.assertTrue(self.operation(ok=False, request=request)["stderr"])

    def test_failed_actual_git_observation_holds_grant_without_adapter_invocation(self) -> None:
        self.start()
        git_head = self.workspace / ".git" / "HEAD"
        original = git_head.read_bytes()
        git_head.write_text("ref: refs/heads/missing-observation\n", encoding="utf-8")
        try:
            result = self.operation(expected_exit=1)
        finally:
            git_head.write_bytes(original)
        self.assertFalse(result["invoked"])
        self.assertEqual(result["outcome"], "preflight_failed")
        self.assertTrue(Path(result["receipt"]).is_file())
        self.assertFalse((self.workspace / "invoked").exists())
        status = self.cli("status", "--session", "enrolled")
        self.assertEqual(status["grant_usage"]["build"]["invocations"], 0)
        self.assertTrue(status["grant_usage"]["build"]["failed"])
        self.assertIn("fail", self.operation(ok=False)["stderr"].lower())

    def test_failed_finalization_cannot_reopen_a_partly_used_grant(self) -> None:
        self.policy_value["grants"]["build"]["max_invocations"] = 3
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        owned_lock = self.data / ".orchestration-state.lock"
        (self.workspace / "lock-finalization").write_text(str(owned_lock), encoding="utf-8")
        (self.workspace / "fail").write_text("fail", encoding="utf-8")
        try:
            result = self.operation(expected_exit=1)
        finally:
            if owned_lock.exists():
                owned_lock.unlink()
        self.assertTrue(result["invoked"])
        self.assertEqual(result["outcome"], "fail")
        self.assertTrue(Path(result["receipt"]).is_file())
        usage = self.cli("status", "--session", "enrolled")["grant_usage"]["build"]
        self.assertEqual(usage["invocations"], 1)
        self.assertTrue(usage["pending_invocation"])
        (self.workspace / "fail").unlink()
        (self.workspace / "lock-finalization").unlink()
        self.assertTrue(self.operation(ok=False)["stderr"])
        self.assertEqual((self.workspace / "invoked").read_text(), "1")
        updated = copy.deepcopy(self.policy_value)
        updated["revision"] = 2
        self.update_policy(updated)
        self.request_value["policy_revision"] = 2
        self.write_json("request.json", self.request_value)
        self.assertTrue(self.operation(ok=False)["stderr"])
        self.assertEqual((self.workspace / "invoked").read_text(), "1")

    def test_receipt_write_failure_retains_actual_result_and_unresolved_grant(self) -> None:
        self.policy_value["grants"]["build"]["max_invocations"] = 3
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        (self.workspace / "receipt-block").write_text("block", encoding="utf-8")
        result = self.operation(expected_exit=1)
        self.assertTrue(result["invoked"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIsNone(result["receipt"])
        self.assertTrue(result["finalization_error"])
        raw = json.loads(Path(result["adapter_result"]).read_text())
        self.assertEqual(raw["outcome"], "pass")
        usage = self.cli("status", "--session", "enrolled")["grant_usage"]["build"]
        self.assertTrue(usage["pending_invocation"])
        self.assertEqual(usage["invocations"], 1)
        (self.workspace / "receipt-block").unlink()
        self.assertTrue(self.operation(ok=False)["stderr"])
        self.assertEqual((self.workspace / "invoked").read_text(), "1")

    def test_unknown_or_changed_stable_postinputs_override_adapter_success(self) -> None:
        for mode in ("delete", "change", "head"):
            self.policy_value["grants"][mode] = copy.deepcopy(self.policy_value["grants"]["build"])
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        original_input = self.input_file.read_bytes()
        head_path = self.workspace / ".git" / "HEAD"
        original_head = head_path.read_bytes()
        for index, mode in enumerate(("delete", "change", "head"), 1):
            with self.subTest(observation=mode):
                request = self.write_json("post-request.json", self.request_value | {"grant": mode})
                (self.workspace / "post-observation").write_text(mode, encoding="utf-8")
                try:
                    result = self.operation(request=request, expected_exit=1)
                finally:
                    self.input_file.write_bytes(original_input)
                    head_path.write_bytes(original_head)
                receipt = json.loads(Path(result["receipt"]).read_text())
                self.assertEqual(receipt["exit_code"], 0)
                self.assertEqual(receipt["adapter_outcome"], "pass")
                self.assertEqual(receipt["outcome"], "fail")
                self.assertTrue(receipt["failure_reasons"])
                if mode == "head":
                    self.assertEqual(receipt["actual_after"]["workspace"]["status"], "unknown")
                    self.assertIsNone(receipt["git_range"]["result"])
                elif mode == "delete":
                    self.assertEqual(receipt["actual_after"]["inputs"]["items"]["status"], "unknown")
                else:
                    self.assertNotEqual(receipt["actual_after"]["inputs"]["items"]["sha256"],
                                        receipt["inputs"]["items"]["sha256"])
                self.assertTrue(self.operation(request=request, ok=False)["stderr"])
                self.assertEqual((self.workspace / "invoked").read_text(), str(index))

    def test_reuse_tracks_only_named_actual_inputs_and_claim_identity(self) -> None:
        self.policy_value.pop("author_constraints")
        self.policy_value.pop("root_controls")
        self.policy_value["adapters"]["fixture"]["claim_kinds"] = ["source"]
        self.request_value["claim_kind"] = "source"
        self.write_json("request.json", self.request_value)
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        result = self.operation()
        receipt = result["receipt"]
        retained = json.loads(Path(receipt).read_text())
        self.assertEqual(retained["resource_attribution"], {"author_floor": None, "root_headroom": None})
        (self.workspace / "unrelated.txt").write_text("unrelated", encoding="utf-8")
        self.git(self.workspace, "config", "user.name", "Runtime Test")
        self.git(self.workspace, "config", "user.email", "runtime-test@example.invalid")
        self.git(self.workspace, "add", "unrelated.txt")
        self.git(self.workspace, "commit", "--quiet", "-m", "unrelated fixture input")
        self.request_value["expected_head"] = self.git(self.workspace, "rev-parse", "HEAD")
        self.write_json("request.json", self.request_value)
        self.assertTrue(self.operation(reuse=receipt)["reusable"])
        updated = copy.deepcopy(self.policy_value)
        updated["revision"] = 2
        updated["roles"]["coordinator"] = {"model": "gpt-6.1-terra", "effort": "high"}
        self.update_policy(updated)
        self.request_value["policy_revision"] = 2
        self.write_json("request.json", self.request_value)
        self.assertTrue(self.operation(reuse=receipt)["reusable"])
        self.input_file.write_text('["different"]', encoding="utf-8")
        self.request_value["inputs"]["items"]["sha256"] = self.digest(self.input_file)
        self.write_json("request.json", self.request_value)
        self.assertFalse(self.operation(reuse=receipt, expected_exit=1)["reusable"])
        self.assertTrue(Path(receipt).is_file())

    def test_candidate_reuse_requires_producer_workspace_git_input(self) -> None:
        claims = ("commit", "integrated", "hosted")
        cases = [(claim, declaration) for claim in claims
                 for declaration in ("dirty-json", "clean-json", "other-git", "workspace-git")]
        cases.append(("integrated", "mutable-json"))
        self.policy_value["adapters"]["fixture"]["claim_kinds"] = list(claims)
        for claim in claims:
            self.policy_value["grants"][claim] = self.policy_value["grants"]["build"] | {"max_invocations": 5}
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        original = (self.workspace / "tracked.txt").read_bytes()
        workspace_git = {"kind": "git", "path": str(self.workspace), "head": self.head}
        for index, (claim, declaration) in enumerate(cases, 1):
            with self.subTest(claim=claim, declaration=declaration):
                request = copy.deepcopy(self.request_value)
                request.update(grant=claim, claim_kind=claim)
                if declaration in {"other-git", "workspace-git"}:
                    request["inputs"]["source"] = workspace_git | {
                        "path": str(self.author if declaration == "other-git" else self.workspace)}
                path = self.write_json("candidate-request.json", request)
                if declaration == "dirty-json":
                    (self.workspace / "tracked.txt").write_text("producer edit", encoding="utf-8")
                    self.assertTrue(self.git(self.workspace, "status", "--porcelain=v1"))
                elif declaration == "mutable-json":
                    (self.workspace / "post-checkout").write_text(
                        json.dumps({"path": str(self.workspace), "mode": "tracked"}), encoding="utf-8")
                try:
                    self.assertEqual(self.git(self.workspace, "rev-parse", "HEAD"), self.head)
                    success = self.operation(request=path)
                    self.assertTrue(success["invoked"])
                    self.assertEqual(success["outcome"], "pass")
                    if declaration == "mutable-json":
                        self.assertNotEqual((self.workspace / "tracked.txt").read_bytes(), original)
                finally:
                    (self.workspace / "tracked.txt").write_bytes(original)
                    if declaration == "mutable-json":
                        (self.workspace / "post-checkout").unlink()
                self.assertEqual(self.git(self.workspace, "status", "--porcelain=v1"), "")
                self.assertEqual(self.git(self.workspace, "rev-parse", "HEAD"), self.head)
                eligible = declaration == "workspace-git"
                reused = self.operation(request=path, reuse=success["receipt"], expected_exit=0 if eligible else 1)
                self.assertEqual(reused["reusable"], eligible)
                self.assertFalse(reused["invoked"])
                if not eligible:
                    self.assertIn("workspace Git input", " ".join(reused["reasons"]))
                if declaration == "clean-json":
                    request["inputs"]["source"] = workspace_git
                    self.write_json("candidate-request.json", request)
                    denied = self.operation(request=path, reuse=success["receipt"], expected_exit=1)
                    self.assertFalse(denied["reusable"])
                    self.assertIn("does not match", " ".join(denied["reasons"]))
                self.assertEqual((self.workspace / "invoked").read_text(), str(index))
                if claim == "commit" and eligible:
                    commit_receipt = success["receipt"]
                    commit_request = request
        (self.workspace / "unrelated.txt").write_text("unrelated", encoding="utf-8")
        self.git(self.workspace, "config", "user.name", "Runtime Test")
        self.git(self.workspace, "config", "user.email", "runtime-test@example.invalid")
        self.git(self.workspace, "add", "unrelated.txt")
        self.git(self.workspace, "commit", "--quiet", "-m", "unrelated fixture input")
        new_head = self.git(self.workspace, "rev-parse", "HEAD")
        commit_request["expected_head"] = new_head
        commit_request["inputs"]["source"]["head"] = new_head
        path = self.write_json("candidate-request.json", commit_request)
        self.assertFalse(self.operation(request=path, reuse=commit_receipt, expected_exit=1)["reusable"])
        self.assertEqual((self.workspace / "invoked").read_text(), str(len(cases)))

    def test_named_git_inputs_and_dependencies_reject_dirty_same_head_checkouts(self) -> None:
        cases = [(role, mode) for role in ("input", "dependency") for mode in ("tracked", "staged", "untracked")]
        for role, mode in cases:
            for suffix in ("", "-admission"):
                self.policy_value["grants"][f"{role}-{mode}{suffix}"] = copy.deepcopy(self.policy_value["grants"]["build"])
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        for index, (role, mode) in enumerate(cases, 1):
            with self.subTest(role=role, drift=mode):
                checkout = self.root / f"{role}-{mode}"
                head = self.init_repository(checkout)
                request = copy.deepcopy(self.request_value)
                request["grant"] = f"{role}-{mode}"
                if role == "input":
                    request["inputs"]["source"] = {"kind": "git", "path": str(checkout), "head": head}
                else:
                    request["dependencies"] = {"source": {"path": str(checkout), "head": head}}
                path = self.write_json("git-request.json", request)
                success = self.operation(request=path)
                self.assertTrue(self.operation(request=path, reuse=success["receipt"])["reusable"])
                if mode == "untracked":
                    (checkout / "new.txt").write_text("new", encoding="utf-8")
                else:
                    (checkout / "tracked.txt").write_text("modified", encoding="utf-8")
                    if mode == "staged":
                        self.git(checkout, "add", "tracked.txt")
                status = self.git(checkout, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
                self.assertTrue(status)
                self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), head)
                self.assertIn("dirty", self.operation(request=path, reuse=success["receipt"], ok=False)["stderr"])
                request["grant"] += "-admission"
                self.write_json("git-request.json", request)
                self.assertIn("dirty", self.operation(request=path, ok=False)["stderr"])
                self.assertEqual((self.workspace / "invoked").read_text(), str(index))
                self.assertEqual(self.git(checkout, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"), status)

    def test_git_checkout_drift_after_adapter_pass_fails_stable_input_and_dependency(self) -> None:
        for mode in ("tracked", "staged", "untracked"):
            self.policy_value["grants"][mode] = copy.deepcopy(self.policy_value["grants"]["build"])
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        for mode in ("tracked", "staged", "untracked"):
            with self.subTest(drift=mode):
                checkout = self.root / f"post-{mode}"
                head = self.init_repository(checkout)
                request = copy.deepcopy(self.request_value)
                request["grant"] = mode
                request["inputs"]["source"] = {"kind": "git", "path": str(checkout), "head": head}
                request["dependencies"] = {"source": {"path": str(checkout), "head": head}}
                path = self.write_json("post-git-request.json", request)
                (self.workspace / "post-checkout").write_text(json.dumps({"path": str(checkout), "mode": mode}), encoding="utf-8")
                result = self.operation(request=path, expected_exit=1)
                receipt = json.loads(Path(result["receipt"]).read_text())
                self.assertEqual(receipt["exit_code"], 0)
                self.assertEqual(receipt["adapter_outcome"], "pass")
                self.assertEqual(receipt["outcome"], "fail")
                for before, after in ((receipt["inputs"]["source"], receipt["actual_after"]["inputs"]["source"]),
                                      (receipt["dependencies"]["source"], receipt["actual_after"]["dependencies"]["source"])):
                    self.assertTrue(before["clean"])
                    self.assertFalse(after["clean"])
                    self.assertEqual(before["head"], after["head"])
                    self.assertTrue(after["git_status"])
                self.assertTrue(self.cli("status", "--session", "enrolled")["grant_usage"][mode]["failed"])

    def test_workspace_selection_rejects_competing_owner_and_false_head_without_redefining_base(self) -> None:
        active = self.start()
        self.activate("other", run_id=active["run_id"])
        denied = self.cli("workspace-register", "--session", "other", "--path", str(self.workspace),
                          "--kind", "integration", "--base-commit", self.head, "--expected-head", self.head,
                          "--plugin-data", str(self.data), ok=False)
        self.assertIn("owner", denied["stderr"])
        owner_attestation = self.write_json("owner-release.json", {"delivery_resolved": False})
        released = self.cli("workspace-release", "--session", "enrolled", "--path", str(self.workspace),
                            "--attestation", str(owner_attestation), "--plugin-data", str(self.data))
        self.assertEqual(released["attestation_sha256"], self.digest(owner_attestation))
        other_attestation = self.write_json("other-release.json", {})
        denied = self.cli("workspace-release", "--session", "other", "--path", str(self.workspace),
                          "--attestation", str(other_attestation), "--plugin-data", str(self.data), ok=False)
        self.assertIn("owner", denied["stderr"])
        self.git(self.workspace, "config", "user.name", "Runtime Test")
        self.git(self.workspace, "config", "user.email", "runtime-test@example.invalid")
        (self.workspace / "tracked.txt").write_text("next", encoding="utf-8")
        self.git(self.workspace, "add", "tracked.txt")
        self.git(self.workspace, "commit", "--quiet", "-m", "fixture candidate")
        new_head = self.git(self.workspace, "rev-parse", "HEAD")
        denied = self.cli("workspace-register", "--session", "enrolled", "--path", str(self.workspace),
                          "--kind", "integration", "--base-commit", self.head, "--expected-head", self.head,
                          "--plugin-data", str(self.data), ok=False)
        self.assertIn("HEAD", denied["stderr"])
        accepted = self.cli("workspace-register", "--session", "enrolled", "--path", str(self.workspace),
                            "--kind", "integration", "--base-commit", self.head, "--expected-head", new_head,
                            "--plugin-data", str(self.data))
        self.assertEqual(accepted["base_commit"], self.head)
        self.request_value["expected_head"] = new_head
        self.write_json("request.json", self.request_value)
        result = self.operation()
        receipt = json.loads(Path(result["receipt"]).read_text())
        self.assertEqual(receipt["git_range"], {"registered_base": self.head, "before": new_head,
                                               "result": new_head, "range": f"{self.head}..{new_head}"})

    def test_resource_scope_blocks_overlap_but_not_an_independent_selected_scope(self) -> None:
        other = self.root / "independent"
        self.git(self.root, "clone", "--quiet", str(self.author), str(other))
        self.policy_value["resources"]["independent"] = {"owner": "enrolled"}
        for name, workspace, resource in (("overlap", self.workspace, "native"),
                                           ("independent", other, "independent")):
            self.policy_value["grants"][name] = self.policy_value["grants"]["build"] | {
                "workspace": str(workspace), "resources": [resource]}
        self.write_json("policy-1.json", self.policy_value)
        self.start()
        self.cli("workspace-register", "--session", "enrolled", "--path", str(other), "--kind", "worker",
                 "--base-commit", self.head, "--expected-head", self.head, "--plugin-data", str(self.data))
        (self.workspace / "wait").write_text("wait", encoding="utf-8")
        process = subprocess.Popen([sys.executable, str(self.package / "scripts/orchestration.py"), "operation",
                                    "--session", "enrolled", "--request", str(self.request_file),
                                    "--plugin-data", str(self.data)], env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 10
            while not (self.workspace / "invoked").exists() and time.monotonic() < deadline:
                time.sleep(.03)
            self.assertTrue((self.workspace / "invoked").exists())
            overlap = self.write_json("overlap.json", self.request_value | {"grant": "overlap"})
            self.assertIn("lock", self.operation(ok=False, request=overlap)["stderr"].lower())
            cross_workspace = self.root / "cross-run"
            self.git(self.root, "clone", "--quiet", str(self.author), str(cross_workspace))
            cross_coord = self.root / "cross-coord"
            cross_coord.mkdir()
            cross_policy = copy.deepcopy(self.policy_value)
            cross_policy["integration"] = None
            cross_policy["resources"] = {"native": {"owner": "other-root"}}
            cross_policy["grants"] = {"build": self.policy_value["grants"]["build"] | {
                "owner": "other-root", "workspace": str(cross_workspace)}}
            cross_policy_file = self.write_json("cross-policy.json", cross_policy)
            self.cli("activate", "--session", "other-root", "--coord-root", str(cross_coord),
                     "--author-repo", str(self.author), "--policy", str(cross_policy_file),
                     "--plugin-data", str(self.data))
            self.cli("workspace-register", "--session", "other-root", "--path", str(cross_workspace),
                     "--kind", "worker", "--base-commit", self.head, "--expected-head", self.head,
                     "--plugin-data", str(self.data))
            cross_request = self.write_json("cross-request.json", self.request_value | {"workspace": str(cross_workspace)})
            denied = self.cli("operation", "--session", "other-root", "--request", str(cross_request),
                              "--plugin-data", str(self.data), ok=False)
            self.assertIn("lock", denied["stderr"].lower())
            independent = self.write_json("independent.json", self.request_value | {
                "grant": "independent", "workspace": str(other)})
            self.assertEqual(self.operation(request=independent)["outcome"], "pass")
            updated = copy.deepcopy(self.policy_value)
            updated["revision"] = 2
            self.assertIn("in-flight", self.update_policy(updated, ok=False)["stderr"])
        finally:
            (self.workspace / "release").write_text("release", encoding="utf-8")
            stdout, stderr = process.communicate(timeout=15)
        self.assertEqual(process.returncode, 0, stderr.decode())
        self.assertEqual(json.loads(stdout)["outcome"], "pass")

    def test_constraint_categories_and_scan_basis_are_checked_before_invocation(self) -> None:
        malformed = copy.deepcopy(self.policy_value)
        malformed["author_constraints"]["resource_headroom"] = malformed["root_controls"]["resource_headroom"]
        path = self.write_json("wrong-attribution.json", malformed)
        denied = self.cli("activate", "--session", "enrolled", "--coord-root", str(self.coord),
                          "--author-repo", str(self.author), "--plugin-data", str(self.data),
                          "--policy", str(path), ok=False)
        self.assertIn("author", denied["stderr"].lower())
        self.start()
        bad_scan = self.write_json("bad-scan.json", self.request_value | {
            "scan": {"reason": "changed_input", "basis_ref": "brief.md#gap", "input": "nonexistent"}})
        self.assertIn("input", self.operation(ok=False, request=bad_scan)["stderr"].lower())
        self.assertFalse((self.workspace / "invoked").exists())
        self.assertEqual(self.operation()["outcome"], "pass")
