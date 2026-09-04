#!/usr/bin/env python3
"""Phase-normalized V8.2 balance evaluator.

This evaluator is deliberately independent of the V8.2 implementation
validator.  It reads an exported GLB, samples a named in-place walk at 120
even loop phases (without its duplicated final key), resolves world TRS, and
reports the V5.5/V8.1 balance-transfer measurements in the GLB world basis:
X=lateral, Y=up, Z=sagittal. Translation envelopes are normalized by the
median pelvis-to-lowest-distal-foot height for that same sampled cycle.

Rotations use the frozen evaluator's world-basis rotation-vector convention:
pelvis/head values are world motion against phase zero; chest/tail values are
the instantaneous world rotation relative to the pelvis. Components are
therefore pitch=X, yaw=Y, roll=Z. This intentionally differs from the
implementation validator's local Euler diagnostics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
import struct
import sys
from typing import Iterable

import numpy as np


PHASE_SAMPLES = 120
SEMANTICS = {
    "pelvis": "Bone_001",
    "chest": "Bone_002",
    "head": "Bone_036",
    "tail_base": "Bone_024",
    "tail_mid": "Bone_020",
    "tail_tip": "Bone_016",
    "ankle_left": "Bone_009",
    "ankle_right": "Bone_013",
    "foot_left": "Bone_008",
    "foot_right": "Bone_012",
    # Distal witnesses used by the frozen V5.5/V8.1 comparison: third digit
    # tips, not the first digit root.
    "toe_tip_left": "Bone_048",
    "toe_tip_right": "Bone_057",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def q_normal(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    return q / max(float(np.linalg.norm(q)), 1e-15)


def q_inv(q: np.ndarray) -> np.ndarray:
    q = q_normal(q)
    return np.asarray([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)


def q_mul(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    x1, y1, z1, w1 = q_normal(left)
    x2, y2, z2, w2 = q_normal(right)
    return q_normal(np.asarray([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ], dtype=np.float64))


def q_slerp(start: np.ndarray, end: np.ndarray, fraction: float) -> np.ndarray:
    start, end = q_normal(start), q_normal(end)
    dot = float(np.dot(start, end))
    if dot < 0.0:
        end, dot = -end, -dot
    if dot > 0.9995:
        return q_normal(start + fraction * (end - start))
    theta = math.acos(np.clip(dot, -1.0, 1.0))
    sine = math.sin(theta)
    return q_normal((math.sin((1.0 - fraction) * theta) / sine) * start + (math.sin(fraction * theta) / sine) * end)


def q_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q_normal(q)
    return np.asarray([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)


def q_euler_xyz(q: np.ndarray) -> np.ndarray:
    """Intrinsic XYZ decomposition, matching scipy Rotation.as_euler('xyz')."""
    x, y, z, w = q_normal(q)
    return np.asarray([
        math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)),
        math.asin(np.clip(2 * (w * y - z * x), -1.0, 1.0)),
        math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)),
    ], dtype=np.float64)


def matrix(translation: np.ndarray, rotation: np.ndarray, scale: np.ndarray) -> np.ndarray:
    result = np.eye(4, dtype=np.float64)
    result[:3, :3] = q_matrix(rotation) @ np.diag(scale)
    result[:3, 3] = translation
    return result


@dataclass(frozen=True)
class Animation:
    name: str
    times: np.ndarray
    rotations: dict[str, np.ndarray]
    translations: dict[str, np.ndarray]

    @property
    def duration(self) -> float:
        return float(self.times[-1] - self.times[0])


class Glb:
    """Narrow, float32 GLB 2.0 reader sufficient for baked skeleton tracks."""

    _WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    _DTYPE = {5120: np.dtype("<i1"), 5121: np.dtype("<u1"), 5122: np.dtype("<i2"), 5123: np.dtype("<u2"), 5125: np.dtype("<u4"), 5126: np.dtype("<f4")}

    def __init__(self, path: Path):
        self.path = path
        raw = path.read_bytes()
        magic, version, total = struct.unpack_from("<4sII", raw, 0)
        if magic != b"glTF" or version != 2 or total != len(raw):
            raise ValueError(f"invalid GLB: {path}")
        cursor = 12
        document = binary = None
        while cursor < len(raw):
            length, kind = struct.unpack_from("<II", raw, cursor)
            cursor += 8
            chunk = raw[cursor: cursor + length]
            cursor += length
            if kind == 0x4E4F534A:
                document = json.loads(chunk.decode("utf-8"))
            elif kind == 0x004E4942:
                binary = chunk
        if document is None or binary is None:
            raise ValueError(f"missing JSON/BIN chunk: {path}")
        self.doc, self.binary = document, binary
        self.nodes = self.doc.get("nodes", [])
        self.name_to_node = {node.get("name", f"node_{index}"): index for index, node in enumerate(self.nodes)}
        self.parents: list[int | None] = [None] * len(self.nodes)
        for parent, node in enumerate(self.nodes):
            for child in node.get("children", []):
                self.parents[int(child)] = parent
        self.rest_translation: list[np.ndarray] = []
        self.rest_rotation: list[np.ndarray] = []
        self.rest_scale: list[np.ndarray] = []
        for node in self.nodes:
            if "matrix" in node:
                raw_matrix = np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4).T
                translation = raw_matrix[:3, 3]
                basis = raw_matrix[:3, :3]
                scale = np.linalg.norm(basis, axis=0)
                # The supplied packs use TRS nodes, but retain a clear error
                # rather than silently guessing a matrix-node quaternion.
                raise ValueError("matrix-form nodes are unsupported by this evaluator")
            else:
                translation = np.asarray(node.get("translation", [0, 0, 0]), dtype=np.float64)
                rotation = q_normal(np.asarray(node.get("rotation", [0, 0, 0, 1]), dtype=np.float64))
                scale = np.asarray(node.get("scale", [1, 1, 1]), dtype=np.float64)
            self.rest_translation.append(translation)
            self.rest_rotation.append(rotation)
            self.rest_scale.append(scale)

    def accessor(self, index: int) -> np.ndarray:
        item = self.doc["accessors"][index]
        if "bufferView" not in item:
            raise ValueError(f"sparse/implicit accessor unsupported: {index}")
        view = self.doc["bufferViews"][item["bufferView"]]
        dtype = self._DTYPE[item["componentType"]]
        width = self._WIDTH[item["type"]]
        count = int(item["count"])
        offset = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
        stride = int(view.get("byteStride", dtype.itemsize * width))
        if stride == dtype.itemsize * width:
            result = np.frombuffer(self.binary, dtype=dtype, count=count * width, offset=offset).reshape(count, width)
        else:
            result = np.ndarray((count, width), dtype=dtype, buffer=self.binary, offset=offset, strides=(stride, dtype.itemsize))
        return np.array(result, dtype=np.float64)

    def animation(self, name: str) -> Animation:
        raw = next((item for item in self.doc.get("animations", []) if item.get("name") == name), None)
        if raw is None:
            available = [item.get("name") for item in self.doc.get("animations", [])]
            raise KeyError(f"unknown animation {name}; available={available}")
        common = None
        rotations: dict[str, np.ndarray] = {}
        translations: dict[str, np.ndarray] = {}
        for channel in raw["channels"]:
            sampler = raw["samplers"][int(channel["sampler"])]
            times = self.accessor(int(sampler["input"])).reshape(-1)
            if common is None:
                common = times
            elif not np.array_equal(common, times):
                raise ValueError(f"mixed track timelines: {name}")
            target = channel["target"]
            node = self.nodes[int(target["node"])].get("name", f"node_{target['node']}")
            if target["path"] == "rotation":
                rotations[node] = self.accessor(int(sampler["output"]))
            elif target["path"] == "translation":
                translations[node] = self.accessor(int(sampler["output"]))
        if common is None:
            raise ValueError(f"empty animation: {name}")
        return Animation(name, common, rotations, translations)

    def sample(self, animation: Animation, time: float) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
        time = float(np.clip(time, animation.times[0], animation.times[-1]))
        index = int(np.searchsorted(animation.times, time, side="right") - 1)
        index = max(0, min(index, len(animation.times) - 1))
        if index == len(animation.times) - 1 or animation.times[index] == time:
            return ({name: values[index] for name, values in animation.rotations.items()}, {name: values[index] for name, values in animation.translations.items()})
        next_index = index + 1
        fraction = float((time - animation.times[index]) / (animation.times[next_index] - animation.times[index]))
        rotations = {name: q_slerp(values[index], values[next_index], fraction) for name, values in animation.rotations.items()}
        translations = {name: values[index] * (1.0 - fraction) + values[next_index] * fraction for name, values in animation.translations.items()}
        return rotations, translations

    def pose(self, animation: Animation, time: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Resolve the frozen evaluator's body-coordinate pose convention.

        This deliberately mirrors the original evaluator's TRS traversal:
        parent rest scale is applied only to the immediate child translation.
        It is not a generic renderer matrix routine; preserving this behavior
        keeps the historical V8.1 normalization (and its scale-wrapper
        treatment) reproducible.
        """
        rotations, translations = self.sample(animation, time)
        local_t = np.asarray(self.rest_translation, dtype=np.float64).copy()
        local_q = np.asarray(self.rest_rotation, dtype=np.float64).copy()
        for index, node in enumerate(self.nodes):
            name = node.get("name", f"node_{index}")
            if name in rotations:
                local_q[index] = rotations[name]
            if name in translations:
                local_t[index] = translations[name]
        world_p = np.zeros((len(self.nodes), 3), dtype=np.float64)
        world_r = np.zeros((len(self.nodes), 3, 3), dtype=np.float64)
        done = np.zeros(len(self.nodes), dtype=bool)
        def resolve(index: int) -> None:
            if done[index]:
                return
            parent = self.parents[index]
            rotation = q_matrix(local_q[index])
            if parent is None:
                world_p[index] = local_t[index]
                world_r[index] = rotation
            else:
                resolve(parent)
                world_p[index] = world_p[parent] + world_r[parent] @ (local_t[index] * self.rest_scale[parent])
                world_r[index] = world_r[parent] @ rotation
            done[index] = True
        for index in range(len(self.nodes)):
            resolve(index)
        return local_t, local_q, world_p, world_r


