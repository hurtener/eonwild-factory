"""V8 locomotion: V7 contact lock with stronger gaze-led large-animal turns."""
from __future__ import annotations
from dataclasses import replace
import math
import numpy as np
from eonproc_v3.curves import minimum_jerk
from eonproc_v3.rig import distribute_chain_rotation
from eonproc_v4.path import EasedArcPath
from eonproc_v4.locomotion import LocomotionSchedule, LocomotionResult
from eonproc_v7.locomotion import TarbosaurusV7LocomotionGenerator, V7BodyPlan, _turn_envelope
from .profile import BipedV8Profile

def _bump(x: float, a: float, b: float, c: float, d: float) -> float:
    if x <= a or x >= d: return 0.0
    if x < b: return minimum_jerk((x-a)/max(b-a,1e-8))
    if x <= c: return 1.0
    return 1.0-minimum_jerk((x-c)/max(d-c,1e-8))

class TarbosaurusV8LocomotionGenerator(TarbosaurusV7LocomotionGenerator):
    profile: BipedV8Profile
    def __init__(self, asset, semantics, profile: BipedV8Profile):
        super().__init__(asset, semantics, profile)
        self.profile = profile

    def body_plan_scheduled(self, schedule: LocomotionSchedule, sample_index: int) -> V7BodyPlan:
        body = super().body_plan_scheduled(schedule, sample_index)
        if not isinstance(schedule.path, EasedArcPath) or not body.turn_active:
            return body
        early = _bump(body.turn_u, 0.055, 0.16, 0.31, 0.53)
        return replace(
            body,
            turn_head_lead=body.turn_head_lead*(1.0+self.profile.turn_head_overshoot_fraction*early),
            turn_neck_lead=body.turn_neck_lead*(1.0+self.profile.turn_neck_overshoot_fraction*early),
        )

    def _pose_for_body(self, time_seconds, global_phase, body, tail_yaw, tail_pitch, leg_seeds, terrain):
        pose, solved, seeds = super()._pose_for_body(time_seconds, global_phase, body, tail_yaw, tail_pitch, leg_seeds, terrain)
        if not getattr(body, "turn_active", False):
            return pose, solved, seeds
        focus = _turn_envelope(body.turn_u, 0.10, 0.76)
        settle = _bump(body.turn_u, 0.62, 0.76, 0.84, 0.97)
        head_pitch = math.radians(self.profile.turn_head_pitch_deg)*focus*(1.0-0.42*settle)
        neck_roll = -body.turn_world_sign*math.radians(self.profile.turn_neck_roll_deg)*focus
        distribute_chain_rotation(pose, self.neck, self.basis.forward, neck_roll, [0.07,0.11,0.17,0.26,0.39])
        pose.rotate_world_rest_axis(self.head, self.basis.lateral, head_pitch)
        return pose, solved, seeds

    def generate_schedule(self, schedule: LocomotionSchedule, keep_world_matrices: bool=True) -> LocomotionResult:
        result = super().generate_schedule(schedule, keep_world_matrices=keep_world_matrices)
        active = bool(result.diagnostics.get("turn_mass_lead",{}).get("active",False))
        result.clip.extras.update({"generator":"Eonwild procedural animation toolkit v8","version":"8.0.0","designLabTurnExpression":active})
        if result.in_place_clip is not None:
            result.in_place_clip.extras.update({"generator":"Eonwild procedural animation toolkit v8","version":"8.0.0","designLabTurnExpression":active})
        if active:
            plans=[self.body_plan_scheduled(schedule,i) for i in range(len(schedule.times))]
            head=np.degrees(np.abs([p.turn_head_lead for p in plans])); neck=np.degrees(np.abs([p.turn_neck_lead for p in plans])); chest=np.degrees(np.abs([p.turn_chest_lead for p in plans]))
            result.diagnostics["turn_expression_v8"]={
                "authored_peak_head_relative_deg":float(np.max(head)),
                "authored_peak_neck_relative_deg":float(np.max(neck)),
                "authored_peak_chest_relative_deg":float(np.max(chest)),
                "head_overshoot_enabled":True,"head_pitch_and_neck_roll_enabled":True,
            }
            gates=result.diagnostics.setdefault("quality_gates",{})
            gates.update({"v8_turn_head_lead_target":float(np.max(head))>=self.profile.minimum_turn_head_lead_deg,"v8_turn_neck_lead_target":float(np.max(neck))>=self.profile.minimum_turn_neck_lead_deg})
            result.clip.diagnostics=result.diagnostics
            if result.in_place_clip is not None: result.in_place_clip.diagnostics={**result.diagnostics,"in_place":True}
        return result
