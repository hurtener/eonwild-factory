"""Additional fail-closed engineering witnesses; never biological approval."""
from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb


def require_supported_geometry(source: Glb) -> None:
    """The current FK/skin adapter consumes TRS, not opaque node matrices."""
    for index, node in enumerate(source.nodes):
        if "matrix" in node:
            raise ContractError(f"node {index} uses a matrix; normalize it to explicit TRS before admission")
        scale = np.asarray(node.get("scale", [1, 1, 1]), dtype=float)
        if scale.shape != (3,) or not np.isfinite(scale).all() or np.any(scale <= 0):
            raise ContractError(f"node {index} has unsupported scale")
        if np.max(scale) - np.min(scale) > 1e-6:
            raise ContractError(f"node {index} has nonuniform scale; bake scale before admission")


def solver_checks(receipt: Mapping[str, Any]) -> dict:
    limits = {"max_foot_target_residual_m": 0.001, "max_unreachable_extension_m": 0.001,
              "maximum_articulation_envelope_violation_degrees": 0.01}
    pitch_rate_key = "maximum_solved_foot_pitch_velocity_degrees_per_s"
    pitch_limit_key = "solved_foot_pitch_velocity_limit_degrees_per_s"
    if pitch_rate_key in receipt or pitch_limit_key in receipt:
        pitch_limit = receipt.get(pitch_limit_key)
        valid_limit = (not isinstance(pitch_limit, bool) and isinstance(pitch_limit, (int, float))
                       and math.isfinite(pitch_limit) and pitch_limit > 0)
        limits[pitch_rate_key] = float(pitch_limit) if valid_limit else None
    checks, values = {}, {}
    for key, limit in limits.items():
        value = receipt.get(key)
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
        values[key] = float(value) if valid else None
        checks[key] = bool(valid and limit is not None and value <= limit)
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "values": values, "limits": limits,
            "classification": "engineering feasibility only; missing evidence is a failure"}


def emitted_rotation_rates(glb: Glb, maximum_degrees_per_s: float) -> dict:
    if not math.isfinite(maximum_degrees_per_s) or maximum_degrees_per_s <= 0:
        raise ContractError("rotation rate limit must be finite and positive")
    peak = 0.0
    witness = None
    channel_count = 0
    for animation in glb.document.get("animations", []):
        for channel in animation["channels"]:
            if channel["target"]["path"] != "rotation":
                continue
            sampler = animation["samplers"][channel["sampler"]]
            if sampler.get("interpolation", "LINEAR") != "LINEAR":
                raise ContractError("factory rate witness requires emitted LINEAR quaternion channels")
            times = np.asarray(glb.accessor_values(sampler["input"]), dtype=float).reshape(-1)
            quaternions = np.asarray(glb.accessor_values(sampler["output"]), dtype=float)
            if len(times) < 2 or quaternions.shape != (len(times), 4) or not np.isfinite(quaternions).all() or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
                raise ContractError("invalid final rotation timeline")
            norms = np.linalg.norm(quaternions, axis=1)
            if np.any(norms < 1e-10):
                raise ContractError("zero final quaternion")
            quaternions /= norms[:, None]
            angles = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quaternions[:-1] * quaternions[1:], axis=1)), 0, 1)))
            speed = angles / np.diff(times)
            index = int(np.argmax(speed)); channel_count += 1
            if float(speed[index]) > peak:
                peak = float(speed[index])
                node = int(channel["target"]["node"])
                witness = {"node": node, "bone": glb.nodes[node].get("name"), "times_s": times[index:index+2].tolist(),
                           "quaternions_xyzw": quaternions[index:index+2].tolist()}
    if not channel_count:
        raise ContractError("rotation witness requires at least one actual rotation channel")
    return {"status": "PASS" if peak <= maximum_degrees_per_s else "FAIL",
            "maximum_degrees_per_s": peak, "limit_degrees_per_s": maximum_degrees_per_s, "peak_witness": witness,
            "classification": "serialized per-channel rotation rate; not joint torque or muscle capacity"}


