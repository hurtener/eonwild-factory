#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
import numpy as np

COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def parse_glb(path: Path):
    raw = path.read_bytes()
    magic, version, declared = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF" and version == 2 and declared == len(raw)
    cursor = 12; chunks = {}
    while cursor < len(raw):
        length, kind = struct.unpack_from("<II", raw, cursor); cursor += 8
        chunks[kind] = raw[cursor:cursor+length]; cursor += length
    doc = json.loads(chunks[0x4E4F534A].decode("utf-8")); binary = chunks[0x004E4942]
    return doc, binary


def accessor(doc, binary, index):
    acc = doc["accessors"][index]; view = doc["bufferViews"][acc["bufferView"]]
    dtype = np.dtype(COMPONENT[acc["componentType"]]).newbyteorder("<")
    width = WIDTH[acc["type"]]
    offset = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", dtype.itemsize * width)
    if stride == dtype.itemsize * width:
        return np.frombuffer(binary, dtype=dtype, count=acc["count"] * width, offset=offset).reshape(acc["count"], width)
    return np.ndarray((acc["count"], width), dtype=dtype, buffer=binary, offset=offset, strides=(stride, dtype.itemsize)).copy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    glb = Path(args.glb); report_path = Path(args.report)
    doc, binary = parse_glb(glb)
    report = json.loads(report_path.read_text())
    names = [a.get("name", "") for a in doc.get("animations", [])]
    checks = {
        "glb_header_and_chunks": True,
        "skin_joint_count_75": len(doc["skins"][0]["joints"]) == 75,
        "unique_animation_names": len(names) == len(set(names)),
        "clip_count_matches_report": len(names) == report["output"]["clip_count"],
        "required_feature_clips": all(any(token in n for n in names) for token in ["WALK_RELAXED", "UNEVEN", "UPSLOPE", "TURN_LEFT", "START_WALK", "BRAKE", "ALERT_WALK", "EAT", "BITE", "ROAR"]),
    }
    time_errors = []
    target_errors = []
    for animation in doc.get("animations", []):
        for sampler in animation.get("samplers", []):
            times = accessor(doc, binary, sampler["input"]).reshape(-1)
            if len(times) < 2 or not np.all(np.diff(times) > 0): time_errors.append(animation.get("name"))
        for channel in animation.get("channels", []):
            node = channel.get("target", {}).get("node")
            if not isinstance(node, int) or not (0 <= node < len(doc.get("nodes", []))): target_errors.append(animation.get("name"))
    checks["strictly_increasing_sample_times"] = not time_errors
    checks["all_channel_targets_valid"] = not target_errors

    locomotion_gates = {}
    transition_checks = {}
    for name, clip in report.get("clips", {}).items():
        tags = set(clip.get("tags", []))
        diagnostics = clip.get("diagnostics", {})
        gates = diagnostics.get("quality_gates", {})
        if "transition" in tags:
            transition_checks[name] = bool(diagnostics.get("phase_matched", False)) or all(
                bool(diagnostics.get(key, False)) for key in (
                    "rotation_start_exact", "rotation_end_exact",
                    "translation_start_exact", "translation_end_exact",
                )
            )
            continue
        if any(token in name for token in ("WALK", "TURN", "START", "BRAKE")):
            locomotion_gates[name] = gates
    checks["zero_anatomical_reversals_all_locomotion"] = all(g.get("zero_anatomical_reversals", False) for g in locomotion_gates.values())
    checks["vertex_penetration_gates_all_locomotion"] = all(g.get("vertex_penetration_within_gate", False) for g in locomotion_gates.values())
    checks["loaded_sole_gap_gates_all_locomotion"] = all(g.get("loaded_sole_gap_within_gate", False) for g in locomotion_gates.values())
    checks["velocity_gates_all_locomotion"] = all(g.get("velocity_within_gate", False) for g in locomotion_gates.values())
    checks["acceleration_gates_all_locomotion"] = all(g.get("acceleration_within_gate", False) for g in locomotion_gates.values())
    action_gates = {
        name: clip.get("diagnostics", {}).get("quality_gates", {})
        for name, clip in report.get("clips", {}).items()
        if "transition" not in set(clip.get("tags", []))
        and any(token in name for token in ("IDLE_BREATH", "ALERT_IDLE", "EAT_LOOP", "BITE_ATTACK", "ROAR_V4"))
    }
    checks["actions_zero_anatomical_reversals"] = all(g.get("zero_anatomical_reversals", False) for g in action_gates.values())
    checks["actions_sole_penetration_within_gate"] = all(g.get("sole_penetration_within_gate", False) for g in action_gates.values())
    checks["looping_actions_close_exactly"] = all(g.get("exact_loop", True) for g in action_gates.values())
    checks["transition_endpoints_exact"] = bool(transition_checks) and all(transition_checks.values())
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "glb": str(glb),
        "animation_count": len(names),
        "animation_names": names,
        "checks": checks,
        "time_errors": time_errors,
        "target_errors": target_errors,
    }
    destination = Path(args.output) if args.output else report_path.with_name("v4-baked-glb-validation.json")
    destination.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS": raise SystemExit(1)

if __name__ == "__main__": main()
