"""Whole-body V7 actions built on the same contact-locked leg solver.

Actions are not upper-body overlays.  Pelvis translation, support load, optional
catch steps and sole targets are resolved first; the final exported pelvis track
is exactly the one used by the constrained leg solve.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import math

import numpy as np

from eonproc_v3.curves import minimum_jerk, smooth_bump
from eonproc_v3.gltf_io import quaternion_continuity
from eonproc_v3.rig import Pose, distribute_chain_rotation
from eonproc_v4.clip import AnimationClip
from eonproc_v4.locomotion import V4FootPlan
from eonproc_v4.terrain import FlatTerrain

from .locomotion import TarbosaurusV7LocomotionGenerator


@dataclass(frozen=True)
class ActionControlsV7:
    pelvis_translation: np.ndarray
    pelvis_yaw: float = 0.0
    pelvis_roll: float = 0.0
    pelvis_pitch: float = 0.0
    spine_pitch: float = 0.0
    spine_yaw: float = 0.0
    spine_roll: float = 0.0
    neck_pitch: float = 0.0
    neck_yaw: float = 0.0
    neck_roll: float = 0.0
    head_pitch: float = 0.0
    head_yaw: float = 0.0
    head_roll: float = 0.0
    jaw_open: float = 0.0
    tail_yaw: float = 0.0
    tail_pitch: float = 0.0
    tail_tip_wave: float = 0.0
    chest_breath_scale: float = 1.0
    arm_tension: float = 0.0
    root_forward: float = 0.0
    root_up: float = 0.0
    left_load: float = 0.5
    right_load: float = 0.5
    left_foot_forward: float = 0.0
    right_foot_forward: float = 0.0
    left_foot_lateral: float = 0.0
    right_foot_lateral: float = 0.0
    left_foot_up: float = 0.0
    right_foot_up: float = 0.0
    left_foot_pitch: float = 0.0
    right_foot_pitch: float = 0.0


def _bump_range(x: float, a: float, b: float, c: float, d: float) -> float:
    if x <= a or x >= d:
        return 0.0
    if x < b:
        return minimum_jerk((x - a) / max(b - a, 1e-6))
    if x <= c:
        return 1.0
    return 1.0 - minimum_jerk((x - c) / max(d - c, 1e-6))


class TarbosaurusV7ActionGenerator:
    def __init__(self, locomotion: TarbosaurusV7LocomotionGenerator):
        self.g = locomotion
        self.profile = locomotion.profile
        self.asset = locomotion.asset
        self.flat = FlatTerrain(locomotion.mesh_ground)

    def _foot_plan(self, side: str, controls: ActionControlsV7) -> V4FootPlan:
        load = controls.left_load if side == "l" else controls.right_load
        forward = controls.left_foot_forward if side == "l" else controls.right_foot_forward
        lateral = controls.left_foot_lateral if side == "l" else controls.right_foot_lateral
        up = controls.left_foot_up if side == "l" else controls.right_foot_up
        pitch = controls.left_foot_pitch if side == "l" else controls.right_foot_pitch
        target = (
            self.g.foot_rest[side].copy()
            + self.g.base_basis.forward * forward
            + self.g.base_basis.lateral * lateral
            + self.g.base_basis.up * up
        )
        stance = bool(load > 0.12 and up < self.g.hip_height * 0.006)
        return V4FootPlan(
            side=side,
            phase=0.32 if side == "l" else 0.68,
            stance=stance,
            swing_u=0.0 if stance else 0.5,
            load=float(load),
            target_world=target,
            contact_world=target.copy(),
            next_contact_world=target.copy(),
            foot_pitch_radians=math.radians(self.profile.contact_foot_deg * 0.30) + pitch,
            toe_radians=0.0,
            terrain_normal=self.g.base_basis.up.copy(),
            terrain_height=self.g.mesh_ground,
            path_heading_radians=0.0,
            contact_distance=0.0,
            next_contact_distance=0.0,
        )

    def _pose(
        self,
        time_seconds: float,
        duration: float,
        controls: ActionControlsV7,
        leg_seeds: dict[str, np.ndarray | None],
    ):
        g = self.g
        g.basis = g.base_basis
        pose = Pose(self.asset)
        pose.add_world_translation_rest(
            g.root,
            g.base_basis.forward * controls.root_forward + g.base_basis.up * controls.root_up,
        )
        # This translation is part of the pose before either leg is solved.
        pose.add_world_translation_rest(g.pelvis, controls.pelvis_translation)
        pose.rotate_world_rest_axis(g.pelvis, g.basis.up, controls.pelvis_yaw)
        pose.rotate_world_rest_axis(g.pelvis, g.basis.forward, controls.pelvis_roll)
        pose.rotate_world_rest_axis(
            g.pelvis,
            g.basis.lateral,
            math.radians(self.profile.pelvis_neutral_pitch_deg) + controls.pelvis_pitch,
        )

        breath_phase = 2.0 * math.pi * self.profile.idle_breath_cycles * time_seconds / max(duration, 1e-8)
        breathing = math.sin(breath_phase) * controls.chest_breath_scale
        distribute_chain_rotation(
            pose,
            g.spine,
            g.basis.lateral,
            math.radians(self.profile.body_lean_deg)
            + controls.spine_pitch
            + math.radians(self.profile.breathing_chest_deg) * breathing,
            [0.06, 0.09, 0.13, 0.18, 0.23, 0.31],
        )
        distribute_chain_rotation(pose, g.spine, g.basis.up, controls.spine_yaw, [0.06, 0.09, 0.14, 0.19, 0.23, 0.29])
        distribute_chain_rotation(pose, g.spine, g.basis.forward, controls.spine_roll, [0.06, 0.09, 0.14, 0.19, 0.23, 0.29])

        relaxed_neck = math.radians(self.profile.neck_relaxed_pitch_deg) - math.radians(self.profile.body_lean_deg) * 0.22
        distribute_chain_rotation(
            pose,
            g.neck,
            g.basis.lateral,
            relaxed_neck + controls.neck_pitch + math.radians(self.profile.breathing_neck_deg) * breathing,
            [0.10, 0.14, 0.19, 0.25, 0.32],
        )
        distribute_chain_rotation(pose, g.neck, g.basis.up, controls.neck_yaw, [0.10, 0.14, 0.19, 0.25, 0.32])
        distribute_chain_rotation(pose, g.neck, g.basis.forward, controls.neck_roll, [0.10, 0.14, 0.19, 0.25, 0.32])
        pose.rotate_world_rest_axis(g.head, g.basis.lateral, math.radians(self.profile.head_horizon_pitch_deg) + controls.head_pitch)
        pose.rotate_world_rest_axis(g.head, g.basis.up, controls.head_yaw)
        pose.rotate_world_rest_axis(g.head, g.basis.forward, controls.head_roll)

        jaw = -math.radians(self.profile.neutral_jaw_close_deg) + controls.jaw_open
        jaw += math.radians(self.profile.jaw_breath_deg) * 0.40 * (0.5 + 0.5 * breathing)
        pose.rotate_world_rest_axis(g.jaw_root, g.basis.lateral, jaw)

        count = len(g.tail)
        for index, bone in enumerate(g.tail):
            f = index / max(count - 1, 1)
            yaw = controls.tail_yaw * (0.45 + 0.85 * f) / count
            yaw += controls.tail_tip_wave * (f ** 1.7) / max(count * 0.55, 1.0)
            pitch = g.tail_neutral_sag[index] + controls.tail_pitch * (0.55 + 0.65 * f) / count
            pose.rotate_world_rest_axis(bone, g.basis.up, float(yaw))
            pose.rotate_world_rest_axis(bone, g.basis.lateral, float(pitch))

        for side, sign in (("l", -1.0), ("r", 1.0)):
            arm, forearm, hand = g.arms[side]
            tension = controls.arm_tension
            pose.rotate_world_rest_axis(arm, -g.basis.lateral, math.radians(1.8) * tension)
            pose.rotate_world_rest_axis(arm, g.basis.up, sign * math.radians(1.4) * tension)
            pose.rotate_world_rest_axis(forearm, g.basis.lateral, math.radians(2.8) * tension)
            pose.rotate_world_rest_axis(hand, g.basis.up, -sign * math.radians(1.0) * tension)

        solved: dict[str, Any] = {}
        new_seeds: dict[str, np.ndarray] = {}
        for side in ("l", "r"):
            foot = self._foot_plan(side, controls)
            pose, result, sole, correction = g._solve_leg_terrain(
                pose, side, foot, 0.0, leg_seeds.get(side), self.flat
            )
            new_seeds[side] = result.angles.copy()
            solved[side] = {"result": result, "sole": sole, "correction": correction, "foot": foot}
        return pose, solved, new_seeds

    def _generate(
        self,
        name: str,
        duration: float,
        loop: bool,
        control_function: Callable[[float, float], ActionControlsV7],
        tags: tuple[str, ...],
    ) -> AnimationClip:
        internal_count = int(round(duration * self.profile.internal_sample_hz)) + 1
        internal_times = np.linspace(0.0, duration, internal_count)
        rotations = {bone: [] for bone in self.g.driven_bones}
        root_translations: list[np.ndarray] = []
        pelvis_translations: list[np.ndarray] = []
        seeds: dict[str, np.ndarray | None] = {"l": None, "r": None}
        penetration = {"l": [], "r": []}
        reversals = 0
        jaw_angles: list[float] = []

        for time_value in internal_times:
            u = float(time_value / max(duration, 1e-8))
            controls = control_function(float(time_value), u)
            pose, solved, seeds = self._pose(float(time_value), duration, controls, seeds)
            for bone in self.g.driven_bones:
                rotations[bone].append(pose.quaternion(bone))
            root_translations.append(pose.translation[self.asset.name_to_node[self.g.root]].copy())
            pelvis_translations.append(pose.translation[self.asset.name_to_node[self.g.pelvis]].copy())
            jaw_angles.append(self.profile.neutral_jaw_close_deg - math.degrees(controls.jaw_open))
            for side in ("l", "r"):
                penetration[side].append(solved[side]["sole"].maximum_penetration)
                geometry = self.g.leg_geometry[side]
                result = solved[side]["result"]
                if result.knee_signed_degrees * geometry["knee_signed_sign"] <= 0.0:
                    reversals += 1
                if result.ankle_signed_degrees * geometry["ankle_signed_sign"] <= 0.0:
                    reversals += 1

        arrays = {bone: quaternion_continuity(np.asarray(values)) for bone, values in rotations.items()}
        root = np.asarray(root_translations)
        pelvis = np.asarray(pelvis_translations)
        if loop:
            for values in arrays.values():
                values[-1] = values[0]
            root[-1] = root[0]
            pelvis[-1] = pelvis[0]

        decimation = self.profile.internal_sample_hz // self.profile.export_sample_hz
        indices = np.arange(0, internal_count, decimation, dtype=np.int64)
        if indices[-1] != internal_count - 1:
            indices = np.append(indices, internal_count - 1)
        rest_pelvis = self.asset.rest_translation[self.asset.name_to_node[self.g.pelvis]]
        pelvis_delta = pelvis - rest_pelvis[None, :]
        diagnostics = {
            "clip": name,
            "duration_seconds": duration,
            "loop": loop,
            "anatomical_reverse_sample_count": reversals,
            "max_sole_penetration_m": {side: float(max(values)) for side, values in penetration.items()},
            "pelvis_translation": {
                "max_abs_lateral_m": float(np.max(np.abs(pelvis_delta @ self.g.base_basis.lateral))),
                "vertical_peak_to_peak_m": float(np.ptp(pelvis_delta @ self.g.base_basis.up)),
                "forward_peak_to_peak_m": float(np.ptp(pelvis_delta @ self.g.base_basis.forward)),
                "solved_before_leg_ik": True,
            },
            "jaw_close_degrees": {
                "minimum": float(np.min(jaw_angles)),
                "maximum": float(np.max(jaw_angles)),
                "start": float(jaw_angles[0]),
                "end": float(jaw_angles[-1]),
            },
            "quality_gates": {
                "zero_anatomical_reversals": reversals == 0,
                "sole_penetration_within_gate": all(
                    max(values) <= self.g.hip_height * self.profile.sole_penetration_gate_hip_fraction
                    for values in penetration.values()
                ),
                "exact_loop": (not loop) or all(np.max(np.abs(values[-1] - values[0])) == 0.0 for values in arrays.values()),
                "pelvis_part_of_contact_solve": True,
            },
        }
        extras = {
            "generator": "Eonwild procedural animation toolkit v7",
            "version": "7.0.0",
            "loop": loop,
            "rootMotion": bool(np.max(np.abs(root - root[0])) > 1e-7),
            "sampleHz": self.profile.export_sample_hz,
            "internalSampleHz": self.profile.internal_sample_hz,
            "action": True,
            "tags": list(tags),
            "neutralJaw": True,
            "anatomicalLegConstraints": True,
            "vertexSoleCollision": True,
            "contactLockedPelvis": True,
        }
        return AnimationClip(
            name=name,
            times=internal_times[indices],
            rotations={bone: values[indices] for bone, values in arrays.items()},
            translations={self.g.root: root[indices], self.g.pelvis: pelvis[indices]},
            extras=extras,
            diagnostics=diagnostics,
        ).normalize(exact_loop=loop)

    def idle(self) -> AnimationClip:
        duration = self.profile.idle_duration_seconds

        def controls(t: float, u: float) -> ActionControlsV7:
            c = 2.0 * math.pi * u
            shift = self.g.hip_height * self.profile.idle_weight_shift_hip_fraction * math.sin(c)
            scan = math.radians(self.profile.idle_head_scan_yaw_deg) * math.sin(c - 0.42)
            scan_pitch = math.radians(self.profile.idle_head_scan_pitch_deg) * math.sin(2.0 * c + 0.7)
            return ActionControlsV7(
                pelvis_translation=(
                    self.g.base_basis.lateral * shift
                    + self.g.base_basis.up * (0.0009 * self.g.hip_height * math.cos(2.0 * c))
                ),
                pelvis_roll=math.radians(0.24) * math.sin(c),
                pelvis_yaw=math.radians(0.13) * math.sin(c + 0.35),
                spine_roll=-math.radians(0.14) * math.sin(c),
                neck_yaw=scan * 0.36,
                head_yaw=scan,
                head_pitch=scan_pitch,
                tail_yaw=-math.radians(1.2) * math.sin(c),
                tail_tip_wave=math.radians(self.profile.idle_tail_tip_deg) * math.sin(2.0 * c + 0.55),
                left_load=0.5 + 0.035 * math.sin(c),
                right_load=0.5 - 0.035 * math.sin(c),
            )

        return self._generate("PROC_IDLE_BREATH_V7", duration, True, controls, ("idle", "breathing", "contact_locked"))

    def alert_idle(self) -> AnimationClip:
        duration = 6.4

        def controls(t: float, u: float) -> ActionControlsV7:
            c = 2.0 * math.pi * u
            scan = math.radians(self.profile.alert_scan_yaw_deg) * math.sin(c)
            return ActionControlsV7(
                pelvis_translation=self.g.base_basis.lateral * (self.g.hip_height * 0.0048 * math.sin(c)),
                pelvis_roll=math.radians(0.48) * math.sin(c),
                spine_pitch=-math.radians(0.7),
                neck_pitch=-math.radians(self.profile.alert_neck_raise_deg),
                neck_yaw=scan * 0.43,
                head_pitch=-math.radians(self.profile.alert_head_raise_deg),
                head_yaw=scan,
                head_roll=math.radians(0.45) * math.sin(2.0 * c + 0.4),
                tail_pitch=-math.radians(self.profile.alert_tail_raise_deg),
                tail_yaw=-scan * 0.22,
                tail_tip_wave=math.radians(2.7) * math.sin(2.0 * c + 0.8),
                arm_tension=0.65,
                left_load=0.5 + 0.055 * math.sin(c),
                right_load=0.5 - 0.055 * math.sin(c),
            )

        return self._generate("PROC_ALERT_IDLE_V7", duration, True, controls, ("alert", "idle", "contact_locked"))

    def eating_loop(self) -> AnimationClip:
        duration = self.profile.eating_duration_seconds

        def controls(t: float, u: float) -> ActionControlsV7:
            cycle = 2.0 * math.pi * u
            bite_phase = (u * self.profile.eating_bite_count) % 1.0
            open_env = _bump_range(bite_phase, 0.04, 0.22, 0.39, 0.60)
            chew_env = _bump_range(bite_phase, 0.58, 0.64, 0.82, 0.94)
            chew = math.sin(2.0 * math.pi * 2.5 * bite_phase) * chew_env
            search = math.radians(2.4) * math.sin(cycle)
            return ActionControlsV7(
                pelvis_translation=(
                    -self.g.base_basis.forward * (self.g.hip_height * self.profile.eating_pelvis_back_hip_fraction)
                    - self.g.base_basis.up * (self.g.hip_height * self.profile.eating_pelvis_down_hip_fraction)
                    + self.g.base_basis.lateral * (self.g.hip_height * 0.0028 * math.sin(cycle))
                ),
                pelvis_pitch=math.radians(1.2),
                spine_pitch=math.radians(self.profile.eating_body_lower_deg),
                neck_pitch=math.radians(self.profile.eating_neck_lower_deg) + math.radians(1.6) * math.sin(2.0 * cycle),
                neck_yaw=search * 0.34,
                head_pitch=math.radians(self.profile.eating_head_lower_deg) + math.radians(1.1) * math.sin(2.0 * cycle + 0.3),
                head_yaw=search,
                jaw_open=math.radians(self.profile.eating_jaw_open_deg) * open_env + math.radians(self.profile.eating_chew_deg) * chew,
                tail_pitch=-math.radians(3.2),
                tail_yaw=-search * 0.48,
                tail_tip_wave=math.radians(1.8) * math.sin(2.0 * cycle + 0.5),
                arm_tension=0.24,
                left_load=0.52 + 0.055 * math.sin(cycle),
                right_load=0.48 - 0.055 * math.sin(cycle),
            )

        return self._generate("PROC_EAT_LOOP_V7", duration, True, controls, ("eat", "feeding", "whole_body_lower", "loop"))

    def bite_attack(self, lead_side: str = "l") -> AnimationClip:
        if lead_side not in ("l", "r"):
            raise ValueError("lead_side must be 'l' or 'r'")
        duration = self.profile.bite_duration_seconds
        a = self.profile.bite_anticipation_fraction
        contact = self.profile.bite_contact_fraction
        recovery_start = self.profile.bite_recovery_fraction
        mirror = -1.0 if lead_side == "l" else 1.0

        def controls(t: float, u: float) -> ActionControlsV7:
            preload = minimum_jerk(u / a) if u < a else 1.0
            strike = 0.0 if u < a else minimum_jerk((u - a) / max(contact - a, 1e-6)) if u < contact else 1.0
            recovery = 0.0 if u < recovery_start else minimum_jerk((u - recovery_start) / max(1.0 - recovery_start, 1e-6))
            active = 1.0 - recovery
            charge = preload * (1.0 - strike) * active
            delivery = strike * active
            recoil = _bump_range(u, contact, contact + 0.04, recovery_start - 0.06, recovery_start)

            # Wide anticipation gape, complete closure immediately before the
            # contact event, tiny damped rebound only.
            if u < a:
                gape = self.profile.bite_jaw_open_deg * minimum_jerk(u / a)
            elif u < contact - 0.075:
                gape = self.profile.bite_jaw_open_deg
            elif u < contact:
                gape = self.profile.bite_jaw_open_deg * (1.0 - minimum_jerk((u - (contact - 0.075)) / 0.075))
            elif u < contact + 0.10:
                gape = self.profile.bite_snap_close_deg * _bump_range(u, contact, contact + 0.025, contact + 0.055, contact + 0.10)
            else:
                gape = 0.0

            step = _bump_range(u, a + 0.015, a + 0.10, contact + 0.08, recovery_start + 0.08)
            step_lift = _bump_range(u, a + 0.015, a + 0.07, contact - 0.045, contact + 0.015)
            step_forward = self.g.hip_height * self.profile.bite_catch_step_hip_fraction * step
            step_up = self.g.hip_height * 0.030 * step_lift

            preload_lead_load = 0.34
            lead_load = preload_lead_load * charge + 0.63 * delivery + 0.50 * recovery
            lead_load += 0.50 * (1.0 - max(charge, delivery, recovery))
            other_load = 1.0 - lead_load
            # Keep the swinging catch foot unloaded until it has descended.
            if step_lift > 0.04:
                lead_load *= 0.20
                other_load = 1.0 - lead_load

            kwargs = {
                "left_load": lead_load if lead_side == "l" else other_load,
                "right_load": lead_load if lead_side == "r" else other_load,
                "left_foot_forward": step_forward if lead_side == "l" else 0.0,
                "right_foot_forward": step_forward if lead_side == "r" else 0.0,
                "left_foot_up": step_up if lead_side == "l" else 0.0,
                "right_foot_up": step_up if lead_side == "r" else 0.0,
                "left_foot_lateral": -self.g.hip_height * 0.010 * step if lead_side == "l" else 0.0,
                "right_foot_lateral": self.g.hip_height * 0.010 * step if lead_side == "r" else 0.0,
            }
            return ActionControlsV7(
                pelvis_translation=(
                    -self.g.base_basis.forward * (self.g.hip_height * self.profile.bite_preload_back_hip_fraction * charge)
                    - self.g.base_basis.up * (self.g.hip_height * self.profile.bite_preload_down_hip_fraction * charge)
                    + self.g.base_basis.forward * (self.g.hip_height * 0.026 * delivery)
                    + self.g.base_basis.lateral * (mirror * self.g.hip_height * 0.010 * delivery)
                ),
                pelvis_yaw=mirror * math.radians(1.8) * delivery,
                pelvis_roll=-mirror * math.radians(0.8) * charge + mirror * math.radians(1.2) * delivery,
                pelvis_pitch=math.radians(self.profile.bite_body_crouch_deg) * charge,
                spine_pitch=math.radians(self.profile.bite_body_crouch_deg) * 0.62 * charge - math.radians(1.4) * delivery,
                spine_yaw=mirror * math.radians(1.6) * delivery,
                neck_pitch=(
                    math.radians(self.profile.bite_neck_retract_deg) * charge
                    - math.radians(self.profile.bite_neck_thrust_deg) * delivery
                    + math.radians(3.5) * recoil
                ),
                neck_yaw=mirror * math.radians(1.5) * delivery,
                head_pitch=-math.radians(4.3) * delivery + math.radians(2.6) * recoil,
                head_yaw=mirror * math.radians(self.profile.bite_head_yaw_deg) * math.sin(math.pi * strike) * active,
                jaw_open=math.radians(gape),
                tail_pitch=-math.radians(3.5) * charge + math.radians(1.6) * recoil,
                tail_yaw=-mirror * math.radians(4.2) * delivery,
                tail_tip_wave=-mirror * math.radians(2.0) * recoil,
                arm_tension=preload * active,
                root_forward=self.g.hip_height * self.profile.bite_lunge_hip_fraction * delivery,
                **kwargs,
            )

        name = "PROC_BITE_ATTACK_V7" if lead_side == "l" else "PROC_BITE_ATTACK_MIRRORED_V7"
        tags = ("attack", "bite", "power", "hindlimb_driven", "lead_left" if lead_side == "l" else "lead_right")
        return self._generate(name, duration, False, controls, tags)

    def roar(self) -> AnimationClip:
        duration = self.profile.roar_duration_seconds
        inhale_end = self.profile.roar_inhale_fraction
        peak = self.profile.roar_peak_fraction
        release = self.profile.roar_release_fraction

        def controls(t: float, u: float) -> ActionControlsV7:
            inhale = minimum_jerk(u / inhale_end) if u < inhale_end else 1.0
            if u < inhale_end:
                open_mix = 0.0
            elif u < peak:
                open_mix = minimum_jerk((u - inhale_end) / max(peak - inhale_end, 1e-6))
            else:
                open_mix = 1.0
            close_mix = 0.0 if u < release else minimum_jerk((u - release) / max(1.0 - release, 1e-6))
            active = open_mix * (1.0 - close_mix)
            shake = math.sin(2.0 * math.pi * 5.0 * t) * _bump_range(u, peak - 0.16, peak - 0.08, release - 0.04, release + 0.06)
            return ActionControlsV7(
                pelvis_translation=-self.g.base_basis.up * (self.g.hip_height * 0.010 * inhale),
                pelvis_roll=math.radians(0.6) * shake,
                spine_pitch=-math.radians(1.6) * inhale,
                neck_pitch=-math.radians(self.profile.roar_neck_raise_deg) * active - math.radians(3.4) * inhale * (1.0 - open_mix),
                neck_yaw=math.radians(0.6) * shake,
                head_pitch=-math.radians(self.profile.roar_head_raise_deg) * active,
                head_yaw=math.radians(self.profile.roar_head_shake_deg) * shake,
                head_roll=math.radians(0.65) * shake,
                jaw_open=math.radians(self.profile.roar_jaw_open_deg) * active,
                tail_pitch=-math.radians(self.profile.roar_tail_brace_deg) * inhale,
                tail_yaw=-math.radians(1.2) * shake,
                tail_tip_wave=math.radians(1.8) * math.sin(2.0 * math.pi * 1.35 * t) * active,
                chest_breath_scale=1.0 + self.profile.roar_chest_expand_deg / max(self.profile.breathing_chest_deg, 0.1) * inhale,
                arm_tension=active,
                left_load=0.5 + 0.035 * shake,
                right_load=0.5 - 0.035 * shake,
            )

        return self._generate("PROC_ROAR_V7", duration, False, controls, ("roar", "display", "one_shot"))
