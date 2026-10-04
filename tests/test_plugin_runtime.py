from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "plugin"


class PluginRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="orchestration-runtime-")
        self.root = Path(self.temp.name)
        self.package = self.root / "package"
        for rel in ("scripts/orchestration.py", "hooks/bootstrap.py", "hooks/hooks.json"):
            target = self.package / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / rel, target)
        for rel in (
            "plugin.json",
            "skills/orchestrate-work-plugin/SKILL.md",
            "support/skills/orchestrate-work/SKILL.md",
            "support/skills/orchestrate-work/references/worker.md",
            "support/skills/define-goal/SKILL.md",
        ):
            target = self.package / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("test package resource\n", encoding="utf-8")
        (self.package / "plugin.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
        self.rebuild_manifest()
        self.data = self.root / "data"
        self.coord = self.root / "coord"
        self.author = self.root / "author"
        self.coord.mkdir()
        self.author.mkdir()
        self.env = os.environ.copy()
        for name in ("PLUGIN_ROOT", "PLUGIN_DATA", "CODEX_THREAD_ID"):
            self.env.pop(name, None)
        self.env["CODEX_HOME"] = str(self.root / "codex-home")
        self.env["ORCHESTRATE_WORK_LOCATOR"] = str(self.root / "locator" / "locator.json")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def rebuild_manifest(self) -> None:
        files = {
            path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.package.rglob("*")
            if path.is_file() and path.name != "build-info.json"
        }
        fingerprint = hashlib.sha256(
            json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        (self.package / "build-info.json").write_text(
            json.dumps({"schema_version": 1, "package_fingerprint": fingerprint, "files": files}),
            encoding="utf-8",
        )

    def cli(self, *args: str, script: str | None = None, ok: bool = True) -> dict:
        result = subprocess.run(
            [sys.executable, script or str(self.package / "scripts/orchestration.py"), *args],
            env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return {"stderr": result.stderr.decode("utf-8", "replace")}

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_repository(self, path: Path) -> str:
        path.mkdir(parents=True, exist_ok=True)
        self.git(path, "init", "--quiet")
        self.git(path, "config", "user.name", "Runtime Test")
        self.git(path, "config", "user.email", "runtime-test@example.invalid")
        (path / "tracked.txt").write_text("base\n", encoding="utf-8")
        self.git(path, "add", "tracked.txt")
        self.git(path, "-c", "user.name=Runtime Test", "-c", "user.email=runtime-test@example.invalid",
                 "commit", "--quiet", "-m", "base")
        return self.git(path, "rev-parse", "HEAD")

    def register_workspace(self, session: str, path: Path, base_commit: str, *, kind: str = "worker") -> dict:
        return self.cli("workspace-register", "--session", session, "--path", str(path),
                        "--kind", kind, "--base-commit", base_commit,
                        "--plugin-data", str(self.data))

    def activate(self, session: str = "enrolled", **kwargs: str) -> dict:
        return self.cli(
            "activate", "--session", session, "--coord-root", str(self.coord),
            "--author-repo", str(self.author), "--plugin-data", str(self.data),
            *sum((["--" + name.replace("_", "-"), value] for name, value in kwargs.items()), []),
        )

    def hook(self, event: dict, *, injected_data: Path | None = None) -> subprocess.CompletedProcess:
        env = self.env.copy()
        env["PLUGIN_ROOT"] = str(self.package)
        if injected_data is not None:
            env["PLUGIN_DATA"] = str(injected_data)
        result = subprocess.run(
            [sys.executable, str(self.package / "hooks/bootstrap.py")],
            input=json.dumps(event).encode("utf-8"), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        return result

    @staticmethod
    def spawn(session: str, **args: object) -> dict:
        return {"hook_event_name": "PreToolUse", "session_id": session,
                "tool_name": "spawn_agent", "tool_use_id": "spawn-1", "tool_input": args}

    def test_inactive_and_unrelated_sessions_are_silent_without_writes(self) -> None:
        event = self.spawn("unrelated", model="expensive", reasoning_effort="high")
        result = self.hook(event, injected_data=self.data)
        self.assertEqual((result.stdout, result.stderr), (b"", b""))
        self.assertFalse(self.data.exists())
        self.assertFalse(Path(self.env["ORCHESTRATE_WORK_LOCATOR"]).exists())
        self.activate()
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = self.hook(event)
        self.assertEqual((result.stdout, result.stderr), (b"", b""))
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}, before)

    def test_guard_routes_exact_session_via_locator_and_denies_invalid_dispatch(self) -> None:
        self.activate()
        initial = self.cli("status", "--session", "enrolled")
        self.assertFalse(initial["session_observed"])
        self.assertEqual(initial["observed_events"], {})
        cases = [
            ({"model": "gpt-6-luna", "reasoning_effort": "xhigh", "fork_turns": "none"}, True),
            ({"model": "gpt-6.1-sol", "reasoning_effort": "high", "fork_turns": "2"}, True),
            ({"model": "gpt-6.1-sol", "reasoning_effort": "high", "fork_turns": "101"}, True),
            ({"model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "fork_turns": "none"}, True),
            ({"model": "gpt-6-luna", "reasoning_effort": "high", "fork_turns": "none"}, False),
            ({"model": "gpt-6-luna", "reasoning_effort": "xhigh"}, False),
            ({"model": "gpt-6-luna", "reasoning_effort": "xhigh", "fork_turns": "all"}, False),
            ({"reasoning_effort": "xhigh", "fork_turns": "none"}, False),
            ({"model": {}, "reasoning_effort": "xhigh", "fork_turns": "none"}, False),
        ]
        for args, allowed in cases:
            with self.subTest(args=args):
                result = self.hook(self.spawn("enrolled", **args), injected_data=self.root / "unused-host-data")
                if allowed:
                    self.assertEqual(result.stdout, b"")
                else:
                    decision = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(decision["permissionDecision"], "deny")
                    self.assertTrue(decision["permissionDecisionReason"])
        self.assertFalse((self.root / "unused-host-data").exists())

    def test_installed_update_preserves_snapshot_and_missing_pin_denies_dispatch(self) -> None:
        active = self.activate()
        pinned_cli = Path(active["cli"])
        original = pinned_cli.read_bytes()
        (self.package / "scripts/orchestration.py").write_text("raise SystemExit(91)\n", encoding="utf-8")
        self.rebuild_manifest()
        event = self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh", fork_turns="none")
        result = self.hook(event)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(pinned_cli.read_bytes(), original)
        pinned_cli.unlink()
        result = self.hook(event)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertFalse(pinned_cli.exists())

    def test_recovery_has_pinned_cli_coordination_pointer_and_byte_cap(self) -> None:
        active = self.activate()
        for source in ("resume", "compact"):
            with self.subTest(source=source):
                result = self.hook({"hook_event_name": "SessionStart", "session_id": "enrolled", "source": source})
                self.assertLessEqual(len(result.stdout), 1024)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn(active["cli"], context)
                self.assertIn(str(self.coord), context)
        result = self.hook({"hook_event_name": "SessionStart", "session_id": "enrolled", "source": "startup"})
        self.assertEqual(result.stdout, b"")

    def test_pinned_and_installed_cli_enroll_coordinators_without_migrating_active_run(self) -> None:
        active = self.activate()
        (self.package / "support/skills/orchestrate-work/SKILL.md").write_text("updated resource\n", encoding="utf-8")
        self.rebuild_manifest()
        for session, script in (("from-pin", active["cli"]), ("from-installed", None)):
            with self.subTest(session=session):
                enrolled = self.cli(
                    "activate", "--session", session, "--run-id", active["run_id"],
                    "--coord-root", str(self.coord), "--author-repo", str(self.author),
                    "--plugin-data", str(self.data), script=script,
                )
                self.assertEqual(enrolled["runtime_root"], active["runtime_root"])
                self.assertEqual(enrolled["package_fingerprint"], active["package_fingerprint"])
        for session in ("enrolled", "unknown-coordinator"):
            with self.subTest(conflicting_session=session):
                self.cli(
                    "activate", "--session", session, "--run-id", "unknown-run",
                    "--coord-root", str(self.coord), "--author-repo", str(self.author),
                    "--plugin-data", str(self.data), ok=False,
                )

    def test_registered_locator_with_missing_state_denies_dispatch_without_recreating_state(self) -> None:
        self.activate()
        state = self.data / "orchestration-state.json"
        state.unlink()
        result = self.hook(self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh", fork_turns="none"))
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertFalse(state.exists())

    def test_concurrent_conflicting_activation_binds_one_data_root(self) -> None:
        data_roots = (self.root / "first-data", self.root / "second-data")
        processes = [
            subprocess.Popen(
                [sys.executable, str(self.package / "scripts/orchestration.py"), "activate",
                 "--session", "contended", "--coord-root", str(self.coord),
                 "--author-repo", str(self.author), "--plugin-data", str(data)],
                env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            for data in data_roots
        ]
        outcomes = [(process.returncode, output, error)
                    for process in processes for output, error in [process.communicate(timeout=15)]]
        self.assertEqual(sorted(item[0] for item in outcomes), [0, 2], outcomes)
        active = [self.cli("status", "--session", "contended", "--plugin-data", str(data))["active"]
                  for data in data_roots]
        self.assertEqual(sum(active), 1)
        for data, is_active in zip(data_roots, active):
            if not is_active:
                self.assertFalse((data / "orchestration-state.json").exists())
                self.assertFalse((data / "runtimes").exists())

    def test_unsafe_nested_data_root_is_rejected_before_creation(self) -> None:
        nested = self.package / "nested-data"
        self.cli("activate", "--session", "unsafe", "--coord-root", str(self.coord),
                 "--author-repo", str(self.author), "--plugin-data", str(nested), ok=False)
        self.assertFalse(nested.exists())

    def test_observations_are_session_bound_deduplicated_and_mark_missing_identity(self) -> None:
        active = self.activate()
        self.activate("coordinator", run_id=active["run_id"])
        before = self.cli("status", "--session", "enrolled")
        self.assertFalse(before["session_observed"])
        allowed = self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh", fork_turns="none")
        self.assertEqual(self.hook(allowed).stdout, b"")
        self.assertEqual(self.hook(allowed).stdout, b"")  # Same stable tool_use_id is counted once.
        same_id_other_session = self.spawn("coordinator", model="gpt-6-luna", reasoning_effort="xhigh", fork_turns="none")
        self.assertEqual(same_id_other_session["tool_use_id"], allowed["tool_use_id"])
        self.assertEqual(self.hook(same_id_other_session).stdout, b"")
        denied = self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="high", fork_turns="none")
        denied["tool_use_id"] = "spawn-denied"
        self.assertEqual(json.loads(self.hook(denied).stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        resumed = {"hook_event_name": "SessionStart", "session_id": "enrolled", "source": "resume"}
        self.assertNotEqual(self.hook(resumed).stdout, b"")
        start = {"hook_event_name": "SubagentStart", "session_id": "enrolled", "turn_id": "turn-1", "agent_id": "agent-1"}
        stop = {"hook_event_name": "SubagentStop", "session_id": "enrolled", "turn_id": "turn-1", "agent_id": "agent-1"}
        self.assertEqual(self.hook(start).stdout, b"")
        self.assertEqual(self.hook(stop).stdout, b"")
        status = self.cli("status", "--session", "enrolled")
        self.assertTrue(status["session_observed"])
        self.assertEqual(status["observed_events"], {"PreToolUse": 3, "SubagentStart": 1, "SubagentStop": 1})
        self.assertEqual(status["guard_denials"], 1)
        self.assertTrue(status["observation_incomplete"])
        self.assertEqual(status["dedup_window_size"], 256)
        run_status = self.cli("status", "--run-id", active["run_id"], "--plugin-data", str(self.data))
        self.assertEqual(run_status["session_observed"], {"coordinator": True, "enrolled": True})

    def test_concurrent_unique_hook_events_aggregate_without_lost_updates(self) -> None:
        self.activate()
        processes = []
        for index in range(12):
            event = self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh", fork_turns="none")
            event["tool_use_id"] = f"concurrent-{index}"
            processes.append(subprocess.Popen(
                [sys.executable, str(self.package / "hooks/bootstrap.py")],
                env={**self.env, "PLUGIN_ROOT": str(self.package)},
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ))
            processes[-1].stdin.write(json.dumps(event).encode("utf-8"))
            processes[-1].stdin.close()
        for process in processes:
            stdout = process.stdout.read()
            stderr = process.stderr.read()
            process.stdout.close()
            process.stderr.close()
            self.assertEqual(process.wait(timeout=15), 0, stderr.decode("utf-8", "replace"))
            self.assertEqual((stdout, stderr), (b"", b""))
        run_id = self.cli("status", "--session", "enrolled")["run_id"]
        status = self.cli("status", "--run-id", run_id, "--plugin-data", str(self.data))
        self.assertEqual(status["observed_events"]["PreToolUse"], 12)

    def test_recent_event_dedup_window_remains_bounded_through_hook_boundary(self) -> None:
        self.activate()
        state_path = self.data / "orchestration-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        run_id = state["bindings"]["enrolled"]
        state["runs"][run_id]["observations"]["recent_ids"] = [f"seed-{index}" for index in range(256)]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        event = self.spawn("enrolled", model="gpt-6-luna", reasoning_effort="xhigh", fork_turns="none")
        event["tool_use_id"] = "window-new-event"
        self.hook(event)
        self.hook(event)
        after = json.loads(state_path.read_text(encoding="utf-8"))
        recent = after["runs"][run_id]["observations"]["recent_ids"]
        self.assertEqual(len(recent), 256)
        self.assertEqual(self.cli("status", "--session", "enrolled")["observed_events"], {"PreToolUse": 1})

    def test_deactivation_prunes_last_binding_without_removing_snapshot(self) -> None:
        active = self.activate()
        self.activate("coordinator", run_id=active["run_id"])
        self.cli("deactivate", "--session", "enrolled")
        self.assertTrue(self.cli("status", "--session", "coordinator")["active"])
        self.cli("deactivate", "--session", "coordinator")
        status = self.cli("status", "--plugin-data", str(self.data))
        self.assertEqual((status["active_runs"], status["active_sessions"]), (0, 0))
        self.assertTrue(Path(active["runtime_root"]).is_dir())
        self.assertTrue(Path(active["cli"]).is_file())

    def test_workspace_retirement_ready_requires_external_refs_evidence_and_author_delivery(self) -> None:
        base_commit = self.init_repository(self.author)
        active = self.activate()
        workspace = self.root / "integration-clone"
        self.git(self.root, "clone", "--quiet", str(self.author), str(workspace))
        self.git(workspace, "config", "user.name", "Runtime Test")
        self.git(workspace, "config", "user.email", "runtime-test@example.invalid")
        self.register_workspace("enrolled", workspace, base_commit, kind="integration")

        (workspace / "integrated.txt").write_text("integrated\n", encoding="utf-8")
        self.git(workspace, "add", "integrated.txt")
        self.git(workspace, "commit", "--quiet", "-m", "integrated result")
        result_commit = self.git(workspace, "rev-parse", "HEAD")
        self.git(self.author, "update-ref", "refs/heads/orchestration-base", base_commit)
        self.git(self.author, "fetch", "--quiet", str(workspace),
                 "HEAD:refs/heads/orchestration-result")
        evidence = self.root / "delivery-evidence.txt"
        evidence.write_text("delivery result pointer\n", encoding="utf-8")
        result_pointer = self.root / "integration-result.txt"
        result_pointer.write_text("integrated result\n", encoding="utf-8")
        early_author_doc = self.root / "early-retirement-authorization.md"
        early_author_doc.write_text("author approved early retirement\n", encoding="utf-8")
        attestation = self.root / "release.json"
        statement = {
            "integration_result": str(result_pointer),
            "evidence": [str(evidence)],
            "retained_repo": str(self.author),
            "base_ref": "refs/heads/orchestration-base",
            "result_ref": "refs/heads/orchestration-result",
            "result_commit": result_commit,
            "delivery_resolved": True,
            "operations_clear": True,
            "reports_resolved": True,
            "author_commit": {
                "repo": str(self.author),
                "commit": base_commit,
                "delivery_association_attested": True,
            },
        }

        def check_statement() -> dict:
            attestation.write_text(json.dumps(statement), encoding="utf-8")
            self.cli("workspace-release", "--session", "enrolled", "--path", str(workspace),
                     "--attestation", str(attestation), "--plugin-data", str(self.data))
            return self.cli("workspace-preflight", "--session", "enrolled", "--path", str(workspace),
                            "--plugin-data", str(self.data))

        preflight = check_statement()
        self.assertTrue(preflight["ready"], preflight["reasons"])
        self.assertEqual(preflight["disposition"], "ready")
        self.assertFalse(preflight["deletes_workspace"])
        self.assertTrue(workspace.is_dir())
        self.assertEqual(self.git(self.author, "rev-parse", "refs/heads/orchestration-result^{commit}"), result_commit)
        self.assertTrue(Path(active["runtime_root"]).is_dir())

        statement.pop("author_commit")
        self.assertIn("attested author delivery commit", " ".join(check_statement()["reasons"]))
        statement["early_retirement_author_ref"] = str(early_author_doc)
        self.assertTrue(check_statement()["ready"])

        statement["integration_result"] = str(workspace / "integrated.txt")
        reasons = " ".join(check_statement()["reasons"])
        self.assertIn("integration result and workspace", reasons)
        statement["integration_result"] = str(result_pointer)
        statement["evidence"] = [str(workspace / "integrated.txt")]
        self.assertIn("retained evidence and workspace", " ".join(check_statement()["reasons"]))
        statement["evidence"] = [str(evidence)]

        for field, expected_reason in (
            ("delivery_resolved", "delivery remains unresolved"),
            ("operations_clear", "operation is not attested clear"),
            ("reports_resolved", "report remains unresolved"),
        ):
            with self.subTest(field=field):
                statement[field] = False
                reasons = " ".join(check_statement()["reasons"])
                self.assertIn(expected_reason, reasons)
                statement[field] = True

        check_statement()
        with attestation.open("a", encoding="utf-8") as stream:
            stream.write("\n")
        changed = self.cli("workspace-preflight", "--session", "enrolled", "--path", str(workspace),
                           "--plugin-data", str(self.data))
        self.assertIn("changed after registration", " ".join(changed["reasons"]))

    def test_workspace_preflight_retains_on_missing_refs_evidence_and_ignored_changes(self) -> None:
        base_commit = self.init_repository(self.author)
        self.activate()
        workspace = self.root / "worker-clone"
        self.git(self.root, "clone", "--quiet", str(self.author), str(workspace))
        self.git(workspace, "config", "user.name", "Runtime Test")
        self.git(workspace, "config", "user.email", "runtime-test@example.invalid")
        self.register_workspace("enrolled", workspace, base_commit)
        (workspace / ".gitignore").write_text("ignored-output/\n", encoding="utf-8")
        (workspace / "ignored-output").mkdir()
        (workspace / "ignored-output" / "leftover.bin").write_bytes(b"leftover")
        missing_evidence = self.root / "absent-evidence.txt"
        attestation = self.root / "incomplete-release.json"
        attestation.write_text(json.dumps({
            "integration_result": str(self.root / "result.txt"),
            "evidence": [str(missing_evidence)],
            "retained_repo": str(self.author),
            "base_ref": "refs/heads/orchestration-base-missing",
            "result_ref": "refs/heads/orchestration-result-missing",
            "result_commit": base_commit,
            "delivery_resolved": True,
            "operations_clear": False,
            "reports_resolved": True,
        }), encoding="utf-8")
        (self.root / "result.txt").write_text("result\n", encoding="utf-8")
        self.cli("workspace-release", "--session", "enrolled", "--path", str(workspace),
                 "--attestation", str(attestation), "--plugin-data", str(self.data))
        preflight = self.cli("workspace-preflight", "--session", "enrolled", "--path", str(workspace),
                             "--plugin-data", str(self.data))
        self.assertFalse(preflight["ready"])
        self.assertEqual(preflight["disposition"], "retain")
        joined = " ".join(preflight["reasons"])
        self.assertIn("ignored changes", joined)
        self.assertIn("existing file", joined)
        self.assertIn("actual Git ref", joined)
        self.assertIn("not attested clear", joined)
        self.assertTrue(workspace.is_dir())

    def test_workspace_registration_refuses_author_checkout_and_never_creates_elsewhere(self) -> None:
        base_commit = self.init_repository(self.author)
        self.activate()
        result = self.cli(
            "workspace-register", "--session", "enrolled", "--path", str(self.author),
            "--kind", "worker", "--base-commit", base_commit,
            "--plugin-data", str(self.data), ok=False,
        )
        self.assertIn("must not overlap", result["stderr"])
        state = json.loads((self.data / "orchestration-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["runs"][state["bindings"]["enrolled"]]["workspaces"], {})

    def test_workspace_preflight_retains_shared_clone_with_borrowed_objects(self) -> None:
        base_commit = self.init_repository(self.author)
        self.activate()
        workspace = self.root / "integration-clone"
        self.git(self.root, "clone", "--quiet", str(self.author), str(workspace))
        self.git(workspace, "config", "user.name", "Runtime Test")
        self.git(workspace, "config", "user.email", "runtime-test@example.invalid")
        self.register_workspace("enrolled", workspace, base_commit, kind="integration")
        (workspace / "integrated.txt").write_text("integrated\n", encoding="utf-8")
        self.git(workspace, "add", "integrated.txt")
        self.git(workspace, "commit", "--quiet", "-m", "integrated result")
        result_commit = self.git(workspace, "rev-parse", "HEAD")

        retained = self.root / "shared-retained-repo"
        self.git(self.root, "clone", "--quiet", "--shared", str(workspace), str(retained))
        self.git(retained, "update-ref", "refs/heads/orchestration-base", base_commit)
        self.git(retained, "update-ref", "refs/heads/orchestration-result", result_commit)
        alternates = retained / ".git" / "objects" / "info" / "alternates"
        self.assertTrue(alternates.is_file())
        evidence = self.root / "shared-evidence.txt"
        evidence.write_text("retained evidence\n", encoding="utf-8")
        result_pointer = self.root / "shared-result.txt"
        result_pointer.write_text("integration result\n", encoding="utf-8")
        attestation = self.root / "shared-release.json"
        attestation.write_text(json.dumps({
            "integration_result": str(result_pointer),
            "evidence": [str(evidence)],
            "retained_repo": str(retained),
            "base_ref": "refs/heads/orchestration-base",
            "result_ref": "refs/heads/orchestration-result",
            "result_commit": result_commit,
            "delivery_resolved": True,
            "operations_clear": True,
            "reports_resolved": True,
            "author_commit": {
                "repo": str(self.author),
                "commit": base_commit,
                "delivery_association_attested": True,
            },
        }), encoding="utf-8")
        self.cli("workspace-release", "--session", "enrolled", "--path", str(workspace),
                 "--attestation", str(attestation), "--plugin-data", str(self.data))
        preflight = self.cli("workspace-preflight", "--session", "enrolled", "--path", str(workspace),
                             "--plugin-data", str(self.data))
        self.assertFalse(preflight["ready"])
        self.assertIn("object store uses alternates", " ".join(preflight["reasons"]))
        self.assertTrue(workspace.is_dir())
        self.assertTrue(alternates.is_file())


if __name__ == "__main__":
    unittest.main()
