"""Run with python -m eonwild_motion.factory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

from ..errors import MotionError, ContractError
from ..glb.container import Glb
from .compiler import compile_recipe, verify_package
from .io import digest, read_json, write_json
from .source import admit_geometry


def admit(args) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise ContractError("admission output already exists; never overwrite calibrated geometry")
    source_bytes, rig_bytes = args.source.read_bytes(), args.rig.read_bytes()
    binding = read_json(args.rig)
    geometry, metadata = admit_geometry(Glb.from_bytes(source_bytes), binding["roles"],
        reference_clip=args.reference_clip, forward_axis=args.forward, up_axis=args.up)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".admission-", dir=output.parent))
    receipt = {"schema": "eonwild.motion.admission.v1", "status": "ADMITTED_GEOMETRY",
        "input": {"source_sha256": digest(source_bytes), "rig_sha256": digest(rig_bytes)},
        "files": {"geometry.glb": digest(geometry), "rig.json": digest(rig_bytes)},
        "geometry": metadata, "visual_approval": "PENDING", "biological_validation": False}
    try:
        (stage / "geometry.glb").write_bytes(geometry)
        (stage / "rig.json").write_bytes(rig_bytes)
        write_json(stage / "admission.json", receipt)
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V9 candidate factory (does not grant production approval)")
    sub = parser.add_subparsers(dest="command", required=True)
    admission = sub.add_parser("admit", help="calibrate immutable neutral geometry for new recipe inputs")
    admission.add_argument("--source", type=Path, required=True)
    admission.add_argument("--rig", type=Path, required=True)
    admission.add_argument("--forward", type=float, nargs=3)
    admission.add_argument("--up", type=float, nargs=3, default=[0, 1, 0])
    admission.add_argument("--reference-clip", help="optional declared pose source; never inherited choreography")
    admission.add_argument("--output", type=Path, required=True)
    compile_parser = sub.add_parser("compile", help="generate an immutable candidate; inspect acceptance with verify")
    compile_parser.add_argument("--recipe", type=Path, required=True)
    compile_parser.add_argument("--root", type=Path, default=Path.cwd())
    compile_parser.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify", help="check final hashes; exits 2 when technical acceptance is blocked")
    verify.add_argument("package", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "admit":
            result = admit(args)
        elif args.command == "compile":
            result = compile_recipe(args.recipe, root=args.root, output=args.output)
        else:
            result = verify_package(args.package)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 2 if args.command == "verify" and result["technical_status"] != "PASS" else 0
    except (MotionError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
