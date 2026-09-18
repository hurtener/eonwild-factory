#!/usr/bin/env python3
"""Exact emitted world-joint and foot-material loop check for one checkpoint."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np

from eonwild_motion.factory.emitted_tangent import (
    descendant_indices,
    endpoint_tangent,
    skinned_velocity,
)
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.glb.container import Glb


PRIMARY = Path("/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-closed-diagnostics-integration")
ARC = Path("/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521")
CHECKPOINT = ARC / "out/source-cubic-adult-v10-emission-checkpoint-f9ca924"
OUTPUT = ARC / "audits/root-source-cubic-adult-v10-f9ca924-001/world-material.json"
READER_HEAD = "f9ca924bcc79943d2d2b7eeab28bef8763c18ec4"
LINEAR_LIMIT_MPS = 0.001
READER_FILES = (
    "factory/emitted_tangent.py",
    "contact_gauge.py",
    "glb/animation.py",
    "glb/container.py",
    "layers/leg_contact_resolve_v3.py",
    "errors.py",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_labels_hash(labels: list[str]) -> str:
    return hashlib.sha256(json.dumps(labels, separators=(",", ":")).encode()).hexdigest()


def array_hash(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values, dtype="<f8")
    return hashlib.sha256(array.tobytes()).hexdigest()


def verify_bindings() -> tuple[dict, dict, dict]:
    manifest_path = CHECKPOINT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest["files"].items():
        actual = sha(CHECKPOINT / name)
        if actual != expected:
            raise RuntimeError(f"checkpoint payload hash mismatch: {name}")
    if any(
        not isinstance(name, str)
        or not isinstance(expected, str)
        or len(expected) != 64
        or any(character not in "0123456789abcdef" for character in expected)
        for name, expected in manifest["engine_files"].items()
    ):
        raise RuntimeError("checkpoint generator engine hash inventory is malformed")
    for name, expected in manifest["engine_files"].items():
        blob = subprocess.check_output(["git", "show", "f9ca924bcc79943d2d2b7eeab28bef8763c18ec4:src/eonwild_motion/" + name], cwd=PRIMARY)
        if hashlib.sha256(blob).hexdigest() != expected:
            raise RuntimeError(f"pinned generator blob mismatch: {name}")
    reader_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=PRIMARY, text=True
    ).strip()
    if reader_head != READER_HEAD:
        raise RuntimeError("published reader head changed")
    for name in READER_FILES:
        if sha(PRIMARY / "src/eonwild_motion" / name) != manifest["engine_files"][name]:
            raise RuntimeError(f"published exact reader dependency mismatch: {name}")

    recipe_path = PRIMARY / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v10.json"
    if sha(recipe_path) != manifest["recipe_sha256"]:
        raise RuntimeError("adult-walk.v10 recipe hash mismatch")
    recipe = json.loads(recipe_path.read_text())
    binding_paths = {
        "contact_profile": recipe["contact_profile"]["path"],
        "performance_profile": recipe["performance_profile"]["path"],
        "program_profile": recipe["program_profile"]["path"],
        "rig": recipe["rig"]["path"],
        "source": recipe["source"]["path"],
        "animal": recipe["animal"]["path"],
        "articulation_profile": recipe["articulation_profile"]["path"],
    }
    for name, relative in binding_paths.items():
        if sha(PRIMARY / relative) != manifest["inputs"][name]:
            raise RuntimeError(f"adult-walk.v10 input hash mismatch: {name}")
    contact = json.loads((PRIMARY / recipe["contact_profile"]["path"]).read_text())
    rig = json.loads((PRIMARY / recipe["rig"]["path"]).read_text())
    plan = json.loads((CHECKPOINT / "plan.json").read_text())
    return manifest, recipe, {
        "contact": contact,
        "rig": rig,
        "plan": plan,
    }


def endpoints(path: Path, clip_name: str) -> tuple[Glb, object, object, np.ndarray]:
    glb = Glb(path)
    _, times = read_animation_tracks(glb, clip_name, require_common_timeline=True)
    incoming = endpoint_tangent(
        glb, clip_name, endpoint=len(times) - 1, terminal=True
    )
    outgoing = endpoint_tangent(glb, clip_name, endpoint=0, terminal=False)
    return glb, incoming, outgoing, np.asarray(times, dtype=float)


def maximum_witness(
    labels: list[str], incoming: np.ndarray, outgoing: np.ndarray
) -> tuple[float, dict]:
    differences = np.linalg.norm(incoming - outgoing, axis=1)
    if not np.isfinite(differences).all():
        raise RuntimeError("exact emitted velocity difference is non-finite")
    index = int(np.argmax(differences))
    return float(differences[index]), {
        "index": index,
        "label": labels[index],
        "incoming_m_per_s": incoming[index].tolist(),
        "outgoing_m_per_s": outgoing[index].tolist(),
        "difference_m_per_s": float(differences[index]),
    }


def main() -> None:
    manifest, recipe, bound = verify_bindings()
    contact, rig, plan = bound["contact"], bound["rig"], bound["plan"]
    forward = np.asarray(recipe["forward_axis"], dtype=float)
    if forward.shape != (3,) or not np.isfinite(forward).all() or abs(np.linalg.norm(forward) - 1) > 1e-9:
        raise RuntimeError("adult-walk.v10 forward axis is invalid")

    glbs: dict[str, Glb] = {}
    incoming: dict[str, object] = {}
    outgoing: dict[str, object] = {}
    times: dict[str, np.ndarray] = {}
    for mode in ("root_motion", "in_place"):
        path = CHECKPOINT / f"{mode}.glb"
        raw = Glb(path)
        animations = raw.document.get("animations", [])
        if len(animations) != 1 or not isinstance(animations[0].get("name"), str):
            raise RuntimeError(f"{mode} checkpoint must contain one named animation")
        glbs[mode], incoming[mode], outgoing[mode], times[mode] = endpoints(
            path, animations[0]["name"]
        )
    if not np.array_equal(times["root_motion"], times["in_place"]):
        raise RuntimeError("root-motion and in-place timelines differ")
    plan_times = np.asarray([row["time_s"] for row in plan["samples"]], dtype=float)
    if plan_times.shape != times["root_motion"].shape or np.max(np.abs(plan_times - times["root_motion"])) > 2e-6:
        raise RuntimeError("checkpoint plan and serialized timeline differ")

    root_name = rig["roles"]["root"]
    root_nodes = {mode: glbs[mode].name_to_node[root_name] for mode in glbs}
    motor = {
        "incoming": (
            incoming["root_motion"].world_velocity[root_nodes["root_motion"], :3, 3]
            - incoming["in_place"].world_velocity[root_nodes["in_place"], :3, 3]
        ),
        "outgoing": (
            outgoing["root_motion"].world_velocity[root_nodes["root_motion"], :3, 3]
            - outgoing["in_place"].world_velocity[root_nodes["in_place"], :3, 3]
        ),
    }
    for value in motor.values():
        if not np.isfinite(value).all():
            raise RuntimeError("serialized root motor velocity is non-finite")

    result_modes = {}
    reconstructed: dict[str, dict[str, np.ndarray | list[str]]] = {}
    for mode in ("root_motion", "in_place"):
        glb = glbs[mode]
        descendants = descendant_indices(glb, root_nodes[mode])
        names = [incoming[mode].names[index] for index in descendants]
        if names != [outgoing[mode].names[index] for index in descendants]:
            raise RuntimeError(f"{mode} endpoint topology differs")
        incoming_motor = motor["incoming"] if mode == "in_place" else np.zeros(3)
        outgoing_motor = motor["outgoing"] if mode == "in_place" else np.zeros(3)
        world_in = incoming[mode].world_velocity[descendants, :3, 3] + incoming_motor
        world_out = outgoing[mode].world_velocity[descendants, :3, 3] + outgoing_motor

        skin_labels_in, skin_in = skinned_velocity(glb, contact, incoming[mode])
        skin_labels_out, skin_out = skinned_velocity(glb, contact, outgoing[mode])
        if skin_labels_in != skin_labels_out:
            raise RuntimeError(f"{mode} ordered foot-material endpoint labels differ")
        skin_in = skin_in + incoming_motor
        skin_out = skin_out + outgoing_motor
        world_max, world_witness = maximum_witness(names, world_in, world_out)
        skin_max, skin_witness = maximum_witness(skin_labels_in, skin_in, skin_out)
        result_modes[mode] = {
            "frame_treatment": (
                "serialized root-motion world velocity; no added motor"
                if mode == "root_motion"
                else "serialized in-place world velocity plus exact root-motion minus in-place root velocity at each endpoint"
            ),
            "timeline": {
                "keys": len(times[mode]),
                "start_s": float(times[mode][0]),
                "end_s": float(times[mode][-1]),
                "incoming_neighbor_s": float(incoming[mode].neighbor_time_s),
                "outgoing_neighbor_s": float(outgoing[mode].neighbor_time_s),
            },
            "world_joints": {
                "count": len(names),
                "ordered_labels_sha256": canonical_labels_hash(names),
                "incoming_float64_sha256": array_hash(world_in),
                "outgoing_float64_sha256": array_hash(world_out),
                "maximum_velocity_difference_m_per_s": world_max,
                "witness": world_witness,
                "status_against_1mm_per_s": "PASS" if world_max <= LINEAR_LIMIT_MPS else "BLOCKED",
            },
            "ordered_full_foot_material": {
                "count": len(skin_labels_in),
                "ordered_labels_sha256": canonical_labels_hash(skin_labels_in),
                "incoming_float64_sha256": array_hash(skin_in),
                "outgoing_float64_sha256": array_hash(skin_out),
                "maximum_velocity_difference_m_per_s": skin_max,
                "witness": skin_witness,
                "status_against_1mm_per_s": "PASS" if skin_max <= LINEAR_LIMIT_MPS else "BLOCKED",
            },
        }
        reconstructed[mode] = {
            "names": names,
            "world_in": world_in,
            "world_out": world_out,
            "skin_labels": skin_labels_in,
            "skin_in": skin_in,
            "skin_out": skin_out,
        }

    if reconstructed["root_motion"]["names"] != reconstructed["in_place"]["names"]:
        raise RuntimeError("motion-mode world label order differs")
    if reconstructed["root_motion"]["skin_labels"] != reconstructed["in_place"]["skin_labels"]:
        raise RuntimeError("motion-mode skin label order differs")
    cross_mode = {}
    for layer, first, second in (
        ("world_incoming", "world_in", "world_in"),
        ("world_outgoing", "world_out", "world_out"),
        ("skin_incoming", "skin_in", "skin_in"),
        ("skin_outgoing", "skin_out", "skin_out"),
    ):
        delta = np.linalg.norm(
            reconstructed["root_motion"][first] - reconstructed["in_place"][second], axis=1
        )
        cross_mode[layer] = float(np.max(delta))

    plan_distance = float(plan["samples"][-1]["root_forward_m"] - plan["samples"][0]["root_forward_m"])
    plan_average_speed = plan_distance / float(plan_times[-1] - plan_times[0])
    motor_facts = {}
    for endpoint, value in motor.items():
        projection = float(value @ forward)
        off_axis = float(np.linalg.norm(value - projection * forward))
        motor_facts[endpoint] = {
            "velocity_m_per_s": value.tolist(),
            "forward_projection_m_per_s": projection,
            "off_axis_m_per_s": off_axis,
            "difference_from_plan_average_forward_speed_m_per_s": projection - plan_average_speed,
        }

    result = {
        "schema": "eonwild.motion.source-cubic-world-material-checkpoint.v1",
        "classification": "Independent exact serialized adult endpoint validation; not interval, visual, biological, Unity, or production acceptance.",
        "reader": {
            "head": READER_HEAD,
            "emitted_tangent_sha256": sha(PRIMARY / "src/eonwild_motion/factory/emitted_tangent.py"),
        },
        "checkpoint": {
            "path": str(CHECKPOINT),
            "generator_source_observation": {
                "commit": "f9ca924bcc79943d2d2b7eeab28bef8763c18ec4",
                "classification": "Pinned committed generator; all checkpoint engine file hashes checked against exact committed blobs.",
                "replay_dependency": False,
            },
            "manifest_sha256": sha(CHECKPOINT / "manifest.json"),
            "files": manifest["files"],
            "recipe_sha256": manifest["recipe_sha256"],
            "inputs": manifest["inputs"],
            "all_manifest_file_engine_and_input_hashes_verified": True,
        },
        "root_motor": {
            "authority": "Exact difference between serialized root-motion and in-place root-node world tangents at each endpoint; plan average is diagnostic only.",
            "declared_forward_axis": forward.tolist(),
            "plan_cycle_distance_m": plan_distance,
            "plan_average_forward_speed_m_per_s": plan_average_speed,
            "endpoints": motor_facts,
        },
        "modes": result_modes,
        "cross_mode_after_exact_motor_reconstruction_maximum_m_per_s": cross_mode,
        "limits": {
            "linear_velocity_m_per_s": LINEAR_LIMIT_MPS,
            "scope": "World node origins under exact FK and ordered sole-plus-toe LBS material points selected by the hash-bound contact profile. Does not validate arbitrary skin vertices, intervals, contact, ROM, visual quality, or whole-package gates.",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
