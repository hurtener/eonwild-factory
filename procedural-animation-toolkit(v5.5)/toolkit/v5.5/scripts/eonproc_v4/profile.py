"""Typed quality configuration for Eonwild procedural animation v4."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

from eonproc_v3.profile import BipedV3Profile


@dataclass(frozen=True)
class BipedV4Profile(BipedV3Profile):
    # V4 retains the reference-fitted relaxed Tarbosaurus baseline.
    name: str = "tarbosaurus_reference_fitted_v4"
    cycle_hz: float = 0.45
    stride_length_m: float = 2.05
    stance_fraction: float = 0.70
    body_lean_deg: float = -1.0
    pelvis_neutral_pitch_deg: float = -1.1
    neck_relaxed_pitch_deg: float = -0.6
    head_horizon_pitch_deg: float = 0.35

    # Deterministic 60 Hz constraint solve and browser-ready 60 Hz export.
    # An optional ultra profile raises offline solve density to 120 Hz.
    internal_sample_hz: int = 60
    export_sample_hz: int = 60
    supercycle_count: int = 2

    # Vertex-level sole model.
    sole_weight_threshold: float = 0.28
    sole_height_band_hip_fraction: float = 0.115
    sole_forward_padding_hip_fraction: float = 0.12
    sole_contact_quantile: float = 0.08
    sole_clearance_m: float = 0.0025
    sole_max_vertical_correction_hip_fraction: float = 0.060
    sole_penetration_gate_hip_fraction: float = 0.0020
    sole_loaded_gap_gate_hip_fraction: float = 0.0090
    sole_min_vertices_per_side: int = 48
    sole_max_vertices_per_side: int = 64

    # Terrain adaptation.
    terrain_normal_blend: float = 0.88
    terrain_foot_roll_limit_deg: float = 10.0
    terrain_foot_pitch_limit_deg: float = 14.0
    terrain_pelvis_height_blend: float = 0.72
    terrain_pelvis_roll_gain: float = 0.58
    terrain_pelvis_pitch_gain: float = 0.46
    terrain_probe_radius_hip_fraction: float = 0.045

    # Segmented swing-foot trajectory. The foot unloads and folds upward before
    # most of its forward travel, then extends smoothly into pre-contact.
    swing_advance_start_fraction: float = 0.055
    swing_advance_end_fraction: float = 0.93
    swing_lift_rise_fraction: float = 0.33
    swing_lift_fall_start_fraction: float = 0.60
    swing_turn_lift_scale: float = 1.12
    uneven_terrain_amplitude_hip_fraction: float = 0.024
    uneven_terrain_wavelength_m: float = 1.65

    # Path and locomotion dynamics.
    turn_default_degrees: float = 35.0
    turn_duration_seconds: float = 5.42
    turn_inside_stride_scale: float = 0.79
    turn_outside_stride_scale: float = 1.11
    turn_body_lean_deg: float = 3.2
    start_duration_seconds: float = 4.0
    stop_duration_seconds: float = 3.6
    start_cycles: float = 1.55
    stop_cycles: float = 1.45
    minimum_active_speed_fraction: float = 0.12
    acceleration_lean_deg: float = 4.2
    braking_lean_deg: float = -3.8

    # Alert locomotion and attention.
    alert_cycle_hz: float = 0.52
    alert_stride_scale: float = 0.86
    alert_head_raise_deg: float = 5.0
    alert_neck_raise_deg: float = 4.5
    alert_scan_yaw_deg: float = 8.0
    alert_scan_period_seconds: float = 5.6
    alert_tail_raise_deg: float = 2.4
    alert_step_height_scale: float = 1.10

    # Idle and secondary motion.
    idle_duration_seconds: float = 6.0
    idle_weight_shift_hip_fraction: float = 0.018
    idle_head_scan_yaw_deg: float = 3.2
    idle_head_scan_pitch_deg: float = 1.2
    idle_tail_tip_deg: float = 2.7
    idle_breath_cycles: float = 2.0

    # Eating.
    eating_duration_seconds: float = 8.0
    eating_body_lower_deg: float = 6.5
    eating_neck_lower_deg: float = 24.0
    eating_head_lower_deg: float = 14.0
    eating_pelvis_back_hip_fraction: float = 0.055
    eating_knee_flex_deg: float = 9.0
    eating_jaw_open_deg: float = 20.0
    eating_bite_count: int = 4
    eating_chew_deg: float = 4.5

    # Bite attack.
    bite_duration_seconds: float = 3.4
    bite_anticipation_fraction: float = 0.28
    bite_contact_fraction: float = 0.56
    bite_recovery_fraction: float = 0.80
    bite_lunge_hip_fraction: float = 0.20
    bite_body_crouch_deg: float = 3.5
    bite_rear_load_hip_fraction: float = 0.075
    bite_neck_retract_deg: float = 10.0
    bite_neck_thrust_deg: float = 16.0
    bite_jaw_open_deg: float = 42.0
    bite_snap_close_deg: float = 6.0
    bite_head_yaw_deg: float = 3.5

    # Roar.
    roar_duration_seconds: float = 5.4
    roar_inhale_fraction: float = 0.24
    roar_peak_fraction: float = 0.54
    roar_release_fraction: float = 0.82
    roar_neck_raise_deg: float = 16.0
    roar_head_raise_deg: float = 11.0
    roar_jaw_open_deg: float = 46.0
    roar_chest_expand_deg: float = 4.8
    roar_head_shake_deg: float = 2.6
    roar_tail_brace_deg: float = 3.0

    # Transitions.
    transition_short_seconds: float = 0.75
    transition_medium_seconds: float = 1.25
    transition_long_seconds: float = 1.8
    transition_match_velocity: bool = True

    # V4 quality gates.
    # V4 solver continuity is stronger than V3 because root curvature and
    # terrain-normal changes otherwise expose small IK branch jumps.
    leg_preference_weight: float = 0.17
    leg_continuity_weight: float = 0.28

    max_joint_velocity_deg_s: float = 360.0
    max_joint_acceleration_deg_s2: float = 8000.0
    leg_max_solver_evaluations: int = 8
    max_transition_endpoint_position_error: float = 1e-6
    max_transition_endpoint_rotation_error: float = 1e-6
    max_turn_loaded_slide_hip_fraction: float = 0.008

    @classmethod
    def from_json(cls, path: str | Path) -> "BipedV4Profile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**payload)

    def to_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return destination
