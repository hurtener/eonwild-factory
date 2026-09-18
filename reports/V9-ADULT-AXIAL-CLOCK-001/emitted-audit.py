from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from eonwild_motion.factory.animal import scaled_contact_profile
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import (
    _clip_state,
    _pose,
    _rotation_from_matrix,
    _world_position,
)
from eonwild_motion.solve.skin_rig import SkinRig, rotation_matrix


TASK = Path(
    "/Volumes/m2-extended-disk/Repos/eonwild-task-storage/"
    "01a07d0e-00b8-7a51-9095-c2da82025521"
)
ROOT = TASK / "worktrees/eonwild-adult-axial-clock"
PACKAGES = {
    "v8": TASK / "out/continuation-adult-v8-bind-pose-001",
    "axial": ROOT / "out/continuation-adult-v8-axial-clock-001/package",
}
OUTPUT = ROOT / "out/continuation-adult-v8-axial-clock-001/emitted-audit.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(value):
    value = np.asarray(value, dtype=float)
    return value / np.linalg.norm(value)


def rotation(world):
    return rotation_matrix(_rotation_from_matrix(world))


def rotation_vector_degrees(matrix):
    matrix = np.asarray(matrix, dtype=float)
    angle = math.acos(float(np.clip((np.trace(matrix) - 1) / 2, -1, 1)))
    if angle < 1e-12:
        return np.zeros(3)
    axis = np.asarray([
        matrix[2, 1] - matrix[1, 2],
        matrix[0, 2] - matrix[2, 0],
        matrix[1, 0] - matrix[0, 1],
    ]) / (2 * math.sin(angle))
    return axis * math.degrees(angle)


def stripped_plan(plan):
    # The post-solve plan stores numerical skin-refinement corrections beside
    # authored rows. Compare authored choreography while reporting emitted
    # correction effects separately through skin/contact gates below.
    def authored(value):
        if isinstance(value, dict):
            return {
                key: authored(item)
                for key, item in value.items()
                if key not in ("performance", "target_offset_m")
            }
        if isinstance(value, list):
            return [authored(item) for item in value]
        return value

    return authored(plan)


