from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import AirborneGait, build_airborne_plan, load_airborne_gait, sample_airborne_gait, continuous_body_timing, continuous_body_state, rounded_swing_height
from eonwild_motion.solve.airborne_gait import solve_airborne_gait, active_surface_velocity, ground_plane_velocity_witness, stable_knee_geometry, _orientation_from_bend, _qrotate, periodic_response, driven_body_response
from eonwild_motion.solve.whole_body_gait_transition import _build_glb, _encode


def fixture(prefix="a", scale=1.0, upper_body=False):
    nodes = [{"name": prefix + "root", "children": [1]}, {"name": prefix + "pelvis", "translation": [0, 1.8 * scale, 0], "children": []}]
    roles = {"root": prefix + "root", "pelvis": prefix + "pelvis", "legs": {}}
    for side, sign in (("left", -1), ("right", 1)):
        start = len(nodes)
        nodes[1]["children"].append(start)
        names = [prefix + side + part for part in ("hip", "knee", "ankle", "foot", "toe0", "toe1", "toe2")]
        offsets = [(sign * .18, -.15, 0), (0, -.55, .3), (0, -.65, -.2), (0, -.25, .25), (0, 0, .15), (0, 0, .13), (0, 0, .1)]
        for i, (name, offset) in enumerate(zip(names, offsets)):
            node = {"name": name, "translation": [x * scale for x in offset]}
            if i < 6:
                node["children"] = [start + i + 1]
            nodes.append(node)
        roles["legs"][side] = {"contactChain": names[:4], "toeChains": [names[4:]]}
    if upper_body:
        for chain, offsets in ((["chest", "neck", "head"], [(0, .1, .3)] * 3), (["tail0", "tail1", "tail2"], [(0, 0, -.35)] * 3)):
            parent = 1
            for name, offset in zip(chain, offsets):
                node = len(nodes)
                nodes[parent].setdefault("children", []).append(node)
                nodes.append({"name": prefix + name, "translation": [v * scale for v in offset]})
                parent = node
        roles.update(chest=prefix + "chest", neck=[prefix + "neck"], head=prefix + "head", tail=[prefix + "tail" + str(i) for i in range(3)])
    doc = {"asset": {"version": "2.0"}, "nodes": nodes, "scenes": [{"nodes": [0]}], "scene": 0, "buffers": [{"byteLength": 4}], "bufferViews": [], "accessors": []}
    base = Glb.from_bytes(_encode(doc, b"\0" * 4))
    blob = _build_glb(base, "source", np.array([0., 1.]), {(0, "translation"): np.array([[0., 0., 0.], [0., 0., 2. * scale]])}, "fixture", {})
    return Glb.from_bytes(blob), roles


def test_per_foot_duty_is_half_step_contact_fraction():
    gait = AirborneGait()
    assert gait.duty_factor == pytest.approx(11 / 30)
    plan = build_airborne_plan(gait, 2)
    assert plan["same_foot_cycle_s"] == 2 * gait.step_period_s
    assert plan["flight_seconds_per_step"] == pytest.approx(4 / 24)
    samples = [sample_airborne_gait(gait, (i + .5) / 2400, 2) for i in range(3000)]
    assert sum(r["flight"] for r in samples) / len(samples) == pytest.approx(4 / 15)
    assert {r["support_count"] for r in samples} == {0, 1}


def test_stance_anchor_static_world_and_real_flight():
    gait = AirborneGait()
    rows = [sample_airborne_gait(gait, t, 2) for t in (.05, .15, .35)]
    assert len({r["feet"]["left"]["forward_m"] for r in rows}) == 1
    assert rows[-1]["root_forward_m"] > rows[0]["root_forward_m"]
    flight = sample_airborne_gait(gait, .54, 2)
    assert flight["flight"] and all(f["height_m"] > 0 for f in flight["feet"].values())
    assert flight["pelvis_height_offset_m"] > 0


