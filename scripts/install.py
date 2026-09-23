#!/usr/bin/env python3
"""Install the reviewed skills listed in the repository manifest."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


MANIFEST_NAME = "dependencies.json"
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


class InstallError(Exception):
    """An expected validation or installation failure."""


@dataclass(frozen=True)
class Upstream:
    id: str
    path: PurePosixPath
    url: str
    commit: str


@dataclass(frozen=True)
class FileMapping:
    source: PurePosixPath
    target: PurePosixPath


@dataclass(frozen=True)
class Skill:
    name: str
    files: tuple[FileMapping, ...]


@dataclass(frozen=True)
class Manifest:
    upstreams: tuple[Upstream, ...]
    skills: tuple[Skill, ...]


@dataclass(frozen=True)
class Plan:
    skill: Skill
    files: tuple[tuple[PurePosixPath, bytes], ...]
    identical: bool


def _safe_relative_path(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InstallError(f"{label} must be a non-empty repository-relative path using '/' separators")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/") or any(part in {"", ".", ".."} for part in value.split("/")):
        raise InstallError(f"{label} must not be absolute or contain '.' or '..' path segments: {value!r}")
    for part in path.parts:
        _safe_name(part, label)
    return path


def _safe_name(value: object, label: str) -> str:
    if not isinstance(value, str) or value in {"", ".", ".."}:
        raise InstallError(f"{label} must be a simple name")
    if any(ord(char) < 32 for char in value) or any(char in '<>:"|?*/\\' for char in value):
        raise InstallError(f"{label} contains a character unsafe on common filesystems: {value!r}")
    if value.endswith((".", " ")):
        raise InstallError(f"{label} may not end in a dot or space: {value!r}")
    if value.split(".", 1)[0].casefold() in _WINDOWS_RESERVED:
        raise InstallError(f"{label} uses a reserved Windows device name: {value!r}")
    return value


def _required_string(record: dict[str, object], key: str, label: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InstallError(f"{label}.{key} must be a non-empty string")
    return value


def load_manifest(path: Path) -> Manifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InstallError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InstallError(f"{path} is not valid JSON: {exc}") from exc
    if (
        not isinstance(raw, dict)
        or isinstance(raw.get("schema_version"), bool)
        or raw.get("schema_version") != 1
    ):
        raise InstallError(f"{path} must be an object with schema_version: 1")

    upstream_records = raw.get("upstreams")
    skill_records = raw.get("skills")
    if not isinstance(upstream_records, list) or not isinstance(skill_records, list):
        raise InstallError(f"{path} must contain upstreams and skills arrays")

    upstreams: list[Upstream] = []
    upstream_ids: set[str] = set()
    upstream_paths: set[str] = set()
    for index, record in enumerate(upstream_records):
        label = f"upstreams[{index}]"
        if not isinstance(record, dict):
            raise InstallError(f"{label} must be an object")
        upstream_id = _safe_name(_required_string(record, "id", label), f"{label}.id")
        path_value = _safe_relative_path(record.get("path"), f"{label}.path")
        url = _required_string(record, "url", label)
        commit = _required_string(record, "commit", label).lower()
        if not _COMMIT_RE.fullmatch(commit):
            raise InstallError(f"{label}.commit must be a full 40- or 64-character lowercase Git object id")
        if upstream_id.casefold() in upstream_ids:
            raise InstallError(f"duplicate upstream id: {upstream_id}")
        if path_value.as_posix().casefold() in upstream_paths:
            raise InstallError(f"duplicate upstream path: {path_value}")
        upstream_ids.add(upstream_id.casefold())
        upstream_paths.add(path_value.as_posix().casefold())
        upstreams.append(Upstream(upstream_id, path_value, url, commit))

    skills: list[Skill] = []
    skill_names: set[str] = set()
    for index, record in enumerate(skill_records):
        label = f"skills[{index}]"
        if not isinstance(record, dict):
            raise InstallError(f"{label} must be an object")
        name = _safe_name(_required_string(record, "name", label), f"{label}.name")
        if name.casefold() in skill_names:
            raise InstallError(f"duplicate skill name: {name}")
        skill_names.add(name.casefold())

        file_records = record.get("files")
        if not isinstance(file_records, list) or not file_records:
            raise InstallError(f"{label}.files must be a non-empty array")
        mappings: list[FileMapping] = []
        targets: set[str] = set()
        for file_index, file_record in enumerate(file_records):
            file_label = f"{label}.files[{file_index}]"
            if not isinstance(file_record, dict):
                raise InstallError(f"{file_label} must be an object")
            source = _safe_relative_path(file_record.get("source"), f"{file_label}.source")
            target = _safe_relative_path(file_record.get("target"), f"{file_label}.target")
            target_key = target.as_posix().casefold()
            if target_key in targets:
                raise InstallError(f"{label} has duplicate target path: {target}")
            targets.add(target_key)
            mappings.append(FileMapping(source, target))
        if "skill.md" not in targets:
            raise InstallError(f"{label} must explicitly map a SKILL.md file")
        skills.append(Skill(name, tuple(mappings)))

    if not skills:
        raise InstallError(f"{path} contains no skills")
    return Manifest(tuple(upstreams), tuple(skills))


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise InstallError(f"cannot inspect {path}: {exc}") from exc
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(attributes & reparse_flag)


def _check_no_links(path: Path, include_missing: bool = False) -> None:
    """Reject links/reparse points in every existing component of an absolute path."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if _is_reparse_or_symlink(current):
            raise InstallError(f"refusing to traverse a symbolic link or junction: {current}")
        if not current.exists() and not include_missing:
            break


