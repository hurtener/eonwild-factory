from copy import deepcopy
import hashlib
import math

import pytest

import eonwild_motion.solve.source_motion_query as source_query_module
from eonwild_motion.errors import ContractError
from eonwild_motion.solve.authored_material_contact import (
    AuthoredMaterialContactAdapter,
)
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.grounded_transition_clearance import (
    GroundedTransitionClearanceUnavailable,
    _monotone_floor,
)
from eonwild_motion.solve.source_motion_query import (
    SourceMotionQuery,
    _bounded_authored_joint_height,
    _bounded_authored_reach_height,
)
from eonwild_motion.solve.support_anchors import _digest
from test_constant_skin_targets import _inputs


def _capsule():
    foot = {
        "contact": [True, True, True, False, True],
        "clearance_m": [0.0, 0.0, 0.0, 0.2, 0.0],
        "forward_progress": [0.0, 0.0, 0.0, 0.5, 0.0],
        "foot_pitch_degrees": [0.0, 5.0, 20.0, 10.0, 0.0],
        "swing_phase": [0.0, 0.0, 0.0, 0.5, 0.0],
        "touchdown_index": 0,
        "toe_off_index": 2,
    }
    other = {
        "contact": [True, False, True, True, True],
        "clearance_m": [0.0, 0.2, 0.0, 0.0, 0.0],
        "forward_progress": [0.0, 0.5, 0.0, 0.0, 0.0],
        "foot_pitch_degrees": [20.0, 10.0, 0.0, 5.0, 20.0],
        "swing_phase": [0.0, 0.5, 0.0, 0.0, 0.0],
        "touchdown_index": 2,
        "toe_off_index": 0,
    }
    return {
        "schema": "eonwild.motion.authored-material-path.v1",
        "source_geometry_sha256": hashlib.sha256(b"source").hexdigest(),
        "measured_source_sha256": hashlib.sha256(b"source").hexdigest(),
        "fps": 4.0,
        "interval_count": 4,
        "duration_s": 1.0,
        "feet": {"left": foot, "right": other},
    }


def _query_kwargs(inputs):
    return {
        key: inputs[key]
        for key in (
            "source",
            "semantic_roles",
            "solver_gait",
            "locomotion_gait",
            "plan",
            "up_axis",
            "forward_axis",
            "contact_profile",
            "articulation_profile",
        )
    }


def _policy(maximum_clearance_body_heights=0.125):
    return {
        "schema": "eonwild.motion.authored-material-clearance-policy.v1",
        "id": "heavy-biped-authored-material-clearance",
        "version": 1,
        "model": "body_height_fraction.v1",
        "maximum_clearance_body_heights": maximum_clearance_body_heights,
        "classification": "source_backed_engineering_candidate",
    }


def _build(inputs, capsule=None):
    return AuthoredMaterialContactAdapter.build(
        inputs["query"],
        _capsule() if capsule is None else capsule,
        authored_source=b"source",
        material_clearance_policy=_policy(),
        body_height_m=inputs["query"]._context.body_height,
    )


