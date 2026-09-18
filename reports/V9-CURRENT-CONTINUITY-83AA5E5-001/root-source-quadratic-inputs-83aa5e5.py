#!/usr/bin/env python3
"""Bounded source-law interface probe for walk.v3 start/steady/stop.

This diagnostic samples the bound planners and existing row solver directly.
It does not read emitted animation, apply skin-target refinements, interpolate a
correction table, fit a boundary, or claim that finite differences are formal
derivatives.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.math.quaternion import inverse, multiply, to_rotation_vector
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.gait_transition import (
    GaitTransition,
    build_transition_plan,
    declared_handoff_phase,
    load_gait_transition,
)
from eonwild_motion.planning.grounded_gait import (
    GroundedGait,
    build_grounded_plan,
    load_grounded_gait,
)
from eonwild_motion.solve.gaze import calibrate_rostral_direction
from eonwild_motion.solve.performance import decorate_plan, load_performance
from eonwild_motion.solve.source_motion_query import SourceMotionQuery, SourceMotionResult


REPO = Path("/Volumes/m2-extended-disk/Repos/eonwild-factory")
OUT = Path(__file__).resolve().parent
RECIPES = {
    "steady": REPO / "recipes/heavy-biped/walk.v3.json",
    "start": REPO / "recipes/heavy-biped/walk-start.v3.json",
    "stop": REPO / "recipes/heavy-biped/walk-stop.v3.json",
}
H_VALUES = (1e-3, 3e-4, 1e-4, 3e-5)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


@dataclass(frozen=True)
class Program:
    label: str
    recipe: dict[str, Any]
    input_paths: dict[str, Path]
    source: Glb
    roles: dict[str, Any]
    contact: dict[str, Any]
    grounded: GroundedGait
    solver: AirborneGait
    transition: GaitTransition | None
    plan: dict[str, Any]
    query: SourceMotionQuery
    forward: np.ndarray
    up: np.ndarray


def normalized_frame(recipe: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    forward = np.asarray(recipe["forward_axis"], dtype=float)
    up = np.asarray(recipe["up_axis"], dtype=float)
    forward /= np.linalg.norm(forward)
    up /= np.linalg.norm(up)
    if abs(float(forward @ up)) > 1e-10:
        raise RuntimeError("recipe axes are not orthogonal")
    return forward, up


def build(label: str) -> Program:
    recipe_path = RECIPES[label]
    recipe, paths = load_recipe(recipe_path, REPO)
    source = Glb.from_bytes(paths["source"].read_bytes())
    roles = json.loads(paths["rig"].read_text())["roles"]
    contact = json.loads(paths["contact_profile"].read_text())
    profile_path = paths["gait_profile"] if label != "steady" else paths["program_profile"]
    grounded = load_grounded_gait(json.loads(profile_path.read_text()))
    transition = None if label == "steady" else load_gait_transition(
        json.loads(paths["program_profile"].read_text())
    )
    sample_hz = grounded.sample_hz if transition is None else transition.sample_hz
    solver = AirborneGait(
        step_period_s=grounded.step_period_s,
        cycles=grounded.cycles,
        sample_hz=sample_hz,
        swing_hip_lift_degrees=grounded.swing_hip_lift_degrees,
    )
    forward, up = normalized_frame(recipe)
    height = geometry_height(source, roles, up)
    plan = (
        build_grounded_plan(grounded, height)
        if transition is None
        else build_transition_plan(transition, grounded, height)
    )
    performance = load_performance(json.loads(paths["performance_profile"].read_text()))
    plan = decorate_plan(plan, performance)
    # Match the compiler-owned pre-solve plan exactly. The plan remains
    # unrefined: it has no per-row target_offset_m correction table.
    plan["gaze_calibration"] = calibrate_rostral_direction(
        source,
        roles=roles,
        contact_profile=contact,
        forward_axis=forward,
        up_axis=up,
    )
    query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=grounded,
        transition=transition,
        plan=plan,
        contact_profile=contact,
        up_axis=tuple(float(value) for value in up),
        forward_axis=tuple(float(value) for value in forward),
        legacy_overlay=False,
    )
    return Program(
        label,
        recipe,
        paths,
        source,
        roles,
        contact,
        grounded,
        solver,
        transition,
        plan,
        query,
        forward,
        up,
    )


def evaluate(program: Program, time_s: float) -> SourceMotionResult:
    value = program.query.evaluate(time_s)
    if not isinstance(value, SourceMotionResult) or value.status != "AVAILABLE":
        raise RuntimeError(f"{program.label} source pose unavailable at {time_s}: {value}")
    return value


def node_names(source: Glb) -> list[str]:
    return [str(node.get("name", f"node_{index}")) for index, node in enumerate(source.nodes)]


def joint_indices(program: Program) -> list[int]:
    """Return the actual skeleton rooted at the semantic motion root."""
    root = program.source.name_to_node[program.roles["root"]]
    children: dict[int, list[int]] = {}
    for index, parent in enumerate(program.source.parents):
        if parent is not None:
            children.setdefault(parent, []).append(index)
    owned: set[int] = set()
    pending = [root]
    while pending:
        node = pending.pop()
        if node in owned:
            continue
        owned.add(node)
        pending.extend(children.get(node, ()))
    semantic_names = {
        program.roles["root"],
        program.roles["pelvis"],
        program.roles["chest"],
        program.roles["head"],
        *program.roles.get("spine", ()),
        *program.roles.get("neck", ()),
        *program.roles.get("tail", ()),
    }
    if program.roles.get("jaw_lower"):
        semantic_names.add(program.roles["jaw_lower"])
    for side in ("left", "right"):
        semantic_names.update(program.roles["legs"][side]["contactChain"])
        for chain in program.roles["legs"][side]["toeChains"]:
            semantic_names.update(chain)
    missing = sorted(
        name
        for name in semantic_names
        if program.source.name_to_node.get(name) not in owned
    )
    if missing:
        raise RuntimeError(f"semantic skeleton nodes outside motion root: {missing}")
    return sorted(owned)


def quaternion_delta(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Shortest local rotation vectors from a to b, in radians."""
    left = np.asarray(a, dtype=float)
    right = np.asarray(b, dtype=float).copy()
    left /= np.linalg.norm(left, axis=1, keepdims=True)
    right /= np.linalg.norm(right, axis=1, keepdims=True)
    right[np.sum(left * right, axis=1) < 0] *= -1
    return np.asarray(
        [to_rotation_vector(multiply(inverse(q0), q1)) for q0, q1 in zip(left, right)],
        dtype=float,
    )


