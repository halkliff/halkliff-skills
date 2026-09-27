#!/usr/bin/env python3
"""Capture an author's dirty baseline and deliver integration commits safely."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from typing import Any


class WorkflowError(Exception):
    pass


def _environment(overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"})
    if overrides:
        env.update(overrides)
    return env


def _git(
    repo: Path,
    *args: str,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> bytes:
    command = ["git", "--no-pager", "-C", str(repo), "-c", "core.fsmonitor=false", *args]
    try:
        result = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_environment(env),
            check=False,
        )
    except OSError as exc:
        raise WorkflowError(f"could not run Git: {exc}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise WorkflowError(f"git {' '.join(args)} failed ({result.returncode}): {detail}")
    return result.stdout


def _git_code(
    repo: Path,
    *args: str,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> tuple[int, bytes, bytes]:
    command = ["git", "--no-pager", "-C", str(repo), "-c", "core.fsmonitor=false", *args]
    try:
        result = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_environment(env),
            check=False,
        )
    except OSError as exc:
        raise WorkflowError(f"could not run Git: {exc}") from exc
    return result.returncode, result.stdout, result.stderr


def _text(data: bytes) -> str:
    return data.decode("utf-8", "surrogateescape").strip()


def _git_path(repo: Path, name: str) -> Path:
    raw = _text(_git(repo, "rev-parse", "--git-path", name))
    path = Path(raw)
    return (repo / path).resolve() if not path.is_absolute() else path.resolve()


def _repo_root(path: Path) -> Path:
    root = Path(_text(_git(path, "rev-parse", "--show-toplevel"))).resolve(strict=True)
    if root != path.resolve(strict=True):
        raise WorkflowError(f"repository path is not its worktree root: {path}")
    git_dir = Path(_text(_git(path, "rev-parse", "--absolute-git-dir"))).resolve()
    common_dir = Path(_text(_git(path, "rev-parse", "--git-common-dir")))
    if not common_dir.is_absolute():
        common_dir = (path / common_dir).resolve()
    if git_dir != common_dir.resolve():
        raise WorkflowError("linked worktrees are not supported")
    if _git(path, "rev-parse", "--is-bare-repository").strip() == b"true":
        raise WorkflowError("bare repositories are not supported")
    return root


def _source_head(repo: Path) -> str:
    head = _text(_git(repo, "rev-parse", "--verify", "HEAD^{commit}"))
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", head):
        raise WorkflowError("Git returned an unsupported commit id")
    return head.lower()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(repo: Path) -> dict[str, str]:
    head_file = _git_path(repo, "HEAD")
    index_file = _git_path(repo, "index")
    try:
        head_bytes = head_file.read_bytes()
        index_bytes = index_file.read_bytes()
    except OSError as exc:
        raise WorkflowError(f"cannot read the repository HEAD or index: {exc}") from exc
    refs = _git(repo, "for-each-ref", "--format=%(refname)%00%(objectname)%00")
    return {
        "head": _source_head(repo),
        "head_file": _sha(head_bytes),
        "refs": _sha(refs),
        "index": _sha(index_bytes),
    }


def _relative_path(value: str) -> str:
    if not value or "\x00" in value or "\\" in value or ":" in value:
        raise WorkflowError(f"invalid repository-relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise WorkflowError(f"path must stay inside the repository: {value!r}")
    normalized = path.as_posix()
    if normalized == ".git" or normalized.startswith(".git/"):
        raise WorkflowError("Git metadata paths cannot be selected")
    return normalized


def _pathspec(path: str) -> str:
    return f":(top,literal){path}"


def _safe_worktree_components(repo: Path, relative: str) -> None:
    current = repo
    for part in relative.split("/"):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise WorkflowError(f"symlink or reparse-point path is not supported: {relative}")
        try:
            current.resolve(strict=False).relative_to(repo)
        except ValueError as exc:
            raise WorkflowError(f"path escapes repository: {relative}") from exc


def _tree_entries(repo: Path, commit: str) -> dict[str, tuple[str, str]]:
    raw = _git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    entries: dict[str, tuple[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, _kind, object_id = metadata.decode("ascii").split(" ", 2)
        path = os.fsdecode(path_bytes)
        _relative_path(path)
        if mode == "160000":
            raise WorkflowError("repositories containing submodules are not supported")
        entries[path] = (mode, object_id)
    return entries


def _check_preflight(repo: Path, selected_untracked: list[str]) -> None:
    unmerged = _git(repo, "ls-files", "--unmerged")
    if unmerged:
        raise WorkflowError("unmerged index entries are not supported")

    sparse = _git(repo, "config", "--bool", "--get", "core.sparseCheckout", check=False)
    if sparse.strip().lower() == b"true":
        raise WorkflowError("sparse checkouts are not supported")
    if sparse.strip() and sparse.strip().lower() != b"false":
        raise WorkflowError("could not determine sparse-checkout state")

    tagged = _git(repo, "ls-files", "-v", "-z")
    for record in tagged.split(b"\0"):
        if record and (record[:1] == b"S" or record[:1].islower()):
            raise WorkflowError("sparse or assume-unchanged index entries are not supported")

    for record in _git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        metadata = record.split(b"\t", 1)[0].split()
        if metadata[0] == b"160000" or metadata[2] != b"0":
            raise WorkflowError("submodules and unmerged entries are not supported")

    tracked = _git(repo, "ls-files", "-z").split(b"\0")
    paths = [item for item in tracked if item]
    paths.extend(os.fsencode(path) for path in selected_untracked)
    if paths:
        attrs = _git(repo, "check-attr", "-z", "--stdin", "filter", input_bytes=b"\0".join(paths) + b"\0")
        fields = attrs.split(b"\0")
        for offset in range(0, len(fields) - 2, 3):
            value = fields[offset + 2]
            if value not in (b"unspecified", b"unset", b""):
                raise WorkflowError("custom Git clean/smudge filters are not supported")


def _object_dir(repo: Path) -> Path:
    return _git_path(repo, "objects")


def _snapshot_tree(
    author: Path,
    integration: Path,
    base: str,
    selected_untracked: list[str],
    extra_paths: list[str],
) -> str:
    integration_git = _git_path(integration, "")
    object_dir = _object_dir(integration)
    alternate = _object_dir(author)
    base_entries = _tree_entries(integration, base)
    _check_preflight(author, selected_untracked)
    for path in extra_paths:
        if path in base_entries:
            continue
        _relative_path(path)
        _safe_worktree_components(author, path)

    with tempfile.TemporaryDirectory(prefix="orchestrate-work-", dir=integration_git) as temp_dir:
        index_path = str(Path(temp_dir) / "index")
        env = {
            "GIT_INDEX_FILE": index_path,
            "GIT_OBJECT_DIRECTORY": str(object_dir),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(alternate),
        }
        _git(author, "read-tree", base, env=env)
        _git(author, "add", "-u", "--", ".", env=env)
        absent_from_base = []
        for path in extra_paths:
            if path in base_entries:
                continue
            file = author.joinpath(*path.split("/"))
            if file.exists() or file.is_symlink():
                if not file.is_file() or file.is_symlink():
                    raise WorkflowError(f"known path is not a regular file: {path}")
                absent_from_base.append(_pathspec(path))
        if absent_from_base:
            pathspecs = b"\0".join(os.fsencode(path) for path in absent_from_base) + b"\0"
            _git(
                author,
                "add",
                "-f",
                "-A",
                "--pathspec-from-file=-",
                "--pathspec-file-nul",
                env=env,
                input_bytes=pathspecs,
            )
        staged = _git(author, "ls-files", "--stage", "-z", env=env)
        for record in staged.split(b"\0"):
            if record:
                metadata = record.split(b"\t", 1)[0].split()
                if metadata[0] == b"160000" or metadata[2] != b"0":
                    raise WorkflowError("submodules and unmerged entries are not supported")
        return _text(_git(author, "write-tree", env=env))


def _index_additions(author: Path, head_entries: dict[str, tuple[str, str]]) -> list[str]:
    additions: list[str] = []
    for record in _git(author, "ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, _object_id, stage = metadata.decode("ascii").split()
        if stage != "0" or mode == "160000":
            raise WorkflowError("submodules and unmerged entries are not supported")
        path = os.fsdecode(path_bytes)
        _relative_path(path)
        if path not in head_entries:
            additions.append(path)
    return additions


def _capture_consistent_tree(
    author: Path,
    integration: Path,
    base: str,
    selected_untracked: list[str],
    expected_identity: dict[str, str],
    extra_paths: list[str] | None = None,
) -> str:
    if _identity(author) != expected_identity:
        raise WorkflowError("author HEAD, refs, or real index changed")
    paths = sorted(set(extra_paths or []))
    first = _snapshot_tree(author, integration, base, selected_untracked, paths)
    second = _snapshot_tree(author, integration, base, selected_untracked, paths)
    if first != second:
        raise WorkflowError("author worktree changed during snapshot capture")
    if _identity(author) != expected_identity:
        raise WorkflowError("author HEAD, refs, or real index changed during snapshot capture")
    return second


def _state_path(integration: Path) -> Path:
    return _git_path(integration, "orchestrate-work-state.json")


def _save_state(integration: Path, state: dict[str, Any]) -> None:
    target = _state_path(integration)
    temporary = target.with_name(f"{target.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def _load_state(integration: Path) -> dict[str, Any]:
    try:
        state = json.loads(_state_path(integration).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError("integration clone has no orchestrate-work state; run prepare first") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"could not read orchestrate-work state: {exc}") from exc
    if state.get("version") != 1:
        raise WorkflowError("unsupported orchestrate-work state version")
    return state


def _resolve_directory(value: str, *, must_exist: bool) -> Path:
    path = Path(value).expanduser()
    try:
        return path.resolve(strict=must_exist)
    except OSError as exc:
        raise WorkflowError(f"invalid directory {value!r}: {exc}") from exc


def _overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    author = _resolve_directory(args.author, must_exist=True)
    if not author.is_dir():
        raise WorkflowError("author path must be a directory")
    _repo_root(author)
    clone_arg = Path(args.clone).expanduser()
    if clone_arg.exists() or clone_arg.is_symlink():
        raise WorkflowError("integration clone destination must not already exist")
    parent = clone_arg.parent.resolve(strict=True)
    integration = parent / clone_arg.name
    if _overlap(author, integration):
        raise WorkflowError("author repository and integration clone paths must not overlap")

    allowed = sorted(set(_relative_path(path) for path in args.allow))
    if not allowed:
        raise WorkflowError("at least one --allow path is required")
    explicit_untracked = sorted(set(_relative_path(path) for path in args.untracked))
    for path in explicit_untracked:
        _safe_worktree_components(author, path)

    _check_preflight(author, explicit_untracked)
    source_head = _source_head(author)
    identity = _identity(author)
    head_ref = _git(author, "symbolic-ref", "-q", "HEAD", check=False)
    if head_ref and not re.fullmatch(rb"refs/heads/[A-Za-z0-9._/-]+\n?", head_ref):
        raise WorkflowError("author branch name is not supported by this workflow")
    head_entries = _tree_entries(author, source_head)
    selected = sorted(set(explicit_untracked + _index_additions(author, head_entries)))
    for path in selected:
        if path in head_entries:
            raise WorkflowError(f"--untracked path is already tracked at HEAD: {path}")
        file = author.joinpath(*path.split("/"))
        if not file.is_file() or file.is_symlink():
            raise WorkflowError(f"selected untracked source file does not exist as a regular file: {path}")
        ignored_code, _out, _err = _git_code(author, "check-ignore", "-q", "--", path)
        if ignored_code == 0:
            raise WorkflowError(f"selected untracked source path is ignored: {path}")
        if ignored_code not in (1,):
            raise WorkflowError(f"could not check ignored state for selected path: {path}")

    clone_created = False
    try:
        _git(parent, "clone", "--local", "--no-hardlinks", "--no-checkout", str(author), str(integration))
        clone_created = True
        _repo_root(integration)
        _git(integration, "remote", "remove", "origin")
        _git(integration, "config", "--local", "push.default", "nothing")
        _git(integration, "config", "--local", "user.name", "orchestrate-work baseline")
        _git(integration, "config", "--local", "user.email", "orchestrate-work@invalid")

        tree = _capture_consistent_tree(
            author,
            integration,
            source_head,
            selected,
            identity,
            extra_paths=sorted(set(head_entries) | set(selected)),
        )
        commit_env = {
            "GIT_AUTHOR_NAME": "orchestrate-work baseline",
            "GIT_AUTHOR_EMAIL": "orchestrate-work@invalid",
            "GIT_AUTHOR_DATE": "@0 +0000",
            "GIT_COMMITTER_NAME": "orchestrate-work baseline",
            "GIT_COMMITTER_EMAIL": "orchestrate-work@invalid",
            "GIT_COMMITTER_DATE": "@0 +0000",
        }
        baseline = _text(_git(integration, "commit-tree", tree, "-p", source_head, "-m", "Capture author working tree baseline", env=commit_env))
        branch = f"refs/heads/orchestrate-work/{uuid.uuid4().hex}"
        _git(integration, "update-ref", branch, baseline)
        _git(integration, "checkout", "--force", "-B", branch.removeprefix("refs/heads/"), baseline)
        if _identity(author) != identity:
            raise WorkflowError("author HEAD, refs, or real index changed during prepare")
        baseline_paths = set(_tree_entries(integration, baseline))
        state = {
            "version": 1,
            "author_root": str(author),
            "integration_root": str(integration),
            "author_identity": identity,
            "source_head": source_head,
            "allowed": allowed,
            "selected_untracked": selected,
            "baseline": baseline,
            "delivered": baseline,
            "expected_author_tree": tree,
            "historical_paths": sorted(set(head_entries) - baseline_paths),
            "integration_branch": branch,
            "pending": None,
            "last_delivery": None,
        }
        _save_state(integration, state)
        if _git(integration, "remote").strip():
            raise WorkflowError("integration clone still has a remote push destination")
        return {
            "status": "prepared",
            "source_head": source_head,
            "baseline_commit": baseline,
            "baseline_tree": tree,
            "integration_clone": str(integration),
            "allowed": allowed,
            "selected_untracked": selected,
        }
    except Exception:
        if clone_created and integration.exists() and not integration.is_symlink() and integration.resolve() == integration:
            shutil.rmtree(integration, ignore_errors=True)
        raise


def _load_context(clone_arg: str) -> tuple[Path, dict[str, Any], Path]:
    integration = _resolve_directory(clone_arg, must_exist=True)
    _repo_root(integration)
    state = _load_state(integration)
    author = _resolve_directory(state["author_root"], must_exist=True)
    _repo_root(author)
    if _overlap(author, integration):
        raise WorkflowError("author repository and integration clone paths overlap")
    return integration, state, author


def _candidate_commit(integration: Path, value: str | None) -> str:
    candidate = _text(_git(integration, "rev-parse", "--verify", "HEAD^{commit}")) if value is None else value.lower()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", candidate):
        raise WorkflowError("candidate must be a full Git commit id")
    kind = _text(_git(integration, "cat-file", "-t", candidate, check=False))
    if kind != "commit":
        raise WorkflowError("candidate commit is missing from the integration clone")
    return candidate


def _candidate_scope(integration: Path, state: dict[str, Any], candidate: str) -> tuple[bool, list[str], str]:
    start = state["delivered"]
    rc, _out, err = _git_code(integration, "merge-base", "--is-ancestor", start, candidate)
    if rc not in (0, 1):
        detail = err.decode("utf-8", "replace").strip()
        raise WorkflowError(f"git merge-base failed ({rc}): {detail}")
    descends = rc == 0
    changed = _git(integration, "diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", start, candidate)
    paths = [os.fsdecode(path) for path in changed.split(b"\0") if path]
    for path in paths:
        _relative_path(path)
    if any(PurePosixPath(path).name == ".gitattributes" for path in paths):
        raise WorkflowError("candidate changes .gitattributes; attribute-control changes are unsupported")
    allowed = all(any(path == prefix or path.startswith(prefix + "/") for prefix in state["allowed"]) for path in paths)
    candidate_entries = _tree_entries(integration, candidate)
    for path in paths:
        if candidate_entries.get(path, ("", ""))[0] == "120000":
            raise WorkflowError(f"candidate symlink changes are not supported: {path}")
        _safe_worktree_components(Path(state["author_root"]), path)
        for link, (mode, _oid) in candidate_entries.items():
            if mode == "120000" and (path == link or path.startswith(link + "/")):
                raise WorkflowError(f"candidate path crosses a symlink: {path}")
    tree = _text(_git(integration, "rev-parse", "--verify", f"{candidate}^{{tree}}"))
    return descends, paths, tree


def _author_tree(
    integration: Path,
    author: Path,
    state: dict[str, Any],
    base: str | None = None,
    extra_paths: set[str] | None = None,
) -> str:
    return _capture_consistent_tree(
        author,
        integration,
        base or state["delivered"],
        state["selected_untracked"],
        state["author_identity"],
        extra_paths=sorted(set(state.get("historical_paths", [])) | (extra_paths or set())),
    )


def _advance_historical_paths(
    state: dict[str, Any], candidate_entries: dict[str, tuple[str, str]], deleted_paths: set[str]
) -> None:
    historical = set(state.get("historical_paths", []))
    historical.update(deleted_paths)
    historical.difference_update(candidate_entries)
    state["historical_paths"] = sorted(historical)


def status(args: argparse.Namespace) -> dict[str, Any]:
    integration, state, author = _load_context(args.clone)
    identity_matches = _identity(author) == state["author_identity"]
    author_tree = _author_tree(integration, author, state) if identity_matches else None
    candidate = _candidate_commit(integration, None)
    descends, paths, tree = _candidate_scope(integration, state, candidate)
    scope_ok = all(any(path == prefix or path.startswith(prefix + "/") for prefix in state["allowed"]) for path in paths)
    return {
        "status": "status",
        "source_head": state["source_head"],
        "author_identity_matches": identity_matches,
        "author_tree": author_tree,
        "author_matches_checkpoint": author_tree == state["expected_author_tree"] if author_tree else False,
        "integration_from": state["delivered"],
        "candidate": candidate,
        "candidate_tree": tree,
        "candidate_descends_from_checkpoint": descends,
        "candidate_paths_in_scope": scope_ok,
        "candidate_changed_paths": paths,
        "pending_delivery": state.get("pending"),
    }


def _apply_patch(author: Path, patch: bytes, *, check: bool) -> None:
    _git(author, "apply", *( ["--check"] if check else []), input_bytes=patch)


def _delivery_result(state: dict[str, Any], from_commit: str, to_commit: str, tree: str, already: bool) -> dict[str, Any]:
    return {
        "status": "already_delivered" if already else "delivered",
        "integration_clone": state["integration_root"],
        "source_head": state["source_head"],
        "integration_from": from_commit,
        "integration_to": to_commit,
        "integration_range": f"{from_commit}..{to_commit}",
        "tree": tree,
        "author_worktree_matches": True,
    }


def deliver(args: argparse.Namespace) -> dict[str, Any]:
    integration, state, author = _load_context(args.clone)
    if _identity(author) != state["author_identity"]:
        raise WorkflowError("author HEAD, refs, or real index changed; reconcile before delivery")
    candidate = _candidate_commit(integration, args.candidate)
    descends, paths, candidate_tree = _candidate_scope(integration, state, candidate)
    if not descends:
        raise WorkflowError("candidate does not descend from the delivered checkpoint")
    if not all(any(path == prefix or path.startswith(prefix + "/") for prefix in state["allowed"]) for path in paths):
        raise WorkflowError("candidate changes paths outside --allow scope")

    start = state["delivered"]
    start_entries = _tree_entries(integration, start)
    candidate_entries = _tree_entries(integration, candidate)
    added_paths = {path for path in paths if path not in start_entries and path in candidate_entries}
    deleted_paths = {path for path in paths if path not in candidate_entries}
    before_extra = added_paths
    after_extra = deleted_paths

    pending = state.get("pending")
    if pending:
        if pending.get("to") != candidate or pending.get("from") != start:
            raise WorkflowError("an interrupted delivery is pending; retry that exact candidate first")
        old_tree = _author_tree(integration, author, state, base=start, extra_paths=before_extra)
        candidate_seeded_tree = _author_tree(integration, author, state, base=candidate, extra_paths=after_extra)
        if candidate_seeded_tree == candidate_tree:
            if _identity(author) != state["author_identity"]:
                raise WorkflowError("author HEAD, refs, or real index changed during interrupted delivery")
            state["delivered"] = candidate
            state["expected_author_tree"] = candidate_tree
            _advance_historical_paths(state, candidate_entries, deleted_paths)
            state["pending"] = None
            result = _delivery_result(state, start, candidate, candidate_tree, False)
            state["last_delivery"] = result
            _save_state(integration, state)
            return result
        if old_tree != pending.get("before_tree"):
            raise WorkflowError("author worktree differs from both sides of the interrupted delivery; preserve and reconcile")
        current_tree = old_tree
    else:
        current_tree = _author_tree(integration, author, state, base=start, extra_paths=before_extra)
        if current_tree != state["expected_author_tree"]:
            raise WorkflowError("author working tree changed since the last checkpoint; preserve and reconcile before delivery")

    if candidate == start:
        if current_tree != state["expected_author_tree"]:
            raise WorkflowError("author working tree does not match the delivered checkpoint")
        return _delivery_result(state, start, candidate, candidate_tree, True)

    patch = _git(integration, "diff", "--binary", "--full-index", "--no-renames", "--no-ext-diff", "--no-textconv", start, candidate)
    if _identity(author) != state["author_identity"]:
        raise WorkflowError("author HEAD, refs, or real index changed before apply")
    latest_tree = _author_tree(integration, author, state, base=start, extra_paths=before_extra)
    expected_before = pending.get("before_tree") if pending else state["expected_author_tree"]
    if latest_tree != expected_before:
        raise WorkflowError("author working tree changed before apply; preserve and reconcile")

    if not pending:
        state["pending"] = {"from": start, "to": candidate, "tree": candidate_tree, "before_tree": latest_tree}
        _save_state(integration, state)
    try:
        _apply_patch(author, patch, check=True)
    except WorkflowError:
        if not pending:
            state["pending"] = None
            _save_state(integration, state)
        raise
    _apply_patch(author, patch, check=False)
    applied_tree = _author_tree(integration, author, state, base=candidate, extra_paths=after_extra)
    if applied_tree != candidate_tree:
        raise WorkflowError("post-apply tree differs from candidate; author work was preserved for reconciliation")
    if _identity(author) != state["author_identity"]:
        raise WorkflowError("author HEAD, refs, or real index changed during delivery")

    state["delivered"] = candidate
    state["expected_author_tree"] = candidate_tree
    _advance_historical_paths(state, candidate_entries, deleted_paths)
    state["pending"] = None
    result = _delivery_result(state, start, candidate, candidate_tree, False)
    state["last_delivery"] = result
    _save_state(integration, state)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture and deliver isolated Git work to an author checkout.")
    commands = parser.add_subparsers(dest="command", required=True)

    prep = commands.add_parser("prepare", help="clone a repository and capture its dirty baseline")
    prep.add_argument("--author", required=True, help="author repository worktree root")
    prep.add_argument("--clone", required=True, help="new integration clone destination")
    prep.add_argument("--allow", action="append", default=[], metavar="PATH", help="allowed integration delivery path; repeat as needed")
    prep.add_argument("--untracked", action="append", default=[], metavar="PATH", help="exact untracked source file to include in the baseline")

    stat = commands.add_parser("status", help="compare the source worktree and integration candidate with the checkpoint")
    stat.add_argument("--clone", required=True, help="prepared integration clone")

    delivery = commands.add_parser("deliver", help="apply an integration commit range to the author worktree")
    delivery.add_argument("--clone", required=True, help="prepared integration clone")
    delivery.add_argument("--candidate", help="full integration commit id; defaults to clone HEAD")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = {"prepare": prepare, "status": status, "deliver": deliver}[args.command](args)
    except WorkflowError as exc:
        print(f"git_workflow: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