def test_adapter_applies_material_contact_path_at_keys_and_offgrid():
    inputs = _inputs()
    bare = inputs["query"]
    capsule = _capsule()
    adapter = AuthoredMaterialContactAdapter.build(
        bare,
        capsule,
        authored_source=b"source",
        material_clearance_policy=_policy(),
        body_height_m=bare._context.body_height,
    )
    capsule["feet"]["left"]["clearance_m"][1] = 99.0
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=adapter
    )
    start = query.evaluate(0.0)
    quarter = query.evaluate(float(inputs["plan"]["duration_s"]) * 0.625)
    assert start.status == quarter.status == "AVAILABLE"
    assert start.row["feet"]["left"]["contact"] is True
    assert start.row["feet"]["right"]["contact"] is True
    assert start.row["feet"]["left"]["height_m"] == 0.0
    assert start.row["feet"]["right"]["height_m"] == 0.0
    requested = quarter.row["feet"]["left"]["authored_material_clearance_m"]
    assert requested == pytest.approx(0.1 * adapter._scale)
    assert (
        quarter.row["feet"]["left"][
            "authored_material_achieved_clearance_m"
        ]
        >= requested - 1e-10
    )
    assert (
        quarter.row["feet"]["left"]["authored_material_adaptation_m"]
        >= -1e-10
    )
    assert quarter.row["feet"]["left"]["foot_pitch_degrees"] == pytest.approx(15.0)
    assert quarter.row["feet"]["left"]["swing_phase"] == pytest.approx(0.25)
    assert quarter.row["support_count"] == 1
    assert quarter.row["stage"] == "SINGLE_SUPPORT"
    assert "target_offset_m" not in quarter.row["feet"]["left"]
    assert (
        quarter.material_points["left"][:, 1].min()
        >= (
            query._skin.ground
            + requested
            + 0.0001
            - 1e-10
        )
    )


def test_adapter_binding_names_local_joint_feasibility_semantics():
    inputs = _inputs()
    binding = dict(_build(inputs).binding())
    assert binding["material_effector_resolution"] == (
        "material_floor_and_local_joint_feasibility.v4"
    )
    legacy = {
        **binding,
        "material_effector_resolution": (
            "material_floor_and_local_joint_feasibility.v3"
        ),
    }
    assert _digest(binding) != _digest(legacy)


def test_adapter_recovers_exact_monotone_floor_iteration_exhaustion(monkeypatch):
    inputs = _inputs()
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=_build(inputs)
    )

    def exhausted(measure, ceiling, side, *, target_gap_m, purpose):
        raise GroundedTransitionClearanceUnavailable(
            f"{side} {purpose} material floor did not converge"
        )

    monkeypatch.setattr(source_query_module, "_monotone_floor", exhausted)
    value = query.evaluate(float(inputs["plan"]["duration_s"]) * 0.625)
    assert value.status == "AVAILABLE"
    assert value.row["feet"]["left"]["authored_material_achieved_clearance_m"] >= (
        value.row["feet"]["left"]["authored_material_clearance_m"] - 1e-10
    )


def test_adapter_does_not_reclassify_other_floor_failures(monkeypatch):
    inputs = _inputs()
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=_build(inputs)
    )

    def unavailable(measure, ceiling, side, *, target_gap_m, purpose):
        raise GroundedTransitionClearanceUnavailable(
            f"{side} {purpose} target does not clear the material floor"
        )

    monkeypatch.setattr(source_query_module, "_monotone_floor", unavailable)
    value = query.evaluate(float(inputs["plan"]["duration_s"]) * 0.625)
    assert value.status == "AUTHORED_MATERIAL_CLEARANCE_UNAVAILABLE"
    assert value.reason == (
        "left authored material clearance target does not clear the material floor"
    )