def test_toe_roll_loads_during_late_stance_and_is_continuous_at_toeoff():
    gait = AirborneGait()
    toeoff = gait.step_period_s * (1 - gait.flight_fraction)
    before = sample_airborne_gait(gait, toeoff - 1e-6, 2)["feet"]["left"]
    after = sample_airborne_gait(gait, toeoff + 1e-6, 2)["feet"]["left"]
    assert before["contact"] and before["toe_flex_degrees"] > 10
    for key in ("forward_m", "height_m", "toe_flex_degrees", "foot_pitch_degrees"):
        assert before[key] == pytest.approx(after[key], abs=1e-6)


def test_plan_parameter_mutations_are_causal():
    g = AirborneGait()
    for key in ("step_period_s", "flight_fraction", "step_length_body_heights", "touchdown_reach_body_heights", "swing_clearance_body_heights", "swing_lift_fraction", "swing_lower_fraction", "pelvis_compression_body_heights", "flight_height_body_heights", "toe_flex_degrees", "foot_recovery_pitch_degrees", "push_off_pitch_degrees", "compression_peak_fraction", "push_off_start_fraction"):
        changed = replace(g, **{key: getattr(g, key) * .85})
        assert build_airborne_plan(g, 2)["samples"] != build_airborne_plan(changed, 2)["samples"], key


def test_contact_transition_velocities_and_unwrapped_loop_are_continuous():
    gait = AirborneGait()
    toeoff = gait.step_period_s * (1 - gait.flight_fraction)
    period = 2 * gait.step_period_s
    h = 1e-5
    for t in (toeoff, period):
        rows = [sample_airborne_gait(gait, t + delta, 2) for delta in (-h, 0, h)]
        for key in ("forward_m", "height_m", "toe_flex_degrees", "foot_pitch_degrees"):
            values = [row["feet"]["left"][key] for row in rows]
            assert (values[1] - values[0]) / h == pytest.approx((values[2] - values[1]) / h, abs=.03)
        heights = [row["pelvis_height_offset_m"] for row in rows]
        assert (heights[1] - heights[0]) / h == pytest.approx((heights[2] - heights[1]) / h, abs=.003)
    swing = [sample_airborne_gait(gait, toeoff + (period - toeoff) * i / 100, 2)["feet"]["left"]["forward_m"] for i in range(101)]
    assert all(b >= a for a, b in zip(swing, swing[1:]))


def test_invalid_profiles_reject():
    for change in ({"flight_fraction": 0}, {"step_period_s": -1}, {"toe_flex_degrees": math.nan}, {"cycles": 1.5}, {"sample_hz": True}):
        with pytest.raises(ContractError):
            AirborneGait(**change)
    profile = json.loads((Path(__file__).resolve().parents[1] / "profiles/v9/program.airborne-gait.run.json").read_text())
    assert load_airborne_gait(profile).duty_factor < .5


def test_active_contact_velocity_excludes_lifted_skin_but_detects_skate():
    old = np.array([[0., .01, 0.], [.02, .011, 0.], [.04, .01, 0.], [.06, .025, 0.]])
    new = old.copy()
    new[-1] += [0.1, .001, 0]
    kwargs = dict(up_axis=1, ground_m=0, floor_gap_m=.03, delta_time_s=.01)
    velocity, count = active_surface_velocity(old, new, **kwargs)
    assert velocity == 0 and count == 3
    new[:3, 0] += .01
    assert active_surface_velocity(old, new, **kwargs)[0] == pytest.approx(1.0)


def test_actual_ground_metric_does_not_call_a_lifted_patch_zero_skate():
    old = np.array([[0., .010, 0.], [.02, .011, 0.]])
    new = old + [0.01, 0., 0.]
    kwargs = dict(up_axis=1, ground_m=0, tolerance_m=.001, delta_time_s=.01)
    lifted = ground_plane_velocity_witness(old, new, **kwargs)
    assert lifted["persistent_point_count"] == 0
    assert lifted["maximum_velocity_mps"] is None
    old[:, 1] = new[:, 1] = .0002
    grounded = ground_plane_velocity_witness(old, new, **kwargs)
    assert grounded["persistent_point_count"] == 2
    assert grounded["maximum_tangential_velocity_mps"] == pytest.approx(1.0)
    assert grounded["previous_ground_gap_m"] == pytest.approx(.0002)


