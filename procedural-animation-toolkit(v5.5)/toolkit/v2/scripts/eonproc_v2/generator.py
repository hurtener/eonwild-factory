"""Contact-aware biped animation kernel used by Eonwild procedural animation v2.

The kernel keeps the original deformation skeleton and layers:
  * phase/event foot planning,
  * C2 swing trajectories,
  * world-space contact correction with constrained CCD,
  * support-weight pelvis translation and body compensation,
  * periodic spring-damper tail response,
  * calibrated neutral jaw + breathing micro-motion,
  * dense 120 Hz evaluation and 60 Hz export.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import math

import numpy as np
from scipy.spatial.transform import Rotation

from .curves import minimum_jerk, smooth_bump, cyclic_gaussian
from .gltf_io import GlbAsset, quaternion_continuity
from .profile import BipedV2Profile
from .rig import AnatomicalBasis, Pose, SemanticMap, distribute_chain_rotation


@dataclass(frozen=True)
class FootPlan:
    side: str
    phase: float
    stance: bool
    swing_u: float
    load: float
    target_world: np.ndarray
    contact_world: np.ndarray
    foot_pitch_radians: float
    toe_radians: float


@dataclass(frozen=True)
class BodyPlan:
    root_progress: float
    pelvis_translation_world: np.ndarray
    pelvis_yaw: float
    pelvis_roll: float
    pelvis_pitch: float
    support_lateral_normalized: float
    vertical_signal: float
    left: FootPlan
    right: FootPlan


@dataclass
class GeneratedMotion:
    times_internal: np.ndarray
    times_export: np.ndarray
    rotations_internal: dict[str, np.ndarray]
    rotations_export: dict[str, np.ndarray]
    root_translation_internal: np.ndarray
    root_translation_export: np.ndarray
    diagnostics: dict[str, Any]
    frame_plans: list[BodyPlan]
    world_matrices_internal: list[list[np.ndarray]] | None = None


class ContactAwareBipedGenerator:
    def __init__(
        self,
        asset: GlbAsset,
        semantics: SemanticMap,
        profile: BipedV2Profile,
    ):
        self.asset = asset
        self.semantics = semantics
        self.profile = profile
        self.basis = AnatomicalBasis.gltf_y_up(asset, semantics)
        self._validate()

        self.root = semantics.bone("root")
        self.pelvis = semantics.bone("pelvis")
        self.head = semantics.bone("head")
        self.jaw_root = semantics.bone("jaw")
        self.spine = [semantics.bone(f"spine_{index:02d}") for index in range(1, 6)] + [semantics.bone("chest")]
        self.neck = [semantics.bone(f"neck_{index:02d}") for index in range(1, 6)]
        self.tail = [semantics.bone(f"tail_{index:02d}") for index in range(1, 10)]
        self.legs = {
            side: {
                "thigh": semantics.bone(f"thigh_{side}"),
                "shin": semantics.bone(f"shin_{side}"),
                "ankle": semantics.bone(f"ankle_{side}"),
                "foot": semantics.bone(f"foot_{side}"),
            }
            for side in ("l", "r")
        }
        self.toe_chains: dict[str, list[list[str]]] = {}
        for side in ("l", "r"):
            roots = [
                semantics.bone(f"toe_{side}"),
                semantics.bone(f"toe_2_{side}"),
                semantics.bone(f"toe_3_{side}"),
            ]
            self.toe_chains[side] = [asset.single_child_chain(root, max_nodes=4) for root in roots]
        self.toe_tip_rest_y = {
            side: min(
                float(asset.rest_world[asset.name_to_node[chain[-1]]][1, 3])
                for chain in self.toe_chains[side]
            )
            for side in ("l", "r")
        }
        self.arms = {
            side: [
                semantics.bone(f"arm_{side}"),
                semantics.bone(f"forearm_{side}"),
                semantics.bone(f"hand_{side}"),
            ]
            for side in ("l", "r")
        }
        self.jaw_chain = asset.single_child_chain(self.jaw_root, max_nodes=12)

        primitive = asset.primitive()
        mesh_ground = float(np.min(primitive.positions[:, 1]))
        pelvis_y = float(asset.rest_world[asset.name_to_node[self.pelvis]][1, 3])
        self.hip_height = pelvis_y - mesh_ground
        self.scale = self.hip_height / profile.reference_hip_height_m
        self.stride = profile.stride_length_m * self.scale
        self.speed = self.stride * profile.cycle_hz
        self.cycle_duration = 1.0 / profile.cycle_hz
        self.duration = self.cycle_duration * profile.supercycle_count
        self.swing_lift = self.hip_height * profile.swing_lift_hip_fraction
        self.swing_outward = self.hip_height * profile.swing_outward_hip_fraction
        self.pelvis_bob = self.hip_height * profile.pelvis_vertical_bob_hip_fraction
        self.pelvis_loading_drop = self.hip_height * profile.pelvis_loading_drop_hip_fraction
        self.pelvis_forward_sway = self.hip_height * profile.pelvis_forward_sway_hip_fraction
        self.ik_tolerance = self.hip_height * profile.ik_tolerance_hip_fraction
        self.foot_rest = {
            side: asset.rest_world[asset.name_to_node[self.legs[side]["foot"]]][:3, 3].copy()
            for side in ("l", "r")
        }
        self.foot_mid = 0.5 * (self.foot_rest["l"] + self.foot_rest["r"])
        self.foot_span = float(abs(np.dot(self.foot_rest["r"] - self.foot_rest["l"], self.basis.lateral)))
        self.contact_lead = self.stride * profile.contact_lead_stride
        self.driven_bones = self._driven_bones()

    def _validate(self) -> None:
        required = [
            "root", "pelvis", "head", "jaw", "chest",
            "thigh_l", "shin_l", "ankle_l", "foot_l",
            "thigh_r", "shin_r", "ankle_r", "foot_r",
            "arm_l", "forearm_l", "hand_l", "arm_r", "forearm_r", "hand_r",
        ]
        required += [f"spine_{index:02d}" for index in range(1, 6)]
        required += [f"neck_{index:02d}" for index in range(1, 6)]
        required += [f"tail_{index:02d}" for index in range(1, 10)]
        for side in ("l", "r"):
            required += [f"toe_{side}", f"toe_2_{side}", f"toe_3_{side}"]
        self.semantics.require(*required)
        _, missing = self.semantics.existing_bones(self.asset)
        if missing:
            raise ValueError(f"Mapped bones are missing from GLB: {missing}")
        if self.profile.export_sample_hz <= 0 or self.profile.internal_sample_hz <= 0:
            raise ValueError("Sample rates must be positive")
        if self.profile.internal_sample_hz % self.profile.export_sample_hz != 0:
            raise ValueError("internal_sample_hz must be an integer multiple of export_sample_hz")
        if not (0.5 < self.profile.stance_fraction < 0.85):
            raise ValueError("Biped stance_fraction should be between 0.5 and 0.85")
        if self.profile.supercycle_count < 1:
            raise ValueError("supercycle_count must be >= 1")

    def _driven_bones(self) -> list[str]:
        names = {self.pelvis, self.head, self.jaw_root, *self.spine, *self.neck, *self.tail}
        for side in ("l", "r"):
            names.update(self.legs[side].values())
            names.update(self.arms[side])
            for chain in self.toe_chains[side]:
                names.update(chain)
        return sorted(names, key=lambda name: self.asset.name_to_node[name])

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "profile": asdict(self.profile),
            "hip_height_m": self.hip_height,
            "profile_scale": self.scale,
            "stride_per_cycle_m": self.stride,
            "speed_mps": self.speed,
            "cycle_duration_seconds": self.cycle_duration,
            "supercycle_duration_seconds": self.duration,
            "driven_bone_count": len(self.driven_bones),
            "jaw_chain": self.jaw_chain,
            "toe_chains": self.toe_chains,
        }

    def _cycle_variation(self, global_phase: float) -> float:
        # Period is exactly two gait cycles; value and derivatives match at the boundary.
        return 1.0 + self.profile.asymmetry_fraction * math.sin(math.pi * global_phase)

    def foot_plan(self, side: str, global_phase: float) -> FootPlan:
        offset = 0.0 if side == "l" else 0.5
        relative = global_phase - offset
        contact_index = math.floor(relative + 1e-10)
        phase = relative - contact_index
        if phase >= 1.0 - 1e-10:
            contact_index += 1
            phase = 0.0
        contact_phase = contact_index + offset
        contact = self.foot_rest[side].copy()
        contact += self.basis.forward * (self.stride * contact_phase + self.contact_lead - float(np.dot(self.foot_rest[side] - self.foot_mid, self.basis.forward)))

        stance = phase < self.profile.stance_fraction
        swing_u = 0.0
        target = contact.copy()
        if stance:
            ramp = self.profile.load_ramp_fraction
            load_in = minimum_jerk(phase / ramp) if phase < ramp else 1.0
            remaining = self.profile.stance_fraction - phase
            load_out = minimum_jerk(remaining / ramp) if remaining < ramp else 1.0
            load = min(load_in, load_out)
        else:
            load = 0.0
            swing_u = (phase - self.profile.stance_fraction) / (1.0 - self.profile.stance_fraction)
            target += self.basis.forward * (self.stride * minimum_jerk(swing_u))
            target += self.basis.up * (self.swing_lift * smooth_bump(swing_u))
            outward_sign = -1.0 if side == "l" else 1.0
            target += self.basis.lateral * (outward_sign * self.swing_outward * smooth_bump(swing_u))

        # Foot pitch: settle after contact, rise through toe-off, fold in swing, prepare contact.
        if stance:
            contact_mix = minimum_jerk(min(1.0, phase / 0.10))
            toe_start = max(0.0, (phase - (self.profile.stance_fraction - 0.19)) / 0.19)
            pitch_deg = self.profile.contact_foot_deg * (1.0 - contact_mix)
            pitch_deg -= self.profile.toe_off_foot_deg * minimum_jerk(toe_start)
            toe_deg = self.profile.toe_push_deg * minimum_jerk(toe_start)
        else:
            fold = smooth_bump(swing_u)
            prepare = minimum_jerk(max(0.0, (swing_u - 0.70) / 0.30))
            pitch_deg = self.profile.swing_ankle_deg * fold
            pitch_deg = pitch_deg * (1.0 - prepare) + self.profile.contact_foot_deg * prepare
            toe_deg = -0.16 * self.profile.toe_push_deg * fold
        return FootPlan(
            side=side,
            phase=phase,
            stance=stance,
            swing_u=swing_u,
            load=load,
            target_world=target,
            contact_world=contact,
            foot_pitch_radians=math.radians(pitch_deg),
            toe_radians=math.radians(toe_deg),
        )

    def body_plan(self, global_phase: float) -> BodyPlan:
        left = self.foot_plan("l", global_phase)
        right = self.foot_plan("r", global_phase)
        total_load = max(left.load + right.load, 1e-6)
        support = (left.target_world * left.load + right.target_world * right.load) / total_load
        support_lateral = float(np.dot(support - self.foot_mid, self.basis.lateral))
        normalized = support_lateral / max(self.foot_span * 0.5, 1e-6)
        normalized = float(np.clip(normalized, -1.0, 1.0))

        # Down at contact/double support, up at passing position; add a soft post-contact compression.
        vertical_wave = -math.cos(4.0 * math.pi * global_phase)
        contact_drop = (
            cyclic_gaussian(global_phase, 0.055, 0.055, 0.5)
        )
        vertical = self.pelvis_bob * vertical_wave - self.pelvis_loading_drop * contact_drop
        forward_sway = self.pelvis_forward_sway * math.sin(4.0 * math.pi * global_phase)
        lateral_shift = self.profile.pelvis_support_shift_gain * support_lateral
        translation = (
            self.basis.lateral * lateral_shift
            + self.basis.up * vertical
            + self.basis.forward * forward_sway
        )

        variation = self._cycle_variation(global_phase)
        pelvis_yaw = math.radians(self.profile.pelvis_yaw_deg) * math.sin(2.0 * math.pi * global_phase) * variation
        pelvis_roll = math.radians(self.profile.pelvis_roll_deg) * normalized
        pelvis_pitch = math.radians(self.profile.pelvis_pitch_deg) * math.cos(4.0 * math.pi * global_phase)
        return BodyPlan(
            root_progress=self.stride * global_phase,
            pelvis_translation_world=translation,
            pelvis_yaw=pelvis_yaw,
            pelvis_roll=pelvis_roll,
            pelvis_pitch=pelvis_pitch,
            support_lateral_normalized=normalized,
            vertical_signal=vertical,
            left=left,
            right=right,
        )

    def _tail_dynamics(self, global_phases: np.ndarray, body_plans: list[BodyPlan]) -> tuple[np.ndarray, np.ndarray]:
        """Run a spring-damper chain to periodic steady state at the internal rate."""
        count = len(self.tail)
        samples_per_period = len(global_phases) - 1
        dt = 1.0 / self.profile.internal_sample_hz
        yaw_drive = np.array(
            [
                -self.profile.tail_root_yaw_gain * plan.pelvis_yaw
                - math.radians(self.profile.tail_com_gain * 3.0) * plan.support_lateral_normalized
                for plan in body_plans[:-1]
            ],
            dtype=np.float64,
        )
        if samples_per_period > 2:
            velocity = np.gradient(yaw_drive, dt, edge_order=2)
            yaw_drive -= self.profile.tail_velocity_gain * velocity * 0.12
        pitch_drive = np.array(
            [
                -self.profile.tail_pitch_gain * plan.pelvis_pitch
                - plan.vertical_signal / max(self.hip_height, 1e-6) * 0.18
                for plan in body_plans[:-1]
            ],
            dtype=np.float64,
        )

        stiffness = np.linspace(self.profile.tail_stiffness_root, self.profile.tail_stiffness_tip, count)
        damping = 2.0 * self.profile.tail_damping_ratio * np.sqrt(stiffness)

        def simulate(drive: np.ndarray) -> np.ndarray:
            angle = np.zeros(count, dtype=np.float64)
            angular_velocity = np.zeros(count, dtype=np.float64)
            capture = np.zeros((samples_per_period, count), dtype=np.float64)
            total_periods = self.profile.tail_warmup_supercycles + 1
            for step in range(total_periods * samples_per_period):
                source = drive[step % samples_per_period]
                for index in range(count):
                    attenuation = math.exp(-0.13 * index)
                    target = source * attenuation
                    if index > 0:
                        target += angle[index - 1] * 0.42
                    acceleration = stiffness[index] * (target - angle[index]) - damping[index] * angular_velocity[index]
                    if index > 0:
                        acceleration += self.profile.tail_coupling * (angle[index - 1] - angle[index])
                    if index + 1 < count:
                        acceleration += self.profile.tail_coupling * 0.22 * (angle[index + 1] - angle[index])
                    angular_velocity[index] += acceleration * dt
                    angle[index] += angular_velocity[index] * dt
                if step >= (total_periods - 1) * samples_per_period:
                    capture[step - (total_periods - 1) * samples_per_period] = angle
            # Per-bone limits keep cumulative tail rotation muscular rather than serpentine.
            limits = np.radians(np.linspace(3.2, 1.0, count))
            capture = np.clip(capture, -limits, limits)
            return np.vstack([capture, capture[0]])

        return simulate(yaw_drive), simulate(pitch_drive)

    def _apply_initial_leg_pose(self, pose: Pose, side: str, foot: FootPlan, global_phase: float) -> None:
        phase = foot.phase
        variation = self._cycle_variation(global_phase)
        swing_gate = 0.0 if foot.stance else smooth_bump(foot.swing_u) ** 0.65
        hip_angle = math.radians(self.profile.hip_swing_deg) * math.cos(2.0 * math.pi * phase) * variation
        knee_deg = self.profile.stance_knee_deg + (self.profile.swing_knee_deg - self.profile.stance_knee_deg) * swing_gate
        knee_deg += 4.0 * cyclic_gaussian(phase, self.profile.stance_fraction + 0.12, 0.08)
        ankle_deg = -0.30 * math.degrees(hip_angle) + self.profile.swing_ankle_deg * swing_gate

        leg = self.legs[side]
        pose.rotate_world_rest_axis(leg["thigh"], -self.basis.lateral, hip_angle)
        pose.rotate_world_rest_axis(leg["shin"], self.basis.lateral, math.radians(knee_deg))
        pose.rotate_world_rest_axis(leg["ankle"], -self.basis.lateral, math.radians(ankle_deg))

    @staticmethod
    def _fabrik_positions(points: np.ndarray, target: np.ndarray, iterations: int = 7) -> np.ndarray:
        """Solve a short joint chain in position space while preserving segment lengths."""
        solved = np.asarray(points, dtype=np.float64).copy()
        target = np.asarray(target, dtype=np.float64)
        root = solved[0].copy()
        lengths = np.linalg.norm(np.diff(solved, axis=0), axis=1)
        total = float(lengths.sum())
        if np.linalg.norm(target - root) >= total - 1e-9:
            direction = target - root
            direction /= max(np.linalg.norm(direction), 1e-12)
            solved[0] = root
            for index, length in enumerate(lengths):
                solved[index + 1] = solved[index] + direction * length
            return solved
        for _ in range(iterations):
            solved[-1] = target
            for index in range(len(solved) - 2, -1, -1):
                direction = solved[index] - solved[index + 1]
                direction /= max(np.linalg.norm(direction), 1e-12)
                solved[index] = solved[index + 1] + direction * lengths[index]
            solved[0] = root
            for index in range(len(solved) - 1):
                direction = solved[index + 1] - solved[index]
                direction /= max(np.linalg.norm(direction), 1e-12)
                solved[index + 1] = solved[index] + direction * lengths[index]
            if np.linalg.norm(solved[-1] - target) < 1e-5:
                break
        return solved

    def _solve_leg(self, pose: Pose, side: str, foot: FootPlan) -> tuple[float, float]:
        leg = self.legs[side]
        chain = [leg["thigh"], leg["shin"], leg["ankle"], leg["foot"]]

        def align_to(target: np.ndarray) -> float:
            initial = np.stack([pose.world_position(name) for name in chain])
            solved = self._fabrik_positions(initial, target, iterations=8)
            pose.align_child_direction_world(
                leg["thigh"], leg["shin"], solved[1], fraction=1.0, max_angle_radians=math.pi
            )
            pose.align_child_direction_world(
                leg["shin"], leg["ankle"], solved[2], fraction=1.0, max_angle_radians=math.pi
            )
            pose.align_child_direction_world(
                leg["ankle"], leg["foot"], solved[3], fraction=1.0, max_angle_radians=math.pi
            )
            return float(np.linalg.norm(pose.world_position(leg["foot"]) - target))

        target = foot.target_world.copy()
        error = align_to(target)
        foot_index = self.asset.name_to_node[leg["foot"]]
        desired_foot_world = (
            Rotation.from_rotvec(self.basis.lateral * foot.foot_pitch_radians)
            * self.asset.rest_world_rotation[foot_index]
        )
        pose.set_world_rotation(leg["foot"], desired_foot_world)
        toe_weights = (0.52, 0.30, 0.18)
        for chain_index, toe_chain in enumerate(self.toe_chains[side]):
            outer_scale = (0.92, 1.0, 0.95)[chain_index]
            distribute_chain_rotation(
                pose,
                toe_chain,
                self.basis.lateral,
                foot.toe_radians * outer_scale,
                toe_weights[: len(toe_chain)],
            )

        # Preserve the rest contact height of the lowest toe during loaded stance.
        # This lets the foot root rise naturally through toe-off without driving the
        # toe geometry through the ground plane.
        ground_correction = 0.0
        if foot.stance:
            current_min = min(pose.world_position(toe_chain[-1])[1] for toe_chain in self.toe_chains[side])
            ground_correction = float(np.clip(self.toe_tip_rest_y[side] - current_min, -0.025, self.hip_height * 0.13))
            if abs(ground_correction) > 1e-5:
                target = target + self.basis.up * ground_correction
                error = align_to(target)
        return error, ground_correction

    def _pose_for_sample(
        self,
        global_phase: float,
        body: BodyPlan,
        tail_yaw: np.ndarray,
        tail_pitch: np.ndarray,
        include_root_motion: bool,
    ) -> tuple[Pose, dict[str, float]]:
        pose = Pose(self.asset)
        if include_root_motion:
            pose.add_world_translation_rest(self.root, self.basis.forward * body.root_progress)
        pose.add_world_translation_rest(self.pelvis, body.pelvis_translation_world)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.up, body.pelvis_yaw)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.forward, body.pelvis_roll)
        pose.rotate_world_rest_axis(
            self.pelvis,
            self.basis.lateral,
            body.pelvis_pitch + math.radians(self.profile.body_lean_deg) * 0.20,
        )

        breathing = math.sin(math.pi * global_phase)  # one breath over the two-cycle supercycle
        distribute_chain_rotation(
            pose, self.spine, self.basis.up,
            -body.pelvis_yaw * self.profile.spine_counter_gain,
            [0.08, 0.11, 0.14, 0.18, 0.22, 0.27],
        )
        distribute_chain_rotation(
            pose, self.spine, self.basis.forward,
            -body.pelvis_roll * 0.58,
            [0.08, 0.11, 0.14, 0.18, 0.22, 0.27],
        )
        distribute_chain_rotation(
            pose, self.spine, self.basis.lateral,
            math.radians(self.profile.body_lean_deg) - body.pelvis_pitch * 0.38 + math.radians(self.profile.breathing_chest_deg) * breathing,
            [0.07, 0.10, 0.13, 0.17, 0.22, 0.31],
        )

        distribute_chain_rotation(
            pose, self.neck, self.basis.up,
            body.pelvis_yaw * self.profile.neck_stabilize_gain,
            [0.11, 0.15, 0.19, 0.24, 0.31],
        )
        distribute_chain_rotation(
            pose, self.neck, self.basis.forward,
            body.pelvis_roll * self.profile.neck_stabilize_gain,
            [0.11, 0.15, 0.19, 0.24, 0.31],
        )
        distribute_chain_rotation(
            pose, self.neck, self.basis.lateral,
            -math.radians(self.profile.body_lean_deg) * 0.47 + math.radians(self.profile.breathing_neck_deg) * breathing,
            [0.11, 0.15, 0.19, 0.24, 0.31],
        )
        head_micro = math.radians(self.profile.head_micro_yaw_deg) * math.sin(math.pi * global_phase + 0.45)
        pose.rotate_world_rest_axis(self.head, self.basis.up, -body.pelvis_yaw * self.profile.head_stabilize_gain + head_micro)
        pose.rotate_world_rest_axis(self.head, self.basis.forward, -body.pelvis_roll * self.profile.head_stabilize_gain)
        pose.rotate_world_rest_axis(self.head, self.basis.lateral, -body.pelvis_pitch * 0.52)

        # Bind pose is mouth-open for modeling. The neutral animation layer closes it,
        # then adds a sub-degree breathing gape on an independent supercycle clock.
        jaw_angle = -math.radians(self.profile.neutral_jaw_close_deg)
        jaw_angle += math.radians(self.profile.jaw_breath_deg) * (0.5 - 0.5 * math.cos(math.pi * global_phase))
        pose.rotate_world_rest_axis(self.jaw_root, self.basis.lateral, jaw_angle)

        for index, bone in enumerate(self.tail):
            pose.rotate_world_rest_axis(bone, self.basis.up, float(tail_yaw[index]))
            pose.rotate_world_rest_axis(bone, self.basis.lateral, float(tail_pitch[index]))

        # Forelimbs lag the torso instead of mirroring the hindlimbs mechanically.
        arm_signal = math.sin(2.0 * math.pi * global_phase + 0.35)
        arm_angle = math.radians(self.profile.arm_inertia_deg) * arm_signal
        for side, sign in (("l", -1.0), ("r", 1.0)):
            arm, forearm, hand = self.arms[side]
            pose.rotate_world_rest_axis(arm, -self.basis.lateral, sign * arm_angle)
            pose.rotate_world_rest_axis(forearm, self.basis.lateral, abs(arm_angle) * 0.34)
            pose.rotate_world_rest_axis(hand, self.basis.up, -sign * arm_angle * 0.18)

        self._apply_initial_leg_pose(pose, "l", body.left, global_phase)
        self._apply_initial_leg_pose(pose, "r", body.right, global_phase)
        left_error, left_ground = self._solve_leg(pose, "l", body.left)
        right_error, right_ground = self._solve_leg(pose, "r", body.right)
        return pose, {
            "left_ik_error": left_error,
            "right_ik_error": right_error,
            "left_ground_correction": left_ground,
            "right_ground_correction": right_ground,
        }

    def generate(self, keep_world_matrices: bool = False) -> GeneratedMotion:
        internal_count = int(round(self.duration * self.profile.internal_sample_hz)) + 1
        times = np.linspace(0.0, self.duration, internal_count, dtype=np.float64)
        phases = times / self.cycle_duration
        body_plans = [self.body_plan(float(phase)) for phase in phases]
        tail_yaw, tail_pitch = self._tail_dynamics(phases, body_plans)

        rotations: dict[str, list[np.ndarray]] = {name: [] for name in self.driven_bones}
        root_translation: list[np.ndarray] = []
        errors_left: list[float] = []
        errors_right: list[float] = []
        ground_corrections = {"l": [], "r": []}
        toe_min_y = {"l": [], "r": []}
        foot_positions = {"l": [], "r": []}
        worlds: list[list[np.ndarray]] | None = [] if keep_world_matrices else None

        for index, (phase, body) in enumerate(zip(phases, body_plans)):
            pose, errors = self._pose_for_sample(
                float(phase), body, tail_yaw[index], tail_pitch[index], include_root_motion=True
            )
            for name in self.driven_bones:
                rotations[name].append(pose.quaternion(name))
            root_translation.append(pose.translation[self.asset.name_to_node[self.root]].copy())
            errors_left.append(errors["left_ik_error"])
            errors_right.append(errors["right_ik_error"])
            ground_corrections["l"].append(errors["left_ground_correction"])
            ground_corrections["r"].append(errors["right_ground_correction"])
            for side in ("l", "r"):
                foot_positions[side].append(pose.world_position(self.legs[side]["foot"]))
                toe_min_y[side].append(min(pose.world_position(chain[-1])[1] for chain in self.toe_chains[side]))
            if worlds is not None:
                worlds.append([matrix.copy() for matrix in pose.world_matrices])

        rotation_arrays = {
            name: quaternion_continuity(np.asarray(values, dtype=np.float64))
            for name, values in rotations.items()
        }
        # Enforce exact periodic rotation closure. Root translation intentionally accumulates.
        for values in rotation_arrays.values():
            values[-1] = values[0]
        root_array = np.asarray(root_translation, dtype=np.float64)

        decimation = self.profile.internal_sample_hz // self.profile.export_sample_hz
        export_indices = np.arange(0, internal_count, decimation, dtype=np.int64)
        if export_indices[-1] != internal_count - 1:
            export_indices = np.append(export_indices, internal_count - 1)
        export_times = times[export_indices]
        export_rotations = {name: values[export_indices] for name, values in rotation_arrays.items()}
        export_root = root_array[export_indices]

        foot_arrays = {side: np.asarray(values) for side, values in foot_positions.items()}
        contact_drift: dict[str, float] = {}
        contact_error: dict[str, float] = {}
        toe_ground_error: dict[str, float] = {}
        for side in ("l", "r"):
            loads = np.array([plan.left.load if side == "l" else plan.right.load for plan in body_plans])
            loaded_mask = loads > 0.18
            targets = np.array([plan.left.target_world if side == "l" else plan.right.target_world for plan in body_plans])
            delta = foot_arrays[side] - targets
            # Foot-root vertical lift is intentional during roll/toe-off; contact lock is horizontal.
            horizontal = delta - np.outer(delta @ self.basis.up, self.basis.up)
            errors = np.linalg.norm(horizontal, axis=1)
            contact_error[side] = float(np.max(errors[loaded_mask]))
            contact_drift[side] = float(np.percentile(errors[loaded_mask], 95))
            toe_values = np.asarray(toe_min_y[side])
            toe_ground_error[side] = float(np.max(np.abs(toe_values[loaded_mask] - self.toe_tip_rest_y[side])))

        endpoint_rotation = max(
            float(np.max(np.abs(values[-1] - values[0]))) for values in rotation_arrays.values()
        )
        diagnostics = {
            **self.metadata,
            "internal_sample_count": int(internal_count),
            "export_sample_count": int(len(export_indices)),
            "max_ik_error_m": {
                "left": float(max(errors_left)),
                "right": float(max(errors_right)),
            },
            "p95_contact_target_error_m": contact_drift,
            "max_contact_target_error_m": contact_error,
            "max_loaded_toe_ground_error_m": toe_ground_error,
            "max_ground_correction_m": {side: float(max(map(abs, ground_corrections[side]))) for side in ("l", "r")},
            "normalized_contact_error": {
                side: contact_error[side] / self.hip_height for side in ("l", "r")
            },
            "rotation_endpoint_max_abs_diff": endpoint_rotation,
            "root_motion_distance_m": float(np.dot(root_array[-1] - root_array[0], self.basis.forward)),
            "tail_endpoint_yaw_max_abs_diff": float(np.max(np.abs(tail_yaw[-1] - tail_yaw[0]))),
            "tail_endpoint_pitch_max_abs_diff": float(np.max(np.abs(tail_pitch[-1] - tail_pitch[0]))),
            "stance_fraction": self.profile.stance_fraction,
        }
        return GeneratedMotion(
            times_internal=times,
            times_export=export_times,
            rotations_internal=rotation_arrays,
            rotations_export=export_rotations,
            root_translation_internal=root_array,
            root_translation_export=export_root,
            diagnostics=diagnostics,
            frame_plans=body_plans,
            world_matrices_internal=worlds,
        )

    def animation_specs(self, motion: GeneratedMotion) -> list[dict[str, Any]]:
        root_rest = self.asset.rest_translation[self.asset.name_to_node[self.root]]
        in_place_translation = np.repeat(root_rest[None, :], len(motion.times_export), axis=0)
        common_extras = {
            "generator": "Eonwild procedural animation skill v2",
            "profile": self.profile.name,
            "cycleHz": self.profile.cycle_hz,
            "supercycles": self.profile.supercycle_count,
            "sampleHz": self.profile.export_sample_hz,
            "internalSampleHz": self.profile.internal_sample_hz,
            "contactAware": True,
            "neutralJaw": True,
            "tailDynamics": "periodic spring-damper chain",
        }
        return [
            {
                "name": "PROC_WALK_LARGE_V2_INPLACE",
                "times": motion.times_export.astype(np.float32),
                "rotations": {name: values.astype(np.float32) for name, values in motion.rotations_export.items()},
                "translations": {self.root: in_place_translation.astype(np.float32)},
                "interpolation": "LINEAR",
                "extras": {**common_extras, "rootMotion": False, "recommendedRuntimeSpeedMps": self.speed},
            },
            {
                "name": "PROC_WALK_LARGE_V2_ROOTMOTION",
                "times": motion.times_export.astype(np.float32),
                "rotations": {name: values.astype(np.float32) for name, values in motion.rotations_export.items()},
                "translations": {self.root: motion.root_translation_export.astype(np.float32)},
                "interpolation": "LINEAR",
                "extras": {**common_extras, "rootMotion": True, "rootMotionDistanceM": self.stride * self.profile.supercycle_count},
            },
        ]

    def save_report(self, motion: GeneratedMotion, destination: str | Path) -> Path:
        path = Path(destination)
        path.write_text(json.dumps(motion.diagnostics, indent=2), encoding="utf-8")
        return path