def test_joint_feasibility_recovers_measured_slow_secant_exhaustion():
    target_gap = 0.019172604542864454
    ceiling = 2.106182073161406
    declared_height = 0.019072604542864455
    # Exact requested-height/material-gap pairs from the frozen Allosaurus v4
    # query at t=1.3942162162162162. The secant stays on the lower segment for
    # twenty iterations even though the nearby upper sample is safely above
    # the material floor.
    samples = sorted(
        (
            (0.0, 0.00005996354645053819),
            (0.018955638658452654, 0.0189428147362985),
            (0.019143137135677602, 0.019130313111694126),
            (0.01916213977977479, 0.0191493157454575),
            (0.019169359870648904, 0.01915653583234884),
            (0.01917316261695358, 0.01916033857668435),
            (0.019175509921515694, 0.019162685879919105),
            (0.019177103139392884, 0.01916427909691897),
            (0.01917825536205319, 0.019165431318970635),
            (0.01917912742793532, 0.019166303384330053),
            (0.019179810439447914, 0.01916698639545295),
            (0.019180372254322932, 0.019167548210059473),
            (0.019180877887710446, 0.0191680538432191),
            (0.019181332957759208, 0.019168508912957277),
            (0.019181742520803097, 0.01916891847586592),
            (0.019182111127542596, 0.01916928708236616),
            (0.019182442873608145, 0.019169618828189714),
            (0.01918274144506714, 0.01916991739949587),
            (0.01918542858819808, 0.019224435068839422),
            (0.02106182073161406, 0.021048995680435674),
            (0.2106182073161406, 0.21060536902835617),
            (ceiling, 2.075615112129538),
        )
    )

    def material_gap(height):
        for index, right in enumerate(samples):
            if height <= right[0]:
                if index == 0:
                    return right[1]
                left = samples[index - 1]
                gain = (height - left[0]) / (right[0] - left[0])
                return left[1] + gain * (right[1] - left[1])
        return samples[-1][1]

    def measure(height):
        return material_gap(height), 802, 2e-7, 0.0, 0.0

    with pytest.raises(
        GroundedTransitionClearanceUnavailable, match="did not converge"
    ):
        _monotone_floor(
            lambda height: measure(height)[:2],
            ceiling,
            "left",
            target_gap_m=target_gap,
            purpose="authored material clearance",
        )
    resolved = _bounded_authored_joint_height(
        measure,
        declared_height,
        ceiling,
        "left",
        target_gap_m=target_gap,
    )
    gap, vertex, residual, extension, articulation = measure(resolved)
    assert declared_height < resolved < 0.01918542858819808
    assert vertex == 802
    assert gap >= target_gap
    assert residual <= 0.001
    assert extension <= 0.001
    assert articulation <= 0.01


def test_material_clearance_policy_owns_scale_independently_of_reference_lift():
    inputs = _inputs()
    query = inputs["query"]
    original = query._sample_row

    def exaggerated_reference_lift(time_s, *, apply_clearance):
        row = original(time_s, apply_clearance=apply_clearance)
        for foot in row["feet"].values():
            foot["height_m"] = 99.0
        return row

    query._sample_row = exaggerated_reference_lift
    adapter = _build(inputs)
    expected_maximum = 0.125 * query._context.body_height
    assert adapter._target_maximum_material_clearance_m == pytest.approx(
        expected_maximum
    )
    assert adapter._scale == pytest.approx(expected_maximum / 0.2)
    binding = adapter.binding()
    assert binding["material_clearance_policy"] == _policy()
    assert binding["target_maximum_material_clearance_m"] == pytest.approx(
        expected_maximum
    )


def test_adapter_requires_bound_material_clearance_policy_and_body_height():
    inputs = _inputs()
    query = inputs["query"]
    with pytest.raises(ContractError, match="complete material-clearance policy"):
        AuthoredMaterialContactAdapter.build(
            query,
            _capsule(),
            authored_source=b"source",
            body_height_m=query._context.body_height,
        )
    with pytest.raises(ContractError, match="body height differs"):
        AuthoredMaterialContactAdapter.build(
            query,
            _capsule(),
            authored_source=b"source",
            material_clearance_policy=_policy(),
            body_height_m=query._context.body_height + 0.01,
        )
    malformed = _policy()
    malformed["maximum_clearance_body_heights"] = True
    with pytest.raises(ContractError, match="must be finite numeric"):
        AuthoredMaterialContactAdapter.build(
            query,
            _capsule(),
            authored_source=b"source",
            material_clearance_policy=malformed,
            body_height_m=query._context.body_height,
        )


def test_bounded_reach_accepts_safe_plateau_without_relaxing_residual_gate():
    # This reproduces the real solver's ~13 nm margin reversal inside an
    # already-feasible plateau. Admission remains the exact zero-margin gate.
    def measure(height):
        boundary = 0.08
        if height < boundary:
            return (height - boundary, 112)
        return (0.00099992 + (0.1 - height) * 1.3e-6, 112)

    resolved = _bounded_authored_reach_height(measure, 0.1032517014, "right")
    assert measure(resolved)[0] >= 0.0
    assert measure(math.nextafter(resolved, -math.inf))[0] >= -1e-6


