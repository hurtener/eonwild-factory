from __future__ import annotations

import numpy as np

from ..errors import ContractError, ValidationFailure
from ..math.quaternion import from_rotation_vector, inverse, multiply, to_rotation_vector
from ..math.transforms import world_matrix
from .animation_state import clip_state, close_quaternion_loop, patch, sample_locals


def _rotation_from_matrix(matrix: np.ndarray) -> np.ndarray:
    m = matrix[:3, :3]
    scale = np.linalg.norm(m, axis=0)
    m = m / np.maximum(scale, 1e-15)
    trace = float(np.trace(m))
    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        q = np.array([(m[2,1]-m[1,2])/s, (m[0,2]-m[2,0])/s, (m[1,0]-m[0,1])/s, 0.25*s])
    else:
        i = int(np.argmax(np.diag(m)))
        if i == 0:
            s = np.sqrt(1.0 + m[0,0] - m[1,1] - m[2,2]) * 2.0
            q = np.array([0.25*s, (m[0,1]+m[1,0])/s, (m[0,2]+m[2,0])/s, (m[2,1]-m[1,2])/s])
        elif i == 1:
            s = np.sqrt(1.0 + m[1,1] - m[0,0] - m[2,2]) * 2.0
            q = np.array([(m[0,1]+m[1,0])/s, 0.25*s, (m[1,2]+m[2,1])/s, (m[0,2]-m[2,0])/s])
        else:
            s = np.sqrt(1.0 + m[2,2] - m[0,0] - m[1,1]) * 2.0
            q = np.array([(m[0,2]+m[2,0])/s, (m[1,2]+m[2,1])/s, 0.25*s, (m[1,0]-m[0,1])/s])
    return q / np.linalg.norm(q)


def _clamp_vector(vector: np.ndarray, limit: float) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    return vector if length <= limit else vector * (limit / length)


def _solve_sample(glb, current, baseline, sample, chain, parameters, bounds):
    current_t, current_r, current_s = sample_locals(glb, current, sample)
    base_t, base_r, base_s = sample_locals(glb, baseline, sample)
    foot_index = glb.name_to_node[chain[-1]]
    target = world_matrix(glb, base_t, base_r, foot_index, base_s)
    target_q = _rotation_from_matrix(target)
    articulated = chain[:-1]
    variable = np.zeros(len(articulated) * 3, dtype=np.float64)
    rotation_limits = [
        np.radians(float(value)) for value in parameters["jointLimitsDegrees"]
    ]
    if len(rotation_limits) != len(articulated):
        raise ContractError("joint limit count does not match articulated chain")
    pivot_limit = float(bounds["footPivotTranslationM"])

    def evaluate(values):
        rotations = [row.copy() for row in current_r]
        for offset, name in enumerate(articulated):
            delta = values[offset*3:(offset+1)*3]
            index = glb.name_to_node[name]
            rotations[index] = multiply(rotations[index], from_rotation_vector(delta))
        world = world_matrix(glb, current_t, rotations, foot_index, current_s)
        return world[:3, 3] - target[:3, 3], rotations

    damping = float(parameters["damping"])
    epsilon = float(parameters["finiteDifference"])
    for _ in range(int(parameters["iterations"])):
        residual, _ = evaluate(variable)
        if float(np.linalg.norm(residual)) <= float(parameters["tolerance"]):
            break
        jacobian = np.empty((3, len(variable)), dtype=np.float64)
        for column in range(len(variable)):
            shifted = variable.copy()
            shifted[column] += epsilon
            jacobian[:, column] = (evaluate(shifted)[0] - residual) / epsilon
        lhs = jacobian.T @ jacobian + damping * np.eye(len(variable))
        step = np.linalg.solve(lhs, -jacobian.T @ residual)
        variable += step
        for offset in range(len(articulated)):
            section = slice(offset*3, (offset+1)*3)
            variable[section] = _clamp_vector(variable[section], rotation_limits[offset])
    _, rotations_all = evaluate(variable)
    parent_index = int(glb.parents[foot_index])
    parent_world = world_matrix(glb, current_t, rotations_all, parent_index, current_s)
    required_local = np.linalg.inv(parent_world) @ np.append(target[:3, 3], 1.0)
    foot_translation = required_local[:3]
    pivot = foot_translation - current_t[foot_index]
    pivot = _clamp_vector(pivot, pivot_limit)
    foot_translation = current_t[foot_index] + pivot
    parent_q = _rotation_from_matrix(parent_world)
    foot_rotation = multiply(inverse(parent_q), target_q)
    rotations_all[foot_index] = foot_rotation
    achieved = world_matrix(glb, [*current_t[:foot_index], foot_translation, *current_t[foot_index+1:]], rotations_all, foot_index, current_s)
    position_error = float(np.linalg.norm(achieved[:3, 3] - target[:3, 3]))
    orientation_error = float(np.linalg.norm(to_rotation_vector(multiply(inverse(target_q), _rotation_from_matrix(achieved)))))
    return [rotations_all[glb.name_to_node[name]] for name in chain], foot_translation, position_error, orientation_error, variable, pivot


