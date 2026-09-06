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
    checks, values = {}, {}
    for key, limit in limits.items():
        value = receipt.get(key)
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
        values[key] = float(value) if valid else None
        checks[key] = bool(valid and value <= limit)
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
