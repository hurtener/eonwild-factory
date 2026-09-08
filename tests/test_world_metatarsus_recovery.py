"""Reusable world-target recovery and geometry-centered lane regressions."""
from __future__ import annotations

from dataclasses import replace
import math

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.grounded_gait import (
    GroundedGait, build_grounded_plan, sample_grounded_gait,
)
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.articulation_profile import load_articulation_profile
from eonwild_motion.solve.airborne_gait import (
    _world_metatarsus_recovery, solve_airborne_gait,
)
from eonwild_motion.solve.performance import Performance, decorate_plan
from eonwild_motion.solve.whole_body_gait_transition import _encode
from test_articulation_profile import profile_payload
from test_v9_airborne_gait import fixture


def direction(angle_degrees, forward, up):
    angle = math.radians(angle_degrees)
    return -up * math.cos(angle) + forward * math.sin(angle)


def test_world_target_declares_common_peak_and_validated_c2_gain():
    forward = np.asarray([1.0, 0.0, 1.0])
    forward /= np.linalg.norm(forward)
    up = np.asarray([0.0, 1.0, 0.0])
    assert direction(27.5, forward, up) @ forward > 0
    plan = {"foot_pitch_degrees": 8.0,
            "metatarsal_recovery_world_degrees_from_down": 27.5,
            "metatarsal_recovery_gain": .4}
    assert _world_metatarsus_recovery(plan) == (27.5, .4)
    assert _world_metatarsus_recovery({"foot_pitch_degrees": 8.0}) is None
    for one_sided in (
        {"metatarsal_recovery_world_degrees_from_down": 27.5},
        {"metatarsal_recovery_gain": .4},
    ):
        with pytest.raises(ContractError):
            _world_metatarsus_recovery(one_sided)
    for field, bad in (("metatarsal_recovery_world_degrees_from_down", False),
                       ("metatarsal_recovery_world_degrees_from_down", math.nan),
                       ("metatarsal_recovery_world_degrees_from_down", 91.0),
                       ("metatarsal_recovery_gain", -0.1),
                       ("metatarsal_recovery_gain", 1.1)):
        invalid = dict(plan, **{field: bad})
        with pytest.raises(ContractError):
            _world_metatarsus_recovery(invalid)


def test_grounded_world_target_is_c2_and_omission_preserves_old_plan():
    base = GroundedGait(cycles=1, sample_hz=24)
    assert build_grounded_plan(base, 2) == build_grounded_plan(
        replace(base, metatarsal_recovery_world_degrees_from_down=None), 2)
    gait = replace(base, metatarsal_recovery_world_degrees_from_down=27.5,
                   metatarsal_recovery_release_fraction=.7,
                   rounded_swing_peak_fraction=.42)
    start = 2 * gait.step_period_s * gait.duty_factor
    swing_duration = 2 * gait.step_period_s * (1 - gait.duty_factor)
    h = 1e-5
    def gain(u):
        return sample_grounded_gait(gait, start + u * swing_duration, 2)["feet"]["left"].get(
            "metatarsal_recovery_gain", 0.0)
    for endpoint in (0.0, 1.0):
        sign = 1 if endpoint == 0 else -1
        values = [gain(endpoint + sign * i * h) for i in (0, 1, 2)]
        assert values[0] == pytest.approx(0)
        assert abs((values[2] - 2 * values[1] + values[0]) / h**2) < .1
    peak = sample_grounded_gait(gait, start + .42 * swing_duration, 2)["feet"]["left"]
    assert peak["metatarsal_recovery_gain"] == pytest.approx(1)
    assert peak["metatarsal_recovery_world_degrees_from_down"] == 27.5