def rate(center: SourceMotionResult, neighbor: SourceMotionResult, h: float, direction: str) -> dict[str, Any]:
    if direction == "backward":
        first, second = neighbor, center
    elif direction == "forward":
        first, second = center, neighbor
    else:
        raise ValueError(direction)
    material = {
        side: (second.material_points[side] - first.material_points[side]) / h
        for side in ("left", "right")
    }
    return {
        "local_translation_mps": (
            np.asarray(second.pose.translations, dtype=float)
            - np.asarray(first.pose.translations, dtype=float)
        ) / h,
        "local_angular_radps": quaternion_delta(
            np.asarray(first.pose.rotations, dtype=float),
            np.asarray(second.pose.rotations, dtype=float),
        ) / h,
        "world_node_mps": (second.worlds[:, :3, 3] - first.worlds[:, :3, 3]) / h,
        "material_mps": material,
    }


def max_rows(values: np.ndarray, labels: list[str]) -> dict[str, Any]:
    norms = np.linalg.norm(np.asarray(values, dtype=float), axis=1)
    index = int(np.argmax(norms))
    return {
        "maximum": float(norms[index]),
        "witness_index": index,
        "witness_label": labels[index],
        "witness_vector": np.asarray(values[index], dtype=float).tolist(),
    }


def max_material(values: dict[str, np.ndarray]) -> dict[str, Any]:
    rows = []
    labels = []
    for side in ("left", "right"):
        for index, vector in enumerate(values[side]):
            rows.append(vector)
            labels.append(f"{side}:{index}")
    return max_rows(np.asarray(rows), labels)


def exact_pose_difference(
    before: SourceMotionResult,
    after: SourceMotionResult,
    alignment: np.ndarray,
    names: list[str],
    joints: list[int],
) -> dict[str, Any]:
    world_delta = before.worlds[:, :3, 3] - alignment - after.worlds[:, :3, 3]
    material_delta = {
        side: before.material_points[side] - alignment - after.material_points[side]
        for side in ("left", "right")
    }
    local_rotation_delta = quaternion_delta(
        np.asarray(before.pose.rotations, dtype=float),
        np.asarray(after.pose.rotations, dtype=float),
    )
    return {
        "world_joint_position_m": max_rows(world_delta[joints], [names[i] for i in joints]),
        "ordered_material_position_m": max_material(material_delta),
        "local_rotation_radians": max_rows(
            local_rotation_delta[joints], [names[i] for i in joints]
        ),
    }


