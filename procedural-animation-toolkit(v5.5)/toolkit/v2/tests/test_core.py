"""Pure unit tests for the Eonwild procedural animation v2 package.

Run from v2/:
    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eonproc_v2.curves import (
    c2_piecewise,
    minimum_jerk,
    minimum_jerk_derivative,
    minimum_jerk_second_derivative,
    smooth_bump,
)
from eonproc_v2.profile import BipedV2Profile
from eonproc_v2.generator import ContactAwareBipedGenerator


class CurveTests(unittest.TestCase):
    def test_minimum_jerk_boundary_conditions(self) -> None:
        for x, expected in ((0.0, 0.0), (1.0, 1.0)):
            self.assertAlmostEqual(minimum_jerk(x), expected, places=12)
            self.assertAlmostEqual(minimum_jerk_derivative(x), 0.0, places=12)
            self.assertAlmostEqual(minimum_jerk_second_derivative(x), 0.0, places=12)

    def test_minimum_jerk_is_monotonic(self) -> None:
        values = np.array([minimum_jerk(x) for x in np.linspace(0.0, 1.0, 1001)])
        self.assertTrue(np.all(np.diff(values) >= -1e-12))

    def test_smooth_bump_is_c2_at_boundaries(self) -> None:
        self.assertAlmostEqual(smooth_bump(0.0), 0.0, places=12)
        self.assertAlmostEqual(smooth_bump(1.0), 0.0, places=12)
        self.assertAlmostEqual(smooth_bump(0.5), 1.0, places=12)
        epsilon = 1e-5
        self.assertLess(abs((smooth_bump(epsilon) - smooth_bump(0.0)) / epsilon), 1e-6)
        self.assertLess(abs((smooth_bump(1.0) - smooth_bump(1.0 - epsilon)) / epsilon), 1e-6)

    def test_piecewise_hits_knots(self) -> None:
        knots = [(0.0, 2.0), (0.3, -1.0), (1.0, 4.0)]
        values = c2_piecewise(np.array([0.0, 0.3, 1.0]), knots)
        np.testing.assert_allclose(values, [2.0, -1.0, 4.0], atol=1e-12)


class ProfileTests(unittest.TestCase):
    def test_default_quality_rates(self) -> None:
        profile = BipedV2Profile()
        self.assertGreaterEqual(profile.internal_sample_hz, 120)
        self.assertGreaterEqual(profile.export_sample_hz, 60)
        self.assertEqual(profile.internal_sample_hz % profile.export_sample_hz, 0)
        self.assertGreater(profile.supercycle_count, 1)

    def test_fabrik_preserves_lengths_and_reaches_target(self) -> None:
        points = np.array([[0.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, -2.0, 0.0], [0.0, -2.6, 0.0]])
        target = np.array([0.35, -2.15, 0.25])
        solved = ContactAwareBipedGenerator._fabrik_positions(points, target, iterations=30)
        np.testing.assert_allclose(
            np.linalg.norm(np.diff(solved, axis=0), axis=1),
            np.linalg.norm(np.diff(points, axis=0), axis=1),
            atol=1e-9,
        )
        self.assertLess(np.linalg.norm(solved[-1] - target), 1e-5)


if __name__ == "__main__":
    unittest.main()
