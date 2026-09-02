"""Reopened jaw-only mutation, exact non-jaw identity and loop/rate witnesses."""
import hashlib
import json
from pathlib import Path

import numpy as np

from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices
from eonwild_motion.planning.airborne_gait import load_airborne_gait, jaw_breathing_angle

ROOT = Path(__file__).resolve().parents[3]
ROLES = json.loads((ROOT / "profiles/v9/rig.airborne-jaw-breathing.json").read_text())["roles"]
CASES = (
    ("Run010", "build/V9-AIRBORNE-RUN-001/iteration-009-tail-compensation/candidate", "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate"),
    ("Sprint006", "build/V9-AIRBORNE-SPRINT-001/review-candidate-005/candidate", "build/V9-AIRBORNE-SPRINT-001/review-candidate-006/candidate"),
)


def validate():
    output = []
    for label, before, after in CASES:
        bpath, apath = ROOT / before, ROOT / after
        b = Glb(bpath / "airborne-run-root_motion.glb")
        a = Glb(apath / "airborne-run-root_motion.glb")
        bt, times = _clip_state(b, b.document["animations"][0]["name"])
        at, atimes = _clip_state(a, a.document["animations"][0]["name"])
        assert times == atimes and bt.keys() == at.keys()
        jaw = ROLES["jaw_lower"]
        for key, values in bt.items():
            if key != (jaw, "rotation"):
                assert values == at[key], key
        bp = json.loads((bpath / "engineering-profile.json").read_text())["parameters"]
        ap = json.loads((apath / "engineering-profile.json").read_text())
        assert bp == {k: v for k, v in ap["parameters"].items() if not k.startswith("jaw_breathing_")}
        gait = load_airborne_gait(ap)
        qa, qb = np.array(at[jaw, "rotation"]), np.array(bt[jaw, "rotation"])
        qa /= np.linalg.norm(qa, axis=1)[:, None]
        qb /= np.linalg.norm(qb, axis=1)[:, None]
        angles = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(qa * qb, axis=1)), -1, 1)))
        expected = np.array([jaw_breathing_angle(gait, t) for t in times])
        assert np.abs(angles - expected).max() < 1e-4
        steps = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(qa[:-1] * qa[1:], axis=1)), -1, 1)))
        seam = float(np.degrees(2 * np.arccos(np.clip(abs(qa[0] @ qa[-1]), -1, 1))))
        assert seam < 1e-4
        max_rate = float(np.max(steps / np.diff(times)))
        assert max_rate < 10
        names = [ROLES["root"], ROLES["pelvis"], *ROLES["tail"]] + [n for side in ROLES["legs"].values() for n in side["contactChain"]]
        world_difference = 0.
        for i, _ in enumerate(times):
            bw = np.array(_world_matrices(b, *_pose(b, bt, i)))
            aw = np.array(_world_matrices(a, *_pose(a, at, i)))
            for name in names:
                world_difference = max(world_difference, float(np.abs(bw[b.name_to_node[name]] - aw[a.name_to_node[name]]).max()))
        assert world_difference == 0
        result = {"label": label, "before": before, "after": after, "status": "PASS_JAW_ONLY_IDENTITY_AND_LOOP", "all_non_jaw_channels_identical": True, "sample_times_identical": True, "maximum_root_leg_tail_world_matrix_difference": world_difference, "jaw_opening_degrees_range": [float(angles.min()), float(angles.max())], "maximum_jaw_rate_degrees_per_s": max_rate, "jaw_rotation_seam_degrees": seam, "duration_s": times[-1] - times[0], "hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in apath.glob("*.glb")}}
        output.append(result)
    return output


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
