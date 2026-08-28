from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import uuid

from ..paths import ensure_external_work_root


@dataclass(frozen=True)
class RunContext:
    run_id: str
    repository: Path
    work_root: Path
    run_dir: Path


def create_run_context(repository: Path, work_root: Path, command: str) -> RunContext:
    root = ensure_external_work_root(work_root, repository)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{command}-{uuid.uuid4().hex[:10]}"
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return RunContext(run_id, repository, root, run_dir)


def git_source_state(repository: Path) -> dict[str, object]:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repository,
        text=True,
    )
    return {"gitHead": head, "dirty": bool(status.strip())}
