from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from eonwild_motion.factory.source import _skin_reconstruction_error
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.airborne_gait import _qmul, _qrotvec
from eonwild_motion.solve.skin_rig import SkinRig


ROOT = Path(__file__).resolve().parents[1]
SHA = "3613b67c9513c4ed5b88665c7606e0c15791bb922b01a72e7223aa112546ec89"
SOURCE = ROOT / f"assets/sha256/{SHA}.glb"


def _inputs():
    source = Glb(SOURCE)
    roles = json.loads(
        (ROOT / "catalog/rigs/allosaurus-engineering.v2.json").read_text()
    )["roles"]
    contact = json.loads(
        (ROOT / "catalog/contacts/allosaurus-engineering.v2.json").read_text()
    )
    return source, roles, contact


def test_allosaurus_pedal_source_is_bound_and_neutral_surface_is_preserved():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
    source, roles, contact = _inputs()
    error, count = _skin_reconstruction_error(source, skin_index=0, mesh_node=48)
    assert count == 40105
    assert error < 3e-6
    rig = SkinRig(source, roles, [0, 0, 1], [0, 1, 0], contact)
    assert np.max(np.abs(rig.skin(rig.neutral_world) - rig.positions[:, :3])) < 3e-6


def test_allosaurus_three_pedal_branches_are_real_deformers_and_all_flex():
    source, roles, contact = _inputs()
    rig = SkinRig(source, roles, [0, 0, 1], [0, 1, 0], contact)
    skin_joints = set(source.document["skins"][0]["joints"])
    neutral = rig.skin(rig.neutral_world)
    translations = [np.asarray(value, dtype=float).copy() for value in source.rest_translation]
    rotations = [np.asarray(value, dtype=float).copy() for value in source.rest_rotation]
    scales = [np.asarray(value, dtype=float).copy() for value in source.rest_scale]
    branch_results = []
    for side in ("left", "right"):
        chains = roles["legs"][side]["toeChains"]
        assert len(chains) == 3
        for chain in chains:
            assert len(chain) == 3
            assert source.name_to_node[chain[0]] in skin_joints
            assert source.name_to_node[chain[1]] in skin_joints
            assert source.name_to_node[chain[2]] not in skin_joints
            for index, name in enumerate(chain):
                node = source.name_to_node[name]
                flex = 8.0 * (0.45 if index == 0 else 0.275)
                rotations[node] = _qmul(
                    tuple(rotations[node]), _qrotvec((math.radians(flex), 0.0, 0.0))
                )
            slots = [
                list(source.document["skins"][0]["joints"]).index(
                    source.name_to_node[name]
                )
                for name in chain[:2]
            ]
            ownership = np.where(np.isin(rig.ids, slots), rig.weights, 0.0).sum(axis=1)
            branch_results.append(np.flatnonzero(ownership > 0.05))
    posed = rig.skin(rig.world(translations, rotations, scales))
    displacement = np.linalg.norm(posed - neutral, axis=1)
    for indices in branch_results:
        assert len(indices) > 20
        assert float(np.max(displacement[indices])) > 1e-3


def test_canonical_failed_plantar_vertices_move_to_declared_side_branches():
    source, _, _ = _inputs()
    primitive = source.document["meshes"][0]["primitives"][0]
    attributes = primitive["attributes"]
    joint_rows = np.concatenate(
        [np.asarray(source.accessor_values(attributes[f"JOINTS_{index}"]), dtype=int)
         for index in range(2)], axis=1)
    weight_rows = np.concatenate(
        [np.asarray(source.accessor_values(attributes[f"WEIGHTS_{index}"]), dtype=float)
         for index in range(2)], axis=1)
    joints = source.document["skins"][0]["joints"]
    expected = {
        25268: "Outer",
        25298: "Outer",
        25586: "Inner",
    }
    for vertex, branch in expected.items():
        slots = [
            joints.index(source.name_to_node[f"AllosaurusPedal{branch}{part}.R"])
            for part in ("Proximal", "Distal")
        ]
        assert float(weight_rows[vertex][np.isin(joint_rows[vertex], slots)].sum()) > 0.9
        assert math.isclose(float(weight_rows[vertex].sum()), 1.0, abs_tol=1e-6)
