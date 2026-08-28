from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import platform

from . import __version__
from .contracts.load import validate_document
from .hashing import write_json


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit_report(
    path: Path,
    *,
    command: str,
    status: str,
    run_id: str,
    inputs: list[dict[str, Any]] | None = None,
    outputs: list[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
    checks: dict[str, bool] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    source: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
    tool_versions: dict[str, Any] | None = None,
    repository: Path | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    report = {
        "schema": "eonwild.motion.run-report.v1",
        "runId": run_id,
        "command": command,
        "status": status,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "metrics": metrics or {},
        "checks": checks or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "source": source or {},
        "profile": profile or {
            "id": None,
            "sha256": None,
            "lockSha256": None,
        },
        "toolVersions": tool_versions or {
            "engine": __version__,
            "python": platform.python_version(),
            "blender": None,
            "gltfValidator": None,
        },
        "startedAt": started_at or now_utc(),
        "finishedAt": now_utc(),
    }
    if repository is not None:
        validate_document(report, repository=repository, label="run report")
    write_json(path, report)
    return report
