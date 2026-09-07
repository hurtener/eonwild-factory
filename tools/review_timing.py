"""Native preview clocks, independent of Blender and animation generation."""
from __future__ import annotations

import math
from numbers import Real


def native_sample_times(duration_s: float, fps: int) -> list[float]:
    """Sample [0, duration) without a floating-point duplicate endpoint.

    Only an ULP-sized arithmetic remainder in the *frame count* is normalized.
    Source time, motion speed and clip duration are never rescaled. A one-shot's
    exact terminal pose is rendered separately, not held for an invented frame.
    """
    if (isinstance(duration_s, bool) or not isinstance(duration_s, Real)
        or not math.isfinite(duration_s) or not 0 < duration_s <= 60
        or type(fps) is not int or not 12 <= fps <= 120):
        raise ValueError('invalid native review duration or frame rate')
    frames = float(duration_s) * fps
    nearest = round(frames)
    if abs(frames - nearest) <= 8 * math.ulp(max(1., frames)):
        frames = float(nearest)
    count = max(1, math.ceil(frames))
    return [index / fps for index in range(count)]