def test_bounded_reach_fails_without_a_safe_bracket():
    with pytest.raises(
        GroundedTransitionClearanceUnavailable, match="no feasible bracket"
    ):
        _bounded_authored_reach_height(lambda height: (-0.01, 7), 0.2, "left")


def test_joint_feasibility_brackets_measured_knee_clamp_coupling():
    target_gap = 0.013291004300055361
    lower = (0.014268489938549051, 0.013265030863688103)
    middle = (0.014294463389953738, 0.013351248213287592)
    upper = (0.014336423246479702, 0.013332964132288506)

    assert middle[0] < upper[0]
    assert middle[1] > upper[1] + 1e-8

    def interpolate(left, right, height):
        gain = (height - left[0]) / (right[0] - left[0])
        return left[1] + gain * (right[1] - left[1])

    def measure(height):
        if height <= lower[0]:
            gap = lower[1] + height - lower[0]
        elif height <= middle[0]:
            gap = interpolate(lower, middle, height)
        elif height <= upper[0]:
            gap = interpolate(middle, upper, height)
        else:
            gap = upper[1] + height - upper[0]
        residual = 1.7683600841332874e-7
        extension = 0.0
        if height >= middle[0]:
            residual = 6.127252780483835e-5
            extension = 6.1363103e-5
        return gap, 398, residual, extension, 0.0

    resolved = _bounded_authored_joint_height(
        measure,
        0.013191004300055362,
        2.106182073161406,
        "right",
        target_gap_m=target_gap,
    )
    gap, vertex, residual, extension, articulation = measure(resolved)
    assert lower[0] < resolved <= upper[0]
    assert vertex == 398
    assert gap >= target_gap
    assert residual <= 0.001
    assert extension <= 0.001
    assert articulation <= 0.01


def test_joint_feasibility_fails_without_safe_interval():
    with pytest.raises(
        GroundedTransitionClearanceUnavailable, match="no safe bracket"
    ):
        _bounded_authored_joint_height(
            lambda height: (height, 398, 0.0011, 0.0, 0.0),
            0.01,
            0.02,
            "right",
            target_gap_m=0.011,
        )


def test_joint_feasibility_rechecks_final_combined_gates():
    ceiling_calls = 0

    def measure(height):
        nonlocal ceiling_calls
        if height == 0.02:
            ceiling_calls += 1
            residual = 0.0 if ceiling_calls == 1 else 0.0011
            return 0.02, 398, residual, 0.0, 0.0
        return height, 398, 0.0011, 0.0, 0.0

    with pytest.raises(
        GroundedTransitionClearanceUnavailable,
        match="final combined gates disagree",
    ):
        _bounded_authored_joint_height(
            measure,
            0.019,
            0.02,
            "right",
            target_gap_m=0.0195,
        )


def test_adapter_rejects_cross_query_reuse_and_internal_tamper():
    inputs = _inputs()
    adapter = _build(inputs)
    wrong = deepcopy(inputs["plan"])
    wrong["performance"]["pelvis_yaw_degrees"] = 1.0
    with pytest.raises(ContractError, match="another source query"):
        SourceMotionQuery(
            **dict(_query_kwargs(inputs), plan=wrong),
            authored_material_contact=adapter,
        )
    adapter._capsule["feet"]["left"]["clearance_m"][0] = 1.0
    with pytest.raises(ContractError, match="differs from its validated values"):
        adapter.validate_for_query(inputs["query"])


def test_adapter_rejects_replaced_derived_path():
    inputs = _inputs()
    adapter = _build(inputs)
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=adapter
    )
    adapter._paths = {**adapter._paths, "left": adapter._paths["right"]}
    with pytest.raises(ContractError, match="derived path differs"):
        adapter.validate_for_query(inputs["query"])
    with pytest.raises(ContractError, match="derived path differs"):
        query.evaluate(0.0)


