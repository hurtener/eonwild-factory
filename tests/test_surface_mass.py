from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.dynamics.surface_mass import (
    SCHEMA,
    COORDINATES,
    _vertex_area_weights,
    prepare_surface_mass_proxy,
    prepare_surface_mass_vertex_evaluator,
    surface_mass_body_state,
    surface_mass_centroid,
    surface_mass_interval_momentum,
    surface_mass_vertex_state,
)
from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import apply_uniform_geometry_scale, load_animal_instance
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices


ROOT = Path(__file__).parents[1]


def profile() -> dict:
    return {
        "schema": SCHEMA,
        "instance_uniform_scale": 1.0,
        "mass_model": {"total_mass_kg": 100.0},
        "bindings": [
            {
                "node": "a",
                "mass_fraction": 0.25,
                "bind_world_determinant_scale": 1.0,
                "bind_world_gram_matrix": np.eye(3).tolist(),
                "com_local_m": [1, 0, 0],
                "allocation_point_mass_inertia_tensor_fraction_m2": np.diag([0.25, 0.5, 0.75]).tolist(),
            },
            {
                "node": "b",
                "mass_fraction": 0.75,
                "bind_world_determinant_scale": 1.0,
                "bind_world_gram_matrix": np.eye(3).tolist(),
                "com_local_m": [0, 2, 0],
                "allocation_point_mass_inertia_tensor_fraction_m2": np.diag([1.0, 1.5, 2.0]).tolist(),
            },
        ],
    }


def test_aggregate_centroid_uses_body_specific_joint_frames() -> None:
    identity = np.eye(4)
    moved = np.eye(4)
    moved[:3, 3] = (0, 0, 4)
    assert surface_mass_centroid(profile(), {"a": identity, "b": moved}) == pytest.approx(
        (0.25, 1.5, 3.0)
    )


def test_renamed_binding_has_same_numeric_result() -> None:
    original = profile()
    renamed = copy.deepcopy(original)
    renamed["bindings"][0]["node"] = "renamed_a"
    identity = np.eye(4)
    assert surface_mass_centroid(original, {"a": identity, "b": identity}) == pytest.approx(
        surface_mass_centroid(renamed, {"renamed_a": identity, "b": identity})
    )


def test_body_state_labels_per_joint_inertia_as_allocation_approximation() -> None:
    scaled = np.eye(4)
    scaled[:3, :3] *= 2.0
    value = profile()
    value["instance_uniform_scale"] = 2.0
    for binding in value["bindings"]:
        binding["bind_world_determinant_scale"] = 2.0
        binding["bind_world_gram_matrix"] = (4.0 * np.eye(3)).tolist()
    state = surface_mass_body_state(value, {"a": scaled, "b": scaled})
    assert state["total_mass_kg"] == 100.0
    assert [item["mass_kg"] for item in state["bindings"]] == pytest.approx([25.0, 75.0])
    assert np.allclose(
        state["bindings"][0]["allocation_world_inertia_about_com_kg_m2"],
        np.diag([25.0, 50.0, 75.0]),
    )
    assert state["bindings"][0]["exact_for_lbs_momentum"] is False


