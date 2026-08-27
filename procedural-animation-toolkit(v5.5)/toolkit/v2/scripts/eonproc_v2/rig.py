"""Rig semantics, coordinate inference, and mutable pose operations."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import math

import numpy as np
import yaml
from scipy.spatial.transform import Rotation

from .gltf_io import GlbAsset, matrix_from_trs


@dataclass(frozen=True)
class SemanticMap:
    source_path: Path
    tags: dict[str, str]

    @classmethod
    def load(cls, path: str | Path) -> "SemanticMap":
        source = Path(path)
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
        mappings = payload.get("mappings", {})
        tags = {
            str(tag): str(value["source"] if isinstance(value, dict) else value)
            for tag, value in mappings.items()
        }
        if not tags:
            raise ValueError(f"No mappings found in {source}")
        return cls(source_path=source, tags=tags)

    def require(self, *tags: str) -> None:
        missing = [tag for tag in tags if tag not in self.tags]
        if missing:
            raise KeyError(f"Semantic map is missing required tags: {missing}")

    def bone(self, tag: str) -> str:
        try:
            return self.tags[tag]
        except KeyError as exc:
            raise KeyError(f"Semantic tag {tag!r} is not mapped") from exc

    def existing_bones(self, asset: GlbAsset) -> tuple[list[str], list[str]]:
        mapped = sorted(set(self.tags.values()))
        missing = [name for name in mapped if name not in asset.name_to_node]
        return mapped, missing


@dataclass(frozen=True)
class AnatomicalBasis:
    lateral: np.ndarray
    up: np.ndarray
    forward: np.ndarray

    @classmethod
    def gltf_y_up(cls, asset: GlbAsset, semantics: SemanticMap) -> "AnatomicalBasis":
        """Use glTF's canonical +Y up and infer horizontal forward from pelvis to head."""
        semantics.require("pelvis", "head", "foot_l", "foot_r")
        position = lambda tag: asset.rest_world[asset.name_to_node[semantics.bone(tag)]][:3, 3]
        up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        forward = position("head") - position("pelvis")
        forward -= up * float(np.dot(forward, up))
        forward /= np.linalg.norm(forward)
        lateral = np.cross(up, forward)
        lateral /= np.linalg.norm(lateral)
        if float(np.dot(position("foot_r") - position("foot_l"), lateral)) < 0.0:
            lateral *= -1.0
        forward = np.cross(lateral, up)
        forward /= np.linalg.norm(forward)
        return cls(lateral=lateral, up=up, forward=forward)

    @classmethod
    def infer(cls, asset: GlbAsset, semantics: SemanticMap) -> "AnatomicalBasis":
        semantics.require("pelvis", "head", "foot_l", "foot_r")
        position = lambda tag: asset.rest_world[asset.name_to_node[semantics.bone(tag)]][:3, 3]
        pelvis = position("pelvis")
        head = position("head")
        left_foot = position("foot_l")
        right_foot = position("foot_r")
        foot_mid = 0.5 * (left_foot + right_foot)

        up = pelvis - foot_mid
        up /= np.linalg.norm(up)
        forward = head - pelvis
        forward -= up * float(np.dot(forward, up))
        forward /= np.linalg.norm(forward)
        lateral = np.cross(up, forward)
        lateral /= np.linalg.norm(lateral)
        # Ensure positive lateral points toward the semantic right foot.
        if float(np.dot(right_foot - left_foot, lateral)) < 0.0:
            lateral *= -1.0
        forward = np.cross(lateral, up)
        forward /= np.linalg.norm(forward)
        return cls(lateral=lateral, up=up, forward=forward)


