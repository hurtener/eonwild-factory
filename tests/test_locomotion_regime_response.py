from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path

import pytest
import numpy as np

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.airborne_gait import (
    AirborneGait,
    load_airborne_choreography,
)
from eonwild_motion.planning.gait_transition import GaitTransition, build_transition_plan
from eonwild_motion.solve.locomotion_regime_response import (
    _CARRIER_MAPPING,
    airborne_response_receipt,
    airborne_response_state,
    decorate_airborne_response_plan,
    load_airborne_body_response_policy,
)
from eonwild_motion.solve.performance import Performance
from eonwild_motion.solve.performance import apply_performance
from eonwild_motion.factory.compiler import _airborne_gait_with_shared_articulation
from eonwild_motion.planning.articulation_profile import load_articulation_profile
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from test_v9_airborne_gait import fixture


ROOT = Path(__file__).resolve().parents[1]


def policy_document():
    return {
        "schema": "eonwild.motion.airborne-body-response.v1",
        "model": "explicit_contact_flight_coordination.v1",
        "carrier_mapping": dict(_CARRIER_MAPPING),
        "forward_speed": {
            "model": "reference_scaled_support_exchange.v1",
            "reference_speed_body_heights_per_s": 2.0,
            "reference_pelvis_forward_velocity_modulation_fraction": 0.08,
        },
    }


def state(gait, phase, **changes):
    return airborne_response_state(
        gait,
        phase_s=phase,
        body_height_m=2.0,
        tail_lag_fraction=0.12,
        policy=load_airborne_body_response_policy(policy_document()),
        **changes,
    )


def test_event_polynomials_are_c2_at_every_contact_edge_and_identity_in_flight():
    gait = AirborneGait(step_period_s=0.5, flight_fraction=0.2)
    edge = gait.step_period_s * (1 - gait.flight_fraction)
    h = 1e-5
    for time_s in (0.0, edge, gait.step_period_s, gait.step_period_s + edge):
        center = state(gait, time_s)
        left = state(gait, (time_s - h) % (2 * gait.step_period_s))
        right = state(gait, time_s + h)
        for field in ("lateral_support", "sagittal_support", "load_acceptance"):
            assert abs(getattr(center, field)) < 1e-12
            assert abs((getattr(right, field) - getattr(left, field)) / (2 * h)) < 2e-5
            assert abs((getattr(right, field) - 2 * getattr(center, field) + getattr(left, field)) / h**2) < 2.0
    flight = state(gait, 0.45)
    assert flight.support_count == 0
    assert flight.lateral_support == flight.sagittal_support == flight.load_acceptance == 0
    assert flight.pelvis_forward_displacement_m == flight.pelvis_forward_velocity_mps == 0


def test_per_limb_early_load_is_distinct_from_late_exchange():
    gait = AirborneGait(step_period_s=0.5, flight_fraction=0.1)
    samples = [state(gait, i / 2000) for i in range(2001)]
    assert max(abs(row.lateral_support) for row in samples) <= 1 + 1e-12
    assert max(abs(row.sagittal_support) for row in samples) <= 1 + 1e-12
    assert max(row.load_acceptance for row in samples) <= 1 + 1e-12
    # The admitted airborne topology has a positive flight interval and hence
    # never overlaps two stance intervals. The early pulse is nevertheless
    # formed limb-by-limb: it is positive in early stance and exactly zero in
    # the same limb's negative late-stance exchange.
    assert max(row.support_count for row in samples) == 1
    assert any(row.load_acceptance > 0.49 for row in samples)
    assert any(
        row.sagittal_support < -0.49 and row.load_acceptance == 0
        for row in samples
    )


def test_integrated_forward_exchange_has_zero_stance_edges_and_exact_derivative():
    gait = AirborneGait(step_period_s=0.5, flight_fraction=0.2, step_length_body_heights=1.0)
    stance = gait.step_period_s * (1 - gait.flight_fraction)
    for time_s in (0.0, stance, gait.step_period_s, gait.step_period_s + stance, 2 * gait.step_period_s):
        assert abs(state(gait, time_s).pelvis_forward_displacement_m) < 1e-12
    for time_s in (0.11, 0.29, 0.61, 0.79):
        h = 1e-6
        numerical = (
            state(gait, time_s + h).pelvis_forward_displacement_m
            - state(gait, time_s - h).pelvis_forward_displacement_m
        ) / (2 * h)
        assert numerical == pytest.approx(
            state(gait, time_s).pelvis_forward_velocity_mps, abs=2e-9
        )


