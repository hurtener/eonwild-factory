from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import math
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import (
    apply_uniform_geometry_scale,
    load_animal_instance,
)
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import AirborneGait, build_airborne_plan
from eonwild_motion.planning.articulation_profile import load_articulation_profile
from eonwild_motion.planning.gait_transition import (
    GaitTransition,
    build_transition_plan,
)
from eonwild_motion.planning.grounded_gait import (
    GroundedGait,
    build_grounded_plan,
    load_grounded_gait,
)
from eonwild_motion.solve.airborne_gait import (
    build_airborne_solve_context,
    solve_airborne_gait,
    solve_airborne_plan_sample,
)
from eonwild_motion.solve import jaw_response
from eonwild_motion.solve.performance import decorate_plan, load_performance
from eonwild_motion.solve.source_motion_query import (
    BRANCH_OR_CONVERGENCE_UNAVAILABLE,
    CONTINUOUS_SKIN_TARGET_UNAVAILABLE,
    RAW_NUMERICAL_PROBE_ONLY,
    SourceMotionQuery,
    SourceMotionRawProbe,
    SourceMotionUnavailable,
)
from eonwild_motion.solve.whole_body_gait_transition import _encode
from test_v9_airborne_gait import fixture


ROOT = Path(__file__).resolve().parents[1]
HEAVY = (
    ROOT
    / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb"
)
ADULT_SOURCE_SHA = "2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f"
ADULT_SOURCE = ROOT / "assets/sha256" / f"{ADULT_SOURCE_SHA}.glb"
ADULT_RIG = ROOT / "catalog/rigs/heavy-biped.v9.json"
ADULT_PROGRAM = ROOT / "catalog/programs/heavy-biped.tarbosaurus-adult-walk.v4.json"
ADULT_PERFORMANCE = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v7.json"
ADULT_ANIMAL = ROOT / "catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v2.json"
FIXTURE_HEIGHT_M = 1.6


def _grounded_query(
    *,
    transition: GaitTransition | None = None,
    plan=None,
    gait: GroundedGait | None = None,
    source=None,
    roles=None,
):
    if source is None:
        source, roles = fixture("source_query_", 1.0, upper_body=True)
    grounded = gait or GroundedGait(
        cycles=1, sample_hz=24, step_length_body_heights=0.2
    )
    if plan is None:
        plan = (
            build_grounded_plan(grounded, FIXTURE_HEIGHT_M)
            if transition is None
            else build_transition_plan(transition, grounded, FIXTURE_HEIGHT_M)
        )
    solver = AirborneGait(step_period_s=grounded.step_period_s, cycles=1, sample_hz=24)
    return (
        SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver,
            locomotion_gait=grounded,
            plan=plan,
            transition=transition,
            forward_axis=(0.0, 0.0, 1.0),
        ),
        source,
        roles,
        grounded,
        plan,
        solver,
    )


def _scaled_adult_v7_query(*, source: Glb | None = None):
    if source is None:
        source = Glb.from_bytes(ADULT_SOURCE.read_bytes())
        animal = load_animal_instance(
            json.loads(ADULT_ANIMAL.read_text()), source_sha256=ADULT_SOURCE_SHA
        )
        apply_uniform_geometry_scale(source, animal["uniform_scale"])
    roles = json.loads(ADULT_RIG.read_text())["roles"]
    grounded = replace(
        load_grounded_gait(json.loads(ADULT_PROGRAM.read_text())), sample_hz=24
    )
    solver = AirborneGait(
        step_period_s=grounded.step_period_s,
        cycles=grounded.cycles,
        sample_hz=grounded.sample_hz,
        swing_hip_lift_degrees=grounded.swing_hip_lift_degrees,
    )
    performance = replace(
        load_performance(json.loads(ADULT_PERFORMANCE.read_text())), skin_refinement=False
    )
    plan = decorate_plan(
        build_grounded_plan(grounded, geometry_height(source, roles, (0, 1, 0))),
        performance,
    )
    return (
        SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver,
            locomotion_gait=grounded,
            plan=plan,
            up_axis=(0, 1, 0),
            forward_axis=(0, 0, 1),
            legacy_overlay=False,
        ),
        source,
        roles,
        plan,
    )