def evaluate(package: Path, mode: str):
    plan = json.loads((package / "plan.json").read_text())
    runtime = json.loads((package / "runtime.json").read_text())
    recipe = json.loads((package / "recipe.json").read_text())
    biomech = json.loads((package / "biomechanics.json").read_text())
    validation = json.loads((package / "validation.json").read_text())
    glb_path = package / f"{mode}.glb"
    glb = Glb(glb_path)
    roles = runtime["rig_roles"]
    nodes = glb.name_to_node
    forward = unit(runtime["forward_axis"])
    up = unit(runtime["up_axis"])
    lateral = unit(np.cross(up, forward))
    contact = scaled_contact_profile(
        json.loads((ROOT / recipe["contact_profile"]["path"]).read_text()),
        biomech["geometry"]["uniform_scale"],
    )
    skin = SkinRig(glb, roles, forward, up, contact)
    tracks, times = _clip_state(glb, glb.document["animations"][0]["name"])
    times = np.asarray(times, dtype=float)
    if len(times) != len(plan["samples"]):
        raise AssertionError("animation and plan sample counts differ")
    base_worlds = skin.neutral_world
    root = nodes[roles["root"]]
    role_names = {
        "pelvis": roles["pelvis"],
        "chest": roles["chest"],
        "head": roles["head"],
        "tail_base": roles["tail"][0],
        "tail_tip": roles["tail"][-1],
        "left_hip": roles["legs"]["left"]["contactChain"][0],
        "right_hip": roles["legs"]["right"]["contactChain"][0],
    }
    role_nodes = {key: nodes[name] for key, name in role_names.items()}
    neutral_rotations = {
        key: rotation(base_worlds[node]) for key, node in role_nodes.items()
    }
    step = plan["same_foot_cycle_s"] / 2
    duty = plan["parameters"]["duty_factor"]
    targets = {
        "left_leads_double_support": (duty - .5) * step,
        "left_declared_single_support_midpoint": duty * step,
        "right_leads_double_support": (duty + .5) * step,
        "right_declared_single_support_midpoint": (1 + duty) * step,
    }
    landmarks = {
        name: int(np.argmin(np.abs(times - target)))
        for name, target in targets.items()
    }
    landmark_by_index = {index: name for name, index in landmarks.items()}
    rows = {}
    interior_swing_minimum = {side: math.inf for side in ("left", "right")}
    all_swing_minimum = {side: math.inf for side in ("left", "right")}
    local_rotations = []
    skin_points = []
    worlds_by_index = []
    role_positions_all = {key: [] for key in role_nodes}
    role_rotations_all = {key: [] for key in role_nodes}
    for index, row in enumerate(plan["samples"]):
        pose = _pose(glb, tracks, index)
        worlds = skin.world(*pose)
        worlds_by_index.append(worlds)
        xyz = skin.skin(worlds)
        skin_points.append(xyz)
        local_rotations.append(np.asarray(pose[1], dtype=float))
        root_position = np.asarray(_world_position(worlds[root]))
        for key, node in role_nodes.items():
            position = np.asarray(_world_position(worlds[node])) - root_position
            delta = rotation(worlds[node]) @ neutral_rotations[key].T
            rotvec = rotation_vector_degrees(delta)
            role_positions_all[key].append([
                float(position @ axis) for axis in (forward, up, lateral)
            ])
            role_rotations_all[key].append([
                float(rotvec @ axis) for axis in (forward, up, lateral)
            ])
        for side in ("left", "right"):
            foot = row["feet"][side]
            if not foot["contact"]:
                gap = float(np.min(xyz[skin.foot_masks[side]] @ up) - skin.ground)
                all_swing_minimum[side] = min(all_swing_minimum[side], gap)
                if .25 <= foot["swing_phase"] <= .75:
                    interior_swing_minimum[side] = min(
                        interior_swing_minimum[side], gap)
        if index not in landmark_by_index:
            continue
        roles_row = {}
        for key in role_nodes:
            roles_row[key] = {
                "position_root_relative_f_u_l_m": role_positions_all[key][-1],
                "world_rotation_delta_f_u_l_degrees": role_rotations_all[key][-1],
            }
        rows[landmark_by_index[index]] = {
            "target_time_s": targets[landmark_by_index[index]],
            "index": index,
            "time_s": float(times[index]),
            "stage": row["stage"],
            "contacts": [
                side for side in ("left", "right") if row["feet"][side]["contact"]
            ],
            "roles": roles_row,
            "uniform_vertex_mean_root_relative_f_u_l_m": [
                float((xyz.mean(axis=0) - root_position) @ axis)
                for axis in (forward, up, lateral)
            ],
            "foot_patch_minimum_gap_m": {
                side: float(np.min(xyz[skin.foot_masks[side]] @ up) - skin.ground)
                for side in ("left", "right")
            },
        }
    validation_mode = "in_place" if mode == "in_place" else "root_motion"
    return {
        "glb_sha256": digest(glb_path),
        "sample_count": len(times),
        "duration_s": float(times[-1]),
        "times": times,
        "plan_without_performance": stripped_plan(plan),
        "performance": plan["performance"],
        "roles": roles,
        "local_rotations": np.asarray(local_rotations),
        "skin_points": np.asarray(skin_points),
        "worlds": np.asarray(worlds_by_index),
        "role_positions": {
            key: np.asarray(value) for key, value in role_positions_all.items()
        },
        "role_rotations": {
            key: np.asarray(value) for key, value in role_rotations_all.items()
        },
        "landmarks": rows,
        "minimum_swing_foot_patch_gap_m": all_swing_minimum,
        "minimum_interior_swing_foot_patch_gap_m": interior_swing_minimum,
        "validation": {
            "technical_status": validation["technical_status"],
            "solver_feasibility": validation["solver_feasibility"],
            "rotation_rates": validation["rotation_rates"][validation_mode],
            "articulation_envelopes": validation["articulation_envelopes"][validation_mode],
            "skinned_contact": validation[
                "in_place_skinned_contact" if mode == "in_place" else "skinned_contact"
            ],
            "output": validation["outputs"][validation_mode],
            "cyclic_continuity": validation["cyclic_continuity"][validation_mode],
        },
    }


evaluations = {
    label: {mode: evaluate(package, mode) for mode in ("root_motion", "in_place")}
    for label, package in PACKAGES.items()
}

for mode in ("root_motion", "in_place"):
    if evaluations["v8"][mode]["plan_without_performance"] != evaluations["axial"][mode]["plan_without_performance"]:
        raise AssertionError("axial diagnostic changed non-performance plan content")
    if not np.array_equal(evaluations["v8"][mode]["times"], evaluations["axial"][mode]["times"]):
        raise AssertionError("axial diagnostic changed the serialized clock")

payload = {
    "schema": "eonwild.motion.adult-v8-axial-clock-emitted-audit.v1",
    "classification": (
        "Reopened serialized TRS, full multi-influence skin and existing factory gates. "
        "Root-relative origins, rotation-log axis components and uniform vertex means "
        "are kinematic descriptors, not COM, force, load, mass, energy, biological "
        "validity, Unity parity, visual approval or production approval."
    ),
    "source_commit": "483e006b1ddd20617b75e32b2e660b31e5ed0853",
    "packages": {},
    "comparisons": {},
}
for label in ("v8", "axial"):
    payload["packages"][label] = {}
    for mode in ("root_motion", "in_place"):
        value = evaluations[label][mode]
        payload["packages"][label][mode] = {
            key: value[key]
            for key in (
                "glb_sha256",
                "sample_count",
                "duration_s",
                "performance",
                "landmarks",
                "minimum_swing_foot_patch_gap_m",
                "minimum_interior_swing_foot_patch_gap_m",
                "validation",
            )
        }
