from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.contracts.v9_models import canonical_hash
from eonwild_motion.planning.grounded_gait import GroundedGait, load_grounded_gait
from eonwild_motion.planning.parameters import gait_parameters
from eonwild_motion.planning.grounded_intent_resolution import (
    measure_grounded_touchdown_geometry,
    resolve_grounded_intent,
)
from test_source_motion_query import _grounded_query


ROOT = Path(__file__).resolve().parents[1]
ALLO_SHA = "a403679deb968ec88f7b8b89e3e399cc0881e9cc602e765a6e55934c28ad3826"
TARBO_SHA = "2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f"


def _document(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def _policy() -> dict:
    return _document("catalog/locomotion-response/heavy-biped-grounded-reference.v1.json")


def _gait(period: float = 1.23) -> GroundedGait:
    document = _document("catalog/programs/heavy-biped.tarbosaurus-adult-walk.v4.json")
    document["parameters"]["step_period_s"] = period
    return load_grounded_gait(document)


def _query(source: str, rows: dict[str, list[float]]) -> dict:
    return {
        "source_geometry_sha256": source,
        "body_height_m": 2.2841755838983118 if source == TARBO_SHA else 2.106182073161406,
        "gait_parameters_sha256": "0" * 64,
        "sides": {
            side: {
                "event": "canonical_touchdown",
                "zero_step_ankle_from_hip_m": vector,
            }
            for side, vector in rows.items()
        },
    }


TARBO_QUERY = _query(TARBO_SHA, {
    "left": [0.34985465472235344, -1.4748641326630128, -0.15170414336747535],
    "right": [-0.3497169152182188, -1.477060794876222, -0.1595409517875455],
})
ALLO_QUERY = _query(ALLO_SHA, {
    "left": [0.21050781242524208, -1.4991134571109719, -0.20455545659029706],
    "right": [-0.21050781242737215, -1.499113454012734, -0.2045554485309242],
})


def _resolve(animal_path: str, source: str, query: dict, *, period: float = 1.23):
    animal = _document(animal_path)
    support = _document(
        "catalog/calibration/tarbosaurus-pin-552-1-adult-support.v1.json"
        if source == TARBO_SHA
        else "catalog/calibration/allosaurus-engineering-support.v1.json"
    )
    gait = _gait(period)
    query = deepcopy(query)
    query["gait_parameters_sha256"] = canonical_hash({
        key: value for key, value in vars(gait).items() if value is not None
    })
    return resolve_grounded_intent(
        gait,
        body_height_m=(2.2841755838983118 if source == TARBO_SHA else 2.106182073161406),
        animal_hindlimb_length_m=animal["measurements"]["hindlimb_length"]["value"],
        source_geometry_sha256=source,
        neutral_support_geometry=support,
        family_policy=_policy(),
        touchdown_geometry=query,
    )


def test_reference_geometry_preserves_working_walk_exactly():
    gait = _gait()
    result = _resolve(
        "catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v2.json",
        TARBO_SHA,
        TARBO_QUERY,
    )
    assert result.gait == gait
    assert result.requested_step_length_m == (
        _policy()["grounded_intent_resolution"]["step_length_hindlimb_ratio"] * 2.415
    )
    assert result.resolved_step_length_m == pytest.approx(1.370505350338987, abs=1e-15)
    assert result.limiting_side is None
    assert result.receipt()["resolved_gait_parameters"] == {
        key: value for key, value in vars(gait).items() if value is not None
    }


def test_allosaurus_resolves_from_same_rule_and_declared_support_posture():
    result = _resolve(
        "catalog/animals/allosaurus-composite-engineering.adult.v1.json",
        ALLO_SHA,
        ALLO_QUERY,
    )
    assert result.requested_step_length_m == pytest.approx(1.126481623363515)
    assert result.resolved_step_length_m == pytest.approx(0.9192761737944692)
    assert result.gait.step_length_body_heights == pytest.approx(0.4364656719419438)
    assert result.limiting_side == "left"
    assert min(row[2] for row in result.side_evidence) == pytest.approx(0.0, abs=1e-12)
    assert all(row[2] >= -1e-12 for row in result.side_evidence)


def test_exact_touchdown_observations_recover_centered_fraction_basis():
    gait = _gait()
    gait_hash = canonical_hash({
        key: value for key, value in vars(gait).items() if value is not None
    })
    common = {
        "source_geometry_sha256": ALLO_SHA,
        "body_height_m": 2.106182073161406,
        "gait_parameters_sha256": gait_hash,
        "event": "canonical_touchdown",
        "coordinate": {
            "lateral": [1.0, 0.0, 0.0],
            "up": [0.0, 1.0, 0.0],
            "forward": [0.0, 0.0, 1.0],
        },
    }
    observations = {
        "source_geometry_sha256": ALLO_SHA,
        "body_height_m": 2.106182073161406,
        "gait_parameters_sha256": gait_hash,
        "sides": {
            "left": {
                **common, "side": "left", "time_s": 0.0,
                "hip_world_m": [-0.4318727543614686, 2.075940637954479, 1.114027290052678],
                "target_ankle_world_m": [-0.22136494193622652, 0.5768271808435073, 1.6929715646784238],
            },
            "right": {
                **common, "side": "right", "time_s": 1.23,
                "hip_world_m": [0.4650078313155988, 2.075940637920519, 2.3777365338283643],
                "target_ankle_world_m": [0.25450001888822665, 0.5768271839077852, 2.956680816513482],
            },
        },
    }
    measured = measure_grounded_touchdown_geometry(gait, observations)
    assert measured["sides"]["left"]["zero_step_ankle_from_hip_m"] == pytest.approx(
        ALLO_QUERY["sides"]["left"]["zero_step_ankle_from_hip_m"]
    )
    assert measured["sides"]["right"]["zero_step_ankle_from_hip_m"] == pytest.approx(
        ALLO_QUERY["sides"]["right"]["zero_step_ankle_from_hip_m"]
    )


def test_source_query_exposes_bound_touchdown_observations_without_leg_solve(
    monkeypatch,
):
    gait = GroundedGait(
        centered_stance=True, step_length_body_heights=0.6,
        cycles=1, sample_hz=24,
    )
    query, *_ = _grounded_query(gait=gait)
    monkeypatch.setattr(
        type(query),
        "evaluate",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("touchdown observation must not execute the leg solve")
        ),
    )
    left = query.grounded_touchdown_observation(0.0, "left")
    right = query.grounded_touchdown_observation(gait.step_period_s, "right")
    combined = {
        "source_geometry_sha256": left["source_geometry_sha256"],
        "body_height_m": left["body_height_m"],
        "gait_parameters_sha256": left["gait_parameters_sha256"],
        "sides": {"left": left, "right": right},
    }
    measured = measure_grounded_touchdown_geometry(gait, combined)
    assert measured["source_geometry_sha256"] == left["source_geometry_sha256"]
    assert set(measured["sides"]) == {"left", "right"}
    with pytest.raises(ContractError, match="canonical touchdown"):
        query.grounded_touchdown_observation(gait.step_period_s / 2, "left")


