"""V9 dynamics slice: world-frame COM, ballistic plans, capacity gates,
contact authority, continuity/turning/braking, growth hysteresis and the
runtime seam. All synthetic — no Blender, no rig files."""

from __future__ import annotations

import math

import numpy as np
import pytest

from eonwild_motion.contracts.v9_models import BodyInstanceProfile
from eonwild_motion.dynamics.ballistic import (
    BallisticRequest,
    plan_ballistic_com,
    required_horizontal_launch_velocity,
    verify_ballistic_samples,
)
from eonwild_motion.dynamics.capacity import (
    CapacityProfile,
    JointEnvelope,
    assess_landing,
    assess_takeoff,
    contracted_preferred_envelope,
    decide_attack_variant,
    friction_cone_ok,
)
from eonwild_motion.dynamics.centroidal import (
    bind_profile_segments,
    compute_centroidal_series,
    fk_world_frames,
    quat_to_matrix,
    solve_root_from_com,
)
from eonwild_motion.dynamics.contact_authority import (
    AuthorityThresholds,
    PatchFrame,
    evaluate_contact_authority,
    ground_plane_witness,
)
from eonwild_motion.dynamics.evidence import (
    figure_ballistic_vs_kinematic,
    figure_budgets_and_growth,
    figure_contact_authority,
)
from eonwild_motion.dynamics.growth import (
    DEFAULT_TIERS,
    allometric_scale,
    apply_condition,
    select_tier,
)
from eonwild_motion.dynamics.runtime import (
    NON_INTERRUPTIBLE,
    Event,
    RuntimeTrack,
    interpolate_com_plans,
)
from eonwild_motion.dynamics.transition import (
    ContinuityPacket,
    blend_packets,
    brake_plan,
    capture_step_target,
    continuity_error,
    redistribute_tail_head,
    turn_plan,
)
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.power_attack import (
    PowerAttackRequest,
    attack_entry_packet,
    plan_power_attack,
    solve_attack_root_track,
)


def _body(absolute: bool = True) -> BodyInstanceProfile:
    segments = [
        {"id": "pelvis", "parent_id": None, "role": "pelvis", "mass_fraction": 0.5,
         "com_body_m": [0.0, 1.0, 0.0], "inertia_diagonal_normalized": [0.004, 0.006, 0.004]},
        {"id": "trunk", "parent_id": "pelvis", "role": "trunk", "mass_fraction": 0.5,
         "com_body_m": [0.0, 1.6, 0.0], "inertia_diagonal_normalized": [0.006, 0.009, 0.006]},
    ]
    return BodyInstanceProfile.from_document(
        {
            "profile_id": "slice_fixture",
            "family": "heavy_predatory_biped",
            "taxon": "synthetic fixture",
            "coordinate_system": {"units": "m", "time_units": "s", "mass_units": "kg",
                                  "handedness": "right", "up_axis": "Y", "forward_axis": "-Z"},
            "dimensions": {"body_length_m": 7.0, "hip_height_m": 2.15, "body_width_m": 0.95},
            "segment_com_frame": "body",
            "mass": {"mode": "absolute" if absolute else "normalized",
                     "total_mass_kg": 1500.0 if absolute else None,
                     "mass_fraction_sum": 1.0,
                     "absolute_dynamics_enabled": absolute,
                     "absolute_policy": "fixture_absolute_allowed" if absolute else "normalized_only"},
            "provenance": {"source": "slice_test", "status": "fixture", "kind": "synthetic_fixture",
                           "scientific_claims": False},
            "segments": segments,
        }
    )


# --- centroidal / FK ------------------------------------------------------


def test_fk_chain_accumulates_translations():
    pos, rot = fk_world_frames([None, 0, 1], [(0, 0, 0), (0, 1, 0), (0, 1, 0)],
                               [(0, 0, 0, 1)] * 3)
    assert pos[2] == pytest.approx([0, 2, 0])
    assert rot[0] == pytest.approx(np.eye(3))


