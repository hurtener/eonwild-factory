"""Compile selected locked recipes without importing any experiment builder.

python tools/build_showcase.py --output out/showcase --render
A successful build is not production acceptance. Every final gate is preserved
in its package. Failed recipes are reported; they never become missing passes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

from eonwild_motion.factory.compiler import compile_recipe, verify_package


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--recipes", nargs="+", default=["run.v1", "run.v2", "sprint.v2", "reverse-walk.v1"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in args.recipes:
        if not name.replace("-", "").replace(".", "").isalnum():
            raise ValueError("recipe names must be simple catalog names")
        target = output / name
        try:
            manifest = compile_recipe(root / f"recipes/heavy-biped/{name}.json", root=root, output=target)
            integrity = verify_package(target)
            result = {"recipe": name, "generation": "PASS", "integrity": integrity, "files": manifest["files"]}
            if args.render:
                render = output / "previews" / name
                command = [args.blender, "-b", "-t", "2", "--python-exit-code", "1", "--python", str(root / "tools/render_candidate.py"),
                    "--", "--package", str(target), "--output", str(render), "--fbx"]
                if sys.platform.startswith("linux") and shutil.which("xvfb-run"):
                    command = ["xvfb-run", "-a", *command]
                process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
                (output / (name + ".render.log")).write_text(process.stdout)
                result["render"] = "PASS" if process.returncode == 0 else "FAIL"
                if process.returncode:
                    print(process.stdout[-4000:], flush=True)
        except Exception as exc:
            result = {"recipe": name, "generation": "FAIL", "error": str(exc)}
            (output / (name + ".error.log")).write_text(traceback.format_exc())
        results.append(result)
        print(json.dumps(result, indent=2), flush=True)
    (output / "showcase.json").write_text(json.dumps({"results": results, "production_approved": False}, indent=2) + "\n")
    return 1 if any(r["generation"] != "PASS" or r.get("render") == "FAIL" for r in results) else 0


if __name__ == "__main__": raise SystemExit(main())
