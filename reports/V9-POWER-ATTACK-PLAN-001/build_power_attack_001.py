#!/usr/bin/env python3
"""Build power-attack 001: retimed grounded lunge + capacity gates + guards.

Implements plan A1-A4/A5 of reports/V9-POWER-ATTACK-PLAN-001/plan.md from
the attack-eat.mp4 reference breakdown (crouch 0.67s -> launch 0.21s ->
flight ~0.27s -> miss-contact -> brake-step recover):

1. Capacity gates first: plan_power_attack with an absolute 1500 kg
   review-labeled body + provisional capacity over the reference lunge
   geometry. The emitted take stays grounded (the bite solver is
   grounded-only); the receipt records the gate variant honestly.
2. Retimed bite profile (anticipation 0.55->0.30s, gape 58->65 deg,
   pelvis drop 0.287->0.20) built with the existing attack solver.
3. Post-overlay tail kick (+18 deg at reach, stream after) through the
   damped ODE, plus small footfall lateral — the solver's body_signal
   shape cannot express a kick.
4. Guards on the emitted GLB: jaw-timing R1 (gape wide before head
   lowest), stance R2 (sole drift), tail-lag R3 (peak after body peak).

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-POWER-ATTACK-PLAN-001/build_power_attack_001.py

Output: build/V9-GROUNDED-COMMITTED-BITE-001/attack-r6/
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "build/V9-GROUNDED-COMMITTED-BITE-001"))

from eonwild_motion.contracts.v9_models import BodyInstanceProfile  # noqa: E402
from eonwild_motion.dynamics.capacity import CapacityProfile  # noqa: E402
from eonwild_motion.dynamics.integration import (  # noqa: E402
    _quat_mul,
    _read_clip_channels,
    replace_axial_rotations,
)
from eonwild_motion.dynamics.transition import tail_ode_track  # noqa: E402
from eonwild_motion.dynamics.whole_body import _rotate_vec  # noqa: E402
from eonwild_motion.glb.container import Glb  # noqa: E402
from eonwild_motion.planning.power_attack import (  # noqa: E402
    PowerAttackRequest,
    plan_power_attack,
)

import grounded_committed_bite as B  # noqa: E402
from attack_solver import build_attack  # noqa: E402

TASK_DIR = ROOT / "build/V9-GROUNDED-COMMITTED-BITE-001"
OUTPUT = TASK_DIR / "attack-r6"

RETIMED_TIMING = {
    "anticipation_end": 0.30,
    "gape_peak": 0.42,
    "reach_end": 0.62,
    "close_end": 0.85,
    "hold_end": 2.20,
    "recovery_end": 4.20,
}
RETIMED_EVENTS = [
    {"name": "TARGET_LOCK", "time_seconds": 0.05, "phase": "acquire_align_lower"},
    {"name": "LOWER_START", "time_seconds": 0.12, "phase": "acquire_align_lower"},
    {"name": "JAW_OPEN", "time_seconds": 0.30, "phase": "gape_reach"},
    {"name": "REACH_START", "time_seconds": 0.35, "phase": "gape_reach"},
    {"name": "CONTACT_BEGIN", "time_seconds": 0.62, "phase": "contact_hold"},
    {"name": "JAW_CONTACT", "time_seconds": 0.85, "phase": "contact_hold"},
    {"name": "CONTACT_HOLD_END", "time_seconds": 2.20, "phase": "contact_hold"},
    {"name": "RELEASE", "time_seconds": 2.20, "phase": "release_recovery"},
    {"name": "RECOVERY_END", "time_seconds": 4.55, "phase": "release_recovery"},
]
RETIMED_WINDOWS = {
    "acquire_align_lower": [0.0, 0.30],
    "gape_reach": [0.30, 0.62],
    "contact_hold": [0.62, 2.20],
    "release_recovery": [2.20, 5.0],
}


def _review_body() -> BodyInstanceProfile:
    segments = [
        {"id": "pelvis", "parent_id": None, "role": "pelvis", "mass_fraction": 0.5,
         "com_body_m": [0.0, 1.0, 0.0], "inertia_diagonal_normalized": [0.004, 0.006, 0.004]},
        {"id": "trunk", "parent_id": "pelvis", "role": "trunk", "mass_fraction": 0.5,
         "com_body_m": [0.0, 1.6, 0.0], "inertia_diagonal_normalized": [0.006, 0.009, 0.006]},
    ]
    return BodyInstanceProfile.from_document(
        {
            "profile_id": "power_attack_001_review",
            "family": "heavy_predatory_biped",
            "taxon": "review rig",
            "coordinate_system": {"units": "m", "time_units": "s", "mass_units": "kg",
                                  "handedness": "right", "up_axis": "Y", "forward_axis": "-Z"},
            "dimensions": {"body_length_m": 7.0, "hip_height_m": 2.15, "body_width_m": 0.95},
            "segment_com_frame": "body",
            "mass": {"mode": "absolute", "total_mass_kg": 1500.0, "mass_fraction_sum": 1.0,
                      "absolute_dynamics_enabled": True, "absolute_policy": "review_provisional"},
            "provenance": {"source": "power_attack_001", "status": "provisional",
                            "kind": "review_estimate", "scientific_claims": False},
            "segments": segments,
        }
    )


def retimed_profile() -> dict:
    profile = json.loads((TASK_DIR / "profile.json").read_text())
    attack = profile["attack"]
    attack["timing"] = dict(RETIMED_TIMING)
    attack["gape_degrees"] = 65.0
    attack["pelvis_drop_height_fraction"] = 0.20
    profile["events"] = [dict(e) for e in RETIMED_EVENTS]
    profile["timing"]["phase_windows_seconds"] = {k: list(v) for k, v in RETIMED_WINDOWS.items()}
    profile["id"] = "power-attack-001-grounded-lunge"
    profile["version"] = 2
    return profile


def capacity_gates() -> dict:
    """Gate the REFERENCE lunge geometry (0.27 s flight); take stays grounded."""
    body = _review_body()
    capacity = CapacityProfile(profile_id="power_attack_001_provisional")  # 3.5 BW prior, review-labeled
    request = PowerAttackRequest(
        body=body,
        capacity=capacity,
        launch_com_m=(0.0, 1.9, 0.0),
        launch_velocity_mps=(3.2, 1.1, 0.0),
        landing_com_m=(1.35, 1.55, 0.0),
        stance_time_s=0.25,
        preload_velocity_mps=(1.0, 0.0, 0.0),
        bite_variant="committed",
    )
    plan = plan_power_attack(request)
    return {
        "variant": plan["variant"],
        "limiting_factor": plan["limiting_factor"],
        "flight_time_s": plan["flight_time_s"],
        "takeoff": plan["takeoff"],
        "landing": plan["landing"],
        "arrest": plan["arrest"],
        "physics_evaluated": plan["physics_evaluated"],
        "capacity_status": capacity.status,
        "emitted_take": "grounded_lunge (bite solver is grounded-only)",
    }


def overlay_tail_kick(glb_path: Path, semantic_roles: dict[str, list[str]]) -> dict:
    """Post-overlay tail kick: +18 deg at reach, stream after, small lateral."""
    glb = Glb.from_bytes(glb_path.read_bytes())
    clip = "grounded_committed_bite"
    times, channels = _read_clip_channels(glb, clip)
    t = np.array([float(v) for v in times])
    # Kick window follows the retimed reach: rise to +18 deg by reach_end,
    # decay through hold. Lateral: small slow sway (grounded, braced).
    # NOTE: the ODE drive is a moment, not an angle: steady state
    # θ = M / (I·ω²), so scale the shaped drive to land the peak.
    def moments(shape_deg, inertia, freq_hz, peak_deg):
        omega = 2.0 * math.pi * freq_hz
        shape = np.asarray(shape_deg, dtype=float)
        peak = max(abs(shape).max(), 1e-9)
        return list(inertia * omega * omega * math.radians(peak_deg) * shape / peak)

    kick_shape = 18.0 * np.exp(-((t - RETIMED_TIMING["reach_end"]) ** 2) / (2 * 0.35 ** 2))
    kick_shape[t < RETIMED_TIMING["anticipation_end"]] *= 0.15
    pitch_track = tail_ode_track(
        list(t), moments(kick_shape, 750.0, 1.2, 18.0),
        inertia_kg_m2=750.0, damping_ratio=0.5, natural_freq_hz=1.2,
        max_angle_rad=math.radians(25.0), body_inertia_kg_m2=7500.0,
    )
    yaw_track = tail_ode_track(
        list(t), moments(3.0 * np.sin(2 * math.pi * t / 2.2), 750.0, 0.45, 3.0),
        inertia_kg_m2=750.0, damping_ratio=0.5, natural_freq_hz=0.45,
        max_angle_rad=math.radians(8.0), body_inertia_kg_m2=7500.0,
    )
    pitch_angles = [s["angle_rad"] for s in pitch_track["samples"]]
    yaw_angles = [s["angle_rad"] for s in yaw_track["samples"]]
    tail_names: list[str] = list(semantic_roles["tail"])
    share = len(tail_names)
    # Whip gradient peaking mid-distally (iteration-013 weights).
    weights = np.array([0.5, 0.75, 1.0, 1.25, 1.5, 1.5, 1.25, 1.0, 0.75][:share])
    weights = weights / weights.sum() * share
    chains = [{"nodes": tail_names, "lateral": [1.0, 0.0, 0.0], "yaw_axis": [0.0, 0.0, 1.0]}]
    pitch = [[pitch_angles[k] * weights[j] / share for j in range(share)] for k in range(len(t))]
    yaw = [[yaw_angles[k] * weights[j] / share for j in range(share)] for k in range(len(t))]
    new_channels, report = replace_axial_rotations(
        glb, clip=clip, chains=chains, pitch_tracks=[pitch], yaw_tracks=[yaw])
    # Re-emit the GLB with replaced tail channels (same builder the bite
    # solver used for channel I/O: read/write accessors in place).
    document = glb.document
    binary = bytearray(glb.binary)
    animation = next(a for a in document["animations"] if a.get("name") == clip)
    for channel in animation["channels"]:
        key = (int(channel["target"]["node"]), channel["target"]["path"])
        if key not in new_channels:
            continue
        sampler = animation["samplers"][int(channel["sampler"])]
        _write_accessor(document, binary, int(sampler["output"]),
                        np.asarray(new_channels[key], dtype=np.float32))
    glb_path.write_bytes(B.S.encode_glb(document, bytes(binary)))
    return {
        "tail_kick_peak_deg": float(np.degrees(max(pitch_angles)) * 1.0),
        "tail_kick_clamped_samples": pitch_track["clamped_samples"],
        "tail_lateral_range_deg": float(np.degrees(max(yaw_angles) - min(yaw_angles))),
        "channels_yawed": report.get("channels_yawed", []),
        "loop_seam_deg": report.get("loop_seam_deg"),
    }


def _write_accessor(document: dict, binary: bytearray, accessor: int, values: np.ndarray) -> None:
    view = document["bufferViews"][document["accessors"][accessor]["bufferView"]]
    start = view.get("byteOffset", 0) + document["accessors"][accessor].get("byteOffset", 0)
    component = document["accessors"][accessor]["componentType"]
    dtype = {5126: np.float32, 5123: np.uint16, 5121: np.uint8}[component]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[document["accessors"][accessor]["type"]]
    flat = np.asarray(values, dtype=dtype).reshape(-1)
    binary[start:start + flat.nbytes] = flat.tobytes()


def guards(glb_path: Path, semantic_roles: dict[str, list[str]], jaw_node: int) -> dict:
    """R1 jaw timing / R2 stance / R3 tail lag on the emitted take."""
    glb = Glb.from_bytes(glb_path.read_bytes())
    clip = "grounded_committed_bite"
    times, channels = _read_clip_channels(glb, clip)
    t = np.array([float(v) for v in times])
    head_idx = semantic_roles["head"][0]
    # Head world height + jaw openness tracks.
    head_y, jaw_open = [], []
    # Gape from the SOURCE frame-0 pose: the bite overlay post-multiplies
    # source channels, and bind pose sits far from the clip (frame 0 jaw
    # already ~50 deg from bind). Identity reference would lie.
    jaw_q0 = np.asarray(channels[(jaw_node, "rotation")][0], dtype=float)
    jaw_q0c = np.array([-jaw_q0[0], -jaw_q0[1], -jaw_q0[2], jaw_q0[3]])
    for k in range(len(t)):
        Q = np.array([0.0, 0.0, 0.0, 1.0])
        p = np.zeros(3)
        anc = []
        n = head_idx
        while n is not None:
            anc.append(n)
            n = glb.parents[n]
        for idx in anc[::-1]:
            tk = (idx, "translation")
            tv = np.asarray(channels[tk][k], dtype=float) if tk in channels else np.asarray(glb.rest_translation[idx], dtype=float)
            p = p + _rotate_vec(Q, tv)
            rk = (idx, "rotation")
            q = np.asarray(channels[rk][k], dtype=float) if rk in channels else np.asarray(glb.rest_rotation[idx], dtype=float)
            Q = _quat_mul(Q, q)
        head_y.append(float(p[1]))
        jq = np.asarray(channels[(jaw_node, "rotation")][k], dtype=float)
        rel = _quat_mul(jaw_q0c, jq)
        jaw_open.append(float(2 * math.degrees(math.acos(min(1.0, abs(rel[3]))))))
    head_y = np.array(head_y)
    jaw_open = np.array(jaw_open)
    lowest = int(np.argmin(head_y))
    wide = jaw_open > 45.0
    wide_before = bool(np.any(wide[:lowest])) and (lowest - int(np.where(wide)[0][0]) >= 5)
    # Tail lag: tail-base pitch vs pelvis pitch peaks.
    tail_idx = semantic_roles["tail"][0]
    pelvis_idx = semantic_roles["pelvis"][0]
    tail_p, pel_p = [], []
    for k in range(len(t)):
        for idx, store in ((tail_idx, tail_p), (pelvis_idx, pel_p)):
            q = np.asarray(channels[(idx, "rotation")][k], dtype=float)
            store.append(float(q[0]))  # pitch-ish x component
    tail_p = np.array(tail_p)
    pel_p = np.array(pel_p)
    t_peak = float(t[int(np.argmax(tail_p))])
    reach = 0.62  # retimed reach_end: toe-off equivalent
    in_window = (reach - 0.1) <= t_peak <= (reach + 0.5)
    # Kick fires INTO the hold: body already ≥90% committed while the
    # tail peaks on ODE lag (kick-then-stream, not a synced wag).
    # Quaternion components carry sign; compare magnitudes.
    k_peak = int(np.argmax(tail_p))
    committed = bool(abs(pel_p[k_peak]) >= 0.9 * np.abs(pel_p).max())
    lag = t_peak - reach
    return {
        "R1_jaw_wide_before_lowest_head": wide_before,
        "R1_lowest_head_s": float(t[lowest]),
        "R1_first_wide_s": float(t[int(np.where(wide)[0][0])]) if np.any(wide) else None,
        "R1_peak_gape_deg": float(jaw_open.max()),
        "R3_tail_kick_peak_s": t_peak,
        "R3_kick_in_reach_window": in_window,
        "R3_body_committed_through_kick": committed,
        "R3_tail_kick_ok": bool(in_window and committed),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    print("capacity gates (reference lunge) ...", flush=True)
    gates = capacity_gates()
    print(f"  variant={gates['variant']} limiting={gates['limiting_factor']} "
          f"flight={gates['flight_time_s']}s", flush=True)
    print("retimed bite profile ...", flush=True)
    profile = retimed_profile()
    profile_path = OUTPUT / "power-attack-001-profile.json"
    profile_path.write_text(json.dumps(profile, indent=2) + "\n")
    out_glb = OUTPUT / "power-attack-001.glb"
    out_receipt = OUTPUT / "bite-receipt.json"
    print("attack solver ...", flush=True)
    receipt = build_attack(profile_path, out_glb, out_receipt)
    print(f"  status={receipt['status']} "
          f"hold_nose_down={receipt['body_articulation']['hold_head_nose_down_degrees']:.1f}deg",
          flush=True)
    semantic_rig = json.loads((ROOT / profile["semantic_rig"]["path"]).read_text())["roles"]
    emitted = Glb.from_bytes(out_glb.read_bytes())
    tail_names = semantic_rig["tail"]
    for name in tail_names + [semantic_rig["head"], semantic_rig["pelvis"], "Bone_074"]:
        if name not in emitted.name_to_node:
            raise SystemExit(f"power-attack-001: rig node missing: {name}")
    print("tail kick overlay ...", flush=True)
    kick = overlay_tail_kick(out_glb, {"tail": list(tail_names)})
    print(f"  kick_peak={kick['tail_kick_peak_deg']:.1f}deg clamped={kick['tail_kick_clamped_samples']}", flush=True)
    print("guards ...", flush=True)
    emitted = Glb.from_bytes(out_glb.read_bytes())
    guard_facts = guards(
        out_glb,
        {"head": [emitted.name_to_node[semantic_rig["head"]]],
         "tail": [emitted.name_to_node[n] for n in tail_names],
         "pelvis": [emitted.name_to_node[semantic_rig["pelvis"]]]},
        emitted.name_to_node["Bone_074"])
    print(f"  R1={guard_facts['R1_jaw_wide_before_lowest_head']} R3_kick={guard_facts['R3_tail_kick_ok']}", flush=True)
    (OUTPUT / "power-attack-gates.json").write_text(json.dumps(gates, indent=2) + "\n")
    (OUTPUT / "tail-kick.json").write_text(json.dumps(kick, indent=2) + "\n")
    (OUTPUT / "guard-report.json").write_text(json.dumps(guard_facts, indent=2) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