def test_fk_rejects_bad_topology():
    with pytest.raises(ContractError):
        fk_world_frames([None, 5], [(0, 0, 0)] * 2, [(0, 0, 0, 1)] * 2)


def test_binding_rejects_unknown_node_and_bad_sum():
    segments = [{"id": "a", "mass_fraction": 0.5, "inertia_diagonal_normalized": [1, 1, 1]},
                {"id": "b", "mass_fraction": 0.5, "inertia_diagonal_normalized": [1, 1, 1]}]
    with pytest.raises(ContractError):
        bind_profile_segments(segments, name_to_node={"root": 0}, segment_to_node={"a": "root"},
                              total_mass_kg=100.0, characteristic_height_m=2.0,
                              absolute_dynamics_enabled=True)
    with pytest.raises(ContractError):
        bind_profile_segments(
            [{"id": "a", "mass_fraction": 0.9, "inertia_diagonal_normalized": [1, 1, 1]},
             {"id": "b", "mass_fraction": 0.5, "inertia_diagonal_normalized": [1, 1, 1]}],
            name_to_node={"root": 0}, segment_to_node={"a": "root", "b": "root"},
            total_mass_kg=100.0, characteristic_height_m=2.0, absolute_dynamics_enabled=True)


def test_centroidal_rest_has_zero_momentum_and_midpoint_com():
    bindings = bind_profile_segments(
        [{"id": "a", "mass_fraction": 0.5, "inertia_diagonal_normalized": [0.01, 0.01, 0.01]},
         {"id": "b", "mass_fraction": 0.5, "inertia_diagonal_normalized": [0.01, 0.01, 0.01]}],
        name_to_node={"n0": 0, "n1": 1}, segment_to_node={"a": "n0", "b": "n1"},
        total_mass_kg=100.0, characteristic_height_m=2.0, absolute_dynamics_enabled=True)
    pos = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    rot = np.array([np.eye(3), np.eye(3)])
    series = compute_centroidal_series(bindings, times_s=[0.0, 0.1],
                                       world_positions=[pos, pos], world_rotations=[rot, rot],
                                       mass_mode="absolute")
    assert series[0].com_m == pytest.approx((1.0, 0.0, 0.0))
    assert series[0].linear_momentum_kg_mps == pytest.approx((0, 0, 0))
    assert series[0].angular_momentum_kg_m2ps == pytest.approx((0, 0, 0))


def test_centroidal_uniform_translation_carries_momentum():
    bindings = bind_profile_segments(
        [{"id": "a", "mass_fraction": 1.0, "inertia_diagonal_normalized": [0.01, 0.01, 0.01]}],
        name_to_node={"n0": 0}, segment_to_node={"a": "n0"},
        total_mass_kg=100.0, characteristic_height_m=2.0, absolute_dynamics_enabled=True)
    frames = [np.array([[t, 0.0, 0.0]]) for t in (0.0, 0.1, 0.2)]
    rots = [np.array([np.eye(3)])] * 3
    series = compute_centroidal_series(bindings, times_s=[0.0, 0.1, 0.2],
                                       world_positions=frames, world_rotations=rots,
                                       mass_mode="absolute")
    assert series[1].linear_momentum_kg_mps == pytest.approx((100.0, 0.0, 0.0), abs=1e-9)


def test_solve_root_from_com_identity():
    assert solve_root_from_com((0.0, 2.0, 0.0), np.eye(3), (0.0, 0.5, 0.0)) == pytest.approx((0, 1.5, 0))


# --- ballistic ------------------------------------------------------------