def test_stable_geometry_does_not_flip_across_the_old_source_pole_ray():
    hip = np.zeros(3)
    normal = np.array([1., 0., 0.])
    knees = []
    for angle in np.linspace(-.08, .08, 101):
        # Sweep the ankle ray through the source upper-leg direction: the old
        # projected-source-pole approach switches knee branches at the center.
        target = np.array([0., -math.cos(.6 + angle), math.sin(.6 + angle)]) * 1.1
        knee, ankle, extension = stable_knee_geometry(hip, target, .96, 1.15, normal)
        assert extension == 0
        assert np.cross(knee - hip, ankle - knee) @ normal > 0
        assert np.linalg.norm(knee - hip) == pytest.approx(.96)
        assert np.linalg.norm(ankle - knee) == pytest.approx(1.15)
        knees.append(knee)
    assert np.linalg.norm(np.diff(knees, axis=0), axis=1).max() < .003


def test_anatomical_frame_preserves_twist_as_knee_lifts():
    # Matching just the upper-leg direction leaves its axial twist undefined.
    # Both the bone axis and source anatomical normal must reach the target.
    source_upper = np.array([.04, -.96, .10])
    source_upper /= np.linalg.norm(source_upper)
    source_normal = np.cross(source_upper, [0., -.6, -.5])
    source_normal /= np.linalg.norm(source_normal)
    for angle in np.linspace(-.7, 1.3, 41):
        target_upper = np.array([0., -math.cos(angle), math.sin(angle)])
        target_normal = np.array([1., 0., 0.])
        delta = _orientation_from_bend(source_upper, source_normal, target_upper, target_normal)
        assert _qrotate(delta, source_upper) == pytest.approx(target_upper, abs=1e-8)
        assert _qrotate(delta, source_normal) == pytest.approx(target_normal, abs=1e-8)


def test_recovery_pitch_releases_heel_before_mid_swing_without_a_phase_kink():
    gait = AirborneGait(push_off_pitch_degrees=60, foot_recovery_pitch_degrees=30)
    toeoff = gait.step_period_s * (1 - gait.flight_fraction)
    swing_duration = 2 * gait.step_period_s - toeoff
    peak = toeoff + swing_duration * gait.swing_recovery_peak_fraction
    h = 1e-5
    values = [sample_airborne_gait(gait, peak + d, 2)["feet"]["left"]["foot_pitch_degrees"] for d in (-h, 0, h)]
    assert values[1] == pytest.approx(-30)
    assert (values[1] - values[0]) / h == pytest.approx((values[2] - values[1]) / h, abs=.001)


