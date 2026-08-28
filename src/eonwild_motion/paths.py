from __future__ import annotations

from pathlib import Path
import tempfile

from .errors import MotionError


def repository_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise MotionError(f"repository root not found from {start}")


def default_work_root() -> Path:
    return Path(tempfile.gettempdir()) / "eonwild-motion"


def ensure_external_work_root(root: Path, repository: Path) -> Path:
    resolved = root.expanduser().resolve()
    repo = repository.resolve()
    if resolved == repo or repo in resolved.parents:
        raise MotionError("work root must be outside the repository")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
