import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/private/tmp/eonwild-sprint-interface-integration/src")

from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import (
    _clip_state,
    _pose,
    _q_to_rotvec,
    _qinv,
    _qmul,
    _world_matrices,
    _world_position,
)


PACKAGE_ROOT = Path("/private/tmp/eonwild-refine22-fixed480-trio")
PHASE_S = 14 / 120
THRESHOLD_MPS = 0.001


def native_times(package: str, *, terminal: bool, phase_s: float | None = None) -> np.ndarray:
    glb = Glb.from_bytes((PACKAGE_ROOT / package / "root_motion.glb").read_bytes())
    _, raw = _clip_state(glb, glb.document["animations"][0]["name"])
    times = np.asarray(raw, dtype=np.float32).astype(np.float64)
    endpoint = len(times) - 1 if terminal else 0
    if phase_s is not None:
        matches = np.flatnonzero(np.abs(times - phase_s) <= 2e-6)
        assert len(matches) == 1
        endpoint = int(matches[0])
    indices = np.arange(endpoint - 4, endpoint + 1) if terminal else np.arange(endpoint, endpoint + 5)
    assert indices.min() >= 0 and indices.max() < len(times)
    return times[indices] - times[endpoint]


PATTERNS = {
    "start": {
        "before": native_times("start", terminal=True),
        "after": native_times("steady", terminal=False, phase_s=PHASE_S),
    },
    "stop": {
        "before": native_times("steady", terminal=True, phase_s=PHASE_S),
        "after": native_times("stop", terminal=False),
    },
}


def derivative_weights(times: np.ndarray, *, terminal: bool, points: int, degree: int) -> np.ndarray:
    selected = np.arange(len(times) - points, len(times)) if terminal else np.arange(points)
    endpoint = selected[-1] if terminal else selected[0]
    other = selected[selected != endpoint]
    x = times[other] - times[endpoint]
    scale = float(np.max(np.abs(x)))
    u = x / scale
    design = np.column_stack([u**power for power in range(1, degree + 1)])
    # Equal-weight endpoint-constrained least squares. For square designs this
    # is the usual exact one-sided finite difference formula.
    other_weights = np.linalg.pinv(design, rcond=1e-14)[0] / scale
    weights = np.zeros(len(times), dtype=np.float64)
    weights[other] = other_weights
    weights[endpoint] = -float(np.sum(other_weights))
    return weights


ESTIMATORS = {
    "quadratic_3_current": (3, 2),
    "cubic_4": (4, 3),
    "quadratic_ls_5": (5, 2),
    "cubic_ls_5": (5, 3),
    "quartic_5": (5, 4),
}


TAIL_LENGTH_M = 4.0
ANGLE_AMPLITUDE_RAD = math.radians(1.62)
OMEGA = 2 * math.pi / (23 / 48)
LAG = math.atan(OMEGA * 0.12)
OFFSET = np.array([12.0, -4.0, 2.0])


def angle(time_s: float) -> float:
    return ANGLE_AMPLITUDE_RAD * math.sin(OMEGA * (PHASE_S + time_s) - LAG)


def tail_position(time_s: float) -> np.ndarray:
    theta = angle(time_s)
    return OFFSET + np.array([
        TAIL_LENGTH_M * math.cos(theta),
        TAIL_LENGTH_M * math.sin(theta),
        0.15 * math.sin(2 * theta),
    ])


def tail_velocity(time_s: float) -> np.ndarray:
    theta = angle(time_s)
    theta_dot = ANGLE_AMPLITUDE_RAD * OMEGA * math.cos(OMEGA * (PHASE_S + time_s) - LAG)
    return np.array([
        -TAIL_LENGTH_M * math.sin(theta) * theta_dot,
        TAIL_LENGTH_M * math.cos(theta) * theta_dot,
        0.3 * math.cos(2 * theta) * theta_dot,
    ])


def bounded_harmonic_tail_position(time_s: float) -> np.ndarray:
    harmonic_omega = 3 * OMEGA
    harmonic_lag = math.atan(harmonic_omega * 0.12)
    theta = math.radians(5.0) * math.sin(harmonic_omega * (PHASE_S + time_s) - harmonic_lag)
    return OFFSET + np.array([
        TAIL_LENGTH_M * math.cos(theta),
        TAIL_LENGTH_M * math.sin(theta),
        0.15 * math.sin(2 * theta),
    ])


