#!/usr/bin/env python3
"""Explicit local runtime for the packaged orchestrate-work workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any


STATE_NAME = "orchestration-state.json"
BUILD_INFO = "build-info.json"
CONTEXT_LIMIT = 1024
LOCK_TIMEOUT_SECONDS = 2.0
MAX_RUNS = 32
MAX_BINDINGS = 128
MAX_WORKSPACES = 128
MAX_RECENT_EVENT_IDS = 256
OBSERVED_EVENTS = {"PreToolUse", "SessionStart", "SubagentStart", "SubagentStop"}
REQUIRED_FILES = (
    "plugin.json",
    "hooks/hooks.json",
    "hooks/bootstrap.py",
    "scripts/orchestration.py",
    "skills/orchestrate-work-plugin/SKILL.md",
    "support/skills/orchestrate-work/SKILL.md",
    "support/skills/orchestrate-work/references/worker.md",
    "support/skills/define-goal/SKILL.md",
)


class RuntimeErrorMessage(Exception):
    """Expected, user-facing runtime error."""


def _canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _reject_link_ancestry(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    for component in (absolute, *absolute.parents):
        if _is_link(component):
            raise RuntimeErrorMessage(f"refusing a symlink or junction path: {component}")


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _ensure_disjoint(left: Path, right: Path, label: str) -> None:
    left_abs = Path(os.path.abspath(left))
    right_abs = Path(os.path.abspath(right))
    if _is_within(left_abs, right_abs) or _is_within(right_abs, left_abs):
        raise RuntimeErrorMessage(f"{label} must not overlap: {left_abs} and {right_abs}")


def _plugin_root() -> Path:
    root = Path(os.path.abspath(__file__)).parents[1]
    _reject_link_ancestry(root)
    return root


def _plugin_data(explicit: str | None = None) -> Path:
    value = explicit or os.environ.get("PLUGIN_DATA")
    if not value:
        script = Path(os.path.abspath(__file__))
        if (len(script.parents) > 3 and script.parent.name == "scripts"
                and script.parents[2].name == "runtimes"
                and len(script.parents[1].name) == 64):
            inferred = script.parents[3]
            _reject_link_ancestry(inferred)
            return inferred
        raise RuntimeErrorMessage("provide --plugin-data or set PLUGIN_DATA")
    path = Path(value)
    if not path.is_absolute():
        raise RuntimeErrorMessage("PLUGIN_DATA must be an absolute path")
    path = Path(os.path.abspath(path))
    _reject_link_ancestry(path)
    return path


def _locator_path() -> Path:
    override = os.environ.get("ORCHESTRATE_WORK_LOCATOR")
    if override:
        path = Path(override)
        if not path.is_absolute():
            raise RuntimeErrorMessage("ORCHESTRATE_WORK_LOCATOR must be an absolute path")
        return Path(os.path.abspath(path))
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    if not base.is_absolute():
        raise RuntimeErrorMessage("CODEX_HOME must be an absolute path")
    return Path(os.path.abspath(base / "orchestration-plugin" / "locator.json"))


def _locator_data_for(session: str) -> Path | None:
    path = _locator_path()
    _reject_link_ancestry(path)
    try:
        locator = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeErrorMessage(f"session locator is unreadable: {exc}") from exc
    if (not isinstance(locator, dict) or locator.get("schema_version") != 1
            or not isinstance(locator.get("bindings"), dict)):
        raise RuntimeErrorMessage("session locator has an unsupported schema")
    value = locator["bindings"].get(session)
    if value is None:
        return None
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise RuntimeErrorMessage("session locator contains an invalid data-root path")
    root = Path(os.path.abspath(value))
    _reject_link_ancestry(root)
    return root


def _write_locator_locked(bindings: dict[str, str]) -> None:
    path = _locator_path()
    _reject_link_ancestry(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = _read_locator()
    current["bindings"].update(bindings)
    if len(current["bindings"]) > MAX_BINDINGS:
        raise RuntimeErrorMessage("session locator is full; deactivate an old binding first")
    _atomic_json(path, current)


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _read_locator() -> dict[str, Any]:
    path = _locator_path()
    _reject_link_ancestry(path)
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        current = {"schema_version": 1, "bindings": {}}
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeErrorMessage(f"session locator is unreadable: {exc}") from exc
    if (not isinstance(current, dict) or current.get("schema_version") != 1
            or not isinstance(current.get("bindings"), dict)):
        raise RuntimeErrorMessage("session locator has an unsupported schema")
    if len(current["bindings"]) > MAX_BINDINGS:
        raise RuntimeErrorMessage("session locator exceeds its bounded session registry")
    for session, data_root in current["bindings"].items():
        if (not isinstance(session, str) or not isinstance(data_root, str)
                or not Path(data_root).is_absolute()):
            raise RuntimeErrorMessage("session locator contains an invalid binding")
    return current


def _remove_locator_locked(expected_bindings: dict[str, str]) -> None:
    if not expected_bindings:
        return
    path = _locator_path()
    _reject_link_ancestry(path)
    if not path.exists():
        return
    locator = _read_locator()
    for session, data_root in expected_bindings.items():
        if locator["bindings"].get(session) == data_root:
            locator["bindings"].pop(session, None)
    if locator["bindings"]:
        _atomic_json(path, locator)
    else:
        path.unlink(missing_ok=True)


def _safe_relpath(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw)
    if (not raw or path.is_absolute() or "\\" in raw or ":" in raw
            or any(part in ("", ".", "..") for part in path.parts)):
        raise RuntimeErrorMessage(f"invalid build-info path: {raw!r}")
    return path


def validate_package(root: Path) -> tuple[dict[str, str], str, dict[str, Any]]:
    """Validate the build manifest, required entrypoints and every declared byte."""
    _reject_link_ancestry(root)
    info_path = root / BUILD_INFO
    _reject_link_ancestry(info_path)
    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeErrorMessage(f"missing or invalid {BUILD_INFO}: {exc}") from exc
    if not isinstance(info, dict) or info.get("schema_version") != 1:
        raise RuntimeErrorMessage("unsupported build-info schema; expected schema_version 1")
    files = info.get("files")
    if not isinstance(files, dict) or not files:
        raise RuntimeErrorMessage("build-info files must be a non-empty path-to-SHA256 object")
    normalized: dict[str, str] = {}
    for raw, digest in files.items():
        if not isinstance(raw, str) or not isinstance(digest, str) or len(digest) != 64:
            raise RuntimeErrorMessage("build-info contains an invalid file path or digest")
        rel = _safe_relpath(raw)
        if raw != rel.as_posix() or any(c not in "0123456789abcdef" for c in digest):
            raise RuntimeErrorMessage(f"build-info path or digest is not canonical: {raw!r}")
        file_path = root.joinpath(*rel.parts)
        try:
            file_path.absolute().relative_to(root.absolute())
        except ValueError as exc:
            raise RuntimeErrorMessage(f"build-info asset escapes the package root: {raw}") from exc
        _reject_link_ancestry(file_path)
        if not file_path.is_file():
            raise RuntimeErrorMessage(f"build-info asset is missing or not a regular file: {raw}")
        if _sha256(file_path.read_bytes()) != digest:
            raise RuntimeErrorMessage(f"build-info digest mismatch: {raw}")
        normalized[raw] = digest
    missing = [path for path in REQUIRED_FILES if path not in normalized]
    if missing:
        raise RuntimeErrorMessage("build-info omits required runtime assets: " + ", ".join(missing))
    fingerprint = _sha256(_canonical_json(normalized))
    if info.get("package_fingerprint") != fingerprint:
        raise RuntimeErrorMessage("build-info package_fingerprint does not match its files map")
    try:
        manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeErrorMessage(f"plugin.json is invalid: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("name"), str):
        raise RuntimeErrorMessage("plugin.json has no valid plugin name")
    return normalized, fingerprint, info


def _paths_for(root: Path, fingerprint: str) -> dict[str, str]:
    support = root / "support" / "skills"
    return {
        "plugin_root": str(root),
        "runtime_root": str(root),
        "cli": str(root / "scripts" / "orchestration.py"),
        "core": str(support / "orchestrate-work" / "SKILL.md"),
        "worker": str(support / "orchestrate-work" / "references" / "worker.md"),
        "support": str(support),
        "package_fingerprint": fingerprint,
    }


def _verify_runtime(root: Path, expected_fingerprint: str) -> dict[str, str]:
    _, fingerprint, _ = validate_package(root)
    if fingerprint != expected_fingerprint:
        raise RuntimeErrorMessage(f"pinned runtime fingerprint mismatch at {root}")
    paths = _paths_for(root, fingerprint)
    for key in ("cli", "core", "worker"):
        if not Path(paths[key]).is_file():
            raise RuntimeErrorMessage(f"pinned runtime is missing {key}: {paths[key]}")
    if not (Path(paths["support"]) / "define-goal" / "SKILL.md").is_file():
        raise RuntimeErrorMessage("pinned runtime is missing support skill define-goal")
    return paths


def _copy_snapshot(source: Path, data_root: Path, files: dict[str, str], fingerprint: str) -> Path:
    runtimes = data_root / "runtimes"
    destination = runtimes / fingerprint
    _reject_link_ancestry(data_root)
    if destination.exists():
        _verify_runtime(destination, fingerprint)
        return destination
    runtimes.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{fingerprint}.", dir=runtimes))
    try:
        for raw in files:
            rel = _safe_relpath(raw)
            source_file = source.joinpath(*rel.parts)
            target_file = staging.joinpath(*rel.parts)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, target_file)
        shutil.copyfile(source / BUILD_INFO, staging / BUILD_INFO)
        _verify_runtime(staging, fingerprint)
        try:
            os.replace(staging, destination)
        except OSError:
            if destination.exists():
                _verify_runtime(destination, fingerprint)
                shutil.rmtree(staging, ignore_errors=True)
            else:
                raise
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return destination


def _empty_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "runs": {},
        "bindings": {},
        "session_observed": {},
    }


def _read_state(path: Path) -> dict[str, Any]:
    _reject_link_ancestry(path)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty_state()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeErrorMessage(f"runtime state is unreadable: {exc}") from exc
    if (not isinstance(state, dict) or state.get("schema_version") != 1
            or not isinstance(state.get("runs"), dict) or not isinstance(state.get("bindings"), dict)):
        raise RuntimeErrorMessage("runtime state has an unsupported or inconsistent schema")
    if len(state["runs"]) > MAX_RUNS or len(state["bindings"]) > MAX_BINDINGS:
        raise RuntimeErrorMessage("runtime state exceeds its bounded run or session registry")
    for session, run_id in state["bindings"].items():
        if not isinstance(session, str) or not isinstance(run_id, str) or run_id not in state["runs"]:
            raise RuntimeErrorMessage("runtime state contains an inconsistent session binding")
    observed_sessions = state.setdefault("session_observed", {})
    if not isinstance(observed_sessions, dict):
        raise RuntimeErrorMessage("runtime state has invalid session observation flags")
    if len(observed_sessions) > MAX_BINDINGS:
        raise RuntimeErrorMessage("runtime state exceeds its bounded observed-session registry")
    for session, observed in observed_sessions.items():
        if session not in state["bindings"] or not isinstance(observed, bool):
            raise RuntimeErrorMessage("runtime state contains an inconsistent observed-session flag")
    for session in state["bindings"]:
        observed_sessions.setdefault(session, False)
    for run in state["runs"].values():
        if not isinstance(run, dict):
            raise RuntimeErrorMessage("runtime state contains an invalid run record")
        observations = run.setdefault("observations", {})
        if not isinstance(observations, dict):
            raise RuntimeErrorMessage("runtime state contains invalid observation counters")
        event_counts = observations.setdefault("events", {})
        if not isinstance(event_counts, dict) or any(not isinstance(value, int) or value < 0 for value in event_counts.values()):
            raise RuntimeErrorMessage("runtime state contains invalid event counts")
        recent = observations.setdefault("recent_ids", [])
        if not isinstance(recent, list) or len(recent) > MAX_RECENT_EVENT_IDS or any(not isinstance(item, str) for item in recent):
            raise RuntimeErrorMessage("runtime state contains an invalid deduplication window")
        incomplete = observations.setdefault("incomplete", False)
        if not isinstance(incomplete, bool):
            raise RuntimeErrorMessage("runtime state contains an invalid observation completeness flag")
        observations.setdefault("guard_denials", 0)
        if not isinstance(observations["guard_denials"], int) or observations["guard_denials"] < 0:
            raise RuntimeErrorMessage("runtime state contains an invalid guard-denial count")
        workspaces = run.setdefault("workspaces", {})
        if not isinstance(workspaces, dict):
            raise RuntimeErrorMessage("runtime state contains invalid workspace records")
        if len(workspaces) > MAX_WORKSPACES:
            raise RuntimeErrorMessage("runtime state exceeds its bounded workspace registry")
    return state


@contextmanager
def _state_lock(data_root: Path, lock_name: str = ".orchestration-state.lock"):
    lock_path = data_root / lock_name
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    descriptor = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeErrorMessage("runtime state is busy (lock wait exceeded 2 seconds)")
            time.sleep(0.025)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def _locator_lock():
    path = _locator_path()
    _reject_link_ancestry(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _state_lock(path.parent, ".orchestration-locator.lock"):
        yield


def _write_state(data_root: Path, state: dict[str, Any]) -> None:
    state_path = data_root / STATE_NAME
    _atomic_json(state_path, state)


def _identifier(value: str, label: str) -> str:
    if not value or len(value) > 512 or "\x00" in value:
        raise RuntimeErrorMessage(f"{label} must be a non-empty identifier of at most 512 characters")
    return value


def command_activate(args: argparse.Namespace) -> dict[str, Any]:
    session = _identifier(args.session, "session")
    source = _plugin_root()
    data = _plugin_data(args.plugin_data)
    for raw, label in ((args.coord_root, "coordination root"), (args.author_repo, "author checkout")):
        path = Path(raw)
        if not path.is_absolute() or not path.is_dir():
            raise RuntimeErrorMessage(f"{label} must be an existing absolute directory")
        _reject_link_ancestry(path)
    coord = str(Path(os.path.abspath(args.coord_root)))
    author = str(Path(os.path.abspath(args.author_repo)))
    if Path(coord) == Path(author):
        raise RuntimeErrorMessage("coordination root and author checkout must be different directories")
    files, fingerprint, _ = validate_package(source)
    _reject_link_ancestry(data)
    data_nested_in_source = _is_within(data, source)
    source_nested_in_data = _is_within(source, data)
    if data_nested_in_source:
        raise RuntimeErrorMessage("PLUGIN_DATA may not be inside the plugin source")
    if source_nested_in_data and (not data.is_dir() or source != data / "runtimes" / fingerprint):
        raise RuntimeErrorMessage("PLUGIN_DATA may overlap the source only for its exact pinned runtime snapshot")
    if args.run_id:
        _identifier(args.run_id, "run id")

    with _locator_lock():
        locator = _read_locator()
        located = locator["bindings"].get(session)
        if located is not None and Path(located) != data:
            raise RuntimeErrorMessage("session is already registered to another PLUGIN_DATA root; deactivate it before rebinding")
        if args.run_id and not data.exists():
            raise RuntimeErrorMessage("--run-id must name an existing active run; omit it to start a new run")
        if data.exists() and not data.is_dir():
            raise RuntimeErrorMessage(f"PLUGIN_DATA is not a directory: {data}")
        if not data.exists():
            data.mkdir(parents=True, exist_ok=True)
        _reject_link_ancestry(data)
        with _state_lock(data):
            state_path = data / STATE_NAME
            state_existed = state_path.exists()
            state = _read_state(state_path)
            state_before = json.loads(json.dumps(state))
            if args.run_id and args.run_id not in state["runs"]:
                raise RuntimeErrorMessage("--run-id must name an existing active run; omit it to start a new run")
            requested_run = args.run_id or str(uuid.uuid4())
            existing_session_run = state["bindings"].get(session)
            if existing_session_run and args.run_id and existing_session_run != args.run_id:
                raise RuntimeErrorMessage("session is already bound to a different run id")
            run_id = existing_session_run or requested_run
            run = state["runs"].get(run_id)
            if source_nested_in_data:
                registered = state["runs"].get(args.run_id or existing_session_run)
                if (not registered or registered.get("package_fingerprint") != fingerprint):
                    raise RuntimeErrorMessage("pinned source is not registered to the requested active run")
            if run is not None:
                if run.get("coord_root") != coord or run.get("author_repo") != author:
                    raise RuntimeErrorMessage("existing run roots differ; refusing to rebind or migrate it")
                pin = run.get("package_fingerprint")
                if not isinstance(pin, str):
                    raise RuntimeErrorMessage("existing run has no valid package fingerprint")
                if pin != fingerprint:
                    runtime = data / "runtimes" / pin
                    _verify_runtime(runtime, pin)
                    if existing_session_run or args.run_id:
                        snapshot = runtime
                    else:
                        raise RuntimeErrorMessage("activation retry found a package update; deactivate and start an author-controlled new run to migrate")
                else:
                    snapshot = data / "runtimes" / pin
                    _verify_runtime(snapshot, pin)
            else:
                if len(state["runs"]) >= MAX_RUNS:
                    raise RuntimeErrorMessage("run registry is full; deactivate an old run before starting another")
                snapshot = _copy_snapshot(source, data, files, fingerprint)
                state["runs"][run_id] = {
                    "package_fingerprint": fingerprint,
                    "coord_root": coord,
                    "author_repo": author,
                    "created_at": int(time.time()),
                    "observations": {"events": {}, "recent_ids": [], "incomplete": False, "guard_denials": 0},
                    "workspaces": {},
                }
            if existing_session_run and existing_session_run != run_id:
                raise RuntimeErrorMessage("session is already bound to another active run")
            if session not in state["bindings"] and len(state["bindings"]) >= MAX_BINDINGS:
                raise RuntimeErrorMessage("session registry is full; deactivate an old binding first")
            state["bindings"][session] = run_id
            state["session_observed"][session] = state["session_observed"].get(session, False)
            _write_state(data, state)
            try:
                _write_locator_locked({session: str(data)})
            except Exception:
                if state_existed:
                    _write_state(data, state_before)
                else:
                    state_path.unlink(missing_ok=True)
                raise
    result = {"session_id": session, "run_id": run_id,
              **_paths_for(snapshot, fingerprint if not run else run["package_fingerprint"])}
    result["plugin_data"] = str(data)
    return result


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    if args.session is not None:
        args.session = _identifier(args.session, "session")
    if args.run_id is not None:
        args.run_id = _identifier(args.run_id, "run id")
    if args.plugin_data:
        data = _plugin_data(args.plugin_data)
    elif args.session:
        data = _locator_data_for(args.session)
        if data is None:
            return {"active": False, "session_id": args.session, "run_id": None}
    else:
        data = _plugin_data()
    state_path = data / STATE_NAME
    state = _read_state(state_path)
    if args.session is not None:
        session = _identifier(args.session, "session")
        run_id = state["bindings"].get(session)
        run = state["runs"].get(run_id) if run_id else None
        result: dict[str, Any] = {
            "active": run is not None,
            "session_id": session,
            "run_id": run_id,
            "session_observed": state["session_observed"].get(session, False),
        }
        if run:
            pin = run["package_fingerprint"]
            runtime = data / "runtimes" / pin
            result.update(_verify_runtime(runtime, pin))
            result.update(_observation_status(run))
        return result
    if args.run_id is not None:
        run_id = _identifier(args.run_id, "run id")
        run = state["runs"].get(run_id)
        result = {"active": run is not None, "run_id": run_id,
                  "sessions": sorted(s for s, r in state["bindings"].items() if r == run_id),
                  "session_observed": {
                      s: state["session_observed"].get(s, False)
                      for s, bound_run in sorted(state["bindings"].items()) if bound_run == run_id
                  }}
        if run:
            pin = run["package_fingerprint"]
            result.update(_verify_runtime(data / "runtimes" / pin, pin))
            result.update(_observation_status(run))
        return result
    return {"active_runs": len(state["runs"]), "active_sessions": len(state["bindings"]),
            "runs": sorted(state["runs"])}


def command_deactivate(args: argparse.Namespace) -> dict[str, Any]:
    if args.session is not None:
        args.session = _identifier(args.session, "session")
    else:
        args.run_id = _identifier(args.run_id, "run id")
    with _locator_lock():
        locator = _read_locator()
        if args.plugin_data:
            data = _plugin_data(args.plugin_data)
        elif args.session is not None:
            located = locator["bindings"].get(args.session)
            if located is None:
                return {"deactivated": 0, "session_id": args.session, "retained_snapshots": True}
            data = Path(located)
        else:
            data = _plugin_data()
        if not data.exists():
            return {"deactivated": 0, "retained_snapshots": True}
        with _state_lock(data):
            state = _read_state(data / STATE_NAME)
            removed_sessions: set[str] = set()
            if args.session is not None:
                session = args.session
                run_id = state["bindings"].pop(session, None)
                if run_id:
                    removed_sessions.add(session)
                    state["session_observed"].pop(session, None)
                if run_id and run_id not in state["bindings"].values():
                    state["runs"].pop(run_id, None)
                result = {"deactivated": 1 if run_id else 0, "session_id": session, "run_id": run_id}
            else:
                run_id = args.run_id
                existed = run_id in state["runs"]
                removed_sessions = {session for session, bound_run in state["bindings"].items() if bound_run == run_id}
                state["bindings"] = {s: r for s, r in state["bindings"].items() if r != run_id}
                for session in removed_sessions:
                    state["session_observed"].pop(session, None)
                state["runs"].pop(run_id, None)
                result = {"deactivated": 1 if existed else 0, "run_id": run_id}
            if not state["runs"] and not state["bindings"]:
                try:
                    (data / STATE_NAME).unlink()
                except FileNotFoundError:
                    pass
            else:
                _write_state(data, state)
        _remove_locator_locked({session: str(data) for session in removed_sessions})
    result["retained_snapshots"] = True
    return result


def _read_hook_stdin() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise RuntimeErrorMessage(f"hook input is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeErrorMessage("hook input must be a JSON object")
    return value


def _hook_state(data: Path, session: str) -> tuple[dict[str, Any], str, dict[str, Any]] | None:
    if not session:
        return None
    state = _read_state(data / STATE_NAME)
    run_id = state["bindings"].get(session)
    run = state["runs"].get(run_id) if run_id else None
    return (state, run_id, run) if run else None


def _deny(reason: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def _dispatch_check(event: dict[str, Any]) -> dict[str, Any] | None:
    tool = event.get("tool_name")
    if tool not in ("spawn_agent", "Agent"):
        return None
    args = event.get("tool_input")
    if not isinstance(args, dict):
        return _deny("Spawn is blocked: supply explicit model and reasoning_effort parameters.")
    model = args.get("model")
    effort = args.get("reasoning_effort")
    allowed = {"gpt-6-luna": {"xhigh"}, "gpt-6.1-sol": {"high", "xhigh"}}
    if not isinstance(model, str) or not isinstance(effort, str) or model not in allowed or effort not in allowed[model]:
        return _deny("Spawn is blocked: explicitly set an approved model and reasoning_effort (gpt-6-luna/xhigh or gpt-6.1-sol/high|xhigh).")
    fork_turns = args.get("fork_turns")
    if fork_turns is None or fork_turns == "all":
        return _deny("Spawn is blocked: fork_turns all/omitted inherits full history; choose a bounded explicit fork or use a new isolated chat.")
    string_count = (isinstance(fork_turns, str) and fork_turns.isascii()
                    and fork_turns.isdecimal() and bool(fork_turns.lstrip("0")))
    positive_count = (type(fork_turns) is int and fork_turns > 0) or string_count
    if not (fork_turns == "none" or positive_count):
        return _deny("Spawn is blocked: fork_turns must be 'none' or an explicit positive count.")
    return None


def _observation_identity(event_name: str, session: str, event: dict[str, Any]) -> str | None:
    tool_use_id = event.get("tool_use_id")
    if isinstance(tool_use_id, str) and 0 < len(tool_use_id) <= 512:
        identity = [event_name, session, "tool_use_id", tool_use_id]
    else:
        turn_id = event.get("turn_id")
        agent_id = event.get("agent_id")
        if not (isinstance(turn_id, str) and 0 < len(turn_id) <= 512
                and isinstance(agent_id, str) and 0 < len(agent_id) <= 512):
            return None
        identity = [event_name, session, "turn_id", turn_id, "agent_id", agent_id]
    return _sha256(_canonical_json(identity))


def _record_observation(
    data: Path, session: str, run_id: str, event_name: str,
    event: dict[str, Any], guard_denied: bool,
) -> None:
    identity = _observation_identity(event_name, session, event)
    with _state_lock(data):
        state = _read_state(data / STATE_NAME)
        if state["bindings"].get(session) != run_id or run_id not in state["runs"]:
            return
        observed_before = state["session_observed"].get(session, False)
        state["session_observed"][session] = True
        run = state["runs"][run_id]
        observations = run.setdefault(
            "observations", {"events": {}, "recent_ids": [], "incomplete": False, "guard_denials": 0}
        )
        changed = not observed_before
        if identity is None:
            observations["incomplete"] = True
            changed = True
        elif identity in observations["recent_ids"]:
            pass
        else:
            observations["recent_ids"].append(identity)
            del observations["recent_ids"][:-MAX_RECENT_EVENT_IDS]
            counts = observations["events"]
            counts[event_name] = counts.get(event_name, 0) + 1
            if guard_denied:
                observations["guard_denials"] += 1
            changed = True
        if changed:
            _write_state(data, state)


def _observation_status(run: dict[str, Any]) -> dict[str, Any]:
    observations = run.get("observations", {})
    return {
        "observed_events": dict(sorted(observations.get("events", {}).items())),
        "guard_denials": observations.get("guard_denials", 0),
        "observation_incomplete": observations.get("incomplete", False),
        "dedup_window_size": MAX_RECENT_EVENT_IDS,
    }


def _git(repo: Path, *arguments: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        result = subprocess.run(
            ["git", *arguments], cwd=repo, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeErrorMessage(f"Git inspection failed: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip()[:512]
        raise RuntimeErrorMessage(f"Git inspection failed ({' '.join(arguments)}): {detail}")
    return result.stdout.strip()


def _absolute_directory(raw: str, label: str) -> Path:
    if not isinstance(raw, str):
        raise RuntimeErrorMessage(f"{label} must be an absolute directory path")
    path = Path(raw)
    if not path.is_absolute():
        raise RuntimeErrorMessage(f"{label} must be an absolute path")
    path = Path(os.path.abspath(path))
    _reject_link_ancestry(path)
    if not path.is_dir():
        raise RuntimeErrorMessage(f"{label} must be an existing directory: {path}")
    return path


def _absolute_file(raw: Any, label: str) -> Path:
    if not isinstance(raw, str):
        raise RuntimeErrorMessage(f"{label} must be an absolute file path")
    path = Path(raw)
    if not path.is_absolute():
        raise RuntimeErrorMessage(f"{label} must be an absolute file path")
    path = Path(os.path.abspath(path))
    _reject_link_ancestry(path)
    if not path.is_file():
        raise RuntimeErrorMessage(f"{label} must name an existing file: {path}")
    return path


def _git_root(path: Path) -> Path:
    root = Path(os.path.abspath(_git(path, "rev-parse", "--show-toplevel")))
    if root != path:
        raise RuntimeErrorMessage(f"workspace must be the exact Git checkout root: {path}")
    return root


def _commit_object(repo: Path, commit: Any) -> str:
    if not isinstance(commit, str) or len(commit) not in (40, 64):
        raise RuntimeErrorMessage("commit must be a full hexadecimal commit ID")
    if any(character not in "0123456789abcdefABCDEF" for character in commit):
        raise RuntimeErrorMessage("commit must be a full hexadecimal commit ID")
    resolved = _git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")
    if resolved.lower() != commit.lower():
        raise RuntimeErrorMessage(f"commit ID is not canonical or does not resolve to a commit: {commit}")
    return resolved.lower()


def _source_checkout_root() -> Path | None:
    source = _plugin_root()
    for candidate in source.parents:
        if (candidate / ".git").exists() and (candidate / "dependencies.json").is_file():
            return candidate
    return None


def _workspace_path_for_run(raw: str, run: dict[str, Any], data: Path) -> Path:
    workspace = _absolute_directory(raw, "workspace")
    _git_root(workspace)
    protected = [
        (run.get("author_repo"), "author checkout"),
        (run.get("coord_root"), "coordination root"),
        (str(data), "plugin data"),
        (str(_plugin_root()), "plugin package"),
    ]
    source_checkout = _source_checkout_root()
    if source_checkout is not None:
        protected.append((str(source_checkout), "main checkout"))
    for raw_root, label in protected:
        if not isinstance(raw_root, str) or not Path(raw_root).is_absolute():
            raise RuntimeErrorMessage(f"run has no valid {label} path")
        _ensure_disjoint(workspace, Path(raw_root), f"workspace and {label}")
    return workspace


def _active_run(data: Path, session: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    state = _read_state(data / STATE_NAME)
    run_id = state["bindings"].get(session)
    run = state["runs"].get(run_id) if run_id else None
    if not run:
        raise RuntimeErrorMessage(f"session is not bound to an active run: {session}")
    return state, run_id, run


def _retained_object_store_reason(repo: Path, workspace: Path) -> str | None:
    try:
        common_raw = Path(_git(repo, "rev-parse", "--git-common-dir"))
        common = common_raw if common_raw.is_absolute() else repo / common_raw
        common = Path(os.path.abspath(common))
        _reject_link_ancestry(common)
        if not common.is_dir():
            return "retained Git common directory is missing"
        _ensure_disjoint(common, workspace, "retained Git common directory and workspace")

        objects_raw = Path(_git(repo, "rev-parse", "--git-path", "objects"))
        objects = objects_raw if objects_raw.is_absolute() else repo / objects_raw
        objects = Path(os.path.abspath(objects))
        _reject_link_ancestry(objects)
        if not objects.is_dir():
            return "retained Git object directory is missing"
        _ensure_disjoint(objects, workspace, "retained Git object directory and workspace")

        alternates = objects / "info" / "alternates"
        _reject_link_ancestry(alternates)
        if alternates.exists() and alternates.read_text(encoding="utf-8").strip():
            return "retained Git object store uses alternates; independent commit storage cannot be established"
    except (RuntimeErrorMessage, OSError, UnicodeError) as exc:
        return f"retained Git object storage could not be verified: {exc}"
    return None


def command_workspace_register(args: argparse.Namespace) -> dict[str, Any]:
    session = _identifier(args.session, "session")
    data = _plugin_data(args.plugin_data)
    with _state_lock(data):
        state, run_id, run = _active_run(data, session)
        workspace = _workspace_path_for_run(args.path, run, data)
        base_commit = _commit_object(workspace, args.base_commit)
        workspaces = run["workspaces"]
        path_key = str(workspace)
        existing = workspaces.get(path_key)
        if existing is not None:
            if existing.get("kind") != args.kind or existing.get("base_commit") != base_commit:
                raise RuntimeErrorMessage("workspace is already registered with different metadata")
            return {"registered": True, "session_id": session, "run_id": run_id,
                    "path": path_key, "kind": args.kind, "base_commit": base_commit}
        for other_run in state["runs"].values():
            for other_path in other_run.get("workspaces", {}):
                try:
                    _ensure_disjoint(workspace, Path(other_path), "workspace registrations")
                except RuntimeErrorMessage as exc:
                    raise RuntimeErrorMessage("workspace overlaps an existing registered workspace") from exc
        registered_count = sum(len(item.get("workspaces", {})) for item in state["runs"].values())
        if registered_count >= MAX_WORKSPACES:
            raise RuntimeErrorMessage("workspace registry is full; resolve an existing record first")
        workspaces[path_key] = {
            "path": path_key,
            "kind": args.kind,
            "base_commit": base_commit,
            "registered_at": int(time.time()),
        }
        _write_state(data, state)
    return {"registered": True, "session_id": session, "run_id": run_id,
            "path": str(workspace), "kind": args.kind, "base_commit": base_commit}


def command_workspace_release(args: argparse.Namespace) -> dict[str, Any]:
    session = _identifier(args.session, "session")
    data = _plugin_data(args.plugin_data)
    attestation = _absolute_file(args.attestation, "release attestation")
    with _state_lock(data):
        state, run_id, run = _active_run(data, session)
        workspace = _workspace_path_for_run(args.path, run, data)
        record = run["workspaces"].get(str(workspace))
        if record is None:
            raise RuntimeErrorMessage(f"workspace is not registered to this run: {workspace}")
        _ensure_disjoint(attestation, workspace, "release attestation and workspace")
        try:
            value = json.loads(attestation.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeErrorMessage(f"release attestation is unreadable JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeErrorMessage("release attestation must be a JSON object")
        pointer = {"path": str(attestation), "sha256": _sha256(attestation.read_bytes())}
        record["release_attestation"] = pointer
        _write_state(data, state)
    return {"released": True, "session_id": session, "run_id": run_id,
            "path": str(workspace), "attestation": pointer["path"],
            "attestation_sha256": pointer["sha256"]}


def _preflight_reasons(workspace: Path, run: dict[str, Any], record: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    try:
        _reject_link_ancestry(workspace)
        if not workspace.is_dir():
            reasons.append("workspace path is missing")
        else:
            _git_root(workspace)
            head = _git(workspace, "rev-parse", "--verify", "HEAD^{commit}").lower()
            pointer = record.get("release_attestation")
            if isinstance(pointer, dict):
                attestation_for_head = None
                try:
                    attestation_for_head = json.loads(Path(pointer.get("path", "")).read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
                    pass
                result_commit = attestation_for_head.get("result_commit") if isinstance(attestation_for_head, dict) else None
                if isinstance(result_commit, str) and head != result_commit.lower():
                    reasons.append("workspace HEAD does not match the released result commit")
            status = _git(workspace, "status", "--porcelain=v1", "--untracked-files=all", "--ignored")
            if status:
                reasons.append("workspace has tracked, untracked, or ignored changes")
    except RuntimeErrorMessage as exc:
        reasons.append(str(exc))

    pointer = record.get("release_attestation")
    attestation: dict[str, Any] | None = None
    if not isinstance(pointer, dict) or not isinstance(pointer.get("path"), str):
        reasons.append("no release attestation is registered")
    else:
        try:
            path = _absolute_file(pointer["path"], "release attestation")
            _ensure_disjoint(path, workspace, "release attestation and workspace")
            digest = _sha256(path.read_bytes())
            if pointer.get("sha256") != digest:
                reasons.append("release attestation changed after registration")
            parsed = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(parsed, dict):
                reasons.append("release attestation is not a JSON object")
            else:
                attestation = parsed
        except (RuntimeErrorMessage, OSError, UnicodeError, json.JSONDecodeError) as exc:
            reasons.append(f"release attestation is unavailable: {exc}")

    if attestation is None:
        return list(dict.fromkeys(reasons))

    for field, description in (
        ("delivery_resolved", "delivery remains unresolved"),
        ("operations_clear", "an operation is not attested clear"),
        ("reports_resolved", "a report remains unresolved"),
    ):
        if attestation.get(field) is not True:
            reasons.append(description)

    integration_result = attestation.get("integration_result")
    try:
        integration_result_path = _absolute_file(integration_result, "integration result")
        _ensure_disjoint(integration_result_path, workspace, "integration result and workspace")
    except RuntimeErrorMessage as exc:
        reasons.append(str(exc))

    evidence = attestation.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        reasons.append("retained evidence must name at least one existing external file")
    else:
        for item in evidence:
            try:
                evidence_path = _absolute_file(item, "retained evidence")
                _ensure_disjoint(evidence_path, workspace, "retained evidence and workspace")
            except RuntimeErrorMessage as exc:
                reasons.append(str(exc))

    retained_root: Path | None = None
    retained_repo = attestation.get("retained_repo")
    try:
        if not isinstance(retained_repo, str):
            raise RuntimeErrorMessage("retained_repo must be an absolute Git checkout path")
        retained_root = _absolute_directory(retained_repo, "retained repository")
        _ensure_disjoint(retained_root, workspace, "retained repository and workspace")
        _git_root(retained_root)
        storage_reason = _retained_object_store_reason(retained_root, workspace)
        if storage_reason:
            reasons.append(storage_reason)
    except RuntimeErrorMessage as exc:
        reasons.append(str(exc))
        retained_root = None

    def retained_ref(field: str, label: str) -> str | None:
        ref = attestation.get(field)
        if (retained_root is None or not isinstance(ref, str) or not ref.startswith("refs/")
                or ref.strip() != ref or any(char.isspace() for char in ref) or ".." in ref):
            reasons.append(f"{label} must name an existing full refs/* reference")
            return None
        try:
            _git(retained_root, "show-ref", "--verify", "--hash", ref)
            return _git(retained_root, "rev-parse", "--verify", f"{ref}^{{commit}}").lower()
        except RuntimeErrorMessage:
            reasons.append(f"{label} does not preserve a commit under an actual Git ref")
            return None

    base_ref_commit = retained_ref("base_ref", "base_ref")
    result_ref_commit = retained_ref("result_ref", "result_ref")
    registered_base = record.get("base_commit")
    if base_ref_commit and base_ref_commit != registered_base:
        reasons.append("base_ref does not preserve the registered base commit")
    result_commit = attestation.get("result_commit")
    if (not isinstance(result_commit, str) or len(result_commit) not in (40, 64)
            or any(character not in "0123456789abcdef" for character in result_commit)):
        reasons.append("result_commit must be a lowercase full commit ID")
    elif result_ref_commit and result_ref_commit != result_commit:
        reasons.append("result_ref does not preserve result_commit")

    if record.get("kind") == "integration":
        author_commit = attestation.get("author_commit")
        author_commit_valid = False
        author_commit_error: str | None = None
        if isinstance(author_commit, dict):
            try:
                author_root = _absolute_directory(author_commit.get("repo"), "author commit repository")
                if Path(run["author_repo"]) != author_root:
                    raise RuntimeErrorMessage("author_commit repository does not match the active run author checkout")
                _git_root(author_root)
                _commit_object(author_root, author_commit.get("commit"))
                if author_commit.get("delivery_association_attested") is not True:
                    raise RuntimeErrorMessage("author commit delivery association is not attested")
                author_commit_valid = True
            except (RuntimeErrorMessage, KeyError) as exc:
                author_commit_error = str(exc)
        early_reference_valid = False
        early_reference = attestation.get("early_retirement_author_ref")
        early_reference_error: str | None = None
        if early_reference is not None:
            try:
                early_path = _absolute_file(early_reference, "early-retirement author document")
                _ensure_disjoint(early_path, workspace, "author document and workspace")
                early_reference_valid = True
            except RuntimeErrorMessage as exc:
                early_reference_error = str(exc)
        if not author_commit_valid and not early_reference_valid:
            if author_commit_error:
                reasons.append(author_commit_error)
            if early_reference_error:
                reasons.append(early_reference_error)
            reasons.append("integration result needs an attested author delivery commit or early-retirement author document")

    return list(dict.fromkeys(reasons))


def command_workspace_preflight(args: argparse.Namespace) -> dict[str, Any]:
    session = _identifier(args.session, "session")
    data = _plugin_data(args.plugin_data)
    state, run_id, run = _active_run(data, session)
    workspace = _workspace_path_for_run(args.path, run, data)
    record = run["workspaces"].get(str(workspace))
    if record is None:
        raise RuntimeErrorMessage(f"workspace is not registered to this run: {workspace}")
    reasons = _preflight_reasons(workspace, run, record)
    return {"ready": not reasons, "disposition": "ready" if not reasons else "retain",
            "session_id": session, "run_id": run_id, "path": str(workspace), "reasons": reasons,
            "deletes_workspace": False}


def command_hook(args: argparse.Namespace) -> int:
    event = _read_hook_stdin()
    event_name = event.get("hook_event_name") or event.get("hookEventName")
    session = event.get("session_id")
    if event_name not in OBSERVED_EVENTS or not isinstance(session, str):
        return 0
    if event_name == "PreToolUse" and event.get("tool_name") not in ("spawn_agent", "Agent"):
        return 0
    is_dispatch = event_name == "PreToolUse"
    try:
        candidates: list[Path] = []
        env_data = os.environ.get("PLUGIN_DATA")
        if env_data and Path(env_data).is_absolute():
            candidates.append(Path(os.path.abspath(env_data)))
        located = _locator_data_for(session)
        if located is not None and located not in candidates:
            candidates.append(located)
        # Inactive and unrelated sessions are strictly read-only no-ops.
        active = None
        active_data = None
        state_error = None
        for data in candidates:
            try:
                active = _hook_state(data, session)
            except RuntimeErrorMessage as exc:
                state_error = exc
            if active:
                active_data = data
                break
        if not active:
            if state_error and located is not None:
                if is_dispatch:
                    print(json.dumps(_deny("Spawn blocked: active orchestration state is invalid; inspect the runtime diagnostic."), separators=(",", ":")))
                    print(str(state_error), file=sys.stderr)
                return 0
            return 0
        _, run_id, run = active
        fingerprint = run.get("package_fingerprint")
        if not isinstance(fingerprint, str):
            raise RuntimeErrorMessage("active run has no package fingerprint")
        runtime = active_data / "runtimes" / fingerprint
        _verify_runtime(runtime, fingerprint)
        decision = _dispatch_check(event) if event_name == "PreToolUse" else None
        _record_observation(active_data, session, run_id, event_name, event, decision is not None)
        if event_name == "PreToolUse":
            if decision:
                print(json.dumps(decision, separators=(",", ":")))
        elif event_name == "SessionStart" and event.get("source") in ("resume", "compact"):
            paths = _paths_for(runtime, fingerprint)
            coord = run.get("coord_root")
            content = (f"run={run_id}; coord={coord}; CLI={paths['cli']}; core={paths['core']}; "
                       f"controls: status --run-id {run_id}; deactivate --run-id {run_id}. "
                       "Follow core hold checks before dispatch or integration.")
            response = {"hookSpecificOutput": {
                "hookEventName": "SessionStart", "additionalContext": content,
            }}
            encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
            if len(encoded) > CONTEXT_LIMIT:
                raise RuntimeErrorMessage("pinned recovery paths exceed the 1 KiB hook output budget")
            sys.stdout.buffer.write(encoded)
        return 0
    except RuntimeErrorMessage as exc:
        if is_dispatch:
            print(json.dumps(_deny("Spawn blocked: active orchestration runtime validation failed; inspect the bounded diagnostic."), separators=(",", ":")))
            print(str(exc)[:2048], file=sys.stderr)
            return 0
        raise


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Explicit local orchestration runtime")
    commands = root.add_subparsers(dest="command", required=True)
    activate = commands.add_parser("activate", help="explicitly bind this host session to a pinned run")
    activate.add_argument("--session", required=True, help="canonical session_id from a real host hook event")
    activate.add_argument("--coord-root", required=True)
    activate.add_argument("--author-repo", required=True)
    activate.add_argument("--run-id")
    activate.add_argument("--plugin-data")
    status = commands.add_parser("status", help="inspect a session, run, or all active bindings")
    group = status.add_mutually_exclusive_group()
    group.add_argument("--session")
    group.add_argument("--run-id")
    status.add_argument("--plugin-data")
    deactivate = commands.add_parser("deactivate", help="remove a session or run binding; keep snapshots")
    group = deactivate.add_mutually_exclusive_group(required=True)
    group.add_argument("--session")
    group.add_argument("--run-id")
    deactivate.add_argument("--plugin-data")
    for name, help_text in (
        ("workspace-register", "register an isolated workspace for a pinned run"),
        ("workspace-release", "record an external release statement for a workspace"),
        ("workspace-preflight", "check release and repository retention conditions"),
    ):
        workspace = commands.add_parser(name, help=help_text)
        workspace.add_argument("--session", required=True)
        workspace.add_argument("--path", required=True)
        workspace.add_argument("--plugin-data")
        if name == "workspace-register":
            workspace.add_argument("--kind", required=True, choices=("worker", "integration"))
            workspace.add_argument("--base-commit", required=True)
        elif name == "workspace-release":
            workspace.add_argument("--attestation", required=True)
    hook = commands.add_parser("hook", help=argparse.SUPPRESS)
    hook.set_defaults(_hook=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "hook":
            return command_hook(args)
        if args.command == "activate":
            result = command_activate(args)
        elif args.command == "status":
            result = command_status(args)
        elif args.command == "deactivate":
            result = command_deactivate(args)
        elif args.command == "workspace-register":
            result = command_workspace_register(args)
        elif args.command == "workspace-release":
            result = command_workspace_release(args)
        elif args.command == "workspace-preflight":
            result = command_workspace_preflight(args)
        else:
            raise RuntimeErrorMessage("unknown command")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except RuntimeErrorMessage as exc:
        print(f"orchestration: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