def test_ballistic_plan_matches_analytic_flight():
    request = BallisticRequest(launch_com_m=(0.0, 2.0, 0.0), launch_velocity_mps=(4.0, 3.0, 0.0),
                               landing_com_m=(2.6, 1.7, 0.0), total_mass_kg=1500.0,
                               preload_velocity_mps=(4.0, 0.0, 0.0))
    plan = plan_ballistic_com(request)
    assert plan.variant == "airborne"
    expected_t = (3.0 + math.sqrt(9.0 - 2 * 9.81 * -0.3)) / 9.81
    assert plan.flight_time_s == pytest.approx(expected_t)
    assert verify_ballistic_samples(plan.samples)["verdict"] == "PASS"
    assert plan.takeoff_impulse_ns == pytest.approx((0.0, 4500.0, 0.0))
    landing = np.asarray(plan.landing_impulse_ns)
    assert landing[1] > 0  # arrest upward impulse against downward impact


def test_ballistic_negative_discriminant_falls_back():
    request = BallisticRequest(launch_com_m=(0.0, 1.0, 0.0), launch_velocity_mps=(0.0, 1.0, 0.0),
                               landing_com_m=(0.0, 5.0, 0.0))
    plan = plan_ballistic_com(request)
    assert plan.variant == "grounded_fallback"
    assert plan.infeasibility


def test_horizontal_launch_velocity():
    assert required_horizontal_launch_velocity((4.0, 0.0), 0.5) == pytest.approx((8.0, 0.0))


def test_ballistic_verification_catches_tampering():
    plan = plan_ballistic_com(BallisticRequest(launch_com_m=(0.0, 2.0, 0.0),
                                              launch_velocity_mps=(4.0, 3.0, 0.0),
                                              landing_com_m=(2.6, 1.7, 0.0)))
    tampered = [dict(s) for s in plan.samples]
    tampered[-1] = {**tampered[-1], "com_m": [0.0, 99.0, 0.0]}
    assert verify_ballistic_samples(tampered)["verdict"] == "FAIL"


# --- capacity -------------------------------------------------------------


def test_takeoff_gentle_passes_brutal_fails():
    gentle = assess_takeoff(total_mass_kg=1500.0, takeoff_impulse_ns=(0.0, 4500.0, 0.0),
                            stance_time_s=0.28, capacity=CapacityProfile(profile_id="t"))
    assert gentle["verdict"] == "PASS"
    brutal = assess_takeoff(total_mass_kg=1500.0, takeoff_impulse_ns=(60000.0, 60000.0, 0.0),
                            stance_time_s=0.1, capacity=CapacityProfile(profile_id="t"))
    assert brutal["verdict"] == "FAIL"
    assert brutal["friction_ok"] is False or brutal["force_ok"] is False


def test_landing_energy_gate():
    soft = assess_landing(total_mass_kg=1500.0, impact_velocity_mps=(2.0, -2.0, 0.0),
                          capacity=CapacityProfile(profile_id="t"))
    assert soft["verdict"] == "PASS"
    hard = assess_landing(total_mass_kg=1500.0, impact_velocity_mps=(8.0, -12.0, 0.0),
                          capacity=CapacityProfile(profile_id="t"))
    assert hard["verdict"] == "FAIL"


def test_friction_cone():
    assert friction_cone_ok((100.0, 1000.0, 0.0), friction_coefficient=0.8)["verdict"] == "PASS"
    assert friction_cone_ok((1000.0, 100.0, 0.0), friction_coefficient=0.8)["verdict"] == "FAIL"
    assert friction_cone_ok((0.0, -50.0, 0.0), friction_coefficient=0.8)["verdict"] == "FAIL"


def test_variant_decision_reports_limiting_factor():
    takeoff = assess_takeoff(total_mass_kg=1500.0, takeoff_impulse_ns=(0.0, 4500.0, 0.0),
                             stance_time_s=0.28, capacity=CapacityProfile(profile_id="t"))
    landing = assess_landing(total_mass_kg=1500.0, impact_velocity_mps=(8.0, -12.0, 0.0),
                             capacity=CapacityProfile(profile_id="t"))
    verdict = decide_attack_variant(takeoff, landing)
    assert verdict.variant == "grounded_lunge" and verdict.limiting_factor is not None


