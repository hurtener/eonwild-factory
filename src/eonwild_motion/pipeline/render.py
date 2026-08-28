from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from ..errors import MotionError


def invoke_blender_render(
    *, repository: Path, request_path: Path, log_path: Path
) -> dict:
    entrypoint = repository / "src/eonwild_motion/blender/entrypoint.py"
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [
            "blender",
            "--background",
            "--python-exit-code",
            "1",
            "--python",
            str(entrypoint),
            "--",
            "render",
            "--request",
            str(request_path),
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
    )
    log_path.write_text(process.stdout + process.stderr)
    if process.returncode != 0:
        raise MotionError(
            f"Blender render failed with exit {process.returncode}; see {log_path}"
        )
    request = json.loads(request_path.read_text())
    report_path = Path(request["stageReportPath"])
    if not report_path.is_file():
        raise MotionError("Blender render did not emit its stage report")
    report = json.loads(report_path.read_text())
    if report.get("status") != "PASS":
        raise MotionError("Blender render stage did not pass")
    return report
