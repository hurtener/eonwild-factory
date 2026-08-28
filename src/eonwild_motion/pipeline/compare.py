from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contracts.models import ResolvedProfile
from ..glb.container import Glb
from ..hashing import sha256_file
from .validate import artifact_difference, validate_animation_contract


def compare_artifacts(
    resolved: ResolvedProfile, baseline_path: Path, candidate_path: Path
) -> dict[str, Any]:
    baseline = Glb(baseline_path)
    candidate = Glb(candidate_path)
    candidate_contract = validate_animation_contract(
        candidate, resolved.rig, resolved.motion
    )
    difference = artifact_difference(
        baseline,
        candidate,
        resolved.rig,
        resolved.motion,
        [layer.data for layer in resolved.layers],
    )
    return {
        "schema": "eonwild.motion.comparison-report.v1",
        "status": "PASS",
        "profileId": resolved.profile["id"],
        "lockSha256": resolved.lock_sha256,
        "baseline": {
            "path": str(baseline_path),
            "sha256": sha256_file(baseline_path),
        },
        "candidate": {
            "path": str(candidate_path),
            "sha256": sha256_file(candidate_path),
        },
        "animationContract": candidate_contract,
        "difference": difference,
    }
