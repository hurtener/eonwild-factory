"""Reference-fitted, terrain-aware, variable-speed locomotion for V4."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import math

import numpy as np
from scipy.spatial.transform import Rotation

from eonproc_v3.curves import minimum_jerk, smooth_bump, cyclic_gaussian
from eonproc_v3.generator import (
    AnatomicallyConstrainedBipedGenerator,
    LegSolveResult,
    _signed_turn,
)
from eonproc_v3.gltf_io import quaternion_continuity
from eonproc_v3.rig import AnatomicalBasis, Pose, SemanticMap, distribute_chain_rotation
from eonproc_v3.gltf_io import GlbAsset

from .clip import AnimationClip
from .path import MotionPath, StraightPath, ArcPath, EasedArcPath, PathFrame
from .profile import BipedV4Profile
from .sole import SoleContactModel, SoleMeasurement
from .terrain import TerrainSurface, FlatTerrain


@dataclass(frozen=True)
class V4FootPlan:
    side: str
    phase: float
    stance: bool
    swing_u: float
    load: float
    target_world: np.ndarray
    contact_world: np.ndarray
    next_contact_world: np.ndarray
    foot_pitch_radians: float
    toe_radians: float
    terrain_normal: np.ndarray
    terrain_height: float
    path_heading_radians: float
    contact_distance: float
    next_contact_distance: float


@dataclass(frozen=True)
class V4BodyPlan:
    path_frame: PathFrame
    root_displacement_world: np.ndarray
    root_progress: float
    pelvis_translation_world: np.ndarray
    pelvis_yaw: float
    pelvis_roll: float
    pelvis_pitch: float
    support_lateral_normalized: float
    vertical_signal: float
    speed_fraction: float
    acceleration_fraction: float
    alert_amount: float
    terrain_normal: np.ndarray
    left: V4FootPlan
    right: V4FootPlan


@dataclass(frozen=True)
class LocomotionSchedule:
    name: str
    times: np.ndarray
    phases: np.ndarray
    distances: np.ndarray
    speeds: np.ndarray
    accelerations: np.ndarray
    path: MotionPath
    terrain: TerrainSurface
    loop: bool
    alert_amount: float = 0.0
    root_motion: bool = True
    tags: tuple[str, ...] = ()


@dataclass
class LocomotionResult:
    clip: AnimationClip
    in_place_clip: AnimationClip | None
    diagnostics: dict[str, Any]


def _tilt_rotation(up: np.ndarray, normal: np.ndarray) -> Rotation:
    u = np.asarray(up, dtype=np.float64)
    n = np.asarray(normal, dtype=np.float64)
    u /= max(np.linalg.norm(u), 1e-12)
    n /= max(np.linalg.norm(n), 1e-12)
    dot = float(np.clip(np.dot(u, n), -1.0, 1.0))
    if dot > 1.0 - 1e-10:
        return Rotation.identity()
    axis = np.cross(u, n)
    norm = np.linalg.norm(axis)
    if norm < 1e-10:
        return Rotation.identity()
    return Rotation.from_rotvec(axis / norm * math.acos(dot))


def _sample_integral(values: np.ndarray, dt: float) -> np.ndarray:
    output = np.zeros_like(values, dtype=np.float64)
    if len(values) > 1:
        output[1:] = np.cumsum(0.5 * (values[:-1] + values[1:]) * dt)
    return output


def constant_schedule(
    name: str,
    generator: "TerrainAwareLocomotionGenerator",
    cycles: float,
    path_factory: Callable[[float], MotionPath] | None = None,
    terrain: TerrainSurface | None = None,
    alert_amount: float = 0.0,
    cycle_hz: float | None = None,
    stride_scale: float = 1.0,
    loop: bool = True,
    tags: tuple[str, ...] = (),
) -> LocomotionSchedule:
    hz = float(cycle_hz or generator.profile.cycle_hz)
    duration = cycles / hz
    count = int(round(duration * generator.profile.internal_sample_hz)) + 1
    times = np.linspace(0.0, duration, count)
    phases = np.linspace(0.0, cycles, count)
    stride = generator.stride * float(stride_scale)
    distances = phases * stride
    speeds = np.full(count, stride * hz, dtype=np.float64)
    accelerations = np.zeros(count, dtype=np.float64)
    path = path_factory(float(distances[-1])) if path_factory else StraightPath(generator.root_rest_world, generator.base_basis)
    return LocomotionSchedule(
        name=name, times=times, phases=phases, distances=distances,
        speeds=speeds, accelerations=accelerations, path=path,
        terrain=terrain or FlatTerrain(generator.mesh_ground), loop=loop,
        alert_amount=float(alert_amount), root_motion=True, tags=tags,
    )


def speed_transition_schedule(
    name: str,
    generator: "TerrainAwareLocomotionGenerator",
    duration: float,
    cycles: float,
    accelerating: bool,
    terrain: TerrainSurface | None = None,
    tags: tuple[str, ...] = (),
) -> LocomotionSchedule:
    count = int(round(duration * generator.profile.internal_sample_hz)) + 1
    times = np.linspace(0.0, duration, count)
    u = times / max(duration, 1e-9)
    envelope = np.array([minimum_jerk(float(value)) for value in u])
    if not accelerating:
        envelope = 1.0 - envelope
    final_speed = generator.speed
    speeds = final_speed * envelope
    # Keep a tiny phase advance while the creature is almost stationary so the
    # planted stance can reorganize before the first full step.
    phase_rate = generator.profile.cycle_hz * (
        generator.profile.minimum_active_speed_fraction
        + (1.0 - generator.profile.minimum_active_speed_fraction) * envelope
    )
    dt = times[1] - times[0]
    phases = _sample_integral(phase_rate, dt)
    target_cycles = float(cycles)
    if phases[-1] > 1e-9:
        phases *= target_cycles / phases[-1]
    distances = _sample_integral(speeds, dt)
    accelerations = np.gradient(speeds, dt, edge_order=2)
    return LocomotionSchedule(
        name=name, times=times, phases=phases, distances=distances,
        speeds=speeds, accelerations=accelerations,
        path=StraightPath(generator.root_rest_world, generator.base_basis),
        terrain=terrain or FlatTerrain(generator.mesh_ground), loop=False,
        alert_amount=0.0, root_motion=True, tags=tags,
    )


class TerrainAwareLocomotionGenerator(AnatomicallyConstrainedBipedGenerator):
    def __init__(self, asset: GlbAsset, semantics: SemanticMap, profile: BipedV4Profile):
        super().__init__(asset, semantics, profile)
        self.profile: BipedV4Profile = profile
        self.base_basis = self.basis
        self.root_rest_world = asset.rest_world[asset.name_to_node[self.root]][:3, 3].copy()
        self.mesh_ground = float(np.min(asset.primitive().positions[:, 1]))
        self.foot_offsets: dict[str, dict[str, float]] = {}
        for side in ("l", "r"):
            delta = self.foot_rest[side] - self.root_rest_world
            self.foot_offsets[side] = {
                "lateral": float(np.dot(delta, self.base_basis.lateral)),
                "forward": float(np.dot(delta, self.base_basis.forward)),
                "bone_height": float(self.foot_rest[side][1] - self.mesh_ground),
            }
        self.sole = SoleContactModel(
            asset=asset, semantics=semantics, basis=self.base_basis, hip_height=self.hip_height,
            weight_threshold=profile.sole_weight_threshold,
            height_band=self.hip_height * profile.sole_height_band_hip_fraction,
            min_vertices=profile.sole_min_vertices_per_side,
            max_vertices=profile.sole_max_vertices_per_side,
            contact_quantile=profile.sole_contact_quantile,
            clearance=profile.sole_clearance_m,
            max_correction=self.hip_height * profile.sole_max_vertical_correction_hip_fraction,
        )
        # V4 action layers may use these mapped branches as well.
        extras = []
        for tag in ("skull", "snout", "snout_tip", "wrist_l", "wrist_r", "claw_l", "claw_r"):
            if tag in semantics.tags and semantics.bone(tag) in asset.name_to_node:
                extras.append(semantics.bone(tag))
        self.driven_bones = sorted(set([self.root, *self.driven_bones, *self.jaw_chain, *extras]), key=lambda n: asset.name_to_node[n])

    def _distance_at_phase(self, schedule: LocomotionSchedule, phase_value: float) -> float:
        phases = schedule.phases
        distances = schedule.distances
        if phase_value <= phases[0]:
            stride = self.stride
            return float(distances[0] + (phase_value - phases[0]) * stride)
        if phase_value >= phases[-1]:
            stride = self.stride
            return float(distances[-1] + (phase_value - phases[-1]) * stride)
        return float(np.interp(phase_value, phases, distances))

    def _contact_world(self, schedule: LocomotionSchedule, side: str, distance: float) -> tuple[np.ndarray, np.ndarray, float, float]:
        frame = schedule.path.frame(distance)
        offsets = self.foot_offsets[side]
        point = (
            frame.position
            + frame.basis.lateral * offsets["lateral"]
            + frame.basis.forward * (offsets["forward"] + self.contact_lead)
        )
        terrain_height, normal = schedule.terrain.height_normal(point)
        point = point.copy()
        point[1] = terrain_height + offsets["bone_height"]
        return point, normal, terrain_height, frame.heading_radians

    def foot_plan_scheduled(self, schedule: LocomotionSchedule, sample_index: int, side: str) -> V4FootPlan:
        global_phase = float(schedule.phases[sample_index])
        offset = 0.0 if side == "l" else 0.5
        relative = global_phase - offset
        contact_index = math.floor(relative + 1e-10)
        phase = relative - contact_index
        if phase >= 1.0 - 1e-10:
            contact_index += 1
            phase = 0.0
        contact_phase = contact_index + offset
        next_contact_phase = contact_phase + 1.0
        contact_distance = self._distance_at_phase(schedule, contact_phase)
        next_distance = self._distance_at_phase(schedule, next_contact_phase)
        contact, normal, terrain_height, heading = self._contact_world(schedule, side, contact_distance)
        next_contact, next_normal, _, next_heading = self._contact_world(schedule, side, next_distance)

        stance = phase < self.profile.stance_fraction
        swing_u = 0.0
        target = contact.copy()
        terrain_normal = normal.copy()
        if stance:
            ramp = self.profile.load_ramp_fraction
            load_in = minimum_jerk(phase / ramp) if phase < ramp else 1.0
            remaining = self.profile.stance_fraction - phase
            load_out = minimum_jerk(remaining / ramp) if remaining < ramp else 1.0
            load = min(load_in, load_out)
        else:
            load = 0.0
            swing_u = (phase - self.profile.stance_fraction) / (1.0 - self.profile.stance_fraction)
            advance_start = self.profile.swing_advance_start_fraction
            advance_end = self.profile.swing_advance_end_fraction
            advance_u = np.clip((swing_u - advance_start) / max(advance_end - advance_start, 1e-6), 0.0, 1.0)
            mix = minimum_jerk(float(advance_u))
            rise_u = np.clip(swing_u / max(self.profile.swing_lift_rise_fraction, 1e-6), 0.0, 1.0)
            fall_u = np.clip((swing_u - self.profile.swing_lift_fall_start_fraction) / max(1.0 - self.profile.swing_lift_fall_start_fraction, 1e-6), 0.0, 1.0)
            lift_envelope = minimum_jerk(float(rise_u)) * (1.0 - minimum_jerk(float(fall_u)))
            target = contact * (1.0 - mix) + next_contact * mix
            terrain_normal = normal * (1.0 - mix) + next_normal * mix
            terrain_normal /= max(np.linalg.norm(terrain_normal), 1e-12)
            lift_scale = self.profile.alert_step_height_scale if schedule.alert_amount > 0.5 else 1.0
            if isinstance(schedule.path, EasedArcPath):
                lift_scale *= self.profile.swing_turn_lift_scale
            target += terrain_normal * (self.swing_lift * lift_scale * lift_envelope)
            outward_sign = -1.0 if side == "l" else 1.0
            moving_frame = schedule.path.frame(float(schedule.distances[sample_index]))
            target += moving_frame.basis.lateral * (outward_sign * self.swing_outward * lift_envelope)

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
            prepare = minimum_jerk(max(0.0, (swing_u - (1.0 - self.profile.precontact_window_fraction)) / self.profile.precontact_window_fraction))
            release_window = max(0.12, min(0.30, self.profile.toe_off_window_fraction))
            release = 1.0 - minimum_jerk(min(1.0, swing_u / release_window))
            pitch_deg = -self.profile.toe_off_foot_deg * release
            pitch_deg += self.profile.swing_ankle_deg * fold * (1.0 - release)
            pitch_deg = pitch_deg * (1.0 - prepare) + self.profile.contact_foot_deg * prepare
            toe_deg = self.profile.toe_push_deg * release
            toe_deg += -0.14 * self.profile.toe_push_deg * fold * (1.0 - release)
            toe_deg *= 1.0 - prepare
        return V4FootPlan(
            side=side, phase=phase, stance=stance, swing_u=swing_u, load=load,
            target_world=target, contact_world=contact, next_contact_world=next_contact,
            foot_pitch_radians=math.radians(pitch_deg), toe_radians=math.radians(toe_deg),
            terrain_normal=terrain_normal, terrain_height=terrain_height,
            path_heading_radians=heading * (1.0 - (mix if not stance else 0.0)) + next_heading * (mix if not stance else 0.0),
            contact_distance=contact_distance, next_contact_distance=next_distance,
        )

    def body_plan_scheduled(self, schedule: LocomotionSchedule, sample_index: int) -> V4BodyPlan:
        phase = float(schedule.phases[sample_index])
        distance = float(schedule.distances[sample_index])
        frame0 = schedule.path.frame(distance)
        center_height, center_normal = schedule.terrain.height_normal(frame0.position)
        frame = PathFrame(
            position=frame0.position + self.base_basis.up * (center_height - self.mesh_ground),
            heading_radians=frame0.heading_radians,
            basis=frame0.basis,
        )
        left = self.foot_plan_scheduled(schedule, sample_index, "l")
        right = self.foot_plan_scheduled(schedule, sample_index, "r")
        total_load = max(left.load + right.load, 1e-6)
        support = (left.target_world * left.load + right.target_world * right.load) / total_load
        support_delta = support - frame.position
        support_lateral = float(np.dot(support_delta, frame.basis.lateral))
        normalized = support_lateral / max(self.foot_span * 0.5, 1e-6)
        normalized = float(np.clip(normalized, -1.0, 1.0))

        vertical_wave = -math.cos(4.0 * math.pi * phase)
        contact_drop = cyclic_gaussian(phase, 0.055, 0.055, 0.5)
        vertical = self.pelvis_bob * vertical_wave - self.pelvis_loading_drop * contact_drop
        forward_sway = self.pelvis_forward_sway * math.sin(4.0 * math.pi * phase)
        lateral_shift = self.profile.pelvis_support_shift_gain * support_lateral
        # Only follow differential terrain elevation. The support target contains
        # the foot-bone height above the sole and must not be interpreted as a
        # pelvis drop relative to the root.
        support_ground_height = (left.terrain_height * left.load + right.terrain_height * right.load) / total_load
        terrain_height_follow = (support_ground_height - center_height) * self.profile.terrain_pelvis_height_blend
        translation = (
            frame.basis.lateral * lateral_shift
            + frame.basis.up * (vertical + terrain_height_follow)
            + frame.basis.forward * forward_sway
        )

        tilt = _tilt_rotation(frame.basis.up, center_normal)
        tilt_vec = tilt.as_rotvec()
        terrain_pitch = float(np.dot(tilt_vec, frame.basis.lateral)) * self.profile.terrain_pelvis_pitch_gain
        terrain_roll = float(np.dot(tilt_vec, frame.basis.forward)) * self.profile.terrain_pelvis_roll_gain
        variation = self._cycle_variation(phase)
        speed_fraction = float(schedule.speeds[sample_index] / max(self.speed, 1e-8))
        max_accel = max(self.speed / max(self.profile.start_duration_seconds * 0.34, 1e-6), 1e-6)
        acceleration_fraction = float(np.clip(schedule.accelerations[sample_index] / max_accel, -1.0, 1.0))
        pelvis_yaw = math.radians(self.profile.pelvis_yaw_deg) * math.sin(2.0 * math.pi * phase) * variation
        pelvis_roll = math.radians(self.profile.pelvis_roll_deg) * normalized + terrain_roll
        acceleration_pitch = math.radians(
            self.profile.acceleration_lean_deg if acceleration_fraction >= 0.0 else -self.profile.braking_lean_deg
        ) * acceleration_fraction
        pelvis_pitch = (
            math.radians(self.profile.pelvis_pitch_deg) * math.cos(4.0 * math.pi * phase)
            + terrain_pitch + acceleration_pitch * 0.28
        )
        return V4BodyPlan(
            path_frame=frame,
            root_displacement_world=frame.position - self.root_rest_world,
            root_progress=distance,
            pelvis_translation_world=translation,
            pelvis_yaw=pelvis_yaw, pelvis_roll=pelvis_roll, pelvis_pitch=pelvis_pitch,
            support_lateral_normalized=normalized, vertical_signal=vertical,
            speed_fraction=speed_fraction, acceleration_fraction=acceleration_fraction,
            alert_amount=schedule.alert_amount, terrain_normal=center_normal,
            left=left, right=right,
        )

    def _leg_preferences(self, foot: V4FootPlan, global_phase: float) -> tuple[float, float, float]:
        hip_delta, knee, ankle = super()._leg_preferences(foot, global_phase)
        if foot.stance:
            return hip_delta, knee, ankle
        u = float(np.clip(foot.swing_u, 0.0, 1.0))
        rise_u = np.clip(u / max(self.profile.swing_lift_rise_fraction, 1e-6), 0.0, 1.0)
        fall_u = np.clip((u - self.profile.swing_lift_fall_start_fraction) / max(1.0 - self.profile.swing_lift_fall_start_fraction, 1e-6), 0.0, 1.0)
        lift = minimum_jerk(float(rise_u)) * (1.0 - minimum_jerk(float(fall_u)))
        prepare = minimum_jerk(max(0.0, (u - (1.0 - self.profile.precontact_window_fraction)) / self.profile.precontact_window_fraction))
        knee_release = self.profile.knee_stance_flex_deg + 5.0
        ankle_release = self.profile.ankle_stance_flex_deg - 7.0
        knee_degrees = knee_release + (self.profile.knee_swing_flex_deg - knee_release) * (lift ** 0.78)
        ankle_degrees = ankle_release + (self.profile.ankle_swing_flex_deg - ankle_release) * (lift ** 0.82)
        knee_degrees = knee_degrees * (1.0 - prepare) + self.profile.knee_stance_flex_deg * prepare
        ankle_degrees = ankle_degrees * (1.0 - prepare) + self.profile.ankle_stance_flex_deg * prepare
        return hip_delta, math.radians(knee_degrees), math.radians(ankle_degrees)

    def _tail_dynamics_scheduled(self, schedule: LocomotionSchedule, body_plans: list[V4BodyPlan]) -> tuple[np.ndarray, np.ndarray]:
        count = len(self.tail)
        n = len(schedule.times)
        dt = 1.0 / self.profile.internal_sample_hz
        headings = np.unwrap(np.asarray([plan.path_frame.heading_radians for plan in body_plans], dtype=np.float64))
        heading_velocity = np.gradient(headings, dt, edge_order=2) if n > 2 else np.zeros(n)
        heading_acceleration = np.gradient(heading_velocity, dt, edge_order=2) if n > 2 else np.zeros(n)
        yaw_drive = np.array([
            -self.profile.tail_root_yaw_gain * plan.pelvis_yaw
            - math.radians(self.profile.tail_com_gain * 3.0) * plan.support_lateral_normalized
            - 0.22 * heading_velocity[index]
            - 0.055 * heading_acceleration[index]
            for index, plan in enumerate(body_plans)
        ])
        pitch_drive = np.array([
            -self.profile.tail_pitch_gain * plan.pelvis_pitch
            - plan.vertical_signal / max(self.hip_height, 1e-6) * 0.15
            + math.radians(self.profile.alert_tail_raise_deg) * plan.alert_amount
            for plan in body_plans
        ])
        stiffness = np.linspace(self.profile.tail_stiffness_root, self.profile.tail_stiffness_tip * 0.82, count)
        damping = 2.0 * self.profile.tail_damping_ratio * np.sqrt(stiffness)
        limits = np.radians(np.linspace(self.profile.tail_dynamic_limit_root_deg, self.profile.tail_dynamic_limit_tip_deg * 1.22, count))
        lag_samples = np.rint(np.arange(count) * self.profile.tail_phase_lag_seconds_per_bone * self.profile.internal_sample_hz).astype(int)

        def simulate(drive: np.ndarray) -> np.ndarray:
            angle = np.zeros(count)
            velocity = np.zeros(count)
            capture = np.zeros((n, count))
            warmup = self.profile.tail_warmup_supercycles if schedule.loop else 0
            total = warmup * max(n - 1, 1) + n
            for step in range(total):
                source_index = step % max(n - 1, 1) if schedule.loop else min(step, n - 1)
                acceleration = np.zeros(count)
                for index in range(count):
                    delayed_index = (source_index - lag_samples[index]) % max(n - 1, 1) if schedule.loop else max(0, source_index - lag_samples[index])
                    target = drive[delayed_index] * math.exp(-0.07 * index)
                    if index > 0:
                        target += angle[index - 1] * self.profile.tail_parent_follow
                    acceleration[index] = stiffness[index] * (target - angle[index]) - damping[index] * velocity[index]
                    if index > 0:
                        acceleration[index] += self.profile.tail_coupling * (angle[index - 1] - angle[index])
                    if index + 1 < count:
                        acceleration[index] += self.profile.tail_coupling * 0.12 * (angle[index + 1] - angle[index])
                velocity += acceleration * dt
                angle += velocity * dt
                angle = np.clip(angle, -limits, limits)
                if step >= total - n:
                    capture[step - (total - n)] = angle
            if schedule.loop:
                capture[-1] = capture[0]
            return capture
        return simulate(yaw_drive), simulate(pitch_drive)

    def _solve_leg_terrain(
        self,
        pose: Pose,
        side: str,
        foot: V4FootPlan,
        global_phase: float,
        seed: np.ndarray | None,
        terrain: TerrainSurface,
    ) -> tuple[Pose, LegSolveResult, SoleMeasurement, float]:
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
            if abs(derivative) > 1e-7:
                abduction = float(np.clip(lateral_error_before / derivative, -limit, limit))
                work.rotate_world(leg["thigh"], self.basis.forward, abduction)

            values, knee_target, ankle_target, foot_target, _, cost, success = self._solve_sagittal_angles(
                work, side, foot, target_world, global_phase, initial
            )
            work.align_child_about_world_axis(leg["thigh"], leg["shin"], knee_target, self.basis.lateral, 1.0, math.pi)
            work.align_child_about_world_axis(leg["shin"], leg["ankle"], ankle_target, self.basis.lateral, 1.0, math.pi)
            work.align_child_about_world_axis(leg["ankle"], leg["foot"], foot_target, self.basis.lateral, 1.0, math.pi)

            foot_index = self.asset.name_to_node[leg["foot"]]
            heading_rotation = Rotation.from_rotvec(self.base_basis.up * foot.path_heading_radians)
            blended_normal = self.basis.up * (1.0 - self.profile.terrain_normal_blend) + foot.terrain_normal * self.profile.terrain_normal_blend
            blended_normal /= max(np.linalg.norm(blended_normal), 1e-12)
            terrain_tilt = _tilt_rotation(self.basis.up, blended_normal)
            terrain_vec = terrain_tilt.as_rotvec()
            pitch_component = float(np.clip(np.dot(terrain_vec, self.basis.lateral), -math.radians(self.profile.terrain_foot_pitch_limit_deg), math.radians(self.profile.terrain_foot_pitch_limit_deg)))
            roll_component = float(np.clip(np.dot(terrain_vec, self.basis.forward), -math.radians(self.profile.terrain_foot_roll_limit_deg), math.radians(self.profile.terrain_foot_roll_limit_deg)))
            tilt_limited = Rotation.from_rotvec(self.basis.lateral * pitch_component) * Rotation.from_rotvec(self.basis.forward * roll_component)
            desired_foot_world = (
                tilt_limited
                * Rotation.from_rotvec(self.basis.lateral * foot.foot_pitch_radians)
                * heading_rotation
                * self.asset.rest_world_rotation[foot_index]
            )
            work.set_world_rotation(leg["foot"], desired_foot_world)
            toe_weights = (0.52, 0.30, 0.18)
            for chain_index, toe_chain in enumerate(self.toe_chains[side]):
                outer_scale = (0.92, 1.0, 0.95)[chain_index]
                distribute_chain_rotation(work, toe_chain, self.basis.lateral, foot.toe_radians * outer_scale, toe_weights[: len(toe_chain)])

            points = [work.world_position(leg[name]) for name in ("thigh", "shin", "ankle", "foot")]
            knee_signed = math.degrees(_signed_turn(points[1] - points[0], points[2] - points[1], self.basis.lateral))
            ankle_signed = math.degrees(_signed_turn(points[2] - points[1], points[3] - points[2], self.basis.lateral))
            result = LegSolveResult(
                angles=values,
                target_error=float(np.linalg.norm(work.world_position(leg["foot"]) - target_world)),
                lateral_error=float(np.dot(work.world_position(leg["foot"]) - target_world, self.basis.lateral)),
                solver_cost=cost, solver_success=success,
                knee_signed_degrees=knee_signed, ankle_signed_degrees=ankle_signed,
            )
            return work, result

        target = foot.target_world.copy()
        solved, result = solve_once(target, seed)
        measurement = self.sole.measure(solved, side, terrain, foot.load if foot.stance else 0.0)
        correction = 0.0
        corrected_target = target.copy()
        if foot.stance and foot.load > 0.04:
            for _ in range(3):
                step = measurement.correction_up
                if abs(step) <= 1e-5:
                    break
                correction += step
                corrected_target = corrected_target + self.basis.up * step
                solved, result = solve_once(corrected_target, result.angles)
                measurement = self.sole.measure(solved, side, terrain, foot.load)
                if measurement.maximum_penetration <= self.profile.sole_clearance_m * 0.2:
                    break
        return solved, result, measurement, correction

    def _pose_for_body(
        self,
        time_seconds: float,
        global_phase: float,
        body: V4BodyPlan,
        tail_yaw: np.ndarray,
        tail_pitch: np.ndarray,
        leg_seeds: dict[str, np.ndarray | None],
        terrain: TerrainSurface,
    ) -> tuple[Pose, dict[str, Any], dict[str, np.ndarray]]:
        self.basis = body.path_frame.basis
        pose = Pose(self.asset)
        pose.add_world_translation_rest(self.root, body.root_displacement_world)
        pose.rotate_world_rest_axis(self.root, self.base_basis.up, body.path_frame.heading_radians)
        pose.add_world_translation_rest(self.pelvis, body.pelvis_translation_world)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.up, body.pelvis_yaw)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.forward, body.pelvis_roll)
        pose.rotate_world_rest_axis(
            self.pelvis, self.basis.lateral,
            body.pelvis_pitch + math.radians(self.profile.pelvis_neutral_pitch_deg),
        )

        breathing = math.sin(2.0 * math.pi * 0.29 * time_seconds + 0.15)
        acceleration_lean = math.radians(
            self.profile.acceleration_lean_deg if body.acceleration_fraction >= 0.0 else -self.profile.braking_lean_deg
        ) * body.acceleration_fraction
        distribute_chain_rotation(pose, self.spine, self.basis.up, -body.pelvis_yaw * self.profile.spine_counter_gain, [0.08, 0.11, 0.14, 0.18, 0.22, 0.27])
        distribute_chain_rotation(pose, self.spine, self.basis.forward, -body.pelvis_roll * 0.52, [0.08, 0.11, 0.14, 0.18, 0.22, 0.27])
        distribute_chain_rotation(
            pose, self.spine, self.basis.lateral,
            math.radians(self.profile.body_lean_deg)
            - body.pelvis_pitch * 0.32 + acceleration_lean
            + math.radians(self.profile.breathing_chest_deg) * breathing,
            [0.07, 0.10, 0.13, 0.17, 0.22, 0.31],
        )
        alert_neck = -math.radians(self.profile.alert_neck_raise_deg) * body.alert_amount
        distribute_chain_rotation(pose, self.neck, self.basis.up, body.pelvis_yaw * self.profile.neck_stabilize_gain, [0.11, 0.15, 0.19, 0.24, 0.31])
        distribute_chain_rotation(pose, self.neck, self.basis.forward, body.pelvis_roll * self.profile.neck_stabilize_gain, [0.11, 0.15, 0.19, 0.24, 0.31])
        relaxed_neck = math.radians(self.profile.neck_relaxed_pitch_deg) - math.radians(self.profile.body_lean_deg) * 0.22
        distribute_chain_rotation(
            pose, self.neck, self.basis.lateral,
            relaxed_neck + alert_neck + math.radians(self.profile.breathing_neck_deg) * breathing,
            [0.11, 0.15, 0.19, 0.24, 0.31],
        )
        scan = math.radians(self.profile.alert_scan_yaw_deg) * body.alert_amount * math.sin(2.0 * math.pi * time_seconds / self.profile.alert_scan_period_seconds)
        head_micro = math.radians(self.profile.head_micro_yaw_deg) * math.sin(math.pi * global_phase + 0.45)
        pose.rotate_world_rest_axis(self.head, self.basis.up, -body.pelvis_yaw * self.profile.head_stabilize_gain + head_micro + scan)
        pose.rotate_world_rest_axis(self.head, self.basis.forward, -body.pelvis_roll * self.profile.head_stabilize_gain)
        pose.rotate_world_rest_axis(
            self.head, self.basis.lateral,
            math.radians(self.profile.head_horizon_pitch_deg)
            - body.pelvis_pitch * 0.42
            - math.radians(self.profile.alert_head_raise_deg) * body.alert_amount,
        )

        jaw_angle = -math.radians(self.profile.neutral_jaw_close_deg)
        jaw_angle += math.radians(self.profile.jaw_breath_deg) * (0.5 + 0.5 * breathing)
        jaw_index = self.asset.name_to_node[self.jaw_root]
        jaw_axis_local = self.asset.rest_world_rotation[jaw_index].inv().apply(self.base_basis.lateral)
        jaw_axis_local /= max(np.linalg.norm(jaw_axis_local), 1e-12)
        pose.rotate_local(self.jaw_root, jaw_axis_local, jaw_angle)

        for index, bone in enumerate(self.tail):
            pose.rotate_world_rest_axis(bone, self.basis.up, float(tail_yaw[index]))
            pose.rotate_world_rest_axis(bone, self.basis.lateral, float(self.tail_neutral_sag[index] + tail_pitch[index]))

        arm_signal = math.sin(2.0 * math.pi * global_phase + 0.35)
        arm_angle = math.radians(self.profile.arm_inertia_deg) * arm_signal * max(0.35, body.speed_fraction)
        for side, sign in (("l", -1.0), ("r", 1.0)):
            arm, forearm, hand = self.arms[side]
            pose.rotate_world_rest_axis(arm, -self.basis.lateral, sign * arm_angle)
            pose.rotate_world_rest_axis(forearm, self.basis.lateral, abs(arm_angle) * 0.34)
            pose.rotate_world_rest_axis(hand, self.basis.up, -sign * arm_angle * 0.18)

        new_seeds: dict[str, np.ndarray] = {}
        solve_data: dict[str, Any] = {}
        for side, foot_plan in (("l", body.left), ("r", body.right)):
            pose, result, sole, correction = self._solve_leg_terrain(
                pose, side, foot_plan, global_phase, leg_seeds.get(side), terrain
            )
            new_seeds[side] = result.angles.copy()
            solve_data[side] = {"result": result, "sole": sole, "correction": correction}
        return pose, solve_data, new_seeds

    def generate_schedule(self, schedule: LocomotionSchedule, keep_world_matrices: bool = True) -> LocomotionResult:
        body_plans = [self.body_plan_scheduled(schedule, index) for index in range(len(schedule.times))]
        tail_yaw, tail_pitch = self._tail_dynamics_scheduled(schedule, body_plans)
        rotations: dict[str, list[np.ndarray]] = {name: [] for name in self.driven_bones}
        root_translation: list[np.ndarray] = []
        worlds: list[list[np.ndarray]] | None = [] if keep_world_matrices else None
        leg_seeds: dict[str, np.ndarray | None] = {"l": None, "r": None}
        joint_signed = {"l": {"knee": [], "ankle": []}, "r": {"knee": [], "ankle": []}}
        sole_data: dict[str, list[SoleMeasurement]] = {"l": [], "r": []}
        target_errors = {"l": [], "r": []}
        corrections = {"l": [], "r": []}
        foot_positions = {"l": [], "r": []}

        for index, (time_value, phase, body) in enumerate(zip(schedule.times, schedule.phases, body_plans)):
            pose, solved, leg_seeds = self._pose_for_body(
                float(time_value), float(phase), body, tail_yaw[index], tail_pitch[index], leg_seeds, schedule.terrain
            )
            for name in self.driven_bones:
                rotations[name].append(pose.quaternion(name))
            root_translation.append(pose.translation[self.asset.name_to_node[self.root]].copy())
            for side in ("l", "r"):
                result: LegSolveResult = solved[side]["result"]
                joint_signed[side]["knee"].append(result.knee_signed_degrees)
                joint_signed[side]["ankle"].append(result.ankle_signed_degrees)
                sole_data[side].append(solved[side]["sole"])
                target_errors[side].append(result.target_error)
                corrections[side].append(solved[side]["correction"])
                foot_positions[side].append(pose.world_position(self.legs[side]["foot"]))
            if worlds is not None:
                worlds.append([matrix.copy() for matrix in pose.world_matrices])

        rotation_arrays = {name: quaternion_continuity(np.asarray(values)) for name, values in rotations.items()}
        if schedule.loop:
            for values in rotation_arrays.values():
                values[-1] = values[0]
        root_array = np.asarray(root_translation)
        decimation = self.profile.internal_sample_hz // self.profile.export_sample_hz
        indices = np.arange(0, len(schedule.times), decimation, dtype=np.int64)
        if indices[-1] != len(schedule.times) - 1:
            indices = np.append(indices, len(schedule.times) - 1)
        times = schedule.times[indices]
        rotations_export = {name: values[indices] for name, values in rotation_arrays.items()}
        root_export = root_array[indices]
        worlds_export = None if worlds is None else [worlds[int(index)] for index in indices]

        loaded_penetration: dict[str, float] = {}
        loaded_gap: dict[str, float] = {}
        for side in ("l", "r"):
            loads = np.asarray([
                plan.left.load if side == "l" else plan.right.load for plan in body_plans
            ])
            mask = loads > 0.18
            stable_mask = loads > 0.72
            penetration = np.asarray([value.maximum_penetration for value in sole_data[side]])
            gaps = np.asarray([abs(value.contact_quantile_signed_distance - value.target_contact_quantile) for value in sole_data[side]])
            loaded_penetration[side] = float(np.max(penetration[mask])) if np.any(mask) else 0.0
            loaded_gap[side] = float(np.max(gaps[stable_mask])) if np.any(stable_mask) else 0.0

        joint_diag: dict[str, Any] = {}
        flips = 0
        max_velocity = 0.0
        max_acceleration = 0.0
        dt = 1.0 / self.profile.internal_sample_hz
        for side in ("l", "r"):
            joint_diag[side] = {}
            for joint in ("knee", "ankle"):
                values = np.asarray(joint_signed[side][joint])
                expected = self.leg_geometry[side][f"{joint}_signed_sign"]
                count = int(np.sum(values * expected <= 0.0))
                flips += count
                velocity = np.gradient(values, dt, edge_order=2)
                acceleration = np.gradient(velocity, dt, edge_order=2)
                max_velocity = max(max_velocity, float(np.max(np.abs(velocity))))
                max_acceleration = max(max_acceleration, float(np.max(np.abs(acceleration))))
                joint_diag[side][joint] = {
                    "expected_sign": expected,
                    "min_flex_deg": float(np.min(np.abs(values))),
                    "max_flex_deg": float(np.max(np.abs(values))),
                    "reverse_sample_count": count,
                    "max_velocity_deg_s": float(np.max(np.abs(velocity))),
                    "max_acceleration_deg_s2": float(np.max(np.abs(acceleration))),
                }

        extras = {
            "generator": "Eonwild procedural animation toolkit v4",
            "version": "4.0.0",
            "loop": schedule.loop,
            "rootMotion": True,
            "sampleHz": self.profile.export_sample_hz,
            "internalSampleHz": self.profile.internal_sample_hz,
            "referenceFitted": True,
            "vertexSoleCollision": True,
            "terrainAware": not isinstance(schedule.terrain, FlatTerrain) or schedule.terrain.height != self.mesh_ground,
            "terrain": schedule.terrain.name,
            "path": type(schedule.path).__name__,
            "alertAmount": schedule.alert_amount,
            "tags": list(schedule.tags),
        }
        diagnostics = {
            "clip": schedule.name,
            "duration_seconds": float(schedule.times[-1]),
            "phase_advance_cycles": float(schedule.phases[-1] - schedule.phases[0]),
            "distance_m": float(schedule.distances[-1] - schedule.distances[0]),
            "mean_speed_mps": float(np.mean(schedule.speeds)),
            "peak_speed_mps": float(np.max(schedule.speeds)),
            "terrain": schedule.terrain.name,
            "path": type(schedule.path).__name__,
            "sole": self.sole.metadata(),
            "loaded_max_penetration_m": loaded_penetration,
            "loaded_max_contact_quantile_error_m": loaded_gap,
            "max_leg_target_error_m": {side: float(max(target_errors[side])) for side in ("l", "r")},
            "max_sole_vertical_correction_m": {side: float(max(map(abs, corrections[side]))) for side in ("l", "r")},
            "joint_constraints": joint_diag,
            "anatomical_reverse_sample_count": flips,
            "max_joint_velocity_deg_s": max_velocity,
            "max_joint_acceleration_deg_s2": max_acceleration,
            "quality_gates": {
                "zero_anatomical_reversals": flips == 0,
                "vertex_penetration_within_gate": all(value <= self.hip_height * self.profile.sole_penetration_gate_hip_fraction for value in loaded_penetration.values()),
                "loaded_sole_gap_within_gate": all(value <= self.hip_height * self.profile.sole_loaded_gap_gate_hip_fraction for value in loaded_gap.values()),
                "velocity_within_gate": max_velocity <= self.profile.max_joint_velocity_deg_s,
                "acceleration_within_gate": max_acceleration <= self.profile.max_joint_acceleration_deg_s2,
            },
        }
        clip = AnimationClip(
            name=schedule.name, times=times, rotations=rotations_export,
            translations={self.root: root_export}, extras=extras,
            diagnostics=diagnostics, world_matrices=worlds_export,
        ).normalize(exact_loop=schedule.loop and False)

        in_place = None
        if schedule.root_motion:
            rest = self.asset.rest_translation[self.asset.name_to_node[self.root]]
            in_place_root = root_export.copy()
            # Preserve vertical adaptation while stripping horizontal displacement.
            in_place_root[:, 0] = rest[0]
            in_place_root[:, 2] = rest[2]
            in_place_name = schedule.name.replace("_ROOTMOTION", "_INPLACE") if "_ROOTMOTION" in schedule.name else schedule.name + "_INPLACE"
            in_place_extras = {**extras, "rootMotion": False, "recommendedRuntimeSpeedMps": float(np.max(schedule.speeds))}
            in_place = AnimationClip(
                name=in_place_name, times=times.copy(), rotations={n: v.copy() for n, v in rotations_export.items()},
                translations={self.root: in_place_root}, extras=in_place_extras,
                diagnostics={**diagnostics, "derived_from": schedule.name, "in_place": True},
                world_matrices=None,
            ).normalize(exact_loop=schedule.loop)
        return LocomotionResult(clip=clip, in_place_clip=in_place, diagnostics=diagnostics)
