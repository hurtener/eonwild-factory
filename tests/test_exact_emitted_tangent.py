"""Exact emitted LINEAR/SLERP tangent regressions."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.contact_gauge import _animation_channels, _pose_matrices
from eonwild_motion.factory.emitted_tangent import (
    _skin_influences,
    endpoint_tangent,
    local_cyclic_tangents,
    skinned_velocity,
)
from eonwild_motion.factory.quality import emitted_cyclic_continuity, emitted_rotation_rates
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _build_glb, _encode
from test_v9_airborne_gait import fixture


ROOT = Path(__file__).resolve().parents[1]


def test_exact_skin_binding_rejects_omitted_real_influence_set():
    profile = json.loads(
        (ROOT / "catalog/contacts/allosaurus-engineering.v1.json").read_text()
    )
    glb = Glb(ROOT / profile["source"]["path"])
    positions, influences, *_ = _skin_influences(glb, profile)
    assert len(positions) == len(influences) == 40105
    assert len(profile["geometry"]["joint_accessors"]) == 2
    truncated = deepcopy(profile)
    truncated["geometry"]["joint_accessors"] = truncated["geometry"]["joint_accessors"][:1]
    truncated["geometry"]["weight_accessors"] = truncated["geometry"]["weight_accessors"][:1]
    with pytest.raises(ContractError, match="complete primitive attributes"):
        _skin_influences(glb, truncated)


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


def _cubic_asset(
    channels: dict[tuple[int, str], tuple[np.ndarray, np.ndarray, np.ndarray]],
    *,
    clip_name: str = "cubic",
    times: np.ndarray | None = None,
) -> Glb:
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    document = deepcopy(base.document)
    binary = bytearray(base.binary)
    times = np.array([0.0, 2.0]) if times is None else np.asarray(times, dtype=float)
    time_accessor = _append_accessor(document, binary, times.reshape((-1, 1)), "SCALAR")
    samplers, animation_channels = [], []
    for (node, path), (incoming, values, outgoing) in sorted(channels.items()):
        rows = np.stack((incoming, values, outgoing), axis=1).reshape((-1, values.shape[1]))
        output = _append_accessor(document, binary, rows, {3: "VEC3", 4: "VEC4"}[values.shape[1]])
        samplers.append({"input": time_accessor, "output": output, "interpolation": "CUBICSPLINE"})
        animation_channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})
    document["animations"] = [{"name": clip_name, "samplers": samplers, "channels": animation_channels}]
    document["buffers"][0]["byteLength"] = len(binary)
    return Glb.from_bytes(_encode(document, binary))


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


def test_linear_rotation_sampling_and_derivative_follow_shortest_slerp_in_fk():
    base, roles = fixture()
    root = base.name_to_node[roles["root"]]
    hip = base.name_to_node[roles["legs"]["left"]["contactChain"][0]]
    angle = np.radians(90.)
    rows = np.array([[0., 0., 0., 1.], [0., np.sin(angle / 2), 0., np.cos(angle / 2)]])
    glb = Glb.from_bytes(_build_glb(base, "slerp", np.array([0., 2.]), {(root, "rotation"): rows}, "q", {}))
    parsed, _ = read_animation_tracks(glb, "slerp", require_common_timeline=True)
    track = parsed[(root, "rotation")]
    assert track.sample(.5) == pytest.approx([0., np.sin(np.radians(22.5) / 2), 0., np.cos(np.radians(22.5) / 2)])
    assert track.derivative_at_key(0, terminal=False)[1] == pytest.approx(angle / 4)
    channels, _ = _animation_channels(glb, "slerp")
    world = _pose_matrices(glb, channels, .5)
    rest = _pose_matrices(glb, {}, 0.)
    pivot, point = np.asarray(rest[root])[:3, 3], np.asarray(rest[hip])[:3, 3]
    relative = point - pivot
    half = angle / 4
    expected = pivot + np.array((
        np.cos(half) * relative[0] + np.sin(half) * relative[2],
        relative[1],
        -np.sin(half) * relative[0] + np.cos(half) * relative[2],
    ))
    assert np.asarray(world[hip])[:3, 3] == pytest.approx(expected)
    antipodal = Glb.from_bytes(_build_glb(base, "slerp", np.array([0., 2.]), {(root, "rotation"): rows * np.array([[1.], [-1.]])}, "q", {}))
    antipodal_track, _ = read_animation_tracks(antipodal, "slerp", require_common_timeline=True)
    assert antipodal_track[(root, "rotation")].sample(.5) == pytest.approx(track.sample(.5))


def test_linear_short_angle_slerp_is_not_nlerp_and_antipodal_identity_is_stable():
    base, roles = fixture()
    root = base.name_to_node[roles["root"]]
    duration, angle = 1. / 120., .06
    rows = np.array([[0., 0., 0., 1.], [0., np.sin(angle / 2), 0., np.cos(angle / 2)]])
    glb = Glb.from_bytes(_build_glb(base, "short", np.array([0., duration]), {(root, "rotation"): rows}, "q", {}))
    track, _ = read_animation_tracks(glb, "short", require_common_timeline=True)
    sample = track[(root, "rotation")].sample(duration / 4)
    assert sample == pytest.approx([0., np.sin(angle / 8), 0., np.cos(angle / 8)], abs=1e-8)
    assert track[(root, "rotation")].derivative_at_key(0, terminal=False)[1] == pytest.approx(angle / (2 * duration))
    identity_antipodal = Glb.from_bytes(_build_glb(
        base, "identity", np.array([0., duration]),
        {(root, "rotation"): np.array([[0., 0., 0., 1.], [0., 0., 0., -1.]])}, "q", {},
    ))
    antipodal_track, _ = read_animation_tracks(identity_antipodal, "identity", require_common_timeline=True)
    assert antipodal_track[(root, "rotation")].sample(duration / 4) == pytest.approx([0., 0., 0., 1.])


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
    with pytest.raises(ContractError, match="unsupported"):
        endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)
    animation["samplers"][0]["interpolation"] = []
    with pytest.raises(ContractError, match="unsupported"):
        endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)


@pytest.mark.parametrize("field, value", [("input", -2), ("output", -1), ("input", 999999), ("output", 999999)])
def test_animation_sampler_rejects_out_of_range_accessor_indices(field, value):
    glb, _ = _asset_clip()
    glb.document["animations"][0]["samplers"][0][field] = value
    with pytest.raises(ContractError, match="accessor"):
        endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)


@pytest.mark.parametrize("target, change", [
    ("input", {"componentType": 5123}),
    ("input", {"normalized": False}),
    ("output", {"componentType": 5123}),
    ("output", {"normalized": False}),
])
def test_animation_sampler_requires_float_unnormalized_accessor_metadata(target, change):
    glb, _ = _asset_clip()
    sampler = glb.document["animations"][0]["samplers"][0]
    glb.document["accessors"][sampler[target]].update(change)
    with pytest.raises(ContractError, match="metadata"):
        endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)


def test_linear_reader_is_nonmutating_for_legacy_serialized_bytes():
    glb, _ = _asset_clip(scale=True)
    before = glb.raw
    animation = glb.document["animations"][0]
    output_bytes = [glb.accessor_bytes(sampler["output"]) for sampler in animation["samplers"]]
    _clip_state(glb, "exact-tangent")
    _animation_channels(glb, "exact-tangent")
    endpoint_tangent(glb, "exact-tangent", endpoint=0, terminal=False)
    assert glb.raw == before
    assert [glb.accessor_bytes(sampler["output"]) for sampler in animation["samplers"]] == output_bytes


def test_cubicspline_translation_scale_and_lbs_use_serialized_endpoint_tangents():
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    root = base.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    glb = _cubic_asset({
        (root, "translation"): (
            np.zeros((2, 3)), np.array([[0., 0., 0.], [2., 0., 0.]]), np.array([[3., 0., 0.], [0., 0., 0.]]),
        ),
        (root, "scale"): (
            np.zeros((2, 3)), np.ones((2, 3)), np.array([[1., 0., 0.], [0., 0., 0.]]),
        ),
        (root, "rotation"): (
            np.zeros((2, 4)), np.array([[0., 0., 0., 1.], [0., 0., 0., 1.]]), np.zeros((2, 4)),
        ),
    })
    tangent = endpoint_tangent(glb, "cubic", endpoint=0, terminal=False)
    assert tangent.translation_velocity[root, 0] == pytest.approx(3.)
    assert tangent.scale_velocity[root, 0] == pytest.approx(1.)
    _, skin = skinned_velocity(glb, profile, tangent)
    assert np.isfinite(skin).all()
    tracks, timeline = _clip_state(glb, "cubic")
    assert timeline == (0., 2.)
    assert len(tracks[(base.nodes[root]["name"], "translation")]) == 2
    channels, _ = _animation_channels(glb, "cubic")
    assert channels[(root, "translation")].sample(1.)[0] == pytest.approx(1.75)


def test_cubicspline_quaternion_derivative_normalizes_and_does_not_slerp_flip():
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    root = base.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    identity = np.array([[0., 0., 0., 2.], [0., 0., 0., 2.]])
    glb = _cubic_asset({
        (root, "translation"): (np.zeros((2, 3)), np.array([[0., 0., 0.], [2., 0., 0.]]), np.zeros((2, 3))),
        (root, "rotation"): (
            np.zeros((2, 4)), identity, np.array([[0., 2., 0., 2.], [0., 0., 0., 0.]]),
        ),
    })
    tangent = endpoint_tangent(glb, "cubic", endpoint=0, terminal=False)
    # Raw qdot=(0,2,0,2) at q=(0,0,0,2); normalization removes the radial
    # component, then body angular velocity is 2*q^-1*qdot = (0,2,0).
    assert tangent.angular_velocity[root] == pytest.approx([0., 2., 0.])
    parsed, _ = read_animation_tracks(glb, "cubic", require_common_timeline=True)
    assert parsed[(root, "rotation")].sample(1.)[3] < 1.


def test_cubicspline_rejects_triplet_mismatch_zero_interior_quaternion_and_dynamic_scale():
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    root = base.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    unit = np.array([[0., 0., 0., 1.], [0., 0., 0., 1.]])
    glb = _cubic_asset({
        (root, "translation"): (np.zeros((2, 3)), np.array([[0., 0., 0.], [2., 0., 0.]]), np.zeros((2, 3))),
        (root, "rotation"): (np.zeros((2, 4)), unit, np.zeros((2, 4))),
        (root, "scale"): (np.zeros((2, 3)), np.ones((2, 3)), np.array([[.1, 0., 0.], [0., 0., 0.]])),
    })
    with pytest.raises(ContractError, match="nonconstant animated scale"):
        local_cyclic_tangents(glb, "cubic")
    malformed = Glb.from_bytes(glb.raw)
    output = malformed.document["animations"][0]["samplers"][0]["output"]
    malformed.document["accessors"][output]["count"] = 2
    with pytest.raises(ContractError, match="CUBICSPLINE output"):
        read_animation_tracks(malformed, "cubic", require_common_timeline=True)
    nonfinite = _cubic_asset({
        (root, "translation"): (np.zeros((2, 3)), np.array([[0., 0., 0.], [2., 0., 0.]]), np.array([[np.nan, 0., 0.], [0., 0., 0.]])),
        (root, "rotation"): (np.zeros((2, 4)), unit, np.zeros((2, 4))),
    })
    with pytest.raises(ContractError, match="finite real"):
        read_animation_tracks(nonfinite, "cubic", require_common_timeline=True)
    opposite = _cubic_asset({
        (root, "translation"): (np.zeros((2, 3)), np.array([[0., 0., 0.], [2., 0., 0.]]), np.zeros((2, 3))),
        (root, "rotation"): (np.zeros((2, 4)), np.array([[0., 0., 0., 1.], [0., 0., 0., -1.]]), np.zeros((2, 4))),
    })
    track, _ = read_animation_tracks(opposite, "cubic", require_common_timeline=True)
    with pytest.raises(ContractError, match="interpolated animation quaternion"):
        track[(root, "rotation")].sample(1.)


def test_cubicspline_cyclic_tangent_and_interval_rate_are_both_checked():
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    root = base.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    unit = np.array([[0., 0., 0., 1.], [0., 0., 0., 1.]])
    glb = _cubic_asset({
        (root, "translation"): (np.zeros((2, 3)), np.array([[0., 0., 0.], [2., 0., 0.]]), np.zeros((2, 3))),
        (root, "rotation"): (np.zeros((2, 4)), unit, np.zeros((2, 4))),
    })
    assert emitted_cyclic_continuity(glb, loop=True)["status"] == "PASS"
    rate = emitted_rotation_rates(glb, 600.)
    assert rate["status"] == "PASS"
    assert rate["maximum_degrees_per_s"] == pytest.approx(0)
    assert "conservative" in rate["classification"]


@pytest.mark.parametrize("path", ["translation", "scale"])
def test_full_technical_rate_gate_rejects_cubic_even_when_rotation_is_linear(path):
    profile = json.loads((ROOT / "catalog/contacts/heavy-biped.v9.json").read_text())
    base = Glb(ROOT / profile["source"]["path"])
    root = base.name_to_node[profile["geometry"]["landmarks"]["root_node"]]
    channels = {
        (root, "translation"): np.array([[0., 0., 0.], [1., 0., 0.]]),
        (root, "rotation"): np.array([[0., 0., 0., 1.], [0., 0., 0., 1.]]),
        (root, "scale"): np.ones((2, 3)),
    }
    glb = Glb.from_bytes(_build_glb(base, "mixed", np.array([0., 1.]), channels, "q", {}))
    animation = glb.document["animations"][0]
    sampler = next(
        animation["samplers"][channel["sampler"]]
        for channel in animation["channels"] if channel["target"]["path"] == path
    )
    sampler["interpolation"] = "CUBICSPLINE"
    with pytest.raises(ContractError, match="CUBICSPLINE TRS"):
        emitted_rotation_rates(glb, 600.)
