#!/usr/bin/env python3
"""Fast deterministic unit tests for the Eonwild procedural-animation V4 core."""
from __future__ import annotations

import math
import sys
from pathlib import Path
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v3.rig import AnatomicalBasis
from eonproc_v4.clip import AnimationClip
from eonproc_v4.path import ArcPath, StraightPath, EasedArcPath
from eonproc_v4.profile import BipedV4Profile
from eonproc_v4.terrain import FlatTerrain, PlaneTerrain, ProceduralTerrain
from eonproc_v4.transitions import pose_transition, phase_matched_loop_transition


class TerrainTests(unittest.TestCase):
    def test_flat_height_and_normal(self) -> None:
        terrain = FlatTerrain(1.25)
        points = np.array([[0.0, -3.0, 0.0], [2.0, 8.0, -5.0]])
        heights, normals = terrain.heights_normals(points)
        np.testing.assert_allclose(heights, [1.25, 1.25])
        np.testing.assert_allclose(normals, [[0, 1, 0], [0, 1, 0]])

    def test_plane_is_consistent(self) -> None:
        terrain = PlaneTerrain.from_slopes(forward_slope=0.1, lateral_slope=-0.04, height=0.3)
        point = np.array([0.8, 99.0, 2.1])
        height, normal = terrain.height_normal(point)
        self.assertAlmostEqual(float(np.linalg.norm(normal)), 1.0, places=10)
        np.testing.assert_allclose(np.dot(normal, np.array([point[0], height, point[2]]) - terrain.origin), 0.0, atol=1e-10)

    def test_procedural_vectorized_matches_scalar(self) -> None:
        terrain = ProceduralTerrain(amplitude=0.06, wavelength=1.7, secondary_amplitude=0.011)
        points = np.array([[0.0, 0.0, 0.0], [0.43, 0.0, 1.21], [-0.51, 0.0, 3.7]])
        heights, normals = terrain.heights_normals(points)
        for index, point in enumerate(points):
            h, n = terrain.height_normal(point)
            self.assertAlmostEqual(float(heights[index]), h, places=11)
            np.testing.assert_allclose(normals[index], n, atol=1e-11)
            self.assertAlmostEqual(float(np.linalg.norm(n)), 1.0, places=10)


class PathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.basis = AnatomicalBasis(
            lateral=np.array([1.0, 0.0, 0.0]),
            up=np.array([0.0, 1.0, 0.0]),
            forward=np.array([0.0, 0.0, 1.0]),
        )
        self.origin = np.array([0.0, 0.0, 0.0])

    def test_straight_path(self) -> None:
        frame = StraightPath(self.origin, self.basis).frame(2.4)
        np.testing.assert_allclose(frame.position, [0.0, 0.0, 2.4])
        self.assertEqual(frame.heading_radians, 0.0)

    def test_arc_preserves_radius_and_heading(self) -> None:
        radius = 3.0
        distance = math.pi * radius / 2.0
        path = ArcPath(self.origin, self.basis, radius=radius, sign=1.0)
        frame = path.frame(distance)
        self.assertAlmostEqual(frame.heading_radians, -math.pi / 2.0, places=10)
        center = self.origin - self.basis.lateral * radius
        self.assertAlmostEqual(float(np.linalg.norm(frame.position - center)), radius, places=10)
        self.assertAlmostEqual(float(np.linalg.norm(frame.basis.forward)), 1.0, places=10)
        self.assertAlmostEqual(float(np.dot(frame.basis.forward, frame.basis.lateral)), 0.0, places=10)

    def test_eased_arc_has_straight_extensions_and_exact_heading(self) -> None:
        path = EasedArcPath(
            self.origin, self.basis, total_distance=4.0,
            angle_radians=math.radians(35.0), table_samples=513,
        )
        before = path.frame(-0.5)
        start = path.frame(0.0)
        finish = path.frame(4.0)
        after = path.frame(4.5)
        self.assertAlmostEqual(start.heading_radians, 0.0, places=10)
        self.assertAlmostEqual(finish.heading_radians, -math.radians(35.0), places=8)
        np.testing.assert_allclose(before.position, start.position - self.basis.forward * 0.5, atol=2e-6)
        np.testing.assert_allclose(after.position, finish.position + finish.basis.forward * 0.5, atol=2e-6)
        for frame in (before, start, finish, after):
            basis = np.column_stack([frame.basis.lateral, frame.basis.up, frame.basis.forward])
            np.testing.assert_allclose(basis.T @ basis, np.eye(3), atol=1e-9)

    def test_eased_arc_heading_velocity_starts_and_ends_near_zero(self) -> None:
        path = EasedArcPath(self.origin, self.basis, 4.0, math.radians(35.0), table_samples=1025)
        eps = 1e-3
        start_rate = (path.frame(eps).heading_radians - path.frame(0.0).heading_radians) / eps
        end_rate = (path.frame(4.0).heading_radians - path.frame(4.0 - eps).heading_radians) / eps
        self.assertLess(abs(start_rate), 1e-4)
        self.assertLess(abs(end_rate), 1e-4)


