#!/usr/bin/env python3
"""Build sprint candidate 007: posture retune + unified axial overlay.

Posture answers the review notes on Sprint006 (crouched, over-flexed
knees, nose-down, parked tail) against the extended-sprint reference:

* pelvis_crouch 0.14 -> 0.07 BH, compression 0.035 -> 0.02 (taller run)
* knee_min_interior 65 -> 90 deg (hard floor under the collapse; the
  solver reports violations instead of folding silently)
* front_body_pitch 10 -> 3 deg (level back)
* unified axial gaze (forward/up, "fixed on the prey") + footfall-locked
  lateral tail with animated-mean recenter (iteration-013 treatment)

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-DYNAMICS-SLICE-001/build_sprint007_unified.py

Output: build/V9-AIRBORNE-SPRINT-001/review-candidate-007/candidate/
with unified receipt + strict contact-authority evaluation.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from eonwild_motion.dynamics.contact_authority import AuthorityThresholds
from eonwild_motion.dynamics.integration import solve_unified_run
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import evaluate_airborne_skin_with_authority

SOURCE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb"
)
SOURCE_CLIP = "PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"
BINDING = ROOT / "profiles/v9/rig.airborne-jaw-breathing.json"
SPRINT006_PROFILE = (
    ROOT / "build/V9-AIRBORNE-SPRINT-001/review-candidate-006/candidate/engineering-profile.json"
)
CONTACT_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)
OUTPUT = ROOT / "build/V9-AIRBORNE-SPRINT-001/review-candidate-007/candidate"

OVERRIDES = {
    "pelvis_crouch_body_heights": 0.07,
    "pelvis_compression_body_heights": 0.02,
    "knee_min_interior_degrees": 90.0,
    "front_body_pitch_degrees": 3.0,
}


def main() -> None:
    roles = json.loads(BINDING.read_text())["roles"]
    base = load_airborne_gait(json.loads(SPRINT006_PROFILE.read_text()))
    gait = replace(base, **OVERRIDES)
    contact_profile = json.loads(CONTACT_PROFILE.read_text())
    print("sprint007 unified solve ...", flush=True)
    root_out, in_place_out, unified, detail = solve_unified_run(
        source=Glb.from_bytes(SOURCE.read_bytes()),
        source_clip=SOURCE_CLIP,
        semantic_roles=roles,
        gait=gait,
        axial_lateral=(1.0, 0.0, 0.0),
        gaze_distance_m=1.2,
        gaze_height_offset_m=0.2,
        tail_params={"inertia_kg_m2": 750.0, "body_inertia_kg_m2": 7500.0},
        clip_prefix="V9_SPRINT007_UNIFIED",
        tail_yaw_axis=(0.0, 0.0, 1.0),
        tail_lateral_peak_deg=6.5,
        tail_recenter=1.0,
        tail_yaw_weights=[0.5, 0.75, 1.0, 1.25, 1.5, 1.5, 1.25, 1.0, 0.75],
    )
    print(f"  axial reached={unified['axial_all_reached']} "
          f"worst={unified['axial_worst_residual_m']:.4f}m "
          f"replaced={len(unified['channels_replaced'])} "
          f"yawed={len(unified.get('channels_yawed', []))} "
          f"lateral_total={unified.get('tail_lateral_total_deg', 0.0):.2f}deg "
          f"seam={unified['loop_seam_deg']:.4f}deg", flush=True)
    leg_receipt = detail["leg_receipt"]
    print(f"  leg max_residual={leg_receipt.get('max_foot_target_residual_m')} "
          f"max_unreachable={leg_receipt.get('max_unreachable_extension_m')} "
          f"max_envelope_violation={leg_receipt.get('max_articulation_envelope_violation_degrees')}",
          flush=True)
    print("contact authority ...", flush=True)
    skin = evaluate_airborne_skin_with_authority(
        Glb.from_bytes(root_out),
        contact_profile=contact_profile,
        gait=gait,
        body_height_m=leg_receipt["body_height_m"],
        authority_thresholds=AuthorityThresholds(),
        clip_name="V9_SPRINT007_UNIFIED_ROOT_MOTION",
    )
    authority = skin["contact_authority_v1"]
    print(f"  authority={authority['verdict']}", flush=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "airborne-run-root_motion.glb").write_bytes(root_out)
    (OUTPUT / "airborne-run-in_place.glb").write_bytes(in_place_out)
    profile_out = dict(json.loads(SPRINT006_PROFILE.read_text()))
    profile_out.setdefault("parameters", {}).update(OVERRIDES)
    profile_out["status"] = "SPRINT007_UNIFIED_POSTURE_REVIEW_CANDIDATE"
    for name, value in (
        ("engineering-profile", profile_out),
        ("unified-receipt", unified),
        ("leg-receipt", leg_receipt),
        ("axial-solution", {k: v for k, v in detail["axial"].items() if k != "samples"}),
        ("contact-authority", authority),
    ):
        (OUTPUT / f"{name}.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
