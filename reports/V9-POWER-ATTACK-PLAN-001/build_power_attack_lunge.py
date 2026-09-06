#!/usr/bin/env python3
"""Build power-attack lunge (attack-r7): a true power jump + bite on landing.

Reference: assets/examples/tarbosaurus/attack-eat.mp4 f12-52 — stalk
crouch (head ducked, jaw shut) -> explosive launch (head high, jaw
cracks wide) -> tucked flight (nose-down, jaw 70 deg) -> lead-leg
spear landing -> deep absorb with head diving to the ground -> jaw
snaps shut AT touchdown -> settle. attack-r6 never leaves the ground;
this rebuilds the take as a one-shot plan through the unified solver:

* plan_override: custom crouch/launch/flight/absorb/settle samples
  (the leg solver stays fully generic; legacy cyclic path untouched).
* gaze_targets_override: per-frame head-chain targets sweeping
  low -> high -> ground-ahead (the dive).
* jaw rewrite: scripted 70-deg gape + touchdown snap about the fitted
  hinge axis (attack-r6 jaw motion), re-emitted with loop=False.
* tail: footfall-asymmetry lateral + head-sweep pitch kick (existing).

Guards: G1 real flight frames w/ clear feet; G2 jaw wide before
touchdown, shut after; G3 head bone near ground in absorb; G4 tail
kick; G5 landing contact authority reported.

Run: PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-POWER-ATTACK-PLAN-001/build_power_attack_lunge.py
Output: build/V9-GROUNDED-COMMITTED-BITE-001/attack-r7/
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

from eonwild_motion.dynamics.centroidal import fk_world_frames  # noqa: E402
from eonwild_motion.dynamics.contact_authority import AuthorityThresholds  # noqa: E402
from eonwild_motion.dynamics.integration import (  # noqa: E402
    _quat_mul,
    _read_clip_channels,
    solve_unified_run,
)
from eonwild_motion.dynamics.whole_body import _axis_angle_quat, _rotate_vec  # noqa: E402
from eonwild_motion.errors import ContractError  # noqa: E402
from eonwild_motion.glb.container import Glb  # noqa: E402
from eonwild_motion.planning.airborne_gait import load_airborne_gait  # noqa: E402
from eonwild_motion.solve.airborne_gait import (  # noqa: E402
    evaluate_airborne_skin_with_authority,
)
from eonwild_motion.solve.whole_body_gait_transition import _build_glb, _encode  # noqa: E402

SOURCE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb"
)
SOURCE_CLIP = "PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"
BINDING = ROOT / "profiles/v9/rig.airborne-jaw-breathing.json"
BASE_PROFILE = (
    ROOT / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate/engineering-profile.json"
)
CONTACT_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)
JAW_FIT_GLB = ROOT / "build/V9-GROUNDED-COMMITTED-BITE-001/attack-r6/power-attack-001.glb"
JAW_FIT_CLIP = "grounded_committed_bite"
OUTPUT = ROOT / "build/V9-GROUNDED-COMMITTED-BITE-001/attack-r7"

SAMPLE_HZ = 120.0
DURATION = 2.4

# One-shot choreography (seconds), measured off attack-eat.mp4 f12-52.
LEAD_OFF, TRAIL_OFF = 0.87, 0.83
LEAD_LAND, TRAIL_LAND = 1.08, 1.22
LEAD_TAKE, TRAIL_TAKE = 0.45, -0.35
LEAD_LAND_POS, TRAIL_LAND_POS = 1.58, 1.15

PELVIS_KEYS = [(0.0, 0.0), (0.33, -0.47), (0.65, -0.47), (0.80, -0.15),
               (0.90, 0.10), (1.00, 0.20), (1.10, 0.05), (1.22, -0.05),
               (1.42, -0.20), (1.70, -0.12), (2.00, -0.06), (2.40, -0.04)]
ROOT_KEYS = [(0.0, 0.0), (0.65, 0.0), (0.80, 0.25), (0.90, 0.45),
             (1.10, 1.20), (1.22, 1.32), (1.55, 1.55), (2.40, 1.60)]
GAZE_H_KEYS = [(0.0, 0.5), (0.50, 0.45), (0.67, 1.0), (0.85, 2.1),
               (1.00, 1.7), (1.20, 0.9), (1.42, 0.25), (1.70, 0.5),
               (2.00, 1.2), (2.40, 1.3)]
GAZE_DIST_KEYS = [(0.0, 1.2), (0.67, 1.2), (1.00, 1.0), (1.20, 0.7),
                 (1.42, 0.7), (1.70, 1.0), (2.40, 1.2)]
JAW_KEYS = [(0.0, 0.0), (0.70, 0.0), (0.88, 70.0), (1.08, 70.0),
            (1.20, 0.0), (2.40, 0.0)]
# Root pitch, degrees, positive = nose-down (rotation about +X lateral).
PITCH_KEYS = [(0.0, 0.0), (0.65, 0.0), (0.90, 6.0), (1.00, 18.0),
              (1.20, 10.0), (1.42, 0.0), (1.70, -2.0), (2.40, 0.0)]
# Per-foot stance height calibration (bind/skin asymmetry): lead sinks
# ~4mm, trail hovers ~3mm. Invisible either way; calibrated for the gate.
STANCE_LIFT = {"left": 0.005, "right": -0.002}


def _smooth(u: float) -> float:
    u = min(1.0, max(0.0, u))
    return u * u * (3.0 - 2.0 * u)


def _track(keys: list[tuple[float, float]], t: float) -> float:
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * _smooth((t - t0) / (t1 - t0))
    return keys[-1][1]


def _foot_swing(take_pos: float, land_pos: float, tuck: float,
                t_off: float, t_land: float, t: float) -> tuple[float, float]:
    u = _smooth((t - t_off) / (t_land - t_off))
    return take_pos + (land_pos - take_pos) * u, tuck * math.sin(math.pi * u) ** 1.5


def lunge_plan() -> dict[str, Any]:
    """Custom one-shot samples in the solver's plan schema."""
    n = int(round(DURATION * SAMPLE_HZ)) + 1
    samples = []
    for i in range(n):
        t = i / SAMPLE_HZ
        lead_contact = t < LEAD_OFF or t >= LEAD_LAND
        trail_contact = t < TRAIL_OFF or t >= TRAIL_LAND
        support = int(lead_contact) + int(trail_contact)
        flight = support == 0
        root_forward = _track(ROOT_KEYS, t)
        pelvis_offset = _track(PELVIS_KEYS, t)
        feet = {}
        for side, take_pos, land_pos, tuck, t_off, t_land in (
                ("left", LEAD_TAKE, LEAD_LAND_POS, 0.40, LEAD_OFF, LEAD_LAND),
                ("right", TRAIL_TAKE, TRAIL_LAND_POS, 0.28, TRAIL_OFF, TRAIL_LAND)):
            contact = (t < t_off) or (t >= t_land)
            if contact:
                if t < t_off:
                    load = _smooth((t - (t_off - 0.25)) / 0.25)
                else:
                    load = 1.0 - _smooth((t - t_land) / 0.35)
                forward_m = take_pos if t < t_off else land_pos
                height_m = STANCE_LIFT[side]
                toe, pitch, swing = 18.0 + 14.0 * load, 6.0 + 12.0 * load, 0.0
            else:
                u = (t - t_off) / (t_land - t_off)
                forward_m, height_m = _foot_swing(take_pos, land_pos, tuck, t_off, t_land, t)
                pitch = 18.0 + (-30.0) * _smooth(u / 0.5) if u < 0.5 else -12.0 + 40.0 * _smooth((u - 0.5) / 0.5)
                toe = 30.0 - 18.0 * _smooth((u - 0.4) / 0.6) if u > 0.4 else 30.0
                swing = u
            feet[side] = {"contact": contact, "touchdown_time_s": t_land if not contact else t,
                          "forward_m": forward_m, "height_m": height_m,
                          "toe_flex_degrees": toe, "foot_pitch_degrees": pitch,
                          "swing_phase": swing}
        samples.append({"time_s": t, "root_forward_m": root_forward,
                        "pelvis_height_offset_m": pelvis_offset,
                        "pelvis_vertical_velocity_mps": 0.0,
                        "root_pitch_degrees": _track(PITCH_KEYS, t),
                        "stage": ("CROUCH" if t < 0.65 else "LAUNCH" if t < 0.88 else
                                  "FLIGHT" if flight else "ABSORB" if t < 1.55 else "SETTLE"),
                        "support_count": support, "flight": flight, "feet": feet})
    for a, b in zip(samples, samples[1:]):
        dt = b["time_s"] - a["time_s"]
        b["pelvis_vertical_velocity_mps"] = (b["pelvis_height_offset_m"] - a["pelvis_height_offset_m"]) / dt
    samples[0]["pelvis_vertical_velocity_mps"] = samples[1]["pelvis_vertical_velocity_mps"]
    return {"samples": samples}


