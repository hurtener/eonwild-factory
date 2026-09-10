from __future__ import annotations

import numpy as np
import pytest

from eonwild_motion.dynamics.body_support_bridge import (
    FinalGeometrySample,
    build_surface_mass_trial_evaluator,
)
from eonwild_motion.errors import ContractError


ANCHOR = "a" * 64
SUPPORT = ((-0.1, 0.0, -0.1), (0.1, 0.0, -0.1), (0.1, 0.0, 0.1), (-0.1, 0.0, 0.1))


def _profile(mass: float = 10.0):
    return {"mass_model": {"total_mass_kg": mass}}


def _patch_vertex_evaluator(monkeypatch):
    def vertex_state(source, profile, matrices):
        position = np.asarray(matrices["root"], dtype=float)[:3, 3]
        mass = float(profile["mass_model"]["total_mass_kg"])
        return {
            "total_mass_kg": mass,
            "vertex_mass_kg": np.array([mass]),
            "world_positions_m": position[None, :],
            "com_m": position,
        }

    monkeypatch.setattr(
        "eonwild_motion.dynamics.body_support_bridge.prepare_surface_mass_vertex_evaluator",
        lambda source, profile: lambda matrices: vertex_state(source, profile, matrices),
    )


def _geometry(*, travel=(0.0, 0.0, 1.0), anchor=ANCHOR, passed=True, calls=None):
    def evaluate(delta, time_s):
        if calls is not None:
            calls.append((time_s, delta))
        matrix = np.eye(4)
        matrix[:3, 3] = np.asarray(travel) * time_s
        return FinalGeometrySample(
            time_s,
            {"root": matrix},
            tuple((x, y, z + 10.0 * time_s) for x, y, z in SUPPORT),
            anchor,
            passed,
        )

    return evaluate


def test_bridge_aligns_midpoint_support_and_unwraps_travel_seam(monkeypatch) -> None:
    _patch_vertex_evaluator(monkeypatch)
    calls = []
    evaluator = build_surface_mass_trial_evaluator(
        source_bytes=b"bound",
        surface_mass_profile=_profile(),
        duration_s=1.0,
        body_height_m=2.0,
        sample_count=5,
        cycle_travel_m=(0.0, 0.0, 1.0),
        frozen_anchor_sha256=ANCHOR,
        evaluate_final_geometry=_geometry(calls=calls),
    )
    trial = evaluator((0.0,) * 12)
    assert [sample.time_s for sample in trial.samples] == pytest.approx(
        [0.1, 0.3, 0.5, 0.7, 0.9]
    )
    np.testing.assert_allclose(
        np.asarray([sample.linear_momentum_kg_mps for sample in trial.samples]),
        np.asarray([(0.0, 0.0, 10.0)] * 5),
        rtol=0.0,
        atol=1e-12,
    )
    assert trial.samples[-1].com_m == pytest.approx((0.0, 0.0, 0.9))
    assert trial.samples[1].support_points_m[0][2] == pytest.approx(2.9)
    assert [time for time, _ in calls] == pytest.approx(
        [0.0, 0.2, 0.4, 0.6, 0.8, 0.1, 0.3, 0.5, 0.7, 0.9]
    )


def test_bridge_forwards_periodic_body_coefficients_to_every_geometry_call(monkeypatch) -> None:
    _patch_vertex_evaluator(monkeypatch)
    calls = []
    evaluator = build_surface_mass_trial_evaluator(
        source_bytes=b"bound",
        surface_mass_profile=_profile(),
        duration_s=1.0,
        body_height_m=2.0,
        sample_count=5,
        cycle_travel_m=(0.0, 0.0, 1.0),
        frozen_anchor_sha256=ANCHOR,
        evaluate_final_geometry=_geometry(calls=calls),
    )
    coefficients = (0.01,) + (0.0,) * 11
    evaluator(coefficients)
    assert calls[0][1].translation_m == pytest.approx((0.0, 0.0, 0.0))
    assert calls[5][1].translation_m[0] != 0.0


@pytest.mark.parametrize(
    ("profile,anchor,passed,reason"),
    [
        (_profile(0.0), ANCHOR, True, "total mass"),
        (_profile(), "b" * 64, True, "frozen material anchors"),
        (_profile(), ANCHOR, False, "final full-skin geometry"),
    ],
)
def test_bridge_fails_closed_on_invalid_mass_anchor_or_geometry(
    monkeypatch, profile, anchor, passed, reason
) -> None:
    _patch_vertex_evaluator(monkeypatch)
    if profile["mass_model"]["total_mass_kg"] <= 0:
        with pytest.raises(ContractError, match=reason):
            build_surface_mass_trial_evaluator(
                source_bytes=b"bound",
                surface_mass_profile=profile,
                duration_s=1.0,
                body_height_m=2.0,
                sample_count=5,
                cycle_travel_m=(0.0, 0.0, 1.0),
                frozen_anchor_sha256=ANCHOR,
                evaluate_final_geometry=_geometry(),
            )
        return
    evaluator = build_surface_mass_trial_evaluator(
        source_bytes=b"bound",
        surface_mass_profile=profile,
        duration_s=1.0,
        body_height_m=2.0,
        sample_count=5,
        cycle_travel_m=(0.0, 0.0, 1.0),
        frozen_anchor_sha256=ANCHOR,
        evaluate_final_geometry=_geometry(anchor=anchor, passed=passed),
    )
    with pytest.raises(ContractError, match=reason):
        evaluator((0.0,) * 12)


def test_bridge_rejects_callback_time_alias(monkeypatch) -> None:
    _patch_vertex_evaluator(monkeypatch)

    def wrong_time(delta, time_s):
        sample = _geometry()(delta, time_s)
        return FinalGeometrySample(
            time_s + 1e-4,
            sample.joint_world_matrices,
            sample.support_points_m,
            sample.frozen_anchor_sha256,
            True,
        )

    evaluator = build_surface_mass_trial_evaluator(
        source_bytes=b"bound",
        surface_mass_profile=_profile(),
        duration_s=1.0,
        body_height_m=2.0,
        sample_count=5,
        cycle_travel_m=(0.0, 0.0, 1.0),
        frozen_anchor_sha256=ANCHOR,
        evaluate_final_geometry=wrong_time,
    )
    with pytest.raises(ContractError, match="sample time"):
        evaluator((0.0,) * 12)