def test_geometry_centered_lanes_use_hip_midpoint_and_keep_stance_fixed():
    source, roles = fixture(upper_body=True)
    gait = GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=.2,
                        touchdown_reach_body_heights=.1)
    plan = decorate_plan(build_grounded_plan(gait, 1.8), Performance(
        lane_width_body_heights=.3, pelvis_sway_body_heights=0,
        pelvis_yaw_degrees=0, pelvis_roll_degrees=0, tail_yaw_degrees=0,
        gaze_elevation_degrees=0, center_tail=False,
        center_lanes_on_bilateral_hip_midpoint=True, skin_refinement=False))
    raw, _, _, receipt = solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles,
        gait=AirborneGait(cycles=1, sample_hz=24),
        forward_axis=(0, 0, 1), plan_override=plan, legacy_overlay=False)
    first = receipt["emitted_proxy_samples"][0]
    targets = [np.asarray(first["feet"][side]["target_foot_world_m"]) for side in ("left", "right")]
    hips = [source.name_to_node[roles["legs"][side]["contactChain"][0]] for side in ("left", "right")]
    from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices, _world_position
    worlds = _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale)
    assert .5 * (targets[0][0] + targets[1][0]) == pytest.approx(
        .5 * sum(float(np.asarray(_world_position(worlds[node]))[0]) for node in hips))
    # Constant target lanes leave every loaded toe anchor stationary.
    assert receipt["max_planted_distal_contact_step_drift_m"] < 1e-5
    assert Glb.from_bytes(raw).document["animations"]


def test_actual_staggered_rest_tracks_common_world_target_with_non_axis_forward():
    source, roles = fixture()
    for side, offset in (("left", [0, -.32, .12]), ("right", [0, -.18, .30])):
        foot = source.name_to_node[roles["legs"][side]["contactChain"][3]]
        source.nodes[foot]["translation"] = offset
    source = Glb.from_bytes(_encode(source.document, source.binary))
    forward = np.asarray([.35, 0, 1.0])
    forward /= np.linalg.norm(forward)
    gait = GroundedGait(cycles=1, sample_hz=24,
                        metatarsal_recovery_world_degrees_from_down=20,
                        metatarsal_recovery_release_fraction=.7,
                        rounded_swing_peak_fraction=.42)
    plan = build_grounded_plan(gait, 1.8)
    _, _, _, receipt = solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles,
        gait=AirborneGait(cycles=1, sample_hz=24),
        forward_axis=tuple(forward), plan_override=plan, legacy_overlay=False)
    peak = [foot for row, planned in zip(receipt["emitted_proxy_samples"], plan["samples"])
            for side, foot in row["feet"].items()
            if not foot["contact"] and abs(planned["feet"][side]["swing_phase"] - .42) < .06]
    assert peak
    assert max(abs(foot["metatarsus_world_degrees_from_down"]
                   - foot["metatarsus_world_target_degrees_from_down"])
               for foot in peak) < 1.0


def test_world_metatarsus_release_is_c2_and_finishes_before_touchdown():
    gait = GroundedGait(cycles=1, sample_hz=24,
                        metatarsal_recovery_world_degrees_from_down=10,
                        metatarsal_recovery_release_fraction=.65,
                        rounded_swing_peak_fraction=.42)
    start = 2 * gait.step_period_s * gait.duty_factor
    duration = 2 * gait.step_period_s * (1 - gait.duty_factor)
    def gain(u):
        return sample_grounded_gait(gait, start + u*duration, 2)["feet"]["left"].get(
            "metatarsal_recovery_gain", 0.)
    h=1e-5
    values=[gain(.65+i*h) for i in (-2,-1,0)]
    assert values[-1] == 0
    assert abs((values[0]-2*values[1]+values[2])/(h*h)) < .1
    assert gain(.8) == 0
    for kwargs in (
        {"metatarsal_recovery_world_degrees_from_down": 10},
        {"metatarsal_recovery_release_fraction": .65},
        {"metatarsal_recovery_world_degrees_from_down": 10,
         "metatarsal_recovery_release_fraction": .4,
         "rounded_swing_peak_fraction": .42},
    ):
        with pytest.raises(ContractError):
            GroundedGait(**kwargs)