def bounded_harmonic_tail_velocity(time_s: float) -> np.ndarray:
    harmonic_omega = 3 * OMEGA
    harmonic_lag = math.atan(harmonic_omega * 0.12)
    theta = math.radians(5.0) * math.sin(harmonic_omega * (PHASE_S + time_s) - harmonic_lag)
    theta_dot = math.radians(5.0) * harmonic_omega * math.cos(
        harmonic_omega * (PHASE_S + time_s) - harmonic_lag
    )
    return np.array([
        -TAIL_LENGTH_M * math.sin(theta) * theta_dot,
        TAIL_LENGTH_M * math.cos(theta) * theta_dot,
        0.3 * math.cos(2 * theta) * theta_dot,
    ])


def analytic_translation(time_s: float) -> np.ndarray:
    return OFFSET + np.array([
        1.7 * time_s + 0.08 * math.sin(OMEGA * (PHASE_S + time_s)),
        -0.03 * math.cos(0.7 * OMEGA * (PHASE_S + time_s)),
        0.015 * math.sin(1.4 * OMEGA * (PHASE_S + time_s)),
    ])


def analytic_translation_velocity(time_s: float) -> np.ndarray:
    return np.array([
        1.7 + 0.08 * OMEGA * math.cos(OMEGA * (PHASE_S + time_s)),
        0.03 * 0.7 * OMEGA * math.sin(0.7 * OMEGA * (PHASE_S + time_s)),
        0.015 * 1.4 * OMEGA * math.cos(1.4 * OMEGA * (PHASE_S + time_s)),
    ])


def quaternion(time_s: float) -> np.ndarray:
    half = angle(time_s) / 2
    return np.array([0.0, 0.0, math.sin(half), math.cos(half)])


def values(function, times: np.ndarray, *, float32: bool, jump: np.ndarray | None = None) -> np.ndarray:
    rows = []
    for time_s in times:
        row = function(float(time_s))
        if jump is not None:
            row = row + jump * float(time_s)
        rows.append(row)
    result = np.asarray(rows)
    return result.astype(np.float32).astype(np.float64) if float32 else result.astype(np.float64)


def estimate(times: np.ndarray, rows: np.ndarray, *, terminal: bool, name: str) -> np.ndarray:
    points, degree = ESTIMATORS[name]
    return derivative_weights(times, terminal=terminal, points=points, degree=degree) @ rows


def rotation_estimate(times: np.ndarray, rows: np.ndarray, *, terminal: bool, name: str) -> np.ndarray:
    points, degree = ESTIMATORS[name]
    selected = np.arange(len(times) - points, len(times)) if terminal else np.arange(points)
    endpoint = selected[-1] if terminal else selected[0]
    inverse = _qinv(tuple(rows[endpoint]))
    deltas = np.zeros((len(times), 3), dtype=np.float64)
    for index in selected:
        deltas[index] = _q_to_rotvec(_qmul(inverse, tuple(rows[index])))
    return derivative_weights(times, terminal=terminal, points=points, degree=degree) @ deltas


def directions_for(bias: np.ndarray) -> dict[str, np.ndarray]:
    unit = bias / np.linalg.norm(bias)
    trial = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(unit, trial))) > 0.9:
        trial = np.array([0.0, 1.0, 0.0])
    orthogonal = np.cross(unit, trial)
    orthogonal /= np.linalg.norm(orthogonal)
    diagonal = np.array([1.0, 2.0, -3.0])
    diagonal /= np.linalg.norm(diagonal)
    return {
        "+x": np.array([1.0, 0.0, 0.0]),
        "-x": np.array([-1.0, 0.0, 0.0]),
        "+y": np.array([0.0, 1.0, 0.0]),
        "-y": np.array([0.0, -1.0, 0.0]),
        "+z": np.array([0.0, 0.0, 1.0]),
        "-z": np.array([0.0, 0.0, -1.0]),
        "+smooth_bias": unit,
        "-smooth_bias": -unit,
        "orthogonal": orthogonal,
        "diagonal": diagonal,
        "opposite_diagonal": -diagonal,
    }


report = {
    "package_root": str(PACKAGE_ROOT),
    "phase_s": PHASE_S,
    "threshold_mps": THRESHOLD_MPS,
    "patterns": {},
    "actual_emitted_world": {},
}

