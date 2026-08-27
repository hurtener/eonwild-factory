"""Typed configuration for contact-aware biped locomotion."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass(frozen=True)
class BipedV2Profile:
    name: str = "large_theropod_v2"
    reference_hip_height_m: float = 2.75
    cycle_hz: float = 0.58
    stride_length_m: float = 2.35
    stance_fraction: float = 0.68
    contact_lead_stride: float = 0.27
    swing_lift_hip_fraction: float = 0.095
    swing_outward_hip_fraction: float = 0.008
    load_ramp_fraction: float = 0.12
    pelvis_support_shift_gain: float = 0.19
    pelvis_vertical_bob_hip_fraction: float = 0.018
    pelvis_loading_drop_hip_fraction: float = 0.014
    pelvis_forward_sway_hip_fraction: float = 0.012
    pelvis_roll_deg: float = 4.8
    pelvis_yaw_deg: float = 4.0
    pelvis_pitch_deg: float = 2.0
    body_lean_deg: float = 4.5
    hip_swing_deg: float = 24.0
    stance_knee_deg: float = 18.0
    swing_knee_deg: float = 53.0
    swing_ankle_deg: float = 14.0
    toe_off_foot_deg: float = 10.5
    contact_foot_deg: float = 3.0
    toe_push_deg: float = 12.0
    spine_counter_gain: float = 0.63
    neck_stabilize_gain: float = 0.48
    head_stabilize_gain: float = 0.62
    arm_inertia_deg: float = 3.8
    breathing_chest_deg: float = 1.5
    breathing_neck_deg: float = 0.65
    neutral_jaw_close_deg: float = 33.0
    jaw_breath_deg: float = 0.85
    head_micro_yaw_deg: float = 0.8
    asymmetry_fraction: float = 0.028
    internal_sample_hz: int = 120
    export_sample_hz: int = 60
    supercycle_count: int = 2
    ik_iterations: int = 14
    ik_tolerance_hip_fraction: float = 0.00025
    tail_root_yaw_gain: float = 0.82
    tail_com_gain: float = 1.35
    tail_velocity_gain: float = 0.18
    tail_pitch_gain: float = 0.36
    tail_stiffness_root: float = 31.0
    tail_stiffness_tip: float = 13.0
    tail_damping_ratio: float = 0.82
    tail_coupling: float = 18.0
    tail_warmup_supercycles: int = 18

    @classmethod
    def from_json(cls, path: str | Path) -> "BipedV2Profile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**payload)

    def to_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return destination
