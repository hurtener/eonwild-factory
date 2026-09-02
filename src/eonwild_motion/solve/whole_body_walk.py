"""Bounded residual solve for one approved root/in-place walk pair."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from ..errors import ContractError
from ..glb.container import Glb
from ..hashing import sha256_json


REQUIRED_CHAINS = {
    "pelvis",
    "spine",
    "neck_head",
    "tail_proximal",
    "tail_mid",
    "tail_distal",
    "left_upper_leg",
    "left_lower_leg",
    "left_foot",
    "left_toes",
    "right_upper_leg",
    "right_lower_leg",
    "right_foot",
    "right_toes",
    "passive_roles",
}


def _accessor_exact(source: bytes, output: bytes) -> bool:
    left, right = Glb.from_bytes(source), Glb.from_bytes(output)
    if len(left.document.get("accessors", [])) != len(
        right.document.get("accessors", [])
    ):
        return False
    return all(
        left.accessor_bytes(index) == right.accessor_bytes(index)
        for index in range(len(left.document["accessors"]))
    )


def solve_approved_walk(
    *,
    plan: Mapping[str, Any],
    metrics: Mapping[str, Any],
    root_source_bytes: bytes,
    root_output_bytes: bytes,
    in_place_source_bytes: bytes,
    in_place_output_bytes: bytes,
    root_sha256: str,
    in_place_sha256: str,
    tolerances: Mapping[str, Any],
    passive_role_count: int,
) -> dict[str, Any]:
    """Evaluate independently reconstructed planned/realized residuals once."""

    required_metrics = {
        "com_pair_residual",
        "contact_pair_residual",
        "hip_pair_residual",
        "independent_com_oracle",
        "chain_residuals",
        "velocity_pair_residual",
        "acceleration_pair_residual",
        "loop_residual",
        "sample_count",
    }
    if not required_metrics.issubset(metrics):
        raise ContractError("whole-body solve metrics are incomplete")
    if (
        set(tolerances)
        != {"body_relative", "contact_boundary_frames", "loop", "continuity"}
        or tolerances["contact_boundary_frames"] != 1
    ):
        raise ContractError("whole-body solve tolerance contract is malformed")
    body_tolerance = float(tolerances["body_relative"])
    loop_tolerance = float(tolerances["loop"])
    continuity_tolerance = float(tolerances["continuity"])
    chain_residuals = {
        str(key): float(value) for key, value in metrics["chain_residuals"].items()
    }
    if set(chain_residuals) != REQUIRED_CHAINS or passive_role_count < 1:
        raise ContractError(
            "whole-body solve must account for the exact real body chains and passive roles"
        )
    bounds = (
        float(metrics["com_pair_residual"]) <= body_tolerance
        and float(metrics["contact_pair_residual"]) <= body_tolerance
        and float(metrics["hip_pair_residual"]) <= body_tolerance
        and max(chain_residuals.values()) <= body_tolerance
        and float(metrics["velocity_pair_residual"]) <= continuity_tolerance
        and float(metrics["acceleration_pair_residual"]) <= continuity_tolerance
        and float(metrics["loop_residual"]) <= loop_tolerance
        and float(metrics["independent_com_oracle"]) <= body_tolerance
    )
    if not bounds:
        raise ContractError(
            "approved pair exceeds bounded reference-calibration residuals"
        )
    plan_hash = sha256_json(plan)
    outputs = []
    for view, source_data, output_data, source_hash in (
        ("root_motion", root_source_bytes, root_output_bytes, root_sha256),
        ("in_place", in_place_source_bytes, in_place_output_bytes, in_place_sha256),
    ):
        if hashlib.sha256(source_data).hexdigest() != source_hash:
            raise ContractError(f"{view}: admitted source hash drifted before solve")
        output_hash = hashlib.sha256(output_data).hexdigest()
        byte_exact = output_data == source_data and output_hash == source_hash
        accessor_exact = _accessor_exact(source_data, output_data)
        if not byte_exact or not accessor_exact:
            raise ContractError(f"{view}: approved output is not byte/accessor exact")
        outputs.append(
            {
                "view": view,
                "source_sha256": source_hash,
                "output_sha256": output_hash,
                "byte_exact": True,
                "accessor_exact": True,
                "plan_sha256": plan_hash,
            }
        )
    return {
        "schema": "eonwild.motion.v9.whole-body-solve.v1",
        "id": "approved-walk-whole-body-reference-solve",
        "version": 1,
        "plan_id": plan["id"],
        "plan_sha256": plan_hash,
        "invocation_count": 1,
        "algorithm": "bounded_reference_pair_residual_v1",
        "tolerances": dict(tolerances),
        "sample_count": int(metrics["sample_count"]),
        "passive_role_count": passive_role_count,
        "residuals": {
            "com_max": float(metrics["com_pair_residual"]),
            "contact_max": float(metrics["contact_pair_residual"]),
            "hip_max": float(metrics["hip_pair_residual"]),
            "pose_by_chain": chain_residuals,
            "velocity_max": float(metrics["velocity_pair_residual"]),
            "acceleration_max": float(metrics["acceleration_pair_residual"]),
            "loop_max": float(metrics["loop_residual"]),
            "independent_com_oracle_max": float(metrics["independent_com_oracle"]),
        },
        "bounds_satisfied": True,
        "status": "PASS",
        "outputs": outputs,
        "claims": {
            "classification": "reference_calibration",
            "capacity_feasibility": "unevaluated",
            "units": "normalized_dimensionless",
            "physical": False,
            "scientific": False,
            "force": False,
            "torque": False,
            "biological": False,
            "solver_action": "evaluate_bound_approved_pair_without_curve_mutation",
        },
    }
