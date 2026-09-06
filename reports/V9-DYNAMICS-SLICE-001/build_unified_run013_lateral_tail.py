#!/usr/bin/env python3
"""Build iteration-013: unified Run010 + lateral tail counter-sway.

Same approved leg solve as iteration-012; only the tail overlay gains
two terms: a static recenter (fraction of the rig's rest-pose lean) and
a footfall-locked lateral ODE (stance asymmetry from the shared contact
plan at stride frequency). Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-DYNAMICS-SLICE-001/build_unified_run013_lateral_tail.py \\
        [--peak-deg 4.0] [--recenter 1.0] [--sign 1.0]

Output plus unified receipt go to
``build/V9-AIRBORNE-RUN-001/iteration-013-lateral-tail/`` with a strict
contact-authority evaluation (legs untouched: verdict must match 012).
"""

from __future__ import annotations

import argparse
import json
import sys
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
PROFILE = (
    ROOT / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate/engineering-profile.json"
)
CONTACT_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)
OUTPUT = ROOT / "build/V9-AIRBORNE-RUN-001/iteration-013-lateral-tail"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peak-deg", type=float, default=6.5)
    parser.add_argument("--recenter", type=float, default=1.0)
    parser.add_argument("--sign", type=float, default=1.0)
    args = parser.parse_args()

    roles = json.loads(BINDING.read_text())["roles"]
    gait = load_airborne_gait(json.loads(PROFILE.read_text()))
    contact_profile = json.loads(CONTACT_PROFILE.read_text())
    print("unified solve (lateral tail) ...", flush=True)
    root_out, in_place_out, unified, detail = solve_unified_run(
        source=Glb.from_bytes(SOURCE.read_bytes()),
        source_clip=SOURCE_CLIP,
        semantic_roles=roles,
        gait=gait,
        axial_lateral=(1.0, 0.0, 0.0),
        gaze_distance_m=0.8,
        gaze_height_offset_m=0.1,
        tail_params={"inertia_kg_m2": 750.0, "body_inertia_kg_m2": 7500.0},
        clip_prefix="V9_UNIFIED_RUN_LATERAL_TAIL",
        tail_yaw_axis=(0.0, 0.0, 1.0),
        tail_lateral_peak_deg=args.peak_deg,
        tail_lateral_sign=args.sign,
        tail_recenter=args.recenter,
        tail_yaw_weights=[0.5, 0.75, 1.0, 1.25, 1.5, 1.5, 1.25, 1.0, 0.75],
    )
    print(f"  axial reached={unified['axial_all_reached']} "
          f"worst={unified['axial_worst_residual_m']:.4f}m "
          f"replaced={len(unified['channels_replaced'])} "
          f"yawed={len(unified.get('channels_yawed', []))} "
          f"lateral_total={unified.get('tail_lateral_total_deg', 0.0):.2f}deg "
          f"seam={unified['loop_seam_deg']:.4f}deg", flush=True)
    print("contact authority ...", flush=True)
    skin = evaluate_airborne_skin_with_authority(
        Glb.from_bytes(root_out),
        contact_profile=contact_profile,
        gait=gait,
        body_height_m=detail["leg_receipt"]["body_height_m"],
        authority_thresholds=AuthorityThresholds(),
        clip_name="V9_UNIFIED_RUN_LATERAL_TAIL_ROOT_MOTION",
    )
    authority = skin["contact_authority_v1"]
    print(f"  authority={authority['verdict']}", flush=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "airborne-run-root_motion.glb").write_bytes(root_out)
    (OUTPUT / "airborne-run-in_place.glb").write_bytes(in_place_out)
    for name, value in (
        ("unified-receipt", unified),
        ("leg-receipt", detail["leg_receipt"]),
        ("axial-solution", {k: v for k, v in detail["axial"].items() if k != "samples"}),
        ("contact-authority", authority),
    ):
        (OUTPUT / f"{name}.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