def test_transition_velocity_uses_complete_product_rule():
    gait = AirborneGait(step_period_s=0.5, flight_fraction=0.2, step_length_body_heights=1.0)
    time_s = 0.11
    gain = 0.4
    gain_derivative = 0.7
    row = state(
        gait,
        time_s,
        performance_gain=gain,
        performance_gain_derivative_per_s=gain_derivative,
    )
    h = 1e-6
    plus = state(
        gait,
        time_s + h,
        performance_gain=gain + gain_derivative * h,
        performance_gain_derivative_per_s=gain_derivative,
    )
    minus = state(
        gait,
        time_s - h,
        performance_gain=gain - gain_derivative * h,
        performance_gain_derivative_per_s=gain_derivative,
    )
    assert (plus.pelvis_forward_displacement_m - minus.pelvis_forward_displacement_m) / (2 * h) == pytest.approx(
        row.pelvis_forward_velocity_mps, abs=2e-9
    )
    without_product = gain * state(gait, time_s).pelvis_forward_velocity_mps
    assert abs(row.pelvis_forward_velocity_mps - without_product) > 1e-5


def test_transition_plan_can_record_exact_gain_derivative_without_legacy_change():
    gait = AirborneGait(cycles=1, sample_hz=24)
    transition = GaitTransition("start", ramp_cycles=1, sample_hz=24)
    legacy = build_transition_plan(transition, gait, 2.0)
    bound = build_transition_plan(
        transition,
        gait,
        2.0,
        include_performance_gain_derivative=True,
    )
    assert all("performance_gain_derivative_per_s" not in row for row in legacy["samples"])
    assert [
        {key: value for key, value in row.items() if key != "performance_gain_derivative_per_s"}
        for row in bound["samples"]
    ] == legacy["samples"]
    assert any(
        abs(row["performance_gain_derivative_per_s"]) > 0
        for row in bound["samples"]
    )


def test_lag_is_periodic_and_native_or_offgrid_evaluation_is_history_free():
    gait = AirborneGait(step_period_s=0.5, flight_fraction=0.2)
    a = state(gait, 0.1234567)
    b = state(gait, 1.1234567)
    assert a.lagged_lateral_support == pytest.approx(b.lagged_lateral_support, abs=1e-14)
    assert state(gait, 0.1234567).lagged_lateral_support == a.lagged_lateral_support


def test_policy_is_closed_and_resolution_rejects_invalid_target():
    document = policy_document()
    document["carrier_mapping"].pop("pelvis_roll")
    with pytest.raises(ContractError, match="carrier mapping"):
        load_airborne_body_response_policy(document)
    policy = load_airborne_body_response_policy(policy_document())
    with pytest.raises(ContractError, match="exceeds"):
        airborne_response_receipt(
            replace(AirborneGait(), step_length_body_heights=0.01), policy
        )


def test_returned_policy_and_receipt_are_detached():
    document = policy_document()
    policy = load_airborne_body_response_policy(document)
    document["carrier_mapping"]["pelvis_sway"] = "changed"
    assert policy.carrier_mapping["pelvis_sway"] == "bilateral_support_difference"
    receipt = airborne_response_receipt(AirborneGait(), policy)
    receipt["carrier_mapping"]["pelvis_sway"] = "changed"
    assert policy.carrier_mapping["pelvis_sway"] == "bilateral_support_difference"


def test_plan_decoration_binds_exact_gait_policy_and_detaches_inputs():
    gait = AirborneGait(cycles=1, sample_hz=24)
    from eonwild_motion.planning.airborne_gait import build_airborne_plan

    plan = build_airborne_plan(gait, 2.0)
    document = policy_document()
    decorated = decorate_airborne_response_plan(
        plan, Performance(), gait, document
    )
    document["forward_speed"][
        "reference_pelvis_forward_velocity_modulation_fraction"
    ] = 0.9
    plan["parameters"]["step_period_s"] = 9.0
    assert decorated["parameters"]["step_period_s"] == gait.step_period_s
    assert decorated["airborne_body_response"]["resolution"]["model"] == (
        "explicit_contact_flight_coordination.v1"
    )
    with pytest.raises(ContractError, match="differs"):
        decorate_airborne_response_plan(plan, Performance(), gait, policy_document())