def test_joint_envelope_contracts_inside_hard():
    envelope = JointEnvelope("hip", -45.0, 90.0, -20.0, 60.0)
    calm = contracted_preferred_envelope(envelope)
    assert calm["preferred_conditioned_deg"] == [pytest.approx(-20.0), pytest.approx(60.0)]
    loaded = contracted_preferred_envelope(envelope, joint_load_bw=2.0, joint_speed_radps=3.0)
    low, high = loaded["preferred_conditioned_deg"]
    assert low >= -45.0 and high <= 90.0 and (high - low) < 80.0
    with pytest.raises(ContractError):
        JointEnvelope("bad", 0.0, 10.0, -5.0, 5.0)


# --- contact authority ----------------------------------------------------


def _stance_frames(count: int = 12, gap: float = 0.0002, drift_per_frame: float = 0.0002):
    frames = []
    for i in range(count):
        drift = drift_per_frame * i
        sole = ((drift, gap, 0.10), (drift, gap, -0.10), (drift + 0.05, gap, 0.0))
        toe = ((drift + 0.12, gap, 0.05), (drift + 0.12, gap, -0.05))
        frames.append(PatchFrame(time_s=i / 120.0, sole_m=sole, toe_m=toe))
    return frames


def test_contact_authority_passes_clean_stance():
    report = evaluate_contact_authority(_stance_frames(), [True] * 12)
    assert report["verdict"] == "PASS"


def test_contact_authority_fails_unknown_contact():
    frames = _stance_frames(gap=0.05)  # loaded but never near the floor
    report = evaluate_contact_authority(frames, [True] * 12)
    assert report["verdict"] == "FAIL"
    assert any("no persistent ground points" in r for r in report["reasons"])


def test_contact_authority_fails_penetration_and_skate():
    penetrated = _stance_frames(gap=-0.01)
    assert evaluate_contact_authority(penetrated, [True] * 12)["verdict"] == "FAIL"
    skating = _stance_frames(drift_per_frame=0.05)
    report = evaluate_contact_authority(skating, [True] * 12)
    assert report["verdict"] == "FAIL"


def test_ground_witness_empty_is_unknown_not_zero():
    old = np.array([[0.0, 0.010, 0.0], [0.02, 0.011, 0.0]])
    new = old + np.array([0.01, 0.0, 0.0])
    witness = ground_plane_witness(old, new, up_axis=1, ground_m=0.0, tolerance_m=0.001,
                                   delta_time_s=0.01)
    assert witness["persistent_point_count"] == 0
    assert witness["maximum_velocity_mps"] is None


# --- transition -----------------------------------------------------------


def _packet(**overrides):
    base = {"root_position_m": (0.0, 1.0, 0.0), "root_orientation": (0.0, 0.0, 0.0, 1.0),
            "linear_velocity_mps": (2.0, 0.0, 0.0), "angular_momentum_kg_m2ps": (0.0, 5.0, 0.0),
            "contacts": {"left": "loaded", "right": "swing"}}
    base.update(overrides)
    return ContinuityPacket(**base)


def test_continuity_error_detects_breaks():
    assert continuity_error(_packet(), _packet())["position_error_m"] == 0.0
    error = continuity_error(_packet(), _packet(root_position_m=(1.0, 1.0, 0.0),
                                                contacts={"left": "swing", "right": "loaded"}))
    assert error["position_error_m"] == pytest.approx(1.0)
    assert error["contact_breaks"] == ["left", "right"]


def test_blend_endpoints_match_packets():
    leaving, entering = _packet(), _packet(root_position_m=(2.0, 1.0, 0.0),
                                            linear_velocity_mps=(3.0, 0.0, 0.0))
    samples = blend_packets(leaving, entering, duration_s=0.3)
    assert samples[0]["root_position_m"] == pytest.approx([0.0, 1.0, 0.0])
    assert samples[-1]["root_position_m"] == pytest.approx([2.0, 1.0, 0.0])
    assert samples[-1]["root_orientation"] == pytest.approx([0, 0, 0, 1])