def test_existing_plan_key_matches_direct_phase_local_solve_and_off_grid_is_source_sampled():
    query, _, _, _, plan, _ = _grounded_query()
    row = plan["samples"][7]
    result = query.evaluate(row["time_s"])
    assert result.status == "AVAILABLE"
    assert result.pose == solve_airborne_plan_sample(query.context, row)
    off_grid = query.evaluate(0.123)
    assert off_grid.status == "AVAILABLE"
    assert off_grid.row["time_s"] == pytest.approx(0.123)
    # The corrected binding makes exact-key/adjacent source poses continuous.
    near = query.evaluate(math.nextafter(row["time_s"], math.inf))
    assert (
        np.max(
            np.abs(
                np.asarray(result.pose.translations)
                - np.asarray(near.pose.translations)
            )
        )
        < 1e-9
    )


def test_owned_target_offsets_apply_before_one_solve_and_are_detached(monkeypatch):
    query, _, _, _, plan, _ = _grounded_query()
    index = 7
    time_s = plan["samples"][index]["time_s"]
    offsets = {
        "left": np.array([0.001, -0.002, 0.003]),
        "right": np.array([-0.004, 0.005, -0.006]),
    }
    row = deepcopy(plan["samples"][index])
    for side in ("left", "right"):
        row["feet"][side]["target_offset_m"] = offsets[side].tolist()
    expected = solve_airborne_plan_sample(
        query.context,
        row,
        body_response_sample=query._body_sample(index, row),
    )
    import eonwild_motion.solve.source_motion_query as source_query_module
    original = source_query_module.solve_airborne_plan_sample
    calls = []

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(source_query_module, "solve_airborne_plan_sample", counted)
    result = query.evaluate_with_target_offsets(time_s, offsets)
    assert len(calls) == 1
    assert result.pose == expected
    assert result.row["feet"]["left"]["target_offset_m"] == (0.001, -0.002, 0.003)
    assert "target_offset_m" not in query.evaluate(time_s).row["feet"]["left"]
    offsets["left"][0] = 99.0
    result.pose.translations[0] = (99.0, 99.0, 99.0)
    repeat = query.evaluate_with_target_offsets(
        time_s,
        {"left": [0.001, -0.002, 0.003], "right": [-0.004, 0.005, -0.006]},
    )
    assert repeat.pose == expected
    assert repeat.pose.translations[0] != (99.0, 99.0, 99.0)


@pytest.mark.parametrize(
    "offsets",
    [
        {"left": [0, 0, 0]},
        {"left": [0, 0, 0], "right": [0, 0]},
        {"left": [0, 0, 0], "right": [0, float("nan"), 0]},
        {"left": [0, 0, 0], "right": [False, 0, 0]},
    ],
)
def test_owned_target_offsets_reject_malformed_vectors(offsets):
    query, *_ = _grounded_query()
    with pytest.raises(ContractError, match="target offsets"):
        query.evaluate_with_target_offsets(0.1, offsets)


def test_scaled_adult_neutral_jaw_query_keeps_raw_identity_and_rejects_stale_state(
    monkeypatch,
):
    query, source, roles, plan = _scaled_adult_v7_query()
    jaw = source.name_to_node[roles["jaw_lower"]]
    row = plan["samples"][7]

    assert query._source is not source
    assert query._source.document is not source.document
    assert query._source.raw == source.raw
    assert query.context.jaw == jaw
    assert query.context.jaw_axis is not None
    assert query.context.jaw_neutral_close_degrees > 0
    exact = query.evaluate(row["time_s"])
    assert exact.status == "AVAILABLE"
    body_response = (
        None
        if query._body_response is None
        else query._body_response["samples"][7]
    )
    assert exact.pose == solve_airborne_plan_sample(
        query.context, row, body_response_sample=body_response
    )
    assert query.evaluate(0.123).status == "AVAILABLE"

    observed_admissions = []
    original_admit = jaw_response.admit_neutral_jaw

    def observe_admission(*args, **kwargs):
        observed_admissions.append((args, kwargs))
        return original_admit(*args, **kwargs)

    monkeypatch.setattr(jaw_response, "admit_neutral_jaw", observe_admission)
    _, _, _, receipt = solve_airborne_gait(
        source,
        source_clip=None,
        semantic_roles=roles,
        gait=query._solver_gait,
        up_axis=(0, 1, 0),
        forward_axis=(0, 0, 1),
        plan_override=plan,
        legacy_overlay=False,
    )
    jaw_receipt = receipt["neutral_jaw_calibration"]
    assert len(observed_admissions) == 1
    assert jaw_receipt["source_geometry_sha256"] == ADULT_SOURCE_SHA
    assert jaw_receipt["jaw_node"] == jaw
    assert jaw_receipt["admitted_uniform_scale"] > 0

    stale = Glb.from_bytes(ADULT_SOURCE.read_bytes())
    animal = load_animal_instance(
        json.loads(ADULT_ANIMAL.read_text()), source_sha256=ADULT_SOURCE_SHA
    )
    apply_uniform_geometry_scale(stale, animal["uniform_scale"])
    stale.document["accessors"][0]["count"] += 1
    with pytest.raises(ContractError, match="frozen geometry plus one uniform scale"):
        _scaled_adult_v7_query(source=stale)


