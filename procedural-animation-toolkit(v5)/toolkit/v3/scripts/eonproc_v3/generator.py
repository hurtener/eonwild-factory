"""Contact-aware biped animation kernel used by Eonwild procedural animation v3.

The kernel keeps the original deformation skeleton and layers:
  * reference-informed phase/event foot planning,
  * C2 swing trajectories,
  * sagittal hinge IK with explicit knee/ankle bend-side and angle limits,
  * support-weight pelvis translation and relaxed horizon-facing posture,
  * softer periodically settled spring-damper tail response with distal lag,
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
from .profile import BipedV3Profile
from .rig import AnatomicalBasis, Pose, SemanticMap, distribute_chain_rotation


def _wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def _signed_turn(vector_a: np.ndarray, vector_b: np.ndarray, axis: np.ndarray) -> float:
    a = np.asarray(vector_a, dtype=np.float64).copy()
    b = np.asarray(vector_b, dtype=np.float64).copy()
    a /= max(np.linalg.norm(a), 1e-12)
    b /= max(np.linalg.norm(b), 1e-12)
    n = np.asarray(axis, dtype=np.float64)
    n /= max(np.linalg.norm(n), 1e-12)
    return math.atan2(float(np.dot(n, np.cross(a, b))), float(np.clip(np.dot(a, b), -1.0, 1.0)))


@dataclass(frozen=True)
class LegSolveResult:
    angles: np.ndarray
    target_error: float
    lateral_error: float
    solver_cost: float
    solver_success: bool
    knee_signed_degrees: float
    ankle_signed_degrees: float


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


class AnatomicallyConstrainedBipedGenerator:
    def __init__(
        self,
        asset: GlbAsset,
        semantics: SemanticMap,
        profile: BipedV3Profile,
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
        self.leg_geometry: dict[str, dict[str, Any]] = {}
        for side in ("l", "r"):
            leg = self.legs[side]
            points = [
                asset.rest_world[asset.name_to_node[leg[name]]][:3, 3].copy()
                for name in ("thigh", "shin", "ankle", "foot")
            ]
            vectors = np.diff(np.stack(points), axis=0)
            theta = [
                math.atan2(float(np.dot(vector, self.basis.up)), float(np.dot(vector, self.basis.forward)))
                for vector in vectors
            ]
            knee_turn_2d = _wrap_angle(theta[1] - theta[0])
            ankle_turn_2d = _wrap_angle(theta[2] - theta[1])
            knee_signed = _signed_turn(vectors[0], vectors[1], self.basis.lateral)
            ankle_signed = _signed_turn(vectors[1], vectors[2], self.basis.lateral)
            self.leg_geometry[side] = {
                "lengths": np.linalg.norm(vectors, axis=1),
                "knee_turn_2d_sign": -1.0 if knee_turn_2d < 0.0 else 1.0,
                "ankle_turn_2d_sign": -1.0 if ankle_turn_2d < 0.0 else 1.0,
                "knee_signed_sign": -1.0 if knee_signed < 0.0 else 1.0,
                "ankle_signed_sign": -1.0 if ankle_signed < 0.0 else 1.0,
                "rest_knee_flex_deg": abs(math.degrees(knee_signed)),
                "rest_ankle_flex_deg": abs(math.degrees(ankle_signed)),
            }
        sag_weights = np.array([0.025, 0.040, 0.060, 0.085, 0.110, 0.135, 0.160, 0.185, 0.200], dtype=np.float64)
        sag_weights /= float(sag_weights.sum())
        self.tail_neutral_sag = np.radians(profile.tail_neutral_sag_deg) * sag_weights
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
            "leg_geometry": {
                side: {
                    key: (value.tolist() if isinstance(value, np.ndarray) else value)
                    for key, value in geometry.items()
                }
                for side, geometry in self.leg_geometry.items()
            },
            "reference_motion": {
                "source": "Tarbosaurus#walk_side_v02.mp4",
                "steady_walk_cycle_estimate_seconds": 2.0,
                "posture": "relaxed, horizon-facing, high stance duty factor",
            },
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
        contact += self.basis.forward * (
            self.stride * contact_phase
            + self.contact_lead
            - float(np.dot(self.foot_rest[side] - self.foot_mid, self.basis.forward))
        )

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

        # Every boundary uses minimum-jerk or the C2 bump. The foot never snaps
        # from toe-off to retraction or from pre-contact extension to landing.
        if stance:
            contact_mix = minimum_jerk(min(1.0, phase / max(self.profile.load_ramp_fraction, 1e-6)))
            window = self.profile.toe_off_window_fraction
            toe_start = max(0.0, (phase - (self.profile.stance_fraction - window)) / window)
            toe_mix = minimum_jerk(toe_start)
            pitch_deg = self.profile.contact_foot_deg * (1.0 - contact_mix)
            pitch_deg -= self.profile.toe_off_foot_deg * toe_mix
            toe_deg = self.profile.toe_push_deg * toe_mix
        else:
            fold = smooth_bump(swing_u)
            window = self.profile.precontact_window_fraction
            prepare = minimum_jerk(max(0.0, (swing_u - (1.0 - window)) / window))
            # Preserve C2 orientation continuity across toe-off. At swing_u=0 the
            # stance controller ended at a raised heel and loaded toes; the swing
            # controller must begin from that exact state rather than snapping to
            # a flat foot. The release envelope fades it out before mid-swing.
            release_window = max(0.12, min(0.30, self.profile.toe_off_window_fraction))
            release = 1.0 - minimum_jerk(min(1.0, swing_u / release_window))
            pitch_deg = -self.profile.toe_off_foot_deg * release
            pitch_deg += self.profile.swing_ankle_deg * fold * (1.0 - release)
            pitch_deg = pitch_deg * (1.0 - prepare) + self.profile.contact_foot_deg * prepare
            toe_deg = self.profile.toe_push_deg * release
            toe_deg += -0.14 * self.profile.toe_push_deg * fold * (1.0 - release)
            toe_deg *= 1.0 - prepare
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
        """Periodic spring-damper tail with lower distal stiffness and phase lag."""
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
                - plan.vertical_signal / max(self.hip_height, 1e-6) * 0.15
                for plan in body_plans[:-1]
            ],
            dtype=np.float64,
        )

        stiffness = np.linspace(self.profile.tail_stiffness_root, self.profile.tail_stiffness_tip, count)
        damping = 2.0 * self.profile.tail_damping_ratio * np.sqrt(stiffness)
        limits = np.radians(
            np.linspace(self.profile.tail_dynamic_limit_root_deg, self.profile.tail_dynamic_limit_tip_deg, count)
        )
        lag_samples = np.rint(
            np.arange(count) * self.profile.tail_phase_lag_seconds_per_bone * self.profile.internal_sample_hz
        ).astype(int)

        def simulate(drive: np.ndarray) -> np.ndarray:
            angle = np.zeros(count, dtype=np.float64)
            angular_velocity = np.zeros(count, dtype=np.float64)
            capture = np.zeros((samples_per_period, count), dtype=np.float64)
            total_periods = self.profile.tail_warmup_supercycles + 1
            for step in range(total_periods * samples_per_period):
                acceleration = np.zeros(count, dtype=np.float64)
                for index in range(count):
                    delayed = drive[(step - lag_samples[index]) % samples_per_period]
                    attenuation = math.exp(-0.085 * index)
                    target = delayed * attenuation
                    if index > 0:
                        target += angle[index - 1] * self.profile.tail_parent_follow
                    acceleration[index] = (
                        stiffness[index] * (target - angle[index])
                        - damping[index] * angular_velocity[index]
                    )
                    if index > 0:
                        acceleration[index] += self.profile.tail_coupling * (angle[index - 1] - angle[index])
                    if index + 1 < count:
                        acceleration[index] += self.profile.tail_coupling * 0.15 * (angle[index + 1] - angle[index])
                angular_velocity += acceleration * dt
                angle += angular_velocity * dt
                angle = np.clip(angle, -limits, limits)
                if step >= (total_periods - 1) * samples_per_period:
                    capture[step - (total_periods - 1) * samples_per_period] = angle
            return np.vstack([capture, capture[0]])

        return simulate(yaw_drive), simulate(pitch_drive)

    def _leg_preferences(self, foot: FootPlan, global_phase: float) -> tuple[float, float, float]:
        variation = self._cycle_variation(global_phase)
        hip_delta = math.radians(self.profile.hip_swing_deg) * math.cos(2.0 * math.pi * foot.phase) * variation

        knee_contact = self.profile.knee_stance_flex_deg
        ankle_contact = self.profile.ankle_stance_flex_deg
        knee_release = self.profile.knee_stance_flex_deg + 5.0
        ankle_release = self.profile.ankle_stance_flex_deg - 7.0

        if foot.stance:
            stance_u = foot.phase / max(self.profile.stance_fraction, 1e-6)
            # A C2 loading pulse starts and ends at the contact preference. It
            # replaces the former cyclic Gaussian whose non-zero boundary value
            # introduced a small preference discontinuity at contact.
            load_window = max(0.12, min(0.34, self.profile.load_ramp_fraction * 2.0))
            load_u = min(1.0, stance_u / load_window)
            load_pulse = smooth_bump(load_u)
            extension = smooth_bump(stance_u)
            toe_start = max(0.0, (stance_u - 0.72) / 0.28)
            toe_mix = minimum_jerk(toe_start)
            base_knee = (
                knee_contact
                + self.profile.knee_loading_flex_deg * load_pulse
                - 4.0 * extension
            )
            knee = base_knee * (1.0 - toe_mix) + knee_release * toe_mix
            ankle = ankle_contact * (1.0 - toe_mix) + ankle_release * toe_mix
        else:
            bump = smooth_bump(foot.swing_u) ** 0.72
            prepare = minimum_jerk(
                max(0.0, (foot.swing_u - (1.0 - self.profile.precontact_window_fraction))
                    / self.profile.precontact_window_fraction)
            )
            # Swing begins from the exact toe-off preference and ends at the
            # exact next-contact preference. This removes the old 5–7 degree
            # discontinuity at the stance/swing boundary.
            knee = knee_release + (self.profile.knee_swing_flex_deg - knee_release) * bump
            ankle = ankle_release + (self.profile.ankle_swing_flex_deg - ankle_release) * bump
            knee = knee * (1.0 - prepare) + knee_contact * prepare
            ankle = ankle * (1.0 - prepare) + ankle_contact * prepare
        return hip_delta, math.radians(knee), math.radians(ankle)

    def _solve_sagittal_angles(
        self,
        pose: Pose,
        side: str,
        foot: FootPlan,
        target_world: np.ndarray,
        global_phase: float,
        seed: np.ndarray | None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float, bool]:
        leg = self.legs[side]
        geometry = self.leg_geometry[side]
        hip = pose.world_position(leg["thigh"])
        positions = [pose.world_position(leg[name]) for name in ("thigh", "shin", "ankle", "foot")]
        vectors = np.diff(np.stack(positions), axis=0)
        lengths = geometry["lengths"]
        theta_base = math.atan2(
            float(np.dot(vectors[0], self.basis.up)),
            float(np.dot(vectors[0], self.basis.forward)),
        )
        target_delta = np.asarray(target_world, dtype=np.float64) - hip
        target_2d = np.array(
            [float(np.dot(target_delta, self.basis.forward)), float(np.dot(target_delta, self.basis.up))],
            dtype=np.float64,
        )
        hip_pref_delta, knee_pref, ankle_pref = self._leg_preferences(foot, global_phase)
        theta_pref = theta_base + hip_pref_delta
        knee_sign = geometry["knee_turn_2d_sign"]
        ankle_sign = geometry["ankle_turn_2d_sign"]

        lower = np.array(
            [
                theta_base - math.radians(self.profile.hip_extension_limit_deg),
                math.radians(self.profile.knee_min_flex_deg),
                math.radians(self.profile.ankle_min_flex_deg),
            ],
            dtype=np.float64,
        )
        upper = np.array(
            [
                theta_base + math.radians(self.profile.hip_flexion_limit_deg),
                math.radians(self.profile.knee_max_flex_deg),
                math.radians(self.profile.ankle_max_flex_deg),
            ],
            dtype=np.float64,
        )
        preferred = np.array([theta_pref, knee_pref, ankle_pref], dtype=np.float64)
        initial = preferred.copy() if seed is None else np.asarray(seed, dtype=np.float64).copy()
        initial = np.clip(initial, lower + 1e-8, upper - 1e-8)
        position_scale = max(self.hip_height * self.profile.leg_position_scale_hip_fraction, 1e-5)

        def forward_kinematics(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
            theta1, knee_mag, ankle_mag = values
            theta2 = theta1 + knee_sign * knee_mag
            theta3 = theta2 + ankle_sign * ankle_mag
            direction1 = np.array([math.cos(theta1), math.sin(theta1)])
            direction2 = np.array([math.cos(theta2), math.sin(theta2)])
            direction3 = np.array([math.cos(theta3), math.sin(theta3)])
            normal1 = np.array([-math.sin(theta1), math.cos(theta1)])
            normal2 = np.array([-math.sin(theta2), math.cos(theta2)])
            normal3 = np.array([-math.sin(theta3), math.cos(theta3)])
            knee_2d = lengths[0] * direction1
            ankle_2d = knee_2d + lengths[1] * direction2
            foot_2d = ankle_2d + lengths[2] * direction3
            jacobian = np.column_stack(
                [
                    lengths[0] * normal1 + lengths[1] * normal2 + lengths[2] * normal3,
                    knee_sign * (lengths[1] * normal2 + lengths[2] * normal3),
                    ankle_sign * lengths[2] * normal3,
                ]
            )
            return knee_2d, ankle_2d, foot_2d, jacobian

        if seed is None:
            # Start a newly encountered leg from the source rig's anatomical
            # rest flexion, not from a potentially straighter style preference.
            # This keeps the first constrained solve on the correct reachable
            # branch and avoids a transient failure at clip start.
            values = np.array(
                [
                    theta_pref,
                    math.radians(geometry["rest_knee_flex_deg"]),
                    math.radians(geometry["rest_ankle_flex_deg"]),
                ],
                dtype=np.float64,
            )
        else:
            values = np.asarray(seed, dtype=np.float64).copy()
        values = np.clip(values, lower + 1e-8, upper - 1e-8)
        preference_scales = np.radians(np.array([28.0, 34.0, 30.0], dtype=np.float64))
        preference_diag = np.diag(
            np.full(3, self.profile.leg_preference_weight, dtype=np.float64) / preference_scales
        )
        if seed is None:
            continuity_diag = np.zeros((3, 3), dtype=np.float64)
            previous = values.copy()
        else:
            previous = np.asarray(seed, dtype=np.float64)
            continuity_diag = np.diag(
                np.full(3, self.profile.leg_continuity_weight, dtype=np.float64) / preference_scales
            )
        success = False
        iterations = max(6, min(self.profile.leg_max_solver_evaluations, 24))
        max_step = math.radians(11.0)
        for _ in range(iterations):
            _, _, predicted, jacobian = forward_kinematics(values)
            error = target_2d - predicted
            normalized_jacobian = jacobian / position_scale
            normalized_error = error / position_scale
            system = (
                normalized_jacobian.T @ normalized_jacobian
                + preference_diag.T @ preference_diag
                + continuity_diag.T @ continuity_diag
                + np.eye(3, dtype=np.float64) * 1e-5
            )
            rhs = (
                normalized_jacobian.T @ normalized_error
                + preference_diag.T @ preference_diag @ (preferred - values)
                + continuity_diag.T @ continuity_diag @ (previous - values)
            )
            try:
                step = np.linalg.solve(system, rhs)
            except np.linalg.LinAlgError:
                step = np.linalg.lstsq(system, rhs, rcond=None)[0]
            step = np.clip(step, -max_step, max_step)
            candidate = np.clip(values + step, lower, upper)
            # Backtrack if the Cartesian target error worsens.
            current_error = float(np.linalg.norm(error))
            _, _, candidate_position, _ = forward_kinematics(candidate)
            candidate_error = float(np.linalg.norm(target_2d - candidate_position))
            if candidate_error > current_error + 1e-9:
                accepted = False
                for fraction in (0.5, 0.25, 0.125, 0.0625):
                    trial = np.clip(values + step * fraction, lower, upper)
                    _, _, trial_position, _ = forward_kinematics(trial)
                    if float(np.linalg.norm(target_2d - trial_position)) <= current_error:
                        candidate = trial
                        candidate_error = float(np.linalg.norm(target_2d - trial_position))
                        accepted = True
                        break
                if not accepted:
                    break
            values = candidate
            if candidate_error <= self.ik_tolerance and float(np.max(np.abs(step))) < math.radians(0.02):
                success = True
                break
        knee_2d, ankle_2d, foot_2d, _ = forward_kinematics(values)
        cartesian_error = float(np.linalg.norm(foot_2d - target_2d))
        success = success or cartesian_error <= max(self.ik_tolerance * 4.0, self.hip_height * 0.004)
        preference_error = (values - preferred) / preference_scales
        cost = 0.5 * (cartesian_error / position_scale) ** 2
        cost += 0.5 * self.profile.leg_preference_weight ** 2 * float(np.dot(preference_error, preference_error))

        def to_world(point: np.ndarray) -> np.ndarray:
            return hip + self.basis.forward * point[0] + self.basis.up * point[1]

        return (
            values,
            to_world(knee_2d),
            to_world(ankle_2d),
            to_world(foot_2d),
            cartesian_error,
            float(cost),
            bool(success),
        )

    def _solve_leg(
        self,
        pose: Pose,
        side: str,
        foot: FootPlan,
        global_phase: float,
        seed: np.ndarray | None,
    ) -> tuple[Pose, LegSolveResult, float]:
        leg = self.legs[side]
        base_pose = pose.copy()
        limit = math.radians(self.profile.hip_abduction_limit_deg)

        def solve_once(target_world: np.ndarray, initial: np.ndarray | None) -> tuple[Pose, LegSolveResult]:
            work = base_pose.copy()
            hip = work.world_position(leg["thigh"])
            current_foot = work.world_position(leg["foot"])
            lateral_error_before = float(np.dot(target_world - current_foot, self.basis.lateral))
            lever = current_foot - hip
            derivative = float(np.dot(np.cross(self.basis.forward, lever), self.basis.lateral))
            abduction = 0.0
            if abs(derivative) > 1e-7:
                abduction = float(np.clip(lateral_error_before / derivative, -limit, limit))
                work.rotate_world(leg["thigh"], self.basis.forward, abduction)

            values, knee_target, ankle_target, foot_target, target_error, cost, success = self._solve_sagittal_angles(
                work, side, foot, target_world, global_phase, initial
            )
            work.align_child_about_world_axis(
                leg["thigh"], leg["shin"], knee_target, self.basis.lateral,
                fraction=1.0, max_angle_radians=math.pi,
            )
            work.align_child_about_world_axis(
                leg["shin"], leg["ankle"], ankle_target, self.basis.lateral,
                fraction=1.0, max_angle_radians=math.pi,
            )
            work.align_child_about_world_axis(
                leg["ankle"], leg["foot"], foot_target, self.basis.lateral,
                fraction=1.0, max_angle_radians=math.pi,
            )

            foot_index = self.asset.name_to_node[leg["foot"]]
            desired_foot_world = (
                Rotation.from_rotvec(self.basis.lateral * foot.foot_pitch_radians)
                * self.asset.rest_world_rotation[foot_index]
            )
            work.set_world_rotation(leg["foot"], desired_foot_world)
            toe_weights = (0.52, 0.30, 0.18)
            for chain_index, toe_chain in enumerate(self.toe_chains[side]):
                outer_scale = (0.92, 1.0, 0.95)[chain_index]
                distribute_chain_rotation(
                    work, toe_chain, self.basis.lateral, foot.toe_radians * outer_scale,
                    toe_weights[: len(toe_chain)],
                )

            points = [work.world_position(leg[name]) for name in ("thigh", "shin", "ankle", "foot")]
            knee_signed = math.degrees(_signed_turn(points[1] - points[0], points[2] - points[1], self.basis.lateral))
            ankle_signed = math.degrees(_signed_turn(points[2] - points[1], points[3] - points[2], self.basis.lateral))
            lateral_error = float(np.dot(work.world_position(leg["foot"]) - target_world, self.basis.lateral))
            result = LegSolveResult(
                angles=values,
                target_error=float(np.linalg.norm(work.world_position(leg["foot"]) - target_world)),
                lateral_error=lateral_error,
                solver_cost=cost,
                solver_success=success,
                knee_signed_degrees=knee_signed,
                ankle_signed_degrees=ankle_signed,
            )
            return work, result

        target = foot.target_world.copy()
        solved_pose, result = solve_once(target, seed)
        ground_correction = 0.0
        if foot.stance:
            current_min = min(solved_pose.world_position(chain[-1])[1] for chain in self.toe_chains[side])
            ground_correction = float(
                np.clip(self.toe_tip_rest_y[side] - current_min, -0.015, 0.025)
                * foot.load
            )
            if abs(ground_correction) > 1e-5:
                solved_pose, result = solve_once(target + self.basis.up * ground_correction, result.angles)
        return solved_pose, result, ground_correction

    def _pose_for_sample(
        self,
        global_phase: float,
        body: BodyPlan,
        tail_yaw: np.ndarray,
        tail_pitch: np.ndarray,
        include_root_motion: bool,
        leg_seeds: dict[str, np.ndarray | None],
    ) -> tuple[Pose, dict[str, Any], dict[str, np.ndarray]]:
        pose = Pose(self.asset)
        if include_root_motion:
            pose.add_world_translation_rest(self.root, self.basis.forward * body.root_progress)
        pose.add_world_translation_rest(self.pelvis, body.pelvis_translation_world)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.up, body.pelvis_yaw)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.forward, body.pelvis_roll)
        pose.rotate_world_rest_axis(
            self.pelvis, self.basis.lateral,
            body.pelvis_pitch + math.radians(self.profile.pelvis_neutral_pitch_deg),
        )

        breathing = math.sin(math.pi * global_phase)
        distribute_chain_rotation(
            pose, self.spine, self.basis.up,
            -body.pelvis_yaw * self.profile.spine_counter_gain,
            [0.08, 0.11, 0.14, 0.18, 0.22, 0.27],
        )
        distribute_chain_rotation(
            pose, self.spine, self.basis.forward,
            -body.pelvis_roll * 0.52,
            [0.08, 0.11, 0.14, 0.18, 0.22, 0.27],
        )
        distribute_chain_rotation(
            pose, self.spine, self.basis.lateral,
            math.radians(self.profile.body_lean_deg)
            - body.pelvis_pitch * 0.32
            + math.radians(self.profile.breathing_chest_deg) * breathing,
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
        relaxed_neck = (
            math.radians(self.profile.neck_relaxed_pitch_deg)
            - math.radians(self.profile.body_lean_deg) * 0.22
        )
        distribute_chain_rotation(
            pose, self.neck, self.basis.lateral,
            relaxed_neck + math.radians(self.profile.breathing_neck_deg) * breathing,
            [0.11, 0.15, 0.19, 0.24, 0.31],
        )
        head_micro = math.radians(self.profile.head_micro_yaw_deg) * math.sin(math.pi * global_phase + 0.45)
        pose.rotate_world_rest_axis(
            self.head, self.basis.up,
            -body.pelvis_yaw * self.profile.head_stabilize_gain + head_micro,
        )
        pose.rotate_world_rest_axis(
            self.head, self.basis.forward,
            -body.pelvis_roll * self.profile.head_stabilize_gain,
        )
        pose.rotate_world_rest_axis(
            self.head, self.basis.lateral,
            math.radians(self.profile.head_horizon_pitch_deg) - body.pelvis_pitch * 0.42,
        )

        jaw_angle = -math.radians(self.profile.neutral_jaw_close_deg)
        jaw_angle += math.radians(self.profile.jaw_breath_deg) * (0.5 - 0.5 * math.cos(math.pi * global_phase))
        pose.rotate_world_rest_axis(self.jaw_root, self.basis.lateral, jaw_angle)

        for index, bone in enumerate(self.tail):
            pose.rotate_world_rest_axis(bone, self.basis.up, float(tail_yaw[index]))
            pose.rotate_world_rest_axis(
                bone, self.basis.lateral,
                float(self.tail_neutral_sag[index] + tail_pitch[index]),
            )

        arm_signal = math.sin(2.0 * math.pi * global_phase + 0.35)
        arm_angle = math.radians(self.profile.arm_inertia_deg) * arm_signal
        for side, sign in (("l", -1.0), ("r", 1.0)):
            arm, forearm, hand = self.arms[side]
            pose.rotate_world_rest_axis(arm, -self.basis.lateral, sign * arm_angle)
            pose.rotate_world_rest_axis(forearm, self.basis.lateral, abs(arm_angle) * 0.34)
            pose.rotate_world_rest_axis(hand, self.basis.up, -sign * arm_angle * 0.18)

        new_seeds: dict[str, np.ndarray] = {}
        solve_data: dict[str, Any] = {}
        for side, foot_plan in (("l", body.left), ("r", body.right)):
            pose, result, ground = self._solve_leg(
                pose, side, foot_plan, global_phase, leg_seeds.get(side)
            )
            new_seeds[side] = result.angles.copy()
            solve_data[side] = {"result": result, "ground": ground}
        return pose, solve_data, new_seeds

    def generate(self, keep_world_matrices: bool = False) -> GeneratedMotion:
        internal_count = int(round(self.duration * self.profile.internal_sample_hz)) + 1
        times = np.linspace(0.0, self.duration, internal_count, dtype=np.float64)
        phases = times / self.cycle_duration
        body_plans = [self.body_plan(float(phase)) for phase in phases]
        tail_yaw, tail_pitch = self._tail_dynamics(phases, body_plans)

        rotations: dict[str, list[np.ndarray]] = {name: [] for name in self.driven_bones}
        root_translation: list[np.ndarray] = []
        errors = {"l": [], "r": []}
        lateral_errors = {"l": [], "r": []}
        solver_costs = {"l": [], "r": []}
        solver_success = {"l": [], "r": []}
        ground_corrections = {"l": [], "r": []}
        joint_signed = {"l": {"knee": [], "ankle": []}, "r": {"knee": [], "ankle": []}}
        toe_min_y = {"l": [], "r": []}
        foot_positions = {"l": [], "r": []}
        worlds: list[list[np.ndarray]] | None = [] if keep_world_matrices else None
        leg_seeds: dict[str, np.ndarray | None] = {"l": None, "r": None}

        for index, (phase, body) in enumerate(zip(phases, body_plans)):
            pose, solve_data, leg_seeds = self._pose_for_sample(
                float(phase), body, tail_yaw[index], tail_pitch[index],
                include_root_motion=True, leg_seeds=leg_seeds,
            )
            for name in self.driven_bones:
                rotations[name].append(pose.quaternion(name))
            root_translation.append(pose.translation[self.asset.name_to_node[self.root]].copy())
            for side in ("l", "r"):
                result: LegSolveResult = solve_data[side]["result"]
                errors[side].append(result.target_error)
                lateral_errors[side].append(result.lateral_error)
                solver_costs[side].append(result.solver_cost)
                solver_success[side].append(result.solver_success)
                ground_corrections[side].append(solve_data[side]["ground"])
                joint_signed[side]["knee"].append(result.knee_signed_degrees)
                joint_signed[side]["ankle"].append(result.ankle_signed_degrees)
                foot_positions[side].append(pose.world_position(self.legs[side]["foot"]))
                toe_min_y[side].append(
                    min(pose.world_position(chain[-1])[1] for chain in self.toe_chains[side])
                )
            if worlds is not None:
                worlds.append([matrix.copy() for matrix in pose.world_matrices])

        rotation_arrays = {
            name: quaternion_continuity(np.asarray(values, dtype=np.float64))
            for name, values in rotations.items()
        }
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
            targets = np.array([
                plan.left.target_world if side == "l" else plan.right.target_world
                for plan in body_plans
            ])
            delta = foot_arrays[side] - targets
            horizontal = delta - np.outer(delta @ self.basis.up, self.basis.up)
            measured = np.linalg.norm(horizontal, axis=1)
            contact_error[side] = float(np.max(measured[loaded_mask]))
            contact_drift[side] = float(np.percentile(measured[loaded_mask], 95))
            toe_values = np.asarray(toe_min_y[side])
            toe_ground_error[side] = float(
                np.max(np.abs(toe_values[loaded_mask] - self.toe_tip_rest_y[side]))
            )

        dt = 1.0 / self.profile.internal_sample_hz
        joint_diagnostics: dict[str, Any] = {}
        anatomical_flip_count = {"knee": 0, "ankle": 0}
        max_velocity = 0.0
        max_acceleration = 0.0
        for side in ("l", "r"):
            geometry = self.leg_geometry[side]
            joint_diagnostics[side] = {}
            for joint in ("knee", "ankle"):
                values = np.asarray(joint_signed[side][joint], dtype=np.float64)
                expected_sign = geometry[f"{joint}_signed_sign"]
                flex = np.abs(values)
                velocity = np.gradient(values, dt, edge_order=2)
                acceleration = np.gradient(velocity, dt, edge_order=2)
                max_velocity = max(max_velocity, float(np.max(np.abs(velocity))))
                max_acceleration = max(max_acceleration, float(np.max(np.abs(acceleration))))
                flips = int(np.sum(values * expected_sign <= 0.0))
                anatomical_flip_count[joint] += flips
                joint_diagnostics[side][joint] = {
                    "expected_signed_direction": expected_sign,
                    "signed_min_deg": float(np.min(values)),
                    "signed_max_deg": float(np.max(values)),
                    "flex_min_deg": float(np.min(flex)),
                    "flex_max_deg": float(np.max(flex)),
                    "anatomical_flip_count": flips,
                    "max_velocity_deg_s": float(np.max(np.abs(velocity))),
                    "max_acceleration_deg_s2": float(np.max(np.abs(acceleration))),
                }

        endpoint_rotation = max(
            float(np.max(np.abs(values[-1] - values[0]))) for values in rotation_arrays.values()
        )
        quality_gates = {
            "zero_anatomical_flips": not any(anatomical_flip_count.values()),
            "joint_velocity_within_profile_ceiling": max_velocity <= self.profile.max_joint_velocity_deg_s,
            "joint_acceleration_within_profile_ceiling": max_acceleration <= self.profile.max_joint_acceleration_deg_s2,
            "loaded_contact_below_half_percent_hip": all(
                value / self.hip_height <= 0.005 for value in contact_error.values()
            ),
            "exact_rotation_loop": endpoint_rotation == 0.0,
            "exact_tail_loop": bool(
                np.max(np.abs(tail_yaw[-1] - tail_yaw[0])) == 0.0
                and np.max(np.abs(tail_pitch[-1] - tail_pitch[0])) == 0.0
            ),
        }
        diagnostics = {
            **self.metadata,
            "internal_sample_count": int(internal_count),
            "export_sample_count": int(len(export_indices)),
            "max_ik_error_m": {side: float(max(errors[side])) for side in ("l", "r")},
            "max_lateral_error_m": {side: float(max(map(abs, lateral_errors[side]))) for side in ("l", "r")},
            "solver_success_rate": {
                side: float(np.mean(np.asarray(solver_success[side], dtype=np.float64)))
                for side in ("l", "r")
            },
            "max_solver_cost": {side: float(max(solver_costs[side])) for side in ("l", "r")},
            "p95_contact_target_error_m": contact_drift,
            "max_contact_target_error_m": contact_error,
            "max_loaded_toe_ground_error_m": toe_ground_error,
            "max_ground_correction_m": {
                side: float(max(map(abs, ground_corrections[side]))) for side in ("l", "r")
            },
            "normalized_contact_error": {side: contact_error[side] / self.hip_height for side in ("l", "r")},
            "joint_constraints": joint_diagnostics,
            "anatomical_flip_count": anatomical_flip_count,
            "max_joint_velocity_deg_s": max_velocity,
            "max_joint_acceleration_deg_s2": max_acceleration,
            "rotation_endpoint_max_abs_diff": endpoint_rotation,
            "root_motion_distance_m": float(np.dot(root_array[-1] - root_array[0], self.basis.forward)),
            "tail_endpoint_yaw_max_abs_diff": float(np.max(np.abs(tail_yaw[-1] - tail_yaw[0]))),
            "tail_endpoint_pitch_max_abs_diff": float(np.max(np.abs(tail_pitch[-1] - tail_pitch[0]))),
            "tail_neutral_sag_total_deg": self.profile.tail_neutral_sag_deg,
            "stance_fraction": self.profile.stance_fraction,
            "quality_gates": quality_gates,
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
            "generator": "Eonwild procedural animation toolkit v3",
            "profile": self.profile.name,
            "cycleHz": self.profile.cycle_hz,
            "supercycles": self.profile.supercycle_count,
            "sampleHz": self.profile.export_sample_hz,
            "internalSampleHz": self.profile.internal_sample_hz,
            "contactAware": True,
            "anatomicalHingeConstraints": True,
            "relaxedHorizonPosture": True,
            "neutralJaw": True,
            "tailDynamics": "soft periodic spring-damper chain with distal lag",
        }
        return [
            {
                "name": "PROC_WALK_LARGE_V3_INPLACE",
                "times": motion.times_export.astype(np.float32),
                "rotations": {name: values.astype(np.float32) for name, values in motion.rotations_export.items()},
                "translations": {self.root: in_place_translation.astype(np.float32)},
                "interpolation": "LINEAR",
                "extras": {**common_extras, "rootMotion": False, "recommendedRuntimeSpeedMps": self.speed},
            },
            {
                "name": "PROC_WALK_LARGE_V3_ROOTMOTION",
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
