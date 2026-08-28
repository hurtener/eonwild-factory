from __future__ import annotations

import numpy as np

from ..errors import ContractError, ValidationFailure
from ..math.quaternion import from_rotation_vector, inverse, multiply, to_rotation_vector
from ..math.transforms import all_world_positions, all_world_rotations, quaternion_matrix
from .animation_state import clip_state, close_quaternion_loop, patch, sample_locals


def apply(glb, base_glb, rig, motion, layer):
    if layer["stage"] != "pre-ik":
        raise ContractError("pelvis balance layer requires pre-ik stage")
    pelvis = rig["roles"]["pelvis"]
    parameters = layer["parameters"]
    amplitude = float(parameters["amplitudeScale"])
    axis = parameters["axes"]
    results, metrics = {}, {}
    for clip in motion["clips"]:
        tracks, accessors, timelines = clip_state(glb, clip["name"])
        rotations = tracks[(pelvis, "rotation")].copy()
        translations = tracks[(pelvis, "translation")].copy()
        timeline = timelines[(pelvis, "rotation")]
        if len(timeline) != len(rotations):
            raise ValidationFailure("pelvis track/timeline mismatch")
        duration = float(timeline[-1] - timeline[0])
        cycles = float(parameters["cyclesPerClip"])
        phase = (timeline - timeline[0]) / duration * cycles
        pelvis_index = glb.name_to_node[pelvis]
        lateral_baseline = []
        for sample in range(len(rotations)):
            local_t, local_r, _ = sample_locals(base_glb, tracks, sample)
            lateral_baseline.append(all_world_positions(base_glb, local_t, local_r)[pelvis_index][int(axis["lateral"])])
        lateral_baseline = np.asarray(lateral_baseline, dtype=np.float64)
        support = lateral_baseline - float(np.mean(lateral_baseline))
        support /= max(float(np.ptp(support)) * 0.5, 1e-15)
        vertical = -np.cos(4.0 * np.pi * phase)
        world_delta = np.zeros((len(rotations), 3), dtype=np.float64)
        world_delta[:, int(axis["lateral"])] = amplitude * float(parameters["lateralAmplitudeM"]) * support
        world_delta[:, int(axis["vertical"])] = amplitude * float(parameters["verticalAmplitudeM"]) * vertical
        baseline_world = []
        for sample in range(len(rotations)):
            _, local_r, _ = sample_locals(base_glb, tracks, sample)
            world_r = all_world_rotations(base_glb, local_r)
            baseline_world.append(world_r[pelvis_index])
        roll_signals = []
        angle = np.radians(float(parameters["rollPhaseShiftDegrees"]))
        for sample in range(len(rotations)):
            quadrature = np.cos(2.0 * np.pi * phase[sample])
            roll_signals.append(np.cos(angle) * support[sample] + np.sin(angle) * quadrature)
        roll_signals = np.asarray(roll_signals, dtype=np.float64)
        pulse = np.sin(2.0 * np.pi * phase) ** int(parameters["rollPulseExponent"])
        pulse_weight = float(parameters["rollPulseWeight"])
        roll_signals = (1.0 - pulse_weight) * roll_signals + pulse_weight * pulse
        roll_signals -= float(np.mean(roll_signals))
        roll_signals /= max(float(np.max(np.abs(roll_signals))), 1e-15)
        for sample in range(len(rotations)):
            local_t, local_r, local_s = sample_locals(glb, tracks, sample)
            parent_index = int(glb.parents[pelvis_index])
            world_r = all_world_rotations(glb, local_r)
            parent_basis = quaternion_matrix(world_r[parent_index]) @ np.diag(glb.rest_scale[parent_index])
            translations[sample] += np.linalg.solve(parent_basis, world_delta[sample])
            delta = np.zeros(3, dtype=np.float64)
            delta[int(axis["rollRotationVector"])] = np.radians(
                -amplitude * float(parameters["rollAmplitudeDegrees"]) * roll_signals[sample]
            )
            delta[int(axis["pitchRotationVector"])] = (
                float(parameters["rollPitchCoupling"])
                * delta[int(axis["rollRotationVector"])]
            )
            delta[int(axis["yawRotationVector"])] = (
                np.radians(amplitude * float(parameters["rollAmplitudeDegrees"]))
                * float(parameters["rollYawCoupling"])
                * -pulse[sample]
            )
            desired_world = multiply(from_rotation_vector(delta), baseline_world[sample])
            rotations[sample] = multiply(inverse(world_r[parent_index]), desired_world)
        translations[-1] = translations[0]
        close_quaternion_loop(rotations)
        results[clip["name"]] = {
            pelvis: {
                "rotation": patch(accessors, pelvis, "rotation", rotations),
                "translation": patch(accessors, pelvis, "translation", translations),
            }
        }
        metrics[clip["semanticId"]] = {
            "amplitudeScale": amplitude,
            "supportMean": float(np.mean(support)),
            "lateralAddedP2PM": float(np.ptp(amplitude * float(parameters["lateralAmplitudeM"]) * support)),
            "verticalAddedP2PM": float(np.ptp(amplitude * float(parameters["verticalAmplitudeM"]) * vertical)),
            "rollAddedP2PDegrees": float(2.0 * amplitude * float(parameters["rollAmplitudeDegrees"])),
        }
    return results, metrics