def test_capture_turn_brake_formulas():
    capture = capture_step_target((0.0, 1.0, 0.0), (2.0, 0.0, 0.0), com_height_m=1.0)
    assert capture["displacement_m"] == pytest.approx(2.0 * math.sqrt(1.0 / 9.81))
    turn = turn_plan(entry_speed_mps=5.0, heading_change_deg=90.0)
    assert turn["duration_s"] == pytest.approx(1.0) and turn["steps_required"] >= 1
    brake = brake_plan(entry_speed_mps=6.0, friction_coefficient=0.8)
    assert brake["braking_distance_m"] == pytest.approx(36.0 / (2 * 0.8 * 9.81))


def test_tail_redistribution_conserves_in_flight():
    result = redistribute_tail_head((0.0, 50.0, 0.0), tail_mass_kg=120.0, tail_length_m=2.5,
                                    head_mass_kg=80.0, neck_length_m=1.0, airborne=True)
    assert "conserved" in result["conservation"]
    assert result["tail_angle_deg"] <= 35.0
    ground = redistribute_tail_head((0.0, 5000.0, 0.0), tail_mass_kg=120.0, tail_length_m=2.5,
                                    head_mass_kg=80.0, neck_length_m=1.0, airborne=False)
    assert ground["tail_angle_capped"] is True and ground["untransferred_kg_m2ps"] > 0


# --- growth ---------------------------------------------------------------


def test_allometry_and_hysteresis():
    scales = allometric_scale(0.62)
    assert scales["mass_ratio"] == pytest.approx(0.62**3)
    assert scales["cadence_ratio"] == pytest.approx(1.0 / math.sqrt(0.62))
    first = select_tier(DEFAULT_TIERS, 0.29, None)
    assert first["tier"] == "juvenile"
    # Inside hysteresis band at the 0.30 boundary: hold juvenile.
    held = select_tier(DEFAULT_TIERS, 0.31, "juvenile", hysteresis=0.05)
    assert held["tier"] == "juvenile" and held["switched"] is False
    switched = select_tier(DEFAULT_TIERS, 0.45, "juvenile", hysteresis=0.05)
    assert switched["tier"] == "subadult" and switched["switched"] is True
    assert "tail_state" in switched["carry_over"]
    assert apply_condition(100.0, 1.0) == 100.0
    with pytest.raises(ContractError):
        apply_condition(100.0, 1.5)


# --- runtime --------------------------------------------------------------


def test_runtime_track_windows_and_dispatch():
    track = RuntimeTrack(duration_s=2.0, events=[Event("L_FOOT_CONTACT", "point", 0.5),
                                                 Event("JAW_CLOSE", "point", 1.5)])
    track.add_window(NON_INTERRUPTIBLE, 1.2, 1.8)
    assert track.interruptible(0.5) is True
    assert track.interruptible(1.5) is False
    due = track.dispatch(0.0, 1.0)
    assert [e.name for e in due] == ["L_FOOT_CONTACT"]
    with pytest.raises(ContractError):
        track.add_window("bad", 1.9, 1.2)


def test_runtime_interpolation_preserves_grid():
    plan_a = [{"time_s": 0.0, "com_m": [0, 1, 0], "com_velocity_mps": [1, 0, 0]},
              {"time_s": 0.1, "com_m": [0.1, 1, 0], "com_velocity_mps": [1, 0, 0]}]
    plan_b = [{"time_s": 0.0, "com_m": [0, 2, 0], "com_velocity_mps": [2, 0, 0]},
              {"time_s": 0.1, "com_m": [0.2, 2, 0], "com_velocity_mps": [2, 0, 0]}]
    mid = interpolate_com_plans(plan_a, plan_b, alpha=0.5)
    assert mid[0]["com_m"] == pytest.approx([0, 1.5, 0])
    assert mid[0]["com_velocity_mps"] == pytest.approx([1.5, 0, 0])
    with pytest.raises(ContractError):
        interpolate_com_plans(plan_a, plan_b, alpha=1.5)