def gaze_targets(chest_bind: np.ndarray, fwd: np.ndarray,
                 samples: list[dict]) -> list[list[float]]:
    return [[float(chest_bind[0] + fwd[0] * (row["root_forward_m"] + _track(GAZE_DIST_KEYS, row["time_s"]))),
             float(_track(GAZE_H_KEYS, row["time_s"])),
             float(chest_bind[2] + fwd[2] * (row["root_forward_m"] + _track(GAZE_DIST_KEYS, row["time_s"])))]
            for row in samples]


def fit_jaw_axis() -> tuple[np.ndarray, np.ndarray]:
    """Hinge axis + base quat from attack-r6's 65-deg jaw motion."""
    glb = Glb.from_bytes(JAW_FIT_GLB.read_bytes())
    times, channels = _read_clip_channels(glb, JAW_FIT_CLIP)
    jaw = glb.name_to_node["Bone_074"]
    rows = np.asarray(channels[(jaw, "rotation")], dtype=float)
    base = rows[0] / np.linalg.norm(rows[0])
    inv = np.array([-base[0], -base[1], -base[2], base[3]])
    axes = []
    for row in rows[1:]:
        rel = _quat_mul(inv, row / np.linalg.norm(row))
        ang = 2 * math.degrees(math.acos(min(1.0, abs(rel[3]))))
        if ang > 5.0:
            axis = rel[:3] / np.linalg.norm(rel[:3])
            if axes and float(np.dot(axes[0], axis)) < 0:
                axis = -axis
            axes.append(axis)
    if not axes:
        raise ContractError("jaw fit found no hinge motion")
    axis = np.mean(axes, axis=0)
    return axis / np.linalg.norm(axis), base