def test_world_objective_converges_to_uncontrolled_solution_as_gain_vanishes():
    from copy import deepcopy
    source, roles = fixture()
    gait = GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=.12,
                        touchdown_reach_body_heights=.05, swing_clearance_body_heights=.08,
                        metatarsal_recovery_world_degrees_from_down=10,
                        metatarsal_recovery_release_fraction=.7,
                        rounded_swing_peak_fraction=.42)
    controlled = build_grounded_plan(gait, 1.8)
    baseline = deepcopy(controlled)
    epsilon = deepcopy(controlled)
    for old_row, tiny_row in zip(baseline["samples"], epsilon["samples"]):
        for side in ("left", "right"):
            old = old_row["feet"][side]
            tiny = tiny_row["feet"][side]
            if "metatarsal_recovery_gain" in old:
                del old["metatarsal_recovery_gain"]
                del old["metatarsal_recovery_world_degrees_from_down"]
                tiny["metatarsal_recovery_gain"] = 1e-10
    kwargs = dict(source=source, source_clip=None, semantic_roles=roles,
                  gait=AirborneGait(cycles=1, sample_hz=24),
                  forward_axis=(0, 0, 1), legacy_overlay=False)
    receipts = [solve_airborne_gait(plan_override=plan, **kwargs)[3]
                for plan in (baseline, epsilon)]
    pitches = [[foot["solved_foot_pitch_degrees"]
                for row in receipt["emitted_proxy_samples"]
                for foot in row["feet"].values()] for receipt in receipts]
    assert np.max(np.abs(np.asarray(pitches[0]) - np.asarray(pitches[1]))) < 1e-4


def test_world_target_same_phase_is_independent_of_sampling_history():
    source, roles = fixture()
    gait = GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=.12,
                        touchdown_reach_body_heights=.05, swing_clearance_body_heights=.08,
                        metatarsal_recovery_world_degrees_from_down=-20,
                        metatarsal_recovery_release_fraction=.8,
                        rounded_swing_peak_fraction=.42)
    full = build_grounded_plan(gait, 1.8)
    target_index = next(i for i, row in enumerate(full["samples"])
                        if not row["feet"]["right"]["contact"]
                        and row["feet"]["right"]["metatarsal_recovery_gain"] > .99)
    sparse = {**full, "samples": [full["samples"][0], full["samples"][target_index],
                                   full["samples"][-1]]}
    kwargs = dict(source=source, source_clip=None, semantic_roles=roles,
                  gait=AirborneGait(cycles=1, sample_hz=24), forward_axis=(0, 0, 1),
                  legacy_overlay=False)
    a = solve_airborne_gait(plan_override=full, **kwargs)[3]["emitted_proxy_samples"][target_index]
    b = solve_airborne_gait(plan_override=sparse, **kwargs)[3]["emitted_proxy_samples"][1]
    for side in ("left", "right"):
        for field in ("solved_foot_pitch_degrees", "metatarsus_world_degrees_from_down",
                      "metatarsus_world_baseline_degrees_from_down",
                      "metatarsus_world_target_degrees_from_down"):
            assert a["feet"][side].get(field) == pytest.approx(b["feet"][side].get(field), abs=1e-10)


def test_bound_profile_selects_feasible_pitch_before_soft_objectives():
    source, roles = fixture()
    raw = profile_payload()
    for phase in ("support", "swing"):
        raw["envelopes"][phase]["ankle_interior_degrees"] = {
            "hard_degrees": [150, 180], "preferred_degrees": [150, 180]}
    gait = GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=.12,
                        touchdown_reach_body_heights=.05, swing_clearance_body_heights=.08)
    receipt = solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles,
        gait=AirborneGait(cycles=1, sample_hz=24), forward_axis=(0, 0, 1),
        plan_override=build_grounded_plan(gait, 1.8), legacy_overlay=False,
        articulation_profile=load_articulation_profile(raw))[3]
    assert receipt["maximum_articulation_envelope_violation_degrees"] == 0
