from copy import deepcopy
import hashlib

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
        "clearance_m": [0.0, 0.2, 0.0, 0.0],
        "forward_m": [0.0, 0.1, 0.0, 0.0],
        "foot_pitch_degrees": [0.0, 25.0, 0.0, 0.0],
    }
    other = {
        "clearance_m": [0.2, 0.0, 0.2, 0.2],
        "forward_m": [0.0, -0.1, 0.0, 0.0],
        "foot_pitch_degrees": [20.0, 0.0, 20.0, 20.0],
    }
    return {
        "schema": "eonwild.motion.authored-material-path.v1",
        "source_geometry_sha256": hashlib.sha256(b"source").hexdigest(),
        "measured_source_sha256": hashlib.sha256(b"source").hexdigest(),
        "fps": 3.0,
        "interval_count": 3,
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
        spatial_scale=2.0,
        contact_tolerance_ratio=0.0,
    )
    capsule["feet"]["left"]["clearance_m"][1] = 99.0
    query = SourceMotionQuery(
        **_query_kwargs(inputs), authored_material_contact=adapter
    )
    start = query.evaluate(0.0)
    quarter = query.evaluate(float(inputs["plan"]["duration_s"]) * 0.3)
    assert start.status == quarter.status == "AVAILABLE"
    assert start.row["feet"]["left"]["contact"] is True
    assert start.row["feet"]["right"]["contact"] is False
    assert start.row["feet"]["left"]["height_m"] == 0.0
    assert start.row["feet"]["right"]["height_m"] == pytest.approx(0.4)
    assert quarter.row["feet"]["left"]["height_m"] == pytest.approx(0.36)
    assert quarter.row["feet"]["left"]["foot_pitch_degrees"] == pytest.approx(22.5)
    assert "target_offset_m" not in quarter.row["feet"]["left"]


def test_adapter_rejects_cross_query_reuse_and_internal_tamper():
    inputs = _inputs()
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"],
        _capsule(),
        authored_source=b"source",
        spatial_scale=1.0,
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


def test_adapter_rejects_unbound_authored_source_bytes():
    inputs = _inputs()
    with pytest.raises(ContractError, match="source bytes differ"):
        AuthoredMaterialContactAdapter.build(
            inputs["query"],
            _capsule(),
            authored_source=b"another source",
            spatial_scale=1.0,
        )


def test_constant_skin_law_binds_adapter_and_keeps_pointwise_checks():
    inputs = _inputs()
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"],
        _capsule(),
        authored_source=b"source",
        spatial_scale=0.1,
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
    with pytest.raises(ContractError, match="validated request"):
        law.value(0.0)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(interval_count=True),
        lambda value: value["feet"]["left"].update(clearance_m=[0.0]),
        lambda value: value["feet"]["left"]["clearance_m"].__setitem__(1, float("nan")),
        lambda value: value["feet"]["left"]["forward_m"].__setitem__(3, 0.2),
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
            spatial_scale=1.0,
        )
