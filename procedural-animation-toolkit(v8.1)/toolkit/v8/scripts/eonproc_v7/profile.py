"""Typed quality configuration for Eonwild procedural animation V7.

V7 is the contact-locked rebuild after the V6 pelvis/export regression.  The
profile deliberately keeps whole-body translation small during relaxed motion,
fits the user-supplied walking reference, and adds explicit large-theropod turn
anticipation in the head, neck, chest and tail.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

from eonproc_v4.profile import BipedV4Profile


@dataclass(frozen=True)
class BipedV7Profile(BipedV4Profile):
    # Reference-fitted relaxed walk from tarbosaurus_walk(1).mp4.
    name: str = "tarbosaurus_reference_fitted_v7_contact_locked"
    reference_hip_height_m: float = 2.75
    cycle_hz: float = 0.64
    stride_length_m: float = 1.58
    stance_fraction: float = 0.66
    contact_lead_stride: float = 0.54

    # Compact, readable foot path.  The leg folds before it advances and is
    # already extending before the next contact.
    swing_lift_hip_fraction: float = 0.058
    swing_outward_hip_fraction: float = 0.0035
    load_ramp_fraction: float = 0.18
    toe_off_window_fraction: float = 0.16
    precontact_window_fraction: float = 0.25
    swing_advance_start_fraction: float = 0.08
    swing_advance_end_fraction: float = 0.89
    swing_lift_rise_fraction: float = 0.38
    swing_lift_fall_start_fraction: float = 0.58
    swing_ankle_deg: float = 9.0
    toe_off_foot_deg: float = 7.0
    contact_foot_deg: float = 1.0
    toe_push_deg: float = 8.0

    # Contact-solved pelvis motion.  These amplitudes are intentionally small:
    # the reference reads its weight mostly through the articulated legs, not
    # by translating the complete body from side to side.
    pelvis_support_shift_gain: float = 0.022
    pelvis_vertical_bob_hip_fraction: float = 0.0045
    pelvis_loading_drop_hip_fraction: float = 0.0035
    pelvis_forward_sway_hip_fraction: float = 0.0018
    pelvis_roll_deg: float = 1.35
    pelvis_yaw_deg: float = 1.55
    pelvis_pitch_deg: float = 0.50

    # Living-neutral posture.  Running/sprinting will get a separate aggressive
    # forward-lean profile later rather than contaminating the relaxed walk.
    body_lean_deg: float = -0.75
    pelvis_neutral_pitch_deg: float = 0.10
    neck_relaxed_pitch_deg: float = -0.35
    head_horizon_pitch_deg: float = 0.35

    # Anatomical leg preferences and hard signed bend constraints.
    hip_swing_deg: float = 16.0
    hip_extension_limit_deg: float = 28.0
    hip_flexion_limit_deg: float = 34.0
    hip_abduction_limit_deg: float = 9.0
    knee_min_flex_deg: float = 18.0
    knee_max_flex_deg: float = 112.0
    knee_stance_flex_deg: float = 45.0
    knee_loading_flex_deg: float = 4.0
    knee_swing_flex_deg: float = 80.0
    ankle_min_flex_deg: float = 16.0
    ankle_max_flex_deg: float = 104.0
    ankle_stance_flex_deg: float = 46.0
    ankle_swing_flex_deg: float = 68.0
    leg_preference_weight: float = 0.17
    leg_continuity_weight: float = 0.22
    leg_max_solver_evaluations: int = 12

    # Whole-body residual motion.
    spine_counter_gain: float = 0.44
    neck_stabilize_gain: float = 0.45
    head_stabilize_gain: float = 0.58
    arm_inertia_deg: float = 2.4
    breathing_chest_deg: float = 0.85
    breathing_neck_deg: float = 0.32
    neutral_jaw_close_deg: float = 50.0
    jaw_breath_deg: float = 0.28
    head_micro_yaw_deg: float = 0.35
    asymmetry_fraction: float = 0.008

    # Terrain validation profile.  V7 keeps the showcase undulation broad
    # enough for the ankle/sole solver to follow without introducing a
    # one-sample knee acceleration spike.  More severe terrain remains a
    # runtime stress profile rather than the default production walk.
    uneven_terrain_amplitude_hip_fraction: float = 0.016
    uneven_terrain_wavelength_m: float = 2.40

    # Dense internal solve and browser-ready export.
    internal_sample_hz: int = 120
    export_sample_hz: int = 60
    supercycle_count: int = 2

    # Softer tail with a muscular root and more compliant middle/tip.
    tail_root_yaw_gain: float = 0.62
    tail_com_gain: float = 0.72
    tail_velocity_gain: float = 0.11
    tail_pitch_gain: float = 0.24
    tail_neutral_sag_deg: float = 4.7
    tail_stiffness_root: float = 20.0
    tail_stiffness_tip: float = 4.6
    tail_damping_ratio: float = 0.75
    tail_coupling: float = 8.0
    tail_parent_follow: float = 0.28
    tail_phase_lag_seconds_per_bone: float = 0.028
    tail_dynamic_limit_root_deg: float = 2.4
    tail_dynamic_limit_tip_deg: float = 5.8
    tail_warmup_supercycles: int = 28

    # Turn mechanics.  The root path uses C2 curvature.  Head/neck/chest look
    # into the future path and visibly lead the pelvis; the tail creates the
    # opposite inertial shape.  Values are relative to the already rotating
    # root, not absolute world heading.
    turn_default_degrees: float = 35.0
    turn_cycle_hz_scale: float = 0.86
    turn_stride_scale: float = 0.84
    turn_inside_stride_scale: float = 0.80
    turn_outside_stride_scale: float = 1.10
    turn_inside_contact_lag_cycles: float = 0.025
    turn_head_lead_deg: float = 11.5
    turn_neck_lead_deg: float = 7.6
    turn_chest_lead_deg: float = 3.2
    turn_pelvis_lead_deg: float = 1.25
    turn_head_lookahead_fraction: float = 0.155
    turn_lead_rise_fraction: float = 0.18
    turn_lead_fall_start_fraction: float = 0.76
    turn_body_lean_deg: float = 1.8
    turn_support_shift_hip_fraction: float = 0.0045
    turn_tail_counter_root_deg: float = 3.2
    turn_tail_counter_tip_deg: float = 7.8
    turn_tail_release_lag_fraction: float = 0.10
    turn_head_roll_deg: float = 1.0
    turn_step_yaw_deg: float = 3.0
    swing_turn_lift_scale: float = 1.08

    # Start/brake and alert locomotion.
    start_duration_seconds: float = 3.65
    stop_duration_seconds: float = 3.35
    start_cycles: float = 1.65
    stop_cycles: float = 1.50
    minimum_active_speed_fraction: float = 0.10
    acceleration_lean_deg: float = 2.6
    braking_lean_deg: float = -2.7
    alert_cycle_hz: float = 0.70
    alert_stride_scale: float = 0.88
    alert_head_raise_deg: float = 4.2
    alert_neck_raise_deg: float = 3.8
    alert_scan_yaw_deg: float = 7.0
    alert_scan_period_seconds: float = 5.2
    alert_tail_raise_deg: float = 2.0
    alert_step_height_scale: float = 1.08

    # Idle and behavior actions.
    idle_duration_seconds: float = 7.0
    idle_weight_shift_hip_fraction: float = 0.0040
    idle_head_scan_yaw_deg: float = 3.0
    idle_head_scan_pitch_deg: float = 0.9
    idle_tail_tip_deg: float = 2.4
    idle_breath_cycles: float = 2.0

    eating_duration_seconds: float = 8.4
    eating_body_lower_deg: float = 7.2
    eating_neck_lower_deg: float = 27.0
    eating_head_lower_deg: float = 13.5
    eating_pelvis_back_hip_fraction: float = 0.060
    eating_pelvis_down_hip_fraction: float = 0.066
    eating_knee_flex_deg: float = 6.5
    eating_jaw_open_deg: float = 25.0
    eating_bite_count: int = 4
    eating_chew_deg: float = 3.7

    bite_duration_seconds: float = 3.75
    bite_anticipation_fraction: float = 0.30
    bite_contact_fraction: float = 0.58
    bite_recovery_fraction: float = 0.82
    bite_lunge_hip_fraction: float = 0.20
    bite_preload_back_hip_fraction: float = 0.105
    bite_preload_down_hip_fraction: float = 0.072
    bite_catch_step_hip_fraction: float = 0.115
    bite_body_crouch_deg: float = 4.6
    bite_neck_retract_deg: float = 12.0
    bite_neck_thrust_deg: float = 15.0
    bite_jaw_open_deg: float = 49.0
    bite_snap_close_deg: float = 1.2
    bite_head_yaw_deg: float = 3.0

    roar_duration_seconds: float = 5.6
    roar_inhale_fraction: float = 0.24
    roar_peak_fraction: float = 0.54
    roar_release_fraction: float = 0.82
    roar_neck_raise_deg: float = 15.0
    roar_head_raise_deg: float = 10.0
    roar_jaw_open_deg: float = 50.0
    roar_chest_expand_deg: float = 4.4
    roar_head_shake_deg: float = 2.3
    roar_tail_brace_deg: float = 2.7

    # Quality gates.
    max_joint_velocity_deg_s: float = 390.0
    max_joint_acceleration_deg_s2: float = 9000.0
    max_relaxed_pelvis_lateral_hip_fraction: float = 0.018
    max_relaxed_pelvis_vertical_hip_fraction: float = 0.020
    max_relaxed_mesh_hover_hip_fraction: float = 0.006
    max_turn_head_lead_error_deg: float = 1.0
    minimum_turn_head_lead_deg: float = 5.0
    minimum_turn_neck_lead_deg: float = 3.0
    minimum_turn_tail_counter_deg: float = 2.0

    @classmethod
    def from_json(cls, path: str | Path) -> "BipedV7Profile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**payload)

    def to_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return destination