@pytest.mark.parametrize("polished", [False, True])
def test_emitted_renamed_binding_and_morphology_are_equivariant(polished):
    gait = AirborneGait(cycles=1, sample_hz=24, step_length_body_heights=.38, touchdown_reach_body_heights=.17, swing_clearance_body_heights=.18)
    if polished:
        gait = replace(gait, continuous_body_launch_fraction=.85, rounded_swing_peak_fraction=.42, swing_lift_fraction=.24, swing_lower_fraction=.32, swing_hip_lift_degrees=48)
    outputs = []
    for prefix, scale in (("a", 1), ("completely_renamed_", 1.6)):
        source, roles = fixture(prefix, scale, upper_body=polished)
        if polished:
            gait = replace(gait, chest_response_gain_degrees=2, tail_response_gain_degrees=12, front_body_pitch_degrees=10, tail_elevation_degrees=18, swing_approach_lift_body_heights=.03)
        root, inplace, plan, receipt = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=gait)
        assert receipt["flight_sample_count"] > 0
        assert receipt["max_foot_target_residual_m"] < 1e-5
        assert receipt["max_planted_distal_contact_step_drift_m"] < 1e-5
        assert receipt["max_planted_distal_contact_velocity_mps"] < 1e-4
        assert receipt["minimum_toe_joint_height_m"] > -1e-5
        assert receipt["final_skinned_contact_gate"] == "NOT_YET_MEASURED"
        root_glb, ip_glb = Glb.from_bytes(root), Glb.from_bytes(inplace)
        if polished:
            assert receipt["body_response"]["maximum_cyclic_state_seam_degrees"] < 1e-10
            rotations = root_glb.animation_accessors("V9_AIRBORNE_RUN_ROOT_MOTION", "rotation")
            for name in [roles["chest"], roles["head"], *roles["neck"], *roles["tail"]]:
                values = np.array(root_glb.accessor_values(rotations[name]))
                assert values[0] == pytest.approx(values[-1], abs=1e-7)
                assert np.max(np.linalg.norm(values - values[0], axis=1)) > 1e-4
        root_t = root_glb.animation_accessors("V9_AIRBORNE_RUN_ROOT_MOTION", "translation")
        ip_t = ip_glb.animation_accessors("V9_AIRBORNE_RUN_IN_PLACE", "translation")
        for name, acc in root_t.items():
            values = root_glb.accessor_values(acc)
            if name not in {roles["root"], roles["pelvis"]}:
                assert all(row == values[0] for row in values)
            if name != roles["root"]:
                assert values == ip_glb.accessor_values(ip_t[name])
        outputs.append((receipt, plan))
    assert outputs[1][0]["body_height_m"] == pytest.approx(outputs[0][0]["body_height_m"] * 1.6)
    a = outputs[0][1]["samples"][-1]["root_forward_m"]
    assert outputs[1][1]["samples"][-1]["root_forward_m"] == pytest.approx(a * 1.6)


def test_periodic_response_has_no_startup_transient_and_tracks_actual_drive():
    times = np.linspace(0, 1.25, 151)
    assert periodic_response(times, np.ones(len(times)) * .3, .06) == pytest.approx(np.ones(len(times)) * .3)
    gait = AirborneGait(continuous_body_launch_fraction=.85, chest_response_gain_degrees=2, tail_response_gain_degrees=12)
    roles = {"chest": "c", "head": "h", "neck": ["n"], "tail": ["t0", "t1", "t2"]}
    a = driven_body_response(gait, build_airborne_plan(gait, 2), roles)
    b = driven_body_response(gait, build_airborne_plan(gait, 3.2), roles)
    assert a["maximum_cyclic_state_seam_degrees"] < 1e-10
    for x, y in zip(a["samples"], b["samples"]):
        assert x["sagittal_node_degrees"] == pytest.approx(y["sagittal_node_degrees"])
    assert driven_body_response(AirborneGait(), build_airborne_plan(AirborneGait(), 2), roles) is None
    plan = build_airborne_plan(gait, 2)
    for row in plan["samples"]:
        row["pelvis_vertical_velocity_mps"] = 0
    zero = driven_body_response(gait, plan, roles)
    assert all(abs(v) < 1e-12 for row in zero["samples"] for v in row["sagittal_node_degrees"].values())


def test_distributed_sprint_posture_is_opt_in_and_does_not_move_leg_targets():
    run = AirborneGait(continuous_body_launch_fraction=.85)
    sprint = replace(run, step_period_s=11.5 / 24, flight_fraction=.22, continuous_body_launch_fraction=.9)
    inclined = replace(sprint, front_body_pitch_degrees=10, tail_elevation_degrees=18)
    assert run.flight_fraction > sprint.flight_fraction > 2 / 11.5
    assert build_airborne_plan(sprint, 2)["samples"] == build_airborne_plan(inclined, 2)["samples"]
    for change in ({"front_body_pitch_degrees": 21}, {"tail_elevation_degrees": 31}, {"front_body_pitch_degrees": -1}):
        with pytest.raises(ContractError):
            replace(run, **change)


