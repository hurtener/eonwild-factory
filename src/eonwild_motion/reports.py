from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
        "startedAt": started_at or now_utc(),
        "finishedAt": now_utc(),
    }
    write_json(path, report)
    return report
