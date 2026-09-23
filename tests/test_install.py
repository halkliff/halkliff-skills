from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))
import install  # noqa: E402


@unittest.skipUnless(shutil.which("git"), "Git is required for local submodule fixtures")
class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = tempfile.TemporaryDirectory()
        cls.fixture_root = Path(cls.fixture.name)
        cls.remote = cls.fixture_root / "synthetic-upstream"
        cls.project_template = cls.fixture_root / "project-template"
        cls.remote.mkdir()
        cls.project_template.mkdir()
        cls._git(cls.remote, "init", "--quiet")
        cls._git(cls.remote, "config", "user.name", "Installer Test")
        cls._git(cls.remote, "config", "user.email", "installer@example.invalid")
        cls._write(cls.remote / "skills" / "toy" / "SKILL.md", b"upstream skill\r\n")
        cls._write(cls.remote / "skills" / "toy" / "assets" / "sample.bin", b"\x00\xff\r\n\x10")
        cls._git(cls.remote, "add", "--all")
        cls._git(cls.remote, "commit", "--quiet", "-m", "fixture")
        cls.upstream_commit = cls._git(cls.remote, "rev-parse", "HEAD").strip()

        cls._git(cls.project_template, "init", "--quiet")
        cls._git(cls.project_template, "config", "user.name", "Installer Test")
        cls._git(cls.project_template, "config", "user.email", "installer@example.invalid")
        cls._git(
            cls.project_template,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "--quiet",
            str(cls.remote),
            "upstream/toy",
        )
        cls._write(cls.project_template / "adapters" / "local" / "SKILL.md", b"local skill\r\nsecond line\r\n")
        cls._write(cls.project_template / "adapters" / "local" / "references" / "note.md", b"local note\n")
        cls._git(cls.project_template, "add", "--all")
        cls._git(cls.project_template, "commit", "--quiet", "-m", "fixture root")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.cleanup()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.remote = type(self).remote
        self.root = self.base / "project"
        shutil.copytree(type(self).project_template, self.root, symlinks=True)
        self.destination = self.base / "codex" / "skills"
        self.write_manifest(self.manifest_data())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _git(cwd: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode:
            self.fail(f"Git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    @staticmethod
    def _write(path: Path, contents: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def manifest_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "upstreams": [
                {
                    "id": "toy",
                    "path": "upstream/toy",
                    "url": str(self.remote),
                    "commit": self.upstream_commit,
                }
            ],
            "skills": [
                {
                    "name": "mixed",
                    "files": [
                        {"source": "upstream/toy/skills/toy/SKILL.md", "target": "SKILL.md"},
                        {
                            "source": "upstream/toy/skills/toy/assets/sample.bin",
                            "target": "assets/sample.bin",
                        },
                    ],
                },
                {
                    "name": "local-only",
                    "files": [
                        {"source": "adapters/local/SKILL.md", "target": "SKILL.md"},
                        {"source": "adapters/local/references/note.md", "target": "references/note.md"},
                    ],
                },
            ],
        }

    def write_manifest(self, value: dict[str, object]) -> None:
        (self.root / "dependencies.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def run_install(self, *, offline: bool = False, dry_run: bool = False) -> tuple[list[str], list[str]]:
        return install.install(root=self.root, destination=self.destination, offline=offline, dry_run=dry_run)

    def remove_submodule_checkout(self) -> None:
        shutil.rmtree(self.root / "upstream" / "toy")

    def test_installs_exact_bytes_and_preserves_binary_files(self) -> None:
        installed, identical = self.run_install()
        self.assertEqual(installed, ["mixed", "local-only"])
        self.assertEqual(identical, [])
        self.assertEqual((self.destination / "mixed" / "SKILL.md").read_bytes(), b"upstream skill\r\n")
        self.assertEqual(
            (self.destination / "mixed" / "assets" / "sample.bin").read_bytes(),
            b"\x00\xff\r\n\x10",
        )
        self.assertEqual(
            (self.destination / "local-only" / "SKILL.md").read_bytes(),
            b"local skill\r\nsecond line\r\n",
        )

    def test_identical_install_is_a_no_op(self) -> None:
        self.run_install()
        before = {
            path.relative_to(self.destination).as_posix(): path.read_bytes()
            for path in self.destination.rglob("*")
            if path.is_file()
        }
        installed, identical = self.run_install()
        after = {
            path.relative_to(self.destination).as_posix(): path.read_bytes()
            for path in self.destination.rglob("*")
            if path.is_file()
        }
        self.assertEqual(installed, [])
        self.assertEqual(identical, ["mixed", "local-only"])
        self.assertEqual(after, before)

    def test_conflict_prevents_every_new_skill_from_being_written(self) -> None:
        custom = self.destination / "local-only"
        self._write(custom / "SKILL.md", b"user customization\n")
        self.assertRaisesRegex(install.InstallError, "nothing was installed", self.run_install)
        self.assertFalse((self.destination / "mixed").exists())
        self.assertEqual((custom / "SKILL.md").read_bytes(), b"user customization\n")

    def test_offline_mode_explains_a_missing_submodule_without_writing(self) -> None:
        self.remove_submodule_checkout()
        with self.assertRaisesRegex(install.InstallError, "offline mode cannot fetch missing submodules"):
            self.run_install(offline=True)
        self.assertFalse(self.destination.exists())
        self.assertFalse((self.root / "upstream" / "toy").exists())

    def test_online_mode_initializes_a_missing_submodule_from_its_local_remote(self) -> None:
        self.remove_submodule_checkout()
        installed, _ = self.run_install()
        self.assertEqual(installed, ["mixed", "local-only"])
        checkout = self.root / "upstream" / "toy"
        self.assertTrue((checkout / "skills" / "toy" / "SKILL.md").is_file())
        self.assertEqual(self._git(checkout, "rev-parse", "HEAD").strip(), self.upstream_commit)

    def test_empty_submodule_directory_is_initialized(self) -> None:
        self.remove_submodule_checkout()
        (self.root / "upstream" / "toy").mkdir()
        installed, _ = self.run_install()
        self.assertEqual(installed, ["mixed", "local-only"])
        self.assertEqual(
            self._git(self.root / "upstream" / "toy", "rev-parse", "HEAD").strip(),
            self.upstream_commit,
        )

    def test_dry_run_does_not_write_or_initialize(self) -> None:
        installed, identical = self.run_install(dry_run=True)
        self.assertEqual(installed, ["mixed", "local-only"])
        self.assertEqual(identical, [])
        self.assertFalse(self.destination.exists())

        self.remove_submodule_checkout()
        with self.assertRaisesRegex(install.InstallError, "dry-run mode cannot fetch missing submodules"):
            self.run_install(dry_run=True)
        self.assertFalse(self.destination.exists())
        self.assertFalse((self.root / "upstream" / "toy").exists())

    def test_checkout_commit_drift_is_rejected(self) -> None:
        self._write(self.remote / "skills" / "toy" / "SKILL.md", b"changed upstream\n")
        self._git(self.remote, "add", "--all")
        self._git(self.remote, "commit", "--quiet", "-m", "drift")
        new_commit = self._git(self.remote, "rev-parse", "HEAD").strip()
        checkout = self.root / "upstream" / "toy"
        self._git(checkout, "fetch", "origin")
        self._git(checkout, "checkout", "--quiet", new_commit)
        with self.assertRaisesRegex(install.InstallError, "submodule commit mismatch"):
            self.run_install()
        self.assertFalse(self.destination.exists())

    def test_dirty_checkout_at_the_pinned_commit_is_rejected(self) -> None:
        self._write(self.root / "upstream" / "toy" / "skills" / "toy" / "SKILL.md", b"locally edited\n")
        with self.assertRaisesRegex(install.InstallError, "local changes"):
            self.run_install()
        self.assertFalse(self.destination.exists())

    def test_manifest_commit_must_match_index_gitlink(self) -> None:
        value = self.manifest_data()
        value["upstreams"][0]["commit"] = "0" * 40  # type: ignore[index]
        self.write_manifest(value)
        with self.assertRaisesRegex(install.InstallError, "pinned commit mismatch.*git index"):
            self.run_install()
        self.assertFalse(self.destination.exists())

    def test_path_traversal_in_source_and_target_is_rejected(self) -> None:
        value = self.manifest_data()
        value["skills"][0]["files"][0]["target"] = "../escaped.md"  # type: ignore[index]
        self.write_manifest(value)
        with self.assertRaisesRegex(install.InstallError, "must not be absolute or contain"):
            self.run_install()
        self.assertFalse(self.destination.exists())

        value = self.manifest_data()
        value["skills"][0]["files"][0]["source"] = "../outside.md"  # type: ignore[index]
        self.write_manifest(value)
        with self.assertRaisesRegex(install.InstallError, "must not be absolute or contain"):
            self.run_install()
        self.assertFalse(self.destination.exists())

    def test_source_symlink_is_rejected_when_supported(self) -> None:
        external = self.base / "external"
        self._write(external / "payload.md", b"outside\n")
        link = self.root / "adapters" / "linked"
        try:
            os.symlink(external, link, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"directory symlinks are unavailable: {exc}")
        value = self.manifest_data()
        value["skills"][1]["files"][0]["source"] = "adapters/linked/payload.md"  # type: ignore[index]
        self.write_manifest(value)
        with self.assertRaisesRegex(install.InstallError, "symbolic link or junction"):
            self.run_install()
        self.assertFalse(self.destination.exists())

    def test_destination_symlink_is_rejected_when_supported(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        link = self.base / "linked-destination"
        try:
            os.symlink(outside, link, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"directory symlinks are unavailable: {exc}")
        with self.assertRaisesRegex(install.InstallError, "symbolic link or junction"):
            install.install(root=self.root, destination=link)
        self.assertEqual(list(outside.iterdir()), [])

    def test_failed_second_publish_rolls_back_first_skill_and_new_destination(self) -> None:
        real_rename = os.rename
        calls = 0

        def fail_second_publish(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic publish failure")
            real_rename(source, target)

        with mock.patch.object(install.os, "rename", side_effect=fail_second_publish):
            with self.assertRaisesRegex(install.InstallError, "cannot publish skill"):
                self.run_install()
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
