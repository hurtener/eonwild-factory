#!/usr/bin/env python3
"""Task-local semantic alert-idle quaternion overlay for a bound GLB clip."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any


TASK_ID = "V9-ALERT-IDLE-OVERLAY-001"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def parse_glb(raw: bytes) -> tuple[dict[str, Any], bytearray]:
    if len(raw) < 20:
        raise ValueError("GLB is truncated")
    magic, version, total = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or total != len(raw):
        raise ValueError("invalid GLB header")
    document: dict[str, Any] | None = None
    binary: bytearray | None = None
    cursor = 12
    while cursor < len(raw):
        length, kind = struct.unpack_from("<II", raw, cursor)
        cursor += 8
        chunk = raw[cursor : cursor + length]
        cursor += length
        if kind == 0x4E4F534A:
            loaded = json.loads(chunk.decode("utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("GLB JSON root is not an object")
            document = loaded
        elif kind == 0x004E4942:
            binary = bytearray(chunk)
    if document is None or binary is None:
        raise ValueError("GLB requires JSON and BIN chunks")
    return document, binary


def encode_glb(document: dict[str, Any], binary: bytearray) -> bytes:
    json_bytes = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    binary_bytes = bytes(binary) + b"\x00" * ((-len(binary)) % 4)
    total = 12 + 8 + len(json_bytes) + 8 + len(binary_bytes)
    return (
        struct.pack("<4sII", b"glTF", 2, total)
        + struct.pack("<II", len(json_bytes), 0x4E4F534A)
        + json_bytes
        + struct.pack("<II", len(binary_bytes), 0x004E4942)
        + binary_bytes
    )


def accessor_layout(document: dict[str, Any], index: int) -> tuple[int, int, int, int]:
    accessor = document["accessors"][index]
    if accessor.get("componentType") != 5126:
        raise ValueError(f"accessor {index} must use float32")
    widths = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}
    width = widths.get(accessor.get("type"))
    if width is None or "bufferView" not in accessor:
        raise ValueError(f"unsupported accessor {index}")
    view = document["bufferViews"][accessor["bufferView"]]
    offset = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    stride = int(view.get("byteStride", 4 * width))
    if stride < 4 * width:
        raise ValueError(f"accessor {index} stride is too small")
    return offset, int(accessor["count"]), stride, width


def read_accessor(
    document: dict[str, Any], binary: bytes | bytearray, index: int
) -> list[tuple[float, ...]]:
    offset, count, stride, width = accessor_layout(document, index)
    return [
        struct.unpack_from("<" + "f" * width, binary, offset + row * stride)
        for row in range(count)
    ]


def write_accessor(
    document: dict[str, Any], binary: bytearray, index: int, values: list[tuple[float, ...]]
) -> None:
    offset, count, stride, width = accessor_layout(document, index)
    if len(values) != count or any(len(value) != width for value in values):
        raise ValueError(f"accessor {index} value shape mismatch")
    for row, value in enumerate(values):
        struct.pack_into("<" + "f" * width, binary, offset + row * stride, *value)


def qmul(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def qnormalize(q: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in q))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("invalid quaternion")
    return tuple(value / norm for value in q)


def qaxis(axis: list[float], angle: float) -> tuple[float, ...]:
    if len(axis) != 3:
        raise ValueError("rotation axis must have three values")
    norm = math.sqrt(sum(float(value) ** 2 for value in axis))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("rotation axis must be finite and nonzero")
    scale = math.sin(angle / 2.0) / norm
    return (
        float(axis[0]) * scale,
        float(axis[1]) * scale,
        float(axis[2]) * scale,
        math.cos(angle / 2.0),
    )


def overlay_quaternion(
    *, time: float, cycle: float, strength: float, weight: float,
    mask: dict[str, Any], axes: dict[str, list[float]]
) -> tuple[float, ...]:
    phase = 2.0 * math.pi * (
        time / cycle - float(mask["phase_delay_cycles"])
    )
    # Persistent alert posture plus a low-frequency scan. This is a periodic
    # engineering control signal, not a scheduled listen/reaction event.
    pitch = math.radians(float(mask["pitch_degrees"])) * strength * weight
    yaw = math.radians(float(mask["yaw_degrees"])) * math.sin(phase) * strength * weight
    roll = math.radians(float(mask["roll_degrees"])) * math.sin(phase + math.pi / 2.0) * strength * weight
    return qnormalize(
        qmul(qmul(qaxis(axes["pitch"], pitch), qaxis(axes["yaw"], yaw)), qaxis(axes["roll"], roll))
    )


def semantic_nodes(roles: dict[str, Any], semantic: str) -> list[str]:
    value = roles.get(semantic)
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list) and value and all(isinstance(item, str) and item for item in value):
        return list(value)
    raise ValueError(f"semantic role {semantic!r} is not a node or node chain")


def animation_by_name(document: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [item for item in document.get("animations", []) if item.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one source animation {name!r}")
    return matches[0]


def channel_maps(
    document: dict[str, Any], animation: dict[str, Any]
) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    names: dict[str, int] = {}
    for index, node in enumerate(document.get("nodes", [])):
        name = node.get("name")
        if isinstance(name, str) and name:
            if name in names:
                raise ValueError("node display identities must be unique")
            names[name] = index
    channels: dict[tuple[str, str], int] = {}
    for channel in animation["channels"]:
        target_position = int(channel["target"]["node"])
        name = document["nodes"][target_position].get("name")
        key = (name, channel["target"]["path"])
        if key in channels:
            raise ValueError(f"duplicate animation channel {key}")
        channels[key] = int(animation["samplers"][channel["sampler"]]["output"])
    return names, channels


def validate_profile(profile: dict[str, Any], semantic_rig: dict[str, Any]) -> None:
    if profile.get("schema") != "eonwild.motion.v9.experimental-alert-idle-overlay.v1":
        raise ValueError("unexpected profile schema")
    if semantic_rig.get("schema") != "eonwild.motion.semantic-rig.v1":
        raise ValueError("unexpected semantic rig schema")
    masks = profile.get("authority_masks")
    if not isinstance(masks, list) or not masks:
        raise ValueError("authority_masks must be a nonempty array")
    seen: set[str] = set()
    roles = semantic_rig.get("roles")
    if not isinstance(roles, dict):
        raise ValueError("semantic rig roles must be an object")
    for mask in masks:
        semantic = mask.get("semantic")
        if not isinstance(semantic, str) or semantic in seen:
            raise ValueError("authority mask semantics must be unique strings")
        nodes = semantic_nodes(roles, semantic)
        weights = mask.get("chain_weights")
        if not isinstance(weights, list) or len(weights) != len(nodes):
            raise ValueError(f"semantic {semantic!r} chain weight count mismatch")
        if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 1.0 for value in weights):
            raise ValueError(f"semantic {semantic!r} has invalid chain weight")
        seen.add(semantic)


def build_overlay(
    *, repository: Path, profile_path: Path, output: Path,
    strength: float, variant: str
) -> dict[str, Any]:
    profile_bytes = profile_path.read_bytes()
    profile = json.loads(profile_bytes)
    source_info = profile["source"]
    semantic_info = profile["semantic_rig"]
    source_path = repository / source_info["path"]
    semantic_path = repository / semantic_info["path"]
    source_raw = source_path.read_bytes()
    semantic_bytes = semantic_path.read_bytes()
    if sha256(source_raw) != source_info["sha256"]:
        raise ValueError("source candidate SHA-256 mismatch")
    if sha256(semantic_bytes) != semantic_info["sha256"]:
        raise ValueError("semantic rig SHA-256 mismatch")
    semantic_rig = json.loads(semantic_bytes)
    validate_profile(profile, semantic_rig)
    parameter = profile["parameter"]
    if not float(parameter["minimum"]) <= strength <= float(parameter["maximum"]):
        raise ValueError("alert strength is outside profile bounds")
    if variant not in {"in_place", "root_motion"}:
        raise ValueError("variant must be in_place or root_motion")

    document, binary = parse_glb(source_raw)
    animation = animation_by_name(document, source_info["clip"])
    _, channels = channel_maps(document, animation)
    roles = semantic_rig["roles"]
    axes = profile["axes_local_xyz"]
    cycle = float(profile["timing"]["cycle_seconds"])
    changed: list[dict[str, Any]] = []
    common_timeline: list[float] | None = None

    for mask in profile["authority_masks"]:
        nodes = semantic_nodes(roles, mask["semantic"])
        for chain_position, (node, raw_weight) in enumerate(zip(nodes, mask["chain_weights"])):
            key = (node, "rotation")
            if key not in channels:
                raise ValueError(f"semantic target {mask['semantic']!r} lacks a rotation channel")
            output_accessor = channels[key]
            channel = next(
                item for item in animation["channels"]
                if document["nodes"][item["target"]["node"]].get("name") == node
                and item["target"]["path"] == "rotation"
            )
            sampler = animation["samplers"][channel["sampler"]]
            if sampler.get("interpolation", "LINEAR") != "LINEAR":
                raise ValueError("overlay requires LINEAR animation samplers")
            times = [value[0] for value in read_accessor(document, binary, int(sampler["input"]))]
            if common_timeline is None:
                common_timeline = times
            elif times != common_timeline:
                raise ValueError("overlay targets must share an exact timeline")
            base = read_accessor(document, binary, output_accessor)
            weight = float(raw_weight)
            overlaid = [
                qnormalize(qmul(tuple(rotation), overlay_quaternion(
                    time=time, cycle=cycle, strength=strength, weight=weight,
                    mask=mask, axes=axes
                )))
                for time, rotation in zip(times, base)
            ]
            for index in range(1, len(overlaid)):
                if sum(a * b for a, b in zip(overlaid[index - 1], overlaid[index])) < 0.0:
                    overlaid[index] = tuple(-value for value in overlaid[index])
            write_accessor(document, binary, output_accessor, overlaid)
            changed.append({
                "semantic": mask["semantic"],
                "chain_position": chain_position,
                "resolved_node": node,
                "weight": weight,
                "accessor": output_accessor,
            })

    if common_timeline is None or len(common_timeline) < 3:
        raise ValueError("overlay has no dense common timeline")
    duration = common_timeline[-1] - common_timeline[0]
    cycles = duration / cycle
    if profile["timing"]["required_integer_cycles"] and abs(cycles - round(cycles)) > 1e-9:
        raise ValueError("overlay cycle does not tile the source duration")

    document = copy.deepcopy(document)
    animation = animation_by_name(document, source_info["clip"])
    animation["name"] = f"alert_idle_overlay_{variant}"
    animation["extras"] = {
        "taskId": TASK_ID,
        "classification": profile["classification"],
        "overlayProfileSha256": sha256(profile_bytes),
        "semanticRigSha256": sha256(semantic_bytes),
        "sourceSha256": sha256(source_raw),
        "alertStrength": strength,
        "stationaryRootFactorization": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = encode_glb(document, binary)
    output.write_bytes(raw)
    try:
        output_label = str(output.relative_to(repository))
    except ValueError:
        output_label = str(output)
    return {
        "task_id": TASK_ID,
        "classification": profile["classification"],
        "variant": variant,
        "source": {"path": source_info["path"], "sha256": sha256(source_raw)},
        "profile": {"path": str(profile_path.relative_to(repository)), "sha256": sha256(profile_bytes)},
        "semantic_rig": {"path": semantic_info["path"], "sha256": sha256(semantic_bytes)},
        "output": {"path": output_label, "sha256": sha256(raw), "bytes": len(raw)},
        "clip": animation["name"],
        "alert_strength": strength,
        "duration_seconds": duration,
        "sample_count": len(common_timeline),
        "cycle_seconds": cycle,
        "cycle_count": round(cycles),
        "changed_roles": changed,
        "untouched_contract": "all channels outside resolved semantic rotation authority masks",
        "root_motion": "unchanged stationary source root translation and rotation",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("in_place", "root_motion"), required=True)
    parser.add_argument("--alert-strength", type=float)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve()
    profile_path = (repository / args.profile).resolve()
    profile = load_json(profile_path)
    strength = float(profile["parameter"]["default"] if args.alert_strength is None else args.alert_strength)
    receipt = build_overlay(
        repository=repository,
        profile_path=profile_path,
        output=(repository / args.output).resolve(),
        strength=strength,
        variant=args.variant,
    )
    if args.receipt:
        receipt_path = (repository / args.receipt).resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
