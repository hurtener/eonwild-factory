"""Exact emitted LINEAR/SLERP tangent regressions."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.emitted_tangent import endpoint_tangent, skinned_velocity
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.whole_body_gait_transition import _build_glb
from test_v9_airborne_gait import fixture


ROOT = Path(__file__).resolve().parents[1]


def _asset_clip(*, scale: bool = False) -> tuple[Glb, dict]:
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    root = base.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    times = np.array([0., .1, .4])  # deliberately nonuniform
    channels = {(root, "translation"): np.array([[0., 0., 0.], [.1, 0., 0.], [.4, 0., 0.]])}
    if scale:
        channels[root, "scale"] = np.array([[1., 1., 1.], [1.1, 1., 1.], [1.4, 1., 1.]])
    raw = _build_glb(base, "exact-tangent", times, channels, "exact-test", {})
    return Glb.from_bytes(raw), profile


def test_exact_translation_scale_fk_lbs_nonuniform_clock():
    glb, profile = _asset_clip(scale=True)
    tangent = endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)
    root = glb.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    assert tangent.translation_velocity[root, 0] == pytest.approx(1.)
    assert tangent.scale_velocity[root, 0] == pytest.approx(1.)
    labels, velocity = skinned_velocity(glb, profile, tangent)
    assert labels and velocity.shape == (len(labels), 3)
    assert np.isfinite(velocity).all()
    no_scale, _ = _asset_clip()
    _, no_scale_velocity = skinned_velocity(no_scale, profile, endpoint_tangent(no_scale, "exact-tangent", endpoint=0, terminal=False))
    # Root translation is inherited by every joint and LBS point; the scale
    # derivative then changes that exact material velocity without NaNs.
    assert np.allclose(no_scale_velocity[:, 0], no_scale_velocity[0, 0])
    assert no_scale_velocity[0, 0] > 0.
    assert not np.allclose(velocity, no_scale_velocity)


def test_shortest_slerp_is_sign_equivalent_and_body_framed():
    glb, profile = _asset_clip()
    root = glb.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    base = Glb(ROOT / profile["source"]["path"])
    times = np.array([0., .2])
    angle = np.radians(20.)
    q = np.array([[0., 0., 0., 1.], [0., np.sin(angle / 2), 0., np.cos(angle / 2)]])
    normal = Glb.from_bytes(_build_glb(base, "q", times, {(root, "rotation"): q}, "q", {}))
    antipodal = Glb.from_bytes(_build_glb(base, "q", times, {(root, "rotation"): q * np.array([[1.], [-1.]])}, "q", {}))
    expected = np.radians(20.) / .2
    assert endpoint_tangent(normal, "q", endpoint=0, terminal=False).angular_velocity[root, 1] == pytest.approx(expected)
    assert endpoint_tangent(antipodal, "q", endpoint=0, terminal=False).angular_velocity[root, 1] == pytest.approx(expected)


def test_fk_rotation_product_rule_uses_the_parent_world_frame():
    base, roles = fixture()
    root = base.name_to_node[roles["root"]]
    hip = base.name_to_node[roles["legs"]["left"]["contactChain"][0]]
    angle = np.radians(20.)
    q = np.array([[0., 0., 0., 1.], [0., np.sin(angle / 2), 0., np.cos(angle / 2)]])
    glb = Glb.from_bytes(_build_glb(base, "frame", np.array([0., .2]), {(root, "rotation"): q}, "frame", {}))
    tangent = endpoint_tangent(glb, "frame", endpoint=0, terminal=False)
    omega = np.array([0., angle / .2, 0.])
    point = tangent.world[hip, :3, 3]
    assert tangent.world_velocity[hip, :3, 3] == pytest.approx(np.cross(omega, point))


def test_rejects_non_linear_and_duplicate_channels():
    glb, _ = _asset_clip()
    animation = glb.document["animations"][0]
    animation["samplers"][0]["interpolation"] = "STEP"
    with pytest.raises(ContractError, match="LINEAR"):
        endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)
