"""Loop-safe easing and gait-event curves."""
from __future__ import annotations

import math
import numpy as np


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def smoothstep(value: float) -> float:
    x = clamp01(value)
    return x * x * (3.0 - 2.0 * x)


def minimum_jerk(value: float) -> float:
    """Quintic interpolation with zero velocity and acceleration at both ends."""
    x = clamp01(value)
    return x**3 * (10.0 + x * (-15.0 + 6.0 * x))


def minimum_jerk_derivative(value: float) -> float:
    x = clamp01(value)
    return 30.0 * x * x * (1.0 - x) * (1.0 - x)


def minimum_jerk_second_derivative(value: float) -> float:
    x = clamp01(value)
    return 60.0 * x * (1.0 - x) * (1.0 - 2.0 * x)


def smooth_bump(value: float) -> float:
    """C2-continuous bump: zero value/velocity/acceleration at 0 and 1."""
    x = clamp01(value)
    return 64.0 * x**3 * (1.0 - x) ** 3


def raised_cosine(value: float) -> float:
    x = clamp01(value)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def cyclic_distance(a: float, b: float, period: float = 1.0) -> float:
    return ((a - b + period * 0.5) % period) - period * 0.5


def cyclic_gaussian(phase: float, center: float, width: float, period: float = 1.0) -> float:
    distance = cyclic_distance(phase, center, period)
    return math.exp(-0.5 * (distance / width) ** 2)


def blend_segment(value: float, start: float, end: float) -> float:
    if end <= start:
        raise ValueError("blend_segment requires end > start")
    return minimum_jerk((value - start) / (end - start))


def c2_piecewise(values: np.ndarray, knots: list[tuple[float, float]]) -> np.ndarray:
    """Interpolate scalar knots with minimum-jerk segments.

    Knots must be sorted and cover the requested values. This is not a general spline;
    it is an animation helper whose segment boundaries have zero velocity/acceleration.
    """
    points = np.asarray(values, dtype=np.float64)
    output = np.empty_like(points)
    if len(knots) < 2:
        raise ValueError("At least two knots are required")
    for index, point in np.ndenumerate(points):
        if point <= knots[0][0]:
            output[index] = knots[0][1]
            continue
        if point >= knots[-1][0]:
            output[index] = knots[-1][1]
            continue
        for (t0, y0), (t1, y1) in zip(knots, knots[1:]):
            if t0 <= point <= t1:
                mix = minimum_jerk((float(point) - t0) / (t1 - t0))
                output[index] = y0 + (y1 - y0) * mix
                break
    return output
