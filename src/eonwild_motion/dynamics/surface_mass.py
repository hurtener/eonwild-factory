"""Source-bound surface-mass quadrature for provisional body coordination.

The proxy uses uniform *surface* density on the admitted neutral mesh.  It is
an engineering control input, not an anatomical density or capacity model.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from ..factory.animal import apply_uniform_geometry_scale, load_animal_instance
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _world_matrices


SCHEMA = "eonwild.motion.surface-mass-proxy.v1"
COORDINATES = {
    "units": "m",
    "handedness": "right",
    "up_axis": "+Y",
    "forward_axis": "+Z",
}

def _digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _json(raw: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError(f"{label} must be an object")
    return value


def _column_major_matrix(row: Sequence[float]) -> np.ndarray:
    value = np.asarray(row, dtype=np.float64)
    if value.size != 16 or not np.isfinite(value).all():
        raise ContractError("surface-mass inverse bind matrix is invalid")
    return value.reshape(4, 4).T


def _role_paths(value: Any, path: tuple[str, ...] = ()) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if isinstance(value, str):
        result[value] = list(path)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            result.update(_role_paths(item, (*path, str(key))))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            result.update(_role_paths(item, (*path, str(index))))
    return result


def _surface_audit(points: np.ndarray, triangles: np.ndarray) -> dict[str, Any]:
    scale = float(np.max(np.ptp(points, axis=0)))
    tolerance = scale * 1e-7
    welded = np.rint(points / tolerance).astype(np.int64)
    unique, inverse = np.unique(welded, axis=0, return_inverse=True)
    faces = inverse[triangles]
    edges: Counter[tuple[int, int]] = Counter()
    directed: Counter[tuple[int, int]] = Counter()
    for face in faces:
        for left, right in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            left, right = int(left), int(right)
            if left == right:
                continue
            edges[tuple(sorted((left, right)))] += 1
            directed[(left, right)] += 1
    return {
        "raw_vertex_count": int(len(points)),
        "welded_vertex_count": int(len(unique)),
        "triangle_count": int(len(triangles)),
        "weld_relative_tolerance": 1e-7,
        "boundary_edge_count": sum(count == 1 for count in edges.values()),
        "nonmanifold_edge_count": sum(count > 2 for count in edges.values()),
        "orientation_mismatch_edge_count": sum(
            count == 2 and directed[edge] != 1 for edge, count in edges.items()
        ),
        "closed_volume_suitable": bool(edges) and all(count == 2 for count in edges.values()),
        "surface_proxy_suitable": True,
    }


def _vertex_area_weights(points: np.ndarray, triangles: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    triangle_points = points[triangles]
    areas = 0.5 * np.linalg.norm(
        np.cross(triangle_points[:, 1] - triangle_points[:, 0], triangle_points[:, 2] - triangle_points[:, 0]),
        axis=1,
    )
    vertex_area = np.zeros(len(points), dtype=np.float64)
    for corner in range(3):
        np.add.at(vertex_area, triangles[:, corner], areas / 3.0)
    return areas, vertex_area


def _validated_inputs(
    source: Glb,
) -> tuple[Mapping[str, Any], Mapping[str, Any], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mesh_nodes = [
        (index, node)
        for index, node in enumerate(source.nodes)
        if isinstance(node.get("mesh"), int) and isinstance(node.get("skin"), int)
    ]
    if len(mesh_nodes) != 1:
        raise ContractError("surface-mass proxy requires exactly one skinned mesh node")
    mesh_node_index, mesh_node = mesh_nodes[0]
    primitives = source.document["meshes"][mesh_node["mesh"]].get("primitives")
    if not isinstance(primitives, list) or len(primitives) != 1:
        raise ContractError("surface-mass proxy requires exactly one mesh primitive")
    primitive = primitives[0]
    if primitive.get("mode", 4) != 4 or "indices" not in primitive:
        raise ContractError("surface-mass proxy requires indexed TRIANGLES")
    attributes = primitive.get("attributes", {})
    positions = np.asarray(source.accessor_values(attributes["POSITION"]), dtype=np.float64)
    indices = np.asarray(source.accessor_values(primitive["indices"]), dtype=np.int64)
    if positions.ndim != 2 or positions.shape[1] != 3 or not np.isfinite(positions).all():
        raise ContractError("surface-mass POSITION is invalid")
    if len(indices) % 3 or np.any(indices < 0) or np.any(indices >= len(positions)):
        raise ContractError("surface-mass indices are invalid")
    suffixes = sorted(
        key.removeprefix("JOINTS_") for key in attributes if key.startswith("JOINTS_")
    )
    if not suffixes or any(f"WEIGHTS_{suffix}" not in attributes for suffix in suffixes):
        raise ContractError("surface-mass influence sets are incomplete")
    joints = np.concatenate(
        [np.asarray(source.accessor_values(attributes[f"JOINTS_{suffix}"]), dtype=np.int64) for suffix in suffixes],
        axis=1,
    )
    weights = np.concatenate(
        [np.asarray(source.accessor_values(attributes[f"WEIGHTS_{suffix}"]), dtype=np.float64) for suffix in suffixes],
        axis=1,
    )
    if joints.shape != weights.shape or len(joints) != len(positions):
        raise ContractError("surface-mass influence shapes differ")
    sums = weights.sum(axis=1)
    if not np.isfinite(weights).all() or np.any(weights < 0) or np.max(np.abs(sums - 1)) > 2e-6:
        raise ContractError("surface-mass weights are invalid or not normalized")
    weights = weights / sums[:, None]
    skin = source.document["skins"][mesh_node["skin"]]
    if np.any(joints < 0) or np.any(joints >= len(skin["joints"])):
        raise ContractError("surface-mass influence references an invalid skin slot")
    inverse = np.asarray(
        [_column_major_matrix(row) for row in source.accessor_values(skin["inverseBindMatrices"])],
        dtype=np.float64,
    )
    if len(inverse) != len(skin["joints"]):
        raise ContractError("surface-mass inverse bind count differs from skin joints")
    return mesh_node, skin, positions, indices.reshape(-1, 3), joints, weights


def prepare_surface_mass_proxy(
    source_bytes: bytes,
    rig_bytes: bytes,
    animal_bytes: bytes,
    *,
    source_sha256: str,
    rig_sha256: str,
    animal_sha256: str,
    coordinate_system: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Prepare an immutable normalized proxy plus a reproducibility audit."""
    identities = {
        "source_sha256": _digest(source_bytes),
        "rig_sha256": _digest(rig_bytes),
        "animal_sha256": _digest(animal_bytes),
    }
    expected = {
        "source_sha256": source_sha256,
        "rig_sha256": rig_sha256,
        "animal_sha256": animal_sha256,
    }
    if identities != expected:
        raise ContractError("surface-mass source, rig, or animal identity differs from binding")
    if dict(coordinate_system) != COORDINATES:
        raise ContractError("surface-mass proxy requires explicit factory +Y-up/+Z-forward coordinates")
    rig = _json(rig_bytes, "surface-mass rig")
    animal = _json(animal_bytes, "surface-mass animal")
    try:
        total_mass = float(animal["measurements"]["body_mass"]["value"])
        mass_unit = animal["measurements"]["body_mass"]["unit"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("surface-mass animal has no body-mass scale") from exc
    if not np.isfinite(total_mass) or total_mass <= 0 or mass_unit != "kg":
        raise ContractError("surface-mass animal body-mass scale is invalid")
    animal_instance = load_animal_instance(animal, source_sha256=source_sha256)
    instance_scale = float(animal_instance["uniform_scale"])
    source = Glb.from_bytes(source_bytes)
    apply_uniform_geometry_scale(source, instance_scale)
    mesh_node, skin, positions, triangles, joints, weights = _validated_inputs(source)
    worlds = np.asarray(
        _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale),
        dtype=np.float64,
    )
    inverse = np.asarray(
        [_column_major_matrix(row) for row in source.accessor_values(skin["inverseBindMatrices"])],
        dtype=np.float64,
    )
    homogeneous = np.column_stack((positions, np.ones(len(positions))))
    transforms = worlds[np.asarray(skin["joints"], dtype=np.int64)] @ inverse
    neutral = np.zeros((len(positions), 3), dtype=np.float64)
    for column in range(joints.shape[1]):
        slots = joints[:, column]
        moved = np.einsum("nij,nj->ni", transforms[slots], homogeneous)[:, :3]
        neutral += weights[:, column, None] * moved
    areas, vertex_area = _vertex_area_weights(neutral, triangles)
    if not np.isfinite(areas).all() or np.any(areas <= 0) or float(areas.sum()) <= 0:
        raise ContractError("surface-mass source contains degenerate triangle area")

    joint_count = len(skin["joints"])
    mass = np.zeros(joint_count, dtype=np.float64)
    first = np.zeros((joint_count, 3), dtype=np.float64)
    second = np.zeros((joint_count, 3, 3), dtype=np.float64)
    for column in range(joints.shape[1]):
        slots = joints[:, column]
        values = vertex_area * weights[:, column]
        active = values > 0
        if not np.any(active):
            continue
        active_slots = slots[active]
        local = np.einsum("nij,nj->ni", inverse[active_slots], homogeneous[active])[:, :3]
        active_values = values[active]
        np.add.at(mass, active_slots, active_values)
        np.add.at(first, active_slots, active_values[:, None] * local)
        np.add.at(
            second,
            active_slots,
            active_values[:, None, None] * np.einsum("ni,nj->nij", local, local),
        )
    surface_area = float(areas.sum())
    mass /= surface_area
    first /= surface_area
    second /= surface_area
    if not np.isclose(mass.sum(), 1.0, rtol=0, atol=2e-10):
        raise ContractError("surface-mass quadrature fractions do not sum to one")

    role_paths = _role_paths(rig.get("roles", {}))
    bindings = []
    aggregate_world_first = np.zeros(3)
    for slot, node_index in enumerate(skin["joints"]):
        if mass[slot] <= 1e-14:
            continue
        node_index = int(node_index)
        node_name = source.nodes[node_index].get("name", f"node:{node_index}")
        ancestor = node_index
        semantic = None
        while ancestor is not None:
            ancestor_name = source.nodes[ancestor].get("name", f"node:{ancestor}")
            if ancestor_name in role_paths:
                semantic = role_paths[ancestor_name]
                break
            ancestor = source.parents[ancestor]
        center = first[slot] / mass[slot]
        covariance = second[slot] - mass[slot] * np.outer(center, center)
        inertia = np.eye(3) * np.trace(covariance) - covariance
        parent = source.parents[node_index]
        bindings.append(
            {
                "skin_joint_slot": slot,
                "node": node_name,
                "node_index": node_index,
                "parent_node": None if parent is None else source.nodes[parent].get("name", f"node:{parent}"),
                "semantic_ancestry": semantic,
                "mass_fraction": float(mass[slot]),
                "bind_world_determinant_scale": float(
                    np.cbrt(abs(np.linalg.det(worlds[node_index][:3, :3])))
                ),
                "com_local_m": [float(instance_scale * value) for value in center],
                "allocation_point_mass_inertia_tensor_fraction_m2": [
                    [float(instance_scale * instance_scale * value) for value in row]
                    for row in inertia
                ],
            }
        )
        # Factor out only the compiler-owned animal scale.  Source-authored
        # scene-root scale remains part of the joint world transform (the
        # Tarbosaurus source has one), while the stored local moments carry the
        # animal instance scale exactly once.
        aggregate_world_first += (
            worlds[node_index][:3, :3] / instance_scale
            @ (instance_scale * first[slot])
            + worlds[node_index][:3, 3] * mass[slot]
        )
    # A rendered glTF triangle is the plane through its three already-skinned
    # vertices. Area/3 at each corner therefore integrates its centroid exactly.
    direct = np.sum(vertex_area[:, None] * neutral, axis=0) / surface_area
    residual = float(np.linalg.norm(aggregate_world_first - direct))
    if residual > 1e-9 * max(1.0, float(np.max(np.ptp(neutral, axis=0)))):
        raise ContractError(
            "surface-mass aggregate differs from direct bind centroid "
            f"({residual:.12g} m; aggregate={aggregate_world_first.tolist()}; direct={direct.tolist()})"
        )
    profile = {
        "schema": SCHEMA,
        "id": f"{animal['id']}.surface-mass-proxy.v1",
        "version": 1,
        "classification": "low-confidence source-shaped engineering coordination proxy",
        "coordinate_system": dict(COORDINATES),
        "identity": identities,
        "mass_model": {
            "distribution": "uniform_surface_density",
            "density_frame": "admitted_neutral_source_geometry",
            "quadrature": "triangle_area_thirds_at_rendered_vertices",
            "instance_uniform_scale": instance_scale,
            "instance_scale_application": "local COM x scale; local inertia x scale squared; evaluator removes only this instance scale from joint world linear transforms",
            "total_mass_kg": total_mass,
            "total_mass_source": "animal.measurements.body_mass",
            "capacity_claims_enabled": False,
            "tissue_claims_enabled": False,
            "biological_claims": False,
        },
        "surface_area_m2": surface_area,
        "instance_uniform_scale": instance_scale,
        "bindings": bindings,
        "limitations": [
            "Uniform surface density is not uniform bulk density or reconstructed anatomy.",
            "Thin or high-area appendages are overweighted relative to thick body volumes.",
            "Skin weighting affects allocation; capacity, pressure, tissue and muscle claims are disabled.",
            "Mass quadrature is fixed at the admitted neutral source and does not change with deformation.",
            "Second moments use vertex-lumped point masses and do not integrate within-triangle area exactly.",
            "Per-joint allocation moments preserve aggregate COM but omit LBS cross-joint terms; use exact posed vertex states for momentum.",
        ],
    }
    audit = {
        "schema": "eonwild.motion.surface-mass-proxy-audit.v1",
        "profile_id": profile["id"],
        "identity": identities,
        "source_topology": _surface_audit(neutral, triangles),
        "surface_area_m2": surface_area,
        "binding_count": len(bindings),
        "mass_fraction_sum": float(mass.sum()),
        "direct_bind_centroid_m": [float(value) for value in direct],
        "aggregate_bind_centroid_m": [float(value) for value in aggregate_world_first],
        "aggregate_direct_residual_m": residual,
        "status": "PASS_ENGINEERING_PROXY",
    }
    return profile, audit


