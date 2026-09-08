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
    config = _exact_object(config, {
        "schema", "id", "source_sha256", "skin_index", "reparents",
        "coordinate", "pivot_relocations", "articulations", "evidence", "limitations",
    }, "rig preparation")
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
    skin = skins[skin_index]
    if not isinstance(skin, Mapping) or not isinstance(skin.get("joints"), list):
        raise ContractError("rig preparation requires a joint skin")
    joints = list(skin["joints"])
    if any(type(node) is not int or not 0 <= node < len(source.nodes) for node in joints):
        raise ContractError("rig preparation skin has an invalid joint index")
    if len(set(joints)) != len(joints):
        raise ContractError("rig preparation skin joints must be unique")
    joint_set = set(joints)
    names = source.name_to_node

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
    original_parents = _parents(nodes)
    original_world = np.asarray(_world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale), dtype=float)
    if not np.isfinite(original_world).all():
        raise ContractError("rig preparation source world matrices are non-finite")

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

    new_parents = _parents(nodes)
    pivots = config["pivot_relocations"]
    if not isinstance(pivots, list):
        raise ContractError("rig preparation pivot relocations must be an array")
    desired_world = original_world.copy()
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

    articulations = config["articulations"]
    if not isinstance(articulations, list):
        raise ContractError("rig preparation articulations must be an array")
    articulation_rows = []
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
    projection_errors: list[float] = []
    for node in sorted(range(len(nodes)), key=depth):
        parent = new_parents[node]
        parent_world = np.eye(4) if parent is None else output_world[parent]
        target = desired_world[node]
        local = np.linalg.solve(parent_world, target)
        old_parent = original_parents[node]
        old_parent_world = np.eye(4) if old_parent is None else original_world[old_parent]
        old_local = np.linalg.solve(old_parent_world, original_world[node])
        changed = parent != old_parent or not np.allclose(local, old_local, atol=1e-12, rtol=0.0)
        if changed:
            translation, rotation, scale, diagnostic = _decompose_bind_local(
                local, label=f"prepared local[{node}]")
            entry = nodes[node]
            entry.pop("matrix", None)
            entry["translation"], entry["rotation"], entry["scale"] = translation, rotation, scale
            touched.append(entry.get("name", f"node_{node}"))
            projection_errors.append(diagnostic["linear_projection_error"])
        output_world[node] = target

    mesh_nodes = [index for index, node in enumerate(nodes) if node.get("skin") == skin_index]
    if len(mesh_nodes) != 1:
        raise ContractError("rig preparation requires exactly one mesh node for the selected skin")
    mesh_node = mesh_nodes[0]
    mesh_world = output_world[mesh_node]
    inverse_accessor = _accessor_index(
        source, skin.get("inverseBindMatrices"), label="rig preparation inverse bind",
        accessor_type="MAT4", component_types=(5126,), expected_count=len(joints))
    binary = bytearray(source.binary)
    offset, count, stride = source.accessor_region(inverse_accessor)
    if count != len(joints):
        raise ContractError("rig preparation inverse bind count changed")
    for slot, node in enumerate(joints):
        inverse = np.linalg.solve(output_world[node], mesh_world)
        if not np.isfinite(inverse).all():
            raise ContractError("rig preparation generated a non-finite inverse bind matrix")
        struct.pack_into("<16f", binary, offset + slot * stride,
                         *np.asarray(inverse, dtype=np.float32).T.reshape(-1))

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
    if maximum_world_error > 3e-6 or maximum_skin_error > 3e-6:
        raise ContractError("rig preparation exceeds reopened neutral preservation tolerance")
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
        "touched_local_transforms": touched,
        "articulations": articulation_rows,
        "measurements": {
            "maximum_local_trs_projection_error": max(projection_errors, default=0.0),
            "maximum_reopened_world_matrix_error": maximum_world_error,
            "maximum_reopened_neutral_skin_error_m": maximum_skin_error,
        },
        "limits": {"reopened_world_matrix": 3e-6, "neutral_skin_m": 3e-6},
        "limitations": list(config["limitations"]),
    }
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
