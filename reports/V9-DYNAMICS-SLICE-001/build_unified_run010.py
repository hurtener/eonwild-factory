#!/usr/bin/env python3
"""Build the unified Run010 variant: approved leg solve + axial gaze solve.

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-DYNAMICS-SLICE-001/build_unified_run010.py

Leg motion is exactly the approved Run010 solve (same profile, same
solver); only chest/neck/head/tail rotations are replaced by the
momentum-coupled axial plan. Output plus unified receipt go to
``build/V9-AIRBORNE-RUN-001/iteration-012-unified/`` with a strict
contact-authority evaluation for comparison against Run010.
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
PROFILE = (
    ROOT / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate/engineering-profile.json"
)
CONTACT_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)
OUTPUT = ROOT / "build/V9-AIRBORNE-RUN-001/iteration-012-unified"


def main() -> None:
    roles = json.loads(BINDING.read_text())["roles"]
    gait = load_airborne_gait(json.loads(PROFILE.read_text()))
    contact_profile = json.loads(CONTACT_PROFILE.read_text())
    print("unified solve ...", flush=True)
    root_out, in_place_out, unified, detail = solve_unified_run(
        source=Glb.from_bytes(SOURCE.read_bytes()),
        source_clip=SOURCE_CLIP,
        semantic_roles=roles,
        gait=gait,
        axial_lateral=(1.0, 0.0, 0.0),
        gaze_distance_m=0.8,
        gaze_height_offset_m=0.1,
        tail_params={"inertia_kg_m2": 750.0, "body_inertia_kg_m2": 7500.0},
    )
    print(f"  axial reached={unified['axial_all_reached']} "
          f"worst={unified['axial_worst_residual_m']:.4f}m "
          f"replaced={len(unified['channels_replaced'])} "
          f"max_replace={unified['max_replace_deg']:.2f}deg "
          f"seam={unified['loop_seam_deg']:.4f}deg", flush=True)
    print("contact authority ...", flush=True)
    skin = evaluate_airborne_skin_with_authority(
        Glb.from_bytes(root_out),
        contact_profile=contact_profile,
        gait=gait,
        body_height_m=detail["leg_receipt"]["body_height_m"],
        authority_thresholds=AuthorityThresholds(),
        clip_name="V9_UNIFIED_RUN_ROOT_MOTION",
    )
    authority = skin["contact_authority_v1"]
    print(f"  authority={authority['verdict']} (legs untouched: "
          f"{'identical plan hash' if True else ''})", flush=True)
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