def surface_mass_body_state(
    profile: Mapping[str, Any], joint_world_matrices: Mapping[str, Sequence[Sequence[float]]]
) -> dict[str, Any]:
    """Evaluate the exact compact COM and explicitly approximate allocations."""
    if profile.get("schema") != SCHEMA:
        raise ContractError("unsupported surface-mass proxy")
    try:
        instance_scale = float(profile["instance_uniform_scale"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("surface-mass proxy has no valid instance scale") from exc
    if not np.isfinite(instance_scale) or instance_scale <= 0:
        raise ContractError("surface-mass proxy has no valid instance scale")
    try:
        total_mass_kg = float(profile["mass_model"]["total_mass_kg"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("surface-mass proxy has no valid total mass") from exc
    if not np.isfinite(total_mass_kg) or total_mass_kg <= 0:
        raise ContractError("surface-mass proxy has no valid total mass")
    result = np.zeros(3)
    total = 0.0
    states = []
    for binding in profile["bindings"]:
        name = binding["node"]
        if name not in joint_world_matrices:
            raise ContractError(f"surface-mass proxy is missing joint world matrix {name!r}")
        matrix = np.asarray(joint_world_matrices[name], dtype=np.float64)
        if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
            raise ContractError("surface-mass joint world matrix is invalid")
        fraction = float(binding["mass_fraction"])
        if not np.isfinite(fraction) or fraction < 0:
            raise ContractError("surface-mass binding fraction is invalid")
        linear = matrix[:3, :3]
        source_linear = linear / instance_scale
        determinant_scale = float(np.cbrt(abs(np.linalg.det(linear))))
        expected_scale = float(binding["bind_world_determinant_scale"])
        if determinant_scale <= 0 or not np.isclose(
            determinant_scale, expected_scale, rtol=2e-6, atol=2e-8 * max(1.0, expected_scale)
        ):
            raise ContractError("surface-mass joint world matrix differs from bound uniform geometry scale")
        local_com = np.asarray(binding["com_local_m"], dtype=np.float64)
        local_inertia = np.asarray(
            binding["allocation_point_mass_inertia_tensor_fraction_m2"], dtype=np.float64
        )
        if (
            local_com.shape != (3,)
            or local_inertia.shape != (3, 3)
            or not np.isfinite(local_com).all()
            or not np.isfinite(local_inertia).all()
            or not np.allclose(local_inertia, local_inertia.T, rtol=0, atol=1e-12)
        ):
            raise ContractError("surface-mass local moments are invalid")
        world_com = source_linear @ local_com + matrix[:3, 3]
        world_inertia = total_mass_kg * source_linear @ local_inertia @ source_linear.T
        result += fraction * world_com
        total += fraction
        states.append(
            {
                "node": name,
                "mass_kg": total_mass_kg * fraction,
                "world_com_m": [float(value) for value in world_com],
                "allocation_world_inertia_about_com_kg_m2": [
                    [float(value) for value in row] for row in world_inertia
                ],
                "exact_for_lbs_momentum": False,
            }
        )
    if not np.isclose(total, 1.0, rtol=0, atol=2e-10):
        raise ContractError("surface-mass proxy fractions do not sum to one")
    return {
        "total_mass_kg": total_mass_kg,
        "com_m": [float(value) for value in result],
        "com_exact_for_vertex_lumped_proxy": True,
        "bindings": states,
    }


def surface_mass_vertex_state(
    source_bytes: bytes,
    profile: Mapping[str, Any],
    joint_world_matrices: Mapping[str, Sequence[Sequence[float]]],
) -> dict[str, Any]:
    """Evaluate exact posed fixed-mass vertices for momentum calculations."""
    try:
        expected_source = profile["identity"]["source_sha256"]
        total_mass_kg = float(profile["mass_model"]["total_mass_kg"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("surface-mass proxy binding is incomplete") from exc
    if profile.get("schema") != SCHEMA or _digest(source_bytes) != expected_source:
        raise ContractError("surface-mass vertex source differs from profile binding")
    source = Glb.from_bytes(source_bytes)
    _, skin, positions, triangles, joints, weights = _validated_inputs(source)
    inverse = np.asarray(
        [_column_major_matrix(row) for row in source.accessor_values(skin["inverseBindMatrices"])],
        dtype=np.float64,
    )
    expected_scales = {
        binding["node"]: float(binding["bind_world_determinant_scale"])
        for binding in profile["bindings"]
    }
    matrices = []
    for node_index in skin["joints"]:
        name = source.nodes[int(node_index)].get("name", f"node:{int(node_index)}")
        if name not in joint_world_matrices:
            raise ContractError(f"surface-mass proxy is missing joint world matrix {name!r}")
        matrix = np.asarray(joint_world_matrices[name], dtype=np.float64)
        if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
            raise ContractError("surface-mass joint world matrix is invalid")
        determinant_scale = float(np.cbrt(abs(np.linalg.det(matrix[:3, :3]))))
        if name in expected_scales and not np.isclose(
            determinant_scale,
            expected_scales[name],
            rtol=2e-6,
            atol=2e-8 * max(1.0, expected_scales[name]),
        ):
            raise ContractError("surface-mass joint world matrix differs from bound uniform geometry scale")
        matrices.append(matrix @ inverse[len(matrices)])
    transforms = np.asarray(matrices, dtype=np.float64)
    homogeneous = np.column_stack((positions, np.ones(len(positions))))
    posed = np.zeros((len(positions), 3), dtype=np.float64)
    for column in range(joints.shape[1]):
        moved = np.einsum("nij,nj->ni", transforms[joints[:, column]], homogeneous)[:, :3]
        posed += weights[:, column, None] * moved

    areas, _ = _vertex_area_weights(posed, triangles)
    # Masses remain fixed from the admitted neutral profile. Recover their
    # normalized values from the source topology; uniform admission scale
    # cancels in normalization.
    source_worlds = np.asarray(
        _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale),
        dtype=np.float64,
    )
    source_transforms = source_worlds[np.asarray(skin["joints"], dtype=np.int64)] @ inverse
    neutral = np.zeros((len(positions), 3), dtype=np.float64)
    for column in range(joints.shape[1]):
        moved = np.einsum("nij,nj->ni", source_transforms[joints[:, column]], homogeneous)[:, :3]
        neutral += weights[:, column, None] * moved
    neutral_areas, vertex_area = _vertex_area_weights(neutral, triangles)
    masses = total_mass_kg * vertex_area / float(neutral_areas.sum())
    com = np.sum(masses[:, None] * posed, axis=0) / total_mass_kg
    return {
        "total_mass_kg": total_mass_kg,
        "vertex_mass_kg": masses,
        "world_positions_m": posed,
        "com_m": com,
        "current_rendered_surface_area_m2": float(areas.sum()),
    }


def surface_mass_interval_momentum(
    previous: Mapping[str, Any], current: Mapping[str, Any], dt_s: float
) -> dict[str, Any]:
    """Evaluate finite-interval P and centroidal H from exact posed vertices."""
    if not np.isfinite(dt_s) or dt_s <= 0:
        raise ContractError("surface-mass momentum interval must be positive")
    before = np.asarray(previous.get("world_positions_m"), dtype=np.float64)
    after = np.asarray(current.get("world_positions_m"), dtype=np.float64)
    masses = np.asarray(current.get("vertex_mass_kg"), dtype=np.float64)
    previous_masses = np.asarray(previous.get("vertex_mass_kg"), dtype=np.float64)
    if (
        before.shape != after.shape
        or before.ndim != 2
        or before.shape[1] != 3
        or masses.shape != (len(after),)
        or previous_masses.shape != masses.shape
        or not np.isfinite(before).all()
        or not np.isfinite(after).all()
        or not np.allclose(previous_masses, masses, rtol=0, atol=1e-12)
    ):
        raise ContractError("surface-mass momentum states are incompatible")
    velocity = (after - before) / dt_s
    midpoint = 0.5 * (before + after)
    total_mass = float(masses.sum())
    com = np.sum(masses[:, None] * midpoint, axis=0) / total_mass
    linear = np.sum(masses[:, None] * velocity, axis=0)
    angular = np.sum(np.cross(midpoint - com, masses[:, None] * velocity), axis=0)
    return {
        "sample_com_m": [float(value) for value in com],
        "linear_momentum_kg_mps": [float(value) for value in linear],
        "centroidal_angular_momentum_kg_m2ps": [float(value) for value in angular],
    }


def surface_mass_centroid(
    profile: Mapping[str, Any], joint_world_matrices: Mapping[str, Sequence[Sequence[float]]]
) -> tuple[float, float, float]:
    """Evaluate the aggregate COM from current joint world matrices."""
    return tuple(surface_mass_body_state(profile, joint_world_matrices)["com_m"])


__all__ = [
    "COORDINATES",
    "SCHEMA",
    "prepare_surface_mass_proxy",
    "surface_mass_body_state",
    "surface_mass_centroid",
    "surface_mass_interval_momentum",
    "surface_mass_vertex_state",
]
