#!/usr/bin/env python3
"""Bounded Candidate-A chest solve in the frozen official measurement basis.

The only driver is the existing iteration-b pelvis world-roll signal. For each
exported key, the chest's official relative rotation-vector is edited directly:

    log(R_chest R_pelvis^-1)_target =
      log(R_chest R_pelvis^-1)_iteration_b + [0, 0, -gain * pelvis_roll_z]

Thus the official chest pitch/yaw samples are preserved by construction. A
root-to-tip neck reconstruction carries the resulting chest world delta to
zero at the head, preserving iteration-b head world motion. Pelvis, legs,
tail, and all other channels stay byte-identical. Variants are written only to
a temporary directory for measurement; this script never changes a candidate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EVALUATOR_PATH = ROOT / "reports/V8-2-BALANCE-TRANSFER/evaluation/tools/evaluate_balance.py"
GENERATOR_PATH = ROOT / "candidates/v8.2-balance-transfer/scripts/generate_balance_overlay.py"
CLIPS = ("PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION", "PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE")
CHEST = "Bone_002"
NECK_HEAD = ("Bone_041", "Bone_040", "Bone_039", "Bone_038", "Bone_037", "Bone_036")
# Cumulative cancellation fractions.  The head value of 1 makes head world
# exactly iteration-b's; intermediate values limit any one neck-local delta.
CANCEL_FRACTIONS = (.11, .26, .45, .69, 1.0, 1.0)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ev = load_module("official_balance_evaluator", EVALUATOR_PATH)
gen = load_module("balance_overlay_generator", GENERATOR_PATH)


def q_power(quaternion: np.ndarray, fraction: float) -> np.ndarray:
    """Shortest-path quaternion power using the generator's rotation-vector basis."""
    return gen.q_from_rotvec(gen.q_to_rotvec(quaternion) * fraction)


def native_local_samples(glb, rotations: dict[str, np.ndarray], sample: int) -> list[np.ndarray]:
    return [rotations.get(node.get("name", f"node_{index}"), np.asarray([glb.rest_rotation[index]]))[sample if node.get("name", f"node_{index}") in rotations else 0] for index, node in enumerate(glb.nodes)]


def target_tracks(glb, clip: str, gain: float) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    times, rotations = glb.tracks(clip)
    for name in (CHEST, *NECK_HEAD):
        if name not in rotations:
            raise ValueError(f"{clip} missing {name}")
    output = {name: np.empty_like(rotations[name], dtype=np.float64) for name in (CHEST, *NECK_HEAD)}
    max_local_delta = {name: 0.0 for name in output}
    pelvis = glb.name_to_node["Bone_001"]
    chest = glb.name_to_node[CHEST]
    reference_pelvis = None
    for sample in range(len(times)):
        base_local = native_local_samples(glb, rotations, sample)
        base_world = gen.all_worlds(glb, base_local)
        if reference_pelvis is None:
            reference_pelvis = base_world[pelvis]
        # Exact official signal: current pelvis world against phase-zero world,
        # expressed as a world-basis rotvec. The Z component is fore-aft roll.
        pelvis_roll = gen.q_to_rotvec(gen.q_mul(base_world[pelvis], gen.q_inv(reference_pelvis)))[2]
        relative = gen.q_mul(base_world[chest], gen.q_inv(base_world[pelvis]))
        relative_target = gen.q_from_rotvec(gen.q_to_rotvec(relative) + np.asarray([0.0, 0.0, -gain * pelvis_roll]))
        chest_world_target = gen.q_mul(relative_target, base_world[pelvis])
        chest_delta = gen.q_mul(chest_world_target, gen.q_inv(base_world[chest]))
        target_world = list(base_world)
        parent = glb.parents[chest]
        output[CHEST][sample] = chest_world_target if parent is None else gen.q_mul(gen.q_inv(target_world[int(parent)]), chest_world_target)
        target_world[chest] = chest_world_target
        for name, fraction in zip(NECK_HEAD, CANCEL_FRACTIONS):
            index = glb.name_to_node[name]
            desired_world = gen.q_mul(q_power(chest_delta, 1.0 - fraction), base_world[index])
            parent = glb.parents[index]
            output[name][sample] = desired_world if parent is None else gen.q_mul(gen.q_inv(target_world[int(parent)]), desired_world)
            target_world[index] = desired_world
        for name, values in output.items():
            index = glb.name_to_node[name]
            delta = gen.q_mul(gen.q_inv(base_local[index]), values[sample])
            max_local_delta[name] = max(max_local_delta[name], float(np.degrees(np.linalg.norm(gen.q_to_rotvec(delta)))))
    for values in output.values():
        for sample in range(1, len(values)):
            if float(np.dot(values[sample - 1], values[sample])) < 0.0:
                values[sample] *= -1.0
        values[-1] = values[0]
    return output, max_local_delta


