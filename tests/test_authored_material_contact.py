from copy import deepcopy
import hashlib
import math

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.solve.authored_material_contact import (
    AuthoredMaterialContactAdapter,
)
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
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


def test_adapter_applies_material_contact_path_at_keys_and_offgrid():
    inputs = _inputs()
    bare = inputs["query"]
    capsule = _capsule()
    adapter = AuthoredMaterialContactAdapter.build(
        bare,
        capsule,
        authored_source=b"source",
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


def test_adapter_rejects_cross_query_reuse_and_internal_tamper():
    inputs = _inputs()
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"],
        _capsule(),
        authored_source=b"source",
    )
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
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"], _capsule(), authored_source=b"source"
    )
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
        )


def test_constant_skin_law_binds_adapter_and_keeps_pointwise_checks():
    inputs = _inputs()
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"],
        _capsule(),
        authored_source=b"source",
    )
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
        )


def test_contact_switches_preserve_zero_height_and_consistent_row_phase():
    inputs = _inputs()
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"], _capsule(), authored_source=b"source"
    )
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
