#!/usr/bin/env python3
"""Run the source-bound adult V9 sampled support-resultant sensitivity."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eonwild_motion.dynamics.centroidal import bind_profile_segments, compute_centroidal_series
from eonwild_motion.dynamics.support_resultant import sampled_support_resultants
from eonwild_motion.factory.animal import scaled_contact_profile
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose
from eonwild_motion.solve.skin_rig import SkinRig


REPO = Path(__file__).resolve().parents[1]
TASK = Path("/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521")
DEFAULT_PACKAGE = TASK / "out/continuation-adult-v9-axial-jaw-001"
DEFAULT_ASSUMPTIONS = REPO / "profiles/v9/tarbosaurus-pin-552-1-support-resultant-engineering.v1.json"
SUPPORT_AUDIT = TASK / "audits/adult-v9-support-balance-audit.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rotation(matrix: np.ndarray) -> np.ndarray:
    left, _, right = np.linalg.svd(matrix[:3, :3])
    result = left @ right
    if np.linalg.det(result) <= 0.0:
        raise ValueError("world transform contains a reflection")
    return result


def mass_variant(segments: list[dict], variant: str, delta: float) -> list[dict]:
    result = [dict(item) for item in segments]
    tail = [item for item in result if str(item["id"]).startswith("tail_")]
    center = [item for item in result if item["id"] in {"pelvis", "trunk", "chest"}]
    signed = {"baseline": 0.0, "tail_heavy": delta, "tail_light": -delta}[variant]
    if signed:
        tail_total = sum(float(item["mass_fraction"]) for item in tail)
        center_total = sum(float(item["mass_fraction"]) for item in center)
        for item in tail:
            item["mass_fraction"] = float(item["mass_fraction"]) + signed * float(item["mass_fraction"]) / tail_total
        for item in center:
            item["mass_fraction"] = float(item["mass_fraction"]) - signed * float(item["mass_fraction"]) / center_total
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--assumptions", type=Path, default=DEFAULT_ASSUMPTIONS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assumptions = json.loads(args.assumptions.read_text())
    recipe = json.loads((args.package / "recipe.json").read_text())
    runtime = json.loads((args.package / "runtime.json").read_text())
    plan = json.loads((args.package / "plan.json").read_text())
    biomechanics = json.loads((args.package / "biomechanics.json").read_text())
    support_audit = json.loads(SUPPORT_AUDIT.read_text())
    provisional_path = REPO / assumptions["engineering_model"]["segment_profile"]
    provisional = json.loads(provisional_path.read_text())
    contact_path = REPO / recipe["contact_profile"]["path"]
    animal_path = REPO / recipe["animal"]["path"]
    expected = assumptions["source"]
    actual = {
        "root_motion_glb_sha256": sha(args.package / "root_motion.glb"),
        "plan_sha256": sha(args.package / "plan.json"),
        "recipe_sha256": sha(args.package / "recipe.json"),
        "runtime_sha256": sha(args.package / "runtime.json"),
        "animal_profile_sha256": sha(animal_path),
        "contact_profile_sha256": sha(contact_path),
        "provisional_segment_profile_sha256": sha(provisional_path),
        "support_geometry_audit_sha256": sha(SUPPORT_AUDIT),
    }
    if actual != expected:
        raise ValueError(f"source identity mismatch: {actual!r}")

    glb = Glb.from_bytes((args.package / "root_motion.glb").read_bytes())
    roles = runtime["rig_roles"]
    contact = scaled_contact_profile(json.loads(contact_path.read_text()), biomechanics["geometry"]["uniform_scale"])
    skin = SkinRig(glb, roles, runtime["forward_axis"], runtime["up_axis"], contact)
    tracks, raw_times = _clip_state(glb, glb.document["animations"][0]["name"])
    times = np.asarray(raw_times, dtype=float)
    if len(times) != len(plan["samples"]) or np.max(np.abs(times - [row["time_s"] for row in plan["samples"]])) > 1e-6:
        raise ValueError("serialized and planned timelines differ")
    positions: list[np.ndarray] = []
    rotations: list[np.ndarray] = []
    worlds_by_frame: list[np.ndarray] = []
    for index in range(len(times)):
        worlds = skin.world(*_pose(glb, tracks, index))
        worlds_by_frame.append(worlds)
        positions.append(np.asarray(worlds[:, :3, 3], dtype=float))
        rotations.append(np.asarray([rotation(item) for item in worlds], dtype=float))
    neutral_worlds = skin.world(glb.rest_translation, glb.rest_rotation, glb.rest_scale)
    neutral_rotations = np.asarray([rotation(item) for item in neutral_worlds])
    cop_proxy_nodes = {}
    for side in ("left", "right"):
        foot = glb.name_to_node[roles["legs"][side]["contactChain"][-1]]
        candidates = [glb.name_to_node[chain[-1]] for chain in roles["legs"][side]["toeChains"]]
        cop_proxy_nodes[side] = min(
            candidates,
            key=lambda node: abs(float((neutral_worlds[node, :3, 3] - neutral_worlds[foot, :3, 3]) @ skin.lateral)),
        )

    segment_to_node = assumptions["segment_to_node"]
    midpoint_target = assumptions["midpoint_target_node"]
    name_to_node = glb.name_to_node
    if any(name not in name_to_node for name in segment_to_node.values()):
        raise ValueError("segment binding names a missing node")
    segment_rows = [
        {"id": item["id"], "mass_fraction": item["mass_fraction"], "inertia_diagonal_normalized": item["inertia_diagonal_normalized"]}
        for item in provisional["segments"]
    ]
    midpoint_offsets = {}
    for segment_id, node_name in segment_to_node.items():
        node = name_to_node[node_name]
        target_name = midpoint_target[segment_id]
        if target_name is None:
            midpoint_offsets[segment_id] = [0.0, 0.0, 0.0]
            continue
        target = name_to_node[target_name]
        world_offset = 0.5 * (neutral_worlds[target, :3, 3] - neutral_worlds[node, :3, 3])
        midpoint_offsets[segment_id] = (neutral_rotations[node].T @ world_offset).tolist()
    zero_offsets = {segment_id: [0.0, 0.0, 0.0] for segment_id in segment_to_node}

    total_mass = float(assumptions["published_constraints"]["total_mass_kg"])
    height = float(biomechanics["geometry"]["actual_semantic_pelvis_to_toe_plane_m"])
    model_specs = [
        ("baseline_joint_origin", "baseline", zero_offsets),
        ("baseline_link_midpoint", "baseline", midpoint_offsets),
        ("tail_heavy_link_midpoint", "tail_heavy", midpoint_offsets),
        ("tail_light_link_midpoint", "tail_light", midpoint_offsets),
    ]
    root_index = name_to_node[roles["root"]]
    ground = float(contact["geometry"]["ground"]["level_m"])
    landmarks = support_audit["landmarks"]
    output_models = {}
    for label, mass_name, offsets in model_specs:
        rows = mass_variant(segment_rows, mass_name, float(assumptions["engineering_model"]["tail_mass_fraction_delta"]))
        bindings = bind_profile_segments(
            rows,
            name_to_node=name_to_node,
            segment_to_node=segment_to_node,
            com_local_m=offsets,
            total_mass_kg=total_mass,
            characteristic_height_m=height,
            absolute_dynamics_enabled=True,
        )
        series = compute_centroidal_series(bindings, times_s=times, world_positions=positions, world_rotations=rotations, mass_mode="absolute")
        resultants = sampled_support_resultants(series, ground_height_m=ground, up_axis=skin.up, forward_axis=skin.forward)
        # Static yaw inertia check uses the first emitted pose.  It combines
        # node-frame engineering diagonal terms and parallel-axis terms.
        center = np.asarray(series[0].com_m)
        yaw_inertia = 0.0
        for binding in bindings:
            rot = rotations[0][binding.node_index]
            seg = positions[0][binding.node_index] + rot @ binding.com_local_m
            inertia = rot @ np.diag(binding.inertia_diag_kg_m2) @ rot.T
            radius = seg - center
            yaw_inertia += float(skin.up @ inertia @ skin.up) + binding.mass_kg * (float(radius @ radius) - float(radius @ skin.up) ** 2)
        phase_rows = {}
        for phase, evidence in landmarks.items():
            index = int(evidence["native_key_index"])
            root = positions[index][root_index]
            item = resultants[index]
            point = np.asarray(item.point_m) - root
            projected = [float(point @ axis) for axis in (skin.forward, skin.up, skin.lateral)]
            lateral_range = evidence["declared_support_near_ground_lateral_union_root_relative_m"]
            forward_range = evidence["declared_support_near_ground_forward_union_root_relative_m"]
            contact_proxies = {}
            for side in evidence["declared_contacts"]:
                node = cop_proxy_nodes[side]
                proxy = positions[index][node] - root
                contact_proxies[side] = [
                    float(proxy @ skin.forward),
                    float(ground - root @ skin.up),
                    float(proxy @ skin.lateral),
                ]
            load_models = {}
            if len(contact_proxies) == 1:
                only = next(iter(contact_proxies.values()))
                load_models["single_support_1.0"] = only
            else:
                left, right = np.asarray(contact_proxies["left"]), np.asarray(contact_proxies["right"])
                load_models["equal_0.5_0.5"] = (0.5 * left + 0.5 * right).tolist()
                leading = "left" if "left_leads" in phase else "right"
                lead = left if leading == "left" else right
                trail = right if leading == "left" else left
                load_models["leading_0.6_trailing_0.4"] = (0.6 * lead + 0.4 * trail).tolist()
            phase_rows[phase] = {
                "native_key_index": index,
                "time_s": item.time_s,
                "declared_contacts": evidence["declared_contacts"],
                "required_resultant_root_relative_f_u_l_m": projected,
                "required_force_f_u_l_n": [float(np.asarray(item.force_n) @ axis) for axis in (skin.forward, skin.up, skin.lateral)],
                "angular_momentum_rate_f_u_l_nm": [float(np.asarray(item.angular_momentum_rate_nm) @ axis) for axis in (skin.forward, skin.up, skin.lateral)],
                "free_up_axis_moment_nm": item.free_normal_moment_nm,
                "central_toe_distal_cop_proxies_root_relative_f_u_l_m": contact_proxies,
                "load_weighted_cop_proxy_models_root_relative_f_u_l_m": load_models,
                "required_minus_cop_proxy_f_l_m": {
                    key: [projected[0] - value[0], projected[2] - value[2]]
                    for key, value in load_models.items()
                },
                "geometric_support_lateral_range_m": lateral_range,
                "geometric_support_forward_range_m": forward_range,
                "outside_geometric_support_m": {
                    "lateral": max(0.0, lateral_range[0] - projected[2], projected[2] - lateral_range[1]),
                    "forward": max(0.0, forward_range[0] - projected[0], projected[0] - forward_range[1]),
                },
            }
        output_models[label] = {
            "mass_variant": mass_name,
            "local_com_variant": "semantic_joint_origin" if offsets is zero_offsets else "semantic_link_midpoint",
            "static_sample_yaw_inertia_kg_m2": yaw_inertia,
            "published_axial_body_yaw_inertia_kg_m2": assumptions["published_constraints"]["axial_body_yaw_inertia_kg_m2"],
            "landmarks": phase_rows,
        }

    payload = {
        "schema": "eonwild.motion.adult-v9-support-resultant-sensitivity.v1",
        "classification": "Sampled engineering sensitivity diagnostic; not exact LINEAR-key dynamics, measured CoP/load, fossil segment properties, stability certification, or motion approval",
        "source": actual | {
            "package": str(args.package),
            "assumptions_sha256": sha(args.assumptions),
            "support_resultant_module_sha256": sha(REPO / "src/eonwild_motion/dynamics/support_resultant.py"),
            "sample_count": len(times),
        },
        "published_constraints": assumptions["published_constraints"],
        "engineering_assumptions": assumptions["engineering_model"],
        "models": output_models,
        "limitations": [
            "The existing segment fractions, local COM alternatives, and diagonal inertias are engineering assumptions, not published PIN 552-1 segment measurements.",
            "Finite differences of sampled centroidal velocity and momentum are sensitivity estimates; LINEAR emitted keys have velocity discontinuities.",
            "The material support envelope is geometric availability, not pressure or center of pressure.",
            "A resultant inside that envelope does not prove a feasible pressure distribution, muscle force, tissue stress, or biological validity.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output), "models": list(output_models)}, indent=2))


if __name__ == "__main__":
    main()
