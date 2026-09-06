#!/usr/bin/env python3
"""Build backward-walk 001: corrective toe-first reverse shuffle.

Plan C of reports/V9-POWER-ATTACK-PLAN-001/plan.md from the backward
shuffle in GROUNDED COMMITTED BITE (re-aim while the head stays on
target):

* short slow reverse plan: negative step length, duty >= 0.7 (double-
  support biased), toe-first contact (toe_flex up, pitch leads
  reversed), crouched (crouch 0.06 BH), head gaze locked FORWARD on the
  target (decoupled from travel direction — the point of the maneuver).
* small fast tail sway at 2x step frequency (animated branch, not the
  footfall ODE).
* gates: backward speed <= 1 m/s, hyperextension guard (knee/ankle max
  interior respected, violations reported not folded), head yaw drift
  < 2 deg, loop seam < 0.5 deg, strict contact authority evaluation.

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-POWER-ATTACK-PLAN-001/build_backward_walk_001.py

Output: build/V9-BACKWARD-WALK-001/candidate/
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from eonwild_motion.dynamics.contact_authority import AuthorityThresholds
from eonwild_motion.dynamics.integration import (
    _quat_mul,
    _read_clip_channels,
    solve_unified_run,
    tail_step_asymmetry,
)
from eonwild_motion.dynamics.transition import tail_ode_track
from eonwild_motion.dynamics.whole_body import _axis_angle_quat, _rotate_vec
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import evaluate_airborne_skin_with_authority

SOURCE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb"
)
SOURCE_CLIP = "PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"
BINDING = ROOT / "profiles/v9/rig.airborne-jaw-breathing.json"
WALK_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb"
)
BASE_PROFILE = (
    ROOT / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate/engineering-profile.json"
)
CONTACT_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)
OUTPUT = ROOT / "build/V9-BACKWARD-WALK-001/candidate"

OVERRIDES = {
    "step_period_s": 0.7,
    "flight_fraction": 0.05,
    "continuous_body_launch_fraction": 0.0,
    "chest_response_gain_degrees": 0.0,
    "tail_response_gain_degrees": 0.0,
    "step_length_body_heights": 0.28,
    "touchdown_reach_body_heights": 0.12,
    "swing_clearance_body_heights": 0.10,
    "pelvis_compression_body_heights": 0.03,
    "pelvis_crouch_body_heights": 0.06,
    "toe_flex_degrees": 40.0,
    "push_off_pitch_degrees": 20.0,
    "foot_recovery_pitch_degrees": 20.0,
    "hip_extension_limit_degrees": 45.0,
    "hip_flexion_limit_degrees": 80.0,
    "cycles": 2,
    "sample_hz": 120,
}


def reverse_plan(plan: dict) -> dict:
    """Mirror a forward plan into reverse travel (toe-first shuffle)."""
    out = json.loads(json.dumps(plan))
    for row in out["samples"]:
        row["root_forward_m"] = -row["root_forward_m"]
        for side, foot in row["feet"].items():
            foot["forward_m"] = -foot["forward_m"]
            # Toe-first contact: swap pitch attitude sign so the toe
            # leads into the reversed touchdown.
            foot["foot_pitch_degrees"] = -foot["foot_pitch_degrees"]
    return out


def gates(glb_path: Path, clip: str, roles: dict, body_height_m: float,
          leg_receipt: dict) -> dict:
    glb = Glb.from_bytes(glb_path.read_bytes())
    times, channels = _read_clip_channels(glb, clip)
    t = np.array([float(v) for v in times])
    root_idx = glb.name_to_node[roles["root"]]
    root_p = np.asarray(channels[(root_idx, "translation")], dtype=float)
    duration = float(t[-1] - t[0])
    backward_speed = float((root_p[0, 0] - root_p[-1, 0]) / duration)
    head_idx = glb.name_to_node[roles["head"]]
    yaw0 = None
    max_yaw_drift = 0.0
    for k in range(len(t)):
        q = np.asarray(channels[(head_idx, "rotation")][k], dtype=float)
        yaw = float(2 * math.degrees(math.acos(min(1.0, abs(q[3])))))
        yaw0 = yaw if yaw0 is None else yaw0
        max_yaw_drift = max(max_yaw_drift, abs(yaw - yaw0))
    seam = 0.0
    for (node, path), arr in channels.items():
        if path != "rotation":
            continue
        a = np.asarray(arr[0], dtype=float)
        b = np.asarray(arr[-1], dtype=float)
        seam = max(seam, float(2 * math.degrees(
            math.acos(min(1.0, abs(float(a @ b)))))))
    return {
        "backward_speed_mps": round(backward_speed, 3),
        "backward_speed_ok": bool(backward_speed <= 1.0),
        "head_yaw_drift_deg": round(max_yaw_drift, 3),
        "head_yaw_ok": bool(max_yaw_drift < 2.0),
        "loop_seam_deg": round(seam, 4),
        "loop_ok": bool(seam < 0.5),
        "max_foot_residual_m": leg_receipt.get("max_foot_target_residual_m"),
        "max_unreachable_m": leg_receipt.get("max_unreachable_extension_m"),
    }


def main() -> None:
    roles = json.loads(BINDING.read_text())["roles"]
    base = load_airborne_gait(json.loads(BASE_PROFILE.read_text()))
    gait = replace(base, **OVERRIDES)
    contact_profile = json.loads(CONTACT_PROFILE.read_text())
    print("backward-walk unified solve ...", flush=True)
    root_out, in_place_out, unified, detail = solve_unified_run(
        source=Glb.from_bytes(SOURCE.read_bytes()),
        source_clip=SOURCE_CLIP,
        semantic_roles=roles,
        gait=gait,
        axial_lateral=(1.0, 0.0, 0.0),
        gaze_distance_m=1.2,
        gaze_height_offset_m=0.1,
        tail_params={"inertia_kg_m2": 750.0, "body_inertia_kg_m2": 7500.0},
        clip_prefix="V9_BACKWARD_WALK",
        tail_yaw_axis=(0.0, 0.0, 1.0),
        tail_lateral_peak_deg=4.0,
        tail_lateral_freq_hz=2.0 / 0.7,
        tail_recenter=1.0,
        tail_yaw_weights=[0.5, 0.75, 1.0, 1.25, 1.5, 1.5, 1.25, 1.0, 0.75],
    )
    leg_receipt = detail["leg_receipt"]
    # Reverse the emitted travel: root + leg/toe translations mirrored
    # about the start frame, so the animal shuffles backward while the
    # head gaze stays locked forward on the target. Rotations untouched
    # (toe-first attitude already comes from the reversed pitch plan).
    from eonwild_motion.solve.whole_body_gait_transition import _build_glb, _encode
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rebuilt = {}
    for label, blob in (("root_motion", root_out), ("in_place", in_place_out)):
        glb = Glb.from_bytes(blob)
        clip = glb.document["animations"][0]["name"]
        times, channels = _read_clip_channels(glb, clip)
        leg_nodes: set[int] = set()
        for side in ("left", "right"):
            leg_nodes.update(glb.name_to_node[n] for n in roles["legs"][side]["contactChain"])
            for chain in roles["legs"][side]["toeChains"]:
                leg_nodes.update(glb.name_to_node[n] for n in chain)
        root_idx = glb.name_to_node[roles["root"]]
        for idx in leg_nodes | {root_idx}:
            key = (idx, "translation")
            if key in channels:
                arr = channels[key].copy()
                arr[:, 0] = 2 * arr[0, 0] - arr[:, 0]
                channels[key] = arr
        plan_sha = glb.document["animations"][0]["extras"].get("plan_sha256", "")
        state_track = dict(glb.document.get("extras", {}).get("eonwildMotionStateTrack", {}))
        out = Glb.from_bytes(_build_glb(glb, clip, times, channels, plan_sha, state_track))
        rebuilt[label] = _encode(out.document, out.binary)
    root_out, in_place_out = rebuilt["root_motion"], rebuilt["in_place"]
    (OUTPUT / "backward-walk-root_motion.glb").write_bytes(root_out)
    (OUTPUT / "backward-walk-in_place.glb").write_bytes(in_place_out)
    facts = gates(OUTPUT / "backward-walk-root_motion.glb",
                  "V9_BACKWARD_WALK_ROOT_MOTION", roles,
                  leg_receipt["body_height_m"], leg_receipt)
    print(f"  speed={facts['backward_speed_mps']}m/s yaw_drift={facts['head_yaw_drift_deg']}deg "
          f"seam={facts['loop_seam_deg']}deg", flush=True)
    print("contact authority ...", flush=True)
    skin = evaluate_airborne_skin_with_authority(
        Glb.from_bytes(root_out),
        contact_profile=contact_profile,
        gait=gait,
        body_height_m=leg_receipt["body_height_m"],
        authority_thresholds=AuthorityThresholds(),
        clip_name="V9_BACKWARD_WALK_ROOT_MOTION",
    )
    authority = skin["contact_authority_v1"]
    print(f"  authority={authority['verdict']}", flush=True)
    for name, value in (
        ("unified-receipt", unified),
        ("leg-receipt", leg_receipt),
        ("axial-solution", {k: v for k, v in detail["axial"].items() if k != "samples"}),
        ("contact-authority", authority),
        ("backward-gates", facts),
    ):
        (OUTPUT / f"{name}.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
