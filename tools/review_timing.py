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


def native_still_times(duration_s: float, requested: list[float]) -> list[float]:
    """Validate a small, explicit set of source seconds for still diagnosis."""
    if (isinstance(duration_s, bool) or not isinstance(duration_s, Real)
        or not math.isfinite(duration_s) or not 0 < duration_s <= 60
        or not isinstance(requested, list) or not 1 <= len(requested) <= 12):
        raise ValueError('invalid native still duration or requested times')
    result = []
    for value in requested:
        if (isinstance(value, bool) or not isinstance(value, Real)
            or not math.isfinite(value) or not 0 <= value <= duration_s):
            raise ValueError('native still time lies outside the source interval')
        result.append(float(value))
    if any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError('native still times must be unique and strictly increasing')
    return result
