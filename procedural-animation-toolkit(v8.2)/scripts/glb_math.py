#!/usr/bin/env python3
"""Patch only the allowlisted V8.2 walk rotation float32 accessors in place."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def q_normal(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    return q / np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-15)


def q_inv(q: np.ndarray) -> np.ndarray:
    q = q_normal(q)
    return np.concatenate([-q[..., :3], q[..., 3:4]], axis=-1)


def q_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    av, aw, bv, bw = a[..., :3], a[..., 3:4], b[..., :3], b[..., 3:4]
    return q_normal(np.concatenate([aw * bv + bw * av + np.cross(av, bv), aw * bw - np.sum(av * bv, axis=-1, keepdims=True)], axis=-1))


def q_from_rotvec(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float64)
    angle = np.linalg.norm(vector, axis=-1, keepdims=True)
    half = angle * .5
    scale = np.where(angle > 1e-12, np.sin(half) / angle, .5 - angle * angle / 48.0)
    return q_normal(np.concatenate([vector * scale, np.cos(half)], axis=-1))


def q_to_rotvec(q: np.ndarray) -> np.ndarray:
    q = q_normal(q)
    q = q if q[..., 3] >= 0.0 else -q
    vector, scalar = q[:3], float(np.clip(q[3], -1.0, 1.0))
    angle = 2.0 * np.arctan2(np.linalg.norm(vector), scalar)
    return vector * (angle / max(np.linalg.norm(vector), 1e-15))


def q_rotate(q: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Rotate a 3-vector by an xyzw quaternion without SciPy."""
    q = q_normal(q)
    pure = np.asarray([vector[0], vector[1], vector[2], 0.0], dtype=np.float64)
    return q_mul(q_mul(q, pure), q_inv(q))[:3]


def q_to_euler_xyz(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q_normal(q)
    return np.asarray([
        np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y)),
        np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0)),
        np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)),
    ], dtype=np.float64)


def q_from_euler_xyz(values: np.ndarray) -> np.ndarray:
    x, y, z = np.asarray(values, dtype=np.float64) * .5
    cx, cy, cz = np.cos([x, y, z])
    sx, sy, sz = np.sin([x, y, z])
    # Exact inverse of q_to_euler_xyz / the evaluator's intrinsic XYZ basis.
    # The prior signs reconstructed a different orientation and correctly
    # tripped the local-delta fail-close.
    return q_normal(np.asarray([sx * cy * cz - cx * sy * sz, cx * sy * cz + sx * cy * sz, cx * cy * sz - sx * sy * cz, cx * cy * cz + sx * sy * sz], dtype=np.float64))


def q_power(q: np.ndarray, fraction: float) -> np.ndarray:
    return q_from_rotvec(q_to_rotvec(q) * float(fraction))


class Glb:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_bytes()
        magic, version, total = struct.unpack_from("<4sII", self.raw, 0)
        if magic != b"glTF" or version != 2 or total != len(self.raw):
            raise ValueError("invalid GLB")
        cursor, self.bin_start, self.binary = 12, None, None
        while cursor < len(self.raw):
            length, kind = struct.unpack_from("<II", self.raw, cursor)
            cursor += 8
            chunk = self.raw[cursor:cursor + length]
            if kind == 0x4E4F534A:
                self.json = json.loads(chunk.decode("utf-8"))
            elif kind == 0x004E4942:
                self.bin_start, self.binary = cursor, chunk
            cursor += length
        if self.bin_start is None or self.binary is None:
            raise ValueError("GLB missing BIN")
        self.nodes = self.json["nodes"]
        self.name_to_node = {node.get("name", f"node_{i}"): i for i, node in enumerate(self.nodes)}
        self.parents: list[int | None] = [None] * len(self.nodes)
        for parent, node in enumerate(self.nodes):
            for child in node.get("children", []):
                self.parents[int(child)] = parent
        self.rest_rotation = [np.asarray(node.get("rotation", [0., 0., 0., 1.]), dtype=np.float64) for node in self.nodes]

    def accessor(self, index: int) -> np.ndarray:
        item = self.json["accessors"][index]
        view = self.json["bufferViews"][item["bufferView"]]
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[item["type"]]
        if item["componentType"] != 5126:
            raise ValueError(f"unsupported accessor component: {index}")
        offset = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
        return np.frombuffer(self.binary, dtype="<f4", count=int(item["count"]) * width, offset=offset).reshape((-1, width)).astype(np.float64)

    def animation(self, name: str) -> dict:
        for animation in self.json.get("animations", []):
            if animation.get("name") == name:
                return animation
        raise KeyError(name)

    def tracks(self, name: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        animation = self.animation(name)
        times, rotations = None, {}
        for channel in animation["channels"]:
            sampler = animation["samplers"][channel["sampler"]]
            input_times = self.accessor(int(sampler["input"])).reshape(-1)
            if times is None:
                times = input_times
            elif not np.array_equal(times, input_times):
                raise ValueError(f"mixed timelines: {name}")
            if channel["target"]["path"] == "rotation":
                node = self.nodes[channel["target"]["node"]].get("name")
                rotations[node] = self.accessor(int(sampler["output"]))
        if times is None:
            raise ValueError(f"no tracks: {name}")
        return times, rotations

    def rotation_accessors(self, name: str) -> dict[str, int]:
        animation = self.animation(name)
        output: dict[str, int] = {}
        for channel in animation["channels"]:
            if channel["target"]["path"] == "rotation":
                node = self.nodes[channel["target"]["node"]].get("name")
                output[node] = int(animation["samplers"][channel["sampler"]]["output"])
        return output

    def accessor_offset(self, index: int) -> tuple[int, int]:
        item = self.json["accessors"][index]
        view = self.json["bufferViews"][item["bufferView"]]
        if item["componentType"] != 5126 or item["type"] != "VEC4" or int(view.get("byteStride", 16)) != 16:
            raise ValueError(f"unexpected rotation accessor: {index}")
        return int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0)), int(item["count"])


