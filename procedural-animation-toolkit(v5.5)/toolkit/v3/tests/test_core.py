"""Pure unit tests for Eonwild procedural animation toolkit v3.

Run from v3/:
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

from eonproc_v3.curves import (
    c2_piecewise,
    minimum_jerk,
    minimum_jerk_derivative,
    minimum_jerk_second_derivative,
    smooth_bump,
)
from eonproc_v3.profile import BipedV3Profile
from eonproc_v3.generator import _signed_turn, _wrap_angle


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


class ConstraintMathTests(unittest.TestCase):
    def test_signed_turn_does_not_mutate_vectors(self) -> None:
        first = np.array([0.0, -2.0, 1.0], dtype=np.float64)
        second = np.array([0.0, -1.5, -1.0], dtype=np.float64)
        before_first = first.copy()
        before_second = second.copy()
        value = _signed_turn(first, second, np.array([1.0, 0.0, 0.0]))
        self.assertTrue(math.isfinite(value))
        np.testing.assert_array_equal(first, before_first)
        np.testing.assert_array_equal(second, before_second)

    def test_wrap_angle_range(self) -> None:
        for value in np.linspace(-20.0, 20.0, 101):
            wrapped = _wrap_angle(float(value))
            self.assertGreaterEqual(wrapped, -math.pi)
            self.assertLess(wrapped, math.pi)


class ProfileTests(unittest.TestCase):
    def test_default_quality_rates(self) -> None:
        profile = BipedV3Profile()
        self.assertGreaterEqual(profile.internal_sample_hz, 120)
        self.assertGreaterEqual(profile.export_sample_hz, 60)
        self.assertEqual(profile.internal_sample_hz % profile.export_sample_hz, 0)
        self.assertGreater(profile.supercycle_count, 1)

    def test_joint_ranges_never_include_reverse_bend(self) -> None:
        profile = BipedV3Profile()
        self.assertGreater(profile.knee_min_flex_deg, 0.0)
        self.assertGreater(profile.ankle_min_flex_deg, 0.0)
        self.assertGreater(profile.knee_max_flex_deg, profile.knee_min_flex_deg)
        self.assertGreater(profile.ankle_max_flex_deg, profile.ankle_min_flex_deg)

    def test_relaxed_walk_and_soft_tail_defaults(self) -> None:
        profile = BipedV3Profile()
        self.assertLessEqual(profile.cycle_hz, 0.55)
        self.assertGreaterEqual(profile.stance_fraction, 0.70)
        self.assertLess(profile.body_lean_deg, 0.0)
        self.assertLess(profile.tail_stiffness_tip, profile.tail_stiffness_root)
        self.assertGreater(profile.tail_dynamic_limit_tip_deg, profile.tail_dynamic_limit_root_deg)
        self.assertGreater(profile.tail_neutral_sag_deg, 0.0)


if __name__ == "__main__":
    unittest.main()