class ClipAndTransitionTests(unittest.TestCase):
    def _clip(self, name: str, angle_degrees: float, root_z: float = 0.0, loop: bool = True) -> AnimationClip:
        times = np.array([0.0, 0.5, 1.0])
        angles = np.radians([0.0, angle_degrees * 0.5, angle_degrees])
        rotations = Rotation.from_rotvec(np.column_stack([angles, np.zeros(3), np.zeros(3)])).as_quat()
        translations = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, root_z * 0.5], [0.0, 0.0, root_z]])
        return AnimationClip(
            name=name,
            times=times,
            rotations={"bone": rotations},
            translations={"root": translations},
            extras={"loop": loop, "rootMotion": False},
        ).normalize(exact_loop=False)

    def test_loop_normalization_closes_non_root_motion(self) -> None:
        clip = self._clip("loop", 30.0)
        clip.normalize(exact_loop=True)
        np.testing.assert_allclose(clip.rotations["bone"][0], clip.rotations["bone"][-1], atol=1e-12)
        np.testing.assert_allclose(clip.translations["root"][0], clip.translations["root"][-1], atol=1e-12)

    def test_pose_transition_exact_endpoints(self) -> None:
        source = self._clip("source", 12.0, loop=False)
        target = self._clip("target", -28.0, loop=False)
        transition = pose_transition("blend", source, target, 0.8, 60, 0.0, 1.0, "root")
        np.testing.assert_allclose(transition.rotations["bone"][0], source.rotations["bone"][0], atol=1e-10)
        # Quaternion sign may differ, compare rotations.
        relative = Rotation.from_quat(transition.rotations["bone"][-1]).inv() * Rotation.from_quat(target.rotations["bone"][-1])
        self.assertLess(float(np.linalg.norm(relative.as_rotvec())), 1e-9)
        self.assertEqual(len(transition.times), 49)

    def test_phase_matched_transition_is_finite(self) -> None:
        source = self._clip("source", 18.0)
        target = self._clip("target", -12.0)
        transition = phase_matched_loop_transition("phase", source, target, 1.0, 60, "root")
        self.assertEqual(len(transition.times), 61)
        self.assertTrue(np.all(np.isfinite(transition.rotations["bone"])))
        self.assertTrue(transition.extras["transition"])


class ProfileTests(unittest.TestCase):
    def test_reference_fitted_defaults(self) -> None:
        profile = BipedV4Profile()
        self.assertAlmostEqual(profile.cycle_hz, 0.45)
        self.assertEqual(profile.export_sample_hz, 60)
        self.assertGreaterEqual(profile.sole_max_vertices_per_side, profile.sole_min_vertices_per_side)
        self.assertLess(profile.sole_penetration_gate_hip_fraction, profile.sole_loaded_gap_gate_hip_fraction)
        self.assertGreater(profile.bite_jaw_open_deg, profile.eating_jaw_open_deg)
        self.assertGreater(profile.roar_jaw_open_deg, profile.bite_jaw_open_deg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
