"""Terrain height/normal query surfaces used by the V4 contact solver."""
from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import numpy as np


class TerrainSurface(ABC):
    name: str = "terrain"

    @abstractmethod
    def height_normal(self, point_world: np.ndarray) -> tuple[float, np.ndarray]:
        """Return y height and normalized world-space surface normal at x/z."""

    def heights_normals(self, points_world: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        heights = []
        normals = []
        for point in np.asarray(points_world, dtype=np.float64):
            height, normal = self.height_normal(point)
            heights.append(height)
            normals.append(normal)
        return np.asarray(heights), np.asarray(normals)


@dataclass(frozen=True)
class FlatTerrain(TerrainSurface):
    height: float = 0.0
    name: str = "flat"

    def height_normal(self, point_world: np.ndarray) -> tuple[float, np.ndarray]:
        return float(self.height), np.array([0.0, 1.0, 0.0], dtype=np.float64)

    def heights_normals(self, points_world: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        count = len(points_world)
        return np.full(count, self.height, dtype=np.float64), np.repeat(np.array([[0.0, 1.0, 0.0]], dtype=np.float64), count, axis=0)


@dataclass(frozen=True)
class PlaneTerrain(TerrainSurface):
    origin: np.ndarray
    normal: np.ndarray
    name: str = "plane"

    def __post_init__(self) -> None:
        object.__setattr__(self, "origin", np.asarray(self.origin, dtype=np.float64))
        normal = np.asarray(self.normal, dtype=np.float64)
        normal /= max(np.linalg.norm(normal), 1e-12)
        if normal[1] < 0.0:
            normal *= -1.0
        object.__setattr__(self, "normal", normal)

    @classmethod
    def from_slopes(cls, forward_slope: float = 0.0, lateral_slope: float = 0.0, height: float = 0.0) -> "PlaneTerrain":
        normal = np.array([-lateral_slope, 1.0, -forward_slope], dtype=np.float64)
        return cls(origin=np.array([0.0, height, 0.0]), normal=normal, name="slope")

    def height_normal(self, point_world: np.ndarray) -> tuple[float, np.ndarray]:
        point = np.asarray(point_world, dtype=np.float64)
        # n dot (p-origin)=0, solve y.
        y = self.origin[1] - (
            self.normal[0] * (point[0] - self.origin[0])
            + self.normal[2] * (point[2] - self.origin[2])
        ) / max(self.normal[1], 1e-9)
        return float(y), self.normal.copy()

    def heights_normals(self, points_world: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        points = np.asarray(points_world, dtype=np.float64)
        heights = self.origin[1] - (
            self.normal[0] * (points[:, 0] - self.origin[0])
            + self.normal[2] * (points[:, 2] - self.origin[2])
        ) / max(self.normal[1], 1e-9)
        normals = np.repeat(self.normal[None, :], len(points), axis=0)
        return heights, normals


@dataclass(frozen=True)
class ProceduralTerrain(TerrainSurface):
    amplitude: float = 0.05
    wavelength: float = 1.6
    secondary_amplitude: float = 0.018
    secondary_wavelength: float = 0.72
    phase: float = 0.35
    name: str = "uneven"

    def _height_gradient(self, x: float, z: float) -> tuple[float, float, float]:
        k1 = 2.0 * math.pi / max(self.wavelength, 1e-6)
        k2 = 2.0 * math.pi / max(self.secondary_wavelength, 1e-6)
        a = self.amplitude
        b = self.secondary_amplitude
        h = a * math.sin(k1 * z + self.phase) * math.cos(0.43 * k1 * x)
        h += b * math.sin(k2 * (z + 0.37 * x) - 0.6)
        dhdx = a * math.sin(k1 * z + self.phase) * (-0.43 * k1 * math.sin(0.43 * k1 * x))
        dhdx += b * math.cos(k2 * (z + 0.37 * x) - 0.6) * k2 * 0.37
        dhdz = a * math.cos(k1 * z + self.phase) * k1 * math.cos(0.43 * k1 * x)
        dhdz += b * math.cos(k2 * (z + 0.37 * x) - 0.6) * k2
        return h, dhdx, dhdz

    def height_normal(self, point_world: np.ndarray) -> tuple[float, np.ndarray]:
        point = np.asarray(point_world, dtype=np.float64)
        h, dx, dz = self._height_gradient(float(point[0]), float(point[2]))
        normal = np.array([-dx, 1.0, -dz], dtype=np.float64)
        normal /= max(np.linalg.norm(normal), 1e-12)
        return float(h), normal

    def heights_normals(self, points_world: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        points = np.asarray(points_world, dtype=np.float64)
        x = points[:, 0]
        z = points[:, 2]
        k1 = 2.0 * math.pi / max(self.wavelength, 1e-6)
        k2 = 2.0 * math.pi / max(self.secondary_wavelength, 1e-6)
        h = self.amplitude * np.sin(k1 * z + self.phase) * np.cos(0.43 * k1 * x)
        h += self.secondary_amplitude * np.sin(k2 * (z + 0.37 * x) - 0.6)
        dx = self.amplitude * np.sin(k1 * z + self.phase) * (-0.43 * k1 * np.sin(0.43 * k1 * x))
        dx += self.secondary_amplitude * np.cos(k2 * (z + 0.37 * x) - 0.6) * k2 * 0.37
        dz = self.amplitude * np.cos(k1 * z + self.phase) * k1 * np.cos(0.43 * k1 * x)
        dz += self.secondary_amplitude * np.cos(k2 * (z + 0.37 * x) - 0.6) * k2
        normals = np.stack([-dx, np.ones_like(dx), -dz], axis=1)
        normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
        return h, normals