for join, pair in PATTERNS.items():
    entry = {
        "before_relative_float32_times_s": pair["before"].tolist(),
        "after_relative_float32_times_s": pair["after"].tolist(),
        "weights": {},
        "smooth_counterexamples": {},
        "adversarial_linear_jumps": {},
    }
    for estimator, (points, degree) in ESTIMATORS.items():
        before_weights = derivative_weights(pair["before"], terminal=True, points=points, degree=degree)
        after_weights = derivative_weights(pair["after"], terminal=False, points=points, degree=degree)
        entry["weights"][estimator] = {
            "before_l1_per_s": float(np.sum(np.abs(before_weights))),
            "after_l1_per_s": float(np.sum(np.abs(after_weights))),
            "before": before_weights.tolist(),
            "after": after_weights.tolist(),
        }
        model_results = {}
        for model_name, function, velocity_function in (
            ("analytic_translation", analytic_translation, analytic_translation_velocity),
            ("four_meter_tail_point", tail_position, tail_velocity),
            (
                "four_meter_tail_point_third_harmonic",
                bounded_harmonic_tail_position,
                bounded_harmonic_tail_velocity,
            ),
        ):
            precision_results = {}
            known_velocity = velocity_function(0.0)
            for precision, float32 in (("float64_control", False), ("float32_emitted", True)):
                before_values = values(function, pair["before"], float32=float32)
                after_values = values(function, pair["after"], float32=float32)
                before_velocity = estimate(pair["before"], before_values, terminal=True, name=estimator)
                after_velocity = estimate(pair["after"], after_values, terminal=False, name=estimator)
                precision_results[precision] = {
                    "false_velocity_mismatch_mps": float(np.linalg.norm(before_velocity - after_velocity)),
                    "known_endpoint_velocity_mps": known_velocity.tolist(),
                    "before_absolute_error_mps": float(np.linalg.norm(before_velocity - known_velocity)),
                    "after_absolute_error_mps": float(np.linalg.norm(after_velocity - known_velocity)),
                    "before_velocity_mps": before_velocity.tolist(),
                    "after_velocity_mps": after_velocity.tolist(),
                }
            model_results[model_name] = precision_results
        before_quaternions = values(quaternion, pair["before"], float32=True)
        after_quaternions = values(quaternion, pair["after"], float32=True)
        before_angular = rotation_estimate(pair["before"], before_quaternions, terminal=True, name=estimator)
        after_angular = rotation_estimate(pair["after"], after_quaternions, terminal=False, name=estimator)
        angular_error = before_angular - after_angular
        known_angular = np.array([
            0.0,
            0.0,
            ANGLE_AMPLITUDE_RAD * OMEGA * math.cos(OMEGA * PHASE_S - LAG),
        ])
        model_results["quaternion_rotation_float32"] = {
            "false_angular_velocity_mismatch_degrees_per_s": float(math.degrees(np.linalg.norm(angular_error))),
            "known_endpoint_angular_velocity_degrees_per_s": np.degrees(known_angular).tolist(),
            "before_absolute_error_degrees_per_s": float(math.degrees(np.linalg.norm(before_angular - known_angular))),
            "after_absolute_error_degrees_per_s": float(math.degrees(np.linalg.norm(after_angular - known_angular))),
        }
        entry["smooth_counterexamples"][estimator] = model_results

    smooth_before = values(tail_position, pair["before"], float32=True)
    smooth_after = values(tail_position, pair["after"], float32=True)
    for estimator in ("quadratic_3_current", "cubic_4", "cubic_ls_5", "quartic_5"):
        before_velocity = estimate(pair["before"], smooth_before, terminal=True, name=estimator)
        after_velocity = estimate(pair["after"], smooth_after, terminal=False, name=estimator)
        bias = before_velocity - after_velocity
        directions = directions_for(bias)
        jump_report = {"smooth_bias_mps": bias.tolist(), "cases": {}}
        for magnitude in (0.001, 0.00125, 0.002, 0.003, 0.004, 0.005):
            trials = {}
            for direction_name, direction in directions.items():
                jumped_after = values(
                    tail_position,
                    pair["after"],
                    float32=True,
                    jump=magnitude * direction,
                )
                detected = before_velocity - estimate(pair["after"], jumped_after, terminal=False, name=estimator)
                trials[direction_name] = float(np.linalg.norm(detected))
            minimum_name = min(trials, key=trials.get)
            maximum_name = max(trials, key=trials.get)
            jump_report["cases"][f"{magnitude:.5f}"] = {
                "known_jump_mps": magnitude,
                "minimum_detected_mps": trials[minimum_name],
                "minimum_direction": minimum_name,
                "maximum_detected_mps": trials[maximum_name],
                "maximum_direction": maximum_name,
                "all_directions": trials,
                "all_above_threshold": all(value > THRESHOLD_MPS for value in trials.values()),
            }
        entry["adversarial_linear_jumps"][estimator] = jump_report
    report["patterns"][join] = entry


