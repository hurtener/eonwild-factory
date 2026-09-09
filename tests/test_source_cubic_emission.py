"""Focused source-derived CUBICSPLINE serialization contracts."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.source_cubic import (
    _align_quaternions,
    _build_cubic_glb,
    _project_quaternion_tangent,
    emit_source_cubics,
    one_sided_estimate,
    serialized_key_midpoint_times,
)
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.constant_skin_targets import (
    CanonicalConstantSkinTargetLaw,
    ConstantSkinTargetUnavailable,
)
from test_v9_airborne_gait import fixture


def test_one_sided_estimates_are_second_order_and_use_independent_samples():
    calls = []

    def quadratic(time_s):
        calls.append(time_s)
        return np.array([3 * time_s**2 + 2 * time_s + 7])

    assert one_sided_estimate(
        quadratic, 1.25, direction=1, step_s=.001
    ) == pytest.approx([9.5], abs=1e-9)
    assert calls == pytest.approx([1.25, 1.251, 1.252])
    calls.clear()
    assert one_sided_estimate(
        quadratic, 1.25, direction=-1, step_s=.001
    ) == pytest.approx([9.5], abs=1e-9)
    assert calls == pytest.approx([1.25, 1.249, 1.248])


def test_quaternion_sign_alignment_and_tangent_projection_are_antipodal_safe():
    angle = .2
    values = np.array([
        [[0., 0., 0., 1.]],
        [[0., -np.sin(angle / 2), 0., -np.cos(angle / 2)]],
    ])
    aligned = _align_quaternions(values)
    assert float(np.sum(aligned[0] * aligned[1])) > 0
    raw = np.array([[1., 2., 3., 4.]])
    tangent = _project_quaternion_tangent(aligned[0], raw)
    assert np.sum(aligned[0] * tangent, axis=1) == pytest.approx([0.])


def test_cubic_triplets_serialize_seconds_and_play_exact_normalized_hermite():
    source, _ = fixture("source-cubic", upper_body=True)
    root = 0
    times = np.array([0., 2.])
    translation = (
        np.array([[0., 0., 0.], [0., 0., 0.]]),
        np.array([[0., 0., 0.], [2., 0., 0.]]),
        np.array([[3., 0., 0.], [0., 0., 0.]]),
    )
    rotation = (
        np.zeros((2, 4)),
        np.array([[0., 0., 0., 1.], [0., 0., 0., 1.]]),
        np.zeros((2, 4)),
    )
    raw = _build_cubic_glb(
        source, "source-cubic", times,
        {(root, "translation"): translation, (root, "rotation"): rotation},
        plan_sha256="fixture", state_track={"program": "grounded_gait"},
    )
    glb = Glb.from_bytes(raw)
    tracks, timeline = read_animation_tracks(
        glb, "source-cubic", require_common_timeline=True
    )
    assert timeline == pytest.approx(times)
    track = tracks[root, "translation"]
    assert track.interpolation == "CUBICSPLINE"
    assert track.out_tangents[0] == pytest.approx([3., 0., 0.])
    # glTF multiplies the per-second tangent by the two-second interval.
    assert track.sample(1.) == pytest.approx([1.75, 0., 0.])
    assert tracks[root, "rotation"].sample(1.) == pytest.approx([0., 0., 0., 1.])


def test_midpoint_probe_clock_uses_decoded_float32_endpoints():
    source, _ = fixture("source-cubic-clock", upper_body=True)
    root = 0
    times = np.array([0., .1, .3])
    zeros3 = np.zeros((3, 3))
    values3 = np.column_stack((times, np.zeros((3, 2))))
    zeros4 = np.zeros((3, 4))
    values4 = np.repeat([[0., 0., 0., 1.]], 3, axis=0)
    raw = _build_cubic_glb(
        source, "clock", times,
        {(root, "translation"): (zeros3, values3, zeros3),
         (root, "rotation"): (zeros4, values4, zeros4)},
        plan_sha256="clock", state_track={"program": "grounded_gait"},
    )
    glb = Glb.from_bytes(raw)
    _, decoded = read_animation_tracks(glb, "clock", require_common_timeline=True)
    dense = serialized_key_midpoint_times(glb, "clock")
    assert dense == [
        float(decoded[0]), float((decoded[0] + decoded[1]) / 2),
        float(decoded[1]), float((decoded[1] + decoded[2]) / 2),
        float(decoded[2]),
    ]
    assert dense[-1] != .3


def _synthetic_checked_value(node_count, time_s):
    translations = np.zeros((node_count, 3))
    translations[:, 0] = time_s * time_s
    rotations = np.repeat([[0.0, 0.0, 0.0, 1.0]], node_count, axis=0)
    return SimpleNamespace(
        pose=SimpleNamespace(
            translations=translations.tolist(), rotations=rotations.tolist()
        ),
        row={
            "time_s": time_s,
            "flight": False,
            "support_count": 2,
            "feet": {
                "left": {"contact": True},
                "right": {"contact": True},
            },
        },
    )


def test_emitter_uses_one_checked_batch_and_serializes_source_values(monkeypatch):
    source, _ = fixture("source-cubic-batch", upper_body=True)
    law = object.__new__(CanonicalConstantSkinTargetLaw)
    calls = []

    def values(_self, times):
        calls.append(tuple(times))
        return tuple(_synthetic_checked_value(len(source.nodes), time_s) for time_s in times)

    monkeypatch.setattr(CanonicalConstantSkinTargetLaw, "values", values)
    plan = {
        "program": "grounded_gait",
        "loop": False,
        "duration_s": 0.3,
        "samples": [
            _synthetic_checked_value(len(source.nodes), time_s).row
            for time_s in (0.0, 0.1, 0.3)
        ],
    }
    result = emit_source_cubics(source, law, plan, root_node=0)
    assert len(calls) == 1
    assert tuple(sorted(calls[0])) == calls[0]
    assert result.tangent_estimate["checked_source_time_count"] == len(calls[0])
    glb = Glb.from_bytes(result.root_motion)
    tracks, decoded = read_animation_tracks(
        glb, "V9_SOURCE_CUBIC_ROOT_MOTION", require_common_timeline=True
    )
    assert decoded == pytest.approx([0.0, 0.1, 0.3])
    assert tracks[0, "translation"].values[:, 0] == pytest.approx(
        np.asarray(decoded) ** 2
    )


def test_emitter_refinement_reuses_checked_values_and_inserts_exact_source_key(monkeypatch):
    source, _ = fixture("source-cubic-refine", upper_body=True)
    law = object.__new__(CanonicalConstantSkinTargetLaw)
    calls = []

    def values(_self, times):
        calls.append(tuple(times))
        return tuple(_synthetic_checked_value(len(source.nodes), time_s) for time_s in times)

    monkeypatch.setattr(CanonicalConstantSkinTargetLaw, "values", values)
    plan = {
        "program": "grounded_gait", "loop": False, "duration_s": .2,
        "samples": [
            _synthetic_checked_value(len(source.nodes), time_s).row
            for time_s in (0., .1, .2)
        ],
    }
    initial = emit_source_cubics(source, law, plan, root_node=0)
    unchanged = emit_source_cubics(
        source, law, plan, root_node=0, reuse=initial,
    )
    assert unchanged.root_motion == initial.root_motion
    assert unchanged.in_place == initial.in_place
    assert unchanged.plan == initial.plan
    assert unchanged.midpoint_plan == initial.midpoint_plan
    refined = emit_source_cubics(
        source, law, plan, root_node=0,
        additional_key_times=(.05,), reuse=initial,
    )
    assert len(calls) == 2
    assert set(calls[0]).isdisjoint(calls[1])
    assert refined.tangent_estimate["additional_key_count"] == 1
    assert refined.tangent_estimate["new_checked_source_time_count"] == len(calls[1])
    tracks, timeline = read_animation_tracks(
        Glb.from_bytes(refined.root_motion),
        "V9_SOURCE_CUBIC_ROOT_MOTION", require_common_timeline=True,
    )
    assert timeline == pytest.approx([0., .05, .1, .2])
    assert tracks[0, "translation"].values[:, 0] == pytest.approx(
        np.asarray(timeline) ** 2
    )
    dense = serialized_key_midpoint_times(
        Glb.from_bytes(refined.root_motion), "V9_SOURCE_CUBIC_ROOT_MOTION"
    )
    assert len(dense) == len(refined.midpoint_plan["samples"])
    assert dense == pytest.approx(
        [row["time_s"] for row in refined.midpoint_plan["samples"]], abs=2e-8
    )


def test_emitter_refinement_rejects_unbound_reuse_or_outside_key(monkeypatch):
    source, _ = fixture("source-cubic-refine-invalid", upper_body=True)
    law = object.__new__(CanonicalConstantSkinTargetLaw)
    monkeypatch.setattr(
        CanonicalConstantSkinTargetLaw, "values",
        lambda _self, times: tuple(
            _synthetic_checked_value(len(source.nodes), time_s) for time_s in times
        ),
    )
    plan = {
        "program": "grounded_gait", "loop": False, "duration_s": .1,
        "samples": [
            _synthetic_checked_value(len(source.nodes), time_s).row
            for time_s in (0., .1)
        ],
    }
    initial = emit_source_cubics(source, law, plan, root_node=0)
    with pytest.raises(ContractError, match="inside the source timeline"):
        emit_source_cubics(
            source, law, plan, root_node=0,
            additional_key_times=(.2,), reuse=initial,
        )
    with pytest.raises(ContractError, match="reuse differs"):
        emit_source_cubics(
            source, object.__new__(CanonicalConstantSkinTargetLaw), plan,
            root_node=0, additional_key_times=(.05,), reuse=initial,
        )


@pytest.mark.parametrize("times", [(0., .1, .1), (0., .2, .1), (0., float("nan"), .2)])
def test_emitter_rejects_malformed_original_timeline_before_key_union(monkeypatch, times):
    source, _ = fixture("source-cubic-invalid-original-times", upper_body=True)
    law = object.__new__(CanonicalConstantSkinTargetLaw)
    monkeypatch.setattr(CanonicalConstantSkinTargetLaw, "values", lambda _self, values: ())
    plan = {
        "program": "grounded_gait", "loop": False, "duration_s": .2,
        "samples": [
            _synthetic_checked_value(len(source.nodes), time_s).row
            for time_s in times
        ],
    }
    with pytest.raises(ContractError, match="timeline must be finite and increasing"):
        emit_source_cubics(source, law, plan, root_node=0)


def test_emitter_rejects_any_typed_unavailable_checked_value(monkeypatch):
    source, _ = fixture("source-cubic-unavailable", upper_body=True)
    law = object.__new__(CanonicalConstantSkinTargetLaw)

    def unavailable(_self, times):
        return tuple(
            ConstantSkinTargetUnavailable(
                "UNAVAILABLE", time_s, "synthetic pointwise rejection", {}, {}
            )
            for time_s in times
        )

    monkeypatch.setattr(CanonicalConstantSkinTargetLaw, "values", unavailable)
    plan = {
        "program": "grounded_gait",
        "loop": False,
        "duration_s": 0.1,
        "samples": [
            {"time_s": time_s, "flight": False, "support_count": 2}
            for time_s in (0.0, 0.1)
        ],
    }
    with pytest.raises(ContractError, match="checked value unavailable.*synthetic"):
        emit_source_cubics(source, law, plan, root_node=0)