def test_opt_in_response_reaches_actual_pose_application_and_rejects_receipt_tamper(
    monkeypatch,
):
    source, roles = fixture("airborne_response_", upper_body=True)
    gait = AirborneGait(cycles=1, sample_hz=24)
    from eonwild_motion.planning.airborne_gait import build_airborne_plan

    performance = Performance(
        support_directed_pelvis_carrier=True,
        support_timed_sagittal_carrier=True,
        support_timed_load_acceptance_carrier=True,
        pelvis_support_pitch_degrees=1.0,
        upper_trunk_counterpitch_degrees=0.5,
        tail_counterpitch_degrees=0.5,
        neck_counterpitch_degrees=0.25,
        pelvis_load_acceptance_body_heights=0.005,
        upper_trunk_load_acceptance_pitch_degrees=0.2,
        pelvis_forward_velocity_modulation_fraction=0.1,
        support_timed_axial_carrier=True,
        center_tail=True,
        skin_refinement=False,
    )
    plan = decorate_airborne_response_plan(
        build_airborne_plan(gait, 2.0), performance, gait, policy_document()
    )
    row = next(
        sample for sample in plan["samples"]
        if 0 < sample["time_s"] < gait.step_period_s * (1 - gait.flight_fraction) / 2
    )
    translations = list(source.rest_translation)
    rotations = list(source.rest_rotation)
    scales = list(source.rest_scale)
    before = np.asarray(translations[source.name_to_node[roles["pelvis"]]], dtype=float)
    import eonwild_motion.solve.performance as performance_module

    monkeypatch.setattr(
        performance_module,
        "_sagittal_body_chains",
        lambda *_args: {
            "trunk": [source.name_to_node[roles["chest"]]],
            "tail": [source.name_to_node[name] for name in roles["tail"]],
            "neck": [source.name_to_node[name] for name in roles["neck"]],
        },
    )
    monkeypatch.setattr(
        performance_module, "_counterroll_trunk_names", lambda _roles: [roles["chest"]]
    )

    def legacy_carrier_must_not_run(*_args, **_kwargs):
        raise AssertionError("legacy carrier overrode the v2 airborne response")

    monkeypatch.setattr(
        performance_module, "_support_timed_sagittal_pulse", legacy_carrier_must_not_run
    )
    monkeypatch.setattr(
        performance_module,
        "_support_timed_load_acceptance_pulse",
        legacy_carrier_must_not_run,
    )
    monkeypatch.setattr(
        performance_module,
        "_support_timed_axial_clock",
        legacy_carrier_must_not_run,
    )
    apply_performance(
        source,
        translations,
        rotations,
        scales,
        _world_matrices(source, translations, rotations, scales),
        roles,
        plan,
        row,
        np.asarray((0.0, 1.0, 0.0)),
        np.asarray((0.0, 0.0, 1.0)),
    )
    after = np.asarray(translations[source.name_to_node[roles["pelvis"]]], dtype=float)
    assert np.linalg.norm(after - before) > 1e-6
    hip_left = source.name_to_node[roles["legs"]["left"]["contactChain"][0]]
    hip_right = source.name_to_node[roles["legs"]["right"]["contactChain"][0]]
    worlds = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale
    )
    lateral = np.asarray((1.0, 0.0, 0.0))
    left_sign = -math.copysign(
        1.0,
        float(
            (
                np.asarray(worlds[hip_right])[:3, 3]
                - np.asarray(worlds[hip_left])[:3, 3]
            )
            @ lateral
        ),
    )
    assert float((after - before) @ lateral) * left_sign > 0
    plan["airborne_body_response"]["resolution"][
        "resolved_pelvis_forward_velocity_modulation_fraction"
    ] = 0.9
    with pytest.raises(ContractError, match="inconsistent"):
        apply_performance(
            source,
            list(source.rest_translation),
            list(source.rest_rotation),
            list(source.rest_scale),
            _world_matrices(
                source,
                source.rest_translation,
                source.rest_rotation,
                source.rest_scale,
            ),
            roles,
            plan,
            row,
            np.asarray((0.0, 1.0, 0.0)),
            np.asarray((0.0, 0.0, 1.0)),
        )


@pytest.mark.parametrize("bad", [math.nan, math.inf, True, -1.0])
def test_response_rejects_nonfinite_or_invalid_clock_inputs(bad):
    gait = AirborneGait()
    with pytest.raises(ContractError):
        state(gait, bad)


def test_v2_choreography_excludes_body_style_rom_and_source_calibration():
    document = {
        "schema": "eonwild.motion.airborne-choreography.v1",
        "program": "airborne_gait",
        "classification": "portable foot-event choreography",
        "parameters": {
            "step_period_s": 0.5,
            "flight_fraction": 0.2,
            "step_length_body_heights": 1.0,
            "touchdown_reach_body_heights": 0.4,
            "swing_clearance_body_heights": 0.15,
            "flight_height_body_heights": 0.05,
            "cycles": 1,
            "sample_hz": 120,
        },
    }
    gait = load_airborne_choreography(document)
    assert gait.pelvis_compression_body_heights == 0
    assert gait.pelvis_crouch_body_heights == 0
    for field, value in (
        ("chest_response_gain_degrees", 2.0),
        ("body_response_time_s", 0.09),
        ("knee_max_interior_degrees", 165.0),
        ("stance_ground_offset_left_m", 0.01),
    ):
        changed = {
            **document,
            "parameters": {**document["parameters"], field: value},
        }
        with pytest.raises(ContractError, match="body-owned"):
            load_airborne_choreography(changed)


def test_airborne_solver_scalars_derive_from_shared_closed_rom_profile():
    articulation = load_articulation_profile(
        json.loads(
            (ROOT / "catalog/articulation/heavy-biped.tarbosaurus-adult-walk.v1.json")
            .read_text()
        )
    )
    gait = _airborne_gait_with_shared_articulation(AirborneGait(), articulation)
    assert gait.knee_max_interior_degrees == math.nextafter(180.0, -math.inf)
    assert gait.ankle_max_interior_degrees == math.nextafter(180.0, -math.inf)
    assert gait.knee_min_interior_degrees == min(
        articulation.support["knee_interior_degrees"].hard_min_deg,
        articulation.swing["knee_interior_degrees"].hard_min_deg,
    )
