from __future__ import annotations

import numpy as np

from ..errors import ContractError, ValidationFailure
from ..math.quaternion import from_rotation_vector, inverse, multiply, power, to_rotation_vector
from ..math.transforms import all_world_rotations
from .animation_state import clip_state, patch, sample_locals


def _cyclic_shift(signal, phase, lag, cycles):
    shifted = np.interp((phase - lag) % cycles, phase[:-1], signal[:-1], period=cycles)
    shifted[-1] = shifted[0]
    return shifted


def _cyclic_fundamental(signal, phase, cycles):
    """Project a sampled balance driver onto its declared loop fundamental."""
    theta = 2.0 * np.pi * phase
    design = np.column_stack((np.cos(theta[:-1]), np.sin(theta[:-1])))
    coefficients, *_ = np.linalg.lstsq(design, signal[:-1], rcond=None)
    fitted = np.cos(theta) * coefficients[0] + np.sin(theta) * coefficients[1]
    fitted -= float(np.mean(fitted[:-1]))
    fitted /= max(float(np.max(np.abs(fitted[:-1]))), 1e-15)
    fitted[-1] = fitted[0]
    return fitted


def _semantic_nodes(roles):
    for index, node in enumerate(roles["spine"]): yield f"spine.{index}", node
    yield "chest", roles["chest"]
    for index, node in enumerate(roles["tail"]): yield f"tail.{index}", node
    for index, node in enumerate(roles["neck"]): yield f"neck.{index}", node
    yield "head", roles["head"]


def _manifest(base, values, scale, role, accessor, lag):
    vectors = np.asarray([np.degrees(to_rotation_vector(multiply(inverse(a), b))) for a, b in zip(base, values)])
    steps, second = np.diff(vectors, axis=0), np.diff(vectors, n=2, axis=0)
    return {
        "semantic_role": role, "baseline_accessor_identity": int(accessor),
        "rotation_delta_only": True, "shared_sweep_scale": scale,
        "phase_offset_cycles": lag,
        "p2p_degrees": [float(np.ptp(vectors[:, axis])) for axis in range(3)],
        "mean_degrees": [float(np.mean(vectors[:, axis])) for axis in range(3)],
        "max_adjacent_delta_degrees": float(np.max(np.linalg.norm(steps, axis=1))) if len(steps) else 0.0,
        "max_second_difference_degrees": float(np.max(np.linalg.norm(second, axis=1))) if len(second) else 0.0,
        "loop_seam": float(np.linalg.norm(vectors[-1] - vectors[0])),
    }


