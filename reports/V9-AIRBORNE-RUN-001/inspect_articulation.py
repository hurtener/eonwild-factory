"""Exact emitted knee-branch, angle, rate, and recovery-region witnesses."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices


def inspect(path, roles):
    glb = Glb(path)
    clip = glb.document["animations"][0]["name"]
    tracks, times = _clip_state(glb, clip)
    worlds = [_world_matrices(glb, *_pose(glb, tracks, i)) for i in range(len(times))]
    root = glb.name_to_node[roles["root"]]
    forward = np.asarray([worlds[-1][root][a][3] - worlds[0][root][a][3] for a in range(3)])
    forward[1] = 0
    forward /= np.linalg.norm(forward)
    lateral = np.cross([0, 1, 0], forward)
    output = {"path": str(path), "sample_count": len(times), "per_side": {}}
    for side in ("left", "right"):
        names = roles["legs"][side]["contactChain"]
        nodes = [glb.name_to_node[n] for n in names]
        positions = np.asarray([[[w[n][a][3] for a in range(3)] for n in nodes] for w in worlds])
        upper, lower, distal = np.diff(positions, axis=1).transpose(1, 0, 2)
        sign = np.cross(upper, lower) @ lateral
        hip_angles = np.degrees(np.arctan2(upper @ forward, -upper[:, 1]))
        def interior(a, b):
            return np.degrees(np.arccos(np.clip(np.sum(a * b, axis=1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)), -1, 1)))
        knee_angles = interior(-upper, lower)
        ankle_angles = interior(-lower, distal)
        rates = {}
        for role, name in zip(("hip", "knee", "ankle"), names):
            q = np.asarray(tracks[name, "rotation"])
            q /= np.linalg.norm(q, axis=1)[:, None]
            deltas = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(q[:-1] * q[1:], axis=1)), -1, 1)))
            index = int(deltas.argmax())
            rates[role] = {"max_step_degrees": float(deltas[index]), "maximum_angular_velocity_degrees_per_s": float(np.max(deltas / np.diff(times))), "peak_time_s": [times[index], times[index + 1]], "cyclic_rotation_seam_degrees": float(np.degrees(2 * np.arccos(np.clip(abs(q[0] @ q[-1]), -1, 1))))}
        output["per_side"][side] = {"bend_sign_minimum": float(sign.min()), "bend_sign_flip_count": int(np.sum(sign[:-1] * sign[1:] < 0)), "hip_sagittal_degrees": [float(hip_angles.min()), float(hip_angles.max())], "knee_interior_degrees": [float(knee_angles.min()), float(knee_angles.max())], "ankle_interior_degrees": [float(ankle_angles.min()), float(ankle_angles.max())], "maximum_knee_lateral_offset_from_hip_m": float(np.max(np.abs(upper @ lateral))), "rotation_rates": rates, "frames": [{"time_s": float(t), "points": positions[i].tolist(), "hip_sagittal_degrees": float(hip_angles[i]), "knee_interior_degrees": float(knee_angles[i]), "ankle_interior_degrees": float(ankle_angles[i]), "bend_sign": float(sign[i])} for i, t in enumerate(times)]}
    receipt = path.parent / "solve-receipt.json"
    if receipt.exists():
        rows = json.loads(receipt.read_text())["emitted_proxy_samples"]
        output["selected_pitch_continuity"] = {}
        for side in ("left", "right"):
            if "solved_foot_pitch_degrees" in rows[0]["feet"][side]:
                values = np.asarray([r["feet"][side]["solved_foot_pitch_degrees"] for r in rows])
                output["selected_pitch_continuity"][side] = {"maximum_sample_jump_degrees": float(np.abs(np.diff(values)).max()), "cyclic_seam_degrees": float(abs(values[-1] - values[0]))}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.artifact, json.loads(args.binding.read_text())["roles"])
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({**result, "per_side": {s: {k: v for k, v in side.items() if k != "frames"} for s, side in result["per_side"].items()}}, indent=2))