def apply(glb, base_glb, rig, motion, layer):
    if layer["stage"] != "ik-contact":
        raise ContractError("leg contact layer requires ik-contact stage")
    legs = rig["roles"]["legs"]
    results, metrics = {}, {}
    for clip in motion["clips"]:
        current, accessors, _ = clip_state(glb, clip["name"])
        baseline, _, _ = clip_state(base_glb, clip["name"])
        clip_patches = {}
        maximum_position = 0.0
        maximum_orientation = 0.0
        maximum_pivot = 0.0
        maximum_joint = 0.0
        for side in sorted(legs):
            chain = legs[side]["contactChain"]
            outputs = {name: current[(name, "rotation")].copy() for name in chain}
            foot = chain[-1]
            foot_translations = current[(foot, "translation")].copy()
            for sample in range(len(foot_translations)):
                rotations, translation, position_error, orientation_error, variable, pivot = _solve_sample(
                    glb, current, baseline, sample, chain, layer["parameters"], layer["bounds"]
                )
                for name, rotation in zip(chain, rotations):
                    outputs[name][sample] = rotation
                foot_translations[sample] = translation
                maximum_position = max(maximum_position, position_error)
                maximum_orientation = max(maximum_orientation, np.degrees(orientation_error))
                maximum_pivot = max(maximum_pivot, float(np.linalg.norm(pivot)))
                for offset in range(len(chain) - 1):
                    maximum_joint = max(maximum_joint, np.degrees(float(np.linalg.norm(variable[offset*3:(offset+1)*3]))))
            for rows in outputs.values():
                close_quaternion_loop(rows)
            foot_translations[-1] = foot_translations[0]
            for name, rows in outputs.items():
                clip_patches.setdefault(name, {})["rotation"] = patch(accessors, name, "rotation", rows)
            clip_patches.setdefault(foot, {})["translation"] = patch(accessors, foot, "translation", foot_translations)
        if maximum_position > float(layer["bounds"]["footWorldPositionErrorM"]):
            raise ValidationFailure(f"foot world position solve exceeded bound: {maximum_position}")
        if maximum_orientation > float(layer["bounds"]["footWorldOrientationErrorDegrees"]):
            raise ValidationFailure(f"foot world orientation solve exceeded bound: {maximum_orientation}")
        results[clip["name"]] = clip_patches
        metrics[clip["semanticId"]] = {
            "maxFootWorldPositionErrorM": maximum_position,
            "maxFootWorldOrientationErrorDegrees": maximum_orientation,
            "maxFootPivotTranslationM": maximum_pivot,
            "maxJointLocalDeltaDegrees": maximum_joint,
        }
    return results, metrics
