"""Reproducible, non-promoting rest-rig preparation for preserved GLB sources.

The operation changes hierarchy and joint origins while rebuilding inverse bind
matrices so the neutral skinned surface stays fixed.  It does not author an
animation, infer anatomy, or admit the result to a motion catalog.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import tempfile
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError, MotionError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _world_matrices
from ..solve.whole_body_gait_transition import _encode
from .source import (
    _accessor_index,
    _decompose_bind_local,
    _skin_reconstruction_error,
)


SCHEMA = "eonwild.motion.rig-preparation.v1"


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _exact_object(value: Any, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ContractError(f"{label} contains missing or unknown fields")
    return value


def _name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label} must be a non-empty node name")
    return value


def _vec3(value: Any, label: str) -> np.ndarray:
    try:
        result = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label} must be three finite numbers") from exc
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractError(f"{label} must be three finite numbers")
    return result


def _parents(nodes: list[Mapping[str, Any]]) -> list[int | None]:
    parent: list[int | None] = [None] * len(nodes)
    for index, node in enumerate(nodes):
        children = node.get("children", [])
        if not isinstance(children, list):
            raise ContractError(f"node {index} children must be an index array")
        for child in children:
            if type(child) is not int or not 0 <= child < len(nodes):
                raise ContractError(f"node {index} child must be an in-range integer")
            if parent[child] is not None:
                raise ContractError("rig preparation hierarchy has multiple parents")
            parent[child] = index
    for node in range(len(nodes)):
        seen: set[int] = set()
        cursor: int | None = node
        while cursor is not None:
            if cursor in seen:
                raise ContractError("rig preparation hierarchy contains a cycle")
            seen.add(cursor)
            cursor = parent[cursor]
    return parent


def _is_descendant(node: int, ancestor: int, parents: list[int | None]) -> bool:
    cursor: int | None = node
    while cursor is not None:
        if cursor == ancestor:
            return True
        cursor = parents[cursor]
    return False


def prepare_rig(source: Glb, config: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    legacy_fields = {
        "schema", "id", "source_sha256", "skin_index", "reparents",
        "coordinate", "pivot_relocations", "articulations", "weight_transfers",
        "evidence", "limitations",
    }
    optional_fields = {"endpoints", "near_uniform_scale_normalization", "weighted_branches"}
    if (
        not isinstance(config, Mapping)
        or not legacy_fields <= set(config)
        or set(config) - legacy_fields - optional_fields
    ):
        raise ContractError("rig preparation contains missing or unknown fields")
    if config["schema"] != SCHEMA:
        raise ContractError("unsupported rig preparation schema")
    _name(config["id"], "rig preparation id")
    if (not isinstance(config["source_sha256"], str)
            or len(config["source_sha256"]) != 64
            or any(value not in "0123456789abcdef" for value in config["source_sha256"])):
        raise ContractError("rig preparation source SHA-256 is invalid")
    if _digest(source.raw) != config["source_sha256"]:
        raise ContractError("rig preparation source bytes differ from the frozen source")
    if source.document.get("animations"):
        raise ContractError("rig preparation requires an animation-free source")
    skin_index = config["skin_index"]
    skins = source.document.get("skins")
    if (type(skin_index) is not int or not isinstance(skins, list)
            or not 0 <= skin_index < len(skins)):
        raise ContractError("rig preparation skin index is invalid")
    if len(skins) != 1:
        raise ContractError("rig preparation supports exactly one skin")
    skin = skins[skin_index]
    if not isinstance(skin, Mapping) or not isinstance(skin.get("joints"), list):
        raise ContractError("rig preparation requires a joint skin")
    joints = list(skin["joints"])
    if any(type(node) is not int or not 0 <= node < len(source.nodes) for node in joints):
        raise ContractError("rig preparation skin has an invalid joint index")
    if len(set(joints)) != len(joints):
        raise ContractError("rig preparation skin joints must be unique")
    joint_set = set(joints)
    names = dict(source.name_to_node)

    coordinate = _exact_object(
        config["coordinate"], {"frame", "lateral", "up", "forward"},
        "rig preparation coordinate")
    if coordinate["frame"] != "source_world":
        raise ContractError("rig preparation coordinate frame is unsupported")
    axes = np.asarray([
        _vec3(coordinate[name], f"rig preparation {name} axis")
        for name in ("lateral", "up", "forward")
    ])
    if (not np.allclose(np.linalg.norm(axes, axis=1), 1.0, atol=1e-6, rtol=0.0)
            or not np.allclose(axes @ axes.T, np.eye(3), atol=1e-6, rtol=0.0)
            or float(np.linalg.det(axes)) < 1.0 - 1e-6):
        raise ContractError("rig preparation coordinate axes must be right-handed orthonormal")

    document = deepcopy(source.document)
    nodes = document["nodes"]
    original_node_count = len(nodes)
    original_parents = _parents(nodes)
    original_world = np.asarray(_world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale), dtype=float)
    if not np.isfinite(original_world).all():
        raise ContractError("rig preparation source world matrices are non-finite")
    mesh_nodes = [index for index, node in enumerate(source.nodes)
                  if node.get("skin") == skin_index]
    if len(mesh_nodes) != 1:
        raise ContractError("rig preparation requires exactly one mesh node for the selected skin")
    mesh_node = mesh_nodes[0]
    source_skin_error, source_vertex_count = _skin_reconstruction_error(
        source, skin_index=skin_index, mesh_node=mesh_node)
    if source_skin_error > 3e-6:
        raise ContractError(
            "rig preparation source neutral skin is not canonical POSITION geometry")

    reparents = config["reparents"]
    if not isinstance(reparents, list):
        raise ContractError("rig preparation reparents must be an array")
    reparented: set[int] = set()
    for index, raw in enumerate(reparents):
        row = _exact_object(raw, {"node", "new_parent"}, f"reparent[{index}]")
        child_name = _name(row["node"], f"reparent[{index}] node")
        parent_name = _name(row["new_parent"], f"reparent[{index}] new parent")
        if child_name not in names or parent_name not in names:
            raise ContractError("rig preparation reparent references an unknown node")
        child, parent = names[child_name], names[parent_name]
        if child not in joint_set or parent not in joint_set:
            raise ContractError("rig preparation reparents must stay within the selected skin")
        if child in reparented or child == parent:
            raise ContractError("rig preparation contains a duplicate or self reparent")
        old_parent = original_parents[child]
        if old_parent is None:
            raise ContractError("rig preparation cannot reparent a scene root")
        if old_parent == parent:
            raise ContractError("rig preparation reparent must change the parent")
        nodes[old_parent]["children"].remove(child)
        nodes[parent].setdefault("children", []).append(child)
        reparented.add(child)

    weighted_branches = config.get("weighted_branches", [])
    if not isinstance(weighted_branches, list):
        raise ContractError("rig preparation weighted branches must be an array")
    weighted_branch_rows: list[dict[str, Any]] = []
    added_names: set[str] = set()
    weighted_roles: set[str] = set()
    for index, raw in enumerate(weighted_branches):
        row = _exact_object(
            raw,
            {"role", "parent", "source_nodes", "proximal", "distal", "endpoint", "selector"},
            f"weighted_branch[{index}]",
        )
        role = _name(row["role"], f"weighted_branch[{index}] role")
        if role in weighted_roles:
            raise ContractError("rig preparation weighted branch roles must be unique")
        weighted_roles.add(role)
        parent_name = _name(row["parent"], f"weighted_branch[{index}] parent")
        source_names = row["source_nodes"]
        if (parent_name not in names or not isinstance(source_names, list)
                or not source_names):
            raise ContractError("rig preparation weighted branch references unknown topology")
        source_names = [_name(item, f"weighted_branch[{index}] source node") for item in source_names]
        if any(item not in names or names[item] not in joint_set for item in source_names):
            raise ContractError("rig preparation weighted branch source nodes must be skin joints")
        if names[parent_name] not in joint_set:
            raise ContractError("rig preparation weighted branch parent must be a skin joint")
        if any(not _is_descendant(names[item], names[parent_name], original_parents)
               for item in source_names):
            raise ContractError("rig preparation weighted branch source nodes must belong to its parent branch")
        pieces = []
        piece_parent = parent_name
        for label in ("proximal", "distal", "endpoint"):
            piece = _exact_object(
                row[label], {"name", "world_origin_m", "basis"},
                f"weighted_branch[{index}] {label}",
            )
            piece_name = _name(piece["name"], f"weighted_branch[{index}] {label} name")
            if piece_name in names or piece_name in added_names:
                raise ContractError("rig preparation weighted branch node names must be unique")
            if piece["basis"] != "measured_source_world":
                raise ContractError("rig preparation weighted branch origin basis is unsupported")
            node = len(nodes)
            nodes.append({"name": piece_name})
            nodes[names[piece_parent]].setdefault("children", []).append(node)
            names[piece_name] = node
            added_names.add(piece_name)
            pieces.append({
                "name": piece_name, "node": node, "parent": piece_parent,
                "world_origin_m": _vec3(
                    piece["world_origin_m"], f"weighted_branch[{index}] {label} origin"),
            })
            piece_parent = piece_name
        selector = _exact_object(
            row["selector"],
            {"frame", "lateral_interval_m", "up_maximum_m", "forward_interval_m", "blend_width_m"},
            f"weighted_branch[{index}] selector",
        )
        if selector["frame"] != "source_world":
            raise ContractError("rig preparation weighted branch selector frame is unsupported")
        lateral_interval = np.asarray(selector["lateral_interval_m"], dtype=float)
        forward_interval = np.asarray(selector["forward_interval_m"], dtype=float)
        up_maximum = selector["up_maximum_m"]
        blend_width = selector["blend_width_m"]
        if (lateral_interval.shape != (2,) or forward_interval.shape != (2,)
                or not np.isfinite(lateral_interval).all() or not np.isfinite(forward_interval).all()
                or not lateral_interval[0] < lateral_interval[1]
                or not forward_interval[0] < forward_interval[1]
                or isinstance(up_maximum, bool) or not isinstance(up_maximum, (int, float))
                or not math.isfinite(float(up_maximum))
                or isinstance(blend_width, bool) or not isinstance(blend_width, (int, float))
                or not math.isfinite(float(blend_width)) or not 0.0 < float(blend_width)
                or 2.0 * float(blend_width) >= float(lateral_interval[1] - lateral_interval[0])):
            raise ContractError("rig preparation weighted branch selector is invalid")
        weighted_branch_rows.append({
            "role": role, "parent": parent_name, "source_nodes": source_names,
            "proximal": pieces[0], "distal": pieces[1], "endpoint": pieces[2],
            "selector": deepcopy(selector),
        })

    endpoints = config.get("endpoints", [])
    if not isinstance(endpoints, list):
        raise ContractError("rig preparation endpoints must be an array")
    endpoint_rows: list[dict[str, Any]] = []
    endpoint_names: set[str] = set()
    for index, raw in enumerate(endpoints):
        row = _exact_object(
            raw, {"name", "parent", "world_origin_m", "basis"},
            f"endpoint[{index}]",
        )
        endpoint_name = _name(row["name"], f"endpoint[{index}] name")
        parent_name = _name(row["parent"], f"endpoint[{index}] parent")
        if endpoint_name in names or endpoint_name in endpoint_names:
            raise ContractError("rig preparation endpoint name must be unique")
        if parent_name not in source.name_to_node:
            raise ContractError("rig preparation endpoint parent must be an existing node")
        if row["basis"] != "measured_source_world":
            raise ContractError("rig preparation endpoint basis is unsupported")
        endpoint_names.add(endpoint_name)
        node = len(nodes)
        nodes.append({"name": endpoint_name})
        nodes[names[parent_name]].setdefault("children", []).append(node)
        names[endpoint_name] = node
        endpoint_rows.append({
            "name": endpoint_name,
            "parent": parent_name,
            "node": node,
            "world_origin_m": _vec3(
                row["world_origin_m"], f"endpoint[{index}] origin"
            ),
        })

    scale_policy = config.get("near_uniform_scale_normalization")
    if scale_policy is not None:
        scale_policy = _exact_object(
            scale_policy,
            {"maximum_axis_spread", "maximum_unit_deviation", "target"},
            "near-uniform scale normalization",
        )
        if scale_policy["target"] != "unit":
            raise ContractError("near-uniform scale normalization target is unsupported")
        limits = []
        for key in ("maximum_axis_spread", "maximum_unit_deviation"):
            value = scale_policy[key]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 1e-6 < float(value) <= 1e-4
            ):
                raise ContractError(
                    "near-uniform scale normalization limits must lie within (1e-6, 1e-4]"
                )
            limits.append(float(value))
        maximum_scale_spread, maximum_unit_deviation = limits

    new_parents = _parents(nodes)
    pivots = config["pivot_relocations"]
    if not isinstance(pivots, list):
        raise ContractError("rig preparation pivot relocations must be an array")
    desired_world = np.concatenate(
        (
            original_world.copy(),
            np.repeat(np.eye(4)[None, :, :], len(nodes) - original_node_count, axis=0),
        ),
        axis=0,
    )
    pivot_nodes: set[int] = set()
    for index, raw in enumerate(pivots):
        row = _exact_object(raw, {"node", "world_origin_m", "basis"}, f"pivot[{index}]")
        node_name = _name(row["node"], f"pivot[{index}] node")
        if node_name not in names or names[node_name] not in joint_set:
            raise ContractError("rig preparation pivot references an unknown skin joint")
        if row["basis"] != "measured_source_world":
            raise ContractError("rig preparation pivot basis is unsupported")
        node = names[node_name]
        if node in pivot_nodes:
            raise ContractError("rig preparation pivot nodes must be unique")
        desired_world[node, :3, 3] = _vec3(row["world_origin_m"], f"pivot[{index}] origin")
        pivot_nodes.add(node)

    for row in weighted_branch_rows:
        for piece in (row["proximal"], row["distal"], row["endpoint"]):
            parent = names[piece["parent"]]
            desired_world[piece["node"]] = desired_world[parent]
            desired_world[piece["node"], :3, 3] = piece["world_origin_m"]

    for row in endpoint_rows:
        parent = names[row["parent"]]
        desired_world[row["node"]] = desired_world[parent]
        desired_world[row["node"], :3, 3] = row["world_origin_m"]

    articulations = config["articulations"]
    if not isinstance(articulations, list):
        raise ContractError("rig preparation articulations must be an array")
    articulation_rows = []
    articulation_nodes: dict[str, int] = {}
    for index, raw in enumerate(articulations):
        row = _exact_object(raw, {"role", "node", "parent", "descendants", "axis", "axis_frame"},
                            f"articulation[{index}]")
        role = _name(row["role"], f"articulation[{index}] role")
        node_name = _name(row["node"], f"articulation[{index}] node")
        parent_name = _name(row["parent"], f"articulation[{index}] parent")
        descendants = row["descendants"]
        if not isinstance(descendants, list) or not descendants:
            raise ContractError("rig preparation articulation descendants must be non-empty")
        all_names = [node_name, parent_name, *[_name(item, "articulation descendant") for item in descendants]]
        if any(item not in names for item in all_names):
            raise ContractError("rig preparation articulation references an unknown node")
        node, parent = names[node_name], names[parent_name]
        if any(names[item] not in joint_set for item in all_names):
            raise ContractError("rig preparation articulations must stay within the selected skin")
        if new_parents[node] != parent:
            raise ContractError("rig preparation articulation parent is not direct")
        if any(not _is_descendant(names[item], node, new_parents) for item in descendants):
            raise ContractError("rig preparation articulation descendant lies outside its branch")
        if row["axis_frame"] != "joint_parent_local":
            raise ContractError("rig preparation articulation axis frame is unsupported")
        axis = _vec3(row["axis"], f"articulation[{index}] axis")
        norm = float(np.linalg.norm(axis))
        if not math.isclose(norm, 1.0, abs_tol=1e-6, rel_tol=0.0):
            raise ContractError("rig preparation articulation axis must be unit length")
        if role in articulation_nodes or node in articulation_nodes.values():
            raise ContractError("rig preparation articulation roles and nodes must be unique")
        articulation_nodes[role] = node
        articulation_rows.append({"role": role, "node": node_name, "parent": parent_name,
                                  "descendants": list(descendants), "axis": axis.tolist(),
                                  "axis_frame": row["axis_frame"]})

    if not isinstance(config["evidence"], list) or not config["evidence"]:
        raise ContractError("rig preparation requires explicit evidence")
    if not isinstance(config["limitations"], list) or not config["limitations"]:
        raise ContractError("rig preparation requires explicit limitations")
    if any(not isinstance(item, Mapping) for item in config["evidence"]):
        raise ContractError("rig preparation evidence entries must be objects")
    if any(not isinstance(item, str) or not item for item in config["limitations"]):
        raise ContractError("rig preparation limitations must be non-empty strings")

    depths: dict[int, int] = {}
    def depth(node: int) -> int:
        if node not in depths:
            cursor: int | None = node
            value = 0
            while cursor is not None:
                value += 1
                cursor = new_parents[cursor]
            depths[node] = value
        return depths[node]

    output_world: dict[int, np.ndarray] = {}
    touched: list[str] = []
    normalized_scales: list[dict[str, Any]] = []
    projection_errors: list[float] = []
    for node in sorted(range(len(nodes)), key=depth):
        parent = new_parents[node]
        parent_world = np.eye(4) if parent is None else output_world[parent]
        target = desired_world[node]
        local = np.linalg.solve(parent_world, target)
        if node < original_node_count:
            old_parent = original_parents[node]
            old_parent_world = np.eye(4) if old_parent is None else original_world[old_parent]
            old_local = np.linalg.solve(old_parent_world, original_world[node])
            changed = parent != old_parent or not np.allclose(
                local, old_local, atol=1e-12, rtol=0.0
            )
        else:
            changed = True
        local_scale = np.linalg.norm(local[:3, :3], axis=0)
        normalize_scale = bool(
            scale_policy is not None
            and (
                float(np.ptp(local_scale)) > 1e-6
                or float(np.max(np.abs(local_scale - 1.0))) > 1e-6
            )
        )
        if normalize_scale:
            if (
                float(np.ptp(local_scale)) > maximum_scale_spread
                or float(np.max(np.abs(local_scale - 1.0))) > maximum_unit_deviation
            ):
                raise ContractError(
                    "rig preparation near-uniform scale exceeds its declared normalization limits"
                )
            changed = True
        if changed:
            translation, rotation, scale, diagnostic = _decompose_bind_local(
                local, label=f"prepared local[{node}]")
            if normalize_scale:
                normalized_scales.append({
                    "node": nodes[node].get("name", f"node_{node}"),
                    "input_scale": list(scale),
                    "output_scale": [1.0, 1.0, 1.0],
                })
                scale = [1.0, 1.0, 1.0]
            entry = nodes[node]
            entry.pop("matrix", None)
            entry["translation"], entry["rotation"], entry["scale"] = translation, rotation, scale
            touched.append(entry.get("name", f"node_{node}"))
            projection_errors.append(diagnostic["linear_projection_error"])
            if scale_policy is not None:
                x, y, z, w = rotation
                rotation_matrix = np.array([
                    [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
                ])
                local_output = np.eye(4)
                local_output[:3, :3] = rotation_matrix * np.asarray(scale)
                local_output[:3, 3] = translation
                output_world[node] = parent_world @ local_output
            else:
                # Preserve the historical exact target propagation when scale
                # normalization is not requested. Reconstructing from serialized
                # TRS here perturbs descendants and breaks prepared-source bytes.
                output_world[node] = target
        else:
            output_world[node] = target

    mesh_world = output_world[mesh_node]
    inverse_accessor = _accessor_index(
        source, skin.get("inverseBindMatrices"), label="rig preparation inverse bind",
        accessor_type="MAT4", component_types=(5126,), expected_count=len(joints))
    binary = bytearray(source.binary)
    # Proximal and distal nodes are real deformers. Endpoints remain semantic
    # effectors and therefore are deliberately absent from the skin.
    for row in weighted_branch_rows:
        joints.extend((row["proximal"]["node"], row["distal"]["node"]))
    document["skins"][skin_index]["joints"] = joints
    weight_transfer_rows = []
    transfers = config["weight_transfers"]
    if not isinstance(transfers, list):
        raise ContractError("rig preparation weight transfers must be an array")
    if len(transfers) > 1:
        raise ContractError("rig preparation supports at most one weight transfer")
    meshes = source.document.get("meshes")
    mesh_index = source.nodes[mesh_node].get("mesh")
    if (type(mesh_index) is not int or not isinstance(meshes, list)
            or not 0 <= mesh_index < len(meshes)):
        raise ContractError("rig preparation selected skin has an invalid mesh")
    primitives = meshes[mesh_index].get("primitives")
    if not isinstance(primitives, list) or not primitives:
        raise ContractError("rig preparation selected skin requires mesh primitives")

    def admit_physical_skin_rows(
        position_accessor: int,
        joint_accessors: list[int],
        weight_accessors: list[int],
        *,
        bundles: set[tuple[int, ...]],
        accessor_owners: dict[int, tuple[int, ...]],
    ) -> tuple[bool, tuple[int, ...]]:
        """Admit one physical vertex/skin row bundle exactly once.

        Multiple material primitives may share every accessor.  Reprocessing
        that shared storage would compound partial-gain weight operations.
        Partial aliases are rejected because they do not identify one
        unambiguous physical row ownership model.
        """
        bundle = (
            position_accessor,
            *joint_accessors,
            *weight_accessors,
        )
        for accessor in bundle:
            owner = accessor_owners.get(accessor)
            if owner is not None and owner != bundle:
                raise ContractError(
                    "rig preparation skin primitives partially alias accessors"
                )
        if bundle in bundles:
            return False, bundle
        bundles.add(bundle)
        for accessor in bundle:
            accessor_owners[accessor] = bundle
        return True, bundle

    for transfer_index, raw in enumerate(transfers):
        row = _exact_object(
            raw, {"role", "from_articulation", "to_node", "selector"},
            f"weight_transfer[{transfer_index}]")
        role = _name(row["role"], f"weight_transfer[{transfer_index}] role")
        from_role = _name(
            row["from_articulation"], f"weight_transfer[{transfer_index}] articulation")
        target_name = _name(row["to_node"], f"weight_transfer[{transfer_index}] target")
        if from_role not in articulation_nodes or target_name not in names:
            raise ContractError("rig preparation weight transfer references an unknown role or node")
        branch_node, target_node = articulation_nodes[from_role], names[target_name]
        if target_node not in joint_set or _is_descendant(target_node, branch_node, new_parents):
            raise ContractError("rig preparation weight transfer target must lie outside its branch")
        selector = _exact_object(
            row["selector"], {"frame", "halfspaces"},
            f"weight_transfer[{transfer_index}] selector")
        if selector["frame"] != "source_world":
            raise ContractError("rig preparation weight selector frame is unsupported")
        halfspaces = selector["halfspaces"]
        if not isinstance(halfspaces, list) or not halfspaces:
            raise ContractError("rig preparation weight selector requires halfspaces")
        planes = []
        for plane_index, raw_plane in enumerate(halfspaces):
            plane = _exact_object(
                raw_plane, {"normal", "minimum_dot_m"},
                f"weight_transfer[{transfer_index}] halfspace[{plane_index}]")
            normal = _vec3(
                plane["normal"],
                f"weight_transfer[{transfer_index}] halfspace[{plane_index}] normal")
            minimum = plane["minimum_dot_m"]
            if (isinstance(minimum, bool) or not isinstance(minimum, (int, float))
                    or not math.isfinite(float(minimum))
                    or not math.isclose(float(np.linalg.norm(normal)), 1.0,
                                        abs_tol=1e-6, rel_tol=0.0)):
                raise ContractError("rig preparation weight halfspace must have a unit normal and finite offset")
            planes.append((normal, float(minimum)))
        branch_nodes = {
            node for node in range(len(nodes))
            if _is_descendant(node, branch_node, new_parents)
        }
        branch_slots = {slot for slot, node in enumerate(joints) if node in branch_nodes}
        target_slot = joints.index(target_node)
        selected_count = changed_count = 0
        transferred_weights = []
        physical_bundles: set[tuple[int, ...]] = set()
        physical_accessor_owners: dict[int, tuple[int, ...]] = {}
        for primitive_index, primitive in enumerate(primitives):
            attributes = primitive.get("attributes") if isinstance(primitive, Mapping) else None
            if not isinstance(attributes, Mapping) or "POSITION" not in attributes:
                raise ContractError("rig preparation weight transfer requires POSITION")
            suffixes = sorted(
                key.removeprefix("JOINTS_") for key in attributes
                if key.startswith("JOINTS_"))
            if (not suffixes or any(not suffix.isdecimal() for suffix in suffixes)
                    or any(f"WEIGHTS_{suffix}" not in attributes for suffix in suffixes)):
                raise ContractError("rig preparation weight transfer requires paired joint weights")
            position_accessor = _accessor_index(
                source, attributes["POSITION"],
                label=f"weight transfer primitive[{primitive_index}] POSITION",
                accessor_type="VEC3", component_types=(5126,))
            count = source.document["accessors"][position_accessor]["count"]
            joint_accessors = [_accessor_index(
                source, attributes[f"JOINTS_{suffix}"],
                label=f"weight transfer primitive[{primitive_index}] JOINTS_{suffix}",
                accessor_type="VEC4", component_types=(5121, 5123),
                expected_count=count) for suffix in suffixes]
            weight_accessors = [_accessor_index(
                source, attributes[f"WEIGHTS_{suffix}"],
                label=f"weight transfer primitive[{primitive_index}] WEIGHTS_{suffix}",
                accessor_type="VEC4", component_types=(5126,),
                expected_count=count) for suffix in suffixes]
            first_rows, _ = admit_physical_skin_rows(
                position_accessor, joint_accessors, weight_accessors,
                bundles=physical_bundles,
                accessor_owners=physical_accessor_owners,
            )
            if not first_rows:
                continue
            positions = np.asarray(source.accessor_values(position_accessor), dtype=float)
            world_positions = (
                original_world[mesh_node] @
                np.column_stack((positions, np.ones(len(positions)))).T
            ).T[:, :3]
            selected = np.ones(len(positions), dtype=bool)
            for normal, minimum in planes:
                selected &= world_positions @ normal >= minimum
            joint_rows = [np.asarray(source.accessor_values(index), dtype=int)
                          for index in joint_accessors]
            weight_rows = [np.asarray(source.accessor_values(index), dtype=float)
                           for index in weight_accessors]
            selected_count += int(np.sum(selected))
            for vertex in np.flatnonzero(selected):
                entries = [
                    (set_index, column)
                    for set_index, joints_row in enumerate(joint_rows)
                    for column in range(4)
                    if int(joints_row[vertex, column]) in branch_slots
                    and weight_rows[set_index][vertex, column] > 0.0
                ]
                amount = float(sum(
                    weight_rows[set_index][vertex, column]
                    for set_index, column in entries))
                if amount <= 0.0:
                    continue
                targets = [
                    (set_index, column)
                    for set_index, joints_row in enumerate(joint_rows)
                    for column in range(4)
                    if int(joints_row[vertex, column]) == target_slot
                ]
                destination = targets[0] if targets else entries[0]
                for set_index, column in entries:
                    weight_rows[set_index][vertex, column] = 0.0
                    joint_rows[set_index][vertex, column] = 0
                if not targets:
                    joint_rows[destination[0]][vertex, destination[1]] = target_slot
                weight_rows[destination[0]][vertex, destination[1]] += amount
                changed_count += 1
                transferred_weights.append(amount)
            for accessor, rows in zip(joint_accessors, joint_rows):
                _, _, _, _, code = source.accessor_layout(accessor)
                offset, row_count, stride = source.accessor_region(accessor)
                for vertex in range(row_count):
                    struct.pack_into("<" + code * 4, binary, offset + vertex * stride,
                                     *rows[vertex].tolist())
            for accessor, rows in zip(weight_accessors, weight_rows):
                _, _, _, _, code = source.accessor_layout(accessor)
                offset, row_count, stride = source.accessor_region(accessor)
                for vertex in range(row_count):
                    struct.pack_into("<" + code * 4, binary, offset + vertex * stride,
                                     *rows[vertex].tolist())
        if changed_count == 0:
            raise ContractError("rig preparation weight transfer selects no branch influence")
        weight_transfer_rows.append({
            "role": role,
            "from_articulation": from_role,
            "to_node": target_name,
            "selector": deepcopy(selector),
            "selected_vertex_count": selected_count,
            "changed_vertex_count": changed_count,
            "maximum_transferred_weight": max(transferred_weights),
        })
    claimed_vertices: set[tuple[tuple[int, ...], int]] = set()
    weighted_receipts = []
    joint_row_cache: dict[int, np.ndarray] = {}
    weight_row_cache: dict[int, np.ndarray] = {}

    def binary_rows(accessor: int, *, dtype: type) -> np.ndarray:
        _, _, components, _, code = source.accessor_layout(accessor)
        start, row_count, row_stride = source.accessor_region(accessor)
        return np.asarray([
            struct.unpack_from("<" + code * components, binary, start + vertex * row_stride)
            for vertex in range(row_count)
        ], dtype=dtype)
    for branch_index, row in enumerate(weighted_branch_rows):
        source_slots = {joints.index(names[name]) for name in row["source_nodes"]}
        proximal_slot = joints.index(row["proximal"]["node"])
        distal_slot = joints.index(row["distal"]["node"])
        selector = row["selector"]
        lat_lo, lat_hi = map(float, selector["lateral_interval_m"])
        fwd_lo, fwd_hi = map(float, selector["forward_interval_m"])
        width = float(selector["blend_width_m"])
        changed = 0
        maximum_amount = 0.0
        physical_bundles: set[tuple[int, ...]] = set()
        physical_accessor_owners: dict[int, tuple[int, ...]] = {}
        for primitive_index, primitive in enumerate(primitives):
            attrs = primitive.get("attributes") if isinstance(primitive, Mapping) else None
            suffixes = sorted(
                key.removeprefix("JOINTS_") for key in attrs or {} if key.startswith("JOINTS_"))
            if (not isinstance(attrs, Mapping) or "POSITION" not in attrs or not suffixes
                    or any(not suffix.isdecimal() or f"WEIGHTS_{suffix}" not in attrs
                           for suffix in suffixes)):
                raise ContractError("rig preparation weighted branch requires complete skin attributes")
            position_accessor = _accessor_index(
                source, attrs["POSITION"], label="weighted branch POSITION",
                accessor_type="VEC3", component_types=(5126,))
            count = source.document["accessors"][position_accessor]["count"]
            joint_accessors = [_accessor_index(
                source, attrs[f"JOINTS_{suffix}"], label="weighted branch JOINTS",
                accessor_type="VEC4", component_types=(5121, 5123), expected_count=count)
                for suffix in suffixes]
            for accessor in joint_accessors:
                component = source.document["accessors"][accessor]["componentType"]
                if len(joints) - 1 > (255 if component == 5121 else 65535):
                    raise ContractError("rig preparation weighted branch exceeds joint index capacity")
            weight_accessors = [_accessor_index(
                source, attrs[f"WEIGHTS_{suffix}"], label="weighted branch WEIGHTS",
                accessor_type="VEC4", component_types=(5126,), expected_count=count)
                for suffix in suffixes]
            first_rows, bundle = admit_physical_skin_rows(
                position_accessor, joint_accessors, weight_accessors,
                bundles=physical_bundles,
                accessor_owners=physical_accessor_owners,
            )
            if not first_rows:
                continue
            positions = np.asarray(source.accessor_values(position_accessor), dtype=float)
            world_positions = (original_world[mesh_node] @ np.column_stack(
                (positions, np.ones(len(positions)))).T).T[:, :3]
            lateral = world_positions @ axes[0]
            up = world_positions @ axes[1]
            forward = world_positions @ axes[2]
            for accessor in joint_accessors:
                joint_row_cache.setdefault(
                    accessor, binary_rows(accessor, dtype=int))
            for accessor in weight_accessors:
                weight_row_cache.setdefault(
                    accessor, binary_rows(accessor, dtype=float))
            joint_rows = [joint_row_cache[a] for a in joint_accessors]
            weight_rows = [weight_row_cache[a] for a in weight_accessors]
            candidates = np.flatnonzero(
                (lateral >= lat_lo) & (lateral <= lat_hi)
                & (up <= float(selector["up_maximum_m"]))
                & (forward >= fwd_lo) & (forward <= fwd_hi))
            for vertex in candidates:
                key = (bundle, int(vertex))
                if key in claimed_vertices:
                    raise ContractError("rig preparation weighted branch selectors overlap")
                source_entries = [
                    (s, c) for s, jr in enumerate(joint_rows) for c in range(4)
                    if int(jr[vertex, c]) in source_slots and weight_rows[s][vertex, c] > 0.0]
                amount = float(sum(weight_rows[s][vertex, c] for s, c in source_entries))
                edge = min(
                    float(lateral[vertex] - lat_lo),
                    float(lat_hi - lateral[vertex]),
                    float(forward[vertex] - fwd_lo),
                    float(fwd_hi - forward[vertex]),
                    float(selector["up_maximum_m"] - up[vertex]),
                )
                gain = min(1.0, max(0.0, edge / width))
                gain = gain * gain * (3.0 - 2.0 * gain)
                amount *= gain
                if amount <= 1e-8:
                    continue
                claimed_vertices.add(key)
                for s, c in source_entries:
                    weight_rows[s][vertex, c] *= 1.0 - gain
                    if weight_rows[s][vertex, c] <= 1e-8:
                        weight_rows[s][vertex, c] = 0.0
                        joint_rows[s][vertex, c] = 0
                empty = [(s, c) for s, wr in enumerate(weight_rows) for c in range(4)
                         if wr[vertex, c] == 0.0]
                along = min(1.0, max(0.0, (float(forward[vertex]) - fwd_lo) / (fwd_hi - fwd_lo)))
                along = along * along * (3.0 - 2.0 * along)
                pieces = [(proximal_slot, amount * (1.0 - along)), (distal_slot, amount * along)]
                pieces = [(slot, value) for slot, value in pieces if value > 1e-8]
                if len(empty) < len(pieces):
                    raise ContractError("rig preparation weighted branch exceeds influence capacity")
                for (slot, value), (s, c) in zip(pieces, empty):
                    joint_rows[s][vertex, c] = slot
                    weight_rows[s][vertex, c] = value
                total = sum(float(wr[vertex].sum()) for wr in weight_rows)
                if not math.isclose(total, 1.0, abs_tol=2e-5, rel_tol=0.0):
                    raise ContractError("rig preparation weighted branch input weights are not normalized")
                changed += 1
                maximum_amount = max(maximum_amount, amount)
            for accessor, rows in zip(joint_accessors, joint_rows):
                _, _, _, _, code = source.accessor_layout(accessor)
                start, n, stride = source.accessor_region(accessor)
                for vertex in range(n):
                    struct.pack_into("<" + code * 4, binary, start + vertex * stride, *rows[vertex].tolist())
            for accessor, rows in zip(weight_accessors, weight_rows):
                _, _, _, _, code = source.accessor_layout(accessor)
                start, n, stride = source.accessor_region(accessor)
                for vertex in range(n):
                    struct.pack_into("<" + code * 4, binary, start + vertex * stride, *rows[vertex].tolist())
        if changed == 0:
            raise ContractError("rig preparation weighted branch selects no source influence")
        weighted_receipts.append({
            "role": row["role"], "parent": row["parent"],
            "source_nodes": list(row["source_nodes"]), "changed_vertex_count": changed,
            "maximum_transferred_weight": maximum_amount,
            "weighted_nodes": [row["proximal"]["name"], row["distal"]["name"]],
            "endpoint": row["endpoint"]["name"], "selector": deepcopy(selector),
        })

    matrices = []
    for node in joints:
        inverse = np.linalg.solve(output_world[node], mesh_world)
        if not np.isfinite(inverse).all():
            raise ContractError("rig preparation generated a non-finite inverse bind matrix")
        matrices.append(np.asarray(inverse, dtype=np.float32).T.reshape(-1))
    if weighted_branch_rows:
        while len(binary) % 4:
            binary.append(0)
        start = len(binary)
        matrix_bytes = np.asarray(matrices, dtype="<f4").tobytes()
        binary.extend(matrix_bytes)
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": start, "byteLength": len(matrix_bytes)})
        accessor = len(document["accessors"])
        document["accessors"].append({"bufferView": view, "componentType": 5126,
                                      "count": len(joints), "type": "MAT4"})
        document["skins"][skin_index]["inverseBindMatrices"] = accessor
        document["buffers"][0]["byteLength"] = len(binary)
    else:
        offset, count, stride = source.accessor_region(inverse_accessor)
        if count != len(joints):
            raise ContractError("rig preparation inverse bind count changed")
        for slot, matrix in enumerate(matrices):
            struct.pack_into("<16f", binary, offset + slot * stride, *matrix)

    config_bytes = json.dumps(config, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False, allow_nan=False).encode()
    document.pop("animations", None)
    document["extras"] = {**document.get("extras", {}), "eonwildRigPreparation": {
        "schema": SCHEMA, "id": config["id"], "source_sha256": config["source_sha256"],
        "config_sha256": _digest(config_bytes), "status": "NON_PROMOTED_CANDIDATE",
    }}
    raw = _encode(document, bytes(binary))
    reopened = Glb.from_bytes(raw)
    reopened_world = np.asarray(_world_matrices(
        reopened, reopened.rest_translation, reopened.rest_rotation, reopened.rest_scale), dtype=float)
    maximum_world_error = float(np.max(np.abs(reopened_world - desired_world)))
    maximum_skin_error, vertex_count = _skin_reconstruction_error(
        reopened, skin_index=skin_index, mesh_node=mesh_node)
    world_limit = (
        max(3e-6, maximum_scale_spread)
        if scale_policy is not None
        else 3e-6
    )
    if maximum_world_error > world_limit or maximum_skin_error > 3e-6:
        raise ContractError(
            "rig preparation exceeds reopened neutral preservation tolerance: "
            f"world={maximum_world_error:.9g}, skin={maximum_skin_error:.9g}"
        )
    receipt = {
        "schema": "eonwild.motion.rig-preparation-receipt.v1",
        "status": "NON_PROMOTED_CANDIDATE",
        "input_source_sha256": _digest(source.raw),
        "output_source_sha256": _digest(raw),
        "config_sha256": _digest(config_bytes),
        "coordinate": {
            "frame": coordinate["frame"],
            "lateral": axes[0].tolist(), "up": axes[1].tolist(),
            "forward": axes[2].tolist(),
        },
        "skin_index": skin_index,
        "joint_count": len(joints),
        "vertex_count": vertex_count,
        "animations": len(reopened.document.get("animations", [])),
        "reparented_nodes": [source.nodes[node].get("name", str(node)) for node in sorted(reparented)],
        "relocated_pivots": [source.nodes[node].get("name", str(node)) for node in sorted(pivot_nodes)],
        "added_endpoints": [
            {
                "name": row["name"],
                "parent": row["parent"],
                "world_origin_m": row["world_origin_m"].tolist(),
                "skin_influence": False,
            }
            for row in endpoint_rows
        ],
        "near_uniform_scale_normalization": {
            "policy": deepcopy(scale_policy),
            "nodes": normalized_scales,
        } if scale_policy is not None else None,
        "touched_local_transforms": touched,
        "articulations": articulation_rows,
        "weight_transfers": weight_transfer_rows,
        "weighted_branches": weighted_receipts,
        "measurements": {
            "maximum_input_neutral_skin_error_m": source_skin_error,
            "maximum_local_trs_projection_error": max(projection_errors, default=0.0),
            "maximum_reopened_world_matrix_error": maximum_world_error,
            "maximum_reopened_neutral_skin_error_m": maximum_skin_error,
        },
        "limits": {"reopened_world_matrix": world_limit, "neutral_skin_m": 3e-6},
        "limitations": list(config["limitations"]),
    }
    if vertex_count != source_vertex_count:
        raise ContractError("rig preparation changed the measured skin vertex count")
    return raw, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare an immutable, non-promoted neutral rig candidate")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ContractError("rig preparation output already exists")
        source = Glb(args.source)
        config = json.loads(args.config.read_text())
        raw, receipt = prepare_rig(source, config)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".rig-preparation-", dir=args.output.parent))
        try:
            (stage / "geometry.glb").write_bytes(raw)
            (stage / "config.json").write_bytes(args.config.read_bytes())
            (stage / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            stage.rename(args.output)
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except (MotionError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
