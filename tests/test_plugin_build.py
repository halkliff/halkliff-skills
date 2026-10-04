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


SOURCE_ROOT = Path(__file__).resolve().parents[1]
BUILDER = SOURCE_ROOT / "scripts" / "build_plugin.py"
INSTALLER = SOURCE_ROOT / "scripts" / "install.py"


class PluginBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="plugin-builder-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.upstream = self.repo / "upstream" / "demo"
        self.destination = self.root / "package"
        self.repo.mkdir()
        self.upstream.mkdir(parents=True)
        self._init_git(self.upstream)
        self._make_upstream_history()
        self._make_repo()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _git(root: Path, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if check and result.returncode:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
        return result.stdout.strip()

    def _init_git(self, root: Path) -> None:
        self._git(root, "init", "--quiet")
        self._git(root, "config", "user.name", "Builder test")
        self._git(root, "config", "user.email", "builder@example.invalid")

    def _commit(self, root: Path, message: str) -> str:
        self._git(root, "add", "-A")
        self._git(root, "commit", "--quiet", "-m", message)
        return self._git(root, "rev-parse", "HEAD")

    def _make_upstream_history(self) -> None:
        self.pinned_skill = b"pinned skill bytes\x00\xff\n"
        self.pinned_license = b"PINNED upstream license\n"
        self.current_skill = b"working tree skill bytes\n"
        (self.upstream / "skills" / "demo").mkdir(parents=True)
        (self.upstream / "skills" / "demo" / "SKILL.md").write_bytes(self.pinned_skill)
        (self.upstream / "LICENSE").write_bytes(self.pinned_license)
        self.pin = self._commit(self.upstream, "pinned")
        (self.upstream / "skills" / "demo" / "SKILL.md").write_bytes(self.current_skill)
        (self.upstream / "LICENSE").write_bytes(b"HEAD license, not package license\n")
        self.head = self._commit(self.upstream, "working checkout update")

    def _portable_manifest(self) -> dict:
        return {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": "fixture-plugin",
            "version": "0.1.0",
            "description": "builder fixture",
            "author": {"name": "fixture"},
            "extensions": {
                "com.openai": {
                    "hooks": "./hooks/hooks.json",
                    "interface": {
                        "displayName": "Fixture",
                        "shortDescription": "Test plugin",
                    },
                }
            },
        }

    def _make_repo(self, *, overlay: bool = True) -> None:
        plugin = self.repo / "plugin"
        (plugin / "hooks").mkdir(parents=True)
        (plugin / "scripts").mkdir()
        (plugin / "skills" / "orchestrate-work-plugin" / "agents").mkdir(parents=True)
        manifest = self._portable_manifest()
        (plugin / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        (plugin / "hooks" / "hooks.json").write_text('{"hooks":{}}\n', encoding="utf-8")
        (plugin / "hooks" / "bootstrap.py").write_text("bootstrap fixture\n", encoding="utf-8")
        (plugin / "scripts" / "orchestration.py").write_text("cli fixture\n", encoding="utf-8")
        (plugin / "skills" / "orchestrate-work-plugin" / "SKILL.md").write_text("wrapper fixture\n", encoding="utf-8")
        (plugin / "skills" / "orchestrate-work-plugin" / "agents" / "openai.yaml").write_text("display_name: Fixture\n", encoding="utf-8")
        (plugin / "unlisted-secret.txt").write_text("must not enter package\n", encoding="utf-8")
        if overlay:
            compatible = {
                "name": manifest["name"],
                "version": manifest["version"],
                "description": manifest["description"],
                "author": manifest["author"],
                "skills": "./skills/",
                "hooks": manifest["extensions"]["com.openai"]["hooks"],
                "interface": manifest["extensions"]["com.openai"]["interface"],
            }
            (plugin / ".codex-plugin").mkdir()
            (plugin / ".codex-plugin" / "plugin.json").write_text(json.dumps(compatible), encoding="utf-8")

        (self.repo / "adapters" / "demo").mkdir(parents=True)
        (self.repo / "adapters" / "demo" / "asset.bin").write_bytes(b"local asset\x00\xfe")
        (self.repo / "LICENSE").write_text("Top-level license\n", encoding="utf-8")
        (self.repo / "scripts").mkdir()
        shutil.copyfile(BUILDER, self.repo / "scripts" / "build_plugin.py")
        shutil.copyfile(INSTALLER, self.repo / "scripts" / "install.py")
        manifest_data = {
            "schema_version": 1,
            "upstreams": [{
                "id": "fixture-upstream",
                "path": "upstream/demo",
                "url": "https://example.invalid/fixture.git",
                "commit": self.pin,
            }],
            "skills": [{
                "name": "demo",
                "files": [
                    {"source": "upstream/demo/skills/demo/SKILL.md", "target": "SKILL.md"},
                    {"source": "upstream/demo/LICENSE", "target": "LICENSE.txt"},
                    {"source": "adapters/demo/asset.bin", "target": "assets/local.bin"},
                ],
            }],
        }
        (self.repo / "dependencies.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (self.repo / ".gitmodules").write_text(
            '[submodule "fixture-upstream"]\n\tpath = upstream/demo\n\turl = https://example.invalid/fixture.git\n',
            encoding="utf-8",
        )
        self._init_git(self.repo)
        self._git(self.repo, "add", "-A", "--", ".", ":!upstream")
        self._git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{self.pin},upstream/demo")
        self._git(self.repo, "commit", "--quiet", "-m", "fixture")
        self.repo_revision = self._git(self.repo, "rev-parse", "HEAD")

    def _run(self, *args: str, env: dict[str, str] | None = None, success: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, str(self.repo / "scripts" / "build_plugin.py"), *args],
            cwd=self.repo,
            env=env or os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    @staticmethod
    def _tree(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    def test_build_uses_pinned_blobs_and_emits_closed_hash_inventory(self) -> None:
        before_parent_head = self._git(self.repo, "rev-parse", "HEAD")
        before_upstream_head = self._git(self.upstream, "rev-parse", "HEAD")
        env = os.environ.copy()
        env["GIT_DIR"] = str(self.root / "wrong-git-dir")
        env["GIT_WORK_TREE"] = str(self.root / "wrong-worktree")
        result = self._run("--dest", str(self.destination), env=env)
        output = json.loads(result.stdout)
        self.assertEqual(output["action"], "built")
        self.assertNotEqual(self.head, self.pin)
        self.assertEqual(self._git(self.upstream, "rev-parse", "HEAD"), self.head)
        self.assertEqual(self._git(self.repo, "rev-parse", "HEAD"), before_parent_head)
        self.assertEqual(output["source_revision"], self.repo_revision)

        self.assertEqual((self.destination / "support/skills/demo/SKILL.md").read_bytes(), self.pinned_skill)
        self.assertEqual((self.destination / "support/skills/demo/LICENSE.txt").read_bytes(), self.pinned_license)
        self.assertEqual((self.destination / "support/skills/demo/assets/local.bin").read_bytes(), b"local asset\x00\xfe")
        self.assertEqual((self.destination / "LICENSE").read_text(encoding="utf-8"), "Top-level license\n")
        self.assertFalse((self.destination / "unlisted-secret.txt").exists())
        self.assertEqual(sorted(path.name for path in (self.destination / "skills").iterdir()), ["orchestrate-work-plugin"])
        self.assertTrue((self.destination / ".codex-plugin/plugin.json").is_file())

        info = json.loads((self.destination / "build-info.json").read_text(encoding="utf-8"))
        package_files = self._tree(self.destination)
        self.assertEqual(set(info["files"]), set(package_files) - {"build-info.json"})
        for relative, digest in info["files"].items():
            self.assertEqual(hashlib.sha256(package_files[relative]).hexdigest(), digest)
        expected_fingerprint = hashlib.sha256(
            json.dumps(info["files"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(info["package_fingerprint"], expected_fingerprint)
        self.assertEqual(output["package_fingerprint"], expected_fingerprint)
        self.assertEqual(info["manifest_pins"], {"fixture-upstream": self.pin})
        self.assertEqual(self._git(self.repo, "rev-parse", "HEAD"), before_parent_head)
        self.assertEqual(self._git(self.upstream, "rev-parse", "HEAD"), before_upstream_head)

    def test_identical_destination_is_unchanged_and_conflict_is_never_overwritten(self) -> None:
        self._run("--dest", str(self.destination))
        before = self._tree(self.destination)
        mtimes = {path: path.stat().st_mtime_ns for path in self.destination.rglob("*") if path.is_file()}
        repeated = json.loads(self._run("--dest", str(self.destination)).stdout)
        self.assertEqual(repeated["action"], "already-current")
        self.assertEqual(self._tree(self.destination), before)
        self.assertEqual({path: path.stat().st_mtime_ns for path in mtimes}, mtimes)

        target = self.destination / "LICENSE"
        target.write_bytes(b"destination owner data\n")
        conflicted = self._tree(self.destination)
        result = self._run("--dest", str(self.destination), success=False)
        self.assertIn(b"left untouched", result.stderr)
        self.assertEqual(self._tree(self.destination), conflicted)

    def test_dry_run_and_source_overlap_refusal_do_not_write(self) -> None:
        dry = json.loads(self._run("--dest", str(self.destination), "--dry-run").stdout)
        self.assertEqual(dry["action"], "would-build")
        self.assertFalse(self.destination.exists())
        before_plugin = self._tree(self.repo / "plugin")
        result = self._run("--dest", str(self.repo / "plugin"), success=False)
        self.assertIn(b"overlap", result.stderr)
        self.assertEqual(self._tree(self.repo / "plugin"), before_plugin)

    def test_unsafe_manifest_path_is_rejected_before_output(self) -> None:
        manifest_path = self.repo / "dependencies.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["skills"][0]["files"][0]["target"] = "../escape.md"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self._run("--dest", str(self.destination), success=False)
        self.assertIn(b"target", result.stderr.lower())
        self.assertFalse(self.destination.exists())

    def test_unsafe_destination_names_are_rejected_before_parent_creation(self) -> None:
        for name in ("CON", "trailing.", "trailing "):
            with self.subTest(name=name):
                parent = self.root / "new-output-parent"
                result = self._run("--dest", str(parent / name), success=False)
                self.assertIn(b"output path", result.stderr)
                self.assertFalse(parent.exists())

    def test_missing_pinned_git_object_is_rejected_without_output(self) -> None:
        missing = "f" * 40
        manifest_path = self.repo / "dependencies.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["upstreams"][0]["commit"] = missing
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self._git(self.repo, "update-index", "--cacheinfo", f"160000,{missing},upstream/demo")
        result = self._run("--dest", str(self.destination), success=False)
        self.assertIn(b"cat-file", result.stderr)
        self.assertFalse(self.destination.exists())

    def test_pinned_symlink_blob_is_rejected_before_package_write(self) -> None:
        target_blob = subprocess.run(
            ["git", "-C", str(self.upstream), "hash-object", "-w", "--stdin"],
            input=b"target.txt\n", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.decode("ascii").strip()
        self._git(self.upstream, "update-index", "--cacheinfo", f"120000,{target_blob},skills/demo/SKILL.md")
        tree = self._git(self.upstream, "write-tree")
        symlink_commit = subprocess.run(
            ["git", "-C", str(self.upstream), "-c", "user.name=Builder test", "-c",
             "user.email=builder@example.invalid", "commit-tree", tree, "-p", self.pin, "-m", "symlink pin"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", check=True,
        ).stdout.strip()
        manifest_path = self.repo / "dependencies.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["upstreams"][0]["commit"] = symlink_commit
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self._git(self.repo, "update-index", "--cacheinfo", f"160000,{symlink_commit},upstream/demo")
        result = self._run("--dest", str(self.destination), success=False)
        self.assertIn(b"regular file", result.stderr)
        self.assertFalse(self.destination.exists())

    def test_mismatched_optional_compatibility_manifest_is_rejected(self) -> None:
        overlay_path = self.repo / "plugin" / ".codex-plugin" / "plugin.json"
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        overlay["interface"]["displayName"] = "Drifted"
        overlay_path.write_text(json.dumps(overlay), encoding="utf-8")
        result = self._run("--dest", str(self.destination), success=False)
        self.assertIn(b"not synchronized", result.stderr)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
