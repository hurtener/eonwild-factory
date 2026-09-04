#!/usr/bin/env python3
"""Fail-closed integrity verifier for the approved V8.1 walk snapshot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    snapshot = Path(__file__).resolve().parents[1]
    package_root = snapshot.parents[1]
    factory_root = package_root.parent
    manifest = json.loads((snapshot / "APPROVAL_MANIFEST.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for entry in manifest["files"]:
        path = snapshot / entry["path"]
        actual = sha256(path) if path.is_file() else None
        if actual != entry["sha256"]:
            failures.append(f"snapshot:{entry['path']}: expected {entry['sha256']}, got {actual}")
    for entry in manifest["externalSourceChecks"]:
        path = factory_root / entry["path"]
        actual = sha256(path) if path.is_file() else None
        if actual != entry["sha256"]:
            failures.append(f"source:{entry['path']}: expected {entry['sha256']}, got {actual}")
    result = {
        "snapshotId": manifest["snapshotId"],
        "status": "PASS" if not failures else "FAIL",
        "checkedSnapshotFiles": len(manifest["files"]),
        "checkedExternalSources": len(manifest["externalSourceChecks"]),
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
