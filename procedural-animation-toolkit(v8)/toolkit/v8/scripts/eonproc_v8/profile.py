"""Tarbosaurus V8 quality profile: reference-staged actions and expressive turns."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from eonproc_v7.profile import BipedV7Profile

@dataclass(frozen=True)
class BipedV8Profile(BipedV7Profile):
    name: str = "tarbosaurus_design_lab_v8_actions_and_turn_expression"

    # Stronger cranio-cervical lead in large-radius turns.
    turn_head_lead_deg: float = 18.5
    turn_neck_lead_deg: float = 12.2
    turn_chest_lead_deg: float = 4.8
    turn_pelvis_lead_deg: float = 1.35
    turn_head_lookahead_fraction: float = 0.205
    turn_lead_rise_fraction: float = 0.13
    turn_lead_fall_start_fraction: float = 0.72
    turn_head_roll_deg: float = 2.0
    turn_body_lean_deg: float = 2.1
    turn_tail_counter_root_deg: float = 3.8
    turn_tail_counter_tip_deg: float = 9.6
    turn_tail_release_lag_fraction: float = 0.13
    turn_head_overshoot_fraction: float = 0.22
    turn_neck_overshoot_fraction: float = 0.11
    turn_head_pitch_deg: float = 1.25
    turn_neck_roll_deg: float = 0.85
    minimum_turn_head_lead_deg: float = 12.0
    minimum_turn_neck_lead_deg: float = 7.0
    minimum_turn_tail_counter_deg: float = 4.0

    # Reference-staged two-step power attack.
    bite_duration_seconds: float = 4.60
    bite_focus_fraction: float = 0.09
    bite_anticipation_fraction: float = 0.28
    bite_first_catch_fraction: float = 0.49
    bite_contact_fraction: float = 0.67
    bite_hold_end_fraction: float = 0.80
    bite_recovery_fraction: float = 0.84
    bite_lunge_hip_fraction: float = 0.305
    bite_preload_back_hip_fraction: float = 0.115
    bite_preload_down_hip_fraction: float = 0.078
    bite_first_catch_step_hip_fraction: float = 0.205
    bite_second_catch_step_hip_fraction: float = 0.150
    bite_first_step_height_hip_fraction: float = 0.038
    bite_second_step_height_hip_fraction: float = 0.030
    bite_body_crouch_deg: float = 6.2
    bite_neck_retract_deg: float = 15.0
    bite_neck_thrust_deg: float = 18.5
    bite_jaw_open_deg: float = 50.0
    bite_snap_close_deg: float = 0.8
    bite_target_head_yaw_deg: float = 4.6
    bite_contact_head_yaw_deg: float = 5.8
    bite_contact_head_roll_deg: float = 2.7
    bite_tear_head_yaw_deg: float = 7.5
    bite_tear_neck_yaw_deg: float = 4.2
    bite_tear_chest_yaw_deg: float = 1.8
    bite_tail_preload_deg: float = 4.8
    bite_tail_delivery_deg: float = 6.0
    bite_tail_tear_deg: float = 5.2

    # Irregular bite/hold/pull/chew feeding loop.
    eating_duration_seconds: float = 10.80
    eating_body_lower_deg: float = 7.8
    eating_neck_lower_deg: float = 29.0
    eating_head_lower_deg: float = 14.5
    eating_pelvis_back_hip_fraction: float = 0.062
    eating_pelvis_down_hip_fraction: float = 0.069
    eating_knee_flex_deg: float = 7.0
    eating_jaw_open_deg: float = 29.0
    eating_chew_deg: float = 3.2
    eating_target_search_yaw_deg: float = 2.4
    eating_bite_retract_deg: float = 4.8
    eating_bite_thrust_deg: float = 5.4
    eating_pull_head_yaw_deg: float = 5.8
    eating_pull_neck_yaw_deg: float = 3.4
    eating_pull_head_roll_deg: float = 2.4
    eating_pull_head_raise_deg: float = 4.0
    eating_pull_pelvis_shift_hip_fraction: float = 0.0065
    eating_tail_counter_deg: float = 3.6
    eating_swallow_head_raise_deg: float = 2.2
    eating_bite_count: int = 3
    eating_bite_times: tuple[float, float, float] = (0.165, 0.485, 0.785)
    eating_bite_directions: tuple[float, float, float] = (-1.0, 1.0, -1.0)
    eating_bite_strengths: tuple[float, float, float] = (1.0, 0.78, 1.08)

    minimum_attack_preload_back_hip_fraction: float = 0.085
    minimum_attack_preload_down_hip_fraction: float = 0.055
    minimum_attack_root_delivery_hip_fraction: float = 0.22
    minimum_attack_head_tear_deg: float = 4.0
    minimum_eating_head_yaw_span_deg: float = 6.0
    minimum_eating_jaw_events: int = 3
    minimum_eating_pelvis_down_hip_fraction: float = 0.055

    @classmethod
    def from_json(cls, path: str | Path) -> "BipedV8Profile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        for key in ("eating_bite_times", "eating_bite_directions", "eating_bite_strengths"):
            if key in payload:
                payload[key] = tuple(payload[key])
        return cls(**payload)

    def to_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return destination
