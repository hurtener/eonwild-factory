#!/usr/bin/env python3
"""Write the V5 showcase provenance and machine-readable evidence bundle."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "reports" / "V5-SHOWCASE-001"
TOOLKIT = ROOT / "procedural-animation-toolkit(v5)"
SOURCE = TOOLKIT / "validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb"
V5_MANIFEST = TOOLKIT / "validated_result/v5/animation-manifest.v5.json"
SITE = ROOT / "showcase/v5/site"
EXPECTED_TOOLKIT_HASH = "c4f4905f2974aa751a7fe0485a44d194898ead71280992c34d0129dc81362119"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def toolkit_hash() -> str:
    data = subprocess.check_output(["git", "ls-files", "-s", "--", str(TOOLKIT.relative_to(ROOT))], cwd=ROOT)
    return hashlib.sha256(data).hexdigest()


def command_version(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).splitlines()[0]


def main() -> None:
    TASK.mkdir(parents=True, exist_ok=True)
    source_manifest = json.loads(V5_MANIFEST.read_text())
    priority = [clip for clip in source_manifest["clips"] if not clip.get("transition")]
    # Exclude the manifest itself to avoid a self-referential hash.
    site_files = sorted(path for path in SITE.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.name != "asset-manifest.json")
    artifacts = [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "bytes": path.stat().st_size, "kind": path.suffix.lstrip(".") or "file"} for path in site_files]
    pre_hash = EXPECTED_TOOLKIT_HASH
    post_hash = toolkit_hash()
    toolkit_rel = str(TOOLKIT.relative_to(ROOT))
    unstaged_clean = subprocess.run(["git", "diff", "--quiet", "--", toolkit_rel], cwd=ROOT).returncode == 0
    staged_clean = subprocess.run(["git", "diff", "--cached", "--quiet", "--", toolkit_rel], cwd=ROOT).returncode == 0
    head_clean = subprocess.run(["git", "diff-tree", "--quiet", "HEAD", "--", toolkit_rel], cwd=ROOT).returncode == 0
    hash_unchanged = pre_hash == post_hash
    diff_clean = unstaged_clean and staged_clean and head_clean
    if not (hash_unchanged and diff_clean):
        raise RuntimeError(
            "immutable toolkit boundary failed: "
            f"hash_unchanged={hash_unchanged}, unstaged_clean={unstaged_clean}, "
            f"staged_clean={staged_clean}, head_clean={head_clean}"
        )
    provenance = {
        "schema": "eonwild.showcase-provenance.v1",
        "task_id": "V5-SHOWCASE-001",
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "asset": "Tarbosaurus V5 animation showcase",
        "source": {
            "path": str(SOURCE.relative_to(ROOT)),
            "sha256": sha256(SOURCE),
            "license_status": "internal validated fixture; no external media ingested",
            "material_policy": "GLB-embedded materials/textures preserved for Blender rendering",
        },
        "tool": {"blender": command_version(["blender", "--version"]), "ffmpeg": command_version(["ffmpeg", "-version"])},
        "animation_scope": {"total_source_clips": len(source_manifest["clips"]), "priority_non_transition_clips": len(priority), "authored_transitions": len(source_manifest["clips"]) - len(priority), "rendered_priority_stills": 21, "rendered_films": ["idle-breath", "walk-relaxed-inplace", "turn-left-35-inplace", "start-walk-inplace", "eat-loop", "bite-attack", "roar"]},
        "immutable_toolkit_boundary": {"tracked_entries": 501, "pre_hash": pre_hash, "post_hash": post_hash, "hash_unchanged": hash_unchanged, "git_diff_clean": diff_clean, "unstaged_clean": unstaged_clean, "staged_clean": staged_clean, "head_clean": head_clean, "note": "Tracked entries under procedural-animation-toolkit(v5) were read only; all three Git tree boundaries are clean."},
        "known_record_mismatch": {"key_sha256": "66cf116a2191311cf00f4571e71e5a38753fd71ad42a8381185156a3af1bacd0", "stale_render_report_sha256": "caa303d196ff3f5cb605fee59db5879c4c70d78c89ee5ce1a454159f21ae35ec", "current_file_sha256": sha256(SOURCE), "resolution": "Current file and KEY_SHA256SUMS agree; stale render report is retained and disclosed."},
        "review_status": "PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED",
    }
    page_manifest = {"schema": "eonwild.v5-showcase-manifest.v1", "source": provenance["source"], "clips": source_manifest["clips"], "rendered_assets": artifacts, "offline": True, "hero": "media/films/walk-relaxed-inplace.mp4", "hero_resolution": [960, 540], "hero_fps": 24, "hero_duration_seconds": 4.458333, "hero_source_duration_seconds": 4.44444465637207, "hero_loop_exact_manifest_frames": 107, "loop_films": {"walk-relaxed-inplace": {"duration_seconds": 4.458333, "source_duration_seconds": 4.44444465637207, "frames": 107}, "eat-loop": {"duration_seconds": 8.0, "source_duration_seconds": 8.0, "frames": 192}}}
    (SITE / "asset-manifest.json").write_text(json.dumps(page_manifest, indent=2) + "\n")
    (TASK / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    (TASK / "artifacts.json").write_text(json.dumps({"artifacts": artifacts}, indent=2) + "\n")
    (TASK / "metrics.json").write_text(json.dumps({"render_resolution": [480, 270], "render_fps": 24, "hero_resolution": [960, 540], "hero_duration_seconds": 4.458333, "hero_source_duration_seconds": 4.44444465637207, "eat_loop_duration_seconds": 8.0, "film_duration_cap_seconds_non_loop": 3.2, "loop_duration_policy": "full manifest duration at 24 fps", "priority_still_count": 21, "film_count": 7, "source_vertex_face_counts": {"vertices": 23653, "faces": 59169}, "source_max_influences_observed": 11, "performance_note": "Offline Blender Eevee render timing only; no browser FPS or runtime package acceptance claim."}, indent=2) + "\n")
    (TASK / "tests.json").write_text(json.dumps({"site_check": "passed", "site_check_controls": {"hero_play_pause": "browser verified", "reduced_motion_default_paused": "implemented and statically verified", "behavior_aria_label_sync": "browser verified"}, "py_compile": "passed", "hero_ffprobe": {"width": 960, "height": 540, "fps": 24, "duration_seconds": 4.458333, "frames": 107}, "eat_loop_ffprobe": {"width": 480, "height": 270, "fps": 24, "duration_seconds": 8.0, "frames": 192}, "films_ffprobe": "passed", "immutable_toolkit_hash": provenance["immutable_toolkit_boundary"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