def depth_order(glb: Glb, names: list[str]) -> list[str]:
    def depth(name: str) -> int:
        node, total = glb.name_to_node[name], 0
        while glb.parents[node] is not None:
            total, node = total + 1, int(glb.parents[node])
        return total
    return sorted(names, key=lambda name: (depth(name), name))


def all_worlds(glb: Glb, locals_: list[np.ndarray]) -> list[np.ndarray]:
    worlds: list[np.ndarray | None] = [None] * len(locals_)
    def resolve(index: int) -> np.ndarray:
        if worlds[index] is None:
            parent = glb.parents[index]
            worlds[index] = locals_[index] if parent is None else q_mul(resolve(int(parent)), locals_[index])
        return worlds[index]  # type: ignore[return-value]
    return [resolve(index) for index in range(len(locals_))]


def baseline_locals(glb: Glb, rotations: dict[str, np.ndarray], sample: int) -> list[np.ndarray]:
    return [rotations.get(node.get("name", f"node_{index}"), np.asarray([glb.rest_rotation[index]]))[sample if node.get("name", f"node_{index}") in rotations else 0] for index, node in enumerate(glb.nodes)]


def make_overlay(glb: Glb, config: dict, scale: dict[str, float]) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    clip = config["pinnedInput"]["walkClips"][1]
    times, rotations = glb.tracks(clip)
    allowed = [name for group in ("spine", "neck", "head", "tail") for name in config["allowlist"][group]]
    local_samples = [baseline_locals(glb, rotations, sample) for sample in range(len(times))]
    rest_world = all_worlds(glb, glb.rest_rotation)
    pelvis = glb.name_to_node["Bone_001"]
    # These local axes are the exact rest-calibrated anatomical axes used by
    # the V5.5/V8.1 Pose.rotate_world_rest_axis solver.  Applying only the
    # V5.5-minus-V8.1 increment on the *right* preserves all frozen V8.1
    # response already present in the local arrays rather than replacing it.
    up, forward = np.array([0., 1., 0.]), np.array([0., 0., 1.])
    def local_axis(name: str, axis: np.ndarray) -> np.ndarray:
        return q_rotate(q_inv(rest_world[glb.name_to_node[name]]), axis)
    pelvis_up, pelvis_forward = local_axis("Bone_001", up), local_axis("Bone_001", forward)
    yaw = np.array([np.dot(q_to_rotvec(q_mul(q_inv(glb.rest_rotation[pelvis]), local[pelvis])), pelvis_up) for local in local_samples])
    roll = np.array([np.dot(q_to_rotvec(q_mul(q_inv(glb.rest_rotation[pelvis]), local[pelvis])), pelvis_forward) for local in local_samples])
    yaw, roll = yaw - yaw.mean(), roll - roll.mean()
    gain = lambda key, alpha: config["blend"][key]["v8_1"] + alpha * (config["blend"][key]["v5_5"] - config["blend"][key]["v8_1"])
    alpha, alpha_tail = float(config["blend"]["alpha"]), float(config["blend"]["alphaTail"])
    spine_delta = gain("spineYawGain", alpha) - config["blend"]["spineYawGain"]["v8_1"]
    neck_delta = gain("neckStabilizeGain", alpha) - config["blend"]["neckStabilizeGain"]["v8_1"]
    head_delta = gain("headStabilizeGain", alpha) - config["blend"]["headStabilizeGain"]["v8_1"]
    tail_factor = alpha_tail * ((config["blend"]["tailRootYawGain"]["v5_5"] / config["blend"]["tailRootYawGain"]["v8_1"] - 1.0) + (config["blend"]["tailComGain"]["v5_5"] / config["blend"]["tailComGain"]["v8_1"] - 1.0)) * .5
    spine_w = dict(zip(config["allowlist"]["spine"], config["weights"]["spine"]))
    neck_w = dict(zip(config["allowlist"]["neck"], config["weights"]["neck"]))
    tail_w = dict(zip(config["allowlist"]["tail"], config["weights"]["tailBaseToTip"]))
    output = {name: np.empty((len(times), 4), dtype=np.float64) for name in allowed}
    max_delta = {name: 0.0 for name in allowed}
    tail_baseline = {name: local_samples[0][glb.name_to_node[name]] for name in config["allowlist"]["tail"]}
    group = config["responseGroups"]
    for sample, locals_ in enumerate(local_samples):
        for name in allowed:
            base_local = locals_[glb.name_to_node[name]]
            if name in spine_w:
                vector = (local_axis(name, up) * (-spine_delta * yaw[sample]) + local_axis(name, forward) * (-float(config["spineRollIncrementGain"]) * roll[sample])) * spine_w[name] * scale["spine"] * float(group["spine"])
            elif name in neck_w:
                vector = (local_axis(name, up) * (neck_delta * yaw[sample]) + local_axis(name, forward) * (neck_delta * roll[sample])) * neck_w[name] * scale["neck"] * float(group["neck"])
            elif name == "Bone_036":
                vector = (local_axis(name, up) * (-head_delta * yaw[sample]) + local_axis(name, forward) * (-head_delta * roll[sample])) * scale["head"] * float(group["head"])
            else:
                # V5.5-minus-V8.1 response transfer: amplify the frozen,
                # already smooth V8.1 tail dynamic about its cycle baseline.
                # This retains its base-to-tip phase and introduces no sampled
                # target curve or isolated keys.
                dynamic = q_to_rotvec(q_mul(q_inv(tail_baseline[name]), base_local))
                vector = dynamic * (tail_factor * tail_w[name] * scale["tail"] * float(group["tail"]))
            local_target = q_mul(base_local, q_from_rotvec(vector))
            output[name][sample] = local_target
            max_delta[name] = max(max_delta[name], float(np.degrees(np.linalg.norm(q_to_rotvec(q_mul(q_inv(base_local), local_target))))) )
    # Candidate-C chest correction: a world-space fore-aft roll increment is
    # distributed through the spine and reconstructed parent-to-child.  Unlike
    # a local-axis roll, this directly changes the evaluator's chest-relative
    # roll basis while preserving pitch/yaw and the already accepted tail/head
    # overlay.  The driver is the frozen pelvis world-roll signal; no new
    # schedule, translation, or sampled target curve is introduced.
    spine_world_gain = float(config.get("spineWorldRollIncrementGain", 0.0))
    if abs(spine_world_gain) > 0.0:
        chest_name = "Bone_002"
        reference_pelvis = all_worlds(glb, local_samples[0])[pelvis]
        for sample, locals_ in enumerate(local_samples):
            source_pelvis = all_worlds(glb, locals_)[pelvis]
            # Match the evaluator's phase-zero world convention: current
            # pelvis world rotation composed with the inverse reference, not
            # the hierarchy-local inverse/reference order.
            pelvis_phase = q_to_euler_xyz(q_mul(source_pelvis, q_inv(reference_pelvis)))
            rebuilt = list(locals_)
            for name in allowed:
                rebuilt[glb.name_to_node[name]] = output[name][sample]
            targets = all_worlds(glb, rebuilt)
            baseline_targets = list(targets)
            index = glb.name_to_node[chest_name]
            parent = glb.parents[index]
            pelvis_world_target = targets[pelvis]
            approved_relative = q_mul(baseline_targets[index], q_inv(pelvis_world_target))
            target_euler = q_to_euler_xyz(approved_relative)
            # Preserve evaluator-relative pitch/yaw exactly. Add only the
            # bounded counterphase roll in R_chest @ R_pelvis.T, then restore
            # chest world as R_relative_target @ R_pelvis.
            target_euler[2] -= spine_world_gain * pelvis_phase[2]
            target_world = q_mul(q_from_euler_xyz(target_euler), pelvis_world_target)
            chest_delta = q_mul(target_world, q_inv(baseline_targets[index]))
            # Smoothly carry the same world delta through the first five spine
            # links; Bone_002 receives the exact residual required to hit the
            # official chest-relative target.
            cumulative = 0.0
            for name, weight in zip(config["allowlist"]["spine"][:-1], config["weights"]["spine"][:-1]):
                cumulative += float(weight)
                child = glb.name_to_node[name]
                parent_child = glb.parents[child]
                desired_world = q_mul(q_power(chest_delta, cumulative), baseline_targets[child])
                desired_local = desired_world if parent_child is None else q_mul(q_inv(targets[int(parent_child)]), desired_world)
                output[name][sample] = desired_local
                targets[child] = desired_world
                max_delta[name] = max(max_delta[name], float(np.degrees(np.linalg.norm(q_to_rotvec(q_mul(q_inv(locals_[child]), desired_local))))) )
            parent = glb.parents[index]
            local_target = target_world if parent is None else q_mul(q_inv(targets[int(parent)]), target_world)
            output[chest_name][sample] = local_target
            max_delta[chest_name] = max(max_delta[chest_name], float(np.degrees(np.linalg.norm(q_to_rotvec(q_mul(q_inv(locals_[index]), local_target))))) )
            targets[index] = target_world
            # Stabilize the head against the new chest world delta with a
            # parent-to-child cancellation.  At neck link n the residual
            # world delta is (1-fraction[n]) * chest_delta, so the *local*
            # change is only that link's incremental fraction.  Applying
            # -fraction in world space here would double-count the changed
            # chest parent and exceed the local safety bound.
            neck_head = [*config["allowlist"]["neck"], "Bone_036"]
            fractions = [0.11, 0.26, 0.45, 0.69, 1.0, 1.0]
            for name, fraction in zip(neck_head, fractions):
                child = glb.name_to_node[name]
                parent = glb.parents[child]
                desired_world = q_mul(q_power(chest_delta, 1.0 - fraction), baseline_targets[child])
                desired_local = desired_world if parent is None else q_mul(q_inv(targets[int(parent)]), desired_world)
                output[name][sample] = desired_local
                targets[child] = desired_world
                max_delta[name] = max(max_delta[name], float(np.degrees(np.linalg.norm(q_to_rotvec(q_mul(q_inv(locals_[child]), desired_local))))) )
    for values in output.values():
        for sample in range(1, len(values)):
            if float(np.dot(values[sample - 1], values[sample])) < 0.0:
                values[sample] *= -1.0
        values[-1] = values[0]
    return output, max_delta