def test_flight_exchange_lift_is_c2_and_never_moves_loaded_feet():
    base = AirborneGait(flight_fraction=.22)
    lifted = replace(base, flight_foot_lift_body_heights=.10)
    toeoff = base.step_period_s * (1 - base.flight_fraction)
    end = base.step_period_s
    for t in np.linspace(0, 2 * end, 241):
        a, b = (sample_airborne_gait(g, float(t), 2) for g in (base, lifted))
        assert a["root_forward_m"] == b["root_forward_m"]
        assert a["pelvis_height_offset_m"] == b["pelvis_height_offset_m"]
        for side in ("left", "right"):
            assert a["feet"][side]["forward_m"] == b["feet"][side]["forward_m"]
            if not a["flight"]:
                assert a["feet"][side] == b["feet"][side]
    mid = (toeoff + end) * .5
    assert sample_airborne_gait(lifted, mid, 2)["feet"]["left"]["height_m"] - sample_airborne_gait(base, mid, 2)["feet"]["left"]["height_m"] == pytest.approx(.2)
    h = 1e-6
    def added(t):
        return sample_airborne_gait(lifted, t, 2)["feet"]["left"]["height_m"] - sample_airborne_gait(base, t, 2)["feet"]["left"]["height_m"]
    for t in (toeoff, end):
        assert abs((added(t+h)-added(t-h))/(2*h)) < 1e-6
        assert abs((added(t+h)-2*added(t)+added(t-h))/(h*h)) < .01


def test_continuous_body_c2_launch_and_loop_keep_original_extrema():
    gait = AirborneGait(continuous_body_launch_fraction=.85)
    height = 2.0
    trough, rise = continuous_body_timing(gait)
    minimum = continuous_body_state(gait, trough * gait.step_period_s, height)[0]
    maximum = continuous_body_state(gait, (trough + rise) * gait.step_period_s, height)[0]
    launch = continuous_body_state(gait, (1 - gait.flight_fraction) * gait.step_period_s, height)
    assert maximum - minimum == pytest.approx((gait.pelvis_compression_body_heights + gait.flight_height_body_heights) * height)
    assert (launch[0] - minimum) / (maximum - minimum) == pytest.approx(.85)
    assert launch[1] > 0
    for phase in (0, trough, 1 - gait.flight_fraction, trough + rise, 1):
        t = phase * gait.step_period_s
        a, b = (continuous_body_state(gait, t + d, height) for d in (-1e-7, 1e-7))
        assert a == pytest.approx(b, abs=.001)
    assert continuous_body_state(gait, 0, height) == pytest.approx(continuous_body_state(gait, 2 * gait.step_period_s, height))


def test_rounded_clearance_has_no_plateau_and_keeps_c2_contact_endpoints():
    peak = .42
    assert rounded_swing_height(peak, peak) == pytest.approx(1)
    samples = [rounded_swing_height(i / 1000, peak) for i in range(1001)]
    assert max(samples) <= 1 + 1e-12
    assert sum(abs(value - 1) < 1e-8 for value in samples) == 1
    # The one-sided second difference of a cubic endpoint converges O(h).
    h = 1e-6
    for endpoint, direction in ((0, 1), (1, -1)):
        y1 = rounded_swing_height(endpoint + direction * h, peak)
        y2 = rounded_swing_height(endpoint + direction * 2 * h, peak)
        assert y1 / h < 1e-6
        assert abs((y2 - 2 * y1) / (h * h)) < .02


