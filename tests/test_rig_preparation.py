from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import struct

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.rig_preparation import prepare_rig
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.whole_body_gait_transition import _encode


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
        "weight_transfers": [],
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


def test_legacy_preparation_without_scale_policy_preserves_exact_bytes():
    source = Glb(SOURCE)
    raw, _ = prepare_rig(source, config(source))
    assert hashlib.sha256(raw).hexdigest() == (
        "5404d81a401b385cec6ae458c1e211734892299f884373d5102a7a4449164832"
    )


def test_preparation_rejects_noncanonical_input_skin():
    source = Glb(SOURCE)
    inverse = source.document["skins"][0]["inverseBindMatrices"]
    offset, _, _ = source.accessor_region(inverse)
    raw = bytearray(source.raw)
    # Column-major MAT4 translation x is element 12.
    value_offset = source.bin_start + offset + 12 * 4
    value = struct.unpack_from("<f", raw, value_offset)[0]
    struct.pack_into("<f", raw, value_offset, value + 0.01)
    changed = Glb.from_bytes(bytes(raw))
    changed_config = config(changed)
    with pytest.raises(ContractError, match="not canonical POSITION"):
        prepare_rig(changed, changed_config)


def test_preparation_rejects_multiple_skins_before_mutation():
    source = Glb(SOURCE)
    document = deepcopy(source.document)
    document["skins"].append(deepcopy(document["skins"][0]))
    changed = Glb.from_bytes(_encode(document, source.binary))
    with pytest.raises(ContractError, match="exactly one skin"):
        prepare_rig(changed, config(changed))


def test_preparation_transfers_selected_branch_weights_and_preserves_neutral_skin():
    source = Glb(SOURCE)
    candidate = config(source)
    candidate["weight_transfers"] = [{
        "role": "upper_head",
        "from_articulation": "jaw_lower",
        "to_node": "Bone_035",
        "selector": {
            "frame": "source_world",
            "halfspaces": [{"normal": [0, 1, 0], "minimum_dot_m": -1000.0}],
        },
    }]
    raw, receipt = prepare_rig(source, candidate)
    assert receipt["weight_transfers"][0]["changed_vertex_count"] > 0
    assert receipt["measurements"]["maximum_reopened_neutral_skin_error_m"] < 3e-6
    reopened = Glb.from_bytes(raw)
    assert reopened.document.get("animations") is None
    primitive = reopened.document["meshes"][0]["primitives"][0]
    for suffix in ("0", "1"):
        joints = np.asarray(reopened.accessor_values(
            primitive["attributes"][f"JOINTS_{suffix}"]))
        weights = np.asarray(reopened.accessor_values(
            primitive["attributes"][f"WEIGHTS_{suffix}"]))
        assert np.all(joints[weights == 0] == 0)


def test_preparation_rejects_duplicate_articulation_node():
    source = Glb(SOURCE)
    candidate = config(source)
    duplicate = deepcopy(candidate["articulations"][0])
    duplicate["role"] = "second_role"
    duplicate["axis"] = [-1.0, 0.0, 0.0]
    candidate["articulations"].append(duplicate)
    with pytest.raises(ContractError, match="roles and nodes"):
        prepare_rig(source, candidate)


def test_preparation_adds_non_skinned_semantic_endpoint_and_preserves_surface():
    source = Glb(SOURCE)
    candidate = config(source)
    candidate["endpoints"] = [{
        "name": "renamed_toe_endpoint",
        "parent": "Bone_042",
        "world_origin_m": [2.1, 0.05, 0.3],
        "basis": "measured_source_world",
    }]
    raw, receipt = prepare_rig(source, candidate)
    reopened = Glb.from_bytes(raw)
    assert reopened.node_parent_name("renamed_toe_endpoint") == "Bone_042"
    worlds = np.asarray(_world_matrices(
        reopened, reopened.rest_translation,
        reopened.rest_rotation, reopened.rest_scale,
    ))
    assert np.allclose(
        worlds[reopened.name_to_node["renamed_toe_endpoint"]][:3, 3],
        [2.1, 0.05, 0.3], atol=3e-6, rtol=0,
    )
    assert reopened.name_to_node["renamed_toe_endpoint"] not in (
        reopened.document["skins"][0]["joints"]
    )
    assert receipt["added_endpoints"] == [{
        "name": "renamed_toe_endpoint",
        "parent": "Bone_042",
        "world_origin_m": [2.1, 0.05, 0.3],
        "skin_influence": False,
    }]
    assert receipt["measurements"]["maximum_reopened_neutral_skin_error_m"] < 3e-6


