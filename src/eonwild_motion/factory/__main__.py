"""Run with python -m eonwild_motion.factory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ..errors import MotionError
from .compiler import compile_recipe, verify_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V9 candidate factory (does not grant production approval)")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile", help="generate an immutable candidate, even when review is blocked")
    compile_parser.add_argument("--recipe", type=Path, required=True)
    compile_parser.add_argument("--root", type=Path, default=Path.cwd())
    compile_parser.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify", help="check final artifact hashes; exits 2 when technical acceptance is blocked")
    verify.add_argument("package", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "compile":
            result = compile_recipe(args.recipe, root=args.root, output=args.output)
        else:
            result = verify_package(args.package)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if args.command == "compile" or result["technical_status"] == "PASS" else 2
    except (MotionError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
