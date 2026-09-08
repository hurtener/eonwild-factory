"""Reference-preserving gait adaptation for shared body performance.

The policy scales one baseline-authored kinematic carrier from a locked
reference gait.  It is an art-direction analogy, not a force, work, COM, mass,
or biological model.  Movement programs continue to own their gait timing and
support choreography.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from typing import Any, Mapping

from ..errors import ContractError
from ..planning.grounded_gait import GroundedGait
from ..planning.jaw_response import (
    NeutralJawCalibration,
    load_neutral_jaw_calibration,
)
from .performance import Performance, load_performance


SCHEMA = "eonwild.motion.gait-response-policy.v1"
MODEL = "reference_scaled_excursion_exchange.v1"
NEUTRAL_SCHEMA = "eonwild.motion.neutral-pose-profile.v1"


@dataclass(frozen=True)
class GaitResponsePolicy:
    model: str
    reference_step_period_s: float
    reference_step_length_body_heights: float
    reference_pelvis_excursion_body_heights: float
    reference_pelvis_forward_velocity_modulation_fraction: float

    def __post_init__(self) -> None:
        if self.model != MODEL:
            raise ContractError("unsupported gait-response adaptation model")
        values = (
            self.reference_step_period_s,
            self.reference_step_length_body_heights,
            self.reference_pelvis_excursion_body_heights,
            self.reference_pelvis_forward_velocity_modulation_fraction,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in values
        ):
            raise ContractError("gait-response reference inputs must be finite numeric")
        if (
            self.reference_step_period_s <= 0
            or self.reference_step_length_body_heights == 0
            or self.reference_pelvis_excursion_body_heights <= 0
            or not 0 < self.reference_pelvis_forward_velocity_modulation_fraction < 1
        ):
            raise ContractError(
                "gait-response reference timing, excursion, and coefficient must "
                "be positive and stride must be nonzero"
            )


def load_gait_response_policy(document: Mapping[str, Any]) -> GaitResponsePolicy:
    """Load one strict baseline-owned adaptation policy."""
    if (
        not isinstance(document, Mapping)
        or set(document) != {"schema", "model", "reference"}
        or document.get("schema") != SCHEMA
        or not isinstance(document.get("reference"), Mapping)
    ):
        raise ContractError("unsupported gait-response policy")
    reference = document["reference"]
    required = {
        "step_period_s",
        "step_length_body_heights",
        "pelvis_excursion_body_heights",
        "pelvis_forward_velocity_modulation_fraction",
    }
    if set(reference) != required:
        raise ContractError(
            "gait-response reference is incomplete or has unknown fields"
        )
    return GaitResponsePolicy(
        model=document["model"],
        reference_step_period_s=reference["step_period_s"],
        reference_step_length_body_heights=reference["step_length_body_heights"],
        reference_pelvis_excursion_body_heights=reference[
            "pelvis_excursion_body_heights"
        ],
        reference_pelvis_forward_velocity_modulation_fraction=reference[
            "pelvis_forward_velocity_modulation_fraction"
        ],
    )


def load_neutral_pose_profile(
    document: Mapping[str, Any],
) -> NeutralJawCalibration:
    """Load source-bound neutral-pose calibration independently of style."""
    required = {
        "schema",
        "id",
        "version",
        "classification",
        "neutral_jaw_calibration",
    }
    if (
        not isinstance(document, Mapping)
        or set(document) != required
        or document.get("schema") != NEUTRAL_SCHEMA
        or not isinstance(document.get("id"), str)
        or not document["id"]
        or type(document.get("version")) is not int
        or document["version"] < 1
        or not isinstance(document.get("classification"), str)
        or not document["classification"]
    ):
        raise ContractError("unsupported neutral-pose profile")
    calibration = load_neutral_jaw_calibration(document["neutral_jaw_calibration"])
    return calibration


def assemble_baseline_performance(
    style_document: Mapping[str, Any],
    neutral_document: Mapping[str, Any],
) -> tuple[Performance, dict[str, Any]]:
    """Assemble reusable style with separately bound neutral calibration."""
    parameters = (
        style_document.get("parameters")
        if isinstance(style_document, Mapping)
        else None
    )
    if not isinstance(parameters, Mapping):
        raise ContractError("baseline performance style requires parameters")
    forbidden = {
        "neutral_jaw_calibration",
        "skin_refinement",
        "canonical_support_anchors",
    } & set(parameters)
    if forbidden:
        raise ContractError(
            "baseline performance style cannot contain source-bound calibration "
            "or solver policy"
        )
    performance = load_performance(style_document)
    if performance.pelvis_forward_velocity_modulation_fraction is not None:
        raise ContractError(
            "baseline performance style cannot contain a gait-derived coefficient"
        )
    calibration = load_neutral_pose_profile(neutral_document)
    effective = replace(
        performance,
        neutral_jaw_calibration=calibration,
        skin_refinement=False,
        canonical_support_anchors=None,
    )
    canonical = (
        json.dumps(asdict(effective), indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    receipt = {
        "schema": "eonwild.motion.baseline-performance-resolution.v1",
        "neutral_pose": {
            "id": neutral_document["id"],
            "version": neutral_document["version"],
            "source_geometry_sha256": calibration.source_geometry_sha256,
        },
        "effective_parameters_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    return effective, receipt


def resolve_gait_response(
    performance: Performance,
    gait: GroundedGait,
    policy_document: Mapping[str, Any],
) -> tuple[Performance, dict[str, Any]]:
    """Resolve a reference carrier for the bound steady grounded gait.

    Starts and stops must pass their bound steady gait here.  The transition's
    instantaneous or average root speed is deliberately not an input, so the
    resolved performance is identical at the shared steady interface.
    """
    if not isinstance(performance, Performance):
        raise ContractError("gait-response adaptation requires validated performance")
    if not isinstance(gait, GroundedGait):
        raise ContractError("gait-response adaptation requires a grounded steady gait")
    policy = load_gait_response_policy(policy_document)
    if performance.pelvis_forward_velocity_modulation_fraction is not None:
        raise ContractError(
            "gait-response adaptation conflicts with an explicit performance coefficient"
        )
    reference_coefficient = policy.reference_pelvis_forward_velocity_modulation_fraction
    if gait.pelvis_height_carrier != "stance_vault_proxy":
        raise ContractError("gait-response adaptation requires stance_vault_proxy")

    target_values = (
        gait.step_period_s,
        gait.step_length_body_heights,
        gait.pelvis_excursion_body_heights,
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in target_values
    ):
        raise ContractError("gait-response target inputs must be finite numeric")
    if (
        gait.step_period_s <= 0
        or gait.step_length_body_heights == 0
        or gait.pelvis_excursion_body_heights < 0
    ):
        raise ContractError("gait-response target inputs exceed supported bounds")

    excursion_ratio = (
        gait.pelvis_excursion_body_heights
        / policy.reference_pelvis_excursion_body_heights
    )
    speed_ratio = (
        policy.reference_step_length_body_heights
        * gait.step_period_s
        / (gait.step_length_body_heights * policy.reference_step_period_s)
    )
    coefficient = reference_coefficient * excursion_ratio * speed_ratio**2
    if not math.isfinite(coefficient) or not 0 <= coefficient < 1:
        raise ContractError(
            "resolved gait-response coefficient is outside the performance envelope"
        )

    resolved = replace(
        performance,
        pelvis_forward_velocity_modulation_fraction=coefficient,
    )
    receipt = {
        "schema": "eonwild.motion.gait-response-resolution.v1",
        "policy_schema": SCHEMA,
        "model": policy.model,
        "classification": (
            "reference-scaled kinematic art direction; no COM, force, work, "
            "mass-response, or biological claim"
        ),
        "formula": (
            "k_target = k_reference * (excursion_target / excursion_reference) "
            "* (speed_reference / speed_target)^2; body height cancels within "
            "one bound animal baseline"
        ),
        "reference": {
            "step_period_s": policy.reference_step_period_s,
            "step_length_body_heights": (policy.reference_step_length_body_heights),
            "pelvis_excursion_body_heights": (
                policy.reference_pelvis_excursion_body_heights
            ),
            "pelvis_forward_velocity_modulation_fraction": (reference_coefficient),
        },
        "target": {
            "step_period_s": gait.step_period_s,
            "step_length_body_heights": gait.step_length_body_heights,
            "pelvis_excursion_body_heights": (gait.pelvis_excursion_body_heights),
        },
        "resolved_pelvis_forward_velocity_modulation_fraction": coefficient,
        "transition_policy": (
            "resolve from the bound steady gait; do not use one-shot or "
            "instantaneous transition speed"
        ),
    }
    return resolved, receipt