def p2p(values: np.ndarray) -> float:
    return float(np.ptp(values))


def rotation_vector(matrix_value: np.ndarray) -> np.ndarray:
    """Signed world-basis rotation vector, matching the frozen report."""
    angle = math.acos(np.clip((float(np.trace(matrix_value)) - 1.0) / 2.0, -1.0, 1.0))
    if angle < 1e-9:
        return np.zeros(3, dtype=np.float64)
    axis = np.asarray([
        matrix_value[2, 1] - matrix_value[1, 2],
        matrix_value[0, 2] - matrix_value[2, 0],
        matrix_value[1, 0] - matrix_value[0, 1],
    ], dtype=np.float64) / (2.0 * math.sin(angle))
    return axis * angle


def vector_envelope(values: np.ndarray) -> dict[str, float]:
    return {"pitch_x": p2p(values[:, 0]), "yaw_y": p2p(values[:, 1]), "roll_z": p2p(values[:, 2])}


def q_angle(left: np.ndarray, right: np.ndarray) -> float:
    return math.degrees(2.0 * math.acos(min(1.0, abs(float(np.dot(q_normal(left), q_normal(right)))))))


def phase_times(animation: Animation) -> np.ndarray:
    # Exclude the duplicated loop endpoint.  0..119 are a 120-phase cycle.
    return animation.times[0] + np.arange(PHASE_SAMPLES, dtype=np.float64) * animation.duration / PHASE_SAMPLES


