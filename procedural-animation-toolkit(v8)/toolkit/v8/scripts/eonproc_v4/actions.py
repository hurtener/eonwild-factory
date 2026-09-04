"""Whole-body action and idle animation layers for Tarbosaurus V4."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import math

import numpy as np

from eonproc_v3.curves import minimum_jerk, smooth_bump
from eonproc_v3.gltf_io import quaternion_continuity
from eonproc_v3.rig import Pose, distribute_chain_rotation

from .clip import AnimationClip
from .locomotion import TerrainAwareLocomotionGenerator, V4FootPlan
from .terrain import FlatTerrain


@dataclass(frozen=True)
class ActionControls:
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


class ActionGenerator:
    def __init__(self, locomotion: TerrainAwareLocomotionGenerator):
        self.g = locomotion
        self.profile = locomotion.profile
        self.asset = locomotion.asset
        self.flat = FlatTerrain(locomotion.mesh_ground)

    def _fixed_foot_plan(self, side: str, load: float) -> V4FootPlan:
        target = self.g.foot_rest[side].copy()
        return V4FootPlan(
            side=side, phase=0.32 if side == "l" else 0.68, stance=True, swing_u=0.0,
            load=float(load), target_world=target, contact_world=target.copy(), next_contact_world=target.copy(),
            foot_pitch_radians=math.radians(self.profile.contact_foot_deg * 0.35),
            toe_radians=0.0, terrain_normal=self.g.base_basis.up.copy(), terrain_height=self.g.mesh_ground,
            path_heading_radians=0.0, contact_distance=0.0, next_contact_distance=0.0,
        )

    def _pose(
        self,
        time_seconds: float,
        duration: float,
        controls: ActionControls,
        leg_seeds: dict[str, np.ndarray | None],
    ) -> tuple[Pose, dict[str, Any], dict[str, np.ndarray]]:
        g = self.g
        g.basis = g.base_basis
        pose = Pose(self.asset)
        pose.add_world_translation_rest(g.root, g.base_basis.forward * controls.root_forward + g.base_basis.up * controls.root_up)
        pose.add_world_translation_rest(g.pelvis, controls.pelvis_translation)
        pose.rotate_world_rest_axis(g.pelvis, g.basis.up, controls.pelvis_yaw)
        pose.rotate_world_rest_axis(g.pelvis, g.basis.forward, controls.pelvis_roll)
        pose.rotate_world_rest_axis(g.pelvis, g.basis.lateral, math.radians(self.profile.pelvis_neutral_pitch_deg) + controls.pelvis_pitch)

        breath_phase = 2.0 * math.pi * self.profile.idle_breath_cycles * time_seconds / max(duration, 1e-8)
        breathing = math.sin(breath_phase) * controls.chest_breath_scale
        distribute_chain_rotation(
            pose, g.spine, g.basis.lateral,
            math.radians(self.profile.body_lean_deg) + controls.spine_pitch
            + math.radians(self.profile.breathing_chest_deg) * breathing,
            [0.07, 0.10, 0.13, 0.17, 0.22, 0.31],
        )
        distribute_chain_rotation(pose, g.spine, g.basis.up, controls.spine_yaw, [0.08, 0.11, 0.14, 0.18, 0.22, 0.27])
        distribute_chain_rotation(pose, g.spine, g.basis.forward, controls.spine_roll, [0.08, 0.11, 0.14, 0.18, 0.22, 0.27])

        relaxed_neck = math.radians(self.profile.neck_relaxed_pitch_deg) - math.radians(self.profile.body_lean_deg) * 0.22
        distribute_chain_rotation(
            pose, g.neck, g.basis.lateral,
            relaxed_neck + controls.neck_pitch + math.radians(self.profile.breathing_neck_deg) * breathing,
            [0.11, 0.15, 0.19, 0.24, 0.31],
        )
        distribute_chain_rotation(pose, g.neck, g.basis.up, controls.neck_yaw, [0.11, 0.15, 0.19, 0.24, 0.31])
        distribute_chain_rotation(pose, g.neck, g.basis.forward, controls.neck_roll, [0.11, 0.15, 0.19, 0.24, 0.31])
        pose.rotate_world_rest_axis(g.head, g.basis.lateral, math.radians(self.profile.head_horizon_pitch_deg) + controls.head_pitch)
        pose.rotate_world_rest_axis(g.head, g.basis.up, controls.head_yaw)
        pose.rotate_world_rest_axis(g.head, g.basis.forward, controls.head_roll)

        jaw = -math.radians(self.profile.neutral_jaw_close_deg) + controls.jaw_open
        jaw += math.radians(self.profile.jaw_breath_deg) * 0.45 * (0.5 + 0.5 * breathing)
        pose.rotate_world_rest_axis(g.jaw_root, g.basis.lateral, jaw)

        tail_count = len(g.tail)
        root_to_tip = np.linspace(0.55, 1.35, tail_count)
        for index, bone in enumerate(g.tail):
            yaw = controls.tail_yaw * root_to_tip[index] / tail_count
            yaw += controls.tail_tip_wave * (index / max(tail_count - 1, 1)) ** 1.6 / tail_count
            pitch = g.tail_neutral_sag[index] + controls.tail_pitch * root_to_tip[index] / tail_count
            pose.rotate_world_rest_axis(bone, g.basis.up, float(yaw))
            pose.rotate_world_rest_axis(bone, g.basis.lateral, float(pitch))

        tension = controls.arm_tension
        for side, sign in (("l", -1.0), ("r", 1.0)):
            arm, forearm, hand = g.arms[side]
            pose.rotate_world_rest_axis(arm, -g.basis.lateral, math.radians(2.0) * tension)
            pose.rotate_world_rest_axis(arm, g.basis.up, sign * math.radians(1.6) * tension)
            pose.rotate_world_rest_axis(forearm, g.basis.lateral, math.radians(3.0) * tension)
            pose.rotate_world_rest_axis(hand, g.basis.up, -sign * math.radians(1.2) * tension)

        solved: dict[str, Any] = {}
        new_seeds: dict[str, np.ndarray] = {}
        for side, load in (("l", controls.left_load), ("r", controls.right_load)):
            foot = self._fixed_foot_plan(side, load)
            pose, result, sole, correction = g._solve_leg_terrain(
                pose, side, foot, 0.0, leg_seeds.get(side), self.flat
            )
            new_seeds[side] = result.angles.copy()
            solved[side] = {"result": result, "sole": sole, "correction": correction}
        return pose, solved, new_seeds

    def _generate(
        self,
        name: str,
        duration: float,
        loop: bool,
        control_function: Callable[[float, float], ActionControls],
        tags: tuple[str, ...],
        keep_world_matrices: bool = False,
    ) -> AnimationClip:
        internal_count = int(round(duration * self.profile.internal_sample_hz)) + 1
        internal_times = np.linspace(0.0, duration, internal_count)
        rotations = {name: [] for name in self.g.driven_bones}
        translations: list[np.ndarray] = []
        worlds: list[list[np.ndarray]] | None = [] if keep_world_matrices else None
        seeds: dict[str, np.ndarray | None] = {"l": None, "r": None}
        sole_penetration = {"l": [], "r": []}
        joint_reversals = 0
        for time_value in internal_times:
            u = float(time_value / max(duration, 1e-8))
            controls = control_function(float(time_value), u)
            pose, solved, seeds = self._pose(float(time_value), duration, controls, seeds)
            for bone in self.g.driven_bones:
                rotations[bone].append(pose.quaternion(bone))
            translations.append(pose.translation[self.asset.name_to_node[self.g.root]].copy())
            for side in ("l", "r"):
                sole_penetration[side].append(solved[side]["sole"].maximum_penetration)
                geometry = self.g.leg_geometry[side]
                result = solved[side]["result"]
                if result.knee_signed_degrees * geometry["knee_signed_sign"] <= 0.0:
                    joint_reversals += 1
                if result.ankle_signed_degrees * geometry["ankle_signed_sign"] <= 0.0:
                    joint_reversals += 1
            if worlds is not None:
                worlds.append([matrix.copy() for matrix in pose.world_matrices])

        arrays = {bone: quaternion_continuity(np.asarray(values)) for bone, values in rotations.items()}
        root = np.asarray(translations)
        if loop:
            for values in arrays.values():
                values[-1] = values[0]
            root[-1] = root[0]
        decimation = self.profile.internal_sample_hz // self.profile.export_sample_hz
        indices = np.arange(0, internal_count, decimation, dtype=np.int64)
        if indices[-1] != internal_count - 1:
            indices = np.append(indices, internal_count - 1)
        extras = {
            "generator": "Eonwild procedural animation toolkit v4",
            "version": "4.0.0",
            "loop": loop,
            "rootMotion": bool(np.max(np.abs(root - root[0])) > 1e-7),
            "sampleHz": self.profile.export_sample_hz,
            "internalSampleHz": self.profile.internal_sample_hz,
            "action": True,
            "tags": list(tags),
            "neutralJaw": True,
            "anatomicalLegConstraints": True,
            "vertexSoleCollision": True,
        }
        diagnostics = {
            "clip": name,
            "duration_seconds": duration,
            "loop": loop,
            "max_sole_penetration_m": {side: float(max(values)) for side, values in sole_penetration.items()},
            "anatomical_reverse_sample_count": joint_reversals,
            "quality_gates": {
                "zero_anatomical_reversals": joint_reversals == 0,
                "sole_penetration_within_gate": all(max(values) <= self.g.hip_height * self.profile.sole_penetration_gate_hip_fraction for values in sole_penetration.values()),
                "exact_loop": (not loop) or all(np.max(np.abs(values[-1] - values[0])) == 0.0 for values in arrays.values()),
            },
        }
        return AnimationClip(
            name=name,
            times=internal_times[indices],
            rotations={bone: values[indices] for bone, values in arrays.items()},
            translations={self.g.root: root[indices]},
            extras=extras,
            diagnostics=diagnostics,
            world_matrices=None if worlds is None else [worlds[int(index)] for index in indices],
        ).normalize(exact_loop=loop)

    def idle(self) -> AnimationClip:
        duration = self.profile.idle_duration_seconds
        def controls(t: float, u: float) -> ActionControls:
            cycle = 2.0 * math.pi * u
            shift = self.g.hip_height * self.profile.idle_weight_shift_hip_fraction * math.sin(cycle)
            scan = math.radians(self.profile.idle_head_scan_yaw_deg) * math.sin(cycle - 0.35)
            scan_pitch = math.radians(self.profile.idle_head_scan_pitch_deg) * math.sin(2.0 * cycle + 0.7)
            return ActionControls(
                pelvis_translation=self.g.base_basis.lateral * shift + self.g.base_basis.up * (0.003 * self.g.hip_height * math.cos(2.0 * cycle)),
                pelvis_roll=math.radians(1.4) * math.sin(cycle),
                pelvis_yaw=math.radians(0.7) * math.sin(cycle + 0.4),
                spine_roll=-math.radians(0.8) * math.sin(cycle),
                neck_yaw=scan * 0.38,
                head_yaw=scan,
                head_pitch=scan_pitch,
                tail_yaw=-math.radians(1.8) * math.sin(cycle),
                tail_tip_wave=math.radians(self.profile.idle_tail_tip_deg) * math.sin(2.0 * cycle + 0.55),
                left_load=0.5 + 0.18 * math.sin(cycle),
                right_load=0.5 - 0.18 * math.sin(cycle),
            )
        return self._generate("PROC_IDLE_BREATH_V4", duration, True, controls, ("idle", "breathing"))

    def alert_idle(self) -> AnimationClip:
        duration = 6.0
        def controls(t: float, u: float) -> ActionControls:
            cycle = 2.0 * math.pi * u
            scan = math.radians(self.profile.alert_scan_yaw_deg) * math.sin(cycle)
            return ActionControls(
                pelvis_translation=self.g.base_basis.lateral * (self.g.hip_height * 0.012 * math.sin(cycle)),
                pelvis_roll=math.radians(1.6) * math.sin(cycle),
                spine_pitch=-math.radians(1.2),
                neck_pitch=-math.radians(self.profile.alert_neck_raise_deg),
                neck_yaw=scan * 0.42,
                head_pitch=-math.radians(self.profile.alert_head_raise_deg),
                head_yaw=scan,
                head_roll=math.radians(0.7) * math.sin(2.0 * cycle + 0.4),
                tail_pitch=-math.radians(self.profile.alert_tail_raise_deg),
                tail_yaw=-scan * 0.18,
                tail_tip_wave=math.radians(3.2) * math.sin(2.0 * cycle + 0.8),
                arm_tension=0.7,
                left_load=0.5 + 0.14 * math.sin(cycle),
                right_load=0.5 - 0.14 * math.sin(cycle),
            )
        return self._generate("PROC_ALERT_IDLE_V4", duration, True, controls, ("alert", "idle"))

    def eating_loop(self) -> AnimationClip:
        duration = self.profile.eating_duration_seconds
        def controls(t: float, u: float) -> ActionControls:
            cycle = 2.0 * math.pi * u
            bite_phase = (u * self.profile.eating_bite_count) % 1.0
            open_envelope = smooth_bump(bite_phase) ** 0.62
            chew = math.sin(2.0 * math.pi * bite_phase * 2.0) * (1.0 - smooth_bump(bite_phase))
            side_search = math.sin(cycle) * math.radians(3.0)
            return ActionControls(
                pelvis_translation=-self.g.base_basis.forward * (self.g.hip_height * self.profile.eating_pelvis_back_hip_fraction)
                    - self.g.base_basis.up * (self.g.hip_height * 0.025)
                    + self.g.base_basis.lateral * (self.g.hip_height * 0.008 * math.sin(cycle)),
                pelvis_pitch=math.radians(1.8),
                spine_pitch=math.radians(self.profile.eating_body_lower_deg),
                neck_pitch=math.radians(self.profile.eating_neck_lower_deg) + math.radians(2.0) * math.sin(2.0 * cycle),
                neck_yaw=side_search * 0.35,
                head_pitch=math.radians(self.profile.eating_head_lower_deg) + math.radians(1.4) * math.sin(2.0 * cycle + 0.3),
                head_yaw=side_search,
                jaw_open=math.radians(self.profile.eating_jaw_open_deg) * open_envelope + math.radians(self.profile.eating_chew_deg) * chew,
                tail_pitch=-math.radians(3.5),
                tail_yaw=-side_search * 0.45,
                tail_tip_wave=math.radians(2.0) * math.sin(2.0 * cycle + 0.5),
                arm_tension=0.25,
                left_load=0.53 + 0.08 * math.sin(cycle),
                right_load=0.47 - 0.08 * math.sin(cycle),
            )
        return self._generate("PROC_EAT_LOOP_V4", duration, True, controls, ("eat", "feeding", "loop"))

    def bite_attack(self) -> AnimationClip:
        duration = self.profile.bite_duration_seconds
        a = self.profile.bite_anticipation_fraction
        c = self.profile.bite_contact_fraction
        r = self.profile.bite_recovery_fraction
        def controls(t: float, u: float) -> ActionControls:
            anticipation = minimum_jerk(u / a) if u < a else 1.0
            if u < a:
                attack = 0.0
            elif u < c:
                attack = minimum_jerk((u - a) / (c - a))
            else:
                attack = 1.0
            recovery = 0.0 if u < r else minimum_jerk((u - r) / (1.0 - r))
            active = (1.0 - recovery)
            lunge = attack * active
            crouch = anticipation * (1.0 - attack) * active
            jaw_open = math.radians(self.profile.bite_jaw_open_deg) * anticipation * (1.0 - minimum_jerk(max(0.0, (u - (c - 0.07)) / 0.07)))
            jaw_open += math.radians(self.profile.bite_snap_close_deg) * smooth_bump(max(0.0, min(1.0, (u - c) / 0.13)))
            recoil = smooth_bump(max(0.0, min(1.0, (u - c) / max(r - c, 1e-6))))
            return ActionControls(
                pelvis_translation=-self.g.base_basis.up * (self.g.hip_height * 0.035 * crouch)
                    + self.g.base_basis.forward * (self.g.hip_height * 0.035 * lunge),
                pelvis_pitch=math.radians(self.profile.bite_body_crouch_deg) * crouch,
                spine_pitch=math.radians(self.profile.bite_body_crouch_deg) * crouch - math.radians(2.0) * lunge,
                neck_pitch=math.radians(self.profile.bite_neck_retract_deg) * anticipation * (1.0 - attack)
                    - math.radians(self.profile.bite_neck_thrust_deg) * lunge
                    + math.radians(4.0) * recoil,
                head_pitch=-math.radians(5.0) * lunge + math.radians(3.0) * recoil,
                head_yaw=math.radians(self.profile.bite_head_yaw_deg) * math.sin(math.pi * attack) * active,
                jaw_open=jaw_open,
                tail_pitch=-math.radians(4.0) * crouch + math.radians(2.0) * recoil,
                tail_yaw=-math.radians(3.0) * math.sin(math.pi * attack) * active,
                arm_tension=anticipation * active,
                root_forward=self.g.hip_height * self.profile.bite_lunge_hip_fraction * lunge * (1.0 - 0.72 * recovery),
                left_load=0.58 + 0.10 * crouch,
                right_load=0.42 - 0.10 * crouch,
            )
        return self._generate("PROC_BITE_ATTACK_V4", duration, False, controls, ("attack", "bite", "one_shot"))

    def roar(self) -> AnimationClip:
        duration = self.profile.roar_duration_seconds
        inhale_end = self.profile.roar_inhale_fraction
        peak = self.profile.roar_peak_fraction
        release = self.profile.roar_release_fraction
        def controls(t: float, u: float) -> ActionControls:
            inhale = minimum_jerk(u / inhale_end) if u < inhale_end else 1.0
            if u < inhale_end:
                open_mix = 0.0
            elif u < peak:
                open_mix = minimum_jerk((u - inhale_end) / (peak - inhale_end))
            else:
                open_mix = 1.0
            close_mix = 0.0 if u < release else minimum_jerk((u - release) / (1.0 - release))
            active = open_mix * (1.0 - close_mix)
            shake = math.sin(2.0 * math.pi * 5.2 * t) * smooth_bump(max(0.0, min(1.0, (u - peak + 0.18) / 0.48)))
            return ActionControls(
                pelvis_translation=-self.g.base_basis.up * (self.g.hip_height * 0.012 * inhale),
                pelvis_roll=math.radians(0.8) * shake,
                spine_pitch=-math.radians(2.0) * inhale,
                neck_pitch=-math.radians(self.profile.roar_neck_raise_deg) * active - math.radians(4.0) * inhale * (1.0 - open_mix),
                neck_yaw=math.radians(0.7) * shake,
                head_pitch=-math.radians(self.profile.roar_head_raise_deg) * active,
                head_yaw=math.radians(self.profile.roar_head_shake_deg) * shake,
                head_roll=math.radians(0.8) * shake,
                jaw_open=math.radians(self.profile.roar_jaw_open_deg) * active,
                tail_pitch=-math.radians(self.profile.roar_tail_brace_deg) * inhale,
                tail_yaw=-math.radians(1.5) * shake,
                tail_tip_wave=math.radians(2.2) * math.sin(2.0 * math.pi * 1.4 * t) * active,
                chest_breath_scale=1.0 + self.profile.roar_chest_expand_deg / max(self.profile.breathing_chest_deg, 0.1) * inhale,
                arm_tension=active,
                left_load=0.5 + 0.05 * shake,
                right_load=0.5 - 0.05 * shake,
            )
        return self._generate("PROC_ROAR_V4", duration, False, controls, ("roar", "display", "one_shot"))
