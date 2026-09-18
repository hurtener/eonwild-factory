"""Capture exact unavailable SourceMotionQuery calls during the public compile."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.source_motion_query import (
    SourceMotionQuery,
    SourceMotionUnavailable,
    _thaw,
)

ROOT = Path.cwd()
AUDIT = Path(__file__).resolve().parent
OUTPUT = AUDIT / "diagnostic-output-002"
original = SourceMotionQuery._evaluate_owned
records = []


def capture(self, time_s, **kwargs):
    result = original(self, time_s, **kwargs)
    if isinstance(result, SourceMotionUnavailable):
        record = {
            "time_s": float(result.time_s),
            "reason": result.reason,
            "arguments": _thaw(kwargs),
        }
        records.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
    return result


SourceMotionQuery._evaluate_owned = capture
status = "UNEXPECTED_PASS"
error = None
try:
    compile_motion_set(
        ROOT / "catalog/motion-sets/allosaurus-engineering-acquired-walk.v3.json",
        "walk",
        root=ROOT,
        output=OUTPUT,
        interpolation="CUBICSPLINE",
    )
except Exception as exc:
    status = "FAIL"
    error = {"type": type(exc).__name__, "message": str(exc)}
finally:
    SourceMotionQuery._evaluate_owned = original

receipt = {
    "status": status,
    "error": error,
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip(),
    "unavailable_calls": records,
    "classification": "diagnostic replay of the public compile; no package acceptance",
}
(AUDIT / "unavailable.json").write_text(
    json.dumps(receipt, indent=2, allow_nan=False) + "\n"
)
print(json.dumps({"status": status, "unavailable_count": len(records), "error": error}))