def test_walk_and_fast_share_spatial_resolution_without_overriding_timing():
    walk = _resolve(
        "catalog/animals/allosaurus-composite-engineering.adult.v1.json",
        ALLO_SHA,
        ALLO_QUERY,
        period=1.23,
    )
    fast = _resolve(
        "catalog/animals/allosaurus-composite-engineering.adult.v1.json",
        ALLO_SHA,
        ALLO_QUERY,
        period=0.8,
    )
    assert fast.resolved_step_length_m == walk.resolved_step_length_m
    assert fast.gait.step_period_s == 0.8
    assert walk.gait.step_period_s == 1.23
    receipt = fast.receipt()
    receipt["resolved_gait_parameters"]["step_period_s"] = 999
    assert fast.gait.step_period_s == 0.8


def test_recursively_immutable_inputs_are_admitted_and_detached():
    support = _document("catalog/calibration/allosaurus-engineering-support.v1.json")

    def freeze(value):
        if isinstance(value, dict):
            return MappingProxyType({key: freeze(item) for key, item in value.items()})
        if isinstance(value, list):
            return tuple(freeze(item) for item in value)
        return value

    gait = _gait()
    query = deepcopy(ALLO_QUERY)
    query["gait_parameters_sha256"] = canonical_hash({
        key: value for key, value in vars(gait).items() if value is not None
    })
    result = resolve_grounded_intent(
        gait,
        body_height_m=2.106182073161406,
        animal_hindlimb_length_m=1.985,
        source_geometry_sha256=ALLO_SHA,
        neutral_support_geometry=freeze(support),
        family_policy=freeze(_policy()),
        touchdown_geometry=freeze(query),
    )
    assert result.resolved_step_length_m == pytest.approx(0.9192761737944692)


