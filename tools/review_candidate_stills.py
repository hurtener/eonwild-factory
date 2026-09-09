"""Render a few exact native-time poses from one immutable candidate package.

This is a rapid visual diagnostic. It deliberately emits no movie, FBX, or
full-cycle review claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

from eonwild_motion.factory.compiler import verify_package

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_timing import native_still_times


VIEWS = ("side", "three-quarter", "front", "rear")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blender_command(*, blender: str, root: Path, package: Path, output: Path,
                    view: str, mode: str, times: list[float], width: int,
                    samples: int, camera_lock: Path | None = None) -> list[str]:
    command = [blender, "-b", "-t", "2", "--python-exit-code", "1", "--python",
        str(root / "tools/render_candidate.py"), "--", "--package", str(package),
        "--output", str(output), "--view", view, "--mode", mode,
        "--width", str(width), "--samples", str(samples), "--still-times",
        *[repr(value) for value in times]]
    if camera_lock is not None:
        command.extend(["--camera-lock", str(camera_lock)])
    return command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--times", type=float, nargs="+", required=True)
    parser.add_argument("--views", choices=VIEWS, nargs="+", default=["side", "three-quarter"])
    parser.add_argument("--mode", choices=("root_motion", "in_place"), default="root_motion")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--camera-lock-dir", type=Path,
                        help="create or reuse one immutable camera lock per view")
    args = parser.parse_args(argv)
    if len(set(args.views)) != len(args.views) or not 320 <= args.width <= 3840 or not 1 <= args.samples <= 256:
        parser.error("still views, resolution, or samples are invalid")
    root = Path(__file__).resolve().parents[1]
    package = args.package.resolve()
    output = args.output.resolve()
    camera_lock_dir = args.camera_lock_dir.resolve() if args.camera_lock_dir is not None else None
    before = verify_package(package)
    runtime = json.loads((package / "runtime.json").read_text())
    times = native_still_times(runtime["duration_s"], args.times)
    package_manifest_sha = sha(package / "manifest.json")
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "eonwild.motion.still-review.v1",
        "candidate_manifest_sha256": package_manifest_sha,
        "candidate_status": before, "requested_native_times_s": times,
        "mode": args.mode, "views": {},
        "diagnostic_scope": "requested native-time stills only; no encoded film or full-cycle review claim",
        "visual_review": "PENDING", "unity_parity": "NOT_RUN", "production_approved": False}
    try:
        for view in args.views:
            target = output / view
            camera_lock = camera_lock_dir / f"{view}.json" if camera_lock_dir is not None else None
            command = blender_command(blender=args.blender, root=root, package=package,
                output=target, view=view, mode=args.mode, times=times,
                width=args.width, samples=args.samples, camera_lock=camera_lock)
            process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=600)
            log = output / f"{view}.render.log"
            log.write_text(process.stdout)
            if process.returncode:
                raise RuntimeError(f"{view} still render failed; see {log}")
            receipt_path = target / "render-receipt.json"
            receipt = json.loads(receipt_path.read_text())
            if (receipt.get("schema") != "eonwild.motion.review-stills.v1"
                or receipt.get("requested_native_times_s") != times):
                raise ValueError(f"{view} renderer did not preserve requested native seconds")
            result["views"][view] = {"status": "PASS", "receipt": str(receipt_path),
                "receipt_sha256": sha(receipt_path), "stills": receipt["stills"],
                "log": str(log),
                "camera_lock": (None if camera_lock is None else
                    {"path": str(camera_lock), "sha256": sha(camera_lock)})}
        result["candidate_status"] = verify_package(package)
        if sha(package / "manifest.json") != package_manifest_sha:
            raise ValueError("candidate manifest changed during still review")
    except Exception as exc:
        result["error"] = str(exc)
        (output / "error.log").write_text(traceback.format_exc())
    render_ok = "error" not in result and all(
        result["views"].get(view, {}).get("status") == "PASS" for view in args.views)
    result["render_status"] = "PASS" if render_ok else "FAIL"
    result["exit_code"] = 1 if not render_ok else (
        0 if result["candidate_status"]["technical_status"] == "PASS" else 2)
    (output / "still-review.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("STILL_REVIEW " + json.dumps({k: v for k, v in result.items() if k != "views"}, allow_nan=False))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