def world_boundary(package: str, mode: str, *, terminal: bool, phase_s: float | None = None):
    folder = PACKAGE_ROOT / package
    glb = Glb.from_bytes((folder / f"{mode}.glb").read_bytes())
    runtime = json.loads((folder / "runtime.json").read_text())
    plan = json.loads((folder / "plan.json").read_text())
    animation = glb.document["animations"][0]
    tracks, raw_times = _clip_state(glb, animation["name"])
    times = np.asarray(raw_times, dtype=np.float64)
    endpoint = len(times) - 1 if terminal else 0
    if phase_s is not None:
        matches = np.flatnonzero(np.abs(times - phase_s) <= 2e-6)
        assert len(matches) == 1
        endpoint = int(matches[0])
    indices = np.arange(endpoint - 4, endpoint + 1) if terminal else np.arange(endpoint, endpoint + 5)
    root = glb.name_to_node[runtime["rig_roles"]["root"]]
    descendants = []
    for node in range(len(glb.nodes)):
        cursor = node
        while cursor is not None:
            if cursor == root:
                descendants.append(node)
                break
            cursor = glb.parents[cursor]
    forward = np.asarray(runtime["forward_axis"], dtype=np.float64)
    travel = np.asarray([
        plan["samples"][index]["root_forward_m"] - plan["samples"][0]["root_forward_m"]
        for index in indices
    ])
    positions = []
    rotations = []
    for index, distance in zip(indices, travel):
        pose = _pose(glb, tracks, int(index))
        matrices = _world_matrices(glb, *pose)
        offset = forward * distance if mode == "in_place" else np.zeros(3)
        positions.append([np.asarray(_world_position(matrices[node])) + offset for node in descendants])
        rotations.append([pose[1][node] for node in descendants])
    return (
        times[indices] - times[endpoint],
        np.asarray(positions),
        np.asarray(rotations),
        [glb.nodes[node].get("name") for node in descendants],
    )


for join in ("start", "stop"):
    before_package, after_package = (("start", "steady") if join == "start" else ("steady", "stop"))
    before_phase = PHASE_S if join == "stop" else None
    after_phase = PHASE_S if join == "start" else None
    report["actual_emitted_world"][join] = {}
    for mode in ("root_motion", "in_place"):
        before_times, before_positions, before_rotations, before_names = world_boundary(
            before_package, mode, terminal=True, phase_s=before_phase
        )
        after_times, after_positions, after_rotations, after_names = world_boundary(
            after_package, mode, terminal=False, phase_s=after_phase
        )
        assert before_names == after_names
        results = {}
        for estimator in ESTIMATORS:
            before_linear = np.stack([
                estimate(before_times, before_positions[:, node], terminal=True, name=estimator)
                for node in range(len(before_names))
            ])
            after_linear = np.stack([
                estimate(after_times, after_positions[:, node], terminal=False, name=estimator)
                for node in range(len(after_names))
            ])
            linear_errors = np.linalg.norm(before_linear - after_linear, axis=1)
            linear_witness = int(np.argmax(linear_errors))
            before_angular = np.stack([
                rotation_estimate(before_times, before_rotations[:, node], terminal=True, name=estimator)
                for node in range(len(before_names))
            ])
            after_angular = np.stack([
                rotation_estimate(after_times, after_rotations[:, node], terminal=False, name=estimator)
                for node in range(len(after_names))
            ])
            angular_errors = np.degrees(np.linalg.norm(before_angular - after_angular, axis=1))
            angular_witness = int(np.argmax(angular_errors))
            results[estimator] = {
                "maximum_linear_velocity_mismatch_mps": float(linear_errors[linear_witness]),
                "linear_witness_index": linear_witness,
                "linear_witness_name": before_names[linear_witness],
                "maximum_angular_velocity_mismatch_degrees_per_s": float(angular_errors[angular_witness]),
                "angular_witness_index": angular_witness,
                "angular_witness_name": before_names[angular_witness],
            }
        report["actual_emitted_world"][join][mode] = results

output = Path("/tmp/eonwild-evaluator-adversarial-report.json")
output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
print(output)
