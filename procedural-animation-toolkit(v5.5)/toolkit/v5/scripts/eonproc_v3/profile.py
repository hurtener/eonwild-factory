"""Typed configuration for anatomically constrained biped locomotion v3."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass(frozen=True)
class BipedV3Profile:
    # Scale and timing. The relaxed Tarbosaurus reference is close to a two-second
    # full gait cycle after the opening mouth/pose transition.
    name: str = "large_theropod_relaxed_walk_v3"
    reference_hip_height_m: float = 2.75
    cycle_hz: float = 0.50
    stride_length_m: float = 2.05
    stance_fraction: float = 0.72
    contact_lead_stride: float = 0.36

    # Foot planning and support transfer.
    swing_lift_hip_fraction: float = 0.084
    swing_outward_hip_fraction: float = 0.006
    load_ramp_fraction: float = 0.15
    toe_off_window_fraction: float = 0.20
    precontact_window_fraction: float = 0.28
    pelvis_support_shift_gain: float = 0.15
    pelvis_vertical_bob_hip_fraction: float = 0.014
    pelvis_loading_drop_hip_fraction: float = 0.011
    pelvis_forward_sway_hip_fraction: float = 0.008
    pelvis_roll_deg: float = 3.7
    pelvis_yaw_deg: float = 3.2
    pelvis_pitch_deg: float = 1.2

    # Relaxed posture. Positive anatomical pitch bends the forward chain down;
    # negative values raise the chest/neck toward the horizon.
    body_lean_deg: float = -2.4
    pelvis_neutral_pitch_deg: float = -0.25
    neck_relaxed_pitch_deg: float = -1.0
    head_horizon_pitch_deg: float = -0.25

    # Preferred sagittal gait, followed by the constrained IK solver.
    hip_swing_deg: float = 20.0
    hip_extension_limit_deg: float = 34.0
    hip_flexion_limit_deg: float = 38.0
    hip_abduction_limit_deg: float = 9.0
    knee_min_flex_deg: float = 18.0
    knee_max_flex_deg: float = 112.0
    knee_stance_flex_deg: float = 50.0
    knee_loading_flex_deg: float = 7.0
    knee_swing_flex_deg: float = 91.0
    ankle_min_flex_deg: float = 16.0
    ankle_max_flex_deg: float = 104.0
    ankle_stance_flex_deg: float = 51.0
    ankle_swing_flex_deg: float = 76.0
    leg_position_scale_hip_fraction: float = 0.0025
    leg_preference_weight: float = 0.16
    leg_continuity_weight: float = 0.12
    leg_max_solver_evaluations: int = 48

    # Foot and toe articulation.
    swing_ankle_deg: float = 11.0
    toe_off_foot_deg: float = 9.0
    contact_foot_deg: float = 2.2
    toe_push_deg: float = 10.5

    # Whole-body response.
    spine_counter_gain: float = 0.58
    neck_stabilize_gain: float = 0.51
    head_stabilize_gain: float = 0.68
    arm_inertia_deg: float = 3.1
    breathing_chest_deg: float = 1.35
    breathing_neck_deg: float = 0.52
    neutral_jaw_close_deg: float = 33.0
    jaw_breath_deg: float = 0.62
    head_micro_yaw_deg: float = 0.55
    asymmetry_fraction: float = 0.018

    # Dense solve/export. V3 retains V2's 120 Hz solve and 60 Hz GLB output.
    internal_sample_hz: int = 120
    export_sample_hz: int = 60
    supercycle_count: int = 2
    ik_tolerance_hip_fraction: float = 0.00035

    # Softer, more visibly articulated tail. Distal joints have lower stiffness,
    # greater allowed deflection, and explicit per-joint phase delay.
    tail_root_yaw_gain: float = 0.76
    tail_com_gain: float = 1.20
    tail_velocity_gain: float = 0.16
    tail_pitch_gain: float = 0.30
    tail_neutral_sag_deg: float = 5.4
    tail_stiffness_root: float = 24.0
    tail_stiffness_tip: float = 6.5
    tail_damping_ratio: float = 0.69
    tail_coupling: float = 10.0
    tail_parent_follow: float = 0.34
    tail_phase_lag_seconds_per_bone: float = 0.022
    tail_dynamic_limit_root_deg: float = 2.8
    tail_dynamic_limit_tip_deg: float = 4.8
    tail_warmup_supercycles: int = 28

    # Quality gates.
    max_joint_velocity_deg_s: float = 330.0
    max_joint_acceleration_deg_s2: float = 5200.0
    anatomical_margin_deg: float = 1.0

    @classmethod
    def from_json(cls, path: str | Path) -> "BipedV3Profile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**payload)

    def to_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return destination