for mode in ("root_motion", "in_place"):
    old = evaluations["v8"][mode]
    new = evaluations["axial"][mode]
    roles = new["roles"]
    limb_names = []
    for side in ("left", "right"):
        limb_names.extend(roles["legs"][side]["contactChain"])
        for chain in roles["legs"][side]["toeChains"]:
            limb_names.extend(chain)
    new_glb = Glb(PACKAGES["axial"] / f"{mode}.glb")
    limb_nodes = [new_glb.name_to_node[name] for name in dict.fromkeys(limb_names)]
    comparison = {
        "serialized_times_exactly_equal": True,
        "authored_plan_excluding_skin_refinement_offsets_exactly_equal": True,
        "maximum_all_skin_vertex_delta_m": float(np.max(np.linalg.norm(
            new["skin_points"] - old["skin_points"], axis=2))),
        "maximum_limb_local_quaternion_component_delta": float(np.max(np.abs(
            new["local_rotations"][:, limb_nodes] - old["local_rotations"][:, limb_nodes]))),
        "all_key_body_rotation_component_ranges_f_u_l_degrees": {
            role: {
                "axial_minimum": np.min(new["role_rotations"][role], axis=0).tolist(),
                "axial_maximum": np.max(new["role_rotations"][role], axis=0).tolist(),
                "maximum_absolute_axial_minus_v8": np.max(np.abs(
                    new["role_rotations"][role] - old["role_rotations"][role]
                ), axis=0).tolist(),
            }
            for role in ("pelvis", "chest", "head", "tail_base", "tail_tip")
        },
        "all_key_body_position_ranges_f_u_l_m": {
            role: {
                "axial_minimum": np.min(new["role_positions"][role], axis=0).tolist(),
                "axial_maximum": np.max(new["role_positions"][role], axis=0).tolist(),
                "maximum_absolute_axial_minus_v8": np.max(np.abs(
                    new["role_positions"][role] - old["role_positions"][role]
                ), axis=0).tolist(),
            }
            for role in ("pelvis", "chest", "head", "tail_base", "tail_tip")
        },
        "landmarks": {},
    }
    for landmark in new["landmarks"]:
        a = old["landmarks"][landmark]
        b = new["landmarks"][landmark]
        comparison["landmarks"][landmark] = {
            "index": b["index"],
            "time_s": b["time_s"],
            "stage": b["stage"],
            "contacts": b["contacts"],
            "axial_minus_v8_chest_position_f_u_l_m": [
                x - y for x, y in zip(
                    b["roles"]["chest"]["position_root_relative_f_u_l_m"],
                    a["roles"]["chest"]["position_root_relative_f_u_l_m"],
                )
            ],
            "axial_minus_v8_tail_tip_position_f_u_l_m": [
                x - y for x, y in zip(
                    b["roles"]["tail_tip"]["position_root_relative_f_u_l_m"],
                    a["roles"]["tail_tip"]["position_root_relative_f_u_l_m"],
                )
            ],
            "axial_minus_v8_head_rotation_f_u_l_degrees": [
                x - y for x, y in zip(
                    b["roles"]["head"]["world_rotation_delta_f_u_l_degrees"],
                    a["roles"]["head"]["world_rotation_delta_f_u_l_degrees"],
                )
            ],
            "axial_minus_v8_uniform_vertex_mean_f_u_l_m": [
                x - y for x, y in zip(
                    b["uniform_vertex_mean_root_relative_f_u_l_m"],
                    a["uniform_vertex_mean_root_relative_f_u_l_m"],
                )
            ],
        }
    payload["comparisons"][mode] = comparison

OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
print(OUTPUT)
print(digest(OUTPUT))
print(json.dumps({
    mode: {
        "maximum_all_skin_vertex_delta_m": payload["comparisons"][mode]["maximum_all_skin_vertex_delta_m"],
        "maximum_limb_local_quaternion_component_delta": payload["comparisons"][mode]["maximum_limb_local_quaternion_component_delta"],
        "axial_minimum_interior_swing_gap_m": payload["packages"]["axial"][mode]["minimum_interior_swing_foot_patch_gap_m"],
        "technical_status": payload["packages"]["axial"][mode]["validation"]["technical_status"],
        "landmarks": payload["comparisons"][mode]["landmarks"],
    }
    for mode in ("root_motion", "in_place")
}, indent=2))