def apply(glb, base_glb, rig, motion, layer):
    if layer["stage"] != "stabilization": raise ContractError("counterbalance layer requires stabilization stage")
    roles, parameters = rig["roles"], layer["parameters"]
    scale = float(parameters["amplitudeScale"])
    spine, chest, tail = list(roles["spine"]), roles["chest"], list(roles["tail"])
    neck_head = [*roles["neck"], roles["head"]]
    fractions = [float(value) for value in parameters["headResidualFractions"]]
    spine_amplitudes = [float(value) for value in parameters["spineRollP2PDegreesScaleOne"]]
    tail_amplitudes = [float(value) for value in parameters["tailYawP2PDegreesScaleOne"]]
    tail_lags = [float(value) for value in parameters["tailPhaseLagsCycles"]]
    if len(neck_head) != len(fractions) or fractions[-1] != 1.0: raise ContractError("invalid head residual fractions")
    if len(spine) != len(spine_amplitudes) or len(tail) != len(tail_amplitudes) or len(tail) != len(tail_lags): raise ContractError("counterbalance parameter count mismatch")
    role_by_node = {node: selector for selector, node in _semantic_nodes(roles)}
    results, metrics = {}, {}
    for clip in motion["clips"]:
        current, accessors, timelines = clip_state(glb, clip["name"])
        baseline, base_accessors, _ = clip_state(base_glb, clip["name"])
        timeline = timelines[(roles["pelvis"], "rotation")]
        cycles = float(parameters["cyclesPerClip"])
        phase = (timeline - timeline[0]) / float(timeline[-1] - timeline[0]) * cycles
        pelvis_world = []
        for sample in range(len(timeline)):
            _, local_r, _ = sample_locals(glb, current, sample)
            pelvis_world.append(all_world_rotations(glb, local_r)[glb.name_to_node[roles["pelvis"]]])
        reference = pelvis_world[0]
        signal = np.asarray([to_rotation_vector(multiply(value, inverse(reference)))[2] for value in pelvis_world])
        signal -= float(np.mean(signal[:-1])); signal[-1] = signal[0]
        signal = _cyclic_fundamental(signal, phase, cycles)
        values, lags = {}, {}
        for name, amplitude in zip(spine, spine_amplitudes):
            rows = current[(name, "rotation")].copy(); roll = -signal * np.radians(scale * amplitude * .5)
            for sample in range(len(rows)): rows[sample] = multiply(rows[sample], from_rotation_vector(np.asarray([0., 0., roll[sample]])))
            values[name], lags[name] = rows, 0.0
        rows = current[(chest, "rotation")].copy(); roll = -signal * np.radians(scale * float(parameters["chestRollP2PDegreesScaleOne"]) * .5)
        chest_lag = float(parameters["chestYawPhaseLagCycles"]); chest_yaw_signal = _cyclic_shift(signal, phase, chest_lag, cycles)
        pitch = chest_yaw_signal * np.radians(scale * float(parameters.get("chestPitchP2PDegreesScaleOne", 0.0)) * .5)
        yaw = chest_yaw_signal * np.radians(scale * float(parameters["chestYawP2PDegreesScaleOne"]) * .5)
        for sample in range(len(rows)): rows[sample] = multiply(rows[sample], from_rotation_vector(np.asarray([pitch[sample], yaw[sample], roll[sample]])))
        values[chest], lags[chest] = rows, chest_lag
        for name, amplitude, lag in zip(tail, tail_amplitudes, tail_lags):
            rows = current[(name, "rotation")].copy(); wave = _cyclic_shift(signal, phase, lag, cycles); yaw = float(parameters["tailYawSign"]) * wave * np.radians(scale * amplitude * .5)
            for sample in range(len(rows)): rows[sample] = multiply(rows[sample], from_rotation_vector(np.asarray([0., yaw[sample], 0.])))
            values[name], lags[name] = rows, lag
        correction_chain = neck_head
        correction_fractions = fractions
        if clip["rootMotion"]:
            correction_chain = [*spine, chest, *neck_head]
            correction_fractions = [
                float(index + 1) / len(correction_chain)
                for index in range(len(correction_chain))
            ]
        maximum = {name: 0.0 for name in correction_chain}; head_error = 0.0
        for name in neck_head: values[name], lags[name] = current[(name, "rotation")].copy(), 0.0
        for sample in range(len(timeline)):
            _, current_r, _ = sample_locals(glb, current, sample); _, base_r, _ = sample_locals(base_glb, baseline, sample)
            for name in (*spine, chest, *tail): current_r[glb.name_to_node[name]] = values[name][sample]
            current_world, base_world = all_world_rotations(glb, current_r), all_world_rotations(base_glb, base_r)
            head_index = glb.name_to_node[roles["head"]]; correction = multiply(base_world[head_index], inverse(current_world[head_index])); target_world = list(current_world)
            for name, fraction in zip(correction_chain, correction_fractions):
                index = glb.name_to_node[name]; desired = multiply(power(correction, fraction), current_world[index]); parent = glb.parents[index]
                local = desired if parent is None else multiply(inverse(target_world[int(parent)]), desired)
                values[name][sample] = local; target_world[index] = desired
                maximum[name] = max(maximum[name], np.degrees(float(np.linalg.norm(to_rotation_vector(multiply(inverse(current[(name, "rotation")][sample]), local))))))
            head_error = max(head_error, np.degrees(float(np.linalg.norm(to_rotation_vector(multiply(inverse(base_world[head_index]), target_world[head_index]))))))
        if any(maximum[name] > float(layer["bounds"]["neckLocalDeltaDegrees"]) + 1e-6 for name in roles["neck"]): raise ValidationFailure("neck stabilization bound exceeded")
        if maximum[roles["head"]] > float(layer["bounds"]["headLocalDeltaDegrees"]) + 1e-6: raise ValidationFailure("head stabilization bound exceeded")
        manifests = [_manifest(baseline[(name, "rotation")], rows, scale, role_by_node[name], base_accessors[(name, "rotation")], lags[name]) for name, rows in values.items()]
        results[clip["name"]] = {name: {"rotation": patch(accessors, name, "rotation", rows)} for name, rows in values.items()}
        metrics[clip["semanticId"]] = {"deltaManifest": manifests, "maxLocalDeltaDegrees": maximum, "maxHeadWorldErrorDegrees": head_error}
    return results, metrics
