"""Strict, fail-closed contract helpers for grounded gait transitions."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..errors import ContractError


class GaitTransitionFailure(ContractError):
    pass


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    except (TypeError, ValueError) as exc:
        raise GaitTransitionFailure("document is not canonical finite JSON") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regular_no_follow(repository: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise GaitTransitionFailure(f"unsafe bound path: {relative}")
    repository = repository.resolve(strict=True)
    current = repository
    for part in Path(relative).parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as exc:
            raise GaitTransitionFailure(f"bound path missing: {relative}") from exc
        if stat.S_ISLNK(mode):
            raise GaitTransitionFailure(f"symlink forbidden in bound path: {relative}")
    if not stat.S_ISREG(current.lstat().st_mode):
        raise GaitTransitionFailure(f"bound path is not a regular file: {relative}")
    if current.resolve(strict=True).parent != (repository / Path(relative).parent).resolve(strict=True):
        raise GaitTransitionFailure(f"bound path escapes repository: {relative}")
    return current


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GaitTransitionFailure(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise GaitTransitionFailure(f"JSON root must be object: {path}")
    return value


def validate_document(document: Mapping[str, Any], schema: Mapping[str, Any], *, label: str) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.path))
    if errors:
        where = "/".join(str(item) for item in errors[0].path)
        raise GaitTransitionFailure(f"{label} schema failure at {where}: {errors[0].message}")


def load_and_validate(repository: Path, document_path: str, schema_path: str) -> dict[str, Any]:
    document = load_json(regular_no_follow(repository, document_path))
    schema = load_json(regular_no_follow(repository, schema_path))
    validate_document(document, schema, label=document_path)
    return document


def verify_binding(repository: Path, binding: Mapping[str, Any], *, expected_binding_sha256: str) -> dict[str, Any]:
    required = {"schema", "id", "version", "taskId", "inputs", "outputs", "claims"}
    if set(binding) != required or binding.get("schema") != "eonwild.motion.v9.gait-transition-execution-binding.v1":
        raise GaitTransitionFailure("execution binding shape or schema changed")
    if binding.get("taskId") != "V9-WALK-START-VERTICAL-006" or binding.get("version") != 1:
        raise GaitTransitionFailure("execution binding task/version changed")
    actual_binding_sha256 = sha256_bytes(canonical_bytes(binding))
    if actual_binding_sha256 != expected_binding_sha256:
        raise GaitTransitionFailure("execution binding closure digest mismatch")
    if not binding.get("inputs"):
        raise GaitTransitionFailure("execution binding closure is empty")
    seen_paths: set[str] = set()
    seen_roles: set[str] = set()
    closure = []
    for item in binding.get("inputs", []):
        if not isinstance(item, dict) or set(item) != {"role", "path", "sha256"}:
            raise GaitTransitionFailure("binding input shape changed")
        role, relative, expected = item["role"], item["path"], item["sha256"]
        if role in seen_roles or relative in seen_paths:
            raise GaitTransitionFailure("duplicate binding role or path")
        seen_roles.add(role); seen_paths.add(relative)
        path = regular_no_follow(repository, relative)
        before = os.stat(path, follow_symlinks=False)
        actual = sha256_file(path)
        after = os.stat(path, follow_symlinks=False)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise GaitTransitionFailure(f"bound input mutated while captured: {relative}")
        if actual != expected:
            raise GaitTransitionFailure(f"bound input hash mismatch: {relative}")
        closure.append({"role": role, "path": relative, "sha256": actual, "byteSize": before.st_size})
    return {"status": "pass", "bindingSha256": actual_binding_sha256, "inputCount": len(closure), "closure": closure}