def find_distal_names(glb: Glb) -> tuple[str, str]:
    # The fixed semantics above are explicit for the supplied Tarbosaurus rig;
    # prefer their terminal descendants where present.
    return SEMANTICS["toe_tip_left"], SEMANTICS["toe_tip_right"]


def analyze(glb_path: Path, clip: str) -> dict:
    glb = Glb(glb_path)
    animation = glb.animation(clip)
    required = list(SEMANTICS.values())
    missing = [name for name in required if name not in glb.name_to_node]
    if missing:
        raise ValueError(f"missing Tarbosaurus semantic nodes: {missing}")
    samples = []
    for time in phase_times(animation):
        samples.append(glb.pose(animation, float(time)))
    node = glb.name_to_node
    positions = {name: np.asarray([world_p[node[name]] for _, _, world_p, _ in samples]) for name in SEMANTICS.values()}
    world_rotations = {name: np.asarray([world_r[node[name]] for _, _, _, world_r in samples]) for name in SEMANTICS.values()}
    local_rotations = {name: np.asarray([local_q[node[name]] for _, local_q, _, _ in samples]) for name in SEMANTICS.values()}
    lowest = np.minimum(positions[SEMANTICS["toe_tip_left"]][:, 1], positions[SEMANTICS["toe_tip_right"]][:, 1])
    hip_height = float(np.median(positions[SEMANTICS["pelvis"]][:, 1] - lowest))
    pelvis_pos = positions[SEMANTICS["pelvis"]]
    pelvis_translation = {"lateral_x": p2p(pelvis_pos[:, 0]) / hip_height, "vertical_y": p2p(pelvis_pos[:, 1]) / hip_height, "sagittal_z": p2p(pelvis_pos[:, 2]) / hip_height}
    pelvis_world = world_rotations[SEMANTICS["pelvis"]]
    pelvis_vectors = np.asarray([np.degrees(rotation_vector(value @ pelvis_world[0].T)) for value in pelvis_world])
    chest_vectors = np.asarray([np.degrees(rotation_vector(chest @ pelvis.T)) for chest, pelvis in zip(world_rotations[SEMANTICS["chest"]], pelvis_world)])
    head_relative_vectors = np.asarray([np.degrees(rotation_vector(head @ chest.T)) for head, chest in zip(world_rotations[SEMANTICS["head"]], world_rotations[SEMANTICS["chest"]])])
    head_world_vectors = np.asarray([np.degrees(rotation_vector(value @ world_rotations[SEMANTICS["head"]][0].T)) for value in world_rotations[SEMANTICS["head"]]])
    tail_vectors = {label: np.asarray([np.degrees(rotation_vector(tail @ pelvis.T)) for tail, pelvis in zip(world_rotations[name], pelvis_world)]) for label, name in (("base", SEMANTICS["tail_base"]), ("mid", SEMANTICS["tail_mid"]), ("tip", SEMANTICS["tail_tip"]))}
    result = {
        "asset": str(glb_path), "sha256": sha256(glb_path), "clip": clip, "duration_seconds": animation.duration, "phase_samples": PHASE_SAMPLES,
        "raw_body_coordinate_hip_height_m": hip_height,
        "pelvis_translation_peak_to_peak_by_hip_height": pelvis_translation,
        "pelvis_rotation_peak_to_peak_degrees": vector_envelope(pelvis_vectors),
        "chest_relative_to_pelvis_peak_to_peak_degrees": vector_envelope(chest_vectors),
        "head_relative_to_chest_peak_to_peak_degrees": vector_envelope(head_relative_vectors),
        "head_world_rotation_peak_to_peak_degrees": vector_envelope(head_world_vectors),
        "tail_relative_to_pelvis_peak_to_peak_degrees": {label: vector_envelope(values) for label, values in tail_vectors.items()},
        "tail_relative_to_pelvis_yaw_peak_phase": {label: float(np.argmax(np.abs(values[:, 1])) / PHASE_SAMPLES) for label, values in tail_vectors.items()},
        "counterphase_zero_lag_pearson": {"chest_roll_z_vs_pelvis_roll_z": float(np.corrcoef(chest_vectors[:, 2], pelvis_vectors[:, 2])[0, 1])},
        "lower_leg_local_rotation_envelope_degrees": {},
    }
    # Local-rotation diagnostics use baked local tracks, not world matrices.
    for label in ("ankle_left", "ankle_right", "foot_left", "foot_right", "toe_tip_left", "toe_tip_right"):
        name = SEMANTICS[label]
        if name not in animation.rotations:
            result["lower_leg_local_rotation_envelope_degrees"][label] = 0.0
            continue
        result["lower_leg_local_rotation_envelope_degrees"][label] = float(max(q_angle(local_rotations[name][0], value) for value in local_rotations[name]))
    # A declared geometric support/centroid proxy only. It supplies the
    # frozen comparison's balance read, not a physical COM claim.
    weights = {"pelvis": .34, "chest": .20, "head": .10, "tail_base": .14, "tail_mid": .13, "tail_tip": .09}
    centroid = sum(weight * positions[SEMANTICS[name]] for name, weight in weights.items())
    support, support_count = [], []
    for index in range(PHASE_SAMPLES):
        left = min(positions[SEMANTICS["foot_left"]][index, 1], positions[SEMANTICS["toe_tip_left"]][index, 1])
        right = min(positions[SEMANTICS["foot_right"]][index, 1], positions[SEMANTICS["toe_tip_right"]][index, 1])
        lowest_side = min(left, right)
        points = []
        if left <= lowest_side + .035 * hip_height:
            points.append(positions[SEMANTICS["foot_left"]][index])
        if right <= lowest_side + .035 * hip_height:
            points.append(positions[SEMANTICS["foot_right"]][index])
        if not points:
            points = [positions[SEMANTICS["foot_left"]][index] if left <= right else positions[SEMANTICS["foot_right"]][index]]
        support.append(np.mean(points, axis=0))
        support_count.append(len(points))
    support_delta = (centroid - np.asarray(support)) / hip_height
    result["support_proxy"] = {
        "single_support_phase_fraction": float(np.mean(np.asarray(support_count) == 1)),
        "double_support_phase_fraction": float(np.mean(np.asarray(support_count) == 2)),
        "mean_abs_lateral_offset_by_hip_height": float(np.mean(abs(support_delta[:, 0]))),
        "mean_abs_sagittal_offset_by_hip_height": float(np.mean(abs(support_delta[:, 2]))),
    }
    seam_zero = glb.pose(animation, 0.0)
    seam_end = glb.pose(animation, animation.duration)
    result["loop_seam"] = {
        "max_local_translation_m": max(float(np.linalg.norm(seam_end[0][index] - seam_zero[0][index])) for index in range(len(glb.nodes))),
        "max_local_rotation_degrees": max((q_angle(seam_zero[1][index], seam_end[1][index]) for index in range(len(glb.nodes))), default=0.0),
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved", required=True, type=Path, help="frozen V8.1 iteration-38 GLB")
    parser.add_argument("--approved-clip", default="PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE")
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--candidate-clip", default="PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected", type=Path, help="frozen evaluation-metrics.json; verifies V8.1 baseline")
    parser.add_argument("--tolerance", type=float, default=2e-5, help="absolute tolerance for frozen scalar metrics")
    parser.add_argument("--gate-mode", choices=("candidate-a-upper-only", "candidate-b-full-balance"), default="candidate-b-full-balance", help="acceptance interpretation; metric math remains identical")
    parser.add_argument("--enforce-gate", action="store_true", help="return non-zero when the selected candidate gate fails")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)


