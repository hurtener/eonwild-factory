"""Strict, relocatable inputs and deterministic receipts for motion candidates."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def read_json(path: Path) -> Any:
    def reject(value: str) -> None:
        raise ContractError(f"non-finite JSON value: {value}")
    try:
        return json.loads(path.read_text(), parse_constant=reject)
    except (OSError, ValueError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc


def confined(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ContractError("input paths must be non-empty relative paths")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ContractError(f"input escapes source root: {name}")
    return path


_warned: set[str] = set()


def strict_hashes() -> bool:
    """Hash locks are informational by default so editing a catalog file does not force a
    version cascade through every recipe. EONWILD_STRICT_HASHES=1 restores hard failures."""
    return os.environ.get("EONWILD_STRICT_HASHES") == "1"


def locked_file(root: Path, binding: Mapping[str, Any]) -> Path:
    """Resolve {path[, sha256]}. A changed file is used as-is with a one-time note."""
    if not isinstance(binding, Mapping) or "path" not in binding or set(binding) - {"path", "sha256"}:
        raise ContractError("file bindings require a path (and optionally sha256)")
    path = confined(root, binding["path"])
    if not path.is_file():
        raise ContractError(f"missing input file: {binding['path']}")
    expected = binding.get("sha256")
    if expected is not None and digest(path.read_bytes()) != expected:
        if strict_hashes():
            raise ContractError(f"input hash mismatch: {binding['path']}")
        if binding["path"] not in _warned:
            _warned.add(binding["path"])
            print(f"note: {binding['path']} changed since it was bound; using the current file", file=sys.stderr)
    return path


def verified_file(root: Path, name: str, expected: str) -> Path:
    """Integrity check for a finished package (factory verify): always strict."""
    path = confined(root, name)
    if not path.is_file() or digest(path.read_bytes()) != expected:
        raise ContractError(f"package file hash mismatch or missing: {name}")
    return path


def replace_output(path: Path) -> Path:
    """Make room for a fresh output. The previous one is kept once as <name>.prev."""
    path = Path(path)
    if path.exists():
        previous = path.with_name(path.name + ".prev")
        if previous.is_dir():
            shutil.rmtree(previous)
        elif previous.exists():
            previous.unlink()
        path.rename(previous)
    return path


def bind(root: Path, path: Path) -> dict[str, str]:
    path = path.resolve()
    return {"path": path.relative_to(root.resolve()).as_posix(), "sha256": digest(path.read_bytes())}


def unit_axis(value: Any, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (3,) or not np.isfinite(array).all() or np.linalg.norm(array) < 1e-10:
        raise ContractError(f"{label} must be a finite nonzero 3-vector")
    return array / np.linalg.norm(array)


def frame_axes(forward: Any, up: Any) -> tuple[np.ndarray, np.ndarray]:
    f, u = unit_axis(forward, "forward"), unit_axis(up, "up")
    if abs(float(f @ u)) > 1e-6:
        raise ContractError("forward and up must be perpendicular")
    return f, u


def signed_heading_degrees(direction: Any, reference: Any, up: Any) -> float:
    """World-space signed heading, not unsigned quaternion angle to identity."""
    u = unit_axis(up, "up")
    d, r = np.asarray(direction, dtype=float), np.asarray(reference, dtype=float)
    d = unit_axis(d - u * (d @ u), "projected direction")
    r = unit_axis(r - u * (r @ u), "projected reference")
    return float(np.degrees(np.arctan2(u @ np.cross(r, d), np.clip(r @ d, -1, 1))))