def _check_repo_relative_path(root: Path, relative: PurePosixPath, label: str, *, require_file: bool = False) -> Path:
    candidate = root.joinpath(*relative.parts)
    _check_no_links(candidate, include_missing=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise InstallError(f"{label} escapes the repository root: {relative}") from exc
    if not candidate.exists():
        raise InstallError(f"{label} does not exist: {relative}")
    if require_file and not candidate.is_file():
        raise InstallError(f"{label} is not a regular file: {relative}")
    return candidate


def _git(root: Path, *args: str, required: bool = True) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        if required:
            raise InstallError(f"cannot run Git: {exc}") from exc
        return None
    if result.returncode != 0:
        if required:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            raise InstallError(f"Git {' '.join(args)} failed in {root}: {detail}")
        return None
    return result.stdout.strip()


def _gitmodules(root: Path) -> dict[str, tuple[str, str]]:
    path = root / ".gitmodules"
    if _is_reparse_or_symlink(path):
        raise InstallError("refusing to read .gitmodules through a symbolic link or junction")
    if not path.is_file():
        return {}
    output = _git(root, "config", "--file", str(path), "--get-regexp", r"^submodule\..*\.path$", required=False)
    if not output:
        return {}
    result: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        key, sep, value = line.partition(" ")
        if not sep or not key.startswith("submodule.") or not key.endswith(".path"):
            raise InstallError("could not parse submodule paths in .gitmodules")
        name = key[len("submodule.") : -len(".path")]
        url = _git(root, "config", "--file", str(path), "--get", f"submodule.{name}.url", required=False)
        if url is None:
            raise InstallError(f"submodule {name!r} has no URL in .gitmodules")
        result[value] = (name, url)
    return result


def _verify_gitlink(root: Path, upstream: Upstream) -> None:
    output = _git(root, "ls-files", "--stage", "--", upstream.path.as_posix())
    entries = [line.split() for line in output.splitlines() if line.strip()]
    if len(entries) != 1 or len(entries[0]) < 4:
        raise InstallError(f"{upstream.path} is not a single staged submodule gitlink")
    mode, object_id, stage, _path = entries[0][:4]
    if mode != "160000" or stage != "0":
        raise InstallError(f"{upstream.path} is not a staged submodule gitlink")
    if object_id.lower() != upstream.commit:
        raise InstallError(
            f"pinned commit mismatch for {upstream.id}: manifest {upstream.commit}, git index {object_id}"
        )


def _checkout_exists(path: Path) -> bool:
    if not path.exists():
        return False
    if not path.is_dir():
        raise InstallError(f"submodule path is not a directory: {path}")
    git_marker = path / ".git"
    _check_no_links(git_marker, include_missing=True)
    if not git_marker.exists():
        return False
    top = _git(path, "rev-parse", "--show-toplevel", required=False)
    if top is None:
        return False
    return os.path.normcase(os.path.abspath(top)) == os.path.normcase(os.path.abspath(path))


def _verify_checkout(root: Path, upstream: Upstream, path: Path, *, require_origin_config: bool) -> None:
    if not _checkout_exists(path):
        raise InstallError(f"submodule checkout is missing: {upstream.path}")
    origin = _git(path, "config", "--get", "remote.origin.url", required=False)
    if origin is None:
        if require_origin_config:
            raise InstallError(f"submodule {upstream.id} has no configured remote.origin.url")
    elif origin != upstream.url:
        raise InstallError(
            f"submodule URL mismatch for {upstream.id}: expected {upstream.url!r}, configured origin is {origin!r}"
        )
    actual = _git(path, "rev-parse", "HEAD")
    if actual.lower() != upstream.commit:
        raise InstallError(
            f"submodule commit mismatch for {upstream.id}: expected {upstream.commit}, checkout is {actual}"
        )
    dirty = _git(path, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none")
    if dirty:
        raise InstallError(f"submodule {upstream.id} has local changes; refusing to install from a dirty checkout")


def _prepare_upstreams(root: Path, manifest: Manifest, *, offline: bool, dry_run: bool) -> None:
    if not manifest.upstreams:
        return
    modules = _gitmodules(root)
    configured: list[tuple[Upstream, Path, str]] = []
    missing: list[Upstream] = []
    for upstream in manifest.upstreams:
        path = _check_repo_relative_path(root, upstream.path, f"upstreams[{upstream.id}].path") if (root / Path(*upstream.path.parts)).exists() else root.joinpath(*upstream.path.parts)
        _check_no_links(path, include_missing=True)
        entry = modules.get(upstream.path.as_posix())
        if entry is None:
            raise InstallError(f"{upstream.path} is not declared in .gitmodules")
        name, module_url = entry
        if module_url != upstream.url:
            raise InstallError(
                f".gitmodules URL mismatch for {upstream.id}: expected {upstream.url!r}, found {module_url!r}"
            )
        _verify_gitlink(root, upstream)
        configured_url = _git(root, "config", "--get", f"submodule.{name}.url", required=False)
        if configured_url is not None and configured_url != upstream.url:
            raise InstallError(
                f"local Git URL mismatch for {upstream.id}: expected {upstream.url!r}, configured URL is {configured_url!r}"
            )
        if _checkout_exists(path):
            _verify_checkout(root, upstream, path, require_origin_config=True)
        else:
            missing.append(upstream)
        configured.append((upstream, path, name))

    if missing and (offline or dry_run):
        paths = ", ".join(upstream.path.as_posix() for upstream in missing)
        mode = "offline mode" if offline else "dry-run mode"
        raise InstallError(f"{mode} cannot fetch missing submodules: {paths}; initialize them separately, then retry")
    if missing:
        paths = [upstream.path.as_posix() for upstream in missing]
        _git(root, "submodule", "update", "--init", "--recursive", "--", *paths)

    for upstream, path, _name in configured:
        if _checkout_exists(path):
            _verify_checkout(root, upstream, path, require_origin_config=True)
        else:
            raise InstallError(f"submodule checkout is missing after initialization: {upstream.path}")


def _has_upstream_ancestor(source: PurePosixPath, upstreams: Sequence[Upstream]) -> bool:
    return any(source == upstream.path or upstream.path in source.parents for upstream in upstreams)


def _check_manifest_sources(root: Path, manifest: Manifest) -> None:
    upstream_paths = tuple(upstream.path for upstream in manifest.upstreams)
    for skill in manifest.skills:
        for mapping in skill.files:
            if mapping.source.parts[0].casefold() == "upstream" and not _has_upstream_ancestor(mapping.source, manifest.upstreams):
                raise InstallError(f"source {mapping.source} is under upstream/ but has no declared pinned upstream")
            source = _check_repo_relative_path(root, mapping.source, f"source for {skill.name}/{mapping.target}", require_file=True)
            if not source.is_file():
                raise InstallError(f"source for {skill.name}/{mapping.target} is not a regular file: {mapping.source}")


def _read_skill_sources(root: Path, manifest: Manifest) -> dict[str, tuple[tuple[PurePosixPath, bytes], ...]]:
    result: dict[str, tuple[tuple[PurePosixPath, bytes], ...]] = {}
    for skill in manifest.skills:
        files: list[tuple[PurePosixPath, bytes]] = []
        for mapping in skill.files:
            source = root.joinpath(*mapping.source.parts)
            try:
                files.append((mapping.target, source.read_bytes()))
            except OSError as exc:
                raise InstallError(f"cannot read {mapping.source}: {exc}") from exc
        result[skill.name] = tuple(files)
    return result


def _walk_tree(path: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    stack = [(path, PurePosixPath())]
    while stack:
        directory, relative = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise InstallError(f"cannot inspect existing skill directory {directory}: {exc}") from exc
        for entry in entries:
            child = Path(entry.path)
            if _is_reparse_or_symlink(child):
                raise InstallError(f"existing skill contains a symbolic link or junction: {child}")
            child_relative = relative / entry.name
            if entry.is_dir(follow_symlinks=False):
                directories.add(child_relative.as_posix())
                stack.append((child, child_relative))
            elif entry.is_file(follow_symlinks=False):
                try:
                    files[child_relative.as_posix()] = child.read_bytes()
                except OSError as exc:
                    raise InstallError(f"cannot read existing skill file {child}: {exc}") from exc
            else:
                raise InstallError(f"existing skill contains a non-file entry: {child}")
    return files, directories


def _expected_directories(files: Iterable[PurePosixPath]) -> set[str]:
    directories: set[str] = set()
    for file_path in files:
        parents = list(file_path.parents)
        for parent in parents:
            if parent == PurePosixPath("."):
                break
            directories.add(parent.as_posix())
    return directories


def _compare_existing(path: Path, expected: tuple[tuple[PurePosixPath, bytes], ...], skill_name: str) -> bool:
    files, directories = _walk_tree(path)
    expected_files = {relative.as_posix(): contents for relative, contents in expected}
    expected_dirs = _expected_directories(relative for relative, _ in expected)
    if files == expected_files and directories == expected_dirs:
        return True
    actual_folded = {name.casefold(): name for name in files}
    expected_folded = {name.casefold(): name for name in expected_files}
    if actual_folded.keys() == expected_folded.keys():
        different_case = next(
            (actual_folded[key], expected_folded[key])
            for key in actual_folded
            if actual_folded[key] != expected_folded[key]
        ) if any(actual_folded[key] != expected_folded[key] for key in actual_folded) else None
        if different_case:
            raise InstallError(
                f"existing skill {skill_name!r} differs in filename case: {different_case[0]!r} vs {different_case[1]!r}"
            )
    return False


def _find_existing_skill(destination: Path, name: str) -> Path | None:
    if not destination.exists():
        return None
    try:
        children = list(os.scandir(destination))
    except OSError as exc:
        raise InstallError(f"cannot inspect destination {destination}: {exc}") from exc
    matches = [Path(item.path) for item in children if item.name.casefold() == name.casefold()]
    if not matches:
        return None
    if len(matches) != 1:
        raise InstallError(f"destination has ambiguous case-insensitive matches for skill {name!r}")
    found = matches[0]
    if _is_reparse_or_symlink(found):
        raise InstallError(f"destination skill is a symbolic link or junction: {found}")
    if not found.is_dir():
        raise InstallError(f"destination entry for skill {name!r} is not a directory: {found}")
    if found.name != name:
        raise InstallError(f"destination already contains skill name {found.name!r} with different casing from {name!r}")
    return found


def _destination_path(value: Path) -> Path:
    result = Path(os.path.abspath(value))
    _check_no_links(result, include_missing=True)
    return result


def _preflight_destination(destination: Path, source_bytes: dict[str, tuple[tuple[PurePosixPath, bytes], ...]]) -> list[Plan]:
    if destination.exists() and not destination.is_dir():
        raise InstallError(f"destination is not a directory: {destination}")
    plans: list[Plan] = []
    conflicts: list[str] = []
    for name, files in source_bytes.items():
        existing = _find_existing_skill(destination, name)
        identical = False
        if existing is not None:
            identical = _compare_existing(existing, files, name)
            if not identical:
                conflicts.append(name)
        plans.append(Plan(Skill(name, ()), files, identical))
    if conflicts:
        raise InstallError(
            "existing skill(s) differ from the manifest, so nothing was installed: " + ", ".join(conflicts)
        )
    return plans


def _write_staged_skill(root: Path, plan: Plan) -> Path:
    staged = root / plan.skill.name
    staged.mkdir()
    for relative, contents in plan.files:
        output = staged.joinpath(*relative.parts)
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            output.write_bytes(contents)
        except OSError as exc:
            raise InstallError(f"cannot stage {plan.skill.name}/{relative}: {exc}") from exc
    return staged


def _create_parent_directories(path: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        if current.parent == current:
            break
        current = current.parent
    if current.exists() and not current.is_dir():
        raise InstallError(f"destination parent is not a directory: {current}")
    created: list[Path] = []
    try:
        for directory in reversed(missing):
            directory.mkdir()
            created.append(directory)
    except OSError as exc:
        _remove_empty_directories(reversed(created))
        raise InstallError(f"cannot create destination directory {directory}: {exc}") from exc
    return created


def _remove_empty_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        try:
            path.rmdir()
        except OSError:
            pass


def _install(plans: Sequence[Plan], destination: Path) -> tuple[list[str], list[str]]:
    to_install = [plan for plan in plans if not plan.identical]
    already = [plan.skill.name for plan in plans if plan.identical]
    if not to_install:
        return [], already

    created_parents = _create_parent_directories(destination)
    stage_root: Path | None = None
    published: list[Path] = []
    try:
        stage_root = Path(tempfile.mkdtemp(prefix=".skills-install-", dir=destination))
        staged = [_write_staged_skill(stage_root, plan) for plan in to_install]
        for plan, staged_path in zip(to_install, staged):
            target = destination / plan.skill.name
            if target.exists():
                raise InstallError(f"destination changed during installation; refusing to replace {target}")
            try:
                os.rename(staged_path, target)
            except OSError as exc:
                raise InstallError(f"cannot publish skill {plan.skill.name!r}: {exc}") from exc
            published.append(target)
    except Exception:
        for target in reversed(published):
            shutil.rmtree(target, ignore_errors=True)
        raise
    finally:
        if stage_root is not None:
            shutil.rmtree(stage_root, ignore_errors=True)
        _remove_empty_directories(reversed(created_parents))
    return [plan.skill.name for plan in to_install], already


def install(
    *,
    root: Path,
    destination: Path,
    offline: bool = False,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    root = Path(os.path.abspath(root))
    _check_no_links(root, include_missing=True)
    if not root.is_dir():
        raise InstallError(f"repository root is not a directory: {root}")
    manifest_path = root / MANIFEST_NAME
    _check_no_links(manifest_path, include_missing=True)
    manifest = load_manifest(manifest_path)
    destination = _destination_path(destination)

    # Reject destination conflicts before a normal online run can fetch anything.
    source_bytes: dict[str, tuple[tuple[PurePosixPath, bytes], ...]] | None = None
    if all(_checkout_exists(root.joinpath(*upstream.path.parts)) for upstream in manifest.upstreams):
        _check_manifest_sources(root, manifest)
        source_bytes = _read_skill_sources(root, manifest)
        _preflight_destination(destination, source_bytes)
    elif destination.exists():
        # Source-independent destination type and link checks still happen before fetching.
        for skill in manifest.skills:
            _find_existing_skill(destination, skill.name)

    _prepare_upstreams(root, manifest, offline=offline, dry_run=dry_run)
    _check_manifest_sources(root, manifest)
    source_bytes = _read_skill_sources(root, manifest)
    plans = _preflight_destination(destination, source_bytes)
    if dry_run:
        return [plan.skill.name for plan in plans if not plan.identical], [plan.skill.name for plan in plans if plan.identical]
    return _install(plans, destination)


def _default_destination() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install reviewed skills from dependencies.json")
    parser.add_argument("--dest", type=Path, default=_default_destination(), help="skills directory (default: CODEX_HOME/skills or ~/.codex/skills)")
    parser.add_argument("--dry-run", action="store_true", help="validate and report changes without writing or fetching")
    parser.add_argument("--offline", action="store_true", help="refuse to fetch missing submodules")
    args = parser.parse_args(argv)

    root = Path(__file__).absolute().parent.parent
    try:
        installed, identical = install(
            root=root,
            destination=args.dest,
            offline=args.offline,
            dry_run=args.dry_run,
        )
    except (InstallError, OSError) as exc:
        print(f"install failed: {exc}", file=sys.stderr)
        return 1

    action = "would install" if args.dry_run else "installed"
    if installed:
        print(f"{action} {len(installed)} skill(s): {', '.join(installed)}")
    if identical:
        print(f"already identical: {len(identical)} skill(s): {', '.join(identical)}")
    if not installed and not identical:
        print("nothing to install")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