# --- power attack slice ---------------------------------------------------


def test_power_attack_feasible_airborne():
    # Running takeoff: horizontal speed carried in (preload), stance only
    # generates the vertical impulse — the economical predator launch.
    request = PowerAttackRequest(body=_body(True), capacity=CapacityProfile(profile_id="t"),
                                 launch_com_m=(0.0, 2.0, 0.0),
                                 launch_velocity_mps=(4.5, 2.5, 0.0),
                                 preload_velocity_mps=(4.5, 0.0, 0.0),
                                 landing_com_m=(2.4, 1.7, 0.0))
    receipt = plan_power_attack(request)
    assert receipt["variant"] == "airborne"
    assert receipt["physics_evaluated"] is True
    assert receipt["takeoff"]["verdict"] == "PASS"


def test_power_attack_brutal_falls_back_to_grounded():
    request = PowerAttackRequest(body=_body(True), capacity=CapacityProfile(profile_id="t"),
                                 launch_com_m=(0.0, 2.0, 0.0),
                                 launch_velocity_mps=(14.0, 9.0, 0.0),
                                 landing_com_m=(9.0, 1.7, 0.0))
    receipt = plan_power_attack(request)
    assert receipt["variant"] == "grounded_lunge"
    assert receipt["limiting_factor"] is not None


def test_power_attack_impossible_trajectory_falls_back():
    request = PowerAttackRequest(body=_body(True), capacity=CapacityProfile(profile_id="t"),
                                 launch_com_m=(0.0, 1.0, 0.0),
                                 launch_velocity_mps=(0.0, 1.0, 0.0),
                                 landing_com_m=(0.0, 6.0, 0.0))
    assert plan_power_attack(request)["variant"] == "grounded_lunge"


def test_power_attack_normalized_profile_marks_physics_unevaluated():
    request = PowerAttackRequest(body=_body(False), capacity=CapacityProfile(profile_id="t"),
                                 launch_com_m=(0.0, 2.0, 0.0),
                                 launch_velocity_mps=(4.5, 2.5, 0.0),
                                 landing_com_m=(2.4, 1.7, 0.0))
    receipt = plan_power_attack(request)
    assert receipt["variant"] == "airborne_normalized"
    assert receipt["physics_evaluated"] is False


def test_attack_root_track_and_entry_packet():
    receipt_plan = plan_ballistic_com(BallisticRequest(launch_com_m=(0.0, 2.0, 0.0),
                                                       launch_velocity_mps=(4.0, 3.0, 0.0),
                                                       landing_com_m=(2.6, 1.7, 0.0)))
    track = solve_attack_root_track(receipt_plan.samples,
                                    root_rotations=[np.eye(3)] * len(receipt_plan.samples),
                                    com_relative_to_root=(0.0, 0.5, 0.0))
    assert len(track) == len(receipt_plan.samples)
    assert track[0]["root_position_m"][1] == pytest.approx(1.5)
    packet = attack_entry_packet(root_position_m=(0, 1, 0), root_orientation=(0, 0, 0, 1),
                                 linear_velocity_mps=(4, 0, 0), angular_momentum=(0, 5, 0),
                                 contacts={"left": "loaded"}, target_commitment="prey_01")
    assert packet.interruptible is False and packet.target_commitment == "prey_01"


def test_evidence_figures_render():
    for builder in (figure_ballistic_vs_kinematic, figure_contact_authority, figure_budgets_and_growth):
        svg, facts = builder()
        assert svg.startswith("<svg") and "</svg>" in svg
        assert isinstance(facts, dict) and facts