def rate_difference(
    left: dict[str, Any], right: dict[str, Any], names: list[str], joints: list[int]
) -> dict[str, Any]:
    joint_names = [names[i] for i in joints]

    def compared(a: np.ndarray, b: np.ndarray, labels: list[str]) -> dict[str, Any]:
        delta = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
        result = max_rows(delta, labels)
        index = int(result["witness_index"])
        result["before_estimate"] = np.asarray(a[index], dtype=float).tolist()
        result["after_estimate"] = np.asarray(b[index], dtype=float).tolist()
        return result

    material_left = np.concatenate(
        [left["material_mps"][side] for side in ("left", "right")], axis=0
    )
    material_right = np.concatenate(
        [right["material_mps"][side] for side in ("left", "right")], axis=0
    )
    material_labels = [
        f"{side}:{index}"
        for side in ("left", "right")
        for index in range(len(left["material_mps"][side]))
    ]
    return {
        "world_joint_velocity_mps": compared(
            left["world_node_mps"][joints], right["world_node_mps"][joints], joint_names
        ),
        "ordered_material_velocity_mps": compared(
            material_left, material_right, material_labels
        ),
        "local_translation_velocity_mps": compared(
            left["local_translation_mps"][joints],
            right["local_translation_mps"][joints],
            joint_names,
        ),
        "local_angular_velocity_radps": compared(
            left["local_angular_radps"][joints],
            right["local_angular_radps"][joints],
            joint_names,
        ),
    }


def row_witness(result: SourceMotionResult) -> dict[str, Any]:
    row = result.row
    return {
        "time_s": float(result.time_s),
        "root_forward_m": float(row["root_forward_m"]),
        "root_velocity_mps": float(row.get("root_velocity_mps", math.nan)),
        "root_acceleration_mps2": float(row.get("root_acceleration_mps2", math.nan)),
        "locomotion_time_s": float(row.get("locomotion_time_s", row["time_s"])),
        "performance_gain": float(row.get("performance_gain", 1.0)),
        "pelvis_height_offset_m": float(row["pelvis_height_offset_m"]),
        "pelvis_vertical_velocity_mps": float(row["pelvis_vertical_velocity_mps"]),
        "support_count": int(row["support_count"]),
        "feet": {
            side: {
                key: json_value(row["feet"][side].get(key))
                for key in (
                    "contact",
                    "forward_m",
                    "height_m",
                    "toe_flex_degrees",
                    "foot_pitch_degrees",
                    "swing_phase",
                    "touchdown_time_s",
                    "articulation_scale",
                )
                if key in row["feet"][side]
            }
            for side in ("left", "right")
        },
        "solver_branch_witness": json_value(result.branch_witness),
    }


def join_probe(
    label: str,
    before_program: Program,
    before_time: float,
    after_program: Program,
    after_time: float,
    paired_offset_side: str,
) -> dict[str, Any]:
    before_center = evaluate(before_program, before_time)
    after_center = evaluate(after_program, after_time)
    names = node_names(before_program.source)
    if names != node_names(after_program.source):
        raise RuntimeError("node correspondence differs")
    alignment = before_program.forward * (
        float(before_center.row["root_forward_m"])
        - float(after_center.row["root_forward_m"])
    )
    joints = joint_indices(before_program)
    if joints != joint_indices(after_program):
        raise RuntimeError("skeleton correspondence differs")
    exact = exact_pose_difference(before_center, after_center, alignment, names, joints)
    estimates = []
    for h in H_VALUES:
        before_neighbor = evaluate(before_program, before_time - h)
        after_neighbor = evaluate(after_program, after_time + h)
        if paired_offset_side == "minus":
            paired_before = before_neighbor
            paired_after = evaluate(after_program, after_time - h)
        elif paired_offset_side == "plus":
            paired_before = evaluate(before_program, before_time + h)
            paired_after = after_neighbor
        else:
            raise ValueError(paired_offset_side)
        paired_offset = exact_pose_difference(
            paired_before, paired_after, alignment, names, joints
        )
        before_rate = rate(before_center, before_neighbor, h, "backward")
        after_rate = rate(after_center, after_neighbor, h, "forward")
        estimates.append(
            {
                "h_s": h,
                "paired_pose_at_offsets": paired_offset,
                "one_sided_rate_difference": rate_difference(
                    before_rate, after_rate, names, joints
                ),
                "before_row": row_witness(before_neighbor),
                "after_row": row_witness(after_neighbor),
            }
        )
    return {
        "join": label,
        "before": before_program.label,
        "after": after_program.label,
        "before_interface_time_s": before_time,
        "after_interface_time_s": after_time,
        "travel_alignment_m": alignment.tolist(),
        "exact_interface": {
            "pose_difference": exact,
            "before_row": row_witness(before_center),
            "after_row": row_witness(after_center),
        },
        "finite_difference_estimates": estimates,
    }


