"""Mechanical policy validation and checked adapter operations.

This module takes the runtime module as an adapter so it can be copied into a
pinned package without importing orchestration.py or creating an import cycle.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import uuid
from contextlib import ExitStack
from pathlib import Path
from typing import Any


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX = re.compile(r"^[0-9a-f]{64}$")
_HEAD = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
_MODELS = {
    "gpt-6.1-sol": {"high", "xhigh"},
    "gpt-6-luna": {"xhigh"},
    "gpt-6.1-terra": {"high", "xhigh"},
}
_CLAIMS = {"source", "commit", "build", "installed_caller", "integrated", "hosted"}
_DEFAULT_ROLES = {
    "coordinator": {"model": "gpt-6.1-sol", "effort": "xhigh"},
    "orchestrator": {"model": "gpt-6.1-sol", "effort": "xhigh"},
    "worker": {"model": "gpt-6-luna", "effort": "xhigh"},
}
_REQUEST_KEYS = {
    "schema_version", "policy_revision", "grant", "role", "adapter", "consumer",
    "claim_kind", "procedure", "workspace", "expected_head", "inputs", "dependencies", "scan",
}
_MAX_POLICY_BYTES = 1_048_576
_MAX_REQUEST_BYTES = 1_048_576
_MAX_INPUT_BYTES = 67_108_864
_MAX_ITEMS = 128


class ObservationFailure(Exception):
    """An authorized filesystem or Git observation could not be completed."""


def _error(rt: Any, message: str) -> None:
    raise rt.RuntimeErrorMessage(message)


def _is_int(value: Any, minimum: int = 1) -> bool:
    return type(value) is int and value >= minimum


def _text(rt: Any, value: Any, label: str, maximum: int = 512) -> str:
    if (not isinstance(value, str) or not value or len(value) > maximum
            or any(ord(character) < 32 for character in value)):
        _error(rt, f"{label} must be non-empty text of at most {maximum} characters")
    return value


def _identifier(rt: Any, value: Any, label: str) -> str:
    text = _text(rt, value, label, 128)
    if not _ID.fullmatch(text):
        _error(rt, f"{label} must be a bounded identifier")
    return text


def _object(rt: Any, value: Any, label: str, keys: set[str], required: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        _error(rt, f"{label} must be an object")
    unknown = set(value) - keys
    missing = (required or set()) - set(value)
    if unknown:
        _error(rt, f"{label} has unknown fields: {', '.join(sorted(map(str, unknown)))}")
    if missing:
        _error(rt, f"{label} is missing fields: {', '.join(sorted(missing))}")
    return value


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _read_json(rt: Any, path: Path, label: str, maximum: int) -> tuple[dict[str, Any], bytes]:
    try:
        with path.open("rb") as stream:
            raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            _error(rt, f"{label} exceeds its {maximum}-byte limit")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except rt.RuntimeErrorMessage:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _error(rt, f"{label} is unreadable JSON: {exc}")
    if not isinstance(value, dict):
        _error(rt, f"{label} must contain a JSON object")
    return value, raw


def _hash_file(rt: Any, path: Path, label: str) -> str:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1_048_576), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except rt.RuntimeErrorMessage:
        raise
    except OSError as exc:
        raise ObservationFailure(f"{label} cannot be read: {exc}") from exc


def _digest(rt: Any, value: Any, label: str) -> str:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        _error(rt, f"{label} must be a lowercase SHA-256 digest")
    return value


def _full_head(rt: Any, value: Any, label: str) -> str:
    if not isinstance(value, str) or not _HEAD.fullmatch(value):
        _error(rt, f"{label} must be a full hexadecimal Git commit ID")
    return value.lower()


def _path_text(rt: Any, raw: Any, label: str, directory: bool) -> Path:
    if directory:
        return rt._absolute_directory(raw, label)
    return rt._absolute_file(raw, label)


def _validate_resource_value(rt: Any, value: Any, label: str) -> dict[str, Any]:
    item = _object(rt, value, label, {"bytes", "basis_ref"}, {"bytes", "basis_ref"})
    if not _is_int(item["bytes"]):
        _error(rt, f"{label}.bytes must be a positive integer")
    return {"bytes": item["bytes"], "basis_ref": _text(rt, item["basis_ref"], f"{label}.basis_ref", 1024)}


def _canonical_path(rt: Any, raw: Any, label: str, directory: bool, verify: bool) -> Path:
    if verify:
        return _path_text(rt, raw, label, directory)
    if not isinstance(raw, str) or not Path(raw).is_absolute():
        _error(rt, f"{label} must be an absolute {'directory' if directory else 'file'} path")
    return Path(os.path.abspath(raw))


def _validate_policy(rt: Any, raw: Any, verify_targets: bool = True) -> dict[str, Any]:
    policy = _object(rt, raw, "policy", {
        "schema_version", "revision", "author_constraints", "root_controls", "roles",
        "resources", "grants", "adapters", "integration",
    }, {"schema_version", "revision", "resources", "grants", "adapters"})
    if policy["schema_version"] != 1 or type(policy["schema_version"]) is not int:
        _error(rt, "policy schema_version must be 1")
    if not _is_int(policy["revision"]):
        _error(rt, "policy revision must be a positive integer")

    author = policy.get("author_constraints", {})
    author = _object(rt, author, "author_constraints", {"resource_floor"})
    controls = policy.get("root_controls", {})
    controls = _object(rt, controls, "root_controls", {"resource_headroom"})
    normalized: dict[str, Any] = {
        "schema_version": 1,
        "revision": policy["revision"],
        "author_constraints": ({"resource_floor": _validate_resource_value(rt, author["resource_floor"], "author_constraints.resource_floor")}
                               if "resource_floor" in author else {}),
        "root_controls": ({"resource_headroom": _validate_resource_value(rt, controls["resource_headroom"], "root_controls.resource_headroom")}
                           if "resource_headroom" in controls else {}),
    }
    roles = dict(_DEFAULT_ROLES)
    supplied_roles = policy.get("roles", {})
    if not isinstance(supplied_roles, dict) or len(supplied_roles) > _MAX_ITEMS:
        _error(rt, "roles must be a bounded role-to-route object")
    for role, route in supplied_roles.items():
        role = _identifier(rt, role, "role")
        route = _object(rt, route, f"roles.{role}", {"model", "effort"}, {"model", "effort"})
        model = route["model"]
        effort = route["effort"]
        if not isinstance(model, str) or not isinstance(effort, str) or model not in _MODELS or effort not in _MODELS[model]:
            _error(rt, f"roles.{role} has an unsupported model or reasoning effort")
        roles[role] = {"model": model, "effort": effort}
    normalized["roles"] = roles

    resources = policy["resources"]
    if not isinstance(resources, dict) or len(resources) > _MAX_ITEMS:
        _error(rt, "resources must be a bounded resource-to-owner object")
    normalized_resources: dict[str, Any] = {}
    for resource_id, resource in resources.items():
        resource_id = _identifier(rt, resource_id, "resource id")
        resource = _object(rt, resource, f"resources.{resource_id}", {"owner"}, {"owner"})
        normalized_resources[resource_id] = {"owner": _text(rt, resource["owner"], f"resources.{resource_id}.owner")}
    normalized["resources"] = normalized_resources

    adapters = policy["adapters"]
    if not isinstance(adapters, dict) or len(adapters) > _MAX_ITEMS:
        _error(rt, "adapters must be a bounded adapter object")
    normalized_adapters: dict[str, Any] = {}
    for adapter_id, adapter in adapters.items():
        adapter_id = _identifier(rt, adapter_id, "adapter id")
        adapter = _object(rt, adapter, f"adapters.{adapter_id}", {"command", "sha256", "claim_kinds"},
                          {"command", "sha256", "claim_kinds"})
        command, hashes, claims = adapter["command"], adapter["sha256"], adapter["claim_kinds"]
        if not isinstance(command, list) or len(command) != 2:
            _error(rt, f"adapters.{adapter_id}.command must contain an executable and one script")
        if not isinstance(hashes, list) or len(hashes) != 2:
            _error(rt, f"adapters.{adapter_id}.sha256 must contain executable and script hashes")
        paths = [_canonical_path(rt, item, f"adapters.{adapter_id}.command[{index}]", False, verify_targets)
                 for index, item in enumerate(command)]
        actual_hashes = [_digest(rt, item, f"adapters.{adapter_id}.sha256[{index}]") for index, item in enumerate(hashes)]
        for index, path in enumerate(paths):
            if verify_targets:
                try:
                    actual = _hash_file(rt, path, f"adapter {adapter_id} command file")
                except ObservationFailure as exc:
                    _error(rt, str(exc))
                if actual != actual_hashes[index]:
                    _error(rt, f"adapter {adapter_id} command file hash changed: {path}")
        if (not isinstance(claims, list) or not claims or len(claims) > len(_CLAIMS)
                or any(not isinstance(item, str) or item not in _CLAIMS for item in claims)
                or len(set(claims)) != len(claims)):
            _error(rt, f"adapters.{adapter_id}.claim_kinds contains an invalid or duplicate claim")
        normalized_adapters[adapter_id] = {
            "command": [str(path) for path in paths], "sha256": actual_hashes, "claim_kinds": list(claims),
        }
    normalized["adapters"] = normalized_adapters

    grants = policy["grants"]
    if not isinstance(grants, dict) or not grants or len(grants) > _MAX_ITEMS:
        _error(rt, "grants must be a non-empty bounded grant object")
    normalized_grants: dict[str, Any] = {}
    grant_keys = {"owner", "roles", "adapters", "resources", "workspace", "basis_ref", "max_invocations"}
    for grant_id, grant in grants.items():
        grant_id = _identifier(rt, grant_id, "grant id")
        grant = _object(rt, grant, f"grants.{grant_id}", grant_keys,
                        {"owner", "roles", "adapters", "resources", "workspace", "basis_ref"})
        owner = _text(rt, grant["owner"], f"grants.{grant_id}.owner")
        def names(field: str, available: dict[str, Any], allow_empty: bool = False) -> list[str]:
            value = grant[field]
            if (not isinstance(value, list) or (not value and not allow_empty) or len(value) > _MAX_ITEMS):
                _error(rt, f"grants.{grant_id}.{field} must be a non-empty bounded list")
            result = [_identifier(rt, name, f"grants.{grant_id}.{field} entry") for name in value]
            if len(set(result)) != len(result) or any(name not in available for name in result):
                _error(rt, f"grants.{grant_id}.{field} contains duplicate or unknown names")
            return result
        allowed_roles = names("roles", roles)
        allowed_adapters = names("adapters", normalized_adapters, allow_empty=True)
        allowed_resources = names("resources", normalized_resources, allow_empty=True)
        workspace = _canonical_path(rt, grant["workspace"], f"grants.{grant_id}.workspace", True, verify_targets)
        if verify_targets:
            rt._git_root(workspace)
        maximum = grant.get("max_invocations", 1)
        if not _is_int(maximum):
            _error(rt, f"grants.{grant_id}.max_invocations must be a positive integer")
        normalized_grants[grant_id] = {
            "owner": owner, "roles": allowed_roles, "adapters": allowed_adapters,
            "resources": allowed_resources, "workspace": str(workspace),
            "basis_ref": _text(rt, grant["basis_ref"], f"grants.{grant_id}.basis_ref", 1024),
            "max_invocations": maximum,
        }
    normalized["grants"] = normalized_grants

    integration = policy.get("integration")
    if integration is None:
        normalized["integration"] = None
    else:
        integration = _object(rt, integration, "integration", {"workspace", "owner"}, {"workspace", "owner"})
        workspace = _canonical_path(rt, integration["workspace"], "integration.workspace", True, verify_targets)
        if verify_targets:
            rt._git_root(workspace)
        normalized["integration"] = {
            "workspace": str(workspace), "owner": _text(rt, integration["owner"], "integration.owner"),
        }
    return normalized


def load_policy(rt: Any, path: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    file_path = _path_text(rt, path, "policy file", False)
    value, raw = _read_json(rt, file_path, "policy file", _MAX_POLICY_BYTES)
    policy = _validate_policy(rt, value)
    pointer = {"path": str(file_path), "sha256": rt._sha256(raw), "revision": policy["revision"]}
    return policy, pointer


def selected_policy(rt: Any, run: dict[str, Any]) -> dict[str, Any]:
    pointer = run.get("policy")
    if not isinstance(pointer, dict) or set(pointer) != {"path", "sha256", "revision"}:
        _error(rt, "run has no valid selected policy pointer")
    file_path = _path_text(rt, pointer.get("path"), "selected policy file", False)
    value, raw = _read_json(rt, file_path, "selected policy file", _MAX_POLICY_BYTES)
    policy = _validate_policy(rt, value, verify_targets=False)
    actual = {"path": str(file_path), "sha256": rt._sha256(raw), "revision": policy["revision"]}
    if (pointer.get("path") != actual["path"] or pointer.get("sha256") != actual["sha256"]
            or pointer.get("revision") != actual["revision"]):
        _error(rt, "selected policy changed after it was pinned")
    return policy


def dispatch_check(rt: Any, event: dict[str, Any], session: str, run: dict[str, Any]) -> None:
    if event.get("tool_name") not in ("spawn_agent", "Agent"):
        return
    policy = selected_policy(rt, run)
    args = event.get("tool_input")
    if not isinstance(args, dict):
        _error(rt, "spawn input is missing")
    markers: list[tuple[str, str, int]] = []
    for field in ("message", "prompt"):
        value = args.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or len(value) > 16_384:
            _error(rt, f"spawn {field} must be bounded text")
        for line in value.splitlines():
            match = re.fullmatch(r"ORCHESTRATION role=([A-Za-z0-9][A-Za-z0-9._:-]{0,127}) grant=([A-Za-z0-9][A-Za-z0-9._:-]{0,127}) revision=([1-9][0-9]{0,8})", line)
            if line.startswith("ORCHESTRATION "):
                if not match:
                    _error(rt, "dispatch marker is malformed")
                markers.append((match.group(1), match.group(2), int(match.group(3))))
    if len(markers) != 1:
        _error(rt, "spawn must contain exactly one bounded ORCHESTRATION dispatch marker")
    role, grant_id, revision = markers[0]
    pointer = run["policy"]
    if revision != pointer["revision"]:
        _error(rt, "dispatch marker uses a stale policy revision")
    grant = policy["grants"].get(grant_id)
    if not grant or grant["owner"] != session or role not in grant["roles"]:
        _error(rt, "dispatch grant, owner, or role is not selected for this session")
    if any(policy["resources"][name]["owner"] != session for name in grant["resources"]):
        _error(rt, "dispatch grant names a resource not owned by this session")
    usage_map = run.get("grant_usage", {})
    if not isinstance(usage_map, dict):
        _error(rt, "run has invalid grant usage records")
    usage = usage_map.get(grant_id, {})
    if (not isinstance(usage, dict) or not isinstance(usage.get("failed", False), bool)
            or not isinstance(usage.get("pending_invocation", False), bool)
            or usage.get("failed", False) or usage.get("pending_invocation", False)):
        _error(rt, "dispatch grant has already failed")
    count = usage.get("invocations", 0)
    if not _is_int(count, 0):
        _error(rt, "dispatch grant has an invalid invocation count")
    route = policy["roles"].get(role)
    if not route or args.get("model") != route["model"] or args.get("reasoning_effort") != route["effort"]:
        _error(rt, "spawn model and reasoning effort do not match the selected role")
    if args.get("fork_turns") != "none":
        _error(rt, "spawn must set fork_turns to 'none'")


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _array_value(rt: Any, path: Path, key: Any, label: str) -> tuple[str, int]:
    try:
        with path.open("rb") as stream:
            raw = stream.read(_MAX_INPUT_BYTES + 1)
        if len(raw) > _MAX_INPUT_BYTES:
            _error(rt, f"{label} exceeds the {_MAX_INPUT_BYTES}-byte input limit")
        digest = rt._sha256(raw)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except rt.RuntimeErrorMessage:
        raise
    except OSError as exc:
        raise ObservationFailure(f"{label} cannot be read: {exc}") from exc
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        _error(rt, f"{label} is unreadable JSON: {exc}")
    if key is None:
        array = value
    else:
        key = _text(rt, key, f"{label}.key", 256)
        array = value.get(key) if isinstance(value, dict) else None
    if not isinstance(array, list):
        _error(rt, f"{label} must be a JSON array or contain the named array")
    if len(array) > 1_000_000:
        _error(rt, f"{label} exceeds the one-million-item array limit")
    return digest, len(array)


def _head(rt: Any, path: Path, label: str) -> str:
    try:
        root = Path(os.path.abspath(rt._git(path, "rev-parse", "--show-toplevel")))
        if root != path:
            _error(rt, f"{label} must be the exact Git checkout root: {path}")
        return rt._git(path, "rev-parse", "--verify", "HEAD^{commit}").lower()
    except rt.RuntimeErrorMessage as exc:
        if str(exc).startswith("Git inspection failed"):
            raise ObservationFailure(f"{label} Git identity could not be observed: {exc}") from exc
        raise


def _checkout_identity(rt: Any, path: Path, label: str) -> dict[str, Any]:
    head = _head(rt, path, label)
    try:
        status = rt._git(path, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
    except rt.RuntimeErrorMessage as exc:
        raise ObservationFailure(f"{label} checkout status could not be observed: {exc}") from exc
    return {"path": str(path), "head": head, "clean": not status, "git_status": status}


def _prepare_request(rt: Any, request_path: Path, request: dict[str, Any], raw: bytes,
                     scope: dict[str, Any], run: dict[str, Any],
                     observations: list[dict[str, Any]]) -> dict[str, Any]:
    policy, pointer = scope["policy"], scope["pointer"]
    session, run_id = scope["session"], scope["run_id"]
    grant_id, grant = scope["grant_id"], scope["grant"]
    role, adapter_id = scope["role"], scope["adapter_id"]
    adapter = policy["adapters"][adapter_id]
    consumer = _text(rt, request["consumer"], "consumer", 512)
    claim = scope["claim_kind"]
    procedure = _text(rt, request["procedure"], "procedure", 1024)
    workspace = _path_text(rt, request["workspace"], "operation workspace", True)
    if str(workspace) != grant["workspace"]:
        _error(rt, "operation workspace differs from the grant workspace")
    expected_head = _full_head(rt, request["expected_head"], "expected_head")
    actual_head = _head(rt, workspace, "operation workspace")
    observations.append({"kind": "workspace-head", "expected": expected_head, "actual": actual_head})
    if actual_head != expected_head:
        _error(rt, f"operation workspace HEAD differs: expected {expected_head}, actual {actual_head}")
    record = run.get("workspaces", {}).get(str(workspace))
    if not isinstance(record, dict) or record.get("owner") != session or record.get("path") != str(workspace):
        _error(rt, "operation workspace is not registered to this session")
    try:
        registered_base = rt._commit_object(workspace, record.get("base_commit"))
    except rt.RuntimeErrorMessage as exc:
        raise ObservationFailure(f"registered base commit could not be observed: {exc}") from exc
    if claim in {"integrated", "hosted"} or record.get("kind") == "integration":
        integration = policy.get("integration")
        if (record.get("kind") != "integration" or not integration
                or integration["workspace"] != str(workspace) or integration["owner"] != session):
            _error(rt, "integration operation must match the selected integration workspace and owner")
    dependencies: dict[str, Any] = {}
    raw_dependencies = request.get("dependencies", {})
    if not isinstance(raw_dependencies, dict) or len(raw_dependencies) > _MAX_ITEMS:
        _error(rt, "dependencies must be a bounded name-to-Git-root object")
    for name, item in raw_dependencies.items():
        name = _identifier(rt, name, "dependency name")
        item = _object(rt, item, f"dependencies.{name}", {"path", "head"}, {"path", "head"})
        path = _path_text(rt, item["path"], f"dependency {name}", True)
        expected = _full_head(rt, item["head"], f"dependencies.{name}.head")
        observed = _checkout_identity(rt, path, f"dependency {name}")
        observations.append({"kind": "dependency-head", "name": name, "expected": expected, "actual": observed})
        if expected != observed["head"]:
            _error(rt, f"dependency {name} HEAD differs: expected {expected}, actual {observed['head']}")
        if not observed["clean"]:
            _error(rt, f"dependency {name} checkout is dirty: {observed['git_status']}")
        dependencies[name] = observed

    inputs = request["inputs"]
    if not isinstance(inputs, dict) or not inputs or len(inputs) > _MAX_ITEMS:
        _error(rt, "inputs must contain at least one bounded named input")
    actual_inputs: dict[str, Any] = {}
    for name, item in inputs.items():
        name = _identifier(rt, name, "input name")
        if not isinstance(item, dict):
            _error(rt, f"inputs.{name} must be an object")
        kind = item.get("kind")
        if isinstance(kind, str) and kind in {"file", "json-array"}:
            keys = {"kind", "path", "sha256"} | ({"key"} if kind == "json-array" else set())
            item = _object(rt, item, f"inputs.{name}", keys, {"kind", "path", "sha256"})
            path = _path_text(rt, item["path"], f"input {name}", False)
            expected = _digest(rt, item["sha256"], f"inputs.{name}.sha256")
            if kind == "file":
                actual = _hash_file(rt, path, f"input {name}")
                observations.append({"kind": "file-hash", "name": name, "expected": expected, "actual": actual})
                if actual != expected:
                    _error(rt, f"input {name} SHA-256 differs: expected {expected}, actual {actual}")
                actual_inputs[name] = {"kind": kind, "path": str(path), "sha256": actual}
            else:
                actual, count = _array_value(rt, path, item.get("key"), f"input {name}")
                observations.append({"kind": "json-array", "name": name, "expected": expected,
                                     "actual": actual, "count": count})
                if actual != expected:
                    _error(rt, f"input {name} SHA-256 differs: expected {expected}, actual {actual}")
                derived = {"kind": kind, "path": str(path), "sha256": actual, "count": count}
                if item.get("key") is not None:
                    derived["key"] = item["key"]
                actual_inputs[name] = derived
        elif kind == "git":
            item = _object(rt, item, f"inputs.{name}", {"kind", "path", "head"}, {"kind", "path", "head"})
            path = _path_text(rt, item["path"], f"Git input {name}", True)
            expected = _full_head(rt, item["head"], f"inputs.{name}.head")
            observed = _checkout_identity(rt, path, f"Git input {name}")
            observations.append({"kind": "git-head", "name": name, "expected": expected, "actual": observed})
            if observed["head"] != expected:
                _error(rt, f"Git input {name} HEAD differs: expected {expected}, actual {observed['head']}")
            if not observed["clean"]:
                _error(rt, f"Git input {name} checkout is dirty: {observed['git_status']}")
            actual_inputs[name] = {"kind": kind, **observed}
        else:
            _error(rt, f"inputs.{name}.kind must be file, json-array, or git")

    scan = request.get("scan")
    if scan is not None:
        scan = _object(rt, scan, "scan", {"reason", "basis_ref", "input"}, {"reason", "basis_ref"})
        if not isinstance(scan["reason"], str) or scan["reason"] not in {"changed_input", "contradiction", "first_admission", "new_claim"}:
            _error(rt, "scan.reason is unsupported")
        scan = {"reason": scan["reason"], "basis_ref": _text(rt, scan["basis_ref"], "scan.basis_ref", 1024)}
        if request.get("scan", {}).get("reason") == "changed_input":
            input_name = _identifier(rt, request["scan"].get("input"), "scan.input")
            if input_name not in actual_inputs:
                _error(rt, "changed_input scan must name an actual operation input")
            scan["input"] = input_name
        elif "input" in request.get("scan", {}):
            _error(rt, "scan.input is valid only for changed_input")

    command = list(adapter["command"])
    hashes = list(adapter["sha256"])
    for index, raw_path in enumerate(command):
        path = _path_text(rt, raw_path, f"adapter {adapter_id} command file", False)
        actual = _hash_file(rt, path, f"adapter {adapter_id} command file")
        if actual != hashes[index]:
            _error(rt, f"adapter {adapter_id} command file changed before invocation: expected {hashes[index]}, actual {actual}")
    author_floor = policy["author_constraints"].get("resource_floor")
    root_headroom = policy["root_controls"].get("resource_headroom")
    reuse_identity = {
        "consumer": consumer, "claim_kind": claim, "procedure": procedure,
        "adapter": {"id": adapter_id, "command": command, "sha256": hashes},
        "workspace": str(workspace), "inputs": actual_inputs, "dependencies": dependencies,
    }
    if claim in {"commit", "integrated", "hosted"}:
        reuse_identity["candidate_head"] = actual_head
    full_identity = {**reuse_identity, "candidate": {"path": str(workspace), "head": actual_head}, "policy": pointer}
    return {
        "session": session, "run_id": run_id, "request_path": str(request_path),
        "request_sha256": rt._sha256(raw), "policy": pointer, "policy_data": policy,
        "grant_id": grant_id, "grant": grant, "role": role, "adapter_id": adapter_id,
        "adapter": adapter, "command": command, "command_hashes": hashes,
        "consumer": consumer, "claim_kind": claim, "procedure": procedure,
        "workspace": workspace, "expected_head": expected_head, "actual_head": actual_head,
        "registered_base": registered_base, "inputs": actual_inputs, "dependencies": dependencies, "scan": scan,
        "resource_attribution": {"author_floor": author_floor, "root_headroom": root_headroom},
        "reuse_identity": reuse_identity, "reuse_key": rt._sha256(rt._canonical_json(reuse_identity)),
        "signature": rt._sha256(rt._canonical_json(full_identity)),
    }


def _operation_scope(rt: Any, request: dict[str, Any], session: str,
                     run_id: str, run: dict[str, Any]) -> dict[str, Any]:
    _object(rt, request, "operation request", _REQUEST_KEYS,
            {"schema_version", "policy_revision", "grant", "role", "adapter", "consumer",
             "claim_kind", "procedure", "workspace", "expected_head", "inputs"})
    if type(request["schema_version"]) is not int or request["schema_version"] != 1:
        _error(rt, "operation request schema_version must be 1")
    policy = selected_policy(rt, run)
    pointer = dict(run["policy"])
    if type(request["policy_revision"]) is not int or request["policy_revision"] != pointer["revision"]:
        _error(rt, "operation request policy revision is stale")
    grant_id = _identifier(rt, request["grant"], "grant id")
    grant = policy["grants"].get(grant_id)
    if not grant or grant["owner"] != session:
        _error(rt, "operation grant is not selected for this session")
    role = _identifier(rt, request["role"], "role")
    if role not in grant["roles"] or role not in policy["roles"]:
        _error(rt, "operation role is not allowed by the selected grant")
    adapter_id = _identifier(rt, request["adapter"], "adapter id")
    adapter = policy["adapters"].get(adapter_id)
    if adapter_id not in grant["adapters"] or not adapter:
        _error(rt, "operation adapter is not allowed by the selected grant")
    claim = request["claim_kind"]
    if not isinstance(claim, str) or claim not in _CLAIMS or claim not in adapter["claim_kinds"]:
        _error(rt, "operation claim kind is not allowed by the selected adapter")
    if any(policy["resources"][name]["owner"] != session for name in grant["resources"]):
        _error(rt, "operation grant names a resource not owned by this session")
    return {"session": session, "run_id": run_id, "pointer": pointer,
            "policy": policy, "grant_id": grant_id, "grant": grant,
            "role": role, "adapter_id": adapter_id, "claim_kind": claim}


def _identity_now(rt: Any, prepared: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, item in prepared["inputs"].items():
        try:
            path = Path(item["path"])
            if item["kind"] == "git":
                result[name] = {"kind": "git", **_checkout_identity(rt, path, f"Git input {name}")}
            elif item["kind"] == "json-array":
                digest, count = _array_value(rt, path, item.get("key"), f"input {name}")
                result[name] = {"kind": "json-array", "path": str(path), "sha256": digest, "count": count,
                                **({"key": item["key"]} if "key" in item else {})}
            else:
                result[name] = {"kind": "file", "path": str(path), "sha256": _hash_file(rt, path, f"input {name}")}
        except (rt.RuntimeErrorMessage, ObservationFailure, OSError) as exc:
            result[name] = {"kind": item.get("kind"), "status": "unknown", "error": str(exc)[:512]}
    return result


def _dependency_now(rt: Any, dependencies: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, item in dependencies.items():
        try:
            path = Path(item["path"])
            result[name] = _checkout_identity(rt, path, f"dependency {name}")
        except (rt.RuntimeErrorMessage, ObservationFailure, OSError) as exc:
            result[name] = {"path": item["path"], "status": "unknown", "error": str(exc)[:512]}
    return result


def _post_head(rt: Any, workspace: Path) -> dict[str, Any]:
    try:
        return {"status": "observed", "head": _head(rt, workspace, "operation workspace")}
    except (rt.RuntimeErrorMessage, ObservationFailure, OSError) as exc:
        return {"status": "unknown", "error": str(exc)[:512]}


def _new_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _operation_root(rt: Any, run: dict[str, Any]) -> Path:
    coord = _path_text(rt, run.get("coord_root"), "coordination root", True)
    root = coord / "artifacts" / "operations"
    rt._reject_link_ancestry(root)
    root.mkdir(parents=True, exist_ok=True)
    rt._reject_link_ancestry(root)
    return root


def _receipt_evidence(rt: Any, receipt: dict[str, Any]) -> list[str]:
    value = receipt.get("evidence")
    if not isinstance(value, list):
        return ["receipt evidence list is invalid"]
    reasons: list[str] = []
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            reasons.append("receipt has malformed evidence identity")
            continue
        try:
            path = rt._absolute_file(entry["path"], "receipt evidence")
            if _hash_file(rt, path, "receipt evidence") != entry["sha256"]:
                reasons.append(f"receipt evidence changed: {path}")
        except (rt.RuntimeErrorMessage, ObservationFailure, OSError, TypeError) as exc:
            reasons.append(f"receipt evidence is unavailable: {exc}")
    return reasons


def _reuse(rt: Any, args: Any, data: Path, prepared: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    try:
        path = rt._absolute_file(args.reuse, "reuse receipt")
        operations_root = _operation_root(rt, run)
        if path.name != "receipt.json" or not _inside(path, operations_root):
            return {"invoked": False, "reusable": False, "reasons": ["receipt is outside the retained operations directory"]}
        receipt, _ = _read_json(rt, path, "reuse receipt", _MAX_REQUEST_BYTES)
        if receipt.get("schema_version") != 1 or receipt.get("outcome") != "pass":
            reasons.append("receipt is not a schema 1 passing operation")
        if prepared["claim_kind"] in {"commit", "integrated", "hosted"}:
            if not any(item["kind"] == "git" and item["path"] == str(prepared["workspace"])
                       and item["head"] == prepared["actual_head"] for item in prepared["inputs"].values()):
                reasons.append("cached candidate claims require a matching workspace Git input")
        if receipt.get("reuse_key") != prepared["reuse_key"] or receipt.get("reuse_identity") != prepared["reuse_identity"]:
            reasons.append("receipt does not match the current consumer, claim, adapter, workspace, and named inputs")
        reasons.extend(_receipt_evidence(rt, receipt))
        # A reused result is historical evidence; it does not assert product acceptance.
        with rt._state_lock(data):
            _, run_id, current_run = rt._active_run(data, prepared["session"])
            if run_id != prepared["run_id"] or current_run.get("policy") != prepared["policy"]:
                reasons.append("selected run or policy changed during receipt comparison")
        return {"invoked": False, "reusable": not reasons, "reasons": reasons,
                "receipt": str(path), "outcome": "pass" if not reasons else None}
    except (rt.RuntimeErrorMessage, ObservationFailure, OSError, ValueError, TypeError) as exc:
        return {"invoked": False, "reusable": False, "reasons": [str(exc)[:1024]]}


def _operation_lock_names(rt: Any, run_id: str, grant_id: str, resources: list[str]) -> list[str]:
    prefix = rt._sha256(run_id.encode("utf-8"))[:16]
    grant_lock = f".operation-{prefix}-{rt._sha256(f'grant:{grant_id}'.encode('utf-8'))}.lock"
    resource_locks = [f".operation-resource-{rt._sha256(resource.encode('utf-8'))}.lock" for resource in resources]
    return sorted([grant_lock, *resource_locks])


def _grant_usage(rt: Any, run: dict[str, Any], grant_id: str, maximum: int,
                 allow_pending: bool = False) -> dict[str, Any]:
    usage = run.get("grant_usage", {})
    if not isinstance(usage, dict):
        _error(rt, "run has invalid grant usage records")
    current = usage.get(grant_id, {"invocations": 0, "failed": False, "pending_invocation": False})
    if (not isinstance(current, dict) or not _is_int(current.get("invocations", 0), 0)
            or not isinstance(current.get("failed", False), bool)
            or not isinstance(current.get("pending_invocation", False), bool)):
        _error(rt, "run has an invalid grant usage record")
    if current.get("failed", False):
        _error(rt, "operation grant has failed")
    if current.get("pending_invocation", False) and not allow_pending:
        _error(rt, "operation grant has an unresolved invocation")
    if current.get("invocations", 0) >= maximum:
        _error(rt, "operation grant invocation limit has been reached")
    return current


def _state_for_invocation(rt: Any, data: Path, prepared: dict[str, Any]) -> None:
    with rt._state_lock(data):
        state, run_id, run = rt._active_run(data, prepared["session"])
        rt._require_pinned_source(data, run)
        selected_policy(rt, run)
        if run_id != prepared["run_id"] or run.get("policy") != prepared["policy"]:
            _error(rt, "selected policy or run changed before invocation")
        current = _grant_usage(rt, run, prepared["grant_id"], prepared["grant"]["max_invocations"], allow_pending=True)
        if current.get("pending_invocation") is not True:
            _error(rt, "operation input inspection is not pending")
        count = current.get("invocations", 0)
        current = {"invocations": count + 1, "failed": False, "pending_invocation": True}
        run["grant_usage"][prepared["grant_id"]] = current
        rt._write_state(data, state)
        prepared["reserved_invocations"] = count + 1


def _undo_reservation(rt: Any, data: Path, prepared: dict[str, Any]) -> None:
    with rt._state_lock(data):
        state = rt._read_state(data / rt.STATE_NAME)
        run = state.get("runs", {}).get(prepared["run_id"])
        usage = run.get("grant_usage", {}) if isinstance(run, dict) else {}
        current = usage.get(prepared["grant_id"]) if isinstance(usage, dict) else None
        if isinstance(current, dict) and current.get("invocations") == prepared.get("reserved_invocations"):
            current["invocations"] -= 1
            current["pending_invocation"] = False
            rt._write_state(data, state)


def _record_failure(rt: Any, data: Path, prepared: dict[str, Any], invoked: bool = False) -> str | None:
    try:
        with rt._state_lock(data):
            state = rt._read_state(data / rt.STATE_NAME)
            run = state.get("runs", {}).get(prepared["run_id"])
            usage = run.setdefault("grant_usage", {}) if isinstance(run, dict) else None
            if not isinstance(usage, dict):
                return "run grant usage could not be updated"
            current = usage.setdefault(prepared["grant_id"], {"invocations": int(invoked), "failed": False})
            if not isinstance(current, dict):
                return "grant usage record is malformed"
            current["failed"] = True
            current["pending_invocation"] = False
            rt._write_state(data, state)
        return None
    except (rt.RuntimeErrorMessage, OSError) as exc:
        return str(exc)[:512]


def _record_success(rt: Any, data: Path, prepared: dict[str, Any]) -> str | None:
    try:
        with rt._state_lock(data):
            state = rt._read_state(data / rt.STATE_NAME)
            run = state.get("runs", {}).get(prepared["run_id"])
            usage = run.get("grant_usage", {}) if isinstance(run, dict) else {}
            current = usage.get(prepared["grant_id"]) if isinstance(usage, dict) else None
            if not isinstance(current, dict) or current.get("pending_invocation") is not True:
                return "grant invocation is not pending finalization"
            current["pending_invocation"] = False
            rt._write_state(data, state)
        return None
    except (rt.RuntimeErrorMessage, OSError) as exc:
        return str(exc)[:512]


def _adapter_result(rt: Any, path: Path, prepared: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value, _ = _read_json(rt, path, "adapter result", _MAX_REQUEST_BYTES)
    except (rt.RuntimeErrorMessage, ObservationFailure) as exc:
        return None, str(exc)
    allowed = {"schema_version", "consumer", "claim_kind", "procedure", "outcome", "evidence"}
    if set(value) != allowed or type(value.get("schema_version")) is not int or value.get("schema_version") != 1:
        return None, "adapter result has unknown or missing fields"
    for field in ("consumer", "claim_kind", "procedure"):
        if value.get(field) != prepared[field]:
            return None, f"adapter result {field} does not match the checked request"
    if value.get("outcome") not in ("pass", "fail"):
        return None, "adapter result outcome must be pass or fail"
    evidence = value.get("evidence")
    if not isinstance(evidence, list) or len(evidence) > _MAX_ITEMS:
        return None, "adapter result evidence must be a bounded file list"
    if value["outcome"] == "pass" and not evidence:
        return None, "passing adapter result must include at least one evidence file"
    checked: list[dict[str, str]] = []
    for item in evidence:
        try:
            evidence_path = rt._absolute_file(item, "adapter evidence")
            checked.append({"path": str(evidence_path), "sha256": _hash_file(rt, evidence_path, "adapter evidence")})
        except (rt.RuntimeErrorMessage, ObservationFailure, OSError, TypeError) as exc:
            return None, f"adapter evidence is invalid: {exc}"
    return {**value, "evidence": checked}, None


def _preflight_failed(rt: Any, data: Path, run: dict[str, Any], scope: dict[str, Any],
                      request_hash: str, observations: list[dict[str, Any]], error: ObservationFailure) -> dict[str, Any]:
    root = _operation_root(rt, run)
    evidence_dir = root / str(uuid.uuid4())
    evidence_dir.mkdir()
    rt._reject_link_ancestry(evidence_dir)
    checked = evidence_dir / "checked-request.json"
    stdout_path, stderr_path = evidence_dir / "stdout.log", evidence_dir / "stderr.log"
    _new_json(checked, {"schema_version": 1, "preflight_status": "failed",
                        "run_id": scope["run_id"], "session": scope["session"],
                        "policy": scope["pointer"], "grant": scope["grant_id"],
                        "request_sha256": request_hash, "partial_observations": observations,
                        "observation_error": str(error)[:1024]})
    stdout_path.touch(exist_ok=False)
    stderr_path.touch(exist_ok=False)
    receipt_path = evidence_dir / "receipt.json"
    receipt = {"schema_version": 1, "invoked": False, "outcome": "preflight_failed",
               "policy": scope["pointer"], "grant": scope["grant_id"],
               "request_sha256": request_hash, "partial_observations": observations,
               "observation_error": str(error)[:1024], "checked_request": str(checked),
               "stdout": str(stdout_path), "stderr": str(stderr_path), "evidence": []}
    usage_error = _record_failure(rt, data, scope, invoked=False)
    if usage_error:
        receipt["usage_error"] = usage_error
    _new_json(receipt_path, receipt)
    return {"invoked": False, "outcome": "preflight_failed", "receipt": str(receipt_path)}


def operation(rt: Any, args: Any, data: Path) -> dict[str, Any]:
    session = _text(rt, args.session, "session", 512)
    request_path = rt._absolute_file(args.request, "operation request")
    request, raw = _read_json(rt, request_path, "operation request", _MAX_REQUEST_BYTES)
    _, run_id, run = rt._active_run(data, session)
    rt._require_pinned_source(data, run)
    scope = _operation_scope(rt, request, session, run_id, run)
    lock_names = _operation_lock_names(rt, run_id, scope["grant_id"], scope["grant"]["resources"])

    with ExitStack() as locks:
        for lock_name in lock_names:
            locks.enter_context(rt._state_lock(data, lock_name))
        with rt._state_lock(data):
            state, current_id, current_run = rt._active_run(data, session)
            if current_id != run_id or current_run.get("policy") != scope["pointer"]:
                _error(rt, "selected policy or run changed before input inspection")
            selected_policy(rt, current_run)
            if not args.reuse:
                usage = _grant_usage(rt, current_run, scope["grant_id"], scope["grant"]["max_invocations"])
                current_run.setdefault("grant_usage", {})[scope["grant_id"]] = {**usage, "pending_invocation": True}
                rt._write_state(data, state)
        observations: list[dict[str, Any]] = []
        try:
            rt._require_pinned_source(data, current_run)
            prepared = _prepare_request(rt, request_path, request, raw, scope, current_run, observations)
            if args.reuse:
                return _reuse(rt, args, data, prepared, current_run)
        except ObservationFailure as exc:
            return _preflight_failed(rt, data, current_run, scope, rt._sha256(raw), observations, exc)
        except rt.RuntimeErrorMessage as exc:
            if not args.reuse:
                error = _record_success(rt, data, scope)
                if error:
                    _error(rt, f"{exc}; input-inspection reservation remains unresolved: {error}")
            raise

        operations_root = _operation_root(rt, current_run)
        evidence_dir = operations_root / str(uuid.uuid4())
        evidence_dir.mkdir()
        rt._reject_link_ancestry(evidence_dir)
        manifest_path = evidence_dir / "checked-request.json"
        result_path = evidence_dir / "adapter-result.json"
        stdout_path, stderr_path = evidence_dir / "stdout.log", evidence_dir / "stderr.log"
        manifest = {
            "schema_version": 1, "run_id": run_id, "session": session,
            "request_sha256": prepared["request_sha256"], "request_signature": prepared["signature"],
            "policy": prepared["policy"], "grant": prepared["grant_id"], "role": prepared["role"],
            "adapter": {"id": prepared["adapter_id"], "command": prepared["command"],
                        "sha256": prepared["command_hashes"], "claim_kinds": prepared["adapter"]["claim_kinds"]},
            "consumer": prepared["consumer"], "claim_kind": prepared["claim_kind"],
            "procedure": prepared["procedure"], "workspace": str(prepared["workspace"]),
            "candidate": {"owner": session, "expected_head": prepared["expected_head"],
                          "actual_head": prepared["actual_head"]},
            "inputs": prepared["inputs"], "dependencies": prepared["dependencies"],
            "scan": prepared["scan"], "resource_attribution": prepared["resource_attribution"],
        }
        _new_json(manifest_path, manifest)
        _state_for_invocation(rt, data, prepared)
        invoked = False
        process: subprocess.Popen[bytes] | None = None
        exit_code, launch_error = 0, None
        try:
            with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
                command = [*prepared["command"], "--request", str(manifest_path), "--result", str(result_path)]
                process = subprocess.Popen(command, cwd=prepared["workspace"], shell=False,
                                            stdout=stdout_stream, stderr=stderr_stream)
                invoked = True
                exit_code = process.wait()
        except OSError as exc:
            launch_error = str(exc)[:1024]
            if not invoked:
                _undo_reservation(rt, data, prepared)
                raise rt.RuntimeErrorMessage(f"approved adapter could not be started: {launch_error}") from exc
            exit_code = process.returncode if process is not None and process.returncode is not None else -1
        if not invoked:
            _undo_reservation(rt, data, prepared)
            _error(rt, "approved adapter was not invoked")

        parsed, parse_error = _adapter_result(rt, result_path, prepared) if result_path.is_file() else (None, "adapter result file was not created")
        reasons: list[str] = []
        if launch_error:
            reasons.append(f"adapter wait failed: {launch_error}")
        if exit_code != 0:
            reasons.append(f"adapter exited with status {exit_code}")
        if parse_error:
            reasons.append(parse_error)
        if parsed and parsed["outcome"] == "fail":
            reasons.append("adapter reported outcome fail")
        outcome = "pass" if not reasons and parsed is not None and parsed["outcome"] == "pass" else "fail"
        post = {"workspace": _post_head(rt, prepared["workspace"]),
                "inputs": _identity_now(rt, prepared),
                "dependencies": _dependency_now(rt, prepared["dependencies"])}
        evidence = parsed["evidence"] if parsed else []
        if post["workspace"].get("status") != "observed":
            reasons.append("workspace HEAD could not be observed after the adapter")
        for field in ("inputs", "dependencies"):
            for name, before in prepared[field].items():
                after = post[field].get(name)
                if after != before:
                    reasons.append(f"stable {field}.{name} changed or could not be observed: before {before}, after {after}")
        if reasons:
            outcome = "fail"
        result_head = post["workspace"].get("head")
        receipt_path = evidence_dir / "receipt.json"
        receipt = {
            "schema_version": 1, "invoked": True, "outcome": outcome,
            "request_signature": prepared["signature"], "reuse_key": prepared["reuse_key"],
            "reuse_identity": prepared["reuse_identity"], "policy": prepared["policy"],
            "grant": prepared["grant_id"], "role": prepared["role"], "adapter": manifest["adapter"],
            "consumer": prepared["consumer"], "claim_kind": prepared["claim_kind"],
            "procedure": prepared["procedure"], "workspace": manifest["workspace"],
            "expected_head": prepared["expected_head"], "actual_head_before": prepared["actual_head"],
            "actual_after": post, "inputs": prepared["inputs"], "dependencies": prepared["dependencies"],
            "git_range": {"registered_base": prepared["registered_base"], "before": prepared["actual_head"],
                          "result": result_head, "range": f"{prepared['registered_base']}..{result_head}" if result_head else None},
            "resource_attribution": prepared["resource_attribution"], "scan": prepared["scan"],
            "exit_code": exit_code, "adapter_outcome": parsed["outcome"] if parsed else None,
            "failure_reasons": reasons, "evidence": evidence,
            "checked_request": str(manifest_path), "adapter_result": str(result_path),
            "stdout": str(stdout_path), "stderr": str(stderr_path),
        }
        try:
            _new_json(receipt_path, receipt)
        except OSError as exc:
            return {"invoked": True, "outcome": "fail", "receipt": None, "exit_code": exit_code,
                    "adapter_result": str(result_path), "evidence_dir": str(evidence_dir),
                    "finalization_error": f"receipt could not be retained; invocation remains unresolved: {exc}"}
        usage_error = (_record_failure(rt, data, prepared, invoked=True) if outcome == "fail"
                       else _record_success(rt, data, prepared))
        if usage_error:
            return {"invoked": True, "outcome": "fail", "receipt": str(receipt_path),
                    "finalization_error": usage_error}
        return {"invoked": True, "outcome": outcome, "receipt": str(receipt_path)}
