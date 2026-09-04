#!/usr/bin/env python3
"""Materialize the reviewed Candidate-A official-basis chest solve.

This wrapper reuses the independently reviewed solve equations without
modifying the frozen iteration-b input.  It changes only Bone_002 and the
five neck links plus head rotation accessors in the two approved walk clips.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SOLVER = ROOT / "reports/V8-2-BALANCE-TRANSFER/evaluation/chest-solver/solve_chest_balance.py"


def load_solver():
    spec = importlib.util.spec_from_file_location("reviewed_chest_solver", SOLVER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load reviewed solver: {SOLVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["reviewed_chest_solver"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--gain", default=0.3984375, type=float)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    solver = load_solver()
    if not args.input.is_file():
        raise RuntimeError(f"missing iteration-b input: {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    local_deltas = solver.write_variant(args.input, args.output, args.gain)
    report = {
        "schema": "eonwild.v8_2.apply_official_chest_solver.v1",
        "status": "PASS",
        "input": str(args.input),
        "inputSha256": solver.ev.sha256(args.input),
        "output": str(args.output),
        "outputSha256": solver.ev.sha256(args.output),
        "gain": args.gain,
        "method": "reviewed direct Log(R_chest @ inverse(R_pelvis)) Z increment with deterministic neck world cancellation",
        "changedChannels": [solver.CHEST, *solver.NECK_HEAD],
        "walkClips": list(solver.CLIPS),
        "maxLocalDeltaDegreesFromIterationB": local_deltas,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
