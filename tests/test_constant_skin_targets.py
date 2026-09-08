from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import apply_uniform_geometry_scale
from eonwild_motion.planning.articulation_profile import load_articulation_profile
from eonwild_motion.planning.gait_transition import (
    build_transition_plan,
    load_gait_transition,
)
from eonwild_motion.planning.grounded_gait import build_grounded_plan
from eonwild_motion.solve.constant_skin_targets import (
    CanonicalConstantSkinTargetLaw,
    ConstantSkinTargetUnavailable,
)
from eonwild_motion.solve.airborne_gait import _world_matrices
from eonwild_motion.solve.performance import Performance, decorate_plan
from eonwild_motion.solve.skin_rig import SkinRig
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
from test_canonical_support_anchors import _bound_walk, _provider


ROOT = Path(__file__).resolve().parents[1]


def _inputs(*, performance=None, articulation_profile=None, contact=None):
    source, roles, default_contact, gait, solver, steady, forward = _bound_walk()
    contact = default_contact if contact is None else contact
    plan = decorate_plan(
        build_grounded_plan(gait, float(steady["body_height_m"])),
        performance or Performance(canonical_support_anchors=True),
    )
    provider = _provider(source, roles, contact, gait, solver, plan, forward)
    query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=gait,
        plan=plan,
        up_axis=(0, 1, 0),
        forward_axis=forward,
        contact_profile=contact,
        articulation_profile=articulation_profile,
    )
    return {
        "source": source,
        "semantic_roles": roles,
        "contact_profile": contact,
        "locomotion_gait": gait,
        "solver_gait": solver,
        "plan": plan,
        "provider": provider,
        "query": query,
        "up_axis": (0, 1, 0),
        "forward_axis": forward,
        "transition": None,
        "articulation_profile": articulation_profile,
    }


def _build(inputs):
    values = dict(inputs)
    query = values.pop("query")
    provider = values.pop("provider")
    return CanonicalConstantSkinTargetLaw.build(query, provider, **values)


@pytest.fixture(scope="module")
def law_and_inputs():
    inputs = _inputs()
    return _build(inputs), inputs


def test_constant_law_returns_checked_pose_and_is_history_independent(law_and_inputs):
    law, _ = law_and_inputs
    first = law.value(0.2)
    later = law.value(0.6)
    repeat = law.value(0.2)
    assert first.status == later.status == repeat.status == "AVAILABLE"
    assert first.pose.maximum_unreachable_extension_m <= 0.001
    assert "GLOBAL_C1_AUTHORITY_UNAVAILABLE" in first.branch_witness["status"]
    for side in ("left", "right"):
        assert first.corrections_m[side].flags.writeable is False
        assert np.array_equal(first.corrections_m[side], repeat.corrections_m[side])
        if first.observations[side]["loaded"]:
            assert first.observations[side]["residual_m"] <= 0.0002
        else:
            assert first.observations[side]["minimum_gap_m"] >= 0.0001


def test_batch_matches_pointwise_and_returns_independent_owned_values(law_and_inputs):
    law, _ = law_and_inputs
    times = (0.2, 0.6, 0.2)
    batch = law.values(times)
    pointwise = tuple(law.value(time_s) for time_s in times)
    assert isinstance(batch, tuple)
    for batched, single in zip(batch, pointwise):
        assert batched.status == single.status == "AVAILABLE"
        assert batched.time_s == single.time_s
        assert batched.row == single.row
        assert batched.pose.translations == single.pose.translations
        assert batched.pose.rotations == single.pose.rotations
        for side in ("left", "right"):
            assert np.array_equal(batched.corrections_m[side], single.corrections_m[side])
    batch[0].pose.translations[0] = (999.0, 999.0, 999.0)
    batch[0].corrections_m["left"].setflags(write=True)
    batch[0].corrections_m["left"][0] += 1.0
    assert batch[2].pose.translations[0] != (999.0, 999.0, 999.0)
    assert not np.array_equal(batch[0].corrections_m["left"], batch[2].corrections_m["left"])


