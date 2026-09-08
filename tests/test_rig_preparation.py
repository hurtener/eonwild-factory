from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.rig_preparation import prepare_rig
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/sha256/2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f.glb"


def config(source: Glb) -> dict:
    return {
        "schema": "eonwild.motion.rig-preparation.v1",
        "id": "renamed-fixture.v1",
        "source_sha256": hashlib.sha256(source.raw).hexdigest(),
        "skin_index": 0,
        "coordinate": {"frame": "source_world", "lateral": [1, 0, 0],
                       "up": [0, 1, 0], "forward": [0, 0, 1]},
        "reparents": [{"node": "Bone_011", "new_parent": "Bone_003"}],
        "pivot_relocations": [{
            "node": "Bone_010", "world_origin_m": [-0.38, 1.4, 0.72],
            "basis": "measured_source_world",
        }],
        "articulations": [{
            "role": "jaw_lower", "node": "Bone_074", "parent": "Bone_035",
            "descendants": ["Bone_073"], "axis": [1.0, 0.0, 0.0],
            "axis_frame": "joint_parent_local",
        }],
        "evidence": [{"kind": "fixture", "reference": "test", "claim": "test"}],
        "limitations": ["fixture only"],
    }


def test_real_full_weight_source_reparents_relocates_and_preserves_neutral_skin():
    source = Glb(SOURCE)
    raw, receipt = prepare_rig(source, config(source))
    reopened = Glb.from_bytes(raw)
    assert receipt["animations"] == 0
    assert receipt["measurements"]["maximum_reopened_neutral_skin_error_m"] < 3e-6
    worlds = np.asarray(_world_matrices(
        reopened, reopened.rest_translation, reopened.rest_rotation, reopened.rest_scale))
    assert np.allclose(worlds[reopened.name_to_node["Bone_010"]][:3, 3],
                       [-0.38, 1.4, 0.72], atol=3e-6, rtol=0)
    assert reopened.node_parent_name("Bone_011") == "Bone_003"
    assert not reopened.document.get("animations")


@pytest.mark.parametrize("case", ["hash", "cycle", "nonfinite", "jaw_branch", "axes"])
def test_preparation_rejects_unbound_or_malformed_operations(case):
    source = Glb(SOURCE)
    candidate = config(source)
    if case == "hash":
        candidate["source_sha256"] = "0" * 64
    elif case == "cycle":
        candidate["reparents"] = [{"node": "Bone_001", "new_parent": "Bone_011"}]
    elif case == "nonfinite":
        candidate["pivot_relocations"][0]["world_origin_m"][1] = float("nan")
    elif case == "jaw_branch":
        candidate["articulations"][0]["descendants"] = ["Bone_011"]
    else:
        candidate["coordinate"]["forward"] = [1, 0, 0]
    with pytest.raises(ContractError):
        prepare_rig(source, candidate)


def test_preparation_is_deterministic_and_config_bound():
    source = Glb(SOURCE)
    first, a = prepare_rig(source, config(source))
    second, b = prepare_rig(Glb(SOURCE), deepcopy(config(source)))
    assert first == second
    assert a == b
    changed = config(source)
    changed["limitations"].append("changed declaration")
    altered, c = prepare_rig(source, changed)
    assert altered != first
    assert c["config_sha256"] != a["config_sha256"]
