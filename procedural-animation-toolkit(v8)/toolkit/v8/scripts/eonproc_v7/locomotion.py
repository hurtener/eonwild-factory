"""V7 contact-locked locomotion with mass-led large-theropod turning.

The V6 regression came from exporting pelvis translation that was not part of the
leg/contact solve.  V7 inherits V4's solve order (root -> pelvis -> complete
leg IK -> vertex sole check) and constrains relaxed pelvis travel to reference-
fitted amplitudes.  Turns add a separate anticipation layer: head and neck lead,
chest follows, pelvis commits later, and the tail shapes against the turn.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any

import numpy as np

from eonproc_v3.curves import minimum_jerk
from eonproc_v3.rig import Pose, distribute_chain_rotation
from eonproc_v4.locomotion import (
    TerrainAwareLocomotionGenerator,
    V4BodyPlan,
    V4FootPlan,
    LocomotionSchedule,
    LocomotionResult,
)
from eonproc_v4.path import EasedArcPath

from .profile import BipedV7Profile


@dataclass(frozen=True)
class V7BodyPlan(V4BodyPlan):
    turn_active: bool = False
    turn_u: float = 0.0
    turn_world_sign: float = 0.0
    turn_envelope: float = 0.0
    turn_head_lead: float = 0.0
    turn_neck_lead: float = 0.0
    turn_chest_lead: float = 0.0
    turn_tail_counter: float = 0.0
    turn_roll: float = 0.0


def _turn_envelope(u: float, rise: float, fall_start: float) -> float:
    """C2 onset and release for anticipatory body shaping."""
    x = float(np.clip(u, 0.0, 1.0))
    if x < rise:
        incoming = minimum_jerk(x / max(rise, 1e-6))
    else:
        incoming = 1.0
    if x > fall_start:
        outgoing = 1.0 - minimum_jerk((x - fall_start) / max(1.0 - fall_start, 1e-6))
    else:
        outgoing = 1.0
    return float(incoming * outgoing)


class TarbosaurusV7LocomotionGenerator(TerrainAwareLocomotionGenerator):
    """Terrain/contact solver specialized for the V7 heavy-theropod profile."""

    profile: BipedV7Profile

    def __init__(self, asset, semantics, profile: BipedV7Profile):
        super().__init__(asset, semantics, profile)
        self.profile = profile

    @staticmethod
    def _turn_sign(schedule: LocomotionSchedule) -> float:
        if isinstance(schedule.path, EasedArcPath):
            # This is the actual signed world-Y rotation.  In this asset:
            # negative is anatomical left, positive is anatomical right.
            return float(np.sign(schedule.path.world_angle))
        return 0.0

    def _contact_world(self, schedule: LocomotionSchedule, side: str, distance: float):
        point, normal, terrain_height, heading = super()._contact_world(schedule, side, distance)
        if not isinstance(schedule.path, EasedArcPath):
            return point, normal, terrain_height, heading

        world_sign = self._turn_sign(schedule)
        left_turn = world_sign < 0.0
        inside = (left_turn and side == "l") or ((not left_turn) and side == "r")
        stride_scale = self.profile.turn_inside_stride_scale if inside else self.profile.turn_outside_stride_scale

        # Keep each planted point immutable.  The asymmetric correction is made
        # in the contact frame at contact creation, never from the moving root.
        frame = schedule.path.frame(distance)
        longitudinal_shift = (stride_scale - 1.0) * self.stride * 0.54
        point = point + frame.basis.forward * longitudinal_shift

        # Big theropods visibly orient the feet into an arc, but only modestly.
        step_yaw = math.radians(self.profile.turn_step_yaw_deg)
        heading += world_sign * step_yaw * (0.86 if inside else 1.0)
        return point, normal, terrain_height, heading

    def foot_plan_scheduled(self, schedule: LocomotionSchedule, sample_index: int, side: str) -> V4FootPlan:
        foot = super().foot_plan_scheduled(schedule, sample_index, side)
        if not isinstance(schedule.path, EasedArcPath):
            return foot

        world_sign = self._turn_sign(schedule)
        left_turn = world_sign < 0.0
        inside = (left_turn and side == "l") or ((not left_turn) and side == "r")
        # Inside foot clears a fraction earlier during recovery; outside foot
        # gets slightly more lift to travel the longer arc without toe scuff.
        lift_bias = 0.96 if inside else 1.07
        if not foot.stance:
            current = foot.target_world.copy()
            base_ground = max(foot.terrain_height, self.mesh_ground)
            lift = max(0.0, current[1] - (base_ground + self.foot_offsets[side]["bone_height"]))
            current[1] += lift * (lift_bias - 1.0)
            foot = replace(foot, target_world=current)
        return foot

    def body_plan_scheduled(self, schedule: LocomotionSchedule, sample_index: int) -> V7BodyPlan:
        base = super().body_plan_scheduled(schedule, sample_index)
        if not isinstance(schedule.path, EasedArcPath):
            return V7BodyPlan(**base.__dict__)

        distance = float(schedule.distances[sample_index])
        total = max(schedule.path.total_distance, 1e-8)
        u = float(np.clip(distance / total, 0.0, 1.0))
        envelope = _turn_envelope(u, self.profile.turn_lead_rise_fraction, self.profile.turn_lead_fall_start_fraction)
        world_sign = self._turn_sign(schedule)

        # Small pelvis commitment and small inside support shift.  Both happen
        # before the legs are solved, so the sole targets remain authoritative.
        pelvis_lead = world_sign * math.radians(self.profile.turn_pelvis_lead_deg) * envelope
        anatomical_sign = -world_sign
        turn_roll = anatomical_sign * math.radians(self.profile.turn_body_lean_deg) * envelope
        lateral_shift = (
            base.path_frame.basis.lateral
            * world_sign
            * self.hip_height
            * self.profile.turn_support_shift_hip_fraction
            * envelope
        )

        return V7BodyPlan(
            **{
                **base.__dict__,
                "pelvis_translation_world": base.pelvis_translation_world + lateral_shift,
                "pelvis_yaw": base.pelvis_yaw + pelvis_lead,
                "pelvis_roll": base.pelvis_roll + turn_roll * 0.34,
            },
            turn_active=True,
            turn_u=u,
            turn_world_sign=world_sign,
            turn_envelope=envelope,
            turn_head_lead=world_sign * math.radians(self.profile.turn_head_lead_deg) * envelope,
            turn_neck_lead=world_sign * math.radians(self.profile.turn_neck_lead_deg) * envelope,
            turn_chest_lead=world_sign * math.radians(self.profile.turn_chest_lead_deg) * envelope,
            turn_tail_counter=-world_sign * math.radians(self.profile.turn_tail_counter_tip_deg) * envelope,
            turn_roll=turn_roll,
        )

    def _pose_for_body(
        self,
        time_seconds: float,
        global_phase: float,
        body: V7BodyPlan,
        tail_yaw: np.ndarray,
        tail_pitch: np.ndarray,
        leg_seeds: dict[str, np.ndarray | None],
        terrain,
    ):
        pose, solved, seeds = super()._pose_for_body(
            time_seconds, global_phase, body, tail_yaw, tail_pitch, leg_seeds, terrain
        )
        if not getattr(body, "turn_active", False):
            return pose, solved, seeds

        # The complete leg/contact solve is already complete.  The remaining
        # branches are siblings of the legs beneath the pelvis and therefore do
        # not invalidate the planted feet.
        distribute_chain_rotation(
            pose,
            self.spine,
            self.basis.up,
            body.turn_chest_lead,
            [0.05, 0.08, 0.12, 0.17, 0.24, 0.34],
        )
        distribute_chain_rotation(
            pose,
            self.neck,
            self.basis.up,
            body.turn_neck_lead,
            [0.08, 0.12, 0.18, 0.25, 0.37],
        )
        pose.rotate_world_rest_axis(self.head, self.basis.up, body.turn_head_lead)
        pose.rotate_world_rest_axis(
            self.head,
            self.basis.forward,
            -body.turn_world_sign * math.radians(self.profile.turn_head_roll_deg) * body.turn_envelope,
        )

        # Explicit opposite tail shape.  Proximal segments remain muscular;
        # distal segments take more amplitude and release slightly later.
        count = len(self.tail)
        release_shift = self.profile.turn_tail_release_lag_fraction
        delayed_u = float(np.clip((body.turn_u - release_shift) / max(1.0 - release_shift, 1e-6), 0.0, 1.0))
        delayed_env = _turn_envelope(
            delayed_u,
            self.profile.turn_lead_rise_fraction,
            min(0.88, self.profile.turn_lead_fall_start_fraction + release_shift),
        )
        for index, bone in enumerate(self.tail):
            fraction = index / max(count - 1, 1)
            amplitude = math.radians(
                self.profile.turn_tail_counter_root_deg
                + (self.profile.turn_tail_counter_tip_deg - self.profile.turn_tail_counter_root_deg)
                * (fraction ** 1.18)
            )
            pose.rotate_world_rest_axis(
                bone,
                self.basis.up,
                -body.turn_world_sign * amplitude * delayed_env / max(count * 0.56, 1.0),
            )
            # A tiny vertical settling component keeps the turn from reading as
            # a flat rotation of the entire silhouette.
            pose.rotate_world_rest_axis(
                bone,
                self.basis.lateral,
                body.turn_roll * (0.11 + 0.10 * fraction) / max(count * 0.72, 1.0),
            )
        return pose, solved, seeds

    def generate_schedule(self, schedule: LocomotionSchedule, keep_world_matrices: bool = True) -> LocomotionResult:
        # Force the base solver to retain the sampled world matrices.  V4's
        # historical writer only emitted root translation even though the pose
        # used a local pelvis translation before solving the legs.  V7 derives
        # the exact local pelvis channel from those already-contact-solved world
        # matrices, so the exported skeleton is the same skeleton that passed
        # the sole/contact checks.  No post-solve balance transform is allowed.
        result = super().generate_schedule(schedule, keep_world_matrices=True)
        clip = result.clip
        if clip.world_matrices is None:
            raise RuntimeError("V7 requires contact-solved world matrices to export pelvis translation")
        pelvis_index = self.asset.name_to_node[self.pelvis]
        pelvis_parent = self.asset.parents[pelvis_index]
        pelvis_samples: list[np.ndarray] = []
        for matrices in clip.world_matrices:
            pelvis_world = matrices[pelvis_index]
            local = pelvis_world if pelvis_parent is None else np.linalg.inv(matrices[pelvis_parent]) @ pelvis_world
            pelvis_samples.append(local[:3, 3].copy())
        pelvis_track = np.asarray(pelvis_samples, dtype=np.float64)
        clip.translations[self.pelvis] = pelvis_track
        if result.in_place_clip is not None:
            # Root stripping does not alter the pelvis local transform.
            result.in_place_clip.translations[self.pelvis] = pelvis_track.copy()
        pelvis = pelvis_track
        if pelvis is not None:
            rest = self.asset.rest_translation[self.asset.name_to_node[self.pelvis]]
            delta = pelvis - rest[None, :]
            ranges = np.ptp(delta, axis=0)
            lateral_range = float(np.max(np.abs(delta @ self.base_basis.lateral)))
            vertical_range = float(np.ptp(delta @ self.base_basis.up))
            forward_range = float(np.ptp(delta @ self.base_basis.forward))
        else:
            ranges = np.zeros(3)
            lateral_range = vertical_range = forward_range = 0.0

        body_plans = [self.body_plan_scheduled(schedule, i) for i in range(len(schedule.times))]
        active_turn = any(getattr(plan, "turn_active", False) for plan in body_plans)
        turn_metrics: dict[str, Any] = {"active": active_turn}
        if active_turn:
            head = np.degrees([abs(plan.turn_head_lead) for plan in body_plans])
            neck = np.degrees([abs(plan.turn_neck_lead) for plan in body_plans])
            chest = np.degrees([abs(plan.turn_chest_lead) for plan in body_plans])
            tail = np.degrees([abs(plan.turn_tail_counter) for plan in body_plans])
            peak_index = int(np.argmax(head))
            root_heading = np.degrees(abs(body_plans[peak_index].path_frame.heading_radians))
            turn_metrics.update({
                "direction": "left" if body_plans[peak_index].turn_world_sign < 0 else "right",
                "peak_head_lead_deg": float(np.max(head)),
                "peak_neck_lead_deg": float(np.max(neck)),
                "peak_chest_lead_deg": float(np.max(chest)),
                "peak_tail_counter_target_deg": float(np.max(tail)),
                "root_heading_at_peak_head_lead_deg": float(root_heading),
                "head_leads_before_half_turn": bool(root_heading < abs(self.profile.turn_default_degrees) * 0.5),
            })

        result.diagnostics.update({
            "v7_contact_locked": True,
            "pelvis_translation": {
                "axis_range_xyz_m": ranges.tolist(),
                "max_abs_lateral_m": lateral_range,
                "vertical_peak_to_peak_m": vertical_range,
                "forward_peak_to_peak_m": forward_range,
                "solved_before_leg_ik": True,
            },
            "turn_mass_lead": turn_metrics,
        })
        gates = result.diagnostics.setdefault("quality_gates", {})
        if "WALK_RELAXED" in schedule.name:
            gates.update({
                "relaxed_pelvis_lateral_within_gate": lateral_range <= self.hip_height * self.profile.max_relaxed_pelvis_lateral_hip_fraction,
                "relaxed_pelvis_vertical_within_gate": vertical_range <= self.hip_height * self.profile.max_relaxed_pelvis_vertical_hip_fraction,
            })
        if active_turn:
            gates.update({
                "turn_head_visibly_leads": turn_metrics["peak_head_lead_deg"] >= self.profile.minimum_turn_head_lead_deg,
                "turn_neck_visibly_leads": turn_metrics["peak_neck_lead_deg"] >= self.profile.minimum_turn_neck_lead_deg,
                "turn_tail_countershape_present": turn_metrics["peak_tail_counter_target_deg"] >= self.profile.minimum_turn_tail_counter_deg,
                "turn_lead_precedes_half_heading": turn_metrics["head_leads_before_half_turn"],
            })
        clip.diagnostics = result.diagnostics
        clip.extras.update({
            "generator": "Eonwild procedural animation toolkit v7",
            "version": "7.0.0",
            "contactLockedPelvis": True,
            "massLedTurn": active_turn,
            "headNeckTurnLead": active_turn,
        })
        if result.in_place_clip is not None:
            result.in_place_clip.diagnostics = {**result.diagnostics, "in_place": True}
            result.in_place_clip.extras.update({
                "generator": "Eonwild procedural animation toolkit v7",
                "version": "7.0.0",
                "contactLockedPelvis": True,
                "massLedTurn": active_turn,
                "headNeckTurnLead": active_turn,
            })
        if not keep_world_matrices:
            clip.world_matrices = None
        return result