def test_owned_fastpath_matches_prior_corrected_solve_at_keys_boundaries_and_offgrid(
    law_and_inputs, monkeypatch
):
    law, inputs = law_and_inputs
    times = (
        float(inputs["plan"]["samples"][0]["time_s"]),
        float(inputs["plan"]["samples"][7]["time_s"]),
        0.2,
        float(inputs["plan"]["samples"][-1]["time_s"]),
    )
    fast = tuple(law.value(time_s) for time_s in times)
    original = law._observe

    def injected(query, provider, skin, side, time_s, constants):
        return original(query, provider, skin, side, time_s, constants)

    monkeypatch.setattr(law, "_observe", injected)
    prior = tuple(law.value(time_s) for time_s in times)
    for current, previous in zip(fast, prior):
        assert current.status == previous.status
        assert current.row == previous.row
        assert current.pose.translations == previous.pose.translations
        assert current.pose.rotations == previous.pose.rotations
        assert current.observations == previous.observations
        current_worlds = np.asarray(
            _world_matrices(
                law._query._source,
                current.pose.translations,
                current.pose.rotations,
                law._query.context.base_s,
            )
        )
        previous_worlds = np.asarray(
            _world_matrices(
                law._query._source,
                previous.pose.translations,
                previous.pose.rotations,
                law._query.context.base_s,
            )
        )
        for side in ("left", "right"):
            assert np.array_equal(
                law._patch(law._skin, current_worlds, side),
                law._patch(law._skin, previous_worlds, side),
            )


def test_default_law_value_uses_one_row_solve(law_and_inputs, monkeypatch):
    law, _ = law_and_inputs
    import eonwild_motion.solve.source_motion_query as source_query_module
    original = source_query_module.solve_airborne_plan_sample
    calls = []

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(source_query_module, "solve_airborne_plan_sample", counted)
    assert law.value(0.2).status == "AVAILABLE"
    assert len(calls) == 1


def test_query_subclass_evaluate_override_retains_prior_fallback():
    inputs = _inputs()

    class ObservedQuery(SourceMotionQuery):
        calls = 0

        def evaluate(self, time_s, *, side="value"):
            type(self).calls += 1
            return super().evaluate(time_s, side=side)

    query = ObservedQuery(
        inputs["source"],
        semantic_roles=inputs["semantic_roles"],
        solver_gait=inputs["solver_gait"],
        locomotion_gait=inputs["locomotion_gait"],
        transition=inputs["transition"],
        plan=inputs["plan"],
        up_axis=inputs["up_axis"],
        forward_axis=inputs["forward_axis"],
        articulation_profile=inputs["articulation_profile"],
        contact_profile=inputs["contact_profile"],
    )
    law = _build({**inputs, "query": query})
    ObservedQuery.calls = 0
    assert law.value(0.2).status == "AVAILABLE"
    assert ObservedQuery.calls == 2


def test_injected_query_evaluate_retains_prior_fallback(law_and_inputs, monkeypatch):
    law, _ = law_and_inputs
    original = law._query.evaluate
    calls = []

    def observed(time_s, *, side="value"):
        calls.append((time_s, side))
        return original(time_s, side=side)

    monkeypatch.setattr(law._query, "evaluate", observed)
    assert law.value(0.2).status == "AVAILABLE"
    assert calls == [(0.2, "value"), (0.2, "value")]


