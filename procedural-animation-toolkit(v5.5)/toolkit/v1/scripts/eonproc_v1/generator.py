"""Legacy phase-shaped FK biped kernel preserved for v1 comparisons."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np

from .gltf_io import GlbAsset, quaternion_continuity
from .rig import AnatomicalBasis, Pose, SemanticMap, distribute_chain_rotation
from .curves import smooth_bump, cyclic_gaussian


@dataclass(frozen=True)
class LegacyProfile:
    cycle_hz: float = 0.58
    hip_swing_deg: float = 28.0
    stance_fraction: float = 0.68
    stance_knee_deg: float = 18.0
    swing_knee_deg: float = 56.0
    ankle_lift_deg: float = 18.0
    heel_strike_deg: float = 7.0
    toe_push_deg: float = 18.0
    pelvis_yaw_deg: float = 4.0
    pelvis_roll_deg: float = 3.2
    pelvis_pitch_deg: float = 1.8
    body_lean_deg: float = 5.0
    tail_yaw_deg: float = 6.8
    tail_lag_cycles: float = 0.045
    arm_swing_deg: float = 4.0
    sample_hz: int = 30


class LegacyBipedGenerator:
    def __init__(self, asset: GlbAsset, semantics: SemanticMap, profile: LegacyProfile | None = None):
        self.asset = asset
        self.semantics = semantics
        self.profile = profile or LegacyProfile()
        self.basis = AnatomicalBasis.gltf_y_up(asset, semantics)
        self.pelvis = semantics.bone("pelvis")
        self.root = semantics.bone("root")
        self.head = semantics.bone("head")
        self.spine = [semantics.bone(f"spine_{i:02d}") for i in range(1, 6)] + [semantics.bone("chest")]
        self.neck = [semantics.bone(f"neck_{i:02d}") for i in range(1, 6)]
        self.tail = [semantics.bone(f"tail_{i:02d}") for i in range(1, 10)]
        self.legs = {
            side: {
                "thigh": semantics.bone(f"thigh_{side}"),
                "shin": semantics.bone(f"shin_{side}"),
                "ankle": semantics.bone(f"ankle_{side}"),
                "foot": semantics.bone(f"foot_{side}"),
                "toes": [semantics.bone(f"toe_{side}"), semantics.bone(f"toe_2_{side}"), semantics.bone(f"toe_3_{side}")],
            }
            for side in ("l", "r")
        }
        self.arms = {
            side: [semantics.bone(f"arm_{side}"), semantics.bone(f"forearm_{side}")]
            for side in ("l", "r")
        }
        names = {self.pelvis, self.head, *self.spine, *self.neck, *self.tail}
        for side in ("l", "r"):
            names.update([self.legs[side]["thigh"], self.legs[side]["shin"], self.legs[side]["ankle"], self.legs[side]["foot"], *self.legs[side]["toes"], *self.arms[side]])
        self.driven_bones = sorted(names, key=lambda n: asset.name_to_node[n])
        self.duration = 1.0 / self.profile.cycle_hz

    def pose_at_phase(self, phase: float) -> Pose:
        p = phase % 1.0
        pose = Pose(self.asset)
        single = math.sin(2.0 * math.pi * p)
        double = math.cos(4.0 * math.pi * p)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.up, math.radians(self.profile.pelvis_yaw_deg) * single)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.forward, math.radians(self.profile.pelvis_roll_deg) * single)
        pose.rotate_world_rest_axis(self.pelvis, self.basis.lateral, math.radians(self.profile.pelvis_pitch_deg) * double)
        distribute_chain_rotation(pose, self.spine, self.basis.up, -math.radians(self.profile.pelvis_yaw_deg) * single * 0.62)
        distribute_chain_rotation(pose, self.spine, self.basis.forward, -math.radians(self.profile.pelvis_roll_deg) * single * 0.55)
        distribute_chain_rotation(pose, self.spine, self.basis.lateral, math.radians(self.profile.body_lean_deg) - math.radians(self.profile.pelvis_pitch_deg) * double * 0.35)
        distribute_chain_rotation(pose, self.neck, self.basis.up, math.radians(self.profile.pelvis_yaw_deg) * single * 0.48)
        distribute_chain_rotation(pose, self.neck, self.basis.forward, math.radians(self.profile.pelvis_roll_deg) * single * 0.48)
        pose.rotate_world_rest_axis(self.head, self.basis.up, -math.radians(self.profile.pelvis_yaw_deg) * single * 0.62)
        pose.rotate_world_rest_axis(self.head, self.basis.forward, -math.radians(self.profile.pelvis_roll_deg) * single * 0.62)

        for side, offset in (("l", 0.0), ("r", 0.5)):
            q = (p + offset) % 1.0
            stance = self.profile.stance_fraction
            swing_u = 0.0 if q < stance else (q - stance) / (1.0 - stance)
            swing = smooth_bump(swing_u) ** 0.65 if q >= stance else 0.0
            toe_off = cyclic_gaussian(q, stance, 0.055)
            heel = cyclic_gaussian(q, 0.0, 0.05)
            hip = math.radians(self.profile.hip_swing_deg) * math.cos(2.0 * math.pi * q)
            knee = math.radians(self.profile.stance_knee_deg + (self.profile.swing_knee_deg - self.profile.stance_knee_deg) * swing)
            ankle = math.radians(-0.28 * math.degrees(hip) + self.profile.ankle_lift_deg * swing - 0.35 * self.profile.toe_push_deg * toe_off)
            foot = math.radians(self.profile.heel_strike_deg * heel - self.profile.toe_push_deg * toe_off + 0.35 * self.profile.ankle_lift_deg * swing)
            toe = math.radians(self.profile.toe_push_deg * toe_off - 0.18 * self.profile.toe_push_deg * swing)
            leg = self.legs[side]
            pose.rotate_world_rest_axis(leg["thigh"], -self.basis.lateral, hip)
            pose.rotate_world_rest_axis(leg["shin"], self.basis.lateral, knee)
            pose.rotate_world_rest_axis(leg["ankle"], -self.basis.lateral, ankle)
            pose.rotate_world_rest_axis(leg["foot"], -self.basis.lateral, foot)
            for toe_bone in leg["toes"]:
                pose.rotate_world_rest_axis(toe_bone, self.basis.lateral, toe * 0.65)

        for index, bone in enumerate(self.tail):
            wave = math.sin(2.0 * math.pi * ((p + 0.5) - self.profile.tail_lag_cycles * index))
            attenuation = (1.0 - 0.62 * index / max(1, len(self.tail) - 1)) / len(self.tail)
            pose.rotate_world_rest_axis(bone, self.basis.up, math.radians(self.profile.tail_yaw_deg) * wave * attenuation)
        arm = math.radians(self.profile.arm_swing_deg) * single
        pose.rotate_world_rest_axis(self.arms["l"][0], -self.basis.lateral, -arm)
        pose.rotate_world_rest_axis(self.arms["r"][0], -self.basis.lateral, arm)
        pose.rotate_world_rest_axis(self.arms["l"][1], self.basis.lateral, abs(arm) * 0.3)
        pose.rotate_world_rest_axis(self.arms["r"][1], self.basis.lateral, abs(arm) * 0.3)
        return pose

    def generate(self) -> dict[str, Any]:
        count = int(round(self.duration * self.profile.sample_hz)) + 1
        times = np.linspace(0.0, self.duration, count)
        rotations = {name: [] for name in self.driven_bones}
        for time in times:
            pose = self.pose_at_phase(time / self.duration)
            for name in self.driven_bones:
                rotations[name].append(pose.quaternion(name))
        arrays = {name: quaternion_continuity(np.asarray(values)) for name, values in rotations.items()}
        for values in arrays.values():
            values[-1] = values[0]
        return {"times": times, "rotations": arrays}
