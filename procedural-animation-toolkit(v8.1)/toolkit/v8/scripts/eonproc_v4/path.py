"""Root paths and moving anatomical frames for straight and curved locomotion."""
from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import numpy as np
from scipy.spatial.transform import Rotation

from eonproc_v3.rig import AnatomicalBasis


@dataclass(frozen=True)
class PathFrame:
    position: np.ndarray
    heading_radians: float
    basis: AnatomicalBasis


class MotionPath(ABC):
    def __init__(self, origin: np.ndarray, base_basis: AnatomicalBasis):
        self.origin = np.asarray(origin, dtype=np.float64)
        self.base_basis = base_basis

    @abstractmethod
    def frame(self, distance: float) -> PathFrame:
        ...


class StraightPath(MotionPath):
    def frame(self, distance: float) -> PathFrame:
        position = self.origin + self.base_basis.forward * float(distance)
        return PathFrame(position=position, heading_radians=0.0, basis=self.base_basis)


class ArcPath(MotionPath):
    """Horizontal circular arc. Positive total angle turns toward anatomical left."""
    def __init__(self, origin: np.ndarray, base_basis: AnatomicalBasis, radius: float, sign: float):
        super().__init__(origin, base_basis)
        self.radius = max(abs(float(radius)), 1e-5)
        self.sign = 1.0 if sign >= 0.0 else -1.0

    def frame(self, distance: float) -> PathFrame:
        theta = -self.sign * float(distance) / self.radius
        # Positive sign turns toward anatomical left.  The radial vector starts
        # on the creature's right side, so the world-Y rotation must use the
        # opposite sign for the path tangent to point along anatomical forward.
        center = self.origin - self.base_basis.lateral * (self.sign * self.radius)
        radial0 = self.base_basis.lateral * (self.sign * self.radius)
        rotation = Rotation.from_rotvec(np.array([0.0, 1.0, 0.0]) * theta)
        radial = rotation.apply(radial0)
        position = center + radial
        forward = rotation.apply(self.base_basis.forward)
        lateral = rotation.apply(self.base_basis.lateral)
        basis = AnatomicalBasis(lateral=lateral, up=self.base_basis.up.copy(), forward=forward)
        return PathFrame(position=position, heading_radians=theta, basis=basis)


class EasedArcPath(MotionPath):
    """Finite C2-curvature turn with straight extensions before and after.

    Unlike a mathematical circle extended to negative distance, this path keeps
    pre-turn planted contacts aligned with the incoming heading. Curvature ramps
    in and out through a quintic minimum-jerk heading law, preventing a leg from
    inheriting a rotated contact frame before the authored turn has begun.
    Positive ``angle_radians`` means anatomical left, matching ``ArcPath``.
    """

    def __init__(
        self,
        origin: np.ndarray,
        base_basis: AnatomicalBasis,
        total_distance: float,
        angle_radians: float,
        table_samples: int = 2049,
    ):
        super().__init__(origin, base_basis)
        self.total_distance = max(float(total_distance), 1e-5)
        self.anatomical_angle = float(angle_radians)
        self.world_angle = -self.anatomical_angle
        count = max(129, int(table_samples))
        self._distance = np.linspace(0.0, self.total_distance, count)
        u = self._distance / self.total_distance
        blend = u * u * u * (10.0 + u * (-15.0 + 6.0 * u))
        self._heading = self.world_angle * blend
        forwards = np.stack([
            Rotation.from_rotvec(np.array([0.0, 1.0, 0.0]) * heading).apply(self.base_basis.forward)
            for heading in self._heading
        ])
        self._positions = np.empty((count, 3), dtype=np.float64)
        self._positions[0] = self.origin
        delta_s = np.diff(self._distance)
        increments = 0.5 * (forwards[:-1] + forwards[1:]) * delta_s[:, None]
        self._positions[1:] = self.origin + np.cumsum(increments, axis=0)
        self._end_forward = forwards[-1]
        self._end_lateral = Rotation.from_rotvec(
            np.array([0.0, 1.0, 0.0]) * self.world_angle
        ).apply(self.base_basis.lateral)

    def frame(self, distance: float) -> PathFrame:
        value = float(distance)
        if value <= 0.0:
            position = self.origin + self.base_basis.forward * value
            return PathFrame(position=position, heading_radians=0.0, basis=self.base_basis)
        if value >= self.total_distance:
            position = self._positions[-1] + self._end_forward * (value - self.total_distance)
            basis = AnatomicalBasis(
                lateral=self._end_lateral.copy(),
                up=self.base_basis.up.copy(),
                forward=self._end_forward.copy(),
            )
            return PathFrame(position=position, heading_radians=self.world_angle, basis=basis)
        index = int(np.searchsorted(self._distance, value, side="right") - 1)
        index = max(0, min(index, len(self._distance) - 2))
        span = self._distance[index + 1] - self._distance[index]
        mix = (value - self._distance[index]) / max(span, 1e-12)
        position = self._positions[index] * (1.0 - mix) + self._positions[index + 1] * mix
        heading = float(self._heading[index] * (1.0 - mix) + self._heading[index + 1] * mix)
        rotation = Rotation.from_rotvec(np.array([0.0, 1.0, 0.0]) * heading)
        basis = AnatomicalBasis(
            lateral=rotation.apply(self.base_basis.lateral),
            up=self.base_basis.up.copy(),
            forward=rotation.apply(self.base_basis.forward),
        )
        return PathFrame(position=position, heading_radians=heading, basis=basis)
