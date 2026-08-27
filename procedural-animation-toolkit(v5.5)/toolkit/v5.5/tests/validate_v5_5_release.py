#!/usr/bin/env python3
"""Fail-closed structural and body-balance validation for Tarbosaurus V5.5."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import AnatomicalBasis, SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader


def qsample(values: np.ndarray, phase: float) -> np.ndarray:
    f = float(np.clip(phase, 0.0, 1.0)) * (len(values) - 1)
    i = int(math.floor(f))
    j = min(i + 1, len(values) - 1)
    if i == j:
        return values[i]
    return Slerp([0.0, 1.0], Rotation.from_quat(np.stack([values[i], values[j]])))([f - i]).as_quat()[0]


def qerror_degrees(a: np.ndarray, b: np.ndarray) -> float:
    delta = Rotation.from_quat(a).inv() * Rotation.from_quat(b)
    return float(np.degrees(np.linalg.norm(delta.as_rotvec())))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--bone-map", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--constrained-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    cfg = parser.parse_args()

    baseline = GlbAsset(cfg.baseline)
    generated = GlbAsset(cfg.generated)
    semantics = SemanticMap.load(cfg.bone_map)
    basis = AnatomicalBasis.gltf_y_up(generated, semantics)
    old = AnimationPackReader(baseline)
    new = AnimationPackReader(generated)
    manifest = json.loads(cfg.manifest.read_text())
    profile = json.loads(cfg.profile.read_text())
    constrained = json.loads(cfg.constrained_report.read_text())

    expected_names = {name.replace("_V5", "_V5_5") for name in old.animations}
    actual_names = set(new.animations)
    assert actual_names == expected_names, sorted(actual_names ^ expected_names)
    assert len(actual_names) == 37
    assert all("_V5_5" in name and "_V4" not in name for name in actual_names)
    assert manifest["schema"] == "eonwild.animation-manifest.v5.5"
    assert manifest["version"] == "5.5.0"
    assert {clip["name"] for clip in manifest["clips"]} == actual_names

    old_joints, old_ibm = baseline.skin_data()
    new_joints, new_ibm = generated.skin_data()
    assert old_joints == new_joints and len(new_joints) == 75
    assert np.array_equal(old_ibm, new_ibm)
    assert constrained["automated_quality_pass"] is True
    assert all(all(gates.values()) for gates in constrained["quality_gate_summary"].values())

    ground = float(generated.primitive().positions[:, 1].min())
    pelvis_index = generated.name_to_node[semantics.bone("pelvis")]
    hip_height = float(generated.rest_world[pelvis_index][1, 3] - ground)

    def metrics(reader: AnimationPackReader, asset: GlbAsset, name: str) -> dict[str, object]:
        clip = reader.animation(name)
        worlds = reader.worlds_for_samples(clip, range(len(clip.times)))
        def point(world: list[np.ndarray], tag: str) -> np.ndarray:
            return world[asset.name_to_node[semantics.bone(tag)]][:3, 3]
        torso_pitch = []
        head_pitch = []
        foot_spread = []
        rear_reach = []
        for world in worlds:
            pelvis = point(world, "pelvis")
            chest = point(world, "chest")
            head = point(world, "head")
            left = point(world, "foot_l")
            right = point(world, "foot_r")
            torso = chest - pelvis
            neck_head = head - chest
            torso_pitch.append(math.degrees(math.atan2(float(np.dot(torso, basis.up)), float(np.dot(torso, basis.forward)))))
            head_pitch.append(math.degrees(math.atan2(float(np.dot(neck_head, basis.up)), float(np.dot(neck_head, basis.forward)))))
            foot_spread.append(abs(float(np.dot(right - left, basis.forward))) / hip_height)
            rear_reach.append(min(float(np.dot(left - pelvis, basis.forward)), float(np.dot(right - pelvis, basis.forward))) / hip_height)
        return {
            "torsoPitchMedianDegrees": float(np.median(torso_pitch)),
            "headPitchMedianDegrees": float(np.median(head_pitch)),
            "foreAftFootSpreadMedianHipFraction": float(np.median(foot_spread)),
            "maximumRearReachHipFraction": float(min(rear_reach)),
        }

    idle_old = metrics(old, baseline, "PROC_IDLE_BREATH_V5")
    idle_new = metrics(new, generated, "PROC_IDLE_BREATH_V5_5")
    walk_old = metrics(old, baseline, "PROC_WALK_RELAXED_V5_INPLACE")
    walk_new = metrics(new, generated, "PROC_WALK_RELAXED_V5_5_INPLACE")
    eat_old = metrics(old, baseline, "PROC_EAT_LOOP_V5")
    eat_new = metrics(new, generated, "PROC_EAT_LOOP_V5_5")

    assert abs(idle_new["torsoPitchMedianDegrees"]) < abs(idle_old["torsoPitchMedianDegrees"])
    assert abs(idle_new["headPitchMedianDegrees"]) <= abs(idle_old["headPitchMedianDegrees"]) - 0.5
    assert idle_new["foreAftFootSpreadMedianHipFraction"] >= idle_old["foreAftFootSpreadMedianHipFraction"] + 0.10
    assert abs(walk_new["maximumRearReachHipFraction"]) <= abs(walk_old["maximumRearReachHipFraction"]) * 0.88
    assert profile["contact_lead_stride"] > 0.36
    assert profile["toe_off_window_fraction"] >= 0.23
    assert eat_new["foreAftFootSpreadMedianHipFraction"] >= 0.10
    assert abs(eat_new["torsoPitchMedianDegrees"]) < abs(eat_old["torsoPitchMedianDegrees"])

    attack = new.animation("PROC_BITE_ATTACK_V5_5")
    root = semantics.bone("root")
    pelvis_bone = semantics.bone("pelvis")
    root_delta = attack.translations[root] - generated.rest_translation[generated.name_to_node[root]]
    attack_forward = root_delta @ basis.forward / hip_height
    attack_worlds = new.worlds_for_samples(attack, range(len(attack.times)))
    attack_pelvis_world = np.asarray([world[generated.name_to_node[pelvis_bone]][:3, 3] for world in attack_worlds])
    attack_vertical = (attack_pelvis_world - attack_pelvis_world[0]) @ basis.up / hip_height
    preload_index = int(np.argmin(attack_forward))
    drive_index = int(np.argmax(attack_forward))
    assert float(attack_forward[preload_index]) <= -0.05
    assert float(attack_forward[drive_index]) >= 0.15
    assert float(np.min(attack_vertical)) <= -0.07
    assert preload_index < drive_index
    assert pelvis_bone in attack.translations
    eat_clip = new.animation("PROC_EAT_LOOP_V5_5")
    assert pelvis_bone in eat_clip.translations
    eat_worlds = new.worlds_for_samples(eat_clip, range(len(eat_clip.times)))
    eat_pelvis_world = np.asarray([world[generated.name_to_node[pelvis_bone]][:3, 3] for world in eat_worlds])
    eat_vertical = (eat_pelvis_world - eat_pelvis_world[0]) @ basis.up / hip_height
    eat_vertical_excursion = float(np.max(eat_vertical) - np.min(eat_vertical))
    assert eat_vertical_excursion >= 0.04

    jaw = semantics.bone("jaw")
    jaw_index = generated.name_to_node[jaw]
    jaw_axis = generated.rest_world_rotation[jaw_index].inv().apply(basis.lateral)
    jaw_axis /= np.linalg.norm(jaw_axis)
    jaw_rest = generated.rest_rotation[jaw_index]
    def close_degrees(clip_name: str, index: int) -> float:
        quat = new.animation(clip_name).rotations[jaw][index]
        return -float(np.degrees(np.dot((jaw_rest.inv() * Rotation.from_quat(quat)).as_rotvec(), jaw_axis)))
    neutral_min = min(close_degrees(name, i) for name in actual_names if "_TO_" not in name and any(k in name for k in ("WALK", "TURN", "START", "BRAKE", "IDLE")) for i in range(len(new.animation(name).times)))
    bite = new.animation("PROC_BITE_ATTACK_V5_5")
    bite_early_load = close_degrees(bite.name, int(round(0.15 * (len(bite.times) - 1))))
    bite_contact = close_degrees(bite.name, int(round(0.56 * (len(bite.times) - 1))))
    assert neutral_min > 49.5 and bite_early_load > 49.0 and bite_contact > 49.5 and close_degrees(bite.name, -1) > 49.5

    max_rotation_error = 0.0
    max_position_error = 0.0
    transition_count = 0
    for clip in new.animations.values():
        assert np.all(np.diff(clip.times) > 0.0), clip.name
        if not clip.extras.get("transition"):
            continue
        transition_count += 1
        source = new.animation(clip.extras["sourceClip"])
        target = new.animation(clip.extras["targetClip"])
        source_phase = float(clip.extras.get("sourcePhase", 0.0))
        target_phase = float(clip.extras.get("targetPhase", 0.0))
        for bone, values in clip.rotations.items():
            source_values = source.rotations.get(bone, target.rotations[bone])
            target_values = target.rotations.get(bone, source.rotations[bone])
            max_rotation_error = max(max_rotation_error, qerror_degrees(values[0], qsample(source_values, source_phase)), qerror_degrees(values[-1], qsample(target_values, target_phase)))
        for node, values in clip.translations.items():
            rest = generated.rest_translation[generated.name_to_node[node]]
            if node in source.translations:
                source_values = source.translations[node]
                source_value = source_values[int(round(source_phase * (len(source_values) - 1)))]
            else:
                source_value = rest
            if node in target.translations:
                target_values = target.translations[node]
                target_value = target_values[int(round(target_phase * (len(target_values) - 1)))]
            else:
                target_value = rest
            max_position_error = max(max_position_error, float(np.max(np.abs(values[0] - source_value))), float(np.max(np.abs(values[-1] - target_value))))
    assert transition_count == 16
    assert max_rotation_error < 1e-4, max_rotation_error
    assert max_position_error < 1e-6, max_position_error

    result = {
        "status": "PASS",
        "version": "5.5.0",
        "clipCount": len(actual_names),
        "transitionCount": transition_count,
        "skinJointCount": len(new_joints),
        "skinOrderPreserved": True,
        "inverseBindMatricesExact": True,
        "constrainedQualityGatesPass": True,
        "idle": {"v5": idle_old, "v5_5": idle_new},
        "walk": {"v5": walk_old, "v5_5": walk_new},
        "eat": {"v5": eat_old, "v5_5": eat_new},
        "attack": {
            "preloadForwardHipFraction": float(attack_forward[preload_index]),
            "driveForwardHipFraction": float(attack_forward[drive_index]),
            "preloadBeforeDrive": True,
            "maximumPelvisDropHipFraction": float(np.min(attack_vertical)),
        },
        "eatPelvisVerticalExcursionHipFraction": eat_vertical_excursion,
        "neutralJawMinimumCloseDegrees": neutral_min,
        "biteEarlyLoadCloseDegrees": bite_early_load,
        "biteContactCloseDegrees": bite_contact,
        "maxTransitionEndpointRotationErrorDegrees": max_rotation_error,
        "maxTransitionEndpointPositionError": max_position_error,
        "generatedSha256": sha256(cfg.generated),
        "measurementBoundary": "Visual balance proxies from the animated skeleton; not a physical center-of-mass or biological validation.",
    }
    cfg.output.parent.mkdir(parents=True, exist_ok=True)
    cfg.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
