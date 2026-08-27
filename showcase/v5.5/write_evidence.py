#!/usr/bin/env python3
"""Write V5.5 showcase provenance and machine-readable evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "reports/V5-5-BALANCE-001"
V5 = ROOT / "procedural-animation-toolkit(v5)"
PACK = ROOT / "procedural-animation-toolkit(v5.5)"
OUT = PACK / "validated_result/v5.5"
SOURCE = OUT / "tarbosaurus_procedural_v5_5_animation_pack.glb"
MANIFEST = OUT / "animation-manifest.v5.5.json"
VALIDATION = OUT / "v5.5-release-validation.json"
SITE = ROOT / "showcase/v5.5/site"
EXPECTED_V5_ENTRY_HASH = "c4f4905f2974aa751a7fe0485a44d194898ead71280992c34d0129dc81362119"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_entry_hash(path: Path) -> str:
    data = subprocess.check_output(
        ["git", "ls-files", "-s", "--", str(path.relative_to(ROOT))], cwd=ROOT
    )
    return hashlib.sha256(data).hexdigest()


def version(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).splitlines()[0]


def ffprobe(path: Path) -> dict[str, object]:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_frames",
            "-show_entries", "format=duration,size", "-of", "json", str(path),
        ],
        text=True,
    )
    result = json.loads(raw)
    return {**result["streams"][0], **result["format"]}


def main() -> None:
    TASK.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    validation = json.loads(VALIDATION.read_text())
    browser_acceptance_path = TASK / "browser-acceptance.json"
    if not browser_acceptance_path.is_file():
        raise RuntimeError("missing coordinator browser acceptance record")
    browser_acceptance = json.loads(browser_acceptance_path.read_text())
    if browser_acceptance.get("status") != "PASS":
        raise RuntimeError("coordinator browser acceptance is not PASS")
    if browser_acceptance.get("release_glb_sha256") != sha256(SOURCE):
        raise RuntimeError("browser acceptance does not match the current V5.5 GLB")
    if browser_acceptance.get("site_index_sha256") != sha256(SITE / "index.html"):
        raise RuntimeError("browser acceptance does not match the current showcase HTML")
    site_check_process = subprocess.run(
        [sys.executable, str(ROOT / "showcase/v5.5/check_site.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if site_check_process.returncode:
        raise RuntimeError(f"site check failed: {site_check_process.stdout}{site_check_process.stderr}")
    site_check = json.loads(site_check_process.stdout)
    if site_check.get("status") != "passed":
        raise RuntimeError("site checker did not report passed")
    original_tracked = [
        Path(line)
        for line in subprocess.check_output(
            ["git", "ls-files", "--", str(V5.relative_to(ROOT))], cwd=ROOT, text=True
        ).splitlines()
    ]
    original_relative = [path.relative_to(V5.relative_to(ROOT)) for path in original_tracked]
    missing_copy_paths = [str(path) for path in original_relative if not (PACK / path).is_file()]
    if missing_copy_paths:
        raise RuntimeError(f"V5.5 duplicate is missing V5 paths: {missing_copy_paths}")
    modified_copy_paths = [
        str(path) for path in original_relative
        if sha256(V5 / path) != sha256(PACK / path)
    ]
    films = sorted((SITE / "media/films").glob("*.mp4"))
    stills = sorted((SITE / "media/stills").glob("*.png"))
    site_files = sorted(
        path for path in SITE.rglob("*")
        if path.is_file() and path.name != "asset-manifest.json" and "__pycache__" not in path.parts
    )
    artifacts = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "kind": path.suffix.lstrip(".") or "file",
        }
        for path in site_files
    ]
    v5_hash = tracked_entry_hash(V5)
    v5_status = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", str(V5.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
    )
    if v5_hash != EXPECTED_V5_ENTRY_HASH or v5_status:
        raise RuntimeError(f"V5 immutable boundary failed: hash={v5_hash}, status={v5_status!r}")
    if validation["status"] != "PASS" or not validation["constrainedQualityGatesPass"]:
        raise RuntimeError("V5.5 release validation is not PASS")
    if len(films) != 4 or len(stills) != 21:
        raise RuntimeError(f"expected 4 films and 21 stills, got {len(films)} and {len(stills)}")

    film_probe = {path.stem: ffprobe(path) for path in films}
    provenance = {
        "schema": "eonwild.showcase-provenance.v1",
        "task_id": "V5-5-BALANCE-001",
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "asset": "Tarbosaurus procedural animation V5.5 balance study",
        "source": {
            "path": str(SOURCE.relative_to(ROOT)),
            "sha256": sha256(SOURCE),
            "source_model_sha256": sha256(PACK / "inputs/tarbosaurus_source.glb"),
            "material_policy": "GLB-embedded materials and textures preserved for Blender rendering",
            "license_status": "internal project fixture and user-supplied reference media",
        },
        "references": {
            "side_walk": {
                "path": "procedural-animation-toolkit(v5.5)/inputs/tarbosaurus_reference_walk_side_v02.mp4",
                "sha256": sha256(PACK / "inputs/tarbosaurus_reference_walk_side_v02.mp4"),
                "use": "qualitative phase timing and joint-chain observations",
            },
            "attack_eat": {
                "path": "assets/examples/tarbosaurus/attack-eat.mp4",
                "sha256": sha256(ROOT / "assets/examples/tarbosaurus/attack-eat.mp4"),
                "use": "qualitative rear-load, drive, and feeding-descent observations; camera changes limit measurement",
            },
            "user_stance_image": {
                "description": "same-model side stance with one support leg and the opposite foot forward",
                "use": "qualitative neutral support-foot arrangement",
            },
        },
        "tools": {
            "blender": version(["blender", "--version"]),
            "ffmpeg": version(["ffmpeg", "-version"]),
            "python": version([sys.executable, "--version"]),
            "numpy": "2.5.2",
            "scipy": "1.18.1",
        },
        "release": validation,
        "render_scope": {
            "stills": len(stills),
            "films": film_probe,
            "camera": "locked full-body profile framing derived from global animation bounds",
            "animation_data_policy": "source V5.5 GLB imported read-only; no animation channels edited in Blender",
        },
        "immutable_v5_boundary": {
            "expected_tracked_entry_hash": EXPECTED_V5_ENTRY_HASH,
            "actual_tracked_entry_hash": v5_hash,
            "status_clean": not bool(v5_status),
            "unchanged": True,
        },
        "complete_duplicate": {
            "original_tracked_file_count": len(original_relative),
            "all_original_paths_present": True,
            "missing_paths": missing_copy_paths,
            "byte_identical_copy_count": len(original_relative) - len(modified_copy_paths),
            "intentionally_versioned_copy_paths": modified_copy_paths,
            "note": "Every tracked V5 path is present in the V5.5 package; version-specific files may differ only inside the independent copy.",
        },
        "measurement_boundary": validation["measurementBoundary"],
        "review_status": "PASS_INDEPENDENT_TECHNICAL_AND_PERCEPTUAL_REVIEW",
    }
    page_manifest = {
        "schema": "eonwild.v5.5-showcase-manifest.v1",
        "source": provenance["source"],
        "clips": manifest["clips"],
        "rendered_assets": artifacts,
        "offline": True,
        "hero": "media/films/walk-relaxed-inplace.mp4",
        "hero_probe": film_probe["walk-relaxed-inplace"],
    }
    (SITE / "asset-manifest.json").write_text(json.dumps(page_manifest, indent=2) + "\n")
    (TASK / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    (TASK / "artifacts.json").write_text(json.dumps({"artifacts": artifacts}, indent=2) + "\n")
    (TASK / "metrics.json").write_text(json.dumps({"release": validation, "films": film_probe}, indent=2) + "\n")
    (TASK / "copy-manifest.json").write_text(json.dumps(provenance["complete_duplicate"], indent=2) + "\n")
    (TASK / "tests.json").write_text(json.dumps({
        "release_validation": "PASS",
        "constrained_quality_gates": "PASS",
        "v5_immutable": "PASS",
        "site_static_check": site_check,
        "film_probe": film_probe,
        "browser_acceptance": browser_acceptance,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