def main() -> None:
    programs = {label: build(label) for label in ("steady", "start", "stop")}
    steady = programs["steady"]
    start = programs["start"]
    stop = programs["stop"]
    assert start.transition is not None and stop.transition is not None
    phase = declared_handoff_phase(start.transition, steady.grounded)
    if not math.isclose(phase, declared_handoff_phase(stop.transition, steady.grounded), rel_tol=0, abs_tol=0):
        raise RuntimeError("start and stop declare different handoff phases")

    joins = [
        join_probe(
            "walk-start.v3 terminal to walk.v3 declared phase",
            start,
            float(start.plan["duration_s"]),
            steady,
            phase,
            "minus",
        ),
        join_probe(
            "walk.v3 declared phase to walk-stop.v3 initial",
            steady,
            phase,
            stop,
            0.0,
            "plus",
        ),
    ]

    identities: dict[str, Any] = {}
    all_inputs: dict[str, dict[str, str]] = {}
    for label, program in programs.items():
        identities[label] = {
            "recipe_path": str(RECIPES[label].relative_to(REPO)),
            "recipe_sha256": digest(RECIPES[label]),
            "recipe_id": program.recipe["id"],
            "plan_duration_s": float(program.plan["duration_s"]),
            "plan_sample_count": len(program.plan["samples"]),
            "query_refined": bool(program.query.refined),
        }
        for key, path in program.input_paths.items():
            relative = str(path.relative_to(REPO))
            all_inputs[relative] = {"sha256": digest(path), "kind": key}

    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    )
    payload = {
        "schema": "eonwild.motion.audit.walk-v3-source-interface.v1",
        "classification": (
            "read-only source-planner/FK/LBS finite-difference diagnostic; "
            "not emitted continuity, formal derivative authority, skin-refined output, "
            "force/COM evidence, or production approval"
        ),
        "repository": {
            "path": str(REPO),
            "head": head,
            "working_tree_porcelain": status,
        },
        "driver": {"path": str(Path(__file__).resolve()), "sha256": digest(Path(__file__).resolve())},
        "python": sys.version,
        "coordinate_frame": {
            "forward": steady.forward.tolist(),
            "up": steady.up.tolist(),
            "world_alignment_rule": (
                "subtract forward*(before.root_forward_m-after.root_forward_m) "
                "from every before-side world/material point"
            ),
        },
        "world_joint_correspondence": {
            "definition": "all descendants of the semantic motion root, traversed by parent links",
            "count": len(joint_indices(steady)),
            "node_indices": joint_indices(steady),
            "node_names": [node_names(steady.source)[i] for i in joint_indices(steady)],
        },
        "ordered_material_correspondence": {
            side: {
                "count": len(steady.query._skin.foot_masks[side]),
                "source_vertex_indices": steady.query._skin.foot_masks[side].tolist(),
            }
            for side in ("left", "right")
        },
        "declared_interface": {
            "steady_phase_s": phase,
            "same_foot_cycle_s": 2 * steady.grounded.step_period_s,
            "phase_fraction": phase / (2 * steady.grounded.step_period_s),
            "contacts_at_interface": {
                side: bool(evaluate(steady, phase).row["feet"][side]["contact"])
                for side in ("left", "right")
            },
        },
        "recipes": identities,
        "locked_inputs": dict(sorted(all_inputs.items())),
        "h_values_s": list(H_VALUES),
        "joins": joins,
    }
    target = OUT / "result.json"
    target.write_text(
        json.dumps(json_value(payload), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(target)


if __name__ == "__main__":
    main()
