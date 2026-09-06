"""Evaluate the skinned contact authority on real persisted artifacts.

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-DYNAMICS-SLICE-001/evaluate_real_artifacts.py

Runs ``evaluate_airborne_skin_with_authority`` (persistent ground-plane
semantics, band-relative speeds excluded) on the Run010 and Sprint006
review candidates and writes ``real-artifact-authority.json``. Slow
(skinned sampling at 120 Hz); deterministic for pinned inputs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eonwild_motion.dynamics.contact_authority import AuthorityThresholds
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import evaluate_airborne_skin_with_authority

OUTPUT = Path(__file__).resolve().parent
# Tolerance sweep: where does persistent contact actually live? The legacy
# floor semantics accepted 30 mm; the strict gate demands 1 mm.
TOLERANCE_SWEEP_M = (0.001, 0.005, 0.015)
CONTACT_PROFILE = (
    OUTPUT.parents[1]
    / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)
CANDIDATES = {
    "run010": OUTPUT.parents[1] / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate",
    "sprint006": OUTPUT.parents[1] / "build/V9-AIRBORNE-SPRINT-001/review-candidate-006/candidate",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    contact_profile = json.loads(CONTACT_PROFILE.read_text(encoding="utf-8"))
    ground = float(contact_profile["geometry"]["ground"]["level_m"])
    report: dict = {"contact_profile_sha256": _sha(CONTACT_PROFILE), "candidates": {}}
    for name, directory in sorted(CANDIDATES.items()):
        glb_path = directory / "airborne-run-root_motion.glb"
        profile = json.loads((directory / "engineering-profile.json").read_text(encoding="utf-8"))
        gait = load_airborne_gait(profile)
        body_height = float(
            json.loads((directory / "solve-receipt.json").read_text(encoding="utf-8"))["body_height_m"]
        )
        glb = Glb.from_bytes(glb_path.read_bytes())
        print(f"evaluating {name} ...", flush=True)
        sweeps = {}
        for tolerance in TOLERANCE_SWEEP_M:
            result = evaluate_airborne_skin_with_authority(
                glb,
                contact_profile=contact_profile,
                gait=gait,
                body_height_m=body_height,
                authority_thresholds=AuthorityThresholds(ground_tolerance_m=tolerance, ground_m=ground),
            )
            authority = result["contact_authority_v1"]
            sweeps[str(tolerance)] = {
                "legacy_status": result["status"],
                "authority_verdict": authority["verdict"],
                "per_foot": {
                    side: {
                        "verdict": foot["verdict"],
                        "persistent_point_total": sum(
                            phase.get("persistent_point_total", 0) for phase in foot.get("phases", [])
                        ),
                        "unknown_pairs": sum(
                            phase.get("unknown_pairs", 0) for phase in foot.get("phases", [])
                        ),
                        "min_gap_m": min(
                            (phase["minimum_gap_m"] for phase in foot.get("phases", [])
                             if phase["minimum_gap_m"] is not None),
                            default=None,
                        ),
                        "max_yaw_deg": max(
                            (phase["yaw_deg"] or 0.0 for phase in foot.get("phases", [])),
                            default=0.0,
                        ),
                        "reasons": foot.get("reasons", []),
                    }
                    for side, foot in authority["per_foot"].items()
                },
            }
            print(f"  tol={tolerance}: legacy={result['status']} authority={authority['verdict']}", flush=True)
        report["candidates"][name] = {
            "artifact_sha256": _sha(glb_path),
            "sweeps": sweeps,
        }
    (OUTPUT / "real-artifact-authority.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("wrote real-artifact-authority.json")


if __name__ == "__main__":
    main()