def test_actual_query_yaw_contact_and_articulation_are_bound_to_provider():
    admitted = _inputs()
    wrong_yaw = _inputs(
        performance=Performance(
            canonical_support_anchors=True, pelvis_yaw_degrees=3.0
        )
    )["query"]
    with pytest.raises(ContractError, match="consuming request"):
        CanonicalConstantSkinTargetLaw.build(
            wrong_yaw,
            admitted["provider"],
            **{
                key: value
                for key, value in admitted.items()
                if key not in {"query", "provider"}
            },
        )

    changed_contact = deepcopy(admitted["contact_profile"])
    feet = changed_contact["geometry"]["feet"]["left"]
    feet["sole_joints"], feet["toe_joints"] = (
        feet["toe_joints"],
        feet["sole_joints"],
    )
    wrong_contact = SourceMotionQuery(
        admitted["source"],
        semantic_roles=admitted["semantic_roles"],
        solver_gait=admitted["solver_gait"],
        locomotion_gait=admitted["locomotion_gait"],
        plan=admitted["plan"],
        up_axis=admitted["up_axis"],
        forward_axis=admitted["forward_axis"],
        contact_profile=changed_contact,
    )
    with pytest.raises(ContractError, match="consuming request|material correspondence"):
        CanonicalConstantSkinTargetLaw.build(
            wrong_contact,
            admitted["provider"],
            **{
                key: value
                for key, value in admitted.items()
                if key not in {"query", "provider"}
            },
        )

    profile = load_articulation_profile(
        json.loads(
            (
                ROOT
                / "catalog/articulation/heavy-biped.tarbosaurus-adult-walk.v1.json"
            ).read_text()
        )
    )
    wrong_articulation = SourceMotionQuery(
        admitted["source"],
        semantic_roles=admitted["semantic_roles"],
        solver_gait=admitted["solver_gait"],
        locomotion_gait=admitted["locomotion_gait"],
        plan=admitted["plan"],
        up_axis=admitted["up_axis"],
        forward_axis=admitted["forward_axis"],
        contact_profile=admitted["contact_profile"],
        articulation_profile=profile,
    )
    with pytest.raises(ContractError, match="consuming request"):
        CanonicalConstantSkinTargetLaw.build(
            wrong_articulation,
            admitted["provider"],
            **{
                key: value
                for key, value in admitted.items()
                if key not in {"query", "provider"}
            },
        )


def test_current_query_uniform_scale_mutation_fails_closed():
    inputs = _inputs()
    law = _build(inputs)
    apply_uniform_geometry_scale(inputs["query"]._source, 1.01)
    with pytest.raises(ContractError, match="query differs"):
        law.value(0.2)


def test_start_and_steady_share_canonical_sustained_constants():
    steady_inputs = _inputs()
    steady_law = _build(steady_inputs)
    transition = load_gait_transition(
        json.loads((ROOT / "catalog/programs/heavy-biped.start.v2.json").read_text())
    )
    plan = decorate_plan(
        build_transition_plan(
            transition,
            steady_inputs["locomotion_gait"],
            float(steady_inputs["plan"]["body_height_m"]),
        ),
        Performance(canonical_support_anchors=True),
    )
    provider = _provider(
        steady_inputs["source"],
        steady_inputs["semantic_roles"],
        steady_inputs["contact_profile"],
        steady_inputs["locomotion_gait"],
        steady_inputs["solver_gait"],
        plan,
        steady_inputs["forward_axis"],
        transition,
    )
    query = SourceMotionQuery(
        steady_inputs["source"],
        semantic_roles=steady_inputs["semantic_roles"],
        solver_gait=steady_inputs["solver_gait"],
        locomotion_gait=steady_inputs["locomotion_gait"],
        transition=transition,
        plan=plan,
        up_axis=steady_inputs["up_axis"],
        forward_axis=steady_inputs["forward_axis"],
        contact_profile=steady_inputs["contact_profile"],
    )
    transition_inputs = {
        **steady_inputs,
        "plan": plan,
        "provider": provider,
        "query": query,
        "transition": transition,
    }
    start_law = _build(transition_inputs)
    for side in ("left", "right"):
        assert np.array_equal(
            start_law.value(0.0).corrections_m[side],
            steady_law.value(0.0).corrections_m[side],
        )


