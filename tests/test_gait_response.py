"""Focused checks for baseline-owned, gait-derived body response."""

from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import GroundedGait
from eonwild_motion.solve.gait_response import (
    MODEL,
    assemble_baseline_performance,
    resolve_gait_response,
)
from eonwild_motion.solve.performance import Performance, load_performance


ROOT = Path(__file__).resolve().parents[1]


REFERENCE_COEFFICIENT = 0.14519967609352594
POLICY = {
    "schema": "eonwild.motion.gait-response-policy.v1",
    "model": MODEL,
    "reference": {
        "step_period_s": 1.23,
        "step_length_body_heights": 0.6,
        "pelvis_excursion_body_heights": 0.016,
        "pelvis_forward_velocity_modulation_fraction": REFERENCE_COEFFICIENT,
    },
}


def performance() -> Performance:
    return Performance()


def gait(**changes) -> GroundedGait:
    values = {
        "step_period_s": 1.23,
        "step_length_body_heights": 0.6,
        "pelvis_excursion_body_heights": 0.016,
        "pelvis_height_carrier": "stance_vault_proxy",
    }
    values.update(changes)
    return GroundedGait(**values)


def test_reference_gait_preserves_accepted_coefficient_exactly():
    before = performance()
    resolved, receipt = resolve_gait_response(before, gait(), POLICY)
    assert resolved.pelvis_forward_velocity_modulation_fraction == (
        REFERENCE_COEFFICIENT
    )
    assert {
        key: value
        for key, value in asdict(before).items()
        if key != "pelvis_forward_velocity_modulation_fraction"
    } == {
        key: value
        for key, value in asdict(resolved).items()
        if key != "pelvis_forward_velocity_modulation_fraction"
    }
    assert (
        receipt["reference"]["pelvis_forward_velocity_modulation_fraction"]
        == REFERENCE_COEFFICIENT
    )
    assert receipt["resolved_pelvis_forward_velocity_modulation_fraction"] == (
        REFERENCE_COEFFICIENT
    )


def test_fast_gait_is_derived_from_cadence_without_mutating_baseline():
    before = performance()
    resolved, receipt = resolve_gait_response(before, gait(step_period_s=0.8), POLICY)
    expected = REFERENCE_COEFFICIENT * (0.8 / 1.23) ** 2
    assert resolved.pelvis_forward_velocity_modulation_fraction == pytest.approx(
        expected, abs=1e-16
    )
    assert expected == pytest.approx(0.06142361867926274, abs=1e-16)
    assert before.pelvis_forward_velocity_modulation_fraction is None
    assert receipt["target"] == {
        "step_period_s": 0.8,
        "step_length_body_heights": 0.6,
        "pelvis_excursion_body_heights": 0.016,
    }


def test_response_uses_speed_magnitude_and_excursion_ratio():
    forward, _ = resolve_gait_response(
        performance(),
        gait(
            step_period_s=0.8,
            step_length_body_heights=0.3,
            pelvis_excursion_body_heights=0.008,
        ),
        POLICY,
    )
    reverse, _ = resolve_gait_response(
        performance(),
        gait(
            step_period_s=0.8,
            step_length_body_heights=-0.3,
            pelvis_excursion_body_heights=0.008,
        ),
        POLICY,
    )
    expected = REFERENCE_COEFFICIENT * 0.5 * (0.6 * 0.8 / (0.3 * 1.23)) ** 2
    assert forward.pelvis_forward_velocity_modulation_fraction == pytest.approx(
        expected, abs=1e-16
    )
    assert reverse.pelvis_forward_velocity_modulation_fraction == pytest.approx(
        expected, abs=1e-16
    )