def test_query_retains_source_plan_roles_and_articulation_guardrails_without_aliases():
    query, source, roles, grounded, plan, solver = _grounded_query()
    profile = load_articulation_profile(
        json.loads(
            (
                ROOT / "catalog/articulation/heavy-biped.tarbosaurus-adult-walk.v1.json"
            ).read_text()
        )
    )
    context = build_airborne_solve_context(
        source,
        source_clip=None,
        semantic_roles=roles,
        gait=solver,
        plan=plan,
        forward_axis=(0.0, 0.0, 1.0),
        articulation_profile=profile,
    )
    baseline = query.evaluate(plan["samples"][6]["time_s"])
    support_before = context.articulation_profile.support["knee_interior_degrees"]
    profile.support["knee_interior_degrees"] = profile.swing["knee_interior_degrees"]
    roles["root"] = roles["pelvis"]
    plan["samples"][0]["root_forward_m"] += 1.0
    source.name_to_node.clear()
    source.document["nodes"][0]["name"] = "caller-mutated"
    with pytest.raises(TypeError):
        context.articulation_profile.support["knee_interior_degrees"] = support_before
    assert (
        context.articulation_profile.support["knee_interior_degrees"] == support_before
    )
    assert query.evaluate(baseline.time_s).pose == baseline.pose


def test_source_binding_rejects_plan_height_gait_row_and_transition_mismatches():
    _, source, roles, gait, plan, solver = _grounded_query()
    bad_height = deepcopy(plan)
    bad_height["body_height_m"] = 2.0
    bad_gait = GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=0.4)
    bad_row = deepcopy(plan)
    bad_row["samples"][5]["root_forward_m"] += 0.25
    bad_extra = deepcopy(plan)
    bad_extra["samples"][5]["root_pitch_degrees"] = 1.0
    cases = [
        dict(plan=bad_height, locomotion_gait=gait),
        dict(plan=plan, locomotion_gait=bad_gait),
        dict(plan=bad_row, locomotion_gait=gait),
        dict(plan=bad_extra, locomotion_gait=gait),
    ]
    transition = GaitTransition("start", sample_hz=24, boundary_sample_hz=48)
    transition_plan = build_transition_plan(transition, gait, FIXTURE_HEIGHT_M)
    bad_contract = deepcopy(transition_plan)
    bad_contract["transition_contract"]["root_distance_m"] += 0.1
    cases += [
        dict(plan=transition_plan, locomotion_gait=gait),
        dict(plan=plan, locomotion_gait=gait, transition=transition),
        dict(plan=bad_contract, locomotion_gait=gait, transition=transition),
    ]
    for kwargs in cases:
        with pytest.raises(ContractError):
            SourceMotionQuery(
                source,
                semantic_roles=roles,
                solver_gait=solver,
                forward_axis=(0.0, 0.0, 1.0),
                **kwargs,
            )
    with pytest.raises(ContractError):
        SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=AirborneGait(step_period_s=0.9, cycles=1, sample_hz=24),
            locomotion_gait=gait,
            plan=plan,
            forward_axis=(0.0, 0.0, 1.0),
        )