def _weighted_branch(source: Glb, suffix: str = "A") -> dict:
    worlds = np.asarray(_world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale))
    origin = worlds[source.name_to_node["Bone_042"]][:3, 3]
    return {
        "role": f"fixture_branch_{suffix}",
        "parent": "Bone_042",
        "source_nodes": ["Bone_042"],
        "proximal": {"name": f"fixture_proximal_{suffix}",
                     "world_origin_m": origin.tolist(), "basis": "measured_source_world"},
        "distal": {"name": f"fixture_distal_{suffix}",
                   "world_origin_m": (origin + [0, 0, .05]).tolist(),
                   "basis": "measured_source_world"},
        "endpoint": {"name": f"fixture_endpoint_{suffix}",
                     "world_origin_m": (origin + [0, 0, .1]).tolist(),
                     "basis": "measured_source_world"},
        "selector": {"frame": "source_world", "lateral_interval_m": [-1000, 1000],
                     "up_maximum_m": 1000, "forward_interval_m": [-1000, 1000],
                     "blend_width_m": 1},
    }


def test_preparation_adds_weighted_branch_and_preserves_neutral_skin():
    source = Glb(SOURCE)
    candidate = config(source)
    candidate["weighted_branches"] = [_weighted_branch(source)]
    raw, receipt = prepare_rig(source, candidate)
    reopened = Glb.from_bytes(raw)
    skin = reopened.document["skins"][0]
    for name in ("fixture_proximal_A", "fixture_distal_A"):
        assert reopened.name_to_node[name] in skin["joints"]
    assert reopened.name_to_node["fixture_endpoint_A"] not in skin["joints"]
    assert receipt["weighted_branches"][0]["changed_vertex_count"] > 0
    assert receipt["joint_count"] == len(source.document["skins"][0]["joints"]) + 2
    assert receipt["measurements"]["maximum_reopened_neutral_skin_error_m"] < 3e-6


def test_preparation_rejects_overlapping_weighted_branch_ownership():
    source = Glb(SOURCE)
    candidate = config(source)
    candidate["weighted_branches"] = [
        _weighted_branch(source, "A"), _weighted_branch(source, "B")]
    with pytest.raises(ContractError, match="selectors overlap"):
        prepare_rig(source, candidate)


@pytest.mark.parametrize("case", ["name", "parent", "origin", "basis"])
def test_preparation_rejects_malformed_semantic_endpoint(case):
    source = Glb(SOURCE)
    candidate = config(source)
    endpoint = {
        "name": "renamed_toe_endpoint",
        "parent": "Bone_042",
        "world_origin_m": [2.1, 0.05, 0.3],
        "basis": "measured_source_world",
    }
    candidate["endpoints"] = [endpoint]
    if case == "name":
        endpoint["name"] = "Bone_042"
    elif case == "parent":
        endpoint["parent"] = "missing"
    elif case == "origin":
        endpoint["world_origin_m"][0] = float("nan")
    else:
        endpoint["basis"] = "guessed"
    with pytest.raises(ContractError):
        prepare_rig(source, candidate)


@pytest.mark.parametrize(
    "policy",
    [
        {"maximum_axis_spread": 1e-5, "maximum_unit_deviation": 1e-5},
        {"maximum_axis_spread": 1e-6, "maximum_unit_deviation": 1e-5, "target": "unit"},
        {"maximum_axis_spread": True, "maximum_unit_deviation": 1e-5, "target": "unit"},
        {"maximum_axis_spread": 1e-5, "maximum_unit_deviation": 1e-5, "target": "source"},
    ],
)
def test_preparation_rejects_malformed_near_uniform_scale_policy(policy):
    source = Glb(SOURCE)
    candidate = config(source)
    candidate["near_uniform_scale_normalization"] = policy
    with pytest.raises(ContractError, match="near-uniform scale normalization"):
        prepare_rig(source, candidate)