def flatten_numbers(value: object, prefix: str = "") -> dict[str, float]:
    if isinstance(value, dict):
        output: dict[str, float] = {}
        for key, item in value.items():
            output.update(flatten_numbers(item, f"{prefix}.{key}" if prefix else key))
        return output
    return {prefix: float(value)} if isinstance(value, (int, float)) else {}


def baseline_deltas(actual: dict, expected: dict) -> dict[str, float]:
    keys = ("raw_body_coordinate_hip_height_m", "pelvis_translation_peak_to_peak_by_hip_height", "pelvis_rotation_peak_to_peak_degrees", "chest_relative_to_pelvis_peak_to_peak_degrees", "head_relative_to_chest_peak_to_peak_degrees", "head_world_rotation_peak_to_peak_degrees", "tail_relative_to_pelvis_peak_to_peak_degrees", "counterphase_zero_lag_pearson", "support_proxy", "lower_leg_local_rotation_envelope_degrees", "loop_seam")
    actual_flat, expected_flat = {}, {}
    for key in keys:
        actual_flat.update(flatten_numbers(actual[key], key))
        expected_flat.update(flatten_numbers(expected[key], key))
    return {key: abs(actual_flat[key] - expected_flat[key]) for key in expected_flat}


def inclusive(value: float, bounds: list[float]) -> bool:
    return bounds[0] <= value <= bounds[1]


