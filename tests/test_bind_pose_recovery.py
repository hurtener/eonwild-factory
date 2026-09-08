"""Adversarial bind-pose recovery tests on the production-shaped source."""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import struct

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.source import admit_geometry
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices, _world_position
from eonwild_motion.solve.whole_body_gait_transition import _encode


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb"
ROLES = json.loads((ROOT / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]


def recover(source: Glb, roles=ROLES):
    return admit_geometry(source, roles, forward_axis=(0, 0, 1), up_axis=(0, 1, 0),
                          recover_bind_pose=True, skin_index=0)


def mutate_inverse(source: Glb, transform) -> Glb:
    document = deepcopy(source.document)
    binary = bytearray(source.binary)
    accessor = int(document["skins"][0]["inverseBindMatrices"])
    offset, _, stride = source.accessor_region(accessor)
    row = np.asarray(source.accessor_values(accessor)[0], dtype=float).reshape(4, 4).T
    row = transform(row)
    struct.pack_into("<16f", binary, offset, *row.T.reshape(-1))
    return Glb.from_bytes(_encode(document, bytes(binary)))


def mutate_position(source: Glb, value: float) -> Glb:
    binary = bytearray(source.binary)
    position = source.document["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
    offset, _, _ = source.accessor_region(position)
    struct.pack_into("<f", binary, offset, value)
    return Glb.from_bytes(_encode(source.document, bytes(binary)))


def test_production_bind_recovery_is_deterministic_skin_aligned_and_bilateral():
    source = Glb(SOURCE)
    first, metadata = recover(source)
    second, repeated = recover(Glb(SOURCE))
    assert first == second
    assert metadata == repeated
    reopened = Glb.from_bytes(first)
    assert not reopened.document.get("animations")
    receipt = metadata["bind_pose_recovery"]
    assert receipt["method"] == "skin_bind_pose_from_inverse_bind_matrices.v1"
    assert receipt["joint_count"] == 75 and receipt["vertex_count"] == 59169
    assert receipt["measurements"]["maximum_reopened_world_matrix_error"] < 6e-7
    assert receipt["measurements"]["maximum_reopened_skin_position_error_m"] < 1.2e-6
    worlds = _world_matrices(reopened, reopened.rest_translation,
                             reopened.rest_rotation, reopened.rest_scale)
    points = {
        side: [np.asarray(_world_position(worlds[reopened.name_to_node[name]]))
               for name in ROLES["legs"][side]["contactChain"]]
        for side in ("left", "right")
    }
    plane = 0.5 * (points["left"][0][0] + points["right"][0][0])
    for left, right in zip(points["left"], points["right"]):
        reflected = left.copy()
        reflected[0] = 2 * plane - reflected[0]
        assert np.linalg.norm(right - reflected) < 5e-7


def test_recovery_handles_transformed_mesh_parent_and_renamed_semantics():
    source = Glb(SOURCE)
    document = deepcopy(source.document)
    parent = document["nodes"][77]
    parent["translation"] = [3.0, -2.0, 4.0]
    parent["rotation"] = [0.0, math.sin(0.31), 0.0, math.cos(0.31)]
    parent["scale"] = [1.4, 1.4, 1.4]
    renamed = deepcopy(ROLES)
    names = set()
    def collect(value):
        if isinstance(value, str):
            names.add(value)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    collect(renamed)
    replacements = {name: "renamed_" + name for name in names}
    for node in document["nodes"]:
        if node.get("name") in replacements:
            node["name"] = replacements[node["name"]]
    def rename(value):
        if isinstance(value, str):
            return replacements[value]
        if isinstance(value, dict):
            return {key: rename(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rename(item) for item in value]
        return value
    transformed = Glb.from_bytes(_encode(document, source.binary))
    raw, metadata = recover(transformed, rename(renamed))
    assert Glb.from_bytes(raw).document["extras"]["eonwildGeometry"]["forward_axis"] == [0.0, 0.0, 1.0]
    measured = metadata["bind_pose_recovery"]["measurements"]
    assert measured["maximum_reopened_world_matrix_error"] < 2e-6
    assert measured["maximum_reopened_skin_position_error_m"] < 3e-6


def test_recovery_ignores_animation_tracks_but_preserves_input_binary():
    source = Glb(SOURCE)
    animated_document = deepcopy(source.document)
    animated_document["animations"] = [{"name": "irrelevant", "channels": [], "samplers": []}]
    animated = Glb.from_bytes(_encode(animated_document, source.binary))
    plain, _ = recover(source)
    ignored, metadata = recover(animated)
    assert plain == ignored
    assert metadata["bind_pose_recovery"]["input_animation_tracks_used"] is False
    assert Glb.from_bytes(ignored).binary == source.binary


@pytest.mark.parametrize("case", ["singular", "shear"])
def test_recovery_rejects_malformed_inverse_bind(case):
    source = Glb(SOURCE)
    def change(matrix):
        if case == "singular":
            matrix[0, :3] = 0
        else:
            matrix[0, 1] += 0.01
        return matrix
    malformed = mutate_inverse(source, change)
    with pytest.raises(ContractError, match="singular|shear|projection"):
        recover(malformed)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_recovery_rejects_nonfinite_skin_positions(value):
    with pytest.raises(ContractError, match="POSITION|non-finite"):
        recover(mutate_position(Glb(SOURCE), value))


@pytest.mark.parametrize("case", [
    "boolean_joint", "fractional_joint", "negative_inverse_accessor",
    "boolean_position_accessor", "malformed_inverse_schema",
])
def test_recovery_rejects_nonexact_indices_and_accessor_schemas(case):
    source = Glb(SOURCE)
    document = deepcopy(source.document)
    if case == "boolean_joint":
        document["skins"][0]["joints"][1] = True
    elif case == "fractional_joint":
        document["skins"][0]["joints"][-1] = 74.5
    elif case == "negative_inverse_accessor":
        document["accessors"].append(deepcopy(document["accessors"][10]))
        document["skins"][0]["inverseBindMatrices"] = -1
    elif case == "boolean_position_accessor":
        document["meshes"][0]["primitives"][0]["attributes"]["POSITION"] = True
    else:
        document["accessors"][10]["type"] = "VEC4"
    with pytest.raises(ContractError, match="index|schema"):
        recover(Glb.from_bytes(_encode(document, source.binary)))


@pytest.mark.parametrize("translation", [[0.0, 0.0, 0.0], [0.1, -0.2, 0.05]])
def test_recovery_propagates_through_non_skin_joint_intermediary(translation):
    source = Glb(SOURCE)
    document = deepcopy(source.document)
    parent = source.name_to_node["Bone_043"]
    child = source.name_to_node["Bone_042"]
    helper = len(document["nodes"])
    document["nodes"][parent]["children"] = [
        helper if value == child else value
        for value in document["nodes"][parent]["children"]
    ]
    document["nodes"].append({
        "name": "semantic_agnostic_helper",
        "translation": translation,
        "children": [child],
    })
    old = document["nodes"][child].get("translation", [0.0, 0.0, 0.0])
    document["nodes"][child]["translation"] = [
        float(value - shift) for value, shift in zip(old, translation)
    ]
    raw, metadata = recover(Glb.from_bytes(_encode(document, source.binary)))
    assert metadata["bind_pose_recovery"]["measurements"][
        "maximum_reopened_skin_position_error_m"] < 3e-6
    assert len(Glb.from_bytes(raw).nodes) == len(source.nodes) + 1


def test_recovery_preserves_mesh_world_when_mesh_descends_from_recovered_joint():
    source = Glb(SOURCE)
    document = deepcopy(source.document)
    worlds = [np.asarray(value) for value in _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)]
    mesh = next(index for index, node in enumerate(source.nodes) if node.get("skin") == 0)
    old_parent = source.parents[mesh]
    new_parent = source.name_to_node["Bone_043"]
    document["nodes"][old_parent]["children"].remove(mesh)
    document["nodes"][new_parent].setdefault("children", []).append(mesh)
    local = np.linalg.solve(worlds[new_parent], worlds[mesh])
    scales = np.linalg.norm(local[:3, :3], axis=0)
    rotation = local[:3, :3] / scales
    rotation4 = np.eye(4)
    rotation4[:3, :3] = rotation
    from eonwild_motion.layers.leg_contact_resolve_v3 import _rotation_from_matrix
    document["nodes"][mesh]["translation"] = local[:3, 3].tolist()
    document["nodes"][mesh]["rotation"] = list(_rotation_from_matrix(
        tuple(tuple(float(value) for value in row) for row in rotation4)))
    document["nodes"][mesh]["scale"] = scales.tolist()
    raw, metadata = recover(Glb.from_bytes(_encode(document, source.binary)))
    assert metadata["bind_pose_recovery"]["measurements"][
        "maximum_reopened_skin_position_error_m"] < 3e-6
    reopened = Glb.from_bytes(raw)
    reopened_worlds = _world_matrices(
        reopened, reopened.rest_translation, reopened.rest_rotation, reopened.rest_scale)
    assert np.allclose(reopened_worlds[mesh], worlds[mesh], rtol=0, atol=2e-6)


def test_recovery_requires_explicit_mode_inputs_and_matching_semantics():
    source = Glb(SOURCE)
    with pytest.raises(ContractError, match="explicit forward"):
        admit_geometry(source, ROLES, recover_bind_pose=True, skin_index=0)
    with pytest.raises(ContractError, match="explicit skin index"):
        admit_geometry(source, ROLES, forward_axis=(0, 0, 1), recover_bind_pose=True)
    with pytest.raises(ContractError, match="cannot sample"):
        admit_geometry(source, ROLES, reference_clip="forged", forward_axis=(0, 0, 1),
                       recover_bind_pose=True, skin_index=0)
    forged = deepcopy(ROLES)
    forged["pelvis"] = "not_a_node"
    with pytest.raises(ContractError, match="unknown node"):
        recover(source, forged)
