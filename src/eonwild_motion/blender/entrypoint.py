#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True

SOURCE_ROOT = Path(__file__).resolve().parents[2]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "render"])
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    )
    if args.command == "build":
        from eonwild_motion.pipeline.build import execute_build_request

        execute_build_request(args.request)
    else:
        from eonwild_motion.blender.render import execute_render_request

        execute_render_request(args.request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