def test_polish_preserves_schedule_static_stance_anchors_and_forward_stroke():
    original = AirborneGait()
    polished = replace(original, continuous_body_launch_fraction=.85, rounded_swing_peak_fraction=.42, swing_lift_fraction=.24, swing_lower_fraction=.32, swing_hip_lift_degrees=48)
    for i in range(301):
        time = i * (2 * original.step_period_s) / 300
        a, b = (sample_airborne_gait(g, time, 2.5) for g in (original, polished))
        assert a["root_forward_m"] == b["root_forward_m"]
        assert a["flight"] == b["flight"]
        for side in ("left", "right"):
            assert a["feet"][side]["forward_m"] == b["feet"][side]["forward_m"]
            assert a["feet"][side]["contact"] == b["feet"][side]["contact"]
            if b["feet"][side]["contact"]:
                assert b["feet"][side]["height_m"] == 0


def test_approach_lift_preserves_stroke_and_contact_with_c2_join():
    base = AirborneGait(cycles=1)
    lifted = replace(base, swing_approach_lift_body_heights=.08)
    toeoff = base.step_period_s * (1 - base.flight_fraction)
    swing = 2 * base.step_period_s - toeoff
    def extra(u):
        t = toeoff + u * swing
        return sample_airborne_gait(lifted, t, 2)["feet"]["left"]["height_m"] - sample_airborne_gait(base, t, 2)["feet"]["left"]["height_m"]
    assert extra(.78) == pytest.approx(.16)
    h = 1e-6
    for u in (.55, .78, 1):
        assert (extra(u + h) - extra(u)) / h == pytest.approx((extra(u) - extra(u - h)) / h, abs=.001)
        assert abs((extra(u + h) - 2 * extra(u) + extra(u - h)) / h**2) < .01
    for t in np.linspace(0, 2 * base.step_period_s, 301):
        a, b = (sample_airborne_gait(g, t, 2) for g in (base, lifted))
        assert a["root_forward_m"] == b["root_forward_m"]
        for side in ("left", "right"):
            assert a["feet"][side]["forward_m"] == b["feet"][side]["forward_m"]
            if a["feet"][side]["contact"]:
                assert a["feet"][side] == b["feet"][side]


def test_emitted_parameter_mutations_change_real_channels_and_contact_times():
    source, roles = fixture()
    base = AirborneGait(cycles=1, sample_hz=48, step_length_body_heights=.38, touchdown_reach_body_heights=.17, swing_clearance_body_heights=.18)
    original, _, _, _ = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=base)
    baseline = Glb.from_bytes(original)
    clip = "V9_AIRBORNE_RUN_ROOT_MOTION"
    def values(glb, node, path):
        return glb.accessor_values(glb.animation_accessors(clip, path)[node])
    for parameter, node, path in (("toe_flex_degrees", roles["legs"]["left"]["toeChains"][0][-1], "rotation"), ("foot_recovery_pitch_degrees", roles["legs"]["left"]["contactChain"][2], "rotation"), ("pelvis_compression_body_heights", roles["pelvis"], "translation"), ("flight_height_body_heights", roles["pelvis"], "translation")):
        mutated, _, _, _ = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=replace(base, **{parameter: getattr(base, parameter) * .5}))
        assert values(Glb.from_bytes(mutated), node, path) != values(baseline, node, path), parameter
    crouched, _, _, _ = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=replace(base, pelvis_crouch_body_heights=.03))
    assert values(Glb.from_bytes(crouched), roles["pelvis"], "translation") != values(baseline, roles["pelvis"], "translation")
    mutated, _, _, receipt = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=replace(base, flight_fraction=.4))
    changed = Glb.from_bytes(mutated)
    state0 = baseline.document["extras"]["eonwildMotionStateTrack"]["samples"]
    state1 = changed.document["extras"]["eonwildMotionStateTrack"]["samples"]
    assert min(s["time_s"] for s in state1 if s["flight"]) < min(s["time_s"] for s in state0 if s["flight"])
    assert values(changed, roles["legs"]["left"]["contactChain"][0], "rotation") != values(baseline, roles["legs"]["left"]["contactChain"][0], "rotation")
    assert receipt["max_planted_distal_contact_velocity_mps"] < 1e-4
