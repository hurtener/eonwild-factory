"""Compare exact emitted transforms after a numerical solver correction."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position

parser = argparse.ArgumentParser()
parser.add_argument("--before", type=Path, required=True)
parser.add_argument("--after", type=Path, required=True)
parser.add_argument("--binding", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
roles = json.loads(args.binding.read_text())["roles"]
before, after = Glb(args.before), Glb(args.after)
bt, times = _clip_state(before, before.document["animations"][0]["name"])
at, new_times = _clip_state(after, after.document["animations"][0]["name"])
assert times == new_times and bt.keys() == at.keys()
rotations, translations = {}, {}
for key in bt:
    b, a = np.asarray(bt[key], dtype=float), np.asarray(at[key], dtype=float)
    if key[1] == "rotation":
        b /= np.linalg.norm(b, axis=1)[:, None]
        a /= np.linalg.norm(a, axis=1)[:, None]
        delta = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(b * a, axis=1)), -1, 1)))
        peak = int(delta.argmax())
        rotations[key[0]] = {"maximum_degrees": float(delta[peak]), "time_s": times[peak]}
    elif key[1] == "translation":
        translations[key[0]] = float(np.linalg.norm(b - a, axis=1).max())
nodes = [name for side in ("left", "right") for name in roles["legs"][side]["contactChain"] + [n for chain in roles["legs"][side]["toeChains"] for n in chain]]
max_position = {"distance_m": 0.0}
for index, time in enumerate(times):
    bw, aw = _world_matrices(before, *_pose(before, bt, index)), _world_matrices(after, *_pose(after, at, index))
    for name in nodes:
        distance = float(np.linalg.norm(np.asarray(_world_position(bw[before.name_to_node[name]])) - _world_position(aw[after.name_to_node[name]])))
        if distance > max_position["distance_m"]:
            max_position = {"distance_m": distance, "node": name, "time_s": time}
worst = max(rotations, key=lambda n: rotations[n]["maximum_degrees"])
result = {"before": str(args.before), "after": str(args.after), "sample_times_identical": True, "all_translation_channels_identical": max(translations.values()) == 0, "maximum_local_rotation_change": {"node": worst, **rotations[worst]}, "maximum_semantic_leg_joint_position_change": max_position, "per_semantic_contact_joint_rotation_change": {side: {name: rotations[name] for name in roles["legs"][side]["contactChain"]} for side in ("left", "right")}}
args.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