@pytest.mark.parametrize(
    "document",
    [
        None,
        {},
        {**POLICY, "unknown": 1},
        {**POLICY, "schema": "wrong"},
        {**POLICY, "model": "gravity"},
        {**POLICY, "reference": {}},
        {
            **POLICY,
            "reference": {**POLICY["reference"], "step_period_s": True},
        },
        {
            **POLICY,
            "reference": {**POLICY["reference"], "step_period_s": math.inf},
        },
        {
            **POLICY,
            "reference": {
                **POLICY["reference"],
                "step_length_body_heights": 0,
            },
        },
        {
            **POLICY,
            "reference": {
                **POLICY["reference"],
                "pelvis_excursion_body_heights": -0.01,
            },
        },
    ],
)
def test_policy_rejects_malformed_or_unbounded_reference(document):
    with pytest.raises(ContractError):
        resolve_gait_response(performance(), gait(), document)


def test_policy_rejects_unsupported_or_unbound_inputs():
    with pytest.raises(ContractError, match="validated performance"):
        resolve_gait_response(object(), gait(), POLICY)
    with pytest.raises(ContractError, match="grounded steady gait"):
        resolve_gait_response(performance(), AirborneGait(), POLICY)
    with pytest.raises(ContractError, match="explicit performance coefficient"):
        resolve_gait_response(
            Performance(
                pelvis_forward_velocity_modulation_fraction=(REFERENCE_COEFFICIENT)
            ),
            gait(),
            POLICY,
        )
    with pytest.raises(ContractError, match="stance_vault_proxy"):
        resolve_gait_response(performance(), gait(pelvis_height_carrier=None), POLICY)


def test_policy_fails_closed_when_target_exceeds_performance_envelope():
    with pytest.raises(ContractError, match="outside the performance envelope"):
        resolve_gait_response(
            performance(),
            gait(
                step_period_s=10.0,
                step_length_body_heights=0.01,
                pelvis_excursion_body_heights=0.25,
            ),
            POLICY,
        )


def test_split_style_and_neutral_profile_reconstruct_v10_exactly():
    style = json.loads(
        (
            ROOT / "catalog/performance/heavy-biped.grounded-weight-transfer.v1.json"
        ).read_text()
    )
    neutral = json.loads(
        (
            ROOT / "catalog/calibration/tarbosaurus-pin-552-1-adult-neutral.v1.json"
        ).read_text()
    )
    assembled, receipt = assemble_baseline_performance(style, neutral)
    resolved, _ = resolve_gait_response(assembled, gait(), POLICY)
    historical = load_performance(
        json.loads(
            (
                ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v9.json"
            ).read_text()
        )
    )
    assert asdict(resolved) == asdict(historical)
    assert receipt == {
        "schema": "eonwild.motion.baseline-performance-resolution.v1",
        "neutral_pose": {
            "id": neutral["id"],
            "version": neutral["version"],
            "source_geometry_sha256": neutral["neutral_jaw_calibration"][
                "source_geometry_sha256"
            ],
        },
        "effective_parameters_sha256": (
            "42f811824e3d00917a04f5d2b2d4a1c7dc8e248502a57699ae5841c93bf3e988"
        ),
    }


def test_split_profile_rejects_mixed_or_conflicting_calibration():
    style = json.loads(
        (
            ROOT / "catalog/performance/heavy-biped.grounded-weight-transfer.v1.json"
        ).read_text()
    )
    neutral = json.loads(
        (
            ROOT / "catalog/calibration/tarbosaurus-pin-552-1-adult-neutral.v1.json"
        ).read_text()
    )
    mixed = json.loads(json.dumps(style))
    mixed["parameters"]["neutral_jaw_calibration"] = neutral["neutral_jaw_calibration"]
    with pytest.raises(ContractError, match="cannot contain source-bound"):
        assemble_baseline_performance(mixed, neutral)
    malformed = json.loads(json.dumps(neutral))
    malformed["source_geometry_sha256"] = "0" * 64
    with pytest.raises(ContractError, match="unsupported neutral-pose profile"):
        assemble_baseline_performance(style, malformed)
