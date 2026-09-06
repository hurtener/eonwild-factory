"""Compile recipes and render serialized motion; fail on blocked acceptance.

python tools/build_showcase.py --output out/showcase --render
A successful render is diagnostic evidence, never mechanical/visual approval.
Use one recipe and --reference-package for camera-locked V9 comparisons. The
reference is read-only presentation input and never enters the motion compiler.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback
from typing import Any

from eonwild_motion.factory.compiler import compile_recipe, verify_package

VIEWS = ("side", "front", "rear", "three-quarter")
DEFAULT_RECIPES = ("walk.v2", "reverse-walk.v3", "run.v3", "sprint.v3")


def exit_status(results: list[dict[str, Any]], *, required_views: tuple[str, ...] = ()) -> int:
    """1 = generation/render/integrity failure; 2 = mechanical rejection.

    Missing evidence fails closed. Zero does not confer visual or Unity approval.
    """
    if not results:
        return 1
    for row in results:
        if not isinstance(row, dict) or row.get("generation") != "PASS":
            return 1
        integrity = row.get("integrity")
        if not isinstance(integrity, dict) or integrity.get("integrity") != "PASS":
            return 1
        renders = row.get("renders", {})
        if required_views and (not isinstance(renders, dict) or any(
                not isinstance(renders.get(view), dict) or renders[view].get("status") != "PASS"
                for view in required_views)):
            return 1
        references = row.get("reference_renders")
        if references is not None and (not isinstance(references, dict) or any(
                not isinstance(references.get(view), dict) or references[view].get("status") != "PASS"
                for view in required_views)):
            return 1
    if any(row["integrity"].get("technical_status") != "PASS" for row in results):
        return 2
    return 0


def render_view(package: Path, output: Path, *, root: Path, blender: str,
                view: str, mode: str, fps: int, fbx: bool, camera_lock: Path | None = None) -> dict:
    command = [blender, "-b", "-t", "2", "--python-exit-code", "1", "--python",
               str(root / "tools/render_candidate.py"), "--", "--package", str(package),
               "--output", str(output), "--view", view, "--mode", mode, "--fps", str(fps)]
    if fbx:
        command.append("--fbx")
    if camera_lock is not None:
        command.extend(["--camera-lock", str(camera_lock)])
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, timeout=1800)
        log, returncode = process.stdout, process.returncode
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout or b""
        log = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
        log += "\nRENDER_TIMEOUT: no preview acceptance granted\n"
        returncode = -1
    log_path = output.with_suffix(".render.log")
    log_path.write_text(log)
    result = {"status": "PASS" if returncode == 0 else "FAIL", "exit_code": returncode,
              "log": str(log_path), "mode": mode, "view": view}
    if returncode:
        print(log[-5000:], flush=True)
    else:
        receipt = json.loads((output / "render-receipt.json").read_text())
        result["receipt"] = receipt
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--recipes", nargs="+", default=list(DEFAULT_RECIPES))
    parser.add_argument("--views", nargs="+", choices=VIEWS, default=list(VIEWS))
    parser.add_argument("--mode", choices=("root_motion", "in_place"), default="root_motion")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--reference-package", type=Path,
                        help="read-only prepared reference; requires one recipe, --render and root_motion mode")
    args = parser.parse_args(argv)
    if len(set(args.recipes)) != len(args.recipes) or any(
            re.fullmatch(r"[a-z][a-z0-9-]*\.v[1-9][0-9]*", name) is None for name in args.recipes):
        parser.error("recipe names must be unique versioned catalog names")
    if len(set(args.views)) != len(args.views) or not 12 <= args.fps <= 120:
        parser.error("views must be unique and fps must be between 12 and 120")
    if args.reference_package is not None and (
            len(args.recipes) != 1 or not args.render or args.mode != "root_motion"):
        parser.error("reference comparisons require exactly one recipe, --render and --mode root_motion")
    root = Path(__file__).resolve().parents[1]
    reference = args.reference_package.resolve() if args.reference_package is not None else None
    if reference is not None:
        manifest = json.loads((reference / "manifest.json").read_text())
        if manifest.get("schema") != "eonwild.motion.reference-review-package.v1":
            parser.error("reference must be an explicitly prepared immutable historical comparison")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in args.recipes:
        target = output / name
        try:
            manifest = compile_recipe(root / f"recipes/heavy-biped/{name}.json", root=root, output=target)
            integrity = verify_package(target)
            validation = json.loads((target / "validation.json").read_text())
            print("FINAL_VALIDATION " + name + " " + json.dumps(validation, allow_nan=False), flush=True)
            result = {"recipe": name, "generation": "PASS", "integrity": integrity, "files": manifest["files"]}
            # Render mechanically blocked candidates for diagnosis, but preserve
            # that rejection in the final nonzero exit status.
            if args.render:
                result["renders"] = {}
                if reference is not None:
                    result["reference_renders"] = {}
                for index, view in enumerate(args.views):
                    camera = output / "cameras" / f"{view}.json" if reference is not None else None
                    if reference is not None:
                        result["reference_renders"][view] = render_view(reference, output / "references" / view,
                            root=root, blender=args.blender, view=view, mode=args.mode, fps=args.fps,
                            fbx=False, camera_lock=camera)
                        if result["reference_renders"][view]["status"] != "PASS":
                            result["renders"][view] = {"status": "NOT_RUN", "reason": "reference view failed"}
                            continue
                    result["renders"][view] = render_view(target, output / "previews" / name / view,
                        root=root, blender=args.blender, view=view, mode=args.mode, fps=args.fps,
                        fbx=index == 0, camera_lock=camera)
                # Rendering is read-only. Catch accidental post-validation
                # edits rather than relying on the pre-render integrity receipt.
                result["integrity"] = verify_package(target)
        except Exception as exc:
            result = {"recipe": name, "generation": "FAIL", "error": str(exc)}
            (output / (name + ".error.log")).write_text(traceback.format_exc())
        results.append(result)
        print(json.dumps(result, indent=2, allow_nan=False), flush=True)
    code = exit_status(results, required_views=tuple(args.views) if args.render else ())
    summary = {"schema": "eonwild.motion.showcase.v2", "results": results, "exit_code": code,
               "visual_review": "PENDING", "unity_validation": "NOT_RUN", "production_approved": False}
    (output / "showcase.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