def test_transition_query_uses_canonical_events_not_output_grid_and_preserves_requested_side():
    transition = GaitTransition("start", sample_hz=24, boundary_sample_hz=48)
    query, _, _, _, plan, _ = _grounded_query(transition=transition)
    assert (
        query.evaluate(plan["samples"][len(plan["samples"]) // 2]["time_s"]).status
        == "AVAILABLE"
    )
    # The grounded law owns right liftoff at .352 s; it is independent of the
    # retained 24 Hz sample at .36923... .
    steady, *_ = _grounded_query()
    assert steady._is_boundary(0.352)
    left = steady.evaluate(0.352, side="left_limit")
    right = steady.evaluate(0.352, side="right_limit")
    assert left.row["feet"]["right"]["contact"]
    assert not right.row["feet"]["right"]["contact"]
    assert isinstance(
        steady.derivative(0.352, side="left_limit"), SourceMotionUnavailable
    )
    assert (
        steady.derivative(0.352, side="left_limit").status
        == BRANCH_OR_CONVERGENCE_UNAVAILABLE
    )
    raw = steady.raw_probe(0.352, side="right_limit")
    assert isinstance(raw, SourceMotionRawProbe)
    assert raw.status == RAW_NUMERICAL_PROBE_ONLY
    assert raw.step_sizes_s[0] > 1e-6
    assert steady.raw_probe(0.352, side="left_limit").step_sizes_s[0] > 1e-6
    assert set(raw.per_unit_deltas) == {
        "local_translation_mps",
        "local_angular_radps",
        "world_node_mps",
    }


def test_airborne_query_reuses_continuous_body_response_at_exact_and_off_grid_source_times():
    source, roles = fixture("source_airborne_", 1.0, upper_body=True)
    gait = AirborneGait(
        cycles=1,
        sample_hz=24,
        continuous_body_launch_fraction=0.85,
        chest_response_gain_degrees=1.5,
        tail_response_gain_degrees=2.0,
    )
    plan = build_airborne_plan(gait, FIXTURE_HEIGHT_M)
    query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=gait,
        locomotion_gait=gait,
        plan=plan,
        forward_axis=(0.0, 0.0, 1.0),
    )
    index = 6
    result = query.evaluate(plan["samples"][index]["time_s"])
    assert result.pose == solve_airborne_plan_sample(
        query.context,
        plan["samples"][index],
        body_response_sample=query._body_response["samples"][index],
    )
    assert query.evaluate(0.123).status == "AVAILABLE"


def test_renamed_nonaxis_query_is_order_independent():
    source, roles = fixture("source_nonaxis_", 1.0, upper_body=True)
    document = deepcopy(source.document)
    root = source.name_to_node[roles["root"]]
    document["nodes"][root]["rotation"] = [0.0, math.sqrt(0.5), 0.0, math.sqrt(0.5)]
    source = Glb.from_bytes(_encode(document, source.binary))
    grounded = GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=0.2)
    plan = build_grounded_plan(grounded, FIXTURE_HEIGHT_M)
    query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=AirborneGait(
            step_period_s=grounded.step_period_s, cycles=1, sample_hz=24
        ),
        locomotion_gait=grounded,
        plan=plan,
        forward_axis=(1.0, 0.0, 0.0),
    )
    target = plan["samples"][7]["time_s"]
    first = query.evaluate(target)
    for row in reversed(plan["samples"]):
        query.evaluate(row["time_s"])
    assert query.evaluate(target).pose == first.pose


def test_formal_derivative_is_typed_unavailable_and_raw_probe_is_explicitly_non_authoritative():
    query, *_ = _grounded_query()
    formal = query.derivative(0.123)
    assert isinstance(formal, SourceMotionUnavailable)
    assert formal.status == BRANCH_OR_CONVERGENCE_UNAVAILABLE
    raw = query.raw_probe(0.123)
    assert isinstance(raw, SourceMotionRawProbe)
    assert raw.status == RAW_NUMERICAL_PROBE_ONLY
    assert raw.local_angular_velocity_radps.shape[1] == 3
    assert raw.world_node_velocity_mps.shape[1] == 3
    assert all(b < a for a, b in zip(raw.step_sizes_s, raw.step_sizes_s[1:]))
    for time, side in ((float("nan"), "value"), (0.1, "bad"), (-0.01, "value")):
        with pytest.raises(ContractError):
            query.evaluate(time, side=side)
    with pytest.raises(ContractError):
        query.raw_probe(0.1, initial_h_s=0.0)


