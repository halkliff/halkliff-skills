from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "orchestrate-work" / "scripts" / "git_workflow.py"


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    if extra:
        env.update(extra)
    return env


def git(repo: Path, *args: str, input_bytes: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=clean_env(),
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result


def create_repo(path: Path, *, autocrlf: str | None = None) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Synthetic Author")
    git(path, "config", "user.email", "author@example.invalid")
    if autocrlf is not None:
        git(path, "config", "core.autocrlf", autocrlf)
    return path


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "-A", "--", ".")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.decode().strip()


def write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8", newline="")
    else:
        path.write_bytes(content)


def object_inventory(repo: Path) -> tuple[tuple[str, str], ...]:
    objects = Path(git(repo, "rev-parse", "--git-path", "objects").stdout.decode().strip())
    if not objects.is_absolute():
        objects = repo / objects
    files = []
    for path in objects.rglob("*"):
        if path.is_file():
            files.append((path.relative_to(objects).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return tuple(sorted(files))


def author_metadata(repo: Path) -> tuple[bytes, bytes, bytes, tuple[tuple[str, str], ...]]:
    head_file = Path(git(repo, "rev-parse", "--git-path", "HEAD").stdout.decode().strip())
    index_file = Path(git(repo, "rev-parse", "--git-path", "index").stdout.decode().strip())
    if not head_file.is_absolute():
        head_file = repo / head_file
    if not index_file.is_absolute():
        index_file = repo / index_file
    refs = git(repo, "for-each-ref", "--format=%(refname)%00%(objectname)%00").stdout
    return head_file.read_bytes(), refs, index_file.read_bytes(), object_inventory(repo)


class GitWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="git-workflow-tests-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def cli(self, *args: str, ok: bool = True) -> tuple[subprocess.CompletedProcess[bytes], dict[str, object] | None]:
        hostile = {
            "GIT_DIR": str(self.root / "wrong-git-dir"),
            "GIT_WORK_TREE": str(self.root / "wrong-worktree"),
            "GIT_INDEX_FILE": str(self.root / "wrong-index"),
            "GIT_OBJECT_DIRECTORY": str(self.root / "wrong-objects"),
            "GIT_TRACE": str(self.root / "git-trace.log"),
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=clean_env(hostile),
            check=False,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
            return result, json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"git_workflow:", result.stderr)
        return result, None

    def prepare(self, author: Path, clone: Path, *options: str) -> dict[str, object]:
        _result, payload = self.cli("prepare", "--author", str(author), "--clone", str(clone), *options)
        assert payload is not None
        return payload

    def commit_integration(self, clone: Path, message: str) -> str:
        git(clone, "config", "user.name", "Integration Worker")
        git(clone, "config", "user.email", "worker@example.invalid")
        return commit_all(clone, message)

    def integration_state_path(self, clone: Path) -> Path:
        path = Path(git(clone, "rev-parse", "--git-path", "orchestrate-work-state.json").stdout.decode().strip())
        return path if path.is_absolute() else clone / path

    def test_prepare_captures_dirty_baseline_without_touching_author_index_refs_or_objects(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "tracked.txt", "base\n")
        write(author / "notes.txt", "notes\n")
        write(author / ".gitignore", "ignored.out\n")
        git(author, "add", "--", ".gitignore", "notes.txt", "tracked.txt")
        git(author, "commit", "-m", "base")

        write(author / "tracked.txt", "base\nstaged line\n")
        git(author, "add", "--", "tracked.txt")
        write(author / "tracked.txt", "base\nstaged line\nunstaged line\n")
        write(author / "notes.txt", "dirty notes\n")
        write(author / "staged-new.txt", "staged addition\n")
        git(author, "add", "--", "staged-new.txt")
        write(author / "selected-new.ts", "export const baseline = true;\n")
        write(author / "unselected.txt", "leave out\n")
        write(author / "ignored.out", "leave out too\n")
        metadata_before = author_metadata(author)
        status_before = git(author, "status", "--short").stdout

        clone = self.root / "integration"
        payload = self.prepare(
            author,
            clone,
            "--allow",
            "tracked.txt",
            "--allow",
            "notes.txt",
            "--allow",
            "staged-new.txt",
            "--allow",
            "selected-new.ts",
            "--untracked",
            "selected-new.ts",
        )
        baseline = str(payload["baseline_commit"])
        self.assertEqual(git(clone, "rev-parse", "HEAD").stdout.decode().strip(), baseline)
        self.assertEqual(git(clone, "show", f"{baseline}:tracked.txt").stdout, b"base\nstaged line\nunstaged line\n")
        self.assertEqual(git(clone, "show", f"{baseline}:staged-new.txt").stdout, b"staged addition\n")
        self.assertEqual(git(clone, "show", f"{baseline}:selected-new.ts").stdout, b"export const baseline = true;\n")
        self.assertNotEqual(git(clone, "cat-file", "-e", f"{baseline}:unselected.txt", check=False).returncode, 0)
        self.assertNotEqual(git(clone, "cat-file", "-e", f"{baseline}:ignored.out", check=False).returncode, 0)
        self.assertEqual(git(clone, "remote").stdout, b"")
        self.assertEqual(author_metadata(author), metadata_before)
        self.assertEqual(git(author, "status", "--short").stdout, status_before)
        _result, state = self.cli("status", "--clone", str(clone))
        assert state is not None
        self.assertTrue(state["author_matches_checkpoint"])

    def test_binary_and_crlf_delivery_with_and_without_attributes_is_repeatable(self) -> None:
        for variant, attributes in (("autocrlf-noattrs", False), ("autocrlf-attrs", True)):
            with self.subTest(variant=variant):
                author = create_repo(self.root / variant, autocrlf="true")
                if attributes:
                    write(author / ".gitattributes", "*.txt text eol=crlf\n")
                write(author / "content.txt", "before\nline\n")
                write(author / "payload.bin", b"\x00\x01old\xff\n")
                commit_all(author, "base")
                write(author / "content.txt", b"before\r\nline\r\nauthor staged\r\n")
                git(author, "add", "--", "content.txt")
                write(author / "content.txt", b"before\r\nline\r\nauthor staged\r\nauthor unstaged\r\n")
                metadata_before = author_metadata(author)

                clone = self.root / f"{variant}-integration"
                self.prepare(
                    author,
                    clone,
                    "--allow",
                    "content.txt",
                    "--allow",
                    "payload.bin",
                    "--allow",
                    "agent-new.bin",
                )
                baseline = self.cli_status_checkpoint(clone)
                write(clone / "content.txt", "before\nline\nagent line\n")
                write(clone / "payload.bin", b"\x00\x01new\xff\x00bytes")
                write(clone / "agent-new.bin", b"new binary\x00")
                candidate = self.commit_integration(clone, "candidate")
                _result, delivered = self.cli("deliver", "--clone", str(clone), "--candidate", candidate)
                assert delivered is not None
                self.assertEqual(delivered["integration_range"], f"{baseline}..{candidate}")
                self.assertEqual((author / "payload.bin").read_bytes(), b"\x00\x01new\xff\x00bytes")
                self.assertEqual((author / "agent-new.bin").read_bytes(), b"new binary\x00")
                self.assertIn(b"agent line\r\n", (author / "content.txt").read_bytes())
                self.assertEqual(author_metadata(author), metadata_before)

                _result, repeated = self.cli("deliver", "--clone", str(clone), "--candidate", candidate)
                assert repeated is not None
                self.assertEqual(repeated["status"], "already_delivered")
                self.assertEqual((author / "content.txt").read_bytes().count(b"agent line"), 1)
                _result, state = self.cli("status", "--clone", str(clone))
                assert state is not None
                self.assertTrue(state["author_matches_checkpoint"])

    def cli_status_checkpoint(self, clone: Path) -> str:
        _result, state = self.cli("status", "--clone", str(clone))
        assert state is not None
        return str(state["integration_from"])

    def test_delivery_rejects_candidate_outside_scope_and_preserves_author_files(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "allowed.txt", "base\n")
        write(author / "outside.txt", "base outside\n")
        commit_all(author, "base")
        clone = self.root / "integration"
        self.prepare(author, clone, "--allow", "allowed.txt")
        write(clone / "allowed.txt", "candidate allowed\n")
        write(clone / "outside.txt", "candidate outside\n")
        candidate = self.commit_integration(clone, "out of scope")
        before = author_metadata(author)
        self.cli("deliver", "--clone", str(clone), "--candidate", candidate, ok=False)
        self.assertEqual((author / "allowed.txt").read_text(), "base\n")
        self.assertEqual((author / "outside.txt").read_text(), "base outside\n")
        self.assertEqual(author_metadata(author), before)

    def test_delivery_rejects_stale_tracked_baseline_without_overwriting_author_edit(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "allowed.txt", "base\n")
        write(author / "other.txt", "author baseline\n")
        commit_all(author, "base")
        clone = self.root / "integration"
        self.prepare(author, clone, "--allow", "allowed.txt")
        write(clone / "allowed.txt", "candidate\n")
        candidate = self.commit_integration(clone, "candidate")
        write(author / "other.txt", "new author edit\n")
        metadata_before = author_metadata(author)
        self.cli("deliver", "--clone", str(clone), "--candidate", candidate, ok=False)
        self.assertEqual((author / "other.txt").read_text(), "new author edit\n")
        self.assertEqual((author / "allowed.txt").read_text(), "base\n")
        self.assertEqual(author_metadata(author), metadata_before)

    def test_interrupted_delivery_retry_recognizes_candidate_tree_with_new_files(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "existing.txt", "base\n")
        commit_all(author, "base")
        clone = self.root / "integration"
        self.prepare(author, clone, "--allow", "existing.txt", "--allow", "new-agent.txt")
        initial = git(clone, "rev-parse", "HEAD").stdout.decode().strip()
        write(clone / "existing.txt", "candidate\n")
        write(clone / "new-agent.txt", "new\n")
        candidate = self.commit_integration(clone, "candidate")
        state_path = self.integration_state_path(clone)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["pending"] = {
            "from": initial,
            "to": candidate,
            "tree": git(clone, "rev-parse", f"{candidate}^{{tree}}").stdout.decode().strip(),
            "before_tree": state["expected_author_tree"],
        }
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        patch = git(clone, "diff", "--binary", "--full-index", "--no-renames", initial, candidate).stdout
        git(author, "apply", input_bytes=patch)

        _result, payload = self.cli("deliver", "--clone", str(clone), "--candidate", candidate)
        assert payload is not None
        self.assertEqual(payload["status"], "delivered")
        self.assertEqual((author / "new-agent.txt").read_text(), "new\n")
        _result, repeated = self.cli("deliver", "--clone", str(clone), "--candidate", candidate)
        assert repeated is not None
        self.assertEqual(repeated["status"], "already_delivered")

    def test_interrupted_mixed_add_delete_detects_zero_partial_and_full_application(self) -> None:
        for case in ("zero", "partial", "full"):
            with self.subTest(case=case):
                author = create_repo(self.root / f"author-{case}")
                write(author / "old.txt", "old baseline\n")
                write(author / "stable.txt", "stable baseline\n")
                commit_all(author, "base")
                clone = self.root / f"integration-{case}"
                self.prepare(author, clone, "--allow", "old.txt", "--allow", "new.txt", "--allow", "stable.txt")
                initial = git(clone, "rev-parse", "HEAD").stdout.decode().strip()
                git(clone, "rm", "--", "old.txt")
                write(clone / "new.txt", "new candidate\n")
                candidate = self.commit_integration(clone, "delete and add")

                state_path = self.integration_state_path(clone)
                state = json.loads(state_path.read_text(encoding="utf-8"))
                candidate_tree = git(clone, "rev-parse", f"{candidate}^{{tree}}").stdout.decode().strip()
                state["pending"] = {
                    "from": initial,
                    "to": candidate,
                    "tree": candidate_tree,
                    "before_tree": state["expected_author_tree"],
                }
                state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

                if case == "partial":
                    write(author / "new.txt", "new candidate\n")
                elif case == "full":
                    patch = git(clone, "diff", "--binary", "--full-index", "--no-renames", initial, candidate).stdout
                    git(author, "apply", input_bytes=patch)

                result, payload = self.cli("deliver", "--clone", str(clone), "--candidate", candidate, ok=case != "partial")
                if case == "partial":
                    self.assertEqual((author / "old.txt").read_text(), "old baseline\n")
                    self.assertEqual((author / "new.txt").read_text(), "new candidate\n")
                    self.assertEqual((author / "stable.txt").read_text(), "stable baseline\n")
                    state_after = json.loads(state_path.read_text(encoding="utf-8"))
                    self.assertEqual(state_after["delivered"], initial)
                    self.assertIsNotNone(state_after["pending"])
                    self.assertIsNone(payload)
                else:
                    assert payload is not None
                    self.assertEqual(payload["status"], "delivered")
                    self.assertFalse((author / "old.txt").exists())
                    self.assertEqual((author / "new.txt").read_text(), "new candidate\n")
                    self.assertEqual((author / "stable.txt").read_text(), "stable baseline\n")

    def test_recreated_historical_deletion_is_visible_to_status_and_blocks_next_delivery(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "old.txt", "old baseline\n")
        write(author / "new.txt", "new baseline\n")
        commit_all(author, "base")
        clone = self.root / "integration"
        self.prepare(author, clone, "--allow", "old.txt", "--allow", "new.txt")
        git(clone, "rm", "--", "old.txt")
        write(clone / "new.txt", "candidate one\n")
        first = self.commit_integration(clone, "delete old")
        self.cli("deliver", "--clone", str(clone), "--candidate", first)

        write(author / "old.txt", "recreated stale file\n")
        _result, stale_status = self.cli("status", "--clone", str(clone))
        assert stale_status is not None
        self.assertFalse(stale_status["author_matches_checkpoint"])

        write(clone / "new.txt", "candidate two\n")
        second = self.commit_integration(clone, "next change")
        self.cli("deliver", "--clone", str(clone), "--candidate", second, ok=False)
        self.assertEqual((author / "old.txt").read_text(), "recreated stale file\n")
        self.assertEqual((author / "new.txt").read_text(), "candidate one\n")
        state = json.loads(self.integration_state_path(clone).read_text(encoding="utf-8"))
        self.assertEqual(state["delivered"], first)

    def test_prepare_rejects_path_traversal_and_unsupported_unmerged_index_before_clone(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "file.txt", "base\n")
        commit_all(author, "base")
        traversal_clone = self.root / "traversal-clone"
        self.cli("prepare", "--author", str(author), "--clone", str(traversal_clone), "--allow", "../escape", ok=False)
        self.assertFalse(traversal_clone.exists())

        git(author, "switch", "-c", "side")
        write(author / "file.txt", "side\n")
        commit_all(author, "side")
        git(author, "switch", "main")
        write(author / "file.txt", "main\n")
        commit_all(author, "main")
        git(author, "merge", "side", check=False)
        self.assertNotEqual(git(author, "ls-files", "--unmerged").stdout, b"")
        unsupported_clone = self.root / "unsupported-clone"
        self.cli("prepare", "--author", str(author), "--clone", str(unsupported_clone), "--allow", "file.txt", ok=False)
        self.assertFalse(unsupported_clone.exists())

    def test_prepare_rejects_custom_filters_sparse_checkout_and_symlink_candidate(self) -> None:
        filtered = create_repo(self.root / "filtered")
        write(filtered / ".gitattributes", "*.txt filter=example\n")
        write(filtered / "file.txt", "base\n")
        git(filtered, "config", "filter.example.clean", "cat")
        git(filtered, "config", "filter.example.smudge", "cat")
        commit_all(filtered, "base")
        filter_clone = self.root / "filter-clone"
        self.cli("prepare", "--author", str(filtered), "--clone", str(filter_clone), "--allow", "file.txt", ok=False)
        self.assertFalse(filter_clone.exists())

        sparse = create_repo(self.root / "sparse")
        write(sparse / "file.txt", "base\n")
        commit_all(sparse, "base")
        git(sparse, "config", "core.sparseCheckout", "true")
        sparse_clone = self.root / "sparse-clone"
        self.cli("prepare", "--author", str(sparse), "--clone", str(sparse_clone), "--allow", "file.txt", ok=False)
        self.assertFalse(sparse_clone.exists())

        author = create_repo(self.root / "symlink-author")
        write(author / "file.txt", "base\n")
        commit_all(author, "base")
        clone = self.root / "symlink-integration"
        self.prepare(author, clone, "--allow", "link")
        blob = git(clone, "hash-object", "-w", "--stdin", input_bytes=b"target").stdout.decode().strip()
        git(clone, "update-index", "--add", "--cacheinfo", "120000", blob, "link")
        tree = git(clone, "write-tree").stdout.decode().strip()
        parent = git(clone, "rev-parse", "HEAD").stdout.decode().strip()
        candidate = git(clone, "commit-tree", tree, "-p", parent, "-m", "symlink",).stdout.decode().strip()
        git(clone, "update-ref", "refs/heads/test-symlink", candidate)
        self.cli("deliver", "--clone", str(clone), "--candidate", candidate, ok=False)
        self.assertFalse((author / "link").exists())

    def test_candidate_attribute_control_change_is_rejected_before_author_apply(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "content.txt", "base\n")
        commit_all(author, "base")
        clone = self.root / "integration"
        self.prepare(author, clone, "--allow", "content.txt", "--allow", ".gitattributes")
        write(clone / ".gitattributes", "*.txt filter=example\n")
        write(clone / "content.txt", "candidate\n")
        candidate = self.commit_integration(clone, "candidate filter")
        metadata_before = author_metadata(author)
        self.cli("deliver", "--clone", str(clone), "--candidate", candidate, ok=False)
        self.assertEqual((author / "content.txt").read_text(), "base\n")
        self.assertFalse((author / ".gitattributes").exists())
        self.assertEqual(author_metadata(author), metadata_before)

    def test_argument_path_starting_with_dash_is_literal(self) -> None:
        author = create_repo(self.root / "author")
        write(author / "--odd.txt", "base\n")
        commit_all(author, "base")
        clone = self.root / "integration"
        self.prepare(author, clone, "--allow=--odd.txt")
        write(clone / "--odd.txt", "changed\n")
        candidate = self.commit_integration(clone, "change odd name")
        self.cli("deliver", "--clone", str(clone), "--candidate", candidate)
        self.assertEqual((author / "--odd.txt").read_text(), "changed\n")


if __name__ == "__main__":
    unittest.main()
