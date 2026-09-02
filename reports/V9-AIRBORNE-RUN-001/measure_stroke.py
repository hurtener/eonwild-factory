"""Measure emitted foot stroke and same-frame split in a common body carrier."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices


def measure(path, roles):
    glb = Glb(path)
    clip = glb.document["animations"][0]["name"]
    tracks, times = _clip_state(glb, clip)
    root = glb.name_to_node[roles["root"]]
    worlds = [_world_matrices(glb, *_pose(glb, tracks, i)) for i in range(len(times))]
    root_positions = np.asarray([[w[root][a][3] for a in range(3)] for w in worlds])
    forward = root_positions[-1] - root_positions[0]
    forward[1] = 0
    forward /= np.linalg.norm(forward)
    tips = {s: [glb.name_to_node[chain[-1]] for chain in roles["legs"][s]["toeChains"]] for s in ("left", "right")}
    positions = {s: np.asarray([np.mean([[w[n][a][3] for a in range(3)] for n in nodes], axis=0) for w in worlds]) for s, nodes in tips.items()}
    # Exact full skin body extent at frame0 using all combined influences.
    mesh = glb.document["meshes"][0]["primitives"][0]["attributes"]
    pos = np.c_[np.asarray(glb.accessor_values(mesh["POSITION"])), np.ones(len(glb.accessor_values(mesh["POSITION"])))]
    skin = glb.document["skins"][0]
    inv = np.asarray(glb.accessor_values(skin["inverseBindMatrices"])).reshape(-1, 4, 4).transpose(0, 2, 1)
    matrices = np.asarray([worlds[0][i] for i in skin["joints"]]) @ inv
    skinned = np.zeros((len(pos), 4))
    total = np.zeros(len(pos))
    for key in sorted(k for k in mesh if k.startswith("JOINTS_")):
        joints = np.asarray(glb.accessor_values(mesh[key]), dtype=int)
        weights = np.asarray(glb.accessor_values(mesh[key.replace("JOINTS_", "WEIGHTS_")]))
        for col in range(joints.shape[1]):
            skinned += np.einsum("nij,nj->ni", matrices[joints[:, col]], pos) * weights[:, col, None]
            total += weights[:, col]
    skinned /= total[:, None]
    projection = skinned[:, :3] @ forward
    body_length = float(projection.max() - projection.min())
    split = np.abs((positions["left"] - positions["right"]) @ forward)
    relative = {s: (p - root_positions) @ forward for s, p in positions.items()}
    hips = [glb.name_to_node[roles["legs"][s]["contactChain"][0]] for s in ("left", "right")]
    hip_positions = np.asarray([np.mean([[w[n][a][3] for a in range(3)] for n in hips], axis=0) for w in worlds])
    hip_relative = {s: (p - hip_positions) @ forward for s, p in positions.items()}
    peak = int(split.argmax())
    return {"path": str(path), "clip": clip, "duration_s": times[-1], "body_length_m_frame0": body_length, "maximum_same_frame_distal_toe_split_m": float(split.max()), "maximum_same_frame_split_body_lengths": float(split.max() / body_length), "split_peak_time_s": times[peak], "signed_hip_relative_reaches_at_split_peak_m": {s: float(p[peak]) for s, p in hip_relative.items()}, "root_travel_m": float(np.linalg.norm(root_positions[-1] - root_positions[0])), "root_relative_foot_stroke_m": {s: float(p.max() - p.min()) for s, p in relative.items()}, "root_relative_foot_stroke_body_lengths": {s: float((p.max() - p.min()) / body_length) for s, p in relative.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=Path, nargs="+")
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    roles = json.loads(args.binding.read_text())["roles"]
    report = [measure(path, roles) for path in args.paths]
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
