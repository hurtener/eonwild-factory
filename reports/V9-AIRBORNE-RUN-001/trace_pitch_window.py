"""Trace exact free-swing pitch feasibility around a fixed distal centroid.

Valid only where digit contact lock is zero: rotate the emitted ankle/foot
about their emitted toe centroid, retaining all segment lengths and toe shape.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from eonwild_motion.planning.airborne_gait import load_airborne_gait, sample_airborne_gait
from eonwild_motion.solve.airborne_gait import stable_knee_geometry, _interior, _qrotate, _qrotvec

parser = argparse.ArgumentParser()
parser.add_argument("--iteration", type=Path, required=True)
parser.add_argument("--profile", type=Path, required=True)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--source-clip", required=True)
parser.add_argument("--binding", type=Path, required=True)
parser.add_argument("--forward-phase-bias", type=float, default=0.0)
parser.add_argument("--clearance-reduction", type=float, default=0.0)
parser.add_argument("--output", type=Path)
parser.add_argument("--all-free-swing", action="store_true")
args = parser.parse_args()
gait = load_airborne_gait(json.loads(args.profile.read_text()))
roles = json.loads(args.binding.read_text())["roles"]
source = Glb(args.source)
tracks, _ = _clip_state(source, args.source_clip)
worlds = _world_matrices(source, *_pose(source, tracks, 0))
normal = {}
for side in ("left", "right"):
    h, k, a = [np.asarray(_world_position(worlds[source.name_to_node[n]])) for n in roles["legs"][side]["contactChain"][:3]]
    normal[side] = np.cross(k - h, a - k)
    normal[side] /= np.linalg.norm(normal[side])
receipt = json.loads((args.iteration / "solve-receipt.json").read_text())
diagnostics = json.loads((args.iteration / "articulation-diagnostics.json").read_text())
forward, up = np.asarray(receipt["forward_axis"]), np.asarray(receipt["up_axis"])
lateral = np.cross(up, forward)
output = []
for side in (("left", "right") if args.all_free_swing else ("left",)):
    for row, emitted in zip(diagnostics["per_side"][side]["frames"], receipt["emitted_proxy_samples"]):
        t = row["time_s"]
        phase = sample_airborne_gait(gait, t, receipt["body_height_m"])["feet"][side]["swing_phase"]
        if args.all_free_swing:
            if not .18 < phase < .82:
                continue
        elif not .74 <= t <= .91:
            continue
        assert .18 < phase < .82
        hip, knee, ankle, foot = np.asarray(row["points"])
        pivot = np.asarray(emitted["feet"][side]["distal_contact_centroid_m"])
        shift = forward * (2 * gait.step_length_body_heights * receipt["body_height_m"] * args.forward_phase_bias * 64 * phase ** 3 * (1 - phase) ** 3) - up * (args.clearance_reduction * receipt["body_height_m"])
        current_pitch = emitted["feet"][side]["solved_foot_pitch_degrees"]
        feasible = []
        poses = []
        for pitch in np.arange(-45., 85.0001, .25):
            q = _qrotvec(lateral * np.radians(pitch - current_pitch))
            a = pivot + shift + _qrotate(q, ankle - pivot)
            f = pivot + shift + _qrotate(q, foot - pivot)
            k, end, extension = stable_knee_geometry(hip, a, np.linalg.norm(knee - hip), np.linalg.norm(ankle - knee), normal[side])
            hip_angle = np.degrees(np.arctan2((k - hip) @ forward, -(k - hip) @ up))
            knee_angle, ankle_angle = _interior(hip - k, end - k), _interior(k - end, f - end)
            # Match the existing numerical envelope residual budget explicitly.
            if extension < 1e-6 and -gait.hip_extension_limit_degrees - .1 <= hip_angle <= gait.hip_flexion_limit_degrees + .1 and gait.knee_min_interior_degrees - .1 <= knee_angle <= gait.knee_max_interior_degrees + .1 and gait.ankle_min_interior_degrees - .1 <= ankle_angle <= gait.ankle_max_interior_degrees + .1:
                feasible.append(float(pitch))
                if pitch % 10 == 0:
                    poses.append({"pitch": float(pitch), "hip": float(hip_angle), "knee": knee_angle, "ankle": ankle_angle})
        groups = []
        for pitch in feasible:
            if groups and pitch - groups[-1][1] < .251:
                groups[-1][1] = pitch
            else:
                groups.append([pitch, pitch])
        output.append({"side": side, "time_s": t, "selected_pitch_degrees": current_pitch, "feasible_pitch_intervals_degrees": groups, "feasible_pose_probes": poses})
result = {"classification": "free-swing centroid-preserving geometry; 0.25 degree sampling, 0.1 degree numerical envelope tolerance", "samples": output}
(args.output or args.iteration / "pitch-feasibility-window.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
