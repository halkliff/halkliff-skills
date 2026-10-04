#!/usr/bin/env python3
"""Read-only hook router from the installed plugin to an activated snapshot."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


STATE_NAME = "orchestration-state.json"
SUPPORTED_EVENTS = {"PreToolUse", "SessionStart", "SubagentStart", "SubagentStop"}
REQUIRED_FILES = (
    "plugin.json", "hooks/hooks.json", "hooks/bootstrap.py", "scripts/orchestration.py",
    "skills/orchestrate-work-plugin/SKILL.md",
    "support/skills/orchestrate-work/SKILL.md",
    "support/skills/orchestrate-work/references/worker.md",
    "support/skills/define-goal/SKILL.md",
)


def _link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _reject_links(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    for part in (absolute, *absolute.parents):
        if _link(part):
            raise ValueError(f"symlink or junction in hook path: {part}")


def _error(message: str) -> int:
    print(f"orchestration hook: {message}", file=sys.stderr)
    return 0


def _state(data: Path) -> dict[str, Any] | None:
    _reject_links(data / STATE_NAME)
    try:
        result = json.loads((data / STATE_NAME).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"active runtime state cannot be read: {exc}") from exc
    if (not isinstance(result, dict) or result.get("schema_version") != 1
            or not isinstance(result.get("runs"), dict) or not isinstance(result.get("bindings"), dict)):
        raise ValueError("active runtime state has an unsupported schema")
    for bound_session, run_id in result["bindings"].items():
        if not isinstance(bound_session, str) or not isinstance(run_id, str) or run_id not in result["runs"]:
            raise ValueError("active runtime state has inconsistent session bindings")
    return result


def _locator_path() -> Path:
    override = os.environ.get("ORCHESTRATE_WORK_LOCATOR")
    if override:
        path = Path(override)
        if not path.is_absolute():
            raise ValueError("ORCHESTRATE_WORK_LOCATOR is not an absolute path")
        return Path(os.path.abspath(path))
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    if not base.is_absolute():
        raise ValueError("CODEX_HOME is not an absolute path")
    return Path(os.path.abspath(base / "orchestration-plugin" / "locator.json"))


def _locator_data(session: str) -> Path | None:
    path = _locator_path()
    _reject_links(path)
    try:
        locator = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"session locator cannot be read: {exc}") from exc
    if (not isinstance(locator, dict) or locator.get("schema_version") != 1
            or not isinstance(locator.get("bindings"), dict)):
        raise ValueError("session locator has an unsupported schema")
    value = locator["bindings"].get(session)
    if value is None:
        return None
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError("session locator has an invalid PLUGIN_DATA path")
    result = Path(os.path.abspath(value))
    _reject_links(result)
    return result


def _verified_runtime(root: Path, expected: str) -> Path:
    _reject_links(root)
    _reject_links(root / "build-info.json")
    try:
        info = json.loads((root / "build-info.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"pinned build-info is missing or invalid: {exc}") from exc
    if not isinstance(info, dict) or info.get("schema_version") != 1 or not isinstance(info.get("files"), dict):
        raise ValueError("pinned build-info has an unsupported schema")
    files: dict[str, str] = {}
    for raw, digest in info["files"].items():
        if (not isinstance(raw, str) or not raw or raw.startswith("/") or "\\" in raw or ":" in raw
                or any(part in ("", ".", "..") for part in raw.split("/"))
                or not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("pinned build-info contains an invalid path or digest")
        target = root.joinpath(*raw.split("/"))
        try:
            target.absolute().relative_to(root.absolute())
        except ValueError as exc:
            raise ValueError(f"pinned asset escapes runtime root: {raw}") from exc
        _reject_links(target)
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f"pinned asset is missing or changed: {raw}")
        files[raw] = digest
    missing = [item for item in REQUIRED_FILES if item not in files]
    if missing:
        raise ValueError("pinned build-info omits required assets: " + ", ".join(missing))
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":"),
                                           ensure_ascii=False).encode("utf-8")).hexdigest()
    if info.get("package_fingerprint") != fingerprint or fingerprint != expected:
        raise ValueError("pinned package fingerprint is inconsistent")
    try:
        manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"pinned plugin manifest is invalid: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("name"), str):
        raise ValueError("pinned plugin manifest has no valid name")
    return root / "scripts" / "orchestration.py"


def _dispatch_denial() -> bytes:
    denial = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": "Spawn blocked: active orchestration runtime validation failed; inspect the bounded diagnostic.",
    }}
    return (json.dumps(denial, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    active_dispatch = False
    active = False
    try:
        raw = sys.stdin.buffer.read()
        try:
            event = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return _error("host event is not valid UTF-8 JSON")
        if not isinstance(event, dict):
            return _error("host event must be a JSON object")
        event_name = event.get("hook_event_name") or event.get("hookEventName")
        active_dispatch = event_name == "PreToolUse" and event.get("tool_name") in ("spawn_agent", "Agent")
        if event_name not in SUPPORTED_EVENTS:
            return 0
        if event_name == "PreToolUse" and not active_dispatch:
            return 0
        if event_name == "SessionStart" and event.get("source") not in ("resume", "compact"):
            return 0
        session = event.get("session_id")
        if not isinstance(session, str) or not session:
            return 0
        candidates: list[Path] = []
        data_value = os.environ.get("PLUGIN_DATA")
        if data_value:
            data = Path(data_value)
            if not data.is_absolute():
                return _error("PLUGIN_DATA is not an absolute path")
            _reject_links(data)
            candidates.append(data)
        locator_data = _locator_data(session)
        if locator_data is not None and locator_data not in candidates:
            candidates.append(locator_data)
        selected = None
        run_id = None
        run = None
        state_error: Exception | None = None
        locator_membership = locator_data is not None
        for candidate in candidates:
            try:
                state = _state(candidate)
            except ValueError as exc:
                state_error = exc
                continue
            if state is None:
                continue
            candidate_run_id = state["bindings"].get(session)
            if candidate_run_id is None:
                continue
            active = True
            candidate_run = state["runs"].get(candidate_run_id) if isinstance(candidate_run_id, str) else None
            selected, run_id, run = candidate, candidate_run_id, candidate_run
            break
        if selected is None and locator_membership:
            active = True
            selected = locator_data
            if state_error:
                raise ValueError(f"locator-bound session state is invalid: {state_error}")
            raise ValueError("locator-bound session has no matching active state binding")
        if not active:
            return 0
        data = selected
        if not isinstance(run, dict):
            raise ValueError("active session binding references a missing run")
        fingerprint = run.get("package_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
            raise ValueError("active run has an invalid package fingerprint")
        installed = os.environ.get("PLUGIN_ROOT")
        if not installed:
            raise ValueError("PLUGIN_ROOT is missing for an active session")
        installed_root = Path(installed)
        if not installed_root.is_absolute():
            raise ValueError("PLUGIN_ROOT is not an absolute path")
        _reject_links(installed_root)
        pinned_root = data / "runtimes" / fingerprint
        _reject_links(pinned_root)
        try:
            pinned_root.relative_to(data)
        except ValueError:
            raise ValueError("pinned runtime escapes PLUGIN_DATA")
        script = _verified_runtime(pinned_root, fingerprint)
        child_env = os.environ.copy()
        child_env["PLUGIN_ROOT"] = str(pinned_root)
        child_env["PLUGIN_DATA"] = str(data)
        proc = subprocess.run([sys.executable, str(script), "hook"], input=raw,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=child_env, check=False)
        if proc.stdout:
            sys.stdout.buffer.write(proc.stdout)
        if proc.stderr:
            sys.stderr.buffer.write(proc.stderr)
        if active_dispatch and proc.returncode != 0:
            sys.stdout.buffer.write(_dispatch_denial())
        return 0
    except (OSError, ValueError) as exc:
        if active and active_dispatch:
            sys.stdout.buffer.write(_dispatch_denial())
            print(str(exc)[:2048], file=sys.stderr)
            return 0
        return _error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
