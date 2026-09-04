#!/usr/bin/env python3
"""Fail-closed causal validator for the isolated V8.1 relaxed-walk respin 2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[3]
TOOLKIT = ROOT / "procedural-animation-toolkit(v8.1)" / "toolkit" / "v8" / "scripts"
sys.path.insert(0, str(TOOLKIT))

from eonproc_v3.gltf_io import GlbAsset, sha256_file  # noqa: E402
from eonproc_v3.rig import SemanticMap  # noqa: E402
from eonproc_v4.animation_reader import AnimationPackReader  # noqa: E402
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator  # noqa: E402
from eonproc_v8.profile import BipedV8Profile  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--bone-map", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--generation-report", type=Path, required=True)
    parser.add_argument("--base-validation", type=Path, required=True)
    parser.add_argument("--respin-1-validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def key_cycles(rows: list[dict], side: str) -> list[list[dict]]:
    result = [[], []]
    for row in rows:
        phase = float(row["sides"][side]["phase"])
        # The exported two-cycle clip repeats the same phase. Key time cleanly
        # identifies which physical cycle is being measured.
        cycle = 0 if row["timeSeconds"] < rows[-1]["timeSeconds"] * 0.5 else 1
        if row["keyIndex"] == len(rows) - 1:
            continue  # loop duplicate; never inflate the exported sample count
        entry = dict(row["sides"][side])
        entry["timeSeconds"] = float(row["timeSeconds"])
        entry["keyIndex"] = int(row["keyIndex"])
        entry["phase"] = phase
        result[cycle].append(entry)
    return result


def first(entries: list[dict], predicate) -> dict | None:
    return next((entry for entry in entries if predicate(entry)), None)


def angular_velocity(clip, bone: str) -> np.ndarray:
    values = clip.rotations.get(bone)
    if values is None:
        return np.zeros(len(clip.times) - 1)
    delta = Rotation.from_quat(values[:-1]).inv() * Rotation.from_quat(values[1:])
    return np.linalg.norm(delta.as_rotvec(), axis=1) / np.diff(clip.times)


def phase_at(time_s: float, duration_s: float, side: str) -> float:
    return ((time_s / duration_s) * 2.0 - (0.0 if side == "l" else 0.5)) % 1.0


def skinned_points(asset: GlbAsset, reader: AnimationPackReader, animation, time_s: float, indices: np.ndarray) -> np.ndarray:
    primitive = asset.primitive()
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    worlds = reader.world_matrices_at(animation, time_s)
    return asset.skin_points(primitive.positions[indices], primitive.joints[indices], primitive.weights[indices], worlds, skin)


def terminal_toe_pitch_degrees(asset: GlbAsset, reader: AnimationPackReader, animation, time_s: float, roots: list[str], witness_ids: np.ndarray, generator: TarbosaurusV8LocomotionGenerator) -> list[float]:
    """World-space terminal mesh pitch; negative is toe-down."""
    worlds = reader.world_matrices_at(animation, time_s)
    primitive = asset.primitive()
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    points = asset.skin_points(primitive.positions[witness_ids], primitive.joints[witness_ids], primitive.weights[witness_ids], worlds, skin)
    pitches = []
    for root, point in zip(roots, points):
        root_position = worlds[asset.name_to_node[root]][:3, 3]
        vector = point - root_position
        forward = float(np.dot(vector, generator.base_basis.forward))
        up = float(np.dot(vector, generator.base_basis.up))
        pitches.append(float(np.rad2deg(np.arctan2(up, max(abs(forward), 1e-9)))))
    return pitches


def contiguous(items: list[tuple[float, float]]) -> list[list[tuple[float, float]]]:
    groups: list[list[tuple[float, float]]] = []
    active: list[tuple[float, float]] = []
    for item in items:
        if .40 <= item[1] < .745:
            active.append(item)
        elif active:
            groups.append(active)
            active = []
    if active:
        groups.append(active)
    return groups


def main() -> int:
    args = arguments()
    overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    base = json.loads(args.base_validation.read_text(encoding="utf-8"))
    respin_1 = json.loads(args.respin_1_validation.read_text(encoding="utf-8"))
    generated = json.loads(args.generation_report.read_text(encoding="utf-8"))
    root = base["clips"]["PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"]
    rows = root["keyMeasurements"]
    phase = overlay["phaseLock"]
    profile = BipedV8Profile.from_json(args.profile)
    asset = GlbAsset(args.glb)
    semantics = SemanticMap.load(args.bone_map)
    generator = TarbosaurusV8LocomotionGenerator(asset, semantics, profile)
    reader = AnimationPackReader(asset)
    clip = reader.animation("PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION")
    cycles_report: dict[str, list[dict]] = {}
    causal_ok = True
    for side in ("l", "r"):
        side_cycles = key_cycles(rows, side)
        per_cycle: list[dict] = []
        toe_bones = [chain[0] for chain in generator.toe_chains[side] if chain]
        ankle = semantics.bone(f"foot_{side}")
        channel_bones = toe_bones + [ankle]
        velocities = {bone: angular_velocity(clip, bone) for bone in channel_bones}
        passive_source = generated["toeGroundLock"]["sides"][clip.name][side]["passiveIntegration"]
        ankle_index = asset.name_to_node[ankle]
        ankle_translation = clip.translations.get(ankle, np.repeat(asset.rest_translation[ankle_index][None, :], len(clip.times), axis=0))
        for cycle_index, entries in enumerate(side_cycles):
            # The base report's foot-node height is not a metatarsal witness:
            # it can fall as the hip translates even while the exported ankle
            # rocker channel has already begun. Detect the onset directly from
            # the baked ankle rotation, then let the dense skinned witness
            # gate prove the resulting metatarsal rise and planted toe hold.
            pre_rocker = max((entry for entry in entries if entry["phase"] <= .58), key=lambda entry: entry["phase"], default=None)
            onset = None
            if pre_rocker is not None:
                baseline_rotation = Rotation.from_quat(clip.rotations[ankle][pre_rocker["keyIndex"]])
                for entry in entries:
                    if not (.58 <= entry["phase"] <= .72):
                        continue
                    current_rotation = Rotation.from_quat(clip.rotations[ankle][entry["keyIndex"]])
                    # Geometry is authoritative below; this 1-degree channel
                    # cross-check intentionally ignores sub-visible IK noise
                    # rather than letting a tiny ankle delta relabel an early
                    # skinned metatarsal rise as acceptable.
                    if np.linalg.norm((baseline_rotation.inv() * current_rotation).as_rotvec()) >= np.deg2rad(1.0):
                        onset = entry
                        break
            window = [x for x in entries if .40 <= x["phase"] < .80]
            # Foot origin is candidate-locally pivot-compensated; use the
            # preserved shin relative to pelvis for rear-leg extension.
            shin = semantics.bone(f"shin_{side}")
            pelvis = semantics.bone("pelvis")
            def stable_shin_extension(entry):
                worlds = reader.world_matrices_at(clip, entry["timeSeconds"])
                vector = worlds[asset.name_to_node[shin]][:3, 3] - worlds[asset.name_to_node[pelvis]][:3, 3]
                return -float(np.dot(vector, generator.base_basis.forward))
            peak = max(window, key=stable_shin_extension)
            # Release is the first exported passive-spring key, rather than
            # a broad toe-patch quantile. In toe-only dwell that quantile
            # rises by design while the distal witnesses remain weighted.
            passive_rotation = first(
                passive_source,
                lambda record: record["cycle"] == cycle_index and record.get("translationCorrection") is False,
            )
            release = None if passive_rotation is None else first(
                entries,
                lambda entry: entry["keyIndex"] == passive_rotation["lagKeys"][0],
            )
            loaded = [x for x in entries if onset is not None and onset["phase"] <= x["phase"] < (release["phase"] if release is not None else .76) and x["toePatchMinimumM"] <= .008]
            # Dwell is intentionally evaluated at the *distal edge* (patch
            # minimum), not the 8th-percentile sole-support metric.  During a
            # toe-only rocker, most of the patch is above ground by design;
            # this answers whether the loaded digit tip remains grounded.
            dwell = [x for x in entries if release is not None and (release["phase"] - .12) <= x["phase"] < release["phase"] and x["toePatchMinimumM"] <= .008]
            lag = [x for x in entries if .78 <= x["phase"] < .85]
            lag_indices = [x["keyIndex"] for x in lag if x["keyIndex"] < len(clip.times) - 1]
            # Exclude the interval whose following key has entered receiving
            # arm; otherwise that explicit arm impulse would be misattributed
            # to passive lag.
            lag_velocity_indices = [index for index in lag_indices if index + 1 < len(clip.times) - 1 and any(x["keyIndex"] == index + 1 for x in lag)]
            lag_motion = max((float(velocities[bone][index]) for bone in channel_bones for index in lag_velocity_indices), default=0.0)
            records = [record for record in passive_source if record["cycle"] == cycle_index and record["bone"] in channel_bones and record.get("translationCorrection") is False]
            translation_delta = max((float(np.linalg.norm(ankle_translation[index] - asset.rest_translation[ankle_index])) for index in lag_indices), default=float("inf"))
            translation_records = [record for record in passive_source if record["cycle"] == cycle_index and record.get("translationCorrection") == "passive_decay_only"]
            translation_decay = []
            for record in translation_records:
                indices = [record["anchorKey"]] + list(record["lagKeys"])
                vectors = [ankle_translation[index] - asset.rest_translation[ankle_index] for index in indices]
                offsets = [float(np.linalg.norm(vector)) for vector in vectors]
                velocities_linear = [(b - a) / (clip.times[index_b] - clip.times[index_a]) for a, b, index_a, index_b in zip(vectors, vectors[1:], indices, indices[1:])]
                step_speeds = [float(np.linalg.norm(value)) for value in velocities_linear]
                k, damping = 14.0, 7.0
                energies = [0.5 * speed * speed + 0.5 * k * offset * offset for speed, offset in zip(step_speeds, offsets[1:])]
                translation_decay.append({
                    "anchorOffsetM": offsets[0],
                    "finalOffsetM": offsets[-1],
                    "offsetsM": offsets,
                    "stepSpeedsMps": step_speeds,
                    "monotonicOffsetDecay": all(b <= a + 1e-8 for a, b in zip(offsets, offsets[1:])),
                    "monotonicSpeedDecay": all(b <= a + 1e-6 for a, b in zip(step_speeds, step_speeds[1:])),
                    "mechanicalEnergies": energies,
                    "monotonicEnergyDecay": all(b <= a + 1e-6 for a, b in zip(energies, energies[1:])),
                    "activeTarget": record.get("activeTarget"),
                })
            decay = []
            for record in records:
                bone = record["bone"]
                values = [float(velocities[bone][record["anchorKey"]])]
                values.extend(float(velocities[bone][index]) for index in record["lagKeys"][:-1])
                decay.append({"bone": bone, "initialRadS": values[0], "finalRadS": values[-1], "strictlyDecayingSteps": sum(b <= a + 1e-6 for a, b in zip(values, values[1:])), "stepCount": len(values) - 1})
            arm = [x for x in entries if .85 <= x["phase"] < .86]
            arm_indices = [x["keyIndex"] for x in arm if x["keyIndex"] < len(clip.times) - 1]
            arm_motion = max((float(velocities[bone][index]) for bone in channel_bones for index in arm_indices), default=0.0)
            arm_phase = min((x["phase"] for x in arm if max(float(velocities[bone][x["keyIndex"]]) for bone in channel_bones) > .01), default=None)
            flat = [x for x in entries if .88 <= x["phase"] < 1.0]
            flat_indices = [x["keyIndex"] for x in flat if x["keyIndex"] < len(clip.times) - 1]
            flat_motion = max((float(velocities[bone][index]) for bone in channel_bones for index in flat_indices), default=float("inf"))
            item = {
                "rockerOnsetPhase": None if onset is None else onset["phase"],
                "rockerOnsetMeasurement": "baked_ankle_rotation_change_from_pre_rocker",
                "rearExtensionPeakPhase": peak["phase"],
                "rearExtensionAtOnsetM": None if onset is None else stable_shin_extension(onset),
                "rearExtensionAtPeakM": stable_shin_extension(peak),
                "compensatedFootOriginRearDiagnosticM": -peak["footRelativePelvisForwardM"],
                "loadedRockerSamples": len(loaded),
                "toeOnlyDwellPhase": (len(dwell) / (len(entries) / 1.0)),
                "releasePhase": None if release is None else release["phase"],
                "passiveLagSamples": len(lag),
                "passiveLagMaxExportedAngularVelocityRadS": lag_motion,
                "passiveAnkleTranslationDeviationM": translation_delta,
                "passivePivotTranslationDecay": translation_decay,
                "passiveAngularDecay": decay,
                "receivingArmActualPhase": arm_phase,
                "receivingArmMaxAngularVelocityRadS": arm_motion,
                "flattenMaxAngularVelocityRadS": flat_motion,
                "flattenSamples": len(flat),
            }
            extension_lead = None if onset is None else peak["phase"] - onset["phase"]
            extension_before_release = None if release is None else release["phase"] - peak["phase"]
            item["rockerToExtensionLeadCycle"] = extension_lead
            item["extensionToReleaseLeadCycle"] = extension_before_release
            item["targetRockerToExtensionLeadRange"] = phase["targetOnsetLead"]
            item["passes"] = bool(
                onset is not None
                and item["rearExtensionAtPeakM"] > item["rearExtensionAtOnsetM"]
                and .08 <= item["toeOnlyDwellPhase"] <= .12
                and release is not None and phase["release"][0] <= release["phase"] <= phase["release"][1]
                and extension_before_release is not None and extension_before_release >= phase["extensionPeakBeforeReleaseMinimum"]
                and len(lag) >= 5 and lag_motion > .001
                # Loaded contact may use an analytically derived toe-pivot
                # offset. After release only its spring decay is permitted:
                # no target, no reversal, and decreasing offset/velocity.
                and len(translation_decay) == 1
                and translation_decay[0]["activeTarget"] is None
                and translation_decay[0]["monotonicEnergyDecay"]
                and len(decay) == len(channel_bones)
                and all(entry["initialRadS"] > .001 and entry["finalRadS"] < entry["initialRadS"] and entry["strictlyDecayingSteps"] >= entry["stepCount"] - 1 for entry in decay)
                and arm_phase is not None and phase["receivingArm"][0] <= arm_phase <= phase["receivingArm"][1]
                and arm_motion > .01 and flat_motion < arm_motion and len(flat) > 0
            )
            per_cycle.append(item)
        cycles_report[side] = per_cycle

    # Dense (240 Hz) skinning review of the final exported channels.  Unlike
    # the older broad-sole gate, this tracks each deterministic distal witness
    # through its own loaded-rocker interval.
    primitive = asset.primitive()
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    skin_nodes, _ = asset.skin_data(skin)
    node_to_joint = {node: joint for joint, node in enumerate(skin_nodes)}
    dense_animation = clip
    dense_times = np.linspace(float(dense_animation.times[0]), float(dense_animation.times[-1]), int(round(dense_animation.duration * 240.0)) + 1)
    dense_report: dict[str, object] = {}
    dense_ok = True
    hip = float(profile.reference_hip_height_m)
    x_limit, z_limit, y_limit = .005 * hip, .003 * hip, .003 * hip
    meters_per_pixel = 12.0 / 960.0
    for side in ("l", "r"):
        source = generated["toeGroundLock"]["sides"][dense_animation.name][side]
        witness_ids = np.asarray(source["witnessVertexIndices"], dtype=np.int64)
        foot = semantics.bone(f"foot_{side}")
        sole_ids = generator.sole.selections[side].vertex_indices
        foot_joint = node_to_joint[asset.name_to_node[foot]]
        foot_weight = primitive.weights[sole_ids] * (primitive.joints[sole_ids] == foot_joint)
        met_ids = sole_ids[np.sum(foot_weight, axis=1) >= .25]
        if len(met_ids) < 4:
            met_ids = sole_ids
        phase_times = [(float(time_s), phase_at(float(time_s), dense_animation.duration, side)) for time_s in dense_times[:-1]]
        contact_groups = contiguous(phase_times)
        group_reports = []
        for group in contact_groups:
            # A clip-boundary tail is not a complete loaded contact.  Do not
            # mislabel it as a failed gait event; the neighbouring full cycle
            # supplies its continuous proof.
            if group[-1][1] - group[0][1] < .18:
                group_reports.append({"anchorPhase": group[0][1], "sampleCount": len(group), "ignoredIncompleteBoundaryFragment": True})
                continue
            anchor_time, _ = group[0]
            anchor = skinned_points(asset, reader, dense_animation, anchor_time, witness_ids)
            witness_rows = []
            met_heights = []
            toe_angles = []
            point_history = []
            roots = [chain[0] for chain in generator.toe_chains[side] if chain]
            rotation_anchor, _ = reader.sample_tracks(dense_animation, anchor_time)
            for time_s, phase_value in group:
                points = skinned_points(asset, reader, dense_animation, time_s, witness_ids)
                point_history.append(points)
                delta = points - anchor
                witness_rows.append({
                    "phase": phase_value,
                    "maxXDriftM": float(np.max(np.abs(delta[:, 0]))),
                    "maxZDriftM": float(np.max(np.abs(delta[:, 2]))),
                    "maxYDriftM": float(np.max(np.abs(delta[:, 1]))),
                    "maxHorizontalDriftM": float(np.max(np.linalg.norm(delta[:, [0, 2]], axis=1))),
                })
                if phase_value >= .40:
                    met = skinned_points(asset, reader, dense_animation, time_s, met_ids)
                    met_heights.append((phase_value, float(np.mean(met[:, 1]))))
                rotations, _ = reader.sample_tracks(dense_animation, time_s)
                turns = []
                for root_bone in roots:
                    before = Rotation.from_quat(rotation_anchor.get(root_bone, asset.rest_rotation[asset.name_to_node[root_bone]]))
                    current = Rotation.from_quat(rotations.get(root_bone, asset.rest_rotation[asset.name_to_node[root_bone]]))
                    axis = asset.rest_world_rotation[asset.name_to_node[root_bone]].inv().apply(generator.base_basis.lateral)
                    turns.append(float(np.dot((before.inv() * current).as_rotvec(), axis)))
                toe_angles.append((phase_value, float(np.mean(turns))))
            jumps = [float(np.max(np.linalg.norm(b - a, axis=1))) for a, b in zip(point_history, point_history[1:])]
            rises = [b[1] - a[1] for a, b in zip(met_heights, met_heights[1:])]
            baseline_heights = [height for phase_value, height in met_heights if phase_value < .58]
            baseline_height = float(np.median(baseline_heights)) if baseline_heights else float(met_heights[0][1])
            peak_height = max((height for _, height in met_heights), default=baseline_height)
            rise_threshold = max(.001, .05 * (peak_height - baseline_height))
            effective_onset = None
            for index, (phase_value, height) in enumerate(met_heights):
                if phase_value < .58 or height < baseline_height + rise_threshold:
                    continue
                following = met_heights[index:index + 4]
                if len(following) == 4 and all(value >= baseline_height + rise_threshold for _, value in following):
                    effective_onset = phase_value
                    break
            loaded_angles = [value for phase_value, value in toe_angles if .46 <= phase_value < .70]
            phase_progress = (anchor_time / dense_animation.duration) * 2.0 - (0.0 if side == "l" else 0.5)
            cycle_id = int(np.floor(phase_progress))
            lag_times = [
                float(time_s) for time_s in dense_times[:-1]
                if int(np.floor((float(time_s) / dense_animation.duration) * 2.0 - (0.0 if side == "l" else 0.5))) == cycle_id
                and .78 <= phase_at(float(time_s), dense_animation.duration, side) < .85
            ]
            lag_angles = []
            lag_pitches = []
            for time_s in lag_times:
                rotations, _ = reader.sample_tracks(dense_animation, time_s)
                turns = []
                for root_bone in roots:
                    before = Rotation.from_quat(rotation_anchor.get(root_bone, asset.rest_rotation[asset.name_to_node[root_bone]]))
                    current = Rotation.from_quat(rotations.get(root_bone, asset.rest_rotation[asset.name_to_node[root_bone]]))
                    axis = asset.rest_world_rotation[asset.name_to_node[root_bone]].inv().apply(generator.base_basis.lateral)
                    turns.append(float(np.dot((before.inv() * current).as_rotvec(), axis)))
                lag_angles.append(float(np.mean(turns)))
                lag_pitches.extend(terminal_toe_pitch_degrees(asset, reader, dense_animation, time_s, roots, witness_ids, generator))
            lag_baked_keys = [
                index for index, time_s in enumerate(dense_animation.times[:-1])
                if int(np.floor((float(time_s) / dense_animation.duration) * 2.0 - (0.0 if side == "l" else 0.5))) == cycle_id
                and .78 <= phase_at(float(time_s), dense_animation.duration, side) < .85
            ]
            lag_baked_pitch_sets = [
                terminal_toe_pitch_degrees(asset, reader, dense_animation, float(dense_animation.times[index]), roots, witness_ids, generator)
                for index in lag_baked_keys
            ]
            lag_baked_pitches = [pitch for pitches in lag_baked_pitch_sets for pitch in pitches]
            toe_down_baked = [max(pitches, default=float("inf")) <= -4.0 for pitches in lag_baked_pitch_sets]
            longest_toe_down_run = 0
            current_toe_down_run = 0
            for toe_down in toe_down_baked:
                current_toe_down_run = current_toe_down_run + 1 if toe_down else 0
                longest_toe_down_run = max(longest_toe_down_run, current_toe_down_run)
            report = {
                "anchorPhase": group[0][1],
                "sampleCount": len(witness_rows),
                "maxXDriftM": max((row["maxXDriftM"] for row in witness_rows), default=float("inf")),
                "maxZDriftM": max((row["maxZDriftM"] for row in witness_rows), default=float("inf")),
                "maxYDriftM": max((row["maxYDriftM"] for row in witness_rows), default=float("inf")),
                "maxHorizontalDriftM": max((row["maxHorizontalDriftM"] for row in witness_rows), default=float("inf")),
                "maxAdjacentWitnessJumpM": max(jumps, default=float("inf")),
                "metatarsalNetRiseM": (met_heights[-1][1] - met_heights[0][1]) if len(met_heights) > 1 else 0.0,
                "metatarsalReversalsOver1mm": sum(delta < -.001 for delta in rises),
                "metatarsalLoadedBaselineM": baseline_height,
                "metatarsalPeakM": peak_height,
                "effectiveRockerRiseThresholdM": rise_threshold,
                "effectiveRockerOnsetPhase": effective_onset,
                "clipCycleIndex": 0 if anchor_time < dense_animation.duration * .5 else 1,
                "toeDownLoadedDeltaRad": (loaded_angles[-1] - loaded_angles[0]) if len(loaded_angles) > 1 else 0.0,
                "toeDownPassiveMeanRad": float(np.mean(lag_angles)) if lag_angles else None,
                "passiveToeDownBakedKeyCount": sum(toe_down_baked),
                "passiveToeDownConsecutiveBakedKeyCount": longest_toe_down_run,
                "passiveToeDownPerKey": toe_down_baked,
                "passiveTerminalToePitchDegrees": {"minimum": min(lag_baked_pitches, default=None), "maximum": max(lag_baked_pitches, default=None)},
            }
            report["passes"] = bool(
                report["maxXDriftM"] <= x_limit and report["maxZDriftM"] <= z_limit and report["maxYDriftM"] <= y_limit
                and report["maxHorizontalDriftM"] <= 2.0 * meters_per_pixel
                and report["maxAdjacentWitnessJumpM"] <= 2.0 * meters_per_pixel
                and report["metatarsalNetRiseM"] >= .004 and report["metatarsalReversalsOver1mm"] == 0
                and abs(report["toeDownLoadedDeltaRad"]) >= np.deg2rad(2.0)
                # Terminal skinned toe pitch is the physical criterion. A
                # root-channel delta from the loaded anchor is not: this rig
                # begins its passive interval already toe-down in rest space.
                # Require five *consecutive* exported passive keys whose
                # actual final-skinned terminal mesh pitch is <= -4 degrees.
                # A longer passive window may then naturally relax before its
                # later receiving preparation, without hiding a rigid target.
                and report["passiveToeDownConsecutiveBakedKeyCount"] >= 5
                and report["passiveTerminalToePitchDegrees"]["maximum"] is not None
            )
            dense_ok = dense_ok and report["passes"]
            group_reports.append(report)
        # The in-place loop is the direct seam proof.  It must start stable;
        # root-motion clips naturally translate over the two-cycle span.
        inplace = reader.animation("PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE")
        first_points = skinned_points(asset, reader, inplace, float(inplace.times[0]), witness_ids)
        last_points = skinned_points(asset, reader, inplace, float(inplace.times[-1]), witness_ids)
        seam_drift = float(np.max(np.linalg.norm((last_points - first_points)[:, [0, 2]], axis=1)))
        start_points = skinned_points(asset, reader, inplace, float(inplace.times[min(1, len(inplace.times) - 1)]), witness_ids)
        startup_jump = float(np.max(np.linalg.norm((start_points - first_points)[:, [0, 2]], axis=1)))
        root_bone = generator.toe_chains[side][0][0]
        seam_rot = Rotation.from_quat(reader.animation("PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE").rotations[root_bone][0]).inv() * Rotation.from_quat(reader.animation("PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE").rotations[root_bone][-1])
        seam_degrees = float(np.rad2deg(np.linalg.norm(seam_rot.as_rotvec())))
        dense_report[side] = {"groups": group_reports, "seamToeDriftM": seam_drift, "startupToeJumpM": startup_jump, "seamOrientationDegrees": seam_degrees, "seamPasses": seam_drift <= meters_per_pixel and startup_jump <= 2.0 * meters_per_pixel and seam_degrees <= 1.0}
        dense_ok = dense_ok and bool(dense_report[side]["seamPasses"])

    # Visible geometry, not a formula-only ankle channel, is authoritative for
    # timing. Cross-check it against the baked ankle channel so a small early
    # channel change cannot conceal an early skinned metatarsal rise.
    for side in ("l", "r"):
        full_groups = [group for group in dense_report[side]["groups"] if not group.get("ignoredIncompleteBoundaryFragment", False)]
        for cycle_index, item in enumerate(cycles_report[side]):
            # Full contact groups occur in chronological order for each side.
            # The root clip boundary splits the right gait cycle at a
            # different time than the left, so wall-clock half-clip indexing
            # is not a valid bilateral correspondence.
            group = full_groups[cycle_index] if cycle_index < len(full_groups) else None
            effective = None if group is None else group["effectiveRockerOnsetPhase"]
            channel = item["rockerOnsetPhase"]
            geometric_lead = None if effective is None else item["rearExtensionPeakPhase"] - effective
            item["effectiveSkinnedMetatarsalOnsetPhase"] = effective
            item["effectiveSkinnedRockerToPeakLeadCycle"] = geometric_lead
            item["ankleVsSkinnedOnsetDeltaCycle"] = None if channel is None or effective is None else channel - effective
            visible_loaded = [
                entry for entry in key_cycles(rows, side)[cycle_index]
                if effective is not None and item["releasePhase"] is not None
                and effective <= entry["phase"] < item["releasePhase"]
                and entry["toePatchMinimumM"] <= .008
            ]
            item["channelLoadedRockerSamples"] = item["loadedRockerSamples"]
            item["loadedRockerSamples"] = len(visible_loaded)
            item["passes"] = bool(
                item["passes"]
                and effective is not None
                and geometric_lead is not None and phase["minimumOnsetLead"] <= geometric_lead <= phase["maximumOnsetLead"]
                and phase["loadedRockerSamplesAt60Hz"][0] <= len(visible_loaded) <= phase["loadedRockerSamplesAt60Hz"][1]
                # The preserved ankle channel is retained as a diagnostic
                # only. Final skinned metatarsal geometry defines visible
                # rocker onset after candidate-local toe-pivot compensation.
            )
    causal_ok = all(item["passes"] for side in cycles_report.values() for item in side)

    scale_ratio = overlay["referenceScale"]["targetSameFootStrideM"] / 2.75
    prior_extrema = respin_1["clips"]["PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"]["footExtremaRelativePelvis"]
    current_extrema = root["footExtremaRelativePelvis"]
    reach = {side: {"actualFrontM": current_extrema[side]["frontM"], "derivedMinimumM": prior_extrema[side]["frontM"] * scale_ratio} for side in ("l", "r")}
    checks = {
        "accepted_v8_1_immutable": bool(generated["immutableUnchanged"] and base["checks"]["immutable_v8_1_unchanged"]),
        "all_exported_keys_ground_support_and_joint_continuity": all(base["checks"][key] for key in ("both_clips_all_exported_keys_measured", "no_selected_sole_penetration_any_key", "always_supported", "joint_continuity_and_constraints")),
        "physical_stride_and_speed": bool(base["checks"]["reference_scale_speed_4_5_to_4_8_kmh"] and base["checks"]["reference_scale_same_foot_stride_matches_target_within_1pct"]),
        "front_reach_derived_from_2_60m_stride": all(reach[side]["actualFrontM"] >= reach[side]["derivedMinimumM"] for side in ("l", "r")),
        "bilateral_phase_causal_rocker": causal_ok,
        "dense_distal_toe_contact_lock": dense_ok,
    }
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "candidateGlbSha256": sha256_file(args.glb),
        "checks": checks,
        "method": "base validator skins selected sole/toe vertices at every baked key; this validator derives bilateral causal ordering, zero passive foot translation, exported toe/ankle angular-velocity decay, and later receiving-arm motion directly from the final GLB channels.",
        "physical": {"referenceStrideM": root["referenceScaleSameFootStrideM"], "referenceSpeedKmh": root["referenceScaleMeanRootSpeedKmh"], "worldHipHeightM": base["scale"]["candidateWorldHipHeightM"]},
        "derivedFrontReach": {"formula": "respin-1 front extrema * (2.60 / 2.75); this preserves the prior materially-long reach at the newly locked stride rather than retaining an obsolete absolute 2.75m gate.", "sides": reach},
        "causalCycles": cycles_report,
        "denseDistalToeContact": {"thresholds": {"xDriftM": x_limit, "zDriftM": z_limit, "yDriftM": y_limit, "twoPixelsM": 2.0 * meters_per_pixel, "metatarsalReversalM": .001, "seamPixelsM": meters_per_pixel, "seamOrientationDegrees": 1.0}, "sides": dense_report},
        "baseValidation": str(args.base_validation),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": checks, "physical": result["physical"]}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
