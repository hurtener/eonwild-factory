#!/usr/bin/env python3
"""Decompose the exact emitted sprint Bone_016 handoff velocity witness."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
SOURCE_ROOT = Path("/private/tmp/eonwild-engine-c43d426")
PACKAGE_ROOT = Path("/Volumes/m2-extended-disk/Repos/eonwild-factory")
PAIR = PACKAGE_ROOT / "out/continuation-native-clock-7920c59-pairs/sprint"
sys.path.insert(0, str(SOURCE_ROOT / "src"))

from eonwild_motion.factory.quality import _endpoint_derivative
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import (
    _clip_state,
    _pose,
    _q_to_rotvec,
    _qinv,
    _qmul,
    _rotation_from_matrix,
    _world_matrices,
    _world_position,
)
from eonwild_motion.solve.airborne_gait import _local_delta, _qrotate, _qrotvec
from eonwild_motion.solve.performance import apply_performance, phase_and_gain


EXPECTED_ENGINE = {
    "solve/airborne_gait.py": "1772160aa3885d5d89cb4c5455e082b15dc779982698dad20eb1371575107758",
    "solve/performance.py": "232300a2a779aebffa1420d210bea276cffd050833cc1ec18c691cdfdc19861a",
    "factory/handoff.py": "37c13700200a4db22f5ccdd1e31a56ee84e5a680a74714f22cde2d0456794f7a",
    "layers/leg_contact_resolve_v3.py": "274e2835b52309a53963419d3cde684c4206130282232be87c4e3fc2dd1eb21b",
}
MODES = ("root_motion", "in_place")
KINDS = ("start", "stop")
VARIANTS = ((True, True), (True, False), (False, True), (False, False))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(value) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    return result / np.linalg.norm(result)


def velocity(times: np.ndarray, points: np.ndarray, *, terminal: bool) -> np.ndarray:
    end = -1 if terminal else 0
    ids = [0, 1] if terminal else [1, 2]
    return _endpoint_derivative(times[ids] - times[end], points[ids] - points[end])


def qdistance_degrees(a, b) -> float:
    return math.degrees(np.linalg.norm(_q_to_rotvec(_qmul(_qinv(tuple(a)), tuple(b)))))


class Package:
    def __init__(self, path: Path, mode: str):
        self.path = path
        self.mode = mode
        self.glb_path = path / f"{mode}.glb"
        self.glb = Glb(self.glb_path)
        self.plan = json.loads((path / "plan.json").read_text())
        self.runtime = json.loads((path / "runtime.json").read_text())
        self.receipt = json.loads((path / "solver-receipt.json").read_text())
        self.animation = self.glb.document["animations"][0]["name"]
        self.tracks, raw_times = _clip_state(self.glb, self.animation)
        self.times = np.asarray(raw_times, dtype=float)
        self.roles = self.runtime["rig_roles"]
        self.tail_names = list(self.roles["tail"])
        self.tail = [self.glb.name_to_node[name] for name in self.tail_names]
        self.tip = self.glb.name_to_node["Bone_016"]
        self.root = self.glb.name_to_node[self.roles["root"]]
        self.pelvis = self.glb.name_to_node[self.roles["pelvis"]]
        self.chest = self.glb.name_to_node[self.roles["chest"]]
        self.base_t = list(self.glb.rest_translation)
        self.base_r = list(self.glb.rest_rotation)
        self.base_s = list(self.glb.rest_scale)
        self.base_w = _world_matrices(self.glb, self.base_t, self.base_r, self.base_s)
        self.forward = unit(self.runtime["forward_axis"])
        self.up = unit(self.runtime["up_axis"])
        self.lateral = unit(np.cross(self.up, self.forward))
        self.body = self.receipt["body_response"]["samples"]
        assert len(self.plan["samples"]) == len(self.times) == len(self.body)

    def indices(self, *, terminal: bool, phase_s: float) -> list[int]:
        endpoint = len(self.times) - 1 if terminal else 0
        if phase_s:
            matches = np.flatnonzero(np.abs(self.times - phase_s) <= 2e-6)
            assert len(matches) == 1
            endpoint = int(matches[0])
        return list(range(endpoint - 2, endpoint + 1)) if terminal else list(range(endpoint, endpoint + 3))

    def reconstructed(self, index: int, *, yaw: bool, driven: bool, cast32: bool = False):
        row = self.plan["samples"][index]
        tr, rot, scales = self.base_t[:], self.base_r[:], self.base_s[:]
        root_delta = self.forward * float(row["root_forward_m"])
        tr[self.root] = tuple(
            float(v) for v in np.asarray(self.base_t[self.root])
            + _local_delta(self.glb, self.base_w, self.root, root_delta)
        )
        root_pitch = float(row.get("root_pitch_degrees", 0.0))
        if root_pitch:
            axis = _qrotate(_qinv(_rotation_from_matrix(self.base_w[self.root])), tuple(self.lateral))
            rot[self.root] = _qmul(
                self.base_r[self.root],
                _qrotvec(tuple(np.asarray(axis) * math.radians(root_pitch))),
            )
        tr[self.pelvis] = tuple(
            float(v) for v in np.asarray(self.base_t[self.pelvis])
            + _local_delta(
                self.glb,
                self.base_w,
                self.pelvis,
                self.up * float(row["pelvis_height_offset_m"]),
            )
        )
        for name, degrees in self.body[index]["sagittal_node_degrees"].items():
            if not driven and name in self.tail_names:
                degrees = 0.0
            node = self.glb.name_to_node[name]
            axis = _qrotate(_qinv(_rotation_from_matrix(self.base_w[node])), tuple(self.lateral))
            rot[node] = _qmul(
                self.base_r[node],
                _qrotvec(tuple(np.asarray(axis) * math.radians(float(degrees)))),
            )
        _phase, gain = phase_and_gain(row)
        tail_elevation = float(self.plan["parameters"]["tail_elevation_degrees"])
        for name in self.tail_names:
            node = self.glb.name_to_node[name]
            axis = _qrotate(_qinv(_rotation_from_matrix(self.base_w[node])), tuple(self.lateral))
            rot[node] = _qmul(
                rot[node],
                _qrotvec(tuple(np.asarray(axis) * math.radians(gain * tail_elevation / len(self.tail_names)))),
            )
        performance_plan = self.plan if yaw else deepcopy(self.plan)
        if not yaw:
            performance_plan["performance"]["tail_yaw_degrees"] = 0.0
        apply_performance(
            self.glb, tr, rot, scales, self.base_w, self.roles,
            performance_plan, row, self.up, self.forward,
        )
        if self.mode == "in_place":
            # The in-place export overwrites only the root translation with
            # the first solved sample. The evaluator separately restores the
            # declared motor displacement below.
            first = self.reconstructed(0, yaw=yaw, driven=driven, cast32=False) if index != 0 else None
            if first is not None:
                tr[self.root] = tuple(first[0][self.root])
        if cast32:
            tr = [tuple(np.asarray(v, dtype=np.float32).astype(float)) for v in tr]
            rot = [tuple(np.asarray(v, dtype=np.float32).astype(float)) for v in rot]
            scales = [tuple(np.asarray(v, dtype=np.float32).astype(float)) for v in scales]
        return tr, rot, scales

    def actual(self, index: int):
        return _pose(self.glb, self.tracks, index)

    def tip_point(self, pose, index: int) -> np.ndarray:
        world = _world_matrices(self.glb, *pose)
        point = np.asarray(_world_position(world[self.tip]), dtype=float)
        if self.mode == "in_place":
            rows = self.plan["samples"]
            point += self.forward * (
                float(rows[index]["root_forward_m"]) - float(rows[0]["root_forward_m"])
            )
        return point


def categorized_velocity(package: Package, poses, indices, *, terminal: bool, varying: set[int]) -> np.ndarray:
    endpoint_local = poses[-1 if terminal else 0]
    points = []
    for index, pose in zip(indices, poses):
        tr = list(endpoint_local[0])
        rot = list(endpoint_local[1])
        scales = list(endpoint_local[2])
        for node in varying:
            tr[node], rot[node], scales[node] = pose[0][node], pose[1][node], pose[2][node]
        points.append(package.tip_point((tr, rot, scales), index))
    return velocity(package.times[indices], np.asarray(points), terminal=terminal)


def local_derivatives(package: Package, poses, indices, *, terminal: bool):
    """Apply the unchanged native three-point stencil to each local TRS track."""
    end = -1 if terminal else 0
    ids = [0, 1] if terminal else [1, 2]
    times = package.times[indices]
    translations, rotations, scales = [], [], []
    for node in range(len(package.glb.nodes)):
        t = np.asarray([pose[0][node] for pose in poses], dtype=float)
        s = np.asarray([pose[2][node] for pose in poses], dtype=float)
        endpoint = poses[end][1][node]
        q = np.asarray([
            _q_to_rotvec(_qmul(_qinv(tuple(endpoint)), tuple(poses[index][1][node])))
            for index in ids
        ])
        offsets = times[ids] - times[end]
        translations.append(_endpoint_derivative(offsets, t[ids] - t[end]))
        rotations.append(_endpoint_derivative(offsets, q))
        scales.append(_endpoint_derivative(offsets, s[ids] - s[end]))
    return np.asarray(translations), np.asarray(rotations), np.asarray(scales)


def chain_rule_velocity(package: Package, poses, indices, *, terminal: bool) -> np.ndarray:
    """Differentiate FK at the endpoint from native-stencil local derivatives.

    The symmetric epsilon is only a Jacobian evaluation around one endpoint;
    it does not inspect extra animation samples or replace the native stencil.
    """
    end = -1 if terminal else 0
    endpoint = poses[end]
    translation_v, angular_v, scale_v = local_derivatives(
        package, poses, indices, terminal=terminal
    )
    epsilon = 1e-6

    def point(sign: float) -> np.ndarray:
        translations = [tuple(np.asarray(endpoint[0][node]) + sign * epsilon * translation_v[node])
                        for node in range(len(package.glb.nodes))]
        rotations = [_qmul(endpoint[1][node], _qrotvec(tuple(sign * epsilon * angular_v[node])))
                     for node in range(len(package.glb.nodes))]
        scales = [tuple(np.asarray(endpoint[2][node]) + sign * epsilon * scale_v[node])
                  for node in range(len(package.glb.nodes))]
        worlds = _world_matrices(package.glb, translations, rotations, scales)
        return np.asarray(_world_position(worlds[package.tip]), dtype=float)

    result = (point(1.0) - point(-1.0)) / (2 * epsilon)
    if package.mode == "in_place":
        rows = package.plan["samples"]
        end = -1 if terminal else 0
        ids = [0, 1] if terminal else [1, 2]
        roots = np.asarray([rows[index]["root_forward_m"] for index in indices], dtype=float)
        motor = _endpoint_derivative(
            package.times[indices][ids] - package.times[indices][end],
            roots[ids] - roots[end],
        )
        result += package.forward * float(motor)
    return result


def window(package: Package, indices: list[int], *, terminal: bool) -> dict:
    actual = [package.actual(i) for i in indices]
    variants = {
        (yaw, driven): [
            package.reconstructed(i, yaw=yaw, driven=driven, cast32=False)
            for i in indices
        ]
        for yaw, driven in VARIANTS
    }
    variants32 = {
        key: [
            package.reconstructed(i, yaw=key[0], driven=key[1], cast32=True)
            for i in indices
        ]
        for key in VARIANTS
    }
    def points(poses):
        return np.asarray([package.tip_point(pose, i) for pose, i in zip(poses, indices)])
    actual_points = points(actual)
    values = {
        "actual": velocity(package.times[indices], actual_points, terminal=terminal),
        **{
            f"yaw_{int(yaw)}_driven_{int(driven)}_float64": velocity(
                package.times[indices], points(poses), terminal=terminal
            ) for (yaw, driven), poses in variants.items()
        },
        **{
            f"yaw_{int(yaw)}_driven_{int(driven)}_float32": velocity(
                package.times[indices], points(poses), terminal=terminal
            ) for (yaw, driven), poses in variants32.items()
        },
    }
    plan_times = np.asarray([package.plan["samples"][index]["time_s"] for index in indices])
    values["yaw_1_driven_1_float64_plan_clock"] = velocity(
        plan_times, points(variants[(True, True)]), terminal=terminal
    )
    values["yaw_1_driven_1_float32_plan_clock"] = velocity(
        plan_times, points(variants32[(True, True)]), terminal=terminal
    )
    path_nodes = []
    cursor = package.tip
    while cursor is not None:
        path_nodes.append(cursor)
        cursor = package.glb.parents[cursor]
    root_nodes = {package.root}
    pelvis_nodes = {package.pelvis}
    tail_nodes = set(package.tail)
    baseline = variants[(False, False)]
    values["baseline_root_only_float64"] = categorized_velocity(
        package, baseline, indices, terminal=terminal, varying=root_nodes
    )
    values["baseline_pelvis_only_float64"] = categorized_velocity(
        package, baseline, indices, terminal=terminal, varying=pelvis_nodes
    )
    values["baseline_other_tail_only_float64"] = categorized_velocity(
        package, baseline, indices, terminal=terminal, varying=tail_nodes
    )
    endpoint = indices[-1] if terminal else indices[0]
    actual_endpoint = actual[-1 if terminal else 0]
    reconstructed_endpoint = variants32[(True, True)][-1 if terminal else 0]
    return {
        "indices": indices,
        "times_s": package.times[indices].tolist(),
        "endpoint_index": endpoint,
        "endpoint_plan": {
            key: package.plan["samples"][endpoint].get(key)
            for key in (
                "time_s", "locomotion_time_s", "performance_gain",
                "root_forward_m", "root_velocity_mps",
                "pelvis_height_offset_m", "pelvis_vertical_velocity_mps",
            )
        },
        "endpoint_driven_tail_degrees": {
            name: package.body[endpoint]["sagittal_node_degrees"][name]
            for name in package.tail_names
        },
        "velocity_vectors_mps": {key: value.tolist() for key, value in values.items()},
        "reconstruction": {
            "maximum_tip_position_error_m": float(np.max(np.linalg.norm(
                actual_points - points(variants32[(True, True)]), axis=1
            ))),
            "endpoint_tip_position_error_m": float(np.linalg.norm(
                package.tip_point(actual_endpoint, endpoint)
                - package.tip_point(reconstructed_endpoint, endpoint)
            )),
            "maximum_endpoint_path_local_rotation_error_degrees": float(max(
                qdistance_degrees(actual_endpoint[1][node], reconstructed_endpoint[1][node])
                for node in path_nodes
            )),
            "path": [package.glb.nodes[node].get("name") for node in reversed(path_nodes)],
            "chest_is_tip_ancestor": package.chest in path_nodes,
        },
    }


def vector(values: dict, name: str) -> np.ndarray:
    return np.asarray(values["velocity_vectors_mps"][name], dtype=float)


def interface(kind: str, mode: str) -> dict:
    phase = 0.11666666666666667
    if kind == "start":
        before = Package(PAIR / "start", mode)
        after = Package(PAIR / "steady", mode)
        before_indices = before.indices(terminal=True, phase_s=0.0)
        after_indices = after.indices(terminal=False, phase_s=phase)
        before_terminal, after_terminal = True, False
    else:
        before = Package(PAIR / "steady", mode)
        after = Package(PAIR / "stop", mode)
        before_indices = before.indices(terminal=True, phase_s=phase)
        after_indices = after.indices(terminal=False, phase_s=0.0)
        before_terminal, after_terminal = True, False
    bw = window(before, before_indices, terminal=before_terminal)
    aw = window(after, after_indices, terminal=after_terminal)
    mismatches = {}
    names = bw["velocity_vectors_mps"]
    for name in names:
        mismatches[name] = vector(bw, name) - vector(aw, name)
    m11 = mismatches["yaw_1_driven_1_float64"]
    m01 = mismatches["yaw_0_driven_1_float64"]
    m10 = mismatches["yaw_1_driven_0_float64"]
    m00 = mismatches["yaw_0_driven_0_float64"]
    yaw_shapley = 0.5 * ((m11 - m01) + (m10 - m00))
    driven_shapley = 0.5 * ((m11 - m10) + (m01 - m00))
    root = mismatches["baseline_root_only_float64"]
    pelvis = mismatches["baseline_pelvis_only_float64"]
    other_tail = mismatches["baseline_other_tail_only_float64"]
    baseline_interaction = m00 - root - pelvis - other_tail

    before_full = [before.reconstructed(i, yaw=True, driven=True, cast32=False)
                   for i in before_indices]
    after_full = [after.reconstructed(i, yaw=True, driven=True, cast32=False)
                  for i in after_indices]
    chain_mismatch = chain_rule_velocity(
        before, before_full, before_indices, terminal=before_terminal
    ) - chain_rule_velocity(after, after_full, after_indices, terminal=after_terminal)
    before_local = local_derivatives(before, before_full, before_indices, terminal=True)
    after_local = local_derivatives(after, after_full, after_indices, terminal=False)
    translation_delta = before_local[0] - after_local[0]
    angular_delta = before_local[1] - after_local[1]

    before_endpoint = before_indices[-1]
    after_endpoint = after_indices[0]
    before_pose = before_full[-1]
    after_pose = after_full[0]
    before_distance = (before.plan["samples"][before_endpoint]["root_forward_m"]
                       - before.plan["samples"][0]["root_forward_m"])
    after_distance = (after.plan["samples"][after_endpoint]["root_forward_m"]
                      - after.plan["samples"][0]["root_forward_m"])
    aligned_position = (before.tip_point(before_pose, before_endpoint)
                        - before.forward * (before_distance - after_distance)
                        - after.tip_point(after_pose, after_endpoint))
    path_nodes = []
    cursor = before.tip
    while cursor is not None:
        path_nodes.append(cursor)
        cursor = before.glb.parents[cursor]
    tail_ancestor_rows = []
    for name in before.tail_names:
        node = before.glb.name_to_node[name]
        value = np.degrees(angular_delta[node])
        tail_ancestor_rows.append({"node": name, "vector_degrees_per_s": value.tolist(),
                                   "norm_degrees_per_s": float(np.linalg.norm(value)),
                                   "moves_Bone_016_origin": node != before.tip})

    def record(value):
        value = np.asarray(value, dtype=float)
        return {"vector_mps": value.tolist(), "norm_mps": float(np.linalg.norm(value))}

    return {
        "kind": kind,
        "mode": mode,
        "witness": "Bone_016 runtime node origin",
        "before": bw,
        "after": aw,
        "join_mismatch": {
            name: record(value) for name, value in mismatches.items()
        },
        "float64_shapley_decomposition": {
            "authored_tail_yaw": record(yaw_shapley),
            "driven_tail_sagittal_response": record(driven_shapley),
            "baseline_without_these_two": record(m00),
            "sum": record(yaw_shapley + driven_shapley + m00),
        },
        "baseline_kinematic_decomposition": {
            "root_local_trs": record(root),
            "pelvis_local_trs": record(pelvis),
            "other_tail_local_trs_including_centering_static_elevation": record(other_tail),
            "composition_interaction": record(baseline_interaction),
            "chest": {"vector_mps": [0.0, 0.0, 0.0], "norm_mps": 0.0,
                      "reason": "Bone_002 chest is not an ancestor of Bone_016"},
            "sum": record(root + pelvis + other_tail + baseline_interaction),
        },
        "endpoint_source_state_continuity": {
            "aligned_Bone_016_position_error_m": aligned_position.tolist(),
            "aligned_Bone_016_position_error_norm_m": float(np.linalg.norm(aligned_position)),
            "maximum_path_local_rotation_error_degrees": float(max(
                qdistance_degrees(before_pose[1][node], after_pose[1][node])
                for node in path_nodes
            )),
            "maximum_driven_tail_angle_error_degrees": float(max(
                abs(bw["endpoint_driven_tail_degrees"][name]
                    - aw["endpoint_driven_tail_degrees"][name])
                for name in before.tail_names
            )),
            "pelvis_height_error_m": float(
                bw["endpoint_plan"]["pelvis_height_offset_m"]
                - aw["endpoint_plan"]["pelvis_height_offset_m"]
            ),
            "pelvis_declared_vertical_velocity_error_mps": float(
                bw["endpoint_plan"]["pelvis_vertical_velocity_mps"]
                - aw["endpoint_plan"]["pelvis_vertical_velocity_mps"]
            ),
            "phase_and_gain_reason": (
                "both endpoints resolve phase 0.11666666666666667 s and gain 1; "
                "transition envelope first derivative is zero at its handoff"
            ),
        },
        "local_stencil_witness": {
            "root_translation": record(translation_delta[before.root]),
            "pelvis_translation": record(translation_delta[before.pelvis]),
            "tail_local_angular": tail_ancestor_rows,
        },
        "chain_rule_FK_from_same_local_stencil": record(chain_mismatch),
    }


def main() -> None:
    for relative, expected in EXPECTED_ENGINE.items():
        actual = sha(SOURCE_ROOT / "src/eonwild_motion" / relative)
        if actual != expected:
            raise SystemExit(f"engine source differs for {relative}: {actual}")
    inputs = {}
    locked_engine_maps = []
    for role in ("start", "steady", "stop"):
        inputs[role] = {}
        for name in ("root_motion.glb", "in_place.glb", "plan.json", "solver-receipt.json", "manifest.json", "inputs.lock.json"):
            inputs[role][name] = sha(PAIR / role / name)
        locked_engine_maps.append(json.loads((PAIR / role / "inputs.lock.json").read_text())["engine_files"])
    if not locked_engine_maps[0] == locked_engine_maps[1] == locked_engine_maps[2]:
        raise SystemExit("sprint package engine maps differ")
    mismatched_engine_files = []
    for relative, expected in locked_engine_maps[0].items():
        path = SOURCE_ROOT / "src/eonwild_motion" / relative
        actual = sha(path) if path.exists() else None
        if actual != expected:
            mismatched_engine_files.append({"path": relative, "expected": expected, "actual": actual})
    if mismatched_engine_files:
        raise SystemExit(f"current source differs from package engine map: {mismatched_engine_files}")
    rows = [interface(kind, mode) for kind in KINDS for mode in MODES]
    result = {
        "schema": "eonwild.motion.diagnostic.sprint-tail-handoff-causal.v1",
        "scope": "read-only exact native-window Bone_016 decomposition; evaluator and gates unchanged",
        "source_root": str(SOURCE_ROOT),
        "source_git_commit": "c43d426ca8e5a2610c37ad7ae235ef623cb3f3fa",
        "pair_root": str(PAIR),
        "engine_files": EXPECTED_ENGINE,
        "complete_package_engine_binding": {
            "entry_count": len(locked_engine_maps[0]),
            "canonical_json_sha256": hashlib.sha256(json.dumps(
                locked_engine_maps[0], sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest(),
            "all_three_maps_identical": True,
            "current_source_matches_all_entries": True,
        },
        "immutable_input_sha256": inputs,
        "interfaces": rows,
        "definitions": {
            "float64_reconstruction": "same package plan, body-response receipt, source rest TRS, solver operation order and authored performance formulas, without GLB float32 serialization",
            "float32_reconstruction": "same reconstruction with local TRS cast to float32 before FK",
            "Shapley": "two-control order-independent allocation of the reconstructed mismatch to authored tail yaw and driven sagittal response; baseline retains root, pelvis, centering and static elevation",
            "finite_stencil": "unchanged three-sample one-sided quadratic endpoint derivative used by factory.handoff",
        },
        "evaluator_changed": False,
        "gate_changed": False,
        "source_changed": False,
        "interpretation": {
            "endpoint_state": "phase-aligned source endpoint position, rotations, driven response, pelvis height and declared pelvis velocity agree to floating-point roundoff after declared travel alignment",
            "dominant_term": "the driven sagittal tail response supplies the largest float64 finite-window mismatch; authored yaw is secondary at start and negligible at stop; chest is outside the witness hierarchy",
            "serialization": "float32 timestamps/TRS alter the estimate but happen to reduce all four current residuals; float64 source reconstruction remains above the gate",
            "mechanism": "one-sided finite-window truncation and serialized clock/TRS quantization acting on a long nonlinear FK chain; no endpoint source-state inconsistency was found",
            "chain_rule_assessment": "differentiating FK from the same native-stencil local TRS derivatives does not remove the residual because the local derivative estimates already differ; it is not justified as a follow-up gate change from this evidence",
            "next_action": "preserve the emitted BLOCKED result and make no authored motion, phase, amplitude, evaluator or threshold change from this diagnostic",
        },
        "status": "DIAGNOSTIC_COMPLETE",
    }
    after = {}
    for role, files in inputs.items():
        after[role] = {name: sha(PAIR / role / name) for name in files}
    if after != inputs:
        raise RuntimeError("package inputs changed during analysis")
    result["immutable_input_sha256_after"] = after
    result["inputs_unchanged"] = True
    output = HERE / "result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(output)
    for row in rows:
        actual = row["join_mismatch"]["actual"]["norm_mps"]
        f64 = row["join_mismatch"]["yaw_1_driven_1_float64"]["norm_mps"]
        f32 = row["join_mismatch"]["yaw_1_driven_1_float32"]["norm_mps"]
        decomp = row["float64_shapley_decomposition"]
        print(row["kind"], row["mode"], "actual", actual, "f64", f64, "f32", f32,
              "yaw", decomp["authored_tail_yaw"]["norm_mps"],
              "driven", decomp["driven_tail_sagittal_response"]["norm_mps"],
              "baseline", decomp["baseline_without_these_two"]["norm_mps"])


if __name__ == "__main__":
    main()