class Pose:
    """Mutable local TRS pose with world-space rotation and CCD helpers."""

    def __init__(self, asset: GlbAsset):
        self.asset = asset
        self.translation = [value.copy() for value in asset.rest_translation]
        self.rotation = [Rotation.from_quat(value.as_quat()) for value in asset.rest_rotation]
        self.scale = [value.copy() for value in asset.rest_scale]
        self._world_matrices: list[np.ndarray] | None = None
        self._world_rotations: list[Rotation] | None = None

    def copy(self) -> "Pose":
        other = object.__new__(Pose)
        other.asset = self.asset
        other.translation = [value.copy() for value in self.translation]
        other.rotation = [Rotation.from_quat(value.as_quat()) for value in self.rotation]
        other.scale = [value.copy() for value in self.scale]
        other._world_matrices = None
        other._world_rotations = None
        return other

    def invalidate(self) -> None:
        self._world_matrices = None
        self._world_rotations = None

    @property
    def local_matrices(self) -> list[np.ndarray]:
        return [
            matrix_from_trs(self.translation[index], self.rotation[index], self.scale[index])
            for index in range(len(self.translation))
        ]

    @property
    def world_matrices(self) -> list[np.ndarray]:
        if self._world_matrices is None:
            self._world_matrices = self.asset.world_matrices(self.local_matrices)
        return self._world_matrices

    @property
    def world_rotations(self) -> list[Rotation]:
        if self._world_rotations is None:
            self._world_rotations = self.asset.world_rotations(self.rotation)
        return self._world_rotations

    def node_index(self, name: str) -> int:
        return self.asset.name_to_node[name]

    def world_position(self, name: str) -> np.ndarray:
        return self.world_matrices[self.node_index(name)][:3, 3].copy()

    def world_rotation(self, name: str) -> Rotation:
        return self.world_rotations[self.node_index(name)]

    def set_local_translation(self, name: str, value: Iterable[float]) -> None:
        self.translation[self.node_index(name)] = np.asarray(value, dtype=np.float64)
        self.invalidate()

    def add_local_translation(self, name: str, delta: Iterable[float]) -> None:
        index = self.node_index(name)
        self.translation[index] += np.asarray(delta, dtype=np.float64)
        self.invalidate()

    def add_world_translation(self, name: str, delta_world: Iterable[float]) -> None:
        index = self.node_index(name)
        parent = self.asset.parents[index]
        delta = np.asarray(delta_world, dtype=np.float64)
        if parent is not None:
            delta = self.world_rotations[parent].inv().apply(delta)
        self.translation[index] += delta
        self.invalidate()

    def add_world_translation_rest(self, name: str, delta_world: Iterable[float]) -> None:
        """Fast translation conversion using the rest parent orientation."""
        index = self.node_index(name)
        parent = self.asset.parents[index]
        delta = np.asarray(delta_world, dtype=np.float64)
        if parent is not None:
            delta = self.asset.rest_world_rotation[parent].inv().apply(delta)
        self.translation[index] += delta
        self.invalidate()

    def set_world_rotation(self, name: str, desired_world: Rotation) -> None:
        index = self.node_index(name)
        parent = self.asset.parents[index]
        parent_world = Rotation.identity() if parent is None else self.world_rotations[parent]
        self.rotation[index] = parent_world.inv() * desired_world
        self.invalidate()

    def rotate_world(self, name: str, axis_world: np.ndarray, angle_radians: float) -> None:
        if abs(angle_radians) < 1e-12:
            return
        axis = np.asarray(axis_world, dtype=np.float64)
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-12:
            return
        delta = Rotation.from_rotvec(axis / axis_norm * angle_radians)
        self.set_world_rotation(name, delta * self.world_rotation(name))

    def rotate_world_rest_axis(self, name: str, axis_world: np.ndarray, angle_radians: float) -> None:
        """Fast additive rotation whose anatomical axis is calibrated in the rest pose.

        This is appropriate for layered procedural motion. IK corrections still use
        rotate_world(), which evaluates the current parent orientation exactly.
        """
        if abs(angle_radians) < 1e-12:
            return
        index = self.node_index(name)
        axis = np.asarray(axis_world, dtype=np.float64)
        axis /= max(np.linalg.norm(axis), 1e-12)
        local_axis = self.asset.rest_world_rotation[index].inv().apply(axis)
        local_axis /= max(np.linalg.norm(local_axis), 1e-12)
        self.rotation[index] = self.rotation[index] * Rotation.from_rotvec(local_axis * angle_radians)
        self.invalidate()

    def rotate_local(self, name: str, axis_local: np.ndarray, angle_radians: float) -> None:
        if abs(angle_radians) < 1e-12:
            return
        index = self.node_index(name)
        axis = np.asarray(axis_local, dtype=np.float64)
        axis /= np.linalg.norm(axis)
        self.rotation[index] = self.rotation[index] * Rotation.from_rotvec(axis * angle_radians)
        self.invalidate()

    def align_child_about_world_axis(
        self,
        joint_name: str,
        end_name: str,
        target_world: np.ndarray,
        axis_world: np.ndarray,
        fraction: float = 1.0,
        max_angle_radians: float = math.radians(12.0),
    ) -> float:
        joint = self.world_position(joint_name)
        current = self.world_position(end_name) - joint
        desired = np.asarray(target_world, dtype=np.float64) - joint
        axis = np.asarray(axis_world, dtype=np.float64)
        axis /= np.linalg.norm(axis)
        current -= axis * float(np.dot(current, axis))
        desired -= axis * float(np.dot(desired, axis))
        cn = np.linalg.norm(current)
        dn = np.linalg.norm(desired)
        if cn < 1e-10 or dn < 1e-10:
            return float(np.linalg.norm(self.world_position(end_name) - target_world))
        current /= cn
        desired /= dn
        sin_value = float(np.dot(axis, np.cross(current, desired)))
        cos_value = float(np.clip(np.dot(current, desired), -1.0, 1.0))
        angle = math.atan2(sin_value, cos_value) * fraction
        angle = float(np.clip(angle, -max_angle_radians, max_angle_radians))
        self.rotate_world(joint_name, axis, angle)
        return float(np.linalg.norm(self.world_position(end_name) - target_world))

    def align_child_direction_world(
        self,
        joint_name: str,
        end_name: str,
        target_world: np.ndarray,
        fraction: float = 1.0,
        max_angle_radians: float = math.radians(12.0),
    ) -> float:
        joint = self.world_position(joint_name)
        end = self.world_position(end_name)
        current = end - joint
        desired = np.asarray(target_world, dtype=np.float64) - joint
        current_norm = np.linalg.norm(current)
        desired_norm = np.linalg.norm(desired)
        if current_norm < 1e-10 or desired_norm < 1e-10:
            return float(desired_norm)
        current /= current_norm
        desired /= desired_norm
        dot = float(np.clip(np.dot(current, desired), -1.0, 1.0))
        angle = math.acos(dot)
        if angle < 1e-9:
            return float(np.linalg.norm(self.world_position(end_name) - target_world))
        axis = np.cross(current, desired)
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-10:
            # Antiparallel vectors: choose a stable perpendicular axis.
            candidate = np.cross(current, np.array([1.0, 0.0, 0.0]))
            if np.linalg.norm(candidate) < 1e-8:
                candidate = np.cross(current, np.array([0.0, 1.0, 0.0]))
            axis = candidate
            axis_norm = np.linalg.norm(axis)
        axis /= axis_norm
        applied = min(angle * fraction, max_angle_radians)
        self.rotate_world(joint_name, axis, applied)
        return float(np.linalg.norm(self.world_position(end_name) - target_world))

    def ccd_solve(
        self,
        joint_names: list[str],
        end_name: str,
        target_world: np.ndarray,
        iterations: int = 12,
        tolerance: float = 1e-4,
        fractions: dict[str, float] | None = None,
        max_step_degrees: dict[str, float] | None = None,
    ) -> float:
        target = np.asarray(target_world, dtype=np.float64)
        fractions = fractions or {}
        max_step_degrees = max_step_degrees or {}
        error = float(np.linalg.norm(self.world_position(end_name) - target))
        for _ in range(iterations):
            if error <= tolerance:
                break
            for joint_name in joint_names:
                error = self.align_child_direction_world(
                    joint_name=joint_name,
                    end_name=end_name,
                    target_world=target,
                    fraction=fractions.get(joint_name, 1.0),
                    max_angle_radians=math.radians(max_step_degrees.get(joint_name, 10.0)),
                )
                if error <= tolerance:
                    break
        return error

    def quaternion(self, name: str) -> np.ndarray:
        return self.rotation[self.node_index(name)].as_quat().copy()


def distribute_chain_rotation(
    pose: Pose,
    chain: list[str],
    axis_world: np.ndarray,
    total_angle: float,
    weights: Iterable[float] | None = None,
) -> None:
    if not chain or abs(total_angle) < 1e-12:
        return
    values = np.ones(len(chain), dtype=np.float64) if weights is None else np.asarray(list(weights), dtype=np.float64)
    if values.shape != (len(chain),):
        raise ValueError("Chain weights do not match chain length")
    total = float(values.sum())
    if total <= 0.0:
        raise ValueError("Chain weights must have positive sum")
    values /= total
    for name, weight in zip(chain, values):
        pose.rotate_world_rest_axis(name, axis_world, total_angle * float(weight))