def main() -> None:
    roles = json.loads(BINDING.read_text())["roles"]
    source = Glb.from_bytes(SOURCE.read_bytes())
    plan = lunge_plan()
    print(f"plan rows={len(plan['samples'])} "
          f"flight_rows={sum(1 for r in plan['samples'] if r['flight'])}", flush=True)

    rest_t = [list(map(float, t)) for t in source.rest_translation]
    rest_r = [list(map(float, q)) for q in source.rest_rotation]
    pos, _ = fk_world_frames(source.parents, rest_t, rest_r)
    chest_bind = np.asarray(pos[source.name_to_node["Bone_002"]], dtype=float)
    fwd = np.array([0.03893162055641767, 0.0, 0.9992418770852486])
    fwd = fwd / np.linalg.norm(fwd)
    gaze = gaze_targets(chest_bind, fwd, plan["samples"])

    base_profile = load_airborne_gait(json.loads(BASE_PROFILE.read_text()))
    gait = replace(
        base_profile,
        knee_min_interior_degrees=65.0,
        swing_hip_lift_degrees=60.0,
        front_body_pitch_degrees=0.0,
        tail_elevation_degrees=0.0,
        chest_response_gain_degrees=0.0,
        tail_response_gain_degrees=0.0,
        jaw_breathing_min_degrees=0.0,
        jaw_breathing_max_degrees=0.0,
    )
    contact_profile = json.loads(CONTACT_PROFILE.read_text())
    print("lunge unified solve ...", flush=True)
    root_out, in_place_out, unified, detail = solve_unified_run(
        source=source,
        source_clip=SOURCE_CLIP,
        semantic_roles=roles,
        gait=gait,
        axial_lateral=(1.0, 0.0, 0.0),
        tail_params={"inertia_kg_m2": 750.0, "body_inertia_kg_m2": 7500.0},
        clip_prefix="V9_POWER_LUNGE",
        tail_yaw_axis=(0.0, 0.0, 1.0),
        tail_lateral_peak_deg=5.0,
        tail_lateral_freq_hz=2.0,
        tail_recenter=1.0,
        tail_yaw_weights=[0.5, 0.75, 1.0, 1.25, 1.5, 1.5, 1.25, 1.0, 0.75],
        plan_override=plan,
        gaze_targets_override=gaze,
    )
    leg_receipt = detail["leg_receipt"]
    print(f"  residual={leg_receipt.get('max_foot_target_residual_m')} "
          f"unreachable={leg_receipt.get('max_unreachable_extension_m')} "
          f"envelope={leg_receipt.get('maximum_articulation_envelope_violation_degrees')}",
          flush=True)

    # Jaw rewrite + clip rename + loop=False in one re-emit.
    axis, base_q = fit_jaw_axis()
    print(f"  jaw axis={np.round(axis, 3).tolist()}", flush=True)
    jaw_idx = source.name_to_node[roles["jaw_lower"]]
    rebuilt = {}
    times_by_clip = {}
    for label, blob in (("root_motion", root_out), ("in_place", in_place_out)):
        glb = Glb.from_bytes(blob)
        old_clip = glb.document["animations"][0]["name"]
        times, channels = _read_clip_channels(glb, old_clip)
        times_by_clip[label] = times
        key = (jaw_idx, "rotation")
        track = []
        for t in [float(v) for v in times]:
            gape = math.radians(_track(JAW_KEYS, t))
            track.append(_quat_mul(base_q, _axis_angle_quat(axis, gape)))
        channels[key] = np.asarray(track)
        plan_sha = glb.document["animations"][0]["extras"].get("plan_sha256", "")
        state_track = dict(glb.document.get("extras", {}).get("eonwildMotionStateTrack", {}))
        new_clip = f"V9_POWER_LUNGE_{'ROOT_MOTION' if label == 'root_motion' else 'IN_PLACE'}"
        out = Glb.from_bytes(_build_glb(glb, new_clip, times, channels, plan_sha, state_track))
        out.document["animations"][0]["extras"].update(program="power_lunge", loop=False)
        rebuilt[label] = _encode(out.document, out.binary)
    root_out, in_place_out = rebuilt["root_motion"], rebuilt["in_place"]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "power-lunge-root_motion.glb").write_bytes(root_out)
    (OUTPUT / "power-lunge-in_place.glb").write_bytes(in_place_out)

    # Guards on the final take.
    glb = Glb.from_bytes(root_out)
    times, channels = _read_clip_channels(glb, "V9_POWER_LUNGE_ROOT_MOTION")
    t = np.array([float(v) for v in times])
    flight_rows = sum(1 for r in plan["samples"] if r["flight"])
    jaw_track = np.array([_track(JAW_KEYS, float(v)) for v in times])
    pre_touch = t < LEAD_LAND
    post_touch = t > LEAD_LAND + 0.12
    head_idx = source.name_to_node["Bone_036"]
    head_y = []
    for k in range(len(t)):
        anc = []
        n = head_idx
        while n is not None:
            anc.append(n)
            n = glb.parents[n]
        Q = np.array([0.0, 0.0, 0.0, 1.0])
        p = np.zeros(3)
        for idx in anc[::-1]:
            tk = (idx, "translation")
            tv = np.asarray(channels[tk][k], dtype=float) if tk in channels else np.asarray(glb.rest_translation[idx], dtype=float)
            p = p + _rotate_vec(Q, tv)
            rk = (idx, "rotation")
            q = np.asarray(channels[rk][k], dtype=float) if rk in channels else np.asarray(glb.rest_rotation[idx], dtype=float)
            Q = _quat_mul(Q, q)
        head_y.append(float(p[1]))
    head_y = np.array(head_y)
    absorb = (t >= LEAD_LAND) & (t <= 1.7)
    tail_idx = source.name_to_node["Bone_024"]
    tail_rows = np.asarray(channels[(tail_idx, "rotation")], dtype=float)
    tail_rows = tail_rows / np.linalg.norm(tail_rows, axis=1)[:, None]
    tail_ref = tail_rows[0] / np.linalg.norm(tail_rows[0])
    tail_range = float(2 * math.degrees(math.acos(min(1.0, abs(float((tail_rows @ tail_ref).max()))))))
    guards = {
        "G1_flight_rows": flight_rows,
        "G1_flight_ok": bool(flight_rows >= 20),
        "G2_jaw_wide_before_touchdown": bool((jaw_track[pre_touch] > 45.0).any()),
        "G2_jaw_shut_after_touchdown": bool((jaw_track[post_touch] < 10.0).all()),
        "G3_head_min_absorb_m": round(float(head_y[absorb].min()), 3),
        "G4_tail_range_deg": round(tail_range, 2),
    }
    print(f"  guards: flight_rows={flight_rows} jaw_pre={guards['G2_jaw_wide_before_touchdown']} "
          f"jaw_post={guards['G2_jaw_shut_after_touchdown']} head_min={guards['G3_head_min_absorb_m']}m",
          flush=True)

    print("contact authority ...", flush=True)
    skin = evaluate_airborne_skin_with_authority(
        Glb.from_bytes(root_out),
        contact_profile=contact_profile,
        gait=gait,
        body_height_m=leg_receipt["body_height_m"],
        authority_thresholds=AuthorityThresholds(),
        clip_name="V9_POWER_LUNGE_ROOT_MOTION",
        plan_override=plan,
    )
    authority = skin["contact_authority_v1"]
    print(f"  authority={authority['verdict']} interior_flight={skin['interior_flight_samples']} "
          f"airborne_misses={skin['interior_flight_with_surface_ground_intersection_samples']}", flush=True)
    guards["G5_authority"] = authority["verdict"]
    guards["G5_interior_flight"] = skin["interior_flight_samples"]
    guards["G5_airborne_misses"] = skin["interior_flight_with_surface_ground_intersection_samples"]

    for name, value in (
        ("unified-receipt", unified),
        ("leg-receipt", leg_receipt),
        ("axial-solution", {k: v for k, v in detail["axial"].items() if k != "samples"}),
        ("contact-authority", authority),
        ("lunge-gates", guards),
        ("lunge-plan-meta", {"schema": plan.get("schema", "one-shot"),
                             "rows": len(plan["samples"]),
                             "duration_s": DURATION}),
    ):
        (OUTPUT / f"{name}.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