def overlay_gate(metrics: dict, approved: dict) -> dict:
    """The original V8.2 contract, evaluated in its frozen measurement basis."""
    targets = json.loads((Path(__file__).resolve().parents[1] / "evaluation-metrics.json").read_text(encoding="utf-8"))["v8_2_overlay_target_envelopes"]
    pelvis = metrics["pelvis_translation_peak_to_peak_by_hip_height"]
    pelvis_rotation = metrics["pelvis_rotation_peak_to_peak_degrees"]
    chest = metrics["chest_relative_to_pelvis_peak_to_peak_degrees"]
    tail = metrics["tail_relative_to_pelvis_peak_to_peak_degrees"]
    head = metrics["head_world_rotation_peak_to_peak_degrees"]
    checks = {
        "pelvis_lateral": inclusive(pelvis["lateral_x"], targets["pelvis_Bone_001"]["lateral_x_peak_to_peak_by_hip_height"]),
        "pelvis_vertical": inclusive(pelvis["vertical_y"], targets["pelvis_Bone_001"]["vertical_y_peak_to_peak_by_hip_height"]),
        "pelvis_sagittal": inclusive(pelvis["sagittal_z"], targets["pelvis_Bone_001"]["sagittal_z_peak_to_peak_by_hip_height"]),
        "pelvis_pitch": inclusive(pelvis_rotation["pitch_x"], targets["pelvis_Bone_001"]["pitch_x_degrees"]),
        "pelvis_yaw": inclusive(pelvis_rotation["yaw_y"], targets["pelvis_Bone_001"]["yaw_y_degrees"]),
        "pelvis_roll": inclusive(pelvis_rotation["roll_z"], targets["pelvis_Bone_001"]["roll_z_degrees"]),
        "chest_pitch": inclusive(chest["pitch_x"], targets["chest_Bone_002_relative_to_pelvis"]["pitch_x_degrees"]),
        "chest_yaw": inclusive(chest["yaw_y"], targets["chest_Bone_002_relative_to_pelvis"]["yaw_y_degrees"]),
        "chest_roll": inclusive(chest["roll_z"], targets["chest_Bone_002_relative_to_pelvis"]["roll_z_degrees"]),
        "chest_counterphase": inclusive(metrics["counterphase_zero_lag_pearson"]["chest_roll_z_vs_pelvis_roll_z"], targets["chest_Bone_002_relative_to_pelvis"]["roll_correlation_with_pelvis"]),
        "tail_base_yaw": inclusive(tail["base"]["yaw_y"], targets["tail_Bone_024_to_Bone_016_relative_to_pelvis"]["base_yaw_y_degrees"]),
        "tail_mid_yaw": inclusive(tail["mid"]["yaw_y"], targets["tail_Bone_024_to_Bone_016_relative_to_pelvis"]["mid_yaw_y_degrees"]),
        "tail_tip_yaw": inclusive(tail["tip"]["yaw_y"], targets["tail_Bone_024_to_Bone_016_relative_to_pelvis"]["tip_yaw_y_degrees"]),
        "head_pitch_cap": head["pitch_x"] <= targets["neck_head_Bone_041_to_Bone_036"]["head_world_pitch_x_max_degrees"],
        "head_yaw_cap": head["yaw_y"] <= targets["neck_head_Bone_041_to_Bone_036"]["head_world_yaw_y_max_degrees"],
        "head_roll_cap": head["roll_z"] <= targets["neck_head_Bone_041_to_Bone_036"]["head_world_roll_z_max_degrees"],
        "seam": metrics["loop_seam"]["max_local_translation_m"] == 0.0 and metrics["loop_seam"]["max_local_rotation_degrees"] <= targets["post_overlay_gates"]["max_loop_local_rotation_degrees"],
        "protected_lower_leg_equal_frozen": metrics["lower_leg_local_rotation_envelope_degrees"] == approved["lower_leg_local_rotation_envelope_degrees"],
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def candidate_a_upper_only_gate(metrics: dict, approved: dict) -> dict:
    """Architecture-safe A gate: no pelvis edit or lower-body disturbance."""
    chest, base_chest = metrics["chest_relative_to_pelvis_peak_to_peak_degrees"], approved["chest_relative_to_pelvis_peak_to_peak_degrees"]
    tail, base_tail = metrics["tail_relative_to_pelvis_peak_to_peak_degrees"], approved["tail_relative_to_pelvis_peak_to_peak_degrees"]
    head = metrics["head_world_rotation_peak_to_peak_degrees"]
    phase = metrics["tail_relative_to_pelvis_yaw_peak_phase"]
    checks = {
        # Candidate A is intentionally a post-bake upper-body-only lane.
        "pelvis_exact_to_approved": metrics["pelvis_translation_peak_to_peak_by_hip_height"] == approved["pelvis_translation_peak_to_peak_by_hip_height"] and metrics["pelvis_rotation_peak_to_peak_degrees"] == approved["pelvis_rotation_peak_to_peak_degrees"],
        "protected_lower_leg_exact": metrics["lower_leg_local_rotation_envelope_degrees"] == approved["lower_leg_local_rotation_envelope_degrees"],
        "chest_roll_safe_improvement": 5.4 <= chest["roll_z"] <= 6.25,
        "chest_counterphase": -.95 <= metrics["counterphase_zero_lag_pearson"]["chest_roll_z_vs_pelvis_roll_z"] <= -.70,
        "chest_pitch_no_unintended_change": abs(chest["pitch_x"] - base_chest["pitch_x"]) <= .2,
        "chest_yaw_non_regression": chest["yaw_y"] >= base_chest["yaw_y"],
        "head_caps": head["pitch_x"] <= 2.9 and head["yaw_y"] <= 2.1 and head["roll_z"] <= 1.2,
        "tail_base_yaw_improves": tail["base"]["yaw_y"] > base_tail["base"]["yaw_y"],
        "tail_mid_yaw_improves_at_least_1_5": tail["mid"]["yaw_y"] >= base_tail["mid"]["yaw_y"] + 1.5,
        "tail_tip_yaw_safe_improvement": base_tail["tip"]["yaw_y"] + 2.0 <= tail["tip"]["yaw_y"] <= base_tail["tip"]["yaw_y"] + 3.0,
        "tail_base_to_tip_phase_monotonic": phase["base"] <= phase["mid"] <= phase["tip"],
        "seam_exact": metrics["loop_seam"]["max_local_translation_m"] == 0.0 and metrics["loop_seam"]["max_local_rotation_degrees"] <= 1e-5,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "measured": {"chest": chest, "tail_yaw": {name: tail[name]["yaw_y"] for name in ("base", "mid", "tip")}, "tail_yaw_peak_phase": phase, "head": head}}


def main() -> int:
    args = parse_args()
    approved = analyze(args.approved, args.approved_clip)
    candidate = analyze(args.candidate, args.candidate_clip)
    result: dict[str, object] = {"schema": "eonwild.v8_2.balance_evaluator.v1", "basis": {"translation": {"x": "lateral", "y": "vertical/up", "z": "sagittal/fore-aft"}, "rotation": "phase-zero-relative intrinsic XYZ: pitch, yaw, roll"}, "normalization": "median sampled pelvis-to-lowest-distal-foot height", "approved": approved, "candidate": candidate}
    if args.expected:
        frozen = json.loads(args.expected.read_text(encoding="utf-8"))["per_asset"]["v8_1_iteration_38"]
        deltas = baseline_deltas(approved, frozen)
        result["frozen_baseline_verification"] = {"expected": str(args.expected), "tolerance": args.tolerance, "max_abs_delta": max(deltas.values()), "pass": max(deltas.values()) <= args.tolerance, "deltas": deltas}
        gate = candidate_a_upper_only_gate(candidate, approved) if args.gate_mode == "candidate-a-upper-only" else overlay_gate(candidate, approved)
        result["candidate_gate"] = {"mode": args.gate_mode, **gate}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result.get("frozen_baseline_verification", {"status": "NO_EXPECTED_BASELINE"}), indent=2))
    baseline_pass = not args.expected or result["frozen_baseline_verification"]["pass"]  # type: ignore[index]
    gate_pass = not args.enforce_gate or result["candidate_gate"]["status"] == "PASS"  # type: ignore[index]
    return 0 if baseline_pass and gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
