#!/usr/bin/env python3
"""Admit one prepared Allosaurus standing source and bind new catalog snapshots.

This is a source-bound migration tool. It never edits an existing catalog or
asset. The new standing source must reproduce the current prepared binary
payload, preserve the distal world frames and material floor, and move both
knees forward and upward in the declared source frame.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import numpy as np

from eonwild_motion.factory.__main__ import main as factory_main
from eonwild_motion.factory.animal import load_animal_instance
from eonwild_motion.factory.io import bind, digest, json_bytes, read_json
from eonwild_motion.factory.motion_set import resolve_motion_set_selection
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _rotation_from_matrix, _world_matrices
from eonwild_motion.planning.jaw_response import load_neutral_jaw_calibration
from eonwild_motion.solve.jaw_response import _posed_gap, _semantic_body_height


CURRENT_SOURCE_SHA256 = "f1ac3ddebc2b8471af1a55439d0631ed0d350a750e59edaa661a9cd76ced4684"
CURRENT_ANIMAL = Path("catalog/animals/allosaurus-composite-engineering.adult.v4.json")
CURRENT_CONTACT = Path("catalog/contacts/allosaurus-engineering.v4.json")
CURRENT_NEUTRAL = Path("catalog/calibration/allosaurus-engineering-neutral.v4.json")
CURRENT_SUPPORT = Path("catalog/calibration/allosaurus-engineering-support.v4.json")
CURRENT_BASELINE = Path("catalog/motion-baselines/allosaurus-engineering-locomotion.v5.json")
CURRENT_SET = Path("catalog/motion-sets/allosaurus-engineering-acquired-walk.v5.json")
FAST_INTENT = Path("catalog/motion-intents/heavy-biped.allosaurus-acquired-fast-walk.motion-set.v1.json")
RIG = Path("catalog/rigs/allosaurus-engineering.v2.json")
STANDING_CONFIG = Path("catalog/standing-preparation/allosaurus-engineering-standing.v1.json")

NEW_ANIMAL = Path("catalog/animals/allosaurus-composite-engineering.adult.v5.json")
NEW_CONTACT = Path("catalog/contacts/allosaurus-engineering.v5.json")
NEW_NEUTRAL = Path("catalog/calibration/allosaurus-engineering-neutral.v5.json")
NEW_SUPPORT = Path("catalog/calibration/allosaurus-engineering-support.v5.json")
NEW_BASELINE = Path("catalog/motion-baselines/allosaurus-engineering-locomotion.v6.json")
NEW_SET = Path("catalog/motion-sets/allosaurus-engineering-acquired-walk.v6.json")

SIDES = {
    "left": {
        "chain": ("Bone_023", "Bone_022", "Bone_021", "Bone_020"),
        "distal": ("Bone_021", "Bone_020", "Bone_019", "Bone_018", "AllosaurusToeEndpoint.L"),
    },
    "right": {
        "chain": ("Bone_029", "Bone_028", "Bone_027", "Bone_026"),
        "distal": ("Bone_027", "Bone_026", "Bone_025", "Bone_024", "AllosaurusToeEndpoint.R"),
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_document_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def require_regular_file(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"{label} must be a regular non-symlink file: {path}")
    return resolved


def world_state(source: Glb) -> np.ndarray:
    return np.asarray(
        _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale),
        dtype=np.float64,
    )


def exact_skin(source: Glb, worlds: np.ndarray) -> np.ndarray:
    mesh_nodes = [
        index for index, node in enumerate(source.nodes)
        if isinstance(node.get("mesh"), int) and isinstance(node.get("skin"), int)
    ]
    if len(mesh_nodes) != 1:
        raise RuntimeError("standing catalog requires exactly one skinned mesh node")
    mesh_node = source.nodes[mesh_nodes[0]]
    primitive = source.document["meshes"][mesh_node["mesh"]]["primitives"][0]
    skin = source.document["skins"][mesh_node["skin"]]
    positions = np.asarray(source.accessor_values(primitive["attributes"]["POSITION"]), dtype=np.float64)
    joint_ids = np.concatenate([
        np.asarray(source.accessor_values(primitive["attributes"][key]), dtype=np.int64)
        for key in ("JOINTS_0", "JOINTS_1")
    ], axis=1)
    weights = np.concatenate([
        np.asarray(source.accessor_values(primitive["attributes"][key]), dtype=np.float64)
        for key in ("WEIGHTS_0", "WEIGHTS_1")
    ], axis=1)
    totals = np.sum(weights, axis=1)
    if not np.isfinite(weights).all() or np.any(weights < 0) or np.any(totals <= 0):
        raise RuntimeError("standing catalog skin weights are invalid")
    weights /= totals[:, None]
    joint_nodes = np.asarray(skin["joints"], dtype=np.int64)
    inverse = np.asarray(source.accessor_values(skin["inverseBindMatrices"]), dtype=np.float64)
    inverse = inverse.reshape(-1, 4, 4).transpose(0, 2, 1)
    positions_h = np.column_stack((positions, np.ones(len(positions), dtype=np.float64)))
    transforms = worlds[joint_nodes] @ inverse
    output = np.einsum("nv,nvij,nj->ni", weights, transforms[joint_ids], positions_h)[:, :3]
    if not np.isfinite(output).all():
        raise RuntimeError("standing catalog reconstructed non-finite skin")
    return output


def angle_degrees(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    left, right = a - b, c - b
    cosine = float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def geometry_measurements(source: Glb, roles: dict[str, Any]) -> dict[str, Any]:
    worlds = world_state(source)
    skin = exact_skin(source, worlds)
    output: dict[str, Any] = {
        "material_floor_m": float(np.min(skin[:, 1])),
        "skin_length_m": float(np.ptp(skin[:, 2])),
        "pelvis_to_skin_floor_m": float(
            worlds[source.name_to_node[roles["pelvis"]], 1, 3] - np.min(skin[:, 1])
        ),
        "sides": {},
    }
    for side, specification in SIDES.items():
        chain = np.asarray([
            worlds[source.name_to_node[name], :3, 3] for name in specification["chain"]
        ], dtype=np.float64)
        distal = {
            name: {
                "world_matrix": worlds[source.name_to_node[name]].tolist(),
                "world_rotation_xyzw": list(_rotation_from_matrix(worlds[source.name_to_node[name]])),
            }
            for name in specification["distal"]
        }
        segments = np.linalg.norm(np.diff(chain, axis=0), axis=1)
        output["sides"][side] = {
            "chain_world_m": chain.tolist(),
            "segment_lengths_m": segments.tolist(),
            "hindlimb_length_m": float(np.sum(segments)),
            "knee_degrees": angle_degrees(chain[0], chain[1], chain[2]),
            "hip_world_m": chain[0].tolist(),
            "knee_world_m": chain[1].tolist(),
            "distal": distal,
        }
    return output


def matrix_rotation_error_degrees(before: np.ndarray, after: np.ndarray) -> float:
    if np.array_equal(before[:3, :3], after[:3, :3]):
        return 0.0
    qb = np.asarray(_rotation_from_matrix(before), dtype=np.float64)
    qa = np.asarray(_rotation_from_matrix(after), dtype=np.float64)
    dot = min(1.0, abs(float(np.dot(qb, qa))))
    return math.degrees(2.0 * math.acos(dot))


def standing_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"sides": {}}
    max_distal_translation = 0.0
    max_distal_rotation = 0.0
    max_segment_delta = 0.0
    for side in SIDES:
        old, new = before["sides"][side], after["sides"][side]
        hip_delta = np.asarray(new["hip_world_m"]) - np.asarray(old["hip_world_m"])
        knee_delta = np.asarray(new["knee_world_m"]) - np.asarray(old["knee_world_m"])
        segment_delta = np.asarray(new["segment_lengths_m"]) - np.asarray(old["segment_lengths_m"])
        max_segment_delta = max(max_segment_delta, float(np.max(np.abs(segment_delta))))
        distal = {}
        for name in SIDES[side]["distal"]:
            old_matrix = np.asarray(old["distal"][name]["world_matrix"], dtype=np.float64)
            new_matrix = np.asarray(new["distal"][name]["world_matrix"], dtype=np.float64)
            translation = float(np.linalg.norm(new_matrix[:3, 3] - old_matrix[:3, 3]))
            rotation = matrix_rotation_error_degrees(old_matrix, new_matrix)
            max_distal_translation = max(max_distal_translation, translation)
            max_distal_rotation = max(max_distal_rotation, rotation)
            distal[name] = {
                "translation_residual_m": translation,
                "rotation_residual_degrees": rotation,
            }
        result["sides"][side] = {
            "hip_world_delta_m": hip_delta.tolist(),
            "knee_world_delta_m": knee_delta.tolist(),
            "knee_body_relative_to_hip_delta_m": (knee_delta - hip_delta).tolist(),
            "knee_angle_delta_degrees": float(new["knee_degrees"] - old["knee_degrees"]),
            "segment_length_deltas_m": segment_delta.tolist(),
            "distal": distal,
        }
    result.update({
        "material_floor_delta_m": float(after["material_floor_m"] - before["material_floor_m"]),
        "pelvis_to_skin_floor_delta_m": float(after["pelvis_to_skin_floor_m"] - before["pelvis_to_skin_floor_m"]),
        "maximum_segment_length_delta_m": max_segment_delta,
        "maximum_distal_translation_residual_m": max_distal_translation,
        "maximum_distal_rotation_residual_degrees": max_distal_rotation,
    })
    return result


def set_quantity(document: dict[str, Any], key: str, value: float | list[float]) -> None:
    document["geometry_calibration"]["source_measurements"][key]["value"] = value
    document["geometry_calibration"]["source_measurements"][key]["source"] = {
        "citation": "source-bound standing preparation and exact full-influence reconstruction",
        "locator": key,
    }


def write_new(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(value)


def catalog_documents(
    root: Path,
    source_sha256: str,
    measurements: dict[str, Any],
    neutral_gap_m: float,
    neutral_body_height_m: float,
    template_documents: dict[Path, dict[str, Any]] | None = None,
    template_bindings: dict[Path, dict[str, str]] | None = None,
) -> dict[Path, dict[str, Any]]:
    templates = template_documents or {
        path: read_json(root / path)
        for path in (CURRENT_ANIMAL, CURRENT_CONTACT, CURRENT_NEUTRAL, CURRENT_SUPPORT, CURRENT_BASELINE, CURRENT_SET)
    }
    animal = deepcopy(templates[CURRENT_ANIMAL])
    animal["id"], animal["version"] = "allosaurus-composite-engineering.adult.v5", 5
    animal["geometry_calibration"]["source_geometry_sha256"] = source_sha256
    animal["limitations"] = [
        *animal["limitations"],
        "The default standing pose is an authored engineering calibration; it is not a fossil-derived habitual posture.",
    ]
    set_quantity(animal, "skin_length", measurements["skin_length_m"])
    set_quantity(animal, "pelvis_to_skin_floor", measurements["pelvis_to_skin_floor_m"])
    for side in SIDES:
        set_quantity(animal, f"{side}_semantic_segments", measurements["sides"][side]["segment_lengths_m"])
        set_quantity(animal, f"{side}_semantic_hindlimb", measurements["sides"][side]["hindlimb_length_m"])
    uniform_scale = float(load_animal_instance(animal, source_sha256=source_sha256)["uniform_scale"])

    contact = deepcopy(templates[CURRENT_CONTACT])
    contact["version"] = 5
    contact["geometry"]["ground"]["level_m"] = measurements["material_floor_m"]
    contact["source"] = {
        "path": f"assets/sha256/{source_sha256}.glb",
        "sha256": source_sha256,
        "clips": contact["source"]["clips"],
    }

    neutral = deepcopy(templates[CURRENT_NEUTRAL])
    neutral["id"], neutral["version"] = "allosaurus-engineering-neutral.v5", 5
    calibration = neutral["neutral_jaw_calibration"]
    calibration["source_geometry_sha256"] = source_sha256
    calibration["measured_body_height_m"] = neutral_body_height_m
    calibration["measured_minimum_gap_m"] = neutral_gap_m
    calibration["clearance_body_heights"] = neutral_gap_m / neutral_body_height_m
    neutral["classification"] = (
        "disabled neutral-jaw offset rebound to the standing-prepared source; sampled surface gap only"
    )

    support = deepcopy(templates[CURRENT_SUPPORT])
    support["id"], support["version"] = "allosaurus-engineering-support.v5", 5
    support["source_geometry_sha256"] = source_sha256
    support["limitations"] = [
        "The preferred support knee is the authored standing-preparation result, not biological validation.",
        "The fitted hip center remains uncertain within the visible proximal muscle volume.",
    ]
    for side in SIDES:
        values = measurements["sides"][side]
        support["sides"][side]["upper_length_m"] = values["segment_lengths_m"][0] * uniform_scale
        support["sides"][side]["lower_length_m"] = values["segment_lengths_m"][1] * uniform_scale
        support["sides"][side]["preferred_support_knee_degrees"] = values["knee_degrees"]
        support["sides"][side]["posture_evidence"] = (
            "source-bound authored standing preparation; engineering calibration, not habitual-pose biology"
        )

    documents: dict[Path, dict[str, Any]] = {
        NEW_ANIMAL: animal,
        NEW_CONTACT: contact,
        NEW_NEUTRAL: neutral,
        NEW_SUPPORT: support,
    }
    bindings = {path: {"path": path.as_posix(), "sha256": digest(json_bytes(value))}
                for path, value in documents.items()}

    baseline = deepcopy(templates[CURRENT_BASELINE])
    baseline["id"], baseline["version"] = "allosaurus-engineering-locomotion.v6", 6
    baseline["source"] = {
        "path": f"assets/sha256/{source_sha256}.glb",
        "sha256": source_sha256,
    }
    baseline["animal"] = bindings[NEW_ANIMAL]
    baseline["contact_profile"] = bindings[NEW_CONTACT]
    baseline["neutral_pose_profile"] = bindings[NEW_NEUTRAL]
    baseline["locomotion_response_policy"]["regimes"]["grounded"][
        "neutral_support_profile"
    ] = bindings[NEW_SUPPORT]
    documents[NEW_BASELINE] = baseline

    motion_set = deepcopy(templates[CURRENT_SET])
    motion_set["id"], motion_set["version"] = (
        "allosaurus-engineering-acquired-walk-motion-set.v6", 6
    )
    motion_set["baseline"] = {
        "path": NEW_BASELINE.as_posix(),
        "sha256": digest(json_bytes(baseline)),
    }
    fast_binding = (
        template_bindings[FAST_INTENT]
        if template_bindings is not None
        else bind(root, root / FAST_INTENT)
    )
    walk = next(entry for entry in motion_set["motions"] if entry["name"] == "walk")
    motion_set["motions"] = [walk, {"name": "fast-walk", "intent": fast_binding}]
    documents[NEW_SET] = motion_set
    return documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--prepared-source", type=Path, required=True)
    parser.add_argument("--standing-receipt", type=Path, required=True)
    parser.add_argument("--admission-output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    prepared_path = require_regular_file(args.prepared_source, "prepared standing source")
    standing_receipt_path = require_regular_file(args.standing_receipt, "standing receipt")
    receipt_path = args.receipt.resolve()
    admission_output = args.admission_output.resolve()
    if receipt_path.exists() or admission_output.exists():
        raise RuntimeError("standing regeneration outputs must be new")
    for relative in (*[NEW_ANIMAL, NEW_CONTACT, NEW_NEUTRAL, NEW_SUPPORT], NEW_BASELINE, NEW_SET):
        if (root / relative).exists():
            raise RuntimeError(f"standing catalog target already exists: {relative}")
    old_source_path = require_regular_file(
        root / f"assets/sha256/{CURRENT_SOURCE_SHA256}.glb", "current admitted source"
    )
    rig_path = require_regular_file(root / RIG, "semantic rig")
    standing_receipt_bytes = standing_receipt_path.read_bytes()
    standing_receipt = json.loads(standing_receipt_bytes)
    prepared_bytes = prepared_path.read_bytes()
    prepared_sha = digest(prepared_bytes)
    if (
        standing_receipt.get("schema") != "eonwild.motion.standing-pose-preparation-receipt.v1"
        or standing_receipt.get("status") != "ENGINEERING_CANDIDATE"
    ):
        raise RuntimeError("standing receipt schema differs")
    if (
        standing_receipt.get("input_source_sha256") != CURRENT_SOURCE_SHA256
        or standing_receipt.get("output_source_sha256") != prepared_sha
    ):
        raise RuntimeError("standing receipt does not bind the current source and prepared output")
    template_paths = (
        CURRENT_ANIMAL, CURRENT_CONTACT, CURRENT_NEUTRAL, CURRENT_SUPPORT,
        CURRENT_BASELINE, CURRENT_SET, FAST_INTENT, RIG, STANDING_CONFIG,
    )
    template_payloads = {
        path: require_regular_file(root / path, f"template {path}").read_bytes()
        for path in template_paths
    }
    template_documents = {path: json.loads(raw) for path, raw in template_payloads.items()}
    template_bindings_by_path = {
        path: {"path": path.as_posix(), "sha256": digest(raw)}
        for path, raw in template_payloads.items()
    }
    template_bindings = {
        path.as_posix(): binding for path, binding in template_bindings_by_path.items()
    }
    implementation_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    implementation_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
    ).strip()

    old_source_bytes = old_source_path.read_bytes()
    if digest(old_source_bytes) != CURRENT_SOURCE_SHA256:
        raise RuntimeError("current admitted source identity differs")
    old_source = Glb.from_bytes(old_source_bytes)
    prepared = Glb.from_bytes(prepared_bytes)
    if prepared.document.get("animations"):
        raise RuntimeError("prepared standing source must not contain animation")
    if prepared.binary != old_source.binary:
        raise RuntimeError("standing preparation changed geometry/skin binary payload")
    expected_preparation = {
        "schema": template_documents[STANDING_CONFIG]["schema"],
        "id": template_documents[STANDING_CONFIG]["id"],
        "version": template_documents[STANDING_CONFIG]["version"],
        "source_sha256": CURRENT_SOURCE_SHA256,
        "config_sha256": canonical_document_sha256(template_documents[STANDING_CONFIG]),
        "semantic_roles_sha256": canonical_document_sha256(template_documents[RIG]["roles"]),
        "contact_profile_sha256": canonical_document_sha256(template_documents[CURRENT_CONTACT]),
        "bind_reference": "retained_source_inverse_bind_matrices",
    }
    prepared_marker = prepared.document.get("extras", {}).get("eonwildStandingPreparation")
    if prepared_marker != expected_preparation:
        raise RuntimeError("prepared source marker differs from frozen standing inputs")
    for key in ("config_sha256", "semantic_roles_sha256", "contact_profile_sha256"):
        if standing_receipt.get(key) != expected_preparation[key]:
            raise RuntimeError(f"standing receipt {key} differs from frozen standing inputs")

    admission_input = admission_output.with_name(f"{admission_output.name}-input.glb")
    admission_rig = admission_output.with_name(f"{admission_output.name}-rig.json")
    if admission_input.exists() or admission_rig.exists():
        raise RuntimeError("standing admission snapshots already exist")
    admission_input.write_bytes(prepared_bytes)
    admission_rig.write_bytes(template_payloads[RIG])
    exit_code = factory_main([
        "admit", "--source", str(admission_input), "--rig", str(admission_rig),
        "--forward", "0", "0", "1", "--output", str(admission_output),
    ])
    if exit_code != 0:
        raise RuntimeError(f"public standing-source admission failed: {exit_code}")
    admitted_path = admission_output / "geometry.glb"
    admitted_receipt = read_json(admission_output / "admission.json")
    admitted_sha = sha(admitted_path)
    if admitted_receipt["files"]["geometry.glb"] != admitted_sha:
        raise RuntimeError("standing admission receipt does not bind geometry")
    admitted = Glb(admitted_path)
    if admitted.binary != old_source.binary or admitted.document.get("animations"):
        raise RuntimeError("standing admission changed binary payload or retained animation")
    prepared_worlds = world_state(prepared)
    admitted_worlds = world_state(admitted)
    prepared_skin = exact_skin(prepared, prepared_worlds)
    admitted_skin = exact_skin(admitted, admitted_worlds)
    if prepared_skin.shape != admitted_skin.shape:
        raise RuntimeError("standing admission changed skinned vertex count")
    admission_skin_residual = float(np.max(np.linalg.norm(prepared_skin - admitted_skin, axis=1)))
    if admission_skin_residual > 1.0e-12:
        raise RuntimeError("standing admission changed exact full-influence rest skin")

    roles = template_documents[RIG]["roles"]
    before = geometry_measurements(old_source, roles)
    after = geometry_measurements(admitted, roles)
    delta = standing_delta(before, after)
    declared_floor = float(standing_receipt["material_ground_m"])
    if abs(after["material_floor_m"] - declared_floor) > 1.0e-9:
        raise RuntimeError("standing preparation does not match its declared material floor")
    if delta["maximum_segment_length_delta_m"] > 1.0e-7:
        raise RuntimeError("standing preparation changed semantic segment lengths")
    for side in SIDES:
        knee_relative = delta["sides"][side]["knee_body_relative_to_hip_delta_m"]
        if knee_relative[1] <= 0 or knee_relative[2] <= 0:
            raise RuntimeError(
                f"standing preparation did not move {side} knee upward and forward relative to the hip"
            )
        for name in SIDES[side]["distal"][1:]:
            if delta["sides"][side]["distal"][name]["rotation_residual_degrees"] > 1.0e-5:
                raise RuntimeError(f"standing preparation rotated retained {side} {name} world frame")

    seed = load_neutral_jaw_calibration(template_documents[CURRENT_NEUTRAL]["neutral_jaw_calibration"])
    rebound = replace(seed, source_geometry_sha256=admitted_sha)
    _, _, jaw_gap = _posed_gap(admitted, roles, rebound, (0, 0, 1), (0, 1, 0))
    body_height = _semantic_body_height(admitted, roles, (0, 1, 0))
    documents = catalog_documents(
        root,
        admitted_sha,
        after,
        jaw_gap,
        body_height,
        template_documents,
        template_bindings_by_path,
    )
    asset_path = root / f"assets/sha256/{admitted_sha}.glb"
    if asset_path.exists():
        if sha(asset_path) != admitted_sha:
            raise RuntimeError("existing content-addressed standing asset differs")
    else:
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(admitted_path, asset_path)
        if sha(asset_path) != admitted_sha:
            raise RuntimeError("content-addressed standing asset copy differs")
    for relative, document in documents.items():
        write_new(root / relative, json_bytes(document))

    resolutions = resolve_motion_set_selection(root, root / NEW_SET, ["walk", "fast-walk"])
    result = {
        "schema": "eonwild.allosaurus.standing-catalog-regeneration.v1",
        "status": "CATALOG_REGENERATED_NOT_COMPILED",
        "implementation_head_before_catalog_write": implementation_head,
        "implementation_tree_before_catalog_write": implementation_tree,
        "generator": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha(Path(__file__).resolve()),
        },
        "inputs": {
            "current_source": {
                "path": old_source_path.relative_to(root).as_posix(),
                "sha256": digest(old_source_bytes),
            },
            "prepared_source": {"path": str(prepared_path), "sha256": prepared_sha},
            "admission_input_snapshot": {"path": str(admission_input), "sha256": digest(prepared_bytes)},
            "admission_rig_snapshot": {"path": str(admission_rig), "sha256": digest(template_payloads[RIG])},
            "standing_receipt": {
                "path": str(standing_receipt_path),
                "sha256": digest(standing_receipt_bytes),
            },
            "rig": template_bindings_by_path[RIG],
            "templates": template_bindings,
        },
        "admission": {
            "output": str(admission_output),
            "geometry_sha256": admitted_sha,
            "receipt_sha256": sha(admission_output / "admission.json"),
            "maximum_full_influence_skin_residual_m": admission_skin_residual,
        },
        "measurements": {"before": before, "after": after, "delta": delta},
        "neutral_jaw": {
            "measured_body_height_m": body_height,
            "measured_minimum_gap_m": jaw_gap,
            "clearance_body_heights": jaw_gap / body_height,
        },
        "catalog": {
            relative.as_posix(): digest(json_bytes(document))
            for relative, document in documents.items()
        },
        "resolution": [
            {
                "motion": resolution.motion,
                "set": resolution.set_binding,
                "baseline": resolution.baseline_binding,
                "intent": resolution.intent_binding,
            }
            for resolution in resolutions
        ],
        "technical_status": "NOT_RUN",
        "visual_status": "PENDING_NEUTRAL_REVIEW",
        "unity_status": "NOT_RUN",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    write_new(receipt_path, json_bytes(result))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
