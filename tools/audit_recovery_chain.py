"""Measure an emitted hindlimb recovery chain at every native clip sample.

This is descriptive evidence.  It does not define species range-of-motion
limits, approve visual quality, or alter the immutable candidate package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import scaled_contact_profile
from eonwild_motion.factory.compiler import verify_package
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import (
    _clip_state,
    _pose,
    _world_matrices,
    _world_position,
)
from eonwild_motion.solve.skin_rig import SkinRig


SIDES = ("left", "right")
MEASUREMENTS = (
    "knee_interior_degrees",
    "intertarsal_ankle_interior_degrees",
    "mtp_interior_degrees",
    "proximal_toe_interior_mean_degrees",
    "distal_toe_interior_mean_degrees",
    "thigh_direction_from_down_degrees",
    "tibia_direction_from_down_degrees",
    "metatarsus_direction_from_down_degrees",
    "pad_to_proximal_toe_direction_from_down_degrees",
    "pad_to_distal_toe_direction_from_down_degrees",
    "toe_material_clearance_m",
    "intertarsal_blend_radius_ratio",
    "mtp_blend_radius_ratio",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(value: Sequence[float]) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    norm = float(np.linalg.norm(vector))
    if vector.shape != (3,) or not math.isfinite(norm) or norm <= 1e-12:
        raise ContractError("recovery audit requires a finite nonzero axis")
    return vector / norm


def interior_degrees(first: Sequence[float], second: Sequence[float]) -> float:
    a, b = unit(first), unit(second)
    return math.degrees(math.acos(float(np.clip(a @ b, -1.0, 1.0))))


def direction_from_down_degrees(
    vector: Sequence[float], *, forward: Sequence[float], up: Sequence[float]
) -> float:
    """Signed sagittal direction: zero down, positive toward declared forward."""
    value, front, vertical = unit(vector), unit(forward), unit(up)
    return math.degrees(math.atan2(float(value @ front), float(value @ -vertical)))


def temporal_summary(
    values: Sequence[float], times: Sequence[float], indices: Iterable[int], *,
    circular: bool = False,
) -> dict[str, Any] | None:
    chosen = tuple(int(index) for index in indices)
    if not chosen:
        return None
    data = np.asarray([values[index] for index in chosen], dtype=float)
    if circular:
        data_for_rate = np.unwrap(np.radians(np.asarray(values, dtype=float))) * 180 / math.pi
    else:
        data_for_rate = np.asarray(values, dtype=float)
    low = int(np.argmin(data))
    high = int(np.argmax(data))
    rate_witness = None
    maximum_rate = 0.0
    selected = set(chosen)
    for left, right in zip(range(len(times) - 1), range(1, len(times))):
        if left not in selected or right not in selected:
            continue
        duration = float(times[right] - times[left])
        if duration <= 0:
            raise ContractError("recovery audit timeline is not strictly increasing")
        rate = float((data_for_rate[right] - data_for_rate[left]) / duration)
        if rate_witness is None or abs(rate) > maximum_rate:
            maximum_rate = abs(rate)
            rate_witness = {
                "from_index": left,
                "to_index": right,
                "from_time_s": float(times[left]),
                "to_time_s": float(times[right]),
                "signed_rate_per_s": rate,
            }
    return {
        "sample_count": len(chosen),
        "minimum": {
            "value": float(data[low]),
            "index": chosen[low],
            "time_s": float(times[chosen[low]]),
        },
        "maximum": {
            "value": float(data[high]),
            "index": chosen[high],
            "time_s": float(times[chosen[high]]),
        },
        "maximum_absolute_native_rate_per_s": maximum_rate,
        "maximum_absolute_native_rate_witness": rate_witness,
    }


def _profile(repository: Path, recipe: Mapping[str, Any], runtime: Mapping[str, Any]) -> tuple[dict, Path]:
    reference = recipe.get("contact_profile")
    if not isinstance(reference, Mapping):
        raise ContractError("recovery audit requires a bound contact profile")
    relative = reference.get("path")
    expected = reference.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected, str):
        raise ContractError("recovery audit contact profile binding is malformed")
    path = (repository / relative).resolve()
    try:
        path.relative_to(repository)
    except ValueError as exc:
        raise ContractError("recovery audit contact profile escapes the repository") from exc
    if sha(path) != expected:
        raise ContractError("recovery audit contact profile hash differs from recipe")
    profile = json.loads(path.read_text())
    animal = runtime.get("animal")
    if animal is not None:
        if not isinstance(animal, Mapping):
            raise ContractError("recovery audit animal runtime binding is malformed")
        scale = animal.get("uniform_geometry_scale")
        if isinstance(scale, bool) or not isinstance(scale, (int, float)):
            raise ContractError("recovery audit animal scale is malformed")
        profile = scaled_contact_profile(profile, float(scale))
    return profile, path


def _binding(glb: Glb, runtime: Mapping[str, Any]) -> dict[str, Any]:
    roles = runtime.get("rig_roles")
    if not isinstance(roles, Mapping) or not isinstance(roles.get("legs"), Mapping):
        raise ContractError("recovery audit requires emitted leg bindings")
    result: dict[str, Any] = {}
    for side in SIDES:
        leg = roles["legs"].get(side)
        if not isinstance(leg, Mapping):
            raise ContractError(f"recovery audit is missing the {side} leg")
        chain = leg.get("contactChain")
        toes = leg.get("toeChains")
        if not isinstance(chain, list) or len(chain) != 4 or not all(isinstance(name, str) for name in chain):
            raise ContractError("recovery audit requires four-node contact chains")
        if not isinstance(toes, list) or not toes or any(
            not isinstance(toe, list) or len(toe) != 3 or not all(isinstance(name, str) for name in toe)
            for toe in toes
        ):
            raise ContractError("recovery audit requires bound toe chains")
        try:
            chain_i = [glb.name_to_node[name] for name in chain]
            toes_i = [[glb.name_to_node[name] for name in toe] for toe in toes]
        except KeyError as exc:
            raise ContractError("recovery audit binding names an absent emitted node") from exc
        if any(glb.parents[child] != parent for parent, child in zip(chain_i, chain_i[1:])):
            raise ContractError("recovery audit contact chain is not a parent chain")
        if any(
            glb.parents[toe[0]] != chain_i[-1]
            or any(glb.parents[child] != parent for parent, child in zip(toe, toe[1:]))
            for toe in toes_i
        ):
            raise ContractError("recovery audit toe binding is not attached to the MTP/pad root")
        result[side] = {"chain_names": chain, "chain_indices": chain_i,
                        "toe_names": toes, "toe_indices": toes_i}
    return result


def _bone_weight(rig: SkinRig, node: int) -> np.ndarray:
    return np.where(rig.node_ids == node, rig.weights, 0.0).sum(axis=1)


def _blend_zone(rig: SkinRig, parent: int, child: int, points: np.ndarray,
                neutral_points: np.ndarray, world: Sequence[Any], neutral_world: Sequence[Any]) -> tuple[dict, float]:
    parent_weight, child_weight = _bone_weight(rig, parent), _bone_weight(rig, child)
    vertices = np.flatnonzero((parent_weight >= 0.1) & (child_weight >= 0.1))
    if not len(vertices):
        raise ContractError("recovery audit adjacent-bone blend zone is empty")
    pivot = np.asarray(_world_position(world[child]), dtype=float)
    neutral_pivot = np.asarray(_world_position(neutral_world[child]), dtype=float)
    radii = np.linalg.norm(points[vertices] - pivot, axis=1)
    neutral_radii = np.linalg.norm(neutral_points[vertices] - neutral_pivot, axis=1)
    neutral_mean = float(np.mean(neutral_radii))
    if neutral_mean <= 1e-12:
        raise ContractError("recovery audit blend zone has zero neutral radius")
    definition = {
        "vertex_count": int(len(vertices)),
        "selection": "vertices with normalized aggregate weight >=0.1 for both adjacent rig nodes",
        "parent_mean_weight": float(np.mean(parent_weight[vertices])),
        "child_mean_weight": float(np.mean(child_weight[vertices])),
        "neutral_mean_radius_m": neutral_mean,
        "radius": "mean skinned distance from child joint origin divided by the neutral mean; descriptive linear-blend deformation",
    }
    return definition, float(np.mean(radii) / neutral_mean)


def audit(package: Path, repository: Path) -> dict[str, Any]:
    package, repository = package.resolve(), repository.resolve()
    before = verify_package(package)
    manifest_sha = sha(package / "manifest.json")
    manifest = json.loads((package / "manifest.json").read_text())
    source_hashes = {
        "manifest.json": manifest_sha,
        **{name: sha(package / name) for name in manifest["files"]},
    }
    recipe = json.loads((package / "recipe.json").read_text())
    runtime = json.loads((package / "runtime.json").read_text())
    plan = json.loads((package / "plan.json").read_text())
    profile, profile_path = _profile(repository, recipe, runtime)
    glb = Glb(package / "root_motion.glb")
    if len(glb.document.get("animations", [])) != 1:
        raise ContractError("recovery audit requires exactly one emitted animation")
    clip_name = glb.document["animations"][0].get("name")
    tracks, times = _clip_state(glb, clip_name)
    samples = plan.get("samples")
    if not isinstance(samples, list) or len(samples) != len(times):
        raise ContractError("recovery audit plan and emitted native timeline differ")
    plan_times = tuple(float(row.get("time_s")) for row in samples)
    if any(abs(left - right) > 1e-6 for left, right in zip(plan_times, times)):
        raise ContractError("recovery audit plan seconds differ from emitted native seconds")
    forward, up = unit(runtime.get("forward_axis")), unit(runtime.get("up_axis"))
    if abs(float(forward @ up)) > 1e-6:
        raise ContractError("recovery audit axes are not orthogonal")
    bindings = _binding(glb, runtime)
    rig = SkinRig(glb, runtime["rig_roles"], forward, up, profile)
    neutral_world = _world_matrices(glb, glb.rest_translation, glb.rest_rotation, glb.rest_scale)
    neutral_points = rig.skin(np.asarray(neutral_world))
    side_state: dict[str, dict[str, Any]] = {}
    for side in SIDES:
        binding = bindings[side]
        contact_mask = profile["geometry"]["feet"][side]
        toe_nodes = [glb.name_to_node[name] for name in contact_mask["toe_joints"]]
        toe_strength = np.where(np.isin(rig.node_ids, toe_nodes), rig.weights, 0.0).max(axis=1)
        toe_vertices = np.flatnonzero(toe_strength >= float(contact_mask["weight_threshold"]))
        if not len(toe_vertices):
            raise ContractError("recovery audit toe material mask is empty")
        side_state[side] = {"rows": [], "series": {key: [] for key in MEASUREMENTS},
                            "toe_vertices": toe_vertices, "zones": {}}
    for index, (time_s, plan_row) in enumerate(zip(times, samples)):
        pose = _pose(glb, tracks, index)
        world = _world_matrices(glb, *pose)
        points = rig.skin(np.asarray(world))
        for side in SIDES:
            state, binding = side_state[side], bindings[side]
            hip, knee, ankle, pad = binding["chain_indices"]
            hp, kp, ap, pp = (
                np.asarray(_world_position(world[node]), dtype=float)
                for node in (hip, knee, ankle, pad)
            )
            toe_roots = np.mean([
                np.asarray(_world_position(world[toe[0]]), dtype=float)
                for toe in binding["toe_indices"]
            ], axis=0)
            toe_tips = np.mean([
                np.asarray(_world_position(world[toe[-1]]), dtype=float)
                for toe in binding["toe_indices"]
            ], axis=0)
            toe_interiors = []
            for toe_names, (proximal, middle, distal) in zip(
                binding["toe_names"], binding["toe_indices"]
            ):
                proximal_position = np.asarray(_world_position(world[proximal]), dtype=float)
                middle_position = np.asarray(_world_position(world[middle]), dtype=float)
                distal_position = np.asarray(_world_position(world[distal]), dtype=float)
                toe_interiors.append({
                    "rig_nodes": toe_names,
                    "proximal_interior_degrees": interior_degrees(
                        pp - proximal_position, middle_position - proximal_position
                    ),
                    "distal_interior_degrees": interior_degrees(
                        proximal_position - middle_position, distal_position - middle_position
                    ),
                })
            inter_definition, inter_ratio = _blend_zone(
                rig, knee, ankle, points, neutral_points, world, neutral_world
            )
            mtp_definition, mtp_ratio = _blend_zone(
                rig, ankle, pad, points, neutral_points, world, neutral_world
            )
            if not state["zones"]:
                state["zones"] = {
                    "intertarsal": inter_definition,
                    "mtp": mtp_definition,
                }
            foot_plan = plan_row.get("feet", {}).get(side)
            if not isinstance(foot_plan, Mapping) or not isinstance(foot_plan.get("contact"), bool):
                raise ContractError("recovery audit plan lacks per-side contact state")
            values = {
                "knee_interior_degrees": interior_degrees(hp - kp, ap - kp),
                "intertarsal_ankle_interior_degrees": interior_degrees(kp - ap, pp - ap),
                "mtp_interior_degrees": interior_degrees(ap - pp, toe_roots - pp),
                "proximal_toe_interior_mean_degrees": float(np.mean([
                    row["proximal_interior_degrees"] for row in toe_interiors
                ])),
                "distal_toe_interior_mean_degrees": float(np.mean([
                    row["distal_interior_degrees"] for row in toe_interiors
                ])),
                "thigh_direction_from_down_degrees": direction_from_down_degrees(kp - hp, forward=forward, up=up),
                "tibia_direction_from_down_degrees": direction_from_down_degrees(ap - kp, forward=forward, up=up),
                "metatarsus_direction_from_down_degrees": direction_from_down_degrees(pp - ap, forward=forward, up=up),
                "pad_to_proximal_toe_direction_from_down_degrees": direction_from_down_degrees(toe_roots - pp, forward=forward, up=up),
                "pad_to_distal_toe_direction_from_down_degrees": direction_from_down_degrees(toe_tips - pp, forward=forward, up=up),
                "toe_material_clearance_m": float(np.min(points[state["toe_vertices"]] @ up) - rig.ground),
                "intertarsal_blend_radius_ratio": inter_ratio,
                "mtp_blend_radius_ratio": mtp_ratio,
            }
            for name, value in values.items():
                state["series"][name].append(value)
            state["rows"].append({
                "index": index,
                "native_time_s": float(time_s),
                "contact": foot_plan["contact"],
                "swing_phase": float(foot_plan.get("swing_phase", 0.0)),
                "toe_digit_interiors": toe_interiors,
                **values,
            })
    sides = {}
    circular = {name for name in MEASUREMENTS if "direction_from_down" in name}
    for side in SIDES:
        state = side_state[side]
        all_indices = range(len(times))
        swing_indices = [row["index"] for row in state["rows"] if not row["contact"]]
        mid_swing_indices = [
            row["index"] for row in state["rows"]
            if not row["contact"] and 0.25 <= row["swing_phase"] <= 0.75
        ]
        stance_indices = [row["index"] for row in state["rows"] if row["contact"]]
        summaries = {}
        for scope, indices in (
            ("full_cycle", all_indices),
            ("swing", swing_indices),
            ("mid_swing_phase_0.25_to_0.75", mid_swing_indices),
            ("stance", stance_indices),
        ):
            summaries[scope] = {
                name: temporal_summary(state["series"][name], times, indices, circular=name in circular)
                for name in MEASUREMENTS
            }
        sides[side] = {
            "rig_mapping": {
                "hip_origin_controller": bindings[side]["chain_names"][0],
                "knee_joint_origin": bindings[side]["chain_names"][1],
                "anatomical_intertarsal_ankle_joint_origin": bindings[side]["chain_names"][2],
                "mtp_pad_root_joint_origin": bindings[side]["chain_names"][3],
                "toe_chains": bindings[side]["toe_names"],
            },
            "toe_material_mask": {
                "vertex_count": int(len(state["toe_vertices"])),
                "weight_threshold": float(profile["geometry"]["feet"][side]["weight_threshold"]),
                "ground_level_m": rig.ground,
            },
            "blend_zones": state["zones"],
            "summaries": summaries,
            "native_samples": state["rows"],
        }
    after = verify_package(package)
    after_hashes = {name: sha(package / name) for name in source_hashes}
    if after_hashes != source_hashes or sha(package / "manifest.json") != manifest_sha:
        raise ContractError("candidate package changed during recovery audit")
    return {
        "schema": "eonwild.motion.recovery-chain-audit.v1",
        "scope": "descriptive full-cycle emitted-rig and actual-skin evidence; no species ROM gate, visual approval, or biological validation",
        "candidate_status_before": before,
        "candidate_status_after": after,
        "production_approved": False,
        "visual_review": "NOT_EVALUATED",
        "auditor": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha(Path(__file__).resolve()),
        },
        "package": str(package),
        "package_manifest_sha256": manifest_sha,
        "immutable_package_hashes": {
            "before": source_hashes,
            "after": after_hashes,
            "unchanged": True,
        },
        "contact_profile": {"path": str(profile_path), "sha256": sha(profile_path)},
        "animation": {"name": clip_name, "native_sample_count": len(times),
                      "native_start_s": float(times[0]), "native_end_s": float(times[-1])},
        "axes": {
            "forward": forward.tolist(),
            "up": up.tolist(),
            "direction_sign": "0 degrees is world down; positive is toward declared forward; negative is tailward",
        },
        "definitions": {
            "knee_interior": "angle at contactChain[1] between hip and intertarsal ankle origins",
            "anatomical_intertarsal_ankle_interior": "angle at contactChain[2] between knee and MTP/pad-root origins",
            "mtp_interior": "angle at contactChain[3] between intertarsal ankle and mean proximal-toe origins",
            "proximal_toe_interior": "per toeChain angle at toeChain[0] between MTP/pad root and toeChain[1]; summaries use the mean across digits",
            "distal_toe_interior": "per toeChain angle at toeChain[1] between toeChain[0] and terminal toeChain[2]; terminal rotation has no downstream skeletal angle witness",
            "toe_material_clearance": "minimum reopened skinned toe-mask vertex height above the bound scaled ground plane",
            "native_rate": "first difference between consecutive emitted native samples; swing/stance summaries exclude boundary-crossing intervals",
            "rate_units": "angles use degrees/s, clearance uses m/s, and dimensionless blend ratios use 1/s",
        },
        "sides": sides,
        "audit_status": "COMPLETE_DESCRIPTIVE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--repository", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    package, output = args.package.resolve(), args.output.resolve()
    try:
        output.relative_to(package)
    except ValueError:
        pass
    else:
        parser.error("audit output must remain outside the immutable package")
    if output.exists():
        parser.error("audit output already exists")
    result = audit(package, args.repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("RECOVERY_CHAIN_AUDIT " + json.dumps({
        "audit_status": result["audit_status"],
        "package_manifest_sha256": result["package_manifest_sha256"],
        "output": str(output),
        "output_sha256": sha(output),
    }, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