def test_refined_queries_expose_only_exact_grid_values_without_target_interpolation():
    query, source, roles, grounded, plan, solver = _grounded_query()
    refined = deepcopy(plan)
    for row in refined["samples"]:
        for foot in row["feet"].values():
            foot["target_offset_m"] = [0.0, 0.0, 0.0]
    refined_query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=grounded,
        plan=refined,
        forward_axis=(0.0, 0.0, 1.0),
    )
    assert refined_query.evaluate(refined["samples"][3]["time_s"]).status == "AVAILABLE"
    for result in (
        refined_query.evaluate(0.123),
        refined_query.evaluate_with_target_offsets(
            0.123, {"left": [0, 0, 0], "right": [0, 0, 0]}
        ),
        refined_query.evaluate_with_target_offsets(
            refined["samples"][3]["time_s"],
            {"left": [0, 0, 0], "right": [0, 0, 0]},
        ),
        refined_query.derivative(refined["samples"][3]["time_s"]),
        refined_query.raw_probe(0.123),
    ):
        assert isinstance(result, SourceMotionUnavailable)
        assert result.status == CONTINUOUS_SKIN_TARGET_UNAVAILABLE


def test_constructor_rejects_malformed_rows_and_nonboolean_legacy_overlay():
    _, source, roles, gait, plan, solver = _grounded_query()
    for bad in (
        {"samples": [{}, {}]},
        {"samples": [dict(plan["samples"][0], time_s="bad"), plan["samples"][1]]},
    ):
        with pytest.raises(ContractError):
            SourceMotionQuery(
                source,
                semantic_roles=roles,
                solver_gait=solver,
                locomotion_gait=gait,
                plan=bad,
                forward_axis=(0.0, 0.0, 1.0),
            )
    with pytest.raises(ContractError):
        SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver,
            locomotion_gait=gait,
            plan=plan,
            forward_axis=(0.0, 0.0, 1.0),
            legacy_overlay="false",
        )


def test_source_fk_lbs_material_points_require_matching_profile_provenance():
    source = Glb.from_bytes(HEAVY.read_bytes())
    roles = json.loads((ROOT / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]
    contact = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    wrong_contact = json.loads(
        (ROOT / "catalog/contacts/heavy-biped.v10.json").read_text()
    )
    up, forward = (0.0, 1.0, 0.0), (0.03893162055641767, 0.0, 0.9992418770852486)
    height = geometry_height(source, roles, up)
    grounded = GroundedGait(
        cycles=1,
        sample_hz=24,
        step_length_body_heights=0.1,
        touchdown_reach_body_heights=0.05,
        swing_clearance_body_heights=0.08,
    )
    plan = build_grounded_plan(grounded, height)
    kwargs = dict(
        semantic_roles=roles,
        solver_gait=AirborneGait(
            step_period_s=grounded.step_period_s, cycles=1, sample_hz=24
        ),
        locomotion_gait=grounded,
        plan=plan,
        up_axis=up,
        forward_axis=forward,
    )
    with pytest.raises(ContractError):
        SourceMotionQuery(source, contact_profile=wrong_contact, **kwargs)
    # Profile raw provenance is necessary but not sufficient: a stale mutable
    # current document cannot be re-encoded into the SkinRig snapshot.
    stale = Glb.from_bytes(HEAVY.read_bytes())
    stale.document["accessors"][0]["count"] += 1
    with pytest.raises(ContractError):
        SourceMotionQuery(stale, contact_profile=contact, **kwargs)
    query = SourceMotionQuery(source, contact_profile=contact, **kwargs)
    result = query.evaluate(plan["samples"][5]["time_s"])
    assert result.material_points is not None
    # The only admitted mutable source state is the compiler-owned uniform
    # scene-root animal scale, with a newly bound plan at that measured height.
    scaled = Glb.from_bytes(HEAVY.read_bytes())
    apply_uniform_geometry_scale(scaled, 0.75)
    scaled_plan = build_grounded_plan(grounded, geometry_height(scaled, roles, up))
    scaled_query = SourceMotionQuery(
        scaled,
        contact_profile=contact,
        **dict(kwargs, plan=scaled_plan),
    )
    assert (
        scaled_query.evaluate(scaled_plan["samples"][5]["time_s"]).material_points
        is not None
    )
    assert set(result.material_points) == {"left", "right"}
    assert all(
        points.shape[1] == 3 and len(points) and not points.flags.writeable
        for points in result.material_points.values()
    )
