"""Bind an authored standing pose above an immutable skin bind reference."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError, MotionError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _world_matrices
from ..solve.airborne_gait import (
    _between,
    _interior,
    _local_delta,
    _qmul,
    _rotation_from_matrix,
    _world_rotation,
)
from ..solve.skin_rig import SkinRig
from ..solve.whole_body_gait_transition import _encode


SCHEMA = "eonwild.motion.standing-pose-preparation.v1"


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be finite")
    return result


def _axis(value: Any, label: str) -> np.ndarray:
    try:
        result = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label} must be a unit three-vector") from exc
    if (
        result.shape != (3,)
        or not np.isfinite(result).all()
        or not math.isclose(float(np.linalg.norm(result)), 1.0, abs_tol=1e-8)
    ):
        raise ContractError(f"{label} must be a unit three-vector")
    return result


def _angles(
    worlds: np.ndarray, chain: list[int], forward: np.ndarray, up: np.ndarray
) -> dict[str, float]:
    hip, knee, ankle, foot = (worlds[node, :3, 3] for node in chain)
    metatarsus = foot - ankle
    return {
        "hip_sagittal_degrees": math.degrees(
            math.atan2(float((knee - hip) @ forward), -float((knee - hip) @ up))
        ),
        "knee_interior_degrees": _interior(hip - knee, ankle - knee),
        "ankle_interior_degrees": _interior(knee - ankle, foot - ankle),
        "metatarsus_sagittal_degrees": math.degrees(
            math.atan2(float(metatarsus @ forward), -float(metatarsus @ up))
        ),
    }


def prepare_standing_pose(
    source: Glb,
    *,
    semantic_roles: Mapping[str, Any],
    contact_profile: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    """Create an animation-free standing source while retaining A-bind IBMs."""
    required = {
        "schema",
        "id",
        "version",
        "source_sha256",
        "coordinate",
        "model",
        "hip_sagittal_degrees",
        "knee_interior_degrees",
        "metatarsus_sagittal_degrees",
        "classification",
        "evidence",
        "limitations",
    }
    if not isinstance(config, Mapping) or set(config) != required:
        raise ContractError("standing preparation contains missing or unknown fields")
    if (
        config["schema"] != SCHEMA
        or config["model"] != "bilateral_semantic_sagittal_standing.v1"
        or not isinstance(config["id"], str)
        or not config["id"]
        or type(config["version"]) is not int
        or config["version"] < 1
    ):
        raise ContractError("unsupported standing preparation")
    if _digest(source.raw) != config["source_sha256"]:
        raise ContractError("standing preparation source bytes differ from its binding")
    if source.document.get("animations"):
        raise ContractError("standing preparation requires an animation-free source")
    coordinate = config["coordinate"]
    if (
        not isinstance(coordinate, Mapping)
        or set(coordinate) != {"frame", "lateral", "up", "forward"}
        or coordinate["frame"] != "source_world"
    ):
        raise ContractError("standing preparation coordinate is invalid")
    lateral, up, forward = (
        _axis(coordinate[name], f"standing {name}")
        for name in ("lateral", "up", "forward")
    )
    axes = np.asarray((lateral, up, forward))
    if (
        not np.allclose(axes @ axes.T, np.eye(3), atol=1e-8, rtol=0)
        or np.linalg.det(axes) < 1 - 1e-8
    ):
        raise ContractError("standing axes must be right-handed orthonormal")
    hip_degrees = _finite(config["hip_sagittal_degrees"], "standing hip angle")
    knee_degrees = _finite(config["knee_interior_degrees"], "standing knee angle")
    metatarsus_degrees = _finite(
        config["metatarsus_sagittal_degrees"], "standing metatarsus angle"
    )
    if (
        not -89.0 < hip_degrees < 89.0
        or not 1.0 < knee_degrees < 179.0
        or not -89.0 < metatarsus_degrees < 89.0
    ):
        raise ContractError("standing angles are mathematically degenerate")
    if not isinstance(config["classification"], str) or not config["classification"]:
        raise ContractError("standing classification is required")
    if (
        not isinstance(config["evidence"], list)
        or not config["evidence"]
        or any(
            not isinstance(item, Mapping)
            or set(item) != {"confidence", "evidence_kind", "reference", "scope"}
            or any(not isinstance(value, str) or not value for value in item.values())
            for item in config["evidence"]
        )
    ):
        raise ContractError("standing evidence is required")
    if (
        not isinstance(config["limitations"], list)
        or not config["limitations"]
        or any(
            not isinstance(value, str) or not value for value in config["limitations"]
        )
    ):
        raise ContractError("standing limitations are required")

    try:
        root = source.name_to_node[semantic_roles["root"]]
        pelvis = source.name_to_node[semantic_roles["pelvis"]]
        chains = {
            side: [
                source.name_to_node[name]
                for name in semantic_roles["legs"][side]["contactChain"]
            ]
            for side in ("left", "right")
        }
    except (KeyError, TypeError) as exc:
        raise ContractError(
            "standing preparation requires semantic root and legs"
        ) from exc
    if any(len(chain) != 4 for chain in chains.values()):
        raise ContractError("standing preparation requires hip/knee/ankle/foot chains")
    if any(
        source.parents[child] != parent
        for chain in chains.values()
        for parent, child in zip(chain, chain[1:])
    ):
        raise ContractError("standing leg chain must follow actual parent topology")

    skin = SkinRig(source, semantic_roles, tuple(forward), tuple(up), contact_profile)
    contact_source = contact_profile.get("source")
    if not isinstance(contact_source, Mapping) or contact_source.get(
        "sha256"
    ) != _digest(source.raw):
        raise ContractError("standing contact profile is not bound to the source")
    roles_bytes = json.dumps(
        semantic_roles, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    contact_bytes = json.dumps(
        contact_profile, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    tr = [np.asarray(value, dtype=float).copy() for value in source.rest_translation]
    rot = [tuple(value) for value in source.rest_rotation]
    scales = [np.asarray(value, dtype=float).copy() for value in source.rest_scale]
    worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)
    before_angles = {
        side: _angles(worlds, chain, forward, up) for side, chain in chains.items()
    }
    before_joints = {
        side: {
            name: np.asarray(worlds[node, :3, 3], dtype=float).copy()
            for name, node in zip(("hip", "knee", "ankle", "mtp"), chain)
        }
        for side, chain in chains.items()
    }
    lengths: dict[str, dict[str, float]] = {}
    base_foot_rotations = {
        side: _rotation_from_matrix(worlds[chain[3]]) for side, chain in chains.items()
    }
    distal_nodes = {
        source.name_to_node[name]
        for side in ("left", "right")
        for name in (
            *semantic_roles["legs"][side]["contactChain"][3:],
            *(
                name
                for chain in semantic_roles["legs"][side]["toeChains"]
                for name in chain
            ),
        )
    }
    base_distal_rotations = {
        node: np.asarray(worlds[node, :3, :3], dtype=float).copy()
        for node in distal_nodes
    }
    base_pelvis_height = float(worlds[pelvis, :3, 3] @ up)
    ankle_reference_local: dict[str, tuple[float, ...]] = {}
    foot_reference_local: dict[str, tuple[float, ...]] = {}
    metatarsus_geometry: dict[str, tuple[float, float, np.ndarray]] = {}
    realized_metatarsus = {"left": metatarsus_degrees, "right": metatarsus_degrees}

    def apply_metatarsus(side: str, degrees: float) -> None:
        nonlocal worlds
        _, _, ankle, foot = chains[side]
        rot[ankle] = ankle_reference_local[side]
        rot[foot] = foot_reference_local[side]
        worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)
        vector, foot_lateral, foot_sagittal = metatarsus_geometry[side]
        desired = lateral * foot_lateral + foot_sagittal * (
            -up * math.cos(math.radians(degrees))
            + forward * math.sin(math.radians(degrees))
        )
        ankle_world = _qmul(
            _between(vector, desired), _rotation_from_matrix(worlds[ankle])
        )
        rot[ankle] = _world_rotation(source, worlds, ankle, ankle_world)
        worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)
        rot[foot] = _world_rotation(source, worlds, foot, base_foot_rotations[side])
        worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)

    for side, chain in chains.items():
        hip, knee, ankle, foot = chain
        hp, kp, ap, fp = (worlds[node, :3, 3] for node in (hip, knee, ankle, foot))
        upper_length, lower_length = (
            float(np.linalg.norm(kp - hp)),
            float(np.linalg.norm(ap - kp)),
        )
        lengths[side] = {"upper_m": upper_length, "lower_m": lower_length}
        upper_lateral = float((kp - hp) @ lateral)
        lower_lateral = float((ap - kp) @ lateral)
        upper_sagittal = math.sqrt(max(0.0, upper_length**2 - upper_lateral**2))
        lower_sagittal = math.sqrt(max(0.0, lower_length**2 - lower_lateral**2))
        cosine_delta = (
            -upper_length * lower_length * math.cos(math.radians(knee_degrees))
            - upper_lateral * lower_lateral
        ) / (upper_sagittal * lower_sagittal)
        if not -1.0 <= cosine_delta <= 1.0:
            raise ContractError(
                "standing knee target is incompatible with lateral geometry"
            )
        lower_degrees = hip_degrees - math.degrees(math.acos(cosine_delta))
        upper_direction = lateral * upper_lateral + upper_sagittal * (
            -up * math.cos(math.radians(hip_degrees))
            + forward * math.sin(math.radians(hip_degrees))
        )
        lower_direction = lateral * lower_lateral + lower_sagittal * (
            -up * math.cos(math.radians(lower_degrees))
            + forward * math.sin(math.radians(lower_degrees))
        )
        hip_world = _qmul(
            _between(kp - hp, upper_direction),
            _rotation_from_matrix(worlds[hip]),
        )
        rot[hip] = _world_rotation(source, worlds, hip, hip_world)
        worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)
        kp, ap = (worlds[node, :3, 3] for node in (knee, ankle))
        knee_world = _qmul(
            _between(ap - kp, lower_direction),
            _rotation_from_matrix(worlds[knee]),
        )
        rot[knee] = _world_rotation(source, worlds, knee, knee_world)
        worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)
        ap, fp = (worlds[node, :3, 3] for node in (ankle, foot))
        vector = fp - ap
        original_vector = before_joints[side]["mtp"] - before_joints[side]["ankle"]
        foot_lateral = float(original_vector @ lateral)
        foot_length = float(np.linalg.norm(vector))
        foot_sagittal = math.sqrt(max(0.0, foot_length**2 - foot_lateral**2))
        ankle_reference_local[side] = tuple(rot[ankle])
        foot_reference_local[side] = tuple(rot[foot])
        metatarsus_geometry[side] = (vector, foot_lateral, foot_sagittal)
        apply_metatarsus(side, metatarsus_degrees)

    def foot_minimum(side: str) -> float:
        return float(np.min(skin.skin(worlds, skin.foot_masks[side]) @ up))

    initial_minima = {side: foot_minimum(side) for side in ("left", "right")}
    high_side = max(initial_minima, key=initial_minima.get)
    low_side = "right" if high_side == "left" else "left"
    target_minimum = initial_minima[low_side]
    lo, hi = metatarsus_degrees - 3.0, metatarsus_degrees + 3.0
    apply_metatarsus(high_side, lo)
    f_lo = foot_minimum(high_side) - target_minimum
    apply_metatarsus(high_side, hi)
    f_hi = foot_minimum(high_side) - target_minimum
    if f_lo * f_hi > 0:
        raise ContractError("standing bilateral material refinement is not bracketed")
    for _ in range(32):
        mid = 0.5 * (lo + hi)
        apply_metatarsus(high_side, mid)
        value = foot_minimum(high_side) - target_minimum
        if value == 0 or hi - lo < 1e-9:
            break
        if f_lo * value <= 0:
            hi, f_hi = mid, value
        else:
            lo, f_lo = mid, value
    realized_metatarsus[high_side] = mid

    posed_skin = skin.skin(worlds)
    pre_shift_minima = {
        side: float(np.min(posed_skin[indices] @ up))
        for side, indices in skin.foot_masks.items()
    }
    shift = skin.ground - min(pre_shift_minima.values())
    tr[root] = tr[root] + _local_delta(source, worlds, root, up * shift)
    worlds = np.asarray(_world_matrices(source, tr, rot, scales), dtype=float)
    posed_skin = skin.skin(worlds)
    floor_minima = {
        side: float(np.min(posed_skin[indices] @ up))
        for side, indices in skin.foot_masks.items()
    }
    if any(abs(value - skin.ground) > 5e-5 for value in floor_minima.values()):
        raise ContractError(
            f"standing pose does not preserve bilateral material floor: {floor_minima}"
        )

    document = deepcopy(source.document)
    for node in {root, *(node for chain in chains.values() for node in chain)}:
        entry = document["nodes"][node]
        entry.pop("matrix", None)
        entry["translation"] = tr[node].tolist()
        entry["rotation"] = list(rot[node])
        entry["scale"] = scales[node].tolist()
    config_bytes = json.dumps(
        config, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    document.pop("animations", None)
    document["extras"] = {
        **document.get("extras", {}),
        "eonwildStandingPreparation": {
            "schema": SCHEMA,
            "id": config["id"],
            "version": config["version"],
            "source_sha256": config["source_sha256"],
            "config_sha256": _digest(config_bytes),
            "semantic_roles_sha256": _digest(roles_bytes),
            "contact_profile_sha256": _digest(contact_bytes),
            "bind_reference": "retained_source_inverse_bind_matrices",
        },
    }
    raw = _encode(document, source.binary)
    reopened = Glb.from_bytes(raw)
    reopened_skin = SkinRig(
        reopened,
        semantic_roles,
        tuple(forward),
        tuple(up),
        {
            **deepcopy(contact_profile),
            "source": {
                **deepcopy(contact_profile["source"]),
                "path": "derived-standing-source.glb",
                "sha256": _digest(raw),
            },
        },
    )
    reopened_worlds = reopened_skin.world(
        reopened.rest_translation, reopened.rest_rotation, reopened.rest_scale
    )
    reopened_points = reopened_skin.skin(reopened_worlds)
    if float(np.max(np.abs(reopened_points - posed_skin))) > 3e-6:
        raise ContractError("standing pose changed during serialization")
    after_angles = {
        side: _angles(reopened_worlds, chain, forward, up)
        for side, chain in chains.items()
    }
    after_joints = {
        side: {
            name: np.asarray(reopened_worlds[node, :3, 3], dtype=float).copy()
            for name, node in zip(("hip", "knee", "ankle", "mtp"), chain)
        }
        for side, chain in chains.items()
    }
    lateral_joint_coordinates = {
        state: {
            side: {name: float(point @ lateral) for name, point in values[side].items()}
            for side in ("left", "right")
        }
        for state, values in (("before", before_joints), ("after", after_joints))
    }
    stance_widths = {
        state: {
            name: abs(
                lateral_joint_coordinates[state]["right"][name]
                - lateral_joint_coordinates[state]["left"][name]
            )
            for name in ("hip", "knee", "ankle", "mtp")
        }
        for state in ("before", "after")
    }
    maximum_distal_orientation_difference = max(
        float(np.max(np.abs(reopened_worlds[node, :3, :3] - base)))
        for node, base in base_distal_rotations.items()
    )
    receipt = {
        "schema": "eonwild.motion.standing-pose-preparation-receipt.v1",
        "status": "ENGINEERING_CANDIDATE",
        "input_source_sha256": _digest(source.raw),
        "output_source_sha256": _digest(raw),
        "config_sha256": _digest(config_bytes),
        "semantic_roles_sha256": _digest(roles_bytes),
        "contact_profile_sha256": _digest(contact_bytes),
        "bind_reference": "retained_source_inverse_bind_matrices",
        "animations": len(reopened.document.get("animations", [])),
        "angles_degrees": {"before": before_angles, "after": after_angles},
        "realized_metatarsus_sagittal_degrees": realized_metatarsus,
        "joint_centers_source_world_m": {
            state: {
                side: {name: point.tolist() for name, point in values[side].items()}
                for side in ("left", "right")
            }
            for state, values in (("before", before_joints), ("after", after_joints))
        },
        "lateral_joint_coordinates_m": lateral_joint_coordinates,
        "stance_widths_m": stance_widths,
        "knee_delta_m": {
            side: {
                "source_world": (
                    after_joints[side]["knee"] - before_joints[side]["knee"]
                ).tolist(),
                "body_relative_to_hip": (
                    (after_joints[side]["knee"] - after_joints[side]["hip"])
                    - (before_joints[side]["knee"] - before_joints[side]["hip"])
                ).tolist(),
            }
            for side in ("left", "right")
        },
        "segment_lengths_m": lengths,
        "pelvis_height_change_m": float(
            reopened_worlds[pelvis, :3, 3] @ up - base_pelvis_height
        ),
        "root_floor_translation_m": shift,
        "material_ground_m": skin.ground,
        "bilateral_material_minimum_m": floor_minima,
        "maximum_reopened_skin_difference_m": float(
            np.max(np.abs(reopened_points - posed_skin))
        ),
        "maximum_retained_pad_toe_orientation_matrix_difference": (
            maximum_distal_orientation_difference
        ),
        "classification": config["classification"],
        "limitations": list(config["limitations"]),
    }
    return raw, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare an authored standing source")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--contact", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ContractError("standing preparation output must be new")
        source = Glb(args.source)
        rig = json.loads(args.rig.read_text())
        contact = json.loads(args.contact.read_text())
        config = json.loads(args.config.read_text())
        raw, receipt = prepare_standing_pose(
            source, semantic_roles=rig["roles"], contact_profile=contact, config=config
        )
        args.output.mkdir(parents=True)
        (args.output / "geometry.glb").write_bytes(raw)
        (args.output / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    except (MotionError, OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