@pytest.mark.parametrize(
    "case",
    ["source", "query_source", "query_gait", "coordinate", "ratio", "step", "side", "knee", "event"],
)
def test_resolution_rejects_unbound_or_malformed_inputs(case):
    support = _document("catalog/calibration/allosaurus-engineering-support.v1.json")
    policy = _policy()
    query = deepcopy(ALLO_QUERY)
    gait = _gait()
    query["gait_parameters_sha256"] = canonical_hash({
        key: value for key, value in vars(gait).items() if value is not None
    })
    source = ALLO_SHA
    if case == "source":
        source = "0" * 64
    elif case == "query_source":
        query["source_geometry_sha256"] = "0" * 64
    elif case == "query_gait":
        query["gait_parameters_sha256"] = "0" * 64
    elif case == "coordinate":
        support["coordinate"]["forward"] = [1.0, 0.0, 0.0]
    elif case == "ratio":
        policy["grounded_intent_resolution"]["step_length_hindlimb_ratio"] = 0.5
    elif case == "step":
        policy["grounded_intent_resolution"]["input_step_length_body_heights"] = 0.55
    elif case == "side":
        del support["sides"]["right"]
    elif case == "knee":
        support["sides"]["left"]["preferred_support_knee_degrees"] = True
    else:
        query["sides"]["left"]["event"] = "arbitrary"
    with pytest.raises(ContractError):
        resolve_grounded_intent(
            gait,
            body_height_m=2.106182073161406,
            animal_hindlimb_length_m=1.985,
            source_geometry_sha256=source,
            neutral_support_geometry=support,
            family_policy=policy,
            touchdown_geometry=query,
        )


def test_fixed_touchdown_measurement_removes_authored_reach():
    gait = GroundedGait(centered_stance=False, step_length_body_heights=-.38,
                        touchdown_reach_body_heights=.2)
    gait_hash = canonical_hash(gait_parameters(gait))
    body_height = 2.0
    common = {
        "source_geometry_sha256": TARBO_SHA,
        "body_height_m": body_height,
        "gait_parameters_sha256": gait_hash,
        "event": "canonical_touchdown",
        "coordinate": {"lateral": [1., 0., 0.], "up": [0., 1., 0.],
                       "forward": [0., 0., 1.]},
    }
    observations = {
        "source_geometry_sha256": TARBO_SHA,
        "body_height_m": body_height,
        "gait_parameters_sha256": gait_hash,
        "sides": {
            "left": {**common, "side": "left", "time_s": 0.,
                     "hip_world_m": [0., 1., 0.],
                     "target_ankle_world_m": [0., 0., -.15]},
            "right": {**common, "side": "right", "time_s": gait.step_period_s,
                      "hip_world_m": [0., 1., 0.],
                      "target_ankle_world_m": [0., 0., -.15]},
        },
    }
    measured = measure_grounded_touchdown_geometry(gait, observations)
    # Signed fixed reach is -0.4 m; removing it leaves the source/body basis.
    assert measured["sides"]["left"]["zero_step_ankle_from_hip_m"] == pytest.approx(
        [0., -1., .25]
    )


def test_reference_scaled_reverse_preserves_signed_stride_and_timing():
    gait = GroundedGait(**{
        **vars(_gait(period=1.0)),
        "centered_stance": False,
        "duty_factor": 0.68,
        "step_length_body_heights": -0.38,
        "touchdown_reach_body_heights": 0.2,
    })
    query = _query(TARBO_SHA, {
        "left": [.349, -1., 0.],
        "right": [-.349, -1., 0.],
    })
    query["gait_parameters_sha256"] = canonical_hash(gait_parameters(gait))
    result = resolve_grounded_intent(
        gait,
        body_height_m=2.2841755838983118,
        animal_hindlimb_length_m=2.415,
        source_geometry_sha256=TARBO_SHA,
        neutral_support_geometry=_document(
            "catalog/calibration/tarbosaurus-pin-552-1-adult-support.v1.json"
        ),
        family_policy=_policy(),
        touchdown_geometry=query,
    )
    assert result.gait == gait
    assert result.requested_step_length_m == pytest.approx(
        -0.38 * 2.2841755838983118
    )
    assert result.resolved_step_length_m == pytest.approx(
        -0.38 * 2.2841755838983118
    )
    assert result.gait.step_period_s == 1.0
    assert result.gait.duty_factor == 0.68
    assert result.receipt()["placement_mode"] == "fixed_touchdown_reach_signed_stride"
    assert all(
        row["fixed_touchdown_reach_m"] == pytest.approx(
            -.2 * 2.2841755838983118
        )
        for row in result.receipt()["sides"].values()
    )