def test_adapter_rejects_unbound_authored_source_bytes():
    inputs = _inputs()
    with pytest.raises(ContractError, match="source bytes differ"):
        AuthoredMaterialContactAdapter.build(
            inputs["query"],
            _capsule(),
            authored_source=b"another source",
            material_clearance_policy=_policy(),
            body_height_m=inputs["query"]._context.body_height,
        )


def test_constant_skin_law_binds_adapter_and_keeps_pointwise_checks():
    inputs = _inputs()
    adapter = _build(inputs)
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=adapter
    )
    law = CanonicalConstantSkinTargetLaw.build(
        query,
        inputs["provider"],
        **{
            key: inputs[key]
            for key in (
                "source",
                "semantic_roles",
                "solver_gait",
                "locomotion_gait",
                "plan",
                "contact_profile",
                "up_axis",
                "forward_axis",
                "transition",
                "articulation_profile",
            )
        },
    )
    value = law.value(0.0)
    assert value.status in {"AVAILABLE", "CONSTANT_SKIN_TARGET_UNAVAILABLE"}
    adapter._paths["left"].clearance_m  # retained immutable tuple
    adapter._scale = 2.0
    with pytest.raises(ContractError, match="derived path differs"):
        law.value(0.0)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(interval_count=True),
        lambda value: value["feet"]["left"].update(clearance_m=[0.0]),
        lambda value: value["feet"]["left"]["clearance_m"].__setitem__(1, float("nan")),
        lambda value: value["feet"]["left"]["forward_progress"].__setitem__(4, 0.2),
        lambda value: value["feet"]["left"]["contact"].__setitem__(3, True),
        lambda value: value["feet"]["left"]["swing_phase"].__setitem__(3, 0.25),
    ],
)
def test_adapter_fails_closed_on_malformed_capsules(mutation):
    inputs = _inputs()
    capsule = _capsule()
    mutation(capsule)
    with pytest.raises(ContractError):
        AuthoredMaterialContactAdapter.build(
            inputs["query"],
            capsule,
            authored_source=b"source",
            material_clearance_policy=_policy(),
            body_height_m=inputs["query"]._context.body_height,
        )


def test_contact_switches_preserve_zero_height_and_consistent_row_phase():
    inputs = _inputs()
    adapter = _build(inputs)
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=adapter
    )
    duration = float(inputs["plan"]["duration_s"])
    event = duration * 0.5
    before = query.evaluate(event - 1e-8)
    adjacent_float = query.evaluate(math.nextafter(event, -math.inf))
    exact = query.evaluate(event)
    after = query.evaluate(event + 1e-8)
    assert before.row["feet"]["right"]["contact"] is False
    assert adjacent_float.row["feet"]["right"]["contact"] is True
    assert exact.row["feet"]["right"]["contact"] is True
    assert after.row["feet"]["right"]["contact"] is True
    assert before.row["feet"]["right"]["height_m"] < 1e-7
    assert adjacent_float.row["feet"]["right"]["height_m"] == pytest.approx(
        exact.row["feet"]["right"]["height_m"], abs=1e-12
    )
    assert after.row["feet"]["right"]["height_m"] == pytest.approx(
        exact.row["feet"]["right"]["height_m"], abs=1e-7
    )
    for value in (before, adjacent_float, exact, after):
        assert value.row["support_count"] == sum(
            int(value.row["feet"][side]["contact"]) for side in ("left", "right")
        )
        assert value.row["flight"] is (value.row["support_count"] == 0)
    endpoint = query.evaluate(duration)
    assert endpoint.row["feet"]["left"]["touchdown_time_s"] == pytest.approx(
        duration
    )
    assert endpoint.row["feet"]["right"]["touchdown_time_s"] < duration