def scales_for_bounds(deltas: dict[str, float], config: dict) -> dict[str, float]:
    bounds, allow = config["boundsDegrees"], config["allowlist"]
    def factor(names: list[str], bound: float) -> float:
        value = max(deltas[name] for name in names)
        return 1.0 if value <= bound else bound / value
    return {"spine": factor(allow["spine"], bounds["spinePerBone"]), "neck": factor(allow["neck"], bounds["neckPerBone"]), "head": factor(allow["head"], bounds["headYawRoll"]), "tail": factor(allow["tail"], bounds["tailPerBone"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source = ROOT / config["pinnedInput"]["asset"]
    if sha256(source) != config["pinnedInput"]["sha256"]:
        raise RuntimeError("pinned source SHA mismatch")
    glb = Glb(source)
    allowed = [name for group in ("spine", "neck", "head", "tail") for name in config["allowlist"][group]]
    raw_overlay, raw_delta = make_overlay(glb, config, {"spine": 1., "neck": 1., "head": 1., "tail": 1.})
    scales = scales_for_bounds(raw_delta, config)
    overlay, deltas = make_overlay(glb, config, scales)
    limits = config["boundsDegrees"]
    violations = {
        name: value for name, value in deltas.items()
        if value > (limits["spinePerBone"] if name in config["allowlist"]["spine"]
                    else limits["neckPerBone"] if name in config["allowlist"]["neck"]
                    else limits["headYawRoll"] if name == "Bone_036"
                    else limits["tailPerBone"]) + 1e-6
    }
    if violations:
        raise RuntimeError(f"candidate exceeds local rotation bounds before write: {violations}")
    raw = bytearray(glb.raw)
    for clip in config["pinnedInput"]["walkClips"]:
        accessors = glb.rotation_accessors(clip)
        if not all(name in accessors for name in allowed):
            raise RuntimeError(f"missing allowlisted channel in {clip}")
        for name in allowed:
            offset, count = glb.accessor_offset(accessors[name])
            if overlay[name].shape != (count, 4):
                raise RuntimeError("unexpected accessor length")
            raw[glb.bin_start + offset:glb.bin_start + offset + count * 16] = overlay[name].astype("<f4").tobytes(order="C")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    report = {"schema": "eonwild.v8_2.balance_overlay_generation.v1", "status": "PASS", "source": str(source), "sourceSha256": sha256(source), "candidate": str(args.output), "candidateSha256": sha256(args.output), "walkClips": config["pinnedInput"]["walkClips"], "allowedRotationChannels": allowed, "changedAccessorCount": len(allowed) * 2, "unchangedPolicy": "source bytes copied; only pre-existing allowlisted rotation float32 output regions patched", "groupScalesForBounds": scales, "maxLocalDeltaDegrees": deltas}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
