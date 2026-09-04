#!/usr/bin/env python3
"""Measure every baked power-attack key directly from the final V8.1 GLB."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(HERE))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator
from eonproc_v8.profile import BipedV8Profile

TRUE_FLIGHT_CLEARANCE_M = 0.010
PENETRATION_TOLERANCE_M = 1e-5


def crossing_time(times: np.ndarray, heights: np.ndarray, left: int, right: int) -> float:
    h0 = float(heights[left])
    h1 = float(heights[right])
    if abs(h1 - h0) < 1e-12:
        return float(times[right])
    alpha = float(np.clip((TRUE_FLIGHT_CLEARANCE_M - h0) / (h1 - h0), 0.0, 1.0))
    return float(times[left] + (times[right] - times[left]) * alpha)


def contiguous_true_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(mask.tolist()):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(mask) - 1):
            end = index if value and index == len(mask) - 1 else index - 1
            runs.append((start, end))
            start = None
    return runs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--glb", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    asset = GlbAsset(args.glb)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV8Profile.from_json(args.profile)
    generator = TarbosaurusV8LocomotionGenerator(asset, semantics, profile)
    reader = AnimationPackReader(asset)
    primitive = asset.primitive()
    ground = float(primitive.positions[:, 1].min())
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    power: dict[str, dict] = {}

    for name, lead in (
        ("PROC_POWER_ATTACK_V8_1", "l"),
        ("PROC_POWER_ATTACK_MIRRORED_V8_1", "r"),
    ):
        animation = reader.animation(name)
        times = np.asarray(animation.times, dtype=np.float64)
        measurements: list[dict] = []
        heights_by_side = {"l": [], "r": []}
        for key_index, time_seconds in enumerate(times):
            worlds = reader.world_matrices_at(animation, float(time_seconds))
            row = {
                "keyIndex": key_index,
                "timeSeconds": float(time_seconds),
                "phase": float(time_seconds / animation.duration),
            }
            for side in ("l", "r"):
                indices = generator.sole.selections[side].vertex_indices
                points = asset.skin_points(
                    primitive.positions[indices], primitive.joints[indices],
                    primitive.weights[indices], worlds, skin,
                )
                height = float(points[:, 1].min() - ground)
                heights_by_side[side].append(height)
                row[side] = {
                    "minimumHeightM": height,
                    "penetrationM": float(max(0.0, -height)),
                }
            measurements.append(row)

        left = np.asarray(heights_by_side["l"])
        right = np.asarray(heights_by_side["r"])
        both = np.minimum(left, right)
        runs = contiguous_true_runs(both >= TRUE_FLIGHT_CLEARANCE_M)
        apex_index = int(np.argmax(both))
        containing_apex = [run for run in runs if run[0] <= apex_index <= run[1]]
        if len(containing_apex) != 1:
            raise RuntimeError(f"{name}: expected one clear interval containing baked apex")
        start_index, end_index = containing_apex[0]
        if start_index == 0 or end_index == len(times) - 1:
            raise RuntimeError(f"{name}: true-flight interval is not bounded by contact keys")
        takeoff_seconds = crossing_time(times, both, start_index - 1, start_index)
        landing_seconds = crossing_time(times, both, end_index, end_index + 1)
        lead_values = left if lead == "l" else right
        trailing_values = right if lead == "l" else left
        lead_landing_index = next(
            index for index in range(end_index + 1, len(times))
            if lead_values[index] < TRUE_FLIGHT_CLEARANCE_M
        )
        trailing_catch_index = next(
            index for index in range(lead_landing_index, len(times))
            if trailing_values[index] < TRUE_FLIGHT_CLEARANCE_M
        )
        power[name] = {
            "leadSide": lead,
            "exportedKeyCount": len(times),
            "measuredKeyCount": len(measurements),
            "trueFlightClearanceThresholdM": TRUE_FLIGHT_CLEARANCE_M,
            "trueFlightStartKey": start_index,
            "trueFlightEndKey": end_index,
            "measuredTakeoffSeconds": takeoff_seconds,
            "measuredLandingSeconds": landing_seconds,
            "measuredAirborneDurationSeconds": landing_seconds - takeoff_seconds,
            "minimumBakedKeyClearanceDuringFlightM": float(both[start_index:end_index + 1].min()),
            "maximumBakedBothSolesClearanceM": float(both[apex_index]),
            "bakedApexKey": apex_index,
            "bakedApexSeconds": float(times[apex_index]),
            "worstPenetrationAcrossAllKeysM": float(max(0.0, -min(left.min(), right.min()))),
            "leadLandingKey": lead_landing_index,
            "leadLandingSeconds": float(times[lead_landing_index]),
            "leadLandingHeightM": float(lead_values[lead_landing_index]),
            "trailingHeightAtLeadLandingM": float(trailing_values[lead_landing_index]),
            "trailingCatchKey": trailing_catch_index,
            "trailingCatchSeconds": float(times[trailing_catch_index]),
            "maximumHeightAtCatchM": float(max(left[trailing_catch_index], right[trailing_catch_index])),
            "keyMeasurements": measurements,
        }

    checks = {
        "all_exported_baked_keys_measured": all(
            value["exportedKeyCount"] == 169
            and value["measuredKeyCount"] == value["exportedKeyCount"]
            for value in power.values()
        ),
        "measured_true_flight_interval_source_bounded": all(
            0.17 <= value["measuredAirborneDurationSeconds"] <= 0.21
            for value in power.values()
        ),
        "baked_apex_clearance_in_authored_range": all(
            value["maximumBakedBothSolesClearanceM"]
            >= profile.power_sole_clearance_hip_fraction * generator.hip_height
            for value in power.values()
        ),
        "no_penetration_across_any_baked_key": all(
            value["worstPenetrationAcrossAllKeysM"] <= PENETRATION_TOLERANCE_M
            for value in power.values()
        ),
        "lead_lands_before_trailing": all(
            value["leadLandingSeconds"] < value["trailingCatchSeconds"]
            and value["leadLandingHeightM"] < value["trailingHeightAtLeadLandingM"]
            for value in power.values()
        ),
        "both_feet_caught_by_second_contact": all(
            value["maximumHeightAtCatchM"] <= generator.hip_height * 0.012
            for value in power.values()
        ),
    }
    out = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "method": "all exported baked animation keys; sole vertices skinned from final GLB",
        "checks": checks,
        "meshGroundM": ground,
        "hipHeightM": generator.hip_height,
        "power": power,
    }
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