def test_fixed_touchdown_infeasibility_is_not_hidden_by_stride_reduction():
    gait = GroundedGait(**{
        **vars(_gait(period=1.0)),
        "centered_stance": False,
        "step_length_body_heights": -.05,
        "touchdown_reach_body_heights": .2,
    })
    query = _query(TARBO_SHA, {
        "left": [.349, -1., 2.],
        "right": [-.349, -1., 2.],
    })
    query["gait_parameters_sha256"] = canonical_hash(gait_parameters(gait))
    with pytest.raises(ContractError, match="fixed touchdown placement exceeds"):
        resolve_grounded_intent(
            gait,
            body_height_m=2.2841755838983118,
            animal_hindlimb_length_m=2.415,
            source_geometry_sha256=TARBO_SHA,
            neutral_support_geometry=_document(
                "catalog/calibration/tarbosaurus-pin-552-1-adult-support.v1.json"
            ),
            family_policy=_policy(),
            touchdown_geometry=query,
        )


def test_centered_reverse_uses_backward_reach_envelope():
    gait = GroundedGait(**{
        **vars(_gait(period=1.0)),
        "step_length_body_heights": -.38,
    })
    query = _query(TARBO_SHA, {
        "left": [.349, -1., .1],
        "right": [-.349, -1., .1],
    })
    query["gait_parameters_sha256"] = canonical_hash(gait_parameters(gait))
    result = resolve_grounded_intent(
        gait,
        body_height_m=2.2841755838983118,
        animal_hindlimb_length_m=2.415,
        source_geometry_sha256=TARBO_SHA,
        neutral_support_geometry=_document(
            "catalog/calibration/tarbosaurus-pin-552-1-adult-support.v1.json"
        ),
        family_policy=_policy(),
        touchdown_geometry=query,
    )
    assert result.resolved_step_length_m < 0
    assert all(row[2] >= -1e-12 for row in result.side_evidence)


def test_uncapped_nonreference_geometry_uses_resolved_physical_step():
    gait = _gait()
    source = "1" * 64
    body_height = 2.0
    support = {
        "schema": "eonwild.motion.neutral-support-geometry.v1",
        "id": "synthetic-support.v1",
        "version": 1,
        "source_geometry_sha256": source,
        "hindlimb_length_m": 2.0,
        "coordinate": {
            "frame": "source_world",
            "lateral": [1.0, 0.0, 0.0],
            "up": [0.0, 1.0, 0.0],
            "forward": [0.0, 0.0, 1.0],
        },
        "sides": {
            side: {
                "upper_length_m": 0.9,
                "lower_length_m": 0.9,
                "preferred_support_knee_degrees": 130.0,
                "posture_evidence": "synthetic non-reference regression",
            }
            for side in ("left", "right")
        },
        "limitations": ["synthetic test fixture"],
    }
    gait_hash = canonical_hash({
        key: value for key, value in vars(gait).items() if value is not None
    })
    query = _query(source, {
        "left": [0.1, -0.5, 0.0],
        "right": [-0.1, -0.5, 0.0],
    })
    query["body_height_m"] = body_height
    query["gait_parameters_sha256"] = gait_hash

    result = resolve_grounded_intent(
        gait,
        body_height_m=body_height,
        animal_hindlimb_length_m=2.0,
        source_geometry_sha256=source,
        neutral_support_geometry=support,
        family_policy=_policy(),
        touchdown_geometry=query,
    )

    assert result.limiting_side is None
    assert result.resolved_step_length_m == pytest.approx(
        2.0 * _policy()["grounded_intent_resolution"]["step_length_hindlimb_ratio"]
    )
    assert result.gait.step_length_body_heights * body_height == pytest.approx(
        result.resolved_step_length_m
    )
    assert result.receipt()["resolved_gait_parameters"][
        "step_length_body_heights"
    ] == pytest.approx(result.resolved_step_length_m / body_height)