def write_variant(source: Path, destination: Path, gain: float) -> dict[str, float]:
    glb = gen.Glb(source)
    raw = bytearray(glb.raw)
    all_deltas: dict[str, float] = {}
    for clip in CLIPS:
        tracks, deltas = target_tracks(glb, clip, gain)
        for name, values in tracks.items():
            accessor = glb.rotation_accessors(clip)[name]
            offset, count = glb.accessor_offset(accessor)
            if values.shape != (count, 4):
                raise ValueError(f"unexpected shape for {clip}/{name}: {values.shape} != {(count, 4)}")
            raw[glb.bin_start + offset:glb.bin_start + offset + count * 16] = values.astype("<f4").tobytes(order="C")
            all_deltas[name] = max(all_deltas.get(name, 0.0), deltas[name])
    destination.write_bytes(raw)
    return all_deltas


def local_bounds_pass(deltas: dict[str, float]) -> bool:
    return deltas[CHEST] <= 1.0 and all(deltas[name] <= .75 for name in NECK_HEAD[:-1]) and deltas[NECK_HEAD[-1]] <= 1.0


def summarize(metrics: dict, approved: dict, deltas: dict[str, float]) -> dict:
    gate = ev.candidate_a_upper_only_gate(metrics, approved)
    return {
        "gate": gate,
        "local_delta_degrees": deltas,
        "local_bounds_pass": local_bounds_pass(deltas),
        "chest": metrics["chest_relative_to_pelvis_peak_to_peak_degrees"],
        "head": metrics["head_world_rotation_peak_to_peak_degrees"],
        "counterphase": metrics["counterphase_zero_lag_pearson"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path, help="iteration-b GLB; only read")
    parser.add_argument("--approved", required=True, type=Path, help="frozen V8.1 GLB")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target-roll", type=float, default=5.75)
    parser.add_argument("--gain-min", type=float, default=0.0)
    parser.add_argument("--gain-max", type=float, default=1.5)
    parser.add_argument("--iterations", type=int, default=18)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)


def main() -> int:
    args = parse_args()
    approved = ev.analyze(args.approved, CLIPS[1])
    history = []
    with tempfile.TemporaryDirectory(prefix="eonwild-chest-solve-") as directory:
        temp = Path(directory) / "candidate.glb"
        def evaluate(gain: float) -> dict:
            deltas = write_variant(args.candidate, temp, gain)
            metrics = ev.analyze(temp, CLIPS[1])
            return {"gain": gain, **summarize(metrics, approved, deltas)}
        low, high = args.gain_min, args.gain_max
        low_row, high_row = evaluate(low), evaluate(high)
        history.extend((low_row, high_row))
        if low_row["chest"]["roll_z"] > args.target_roll or high_row["chest"]["roll_z"] < args.target_roll:
            raise RuntimeError("target roll not bracketed by requested gain interval")
        for _ in range(args.iterations):
            mid = (low + high) * .5
            row = evaluate(mid)
            history.append(row)
            if row["chest"]["roll_z"] < args.target_roll:
                low = mid
            else:
                high = mid
        best = min(history, key=lambda row: abs(row["chest"]["roll_z"] - args.target_roll))
    result = {
        "schema": "eonwild.v8_2.candidate_a_chest_solve.v1",
        "status": "PASS" if best["gate"]["status"] == "PASS" and best["local_bounds_pass"] else "FAIL",
        "inputs": {"candidate": str(args.candidate), "candidate_sha256": ev.sha256(args.candidate), "approved": str(args.approved), "approved_sha256": ev.sha256(args.approved)},
        "method": {"target_roll_degrees": args.target_roll, "gain_driver": "negative existing official pelvis world-roll Z signal", "relative_parameterization": "per-key log(R_chest R_pelvis^-1) + [0,0,-gain*pelvis_roll_z]", "head_rule": "root-to-tip neck reconstruction exactly cancels the chest world delta at Bone_036", "channels_changed_in_temporary_variants": [CHEST, *NECK_HEAD]},
        "best": best,
        "search": history,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "gain": best["gain"], "gate": best["gate"]["status"], "chest": best["chest"], "head": best["head"], "local_delta_degrees": best["local_delta_degrees"]}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
