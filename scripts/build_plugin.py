#!/usr/bin/env python3
"""Build an offline, self-contained Codex plugin from pinned manifest assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import install


BUILD_INFO = "build-info.json"
PLUGIN_PAYLOAD = (
    "plugin/plugin.json",
    "plugin/hooks/hooks.json",
    "plugin/hooks/bootstrap.py",
    "plugin/scripts/orchestration.py",
    "plugin/skills/orchestrate-work-plugin/SKILL.md",
    "plugin/skills/orchestrate-work-plugin/agents/openai.yaml",
)
OPTIONAL_PLUGIN_PAYLOAD = "plugin/.codex-plugin/plugin.json"
DEFAULT_DEST = "work/plugin-package/halkliff-orchestration"


class BuildError(Exception):
    """Expected validation or build failure."""


@dataclass(frozen=True)
class BuildPlan:
    destination: Path
    payload: dict[str, bytes]
    fingerprint: str
    source_revision: str
    manifest_pins: dict[str, str]
    identical: bool


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith("GIT_"):
            env.pop(key, None)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except OSError as exc:
        raise BuildError(f"cannot run Git: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise BuildError(f"Git {' '.join(args)} failed in {root}: {detail or result.returncode}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", "strict").strip()


def _repo_root() -> Path:
    root = Path(os.path.abspath(__file__)).parents[1]
    install._check_no_links(root, include_missing=True)
    if not root.is_dir():
        raise BuildError(f"repository root is missing: {root}")
    return root


def _path(root: Path, relative: str | PurePosixPath, label: str) -> Path:
    rel = relative if isinstance(relative, PurePosixPath) else install._safe_relative_path(relative, label)
    candidate = root.joinpath(*rel.parts)
    install._check_no_links(candidate, include_missing=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise BuildError(f"{label} escapes the repository root: {rel}") from exc
    return candidate


def _verify_gitlink(repo: Path, upstream: install.Upstream) -> None:
    output = _git(repo, "ls-files", "--stage", "--", upstream.path.as_posix())
    entries = [line.split(maxsplit=3) for line in str(output).splitlines() if line.strip()]
    if len(entries) != 1 or len(entries[0]) != 4:
        raise BuildError(f"{upstream.path} is not one staged submodule gitlink")
    mode, object_id, stage, indexed_path = entries[0]
    if mode != "160000" or stage != "0" or indexed_path != upstream.path.as_posix():
        raise BuildError(f"{upstream.path} is not a stage-zero submodule gitlink")
    if object_id.lower() != upstream.commit:
        raise BuildError(
            f"manifest pin for {upstream.id} does not match its Git index gitlink: "
            f"{upstream.commit} vs {object_id}"
        )


def _verify_gitmodules(repo: Path, upstream: install.Upstream) -> None:
    modules_path = _path(repo, ".gitmodules", "submodule configuration")
    if not modules_path.is_file():
        raise BuildError("dependencies declare upstreams but repository has no regular .gitmodules")
    output = _git(
        repo,
        "config",
        "--file",
        str(modules_path),
        "--get-regexp",
        r"^submodule\..*\.path$",
    )
    matches: list[str] = []
    for line in str(output).splitlines():
        key, separator, value = line.partition("\t")
        if not separator:
            key, separator, value = line.partition(" ")
        if not separator:
            raise BuildError("cannot parse submodule paths from .gitmodules")
        if value == upstream.path.as_posix():
            prefix = "submodule."
            suffix = ".path"
            if not key.startswith(prefix) or not key.endswith(suffix):
                raise BuildError("cannot parse a submodule name from .gitmodules")
            matches.append(key[len(prefix):-len(suffix)])
    if len(matches) != 1:
        raise BuildError(f".gitmodules does not declare exactly one entry for {upstream.path}")
    url = _git(repo, "config", "--file", str(modules_path), "--get", f"submodule.{matches[0]}.url")
    if url != upstream.url:
        raise BuildError(f".gitmodules URL mismatch for {upstream.id}: expected {upstream.url!r}, found {url!r}")


def _verify_submodule(repo: Path, upstream: install.Upstream) -> Path:
    checkout = _path(repo, upstream.path, f"upstream {upstream.id}")
    if not checkout.is_dir():
        raise BuildError(f"upstream checkout is missing: {upstream.path}")
    _verify_gitmodules(repo, upstream)
    marker = checkout / ".git"
    install._check_no_links(marker, include_missing=True)
    top = str(_git(checkout, "rev-parse", "--show-toplevel"))
    if os.path.normcase(os.path.abspath(top)) != os.path.normcase(os.path.abspath(checkout)):
        raise BuildError(f"upstream path is not its own Git checkout: {upstream.path}")
    _verify_gitlink(repo, upstream)
    _git(checkout, "cat-file", "-e", f"{upstream.commit}^{{commit}}")
    return checkout


def _pinned_blob(checkout: Path, upstream: install.Upstream, relative: PurePosixPath) -> bytes:
    path = relative.as_posix()
    if not path:
        raise BuildError(f"upstream source for {upstream.id} does not name a file")
    tree_output = _git(
        checkout,
        "ls-tree",
        "-r",
        "-z",
        upstream.commit,
        "--",
        f":(literal){path}",
        binary=True,
    )
    records: list[tuple[str, str, str, str]] = []
    for record in bytes(tree_output).split(b"\0"):
        if not record:
            continue
        header, separator, raw_path = record.partition(b"\t")
        if not separator:
            raise BuildError(f"could not parse pinned tree entry for {upstream.id}:{path}")
        try:
            mode, object_type, object_id = header.decode("ascii").split(" ")
            entry_path = raw_path.decode("utf-8")
        except (UnicodeError, ValueError) as exc:
            raise BuildError(f"could not decode pinned tree entry for {upstream.id}:{path}") from exc
        if entry_path == path:
            records.append((mode, object_type, object_id, entry_path))
    if len(records) != 1:
        raise BuildError(f"pinned source is missing or ambiguous: {upstream.id}:{path}")
    mode, object_type, _object_id, _entry_path = records[0]
    if mode not in {"100644", "100755"} or object_type != "blob":
        raise BuildError(f"pinned source is not a regular file (mode {mode}): {upstream.id}:{path}")
    raw = _git(checkout, "cat-file", "blob", f"{upstream.commit}:{path}", binary=True)
    return bytes(raw)


def _source_bytes(
    repo: Path,
    source: PurePosixPath,
    upstreams: tuple[install.Upstream, ...],
    checkouts: dict[str, Path],
) -> bytes:
    match = next((item for item in upstreams if item.path == source or item.path in source.parents), None)
    if match is None:
        path = _path(repo, source, f"source {source}")
        if not path.is_file():
            raise BuildError(f"source is not a regular file: {source}")
        try:
            return path.read_bytes()
        except OSError as exc:
            raise BuildError(f"cannot read source {source}: {exc}") from exc
    relative = PurePosixPath(*source.parts[len(match.path.parts):])
    return _pinned_blob(checkouts[match.id], match, relative)


def _add_payload(payload: dict[str, bytes], path: str, contents: bytes) -> None:
    target = install._safe_relative_path(path, "package target")
    key = target.as_posix().casefold()
    if any(existing.casefold() == key for existing in payload):
        raise BuildError(f"package target is mapped more than once: {path}")
    for existing in payload:
        existing_parts = PurePosixPath(existing).parts
        target_parts = target.parts
        common = min(len(existing_parts), len(target_parts))
        if tuple(part.casefold() for part in existing_parts[:common]) == tuple(part.casefold() for part in target_parts[:common]):
            if len(existing_parts) != len(target_parts):
                raise BuildError(f"package files overlap as a file and directory: {existing!r}, {path!r}")
    payload[target.as_posix()] = contents


def _plugin_manifests_match(portable_bytes: bytes, overlay_bytes: bytes) -> bool:
    try:
        portable = json.loads(portable_bytes.decode("utf-8"))
        overlay = json.loads(overlay_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(portable, dict) or not isinstance(overlay, dict):
        return False
    if overlay == portable:
        return True
    for key in ("name", "version", "description"):
        if overlay.get(key) != portable.get(key):
            return False
    if "author" in overlay and overlay.get("author") != portable.get("author"):
        return False
    openai = portable.get("extensions", {}).get("com.openai") if isinstance(portable.get("extensions"), dict) else None
    if not isinstance(openai, dict):
        return False
    if overlay.get("skills") != "./skills/":
        return False
    if overlay.get("hooks") != openai.get("hooks") or overlay.get("interface") != openai.get("interface"):
        return False
    if any(key.casefold() in {"mcpservers", "servers"} for key in overlay):
        return False
    return True


def _load_payload(repo: Path) -> tuple[dict[str, bytes], dict[str, str], str]:
    manifest_path = _path(repo, "dependencies.json", "dependency manifest")
    if not manifest_path.is_file():
        raise BuildError("dependencies.json is not a regular file")
    try:
        manifest = install.load_manifest(manifest_path)
    except install.InstallError as exc:
        raise BuildError(str(exc)) from exc

    checkout_by_id = {item.id: _verify_submodule(repo, item) for item in manifest.upstreams}
    payload: dict[str, bytes] = {}
    local_plugin_files: dict[str, bytes] = {}
    for relative in PLUGIN_PAYLOAD:
        source = PurePosixPath(relative)
        local_plugin_files[source.as_posix()] = _source_bytes(repo, source, (), {})
    overlay_path = _path(repo, OPTIONAL_PLUGIN_PAYLOAD, "optional plugin compatibility manifest")
    if overlay_path.exists():
        overlay = _source_bytes(repo, PurePosixPath(OPTIONAL_PLUGIN_PAYLOAD), (), {})
        if not _plugin_manifests_match(local_plugin_files["plugin/plugin.json"], overlay):
            raise BuildError("plugin/.codex-plugin/plugin.json is not synchronized with plugin/plugin.json")
        local_plugin_files[OPTIONAL_PLUGIN_PAYLOAD] = overlay
    for source, contents in local_plugin_files.items():
        target = source.removeprefix("plugin/")
        _add_payload(payload, target, contents)

    license_path = _path(repo, "LICENSE", "top-level license")
    if not license_path.is_file():
        raise BuildError("top-level LICENSE is not a regular file")
    _add_payload(payload, "LICENSE", license_path.read_bytes())

    for skill in manifest.skills:
        for mapping in skill.files:
            contents = _source_bytes(repo, mapping.source, manifest.upstreams, checkout_by_id)
            target = f"support/skills/{skill.name}/{mapping.target.as_posix()}"
            _add_payload(payload, target, contents)

    head = str(_git(repo, "rev-parse", "HEAD")).lower()
    if len(head) not in (40, 64) or any(char not in "0123456789abcdef" for char in head):
        raise BuildError("repository HEAD is not a full Git object id")
    pins = {item.id: item.commit for item in manifest.upstreams}
    return payload, pins, head


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _package_payload(
    files: dict[str, bytes], source_revision: str, manifest_pins: dict[str, str]
) -> tuple[dict[str, bytes], str]:
    file_hashes = {path: _digest(contents) for path, contents in files.items()}
    canonical = json.dumps(
        file_hashes, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    fingerprint = _digest(canonical)
    build_info = {
        "schema_version": 1,
        "source_revision": source_revision,
        "manifest_pins": manifest_pins,
        "files": file_hashes,
        "package_fingerprint": fingerprint,
    }
    result = dict(files)
    result[BUILD_INFO] = (json.dumps(build_info, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return result, fingerprint


def _tree(path: Path) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    stack: list[tuple[Path, PurePosixPath]] = [(path, PurePosixPath())]
    while stack:
        directory, relative = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise BuildError(f"cannot inspect existing destination {directory}: {exc}") from exc
        for entry in entries:
            child = Path(entry.path)
            if install._is_reparse_or_symlink(child):
                raise BuildError(f"destination contains a symlink or junction: {child}")
            child_relative = relative / entry.name
            if entry.is_dir(follow_symlinks=False):
                directories.add(child_relative.as_posix())
                stack.append((child, child_relative))
            elif entry.is_file(follow_symlinks=False):
                files[child_relative.as_posix()] = child.read_bytes()
            else:
                raise BuildError(f"destination contains a non-file entry: {child}")
    return files, directories


def _expected_directories(paths: set[str]) -> set[str]:
    result: set[str] = set()
    for raw in paths:
        for parent in PurePosixPath(raw).parents:
            if parent == PurePosixPath("."):
                break
            result.add(parent.as_posix())
    return result


def _overlaps(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def _validate_destination(repo: Path, destination: Path, payload_sources: list[Path]) -> Path:
    for part in destination.parts:
        if part != destination.anchor and part not in {".", ".."}:
            install._safe_name(part, "output path")
    target = Path(os.path.abspath(destination))
    for part in target.parts[1:]:
        install._safe_name(part, "output path")
    install._check_no_links(target, include_missing=True)
    try:
        inside_repo = target.relative_to(repo)
    except ValueError:
        inside_repo = None
    if inside_repo is not None and not inside_repo.parts:
        raise BuildError("package destination may not be the repository root")
    for source in payload_sources:
        if _overlaps(target, source):
            raise BuildError(f"package destination overlaps a source path: {source}")
    if inside_repo is not None:
        if inside_repo.parts[0].casefold() != "work":
            raise BuildError("an in-repository package destination must be under repo/work/")
    else:
        if _overlaps(target, repo):
            raise BuildError("package destination may not be the repository or an ancestor of it")
    if target.exists() and not target.is_dir():
        raise BuildError(f"package destination is not a directory: {target}")
    return target


def make_plan(destination: Path) -> BuildPlan:
    repo = _repo_root()
    payload, pins, source_revision = _load_payload(repo)
    package, fingerprint = _package_payload(payload, source_revision, pins)
    source_paths = [
        repo / "dependencies.json",
        repo / "LICENSE",
        repo / "plugin",
        repo / "skills",
        repo / "adapters",
        repo / "upstream",
        repo / "scripts",
        repo / "tests",
        repo / "docs",
    ]
    target = _validate_destination(repo, destination, source_paths)
    identical = False
    if target.exists():
        actual_files, actual_dirs = _tree(target)
        expected_dirs = _expected_directories(set(package))
        if actual_files == package and actual_dirs == expected_dirs:
            identical = True
        else:
            raise BuildError(f"destination already exists with different contents; left untouched: {target}")
    return BuildPlan(target, package, fingerprint, source_revision, pins, identical)


def _write_plan(plan: BuildPlan) -> None:
    parent = plan.destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    install._check_no_links(plan.destination, include_missing=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{plan.destination.name}.build-", dir=parent))
    try:
        for relative, contents in plan.payload.items():
            rel = install._safe_relative_path(relative, "package output")
            output = stage.joinpath(*rel.parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(contents)
        if plan.destination.exists():
            raise BuildError(f"destination appeared during build; refusing to overwrite: {plan.destination}")
        os.replace(stage, plan.destination)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Build an offline pinned Codex plugin package")
    result.add_argument("--dest", required=True, help=f"new or identical output directory (for example: {DEFAULT_DEST})")
    result.add_argument("--dry-run", action="store_true", help="validate and report without writing output")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        plan = make_plan(Path(args.dest))
        if args.dry_run or plan.identical:
            action = "already-current" if plan.identical else "would-build"
        else:
            _write_plan(plan)
            action = "built"
        print(json.dumps({
            "action": action,
            "destination": str(plan.destination),
            "package_fingerprint": plan.fingerprint,
            "source_revision": plan.source_revision,
            "manifest_pins": plan.manifest_pins,
            "files": len(plan.payload),
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except (BuildError, install.InstallError, OSError) as exc:
        print(f"build_plugin: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