# Added acceptance gates, not substitutes for the unchanged contact/position
# gates. Estimates use a quadratic through the first/last three native samples;
# a duplicated endpoint alone cannot establish cyclic velocity continuity.
CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S = 10.0
CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S = 0.001


def _endpoint_derivative(times: np.ndarray, deltas: np.ndarray) -> np.ndarray:
    if times.shape != (2,) or deltas.shape[0] != 2 or np.any(times == 0):
        raise ContractError("invalid one-sided derivative samples")
    return np.linalg.solve(np.column_stack((times, times * times)), deltas)[0]


def emitted_cyclic_continuity(glb: Glb, *, loop: bool) -> dict:
    """Measure native-time incoming/outgoing velocity on final serialized TRS.

    Quaternion logarithms are relative to each endpoint, use the shortest
    rotation, and are invariant under q/-q encoding. Root displacement is not
    erased: only its derivatives must match across a moving loop. This is a
    sampled engineering witness, not proof of an analytic continuous curve.
    """
    from ..layers.leg_contact_resolve_v3 import _qmul, _qinv, _q_to_rotvec
    if type(loop) is not bool:
        raise ContractError("loop declaration must be boolean")
    if not loop:
        return {"status": "NOT_APPLICABLE", "reason": "one-shot program; entry/exit contracts are separate"}
    angular = linear = 0.0
    witnesses = {"angular": None, "linear": None}
    counts = {"rotation": 0, "translation": 0}
    for animation in glb.document.get("animations", []):
        for channel in animation["channels"]:
            path = channel["target"]["path"]
            if path not in counts:
                continue
            sampler = animation["samplers"][channel["sampler"]]
            if sampler.get("interpolation", "LINEAR") != "LINEAR":
                raise ContractError("continuity witness requires emitted LINEAR channels")
            times = np.asarray(glb.accessor_values(sampler["input"]), dtype=float).reshape(-1)
            values = np.asarray(glb.accessor_values(sampler["output"]), dtype=float)
            width = 4 if path == "rotation" else 3
            if (len(times) < 5 or values.shape != (len(times), width)
                or not np.isfinite(times).all() or not np.isfinite(values).all()
                or np.any(np.diff(times) <= 0)):
                raise ContractError("invalid final cyclic timeline")
            if path == "rotation":
                norms = np.linalg.norm(values, axis=1)
                if np.max(np.abs(norms - 1)) > 1e-4:
                    raise ContractError("invalid quaternion in cyclic witness")
                values /= norms[:, None]
                def deltas(endpoint, indices):
                    inverse = _qinv(tuple(values[endpoint]))
                    return np.array([_q_to_rotvec(_qmul(inverse, tuple(values[i]))) for i in indices])
                start_delta, end_delta = deltas(0, [1, 2]), deltas(-1, [-3, -2])
            else:
                start_delta, end_delta = values[1:3] - values[0], values[-3:-1] - values[-1]
            incoming = _endpoint_derivative(times[-3:-1] - times[-1], end_delta)
            outgoing = _endpoint_derivative(times[1:3] - times[0], start_delta)
            error = float(np.linalg.norm(incoming - outgoing))
            node = int(channel["target"]["node"])
            witness = {"node": node, "bone": glb.nodes[node].get("name"),
                "incoming": incoming.tolist(), "outgoing": outgoing.tolist()}
            if path == "rotation":
                error = math.degrees(error)
                if error > angular:
                    angular, witnesses["angular"] = error, witness
            elif error > linear:
                linear, witnesses["linear"] = error, witness
            counts[path] += 1
    if not all(counts.values()):
        raise ContractError("cyclic witness requires actual rotation and translation channels")
    checks = {"angular_velocity": angular <= CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S,
              "linear_velocity": linear <= CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S}
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "maximum_angular_velocity_seam_degrees_per_s": angular,
        "maximum_linear_velocity_seam_m_per_s": linear,
        "limits": {"angular_degrees_per_s": CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S,
                   "linear_m_per_s": CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S},
        "peak_witnesses": witnesses,
        "classification": "second-order native-time derivatives of final serialized channels; endpoint closure alone is insufficient"}