def test_returned_arrays_pose_and_nested_diagnostics_are_detached(law_and_inputs):
    law, _ = law_and_inputs
    value = law.value(0.2)
    baseline = value.corrections_m["left"].copy()
    value.corrections_m["left"].setflags(write=True)
    value.corrections_m["left"][1] += 0.01
    value.pose.translations[0] = (999.0, 999.0, 999.0)
    with pytest.raises(TypeError):
        value.row["feet"]["left"]["contact"] = False
    with pytest.raises(TypeError):
        value.observations["left"]["loaded"] = False
    repeat = law.value(0.2)
    assert np.array_equal(repeat.corrections_m["left"], baseline)
    assert repeat.pose.translations[0] != (999.0, 999.0, 999.0)


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        ("loaded_residual", "loaded residual"),
        ("clearance", "swing clearance"),
        ("ik", "foot target residual"),
        ("extension", "unreachable IK extension"),
        ("rom", "articulation envelope"),
        ("nonfinite", "non-finite"),
    ],
)
def test_pointwise_failures_return_typed_unavailable(
    law_and_inputs, monkeypatch, mode, reason
):
    law, _ = law_and_inputs
    original = law._observe

    def failed(query, provider, skin, side, time_s, constants):
        result = original(query, provider, skin, side, time_s, constants)
        if side != "right":
            return result
        if mode == "loaded_residual":
            result["loaded"] = True
            result["required_correction_m"] = np.array([0.01, 0.0, 0.0])
        elif mode == "clearance":
            result["loaded"] = False
            result["gap_m"] = -0.001
        elif mode == "ik":
            result["pose"].feet[side]["foot_target_residual_m"] = 0.01
        elif mode == "extension":
            result["pose"] = replace(
                result["pose"], maximum_unreachable_extension_m=0.01
            )
        elif mode == "rom":
            result["pose"].feet[side][
                "articulation_envelope_violation_degrees"
            ] = 1.0
        else:
            result["gap_m"] = float("nan")
        return result

    monkeypatch.setattr(law, "_observe", failed)
    value = law.value(0.37)
    assert isinstance(value, ConstantSkinTargetUnavailable)
    assert value.status == "UNAVAILABLE"
    assert reason in value.reason
    assert "GLOBAL_C1_AUTHORITY_UNAVAILABLE" in value.branch_witness["status"]


def test_cross_foot_failure_is_checked_at_both_touchdowns(monkeypatch):
    inputs = _inputs()
    original = CanonicalConstantSkinTargetLaw._observe.__func__
    opposite_phase = inputs["provider"].anchor_for("left").touchdown_phase_s

    def cross_foot(cls, query, provider, skin, side, time_s, constants):
        result = original(cls, query, provider, skin, side, time_s, constants)
        calibrated = any(np.linalg.norm(value) > 0 for value in constants.values())
        if calibrated and side == "right" and time_s == opposite_phase:
            result["loaded"] = True
            result["required_correction_m"] = np.array([0.01, 0.0, 0.0])
        return result

    monkeypatch.setattr(
        CanonicalConstantSkinTargetLaw, "_observe", classmethod(cross_foot)
    )
    with pytest.raises(ContractError, match="calibration failed.*right loaded residual"):
        _build(inputs)


def test_constructor_refinement_and_extreme_time_cannot_bypass_validation(
    law_and_inputs,
):
    law, inputs = law_and_inputs
    with pytest.raises(ContractError, match="validated build calibration"):
        CanonicalConstantSkinTargetLaw(
            inputs["query"],
            inputs["query"],
            inputs["provider"],
            SkinRig(
                inputs["query"]._source,
                inputs["semantic_roles"],
                inputs["query"].context.forward,
                inputs["query"].context.up,
                inputs["contact_profile"],
            ),
            {"left": np.zeros(3), "right": np.zeros(3)},
        )
    refined = deepcopy(inputs["plan"])
    refined["samples"][0]["feet"]["left"]["target_offset_m"] = [0, 0, 0]
    refined_query = SourceMotionQuery(
        inputs["source"],
        semantic_roles=inputs["semantic_roles"],
        solver_gait=inputs["solver_gait"],
        locomotion_gait=inputs["locomotion_gait"],
        plan=refined,
        up_axis=inputs["up_axis"],
        forward_axis=inputs["forward_axis"],
        contact_profile=inputs["contact_profile"],
    )
    with pytest.raises(ContractError, match="unrefined"):
        CanonicalConstantSkinTargetLaw.build(
            refined_query,
            inputs["provider"],
            **{
                key: value
                for key, value in inputs.items()
                if key not in {"query", "provider"}
            },
        )
    with pytest.raises(ContractError, match="finite numeric"):
        law.value(10**10000)