def test_interval_momentum_matches_uniform_translation() -> None:
    masses = np.asarray([20.0, 80.0])
    before = np.asarray([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    velocity = np.asarray([1.5, -0.25, 3.0])
    previous = {"vertex_mass_kg": masses, "world_positions_m": before}
    current = {"vertex_mass_kg": masses, "world_positions_m": before + 0.2 * velocity}
    result = surface_mass_interval_momentum(previous, current, 0.2)
    assert result["linear_momentum_kg_mps"] == pytest.approx(100.0 * velocity)
    assert result["centroidal_angular_momentum_kg_m2ps"] == pytest.approx((0.0, 0.0, 0.0))


@pytest.mark.parametrize("masses", [[0.0, 0.0], [-1.0, 2.0], [np.nan, 1.0], [np.inf, 1.0]])
def test_interval_momentum_rejects_invalid_particle_mass(masses) -> None:
    positions = np.zeros((2, 3))
    state = {"vertex_mass_kg": np.asarray(masses), "world_positions_m": positions}
    with pytest.raises(ContractError, match="incompatible"):
        surface_mass_interval_momentum(state, state, 0.1)


def test_area_lumped_rendered_centroid_is_subdivision_invariant() -> None:
    original = np.asarray([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    original_faces = np.asarray([[0, 1, 2]])
    midpoint = np.asarray([(original[0] + original[1]) / 2, (original[1] + original[2]) / 2, (original[2] + original[0]) / 2])
    subdivided = np.vstack((original, midpoint))
    subdivided_faces = np.asarray([[0, 3, 5], [3, 1, 4], [5, 4, 2], [3, 4, 5]])
    _, original_weights = _vertex_area_weights(original, original_faces)
    _, subdivided_weights = _vertex_area_weights(subdivided, subdivided_faces)
    assert np.average(original, axis=0, weights=original_weights) == pytest.approx(
        np.average(subdivided, axis=0, weights=subdivided_weights)
    )


@pytest.mark.parametrize(
    ("source_hash", "rig_path", "animal_path", "expected_mass", "expected_scale", "expected_topology"),
    [
        (
            "2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f",
            "catalog/rigs/heavy-biped.v9.json",
            "catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v2.json",
            2816.3,
            0.8595555137374769,
            (59169, 51123, 102258, 0, 0),
        ),
        (
            "4e7683a94a7bf3866fa6b453fe2147756ef42c11fe3b54e0f25e04db58f57964",
            "catalog/rigs/allosaurus-engineering.v2.json",
            "catalog/animals/allosaurus-composite-engineering.adult.v6.json",
            1512.0,
            1.985890232033453,
            (40105, 20300, 40538, 120, 46),
        ),
    ],
)
def test_exact_sources_match_compiler_scaled_full_lbs(
    source_hash: str,
    rig_path: str,
    animal_path: str,
    expected_mass: float,
    expected_scale: float,
    expected_topology: tuple[int, int, int, int, int],
) -> None:
    source_bytes = (ROOT / "assets" / "sha256" / f"{source_hash}.glb").read_bytes()
    rig_bytes = (ROOT / rig_path).read_bytes()
    animal_bytes = (ROOT / animal_path).read_bytes()
    profile_value, audit = prepare_surface_mass_proxy(
        source_bytes,
        rig_bytes,
        animal_bytes,
        source_sha256=source_hash,
        rig_sha256=hashlib.sha256(rig_bytes).hexdigest(),
        animal_sha256=hashlib.sha256(animal_bytes).hexdigest(),
        coordinate_system=COORDINATES,
    )
    replay_profile, replay_audit = prepare_surface_mass_proxy(
        source_bytes,
        rig_bytes,
        animal_bytes,
        source_sha256=source_hash,
        rig_sha256=hashlib.sha256(rig_bytes).hexdigest(),
        animal_sha256=hashlib.sha256(animal_bytes).hexdigest(),
        coordinate_system=COORDINATES,
    )
    assert replay_profile == profile_value
    assert replay_audit == audit
    assert profile_value["mass_model"]["total_mass_kg"] == expected_mass
    assert profile_value["instance_uniform_scale"] == pytest.approx(expected_scale, abs=1e-15)
    topology = audit["source_topology"]
    assert (
        topology["raw_vertex_count"],
        topology["welded_vertex_count"],
        topology["triangle_count"],
        topology["boundary_edge_count"],
        topology["nonmanifold_edge_count"],
    ) == expected_topology

    source = Glb.from_bytes(source_bytes)
    animal = load_animal_instance(json.loads(animal_bytes), source_sha256=source_hash)
    apply_uniform_geometry_scale(source, animal["uniform_scale"])
    worlds = _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale)
    named_worlds = {node.get("name", f"node:{index}"): worlds[index] for index, node in enumerate(source.nodes)}
    compact = surface_mass_body_state(profile_value, named_worlds)
    vertices = surface_mass_vertex_state(source_bytes, profile_value, named_worlds)
    prepared = prepare_surface_mass_vertex_evaluator(source_bytes, profile_value)
    cached_vertices = prepared(named_worlds)
    assert compact["com_m"] == pytest.approx(audit["direct_bind_centroid_m"], abs=2e-9)
    assert vertices["com_m"] == pytest.approx(audit["direct_bind_centroid_m"], abs=2e-9)
    assert float(np.sum(vertices["vertex_mass_kg"])) == pytest.approx(expected_mass, abs=2e-9)
    assert prepared.receipt()["source_sha256"] == source_hash
    assert len(prepared.receipt()["profile_sha256"]) == 64
    for key in (
        "vertex_mass_kg",
        "world_positions_m",
        "com_m",
        "current_rendered_surface_area_m2",
    ):
        assert cached_vertices[key] == pytest.approx(vertices[key], abs=1e-12)

    original_cached_positions = np.array(cached_vertices["world_positions_m"], copy=True)
    cached_vertices["world_positions_m"][:] = 999.0
    cached_vertices["vertex_mass_kg"][:] = 0.0
    profile_value["mass_model"]["total_mass_kg"] = -1.0
    profile_value["bindings"][0]["bind_world_gram_matrix"] = (
        999.0 * np.eye(3)
    ).tolist()
    replay_cached = prepared(named_worlds)
    assert replay_cached["world_positions_m"] == pytest.approx(
        original_cached_positions, abs=1e-12
    )
    assert float(np.sum(replay_cached["vertex_mass_kg"])) == pytest.approx(
        expected_mass, abs=2e-9
    )

    distorted = {name: np.array(matrix, copy=True) for name, matrix in named_worlds.items()}
    active_name = profile_value["bindings"][0]["node"]
    distorted[active_name][:3, :3] = distorted[active_name][:3, :3] @ np.diag([2.0, 0.5, 1.0])
    with pytest.raises(ContractError, match="linear Gram"):
        prepared(distorted)


def test_missing_joint_and_bad_mass_sum_fail_closed() -> None:
    with pytest.raises(ContractError, match="missing joint"):
        surface_mass_centroid(profile(), {"a": np.eye(4)})
    invalid = profile()
    invalid["bindings"][0]["mass_fraction"] = 0.5
    with pytest.raises(ContractError, match="sum to one"):
        surface_mass_centroid(invalid, {"a": np.eye(4), "b": np.eye(4)})


def test_changed_runtime_scale_and_corrupted_source_fail_closed() -> None:
    changed = np.eye(4)
    changed[:3, :3] *= 1.1
    with pytest.raises(ContractError, match="linear Gram"):
        surface_mass_centroid(profile(), {"a": changed, "b": changed})
    determinant_preserving = np.eye(4)
    determinant_preserving[:3, :3] = np.diag([2.0, 0.5, 1.0])
    with pytest.raises(ContractError, match="linear Gram"):
        surface_mass_centroid(
            profile(), {"a": determinant_preserving, "b": determinant_preserving}
        )
    bound = profile()
    bound["identity"] = {"source_sha256": hashlib.sha256(b"expected").hexdigest()}
    with pytest.raises(ContractError, match="differs from profile binding"):
        surface_mass_vertex_state(b"corrupted", bound, {})


@pytest.mark.parametrize("mass", [0.0, -1.0, np.nan, np.inf])
def test_vertex_state_rejects_invalid_profile_mass_before_source_parse(mass) -> None:
    bound = profile()
    bound["identity"] = {"source_sha256": hashlib.sha256(b"expected").hexdigest()}
    bound["mass_model"]["total_mass_kg"] = mass
    with pytest.raises(ContractError, match="valid total mass"):
        surface_mass_vertex_state(b"expected", bound, {})


def test_prepared_vertex_evaluator_rejects_corrupted_source_binding() -> None:
    bound = profile()
    bound["identity"] = {"source_sha256": hashlib.sha256(b"expected").hexdigest()}
    with pytest.raises(ContractError, match="differs from profile binding"):
        prepare_surface_mass_vertex_evaluator(b"corrupted", bound)
