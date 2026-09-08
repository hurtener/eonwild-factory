"""Strict reading and sampling of emitted glTF TRS animation channels.

The factory writes LINEAR channels today. This reader also understands the
glTF 2.0 CUBICSPLINE layout so validators and contact sampling never mistake
its three records per key for three ordinary animation keys.
"""
from __future__ import annotations

from dataclasses import dataclass
import bisect
import math
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from .container import Glb


_PATH_WIDTH = {"translation": 3, "rotation": 4, "scale": 3}
_INTERPOLATIONS = {"LINEAR", "CUBICSPLINE"}


def _numbers(value: Any, *, label: str) -> np.ndarray:
    result = np.asarray(value)
    if result.dtype.kind not in "fiu" or not np.isfinite(result).all():
        raise ContractError(f"{label} must contain finite real values")
    return result.astype(float, copy=False)


def _unit_quaternion(value: np.ndarray, *, label: str) -> np.ndarray:
    norm = float(np.linalg.norm(value))
    if not math.isfinite(norm) or norm <= 1.0e-15:
        raise ContractError(f"{label} is zero")
    return value / norm


@dataclass(frozen=True)
class TrsTrack:
    """One fully validated emitted TRS channel.

    Cubic tangents use glTF's units per second. ``values`` deliberately holds
    the serialized value records (not normalized copies), preserving legacy
    LINEAR consumers that read exact key values and normalize rotations at the
    transform boundary.
    """

    times: np.ndarray
    values: np.ndarray
    path: str
    interpolation: str
    in_tangents: np.ndarray | None = None
    out_tangents: np.ndarray | None = None

    def value_at_key(self, index: int) -> np.ndarray:
        if index < 0 or index >= len(self.times):
            raise ContractError("animation key index is outside timeline")
        value = self.values[index].copy()
        return _unit_quaternion(value, label="animation quaternion") if self.path == "rotation" else value

    def derivative_at_key(self, index: int, *, terminal: bool) -> np.ndarray:
        """Return the one-sided derivative at a key in playback coordinates."""
        if index < 0 or index >= len(self.times):
            raise ContractError("animation key index is outside timeline")
        if self.interpolation == "CUBICSPLINE":
            assert self.in_tangents is not None and self.out_tangents is not None
            raw = self.values[index]
            derivative = self.in_tangents[index] if terminal else self.out_tangents[index]
            if self.path != "rotation":
                return derivative.copy()
            # glTF applies the normalized cubic result. Differentiate q/|q|,
            # rather than treating the stored Hermite components as a unit
            # quaternion curve.
            norm = float(np.linalg.norm(raw))
            if norm <= 1.0e-15:
                raise ContractError("animation quaternion is zero")
            unit = raw / norm
            return (derivative - unit * float(np.dot(unit, derivative))) / norm
        neighbor = index - 1 if terminal else index + 1
        if neighbor < 0 or neighbor >= len(self.times):
            raise ContractError("animation key has no adjacent segment")
        duration = abs(float(self.times[index] - self.times[neighbor]))
        if not math.isfinite(duration) or duration <= 0:
            raise ContractError("animation adjacent duration is invalid")
        return ((self.values[index] - self.values[neighbor]) / duration if terminal
                else (self.values[neighbor] - self.values[index]) / duration)

    def sample(self, time_s: float) -> np.ndarray:
        time = float(time_s)
        if not math.isfinite(time):
            raise ContractError("animation sample time must be finite")
        if time <= self.times[0]:
            return self.value_at_key(0)
        if time >= self.times[-1]:
            return self.value_at_key(len(self.times) - 1)
        right = bisect.bisect_right(self.times.tolist(), time)
        left = right - 1
        duration = float(self.times[right] - self.times[left])
        amount = (time - float(self.times[left])) / duration
        if self.interpolation == "LINEAR":
            result = self.values[left] + amount * (self.values[right] - self.values[left])
        else:
            assert self.in_tangents is not None and self.out_tangents is not None
            t2, t3 = amount * amount, amount * amount * amount
            result = (
                (2 * t3 - 3 * t2 + 1) * self.values[left]
                + duration * (t3 - 2 * t2 + amount) * self.out_tangents[left]
                + (-2 * t3 + 3 * t2) * self.values[right]
                + duration * (t3 - t2) * self.in_tangents[right]
            )
        return _unit_quaternion(result, label="interpolated animation quaternion") if self.path == "rotation" else result


def read_trs_sampler(glb: Glb, sampler: Mapping[str, Any], path: str, *, label: str) -> TrsTrack:
    """Read exactly one glTF TRS sampler, rejecting ambiguous layouts."""
    if not isinstance(path, str) or path not in _PATH_WIDTH:
        raise ContractError(f"{label} has unsupported target path")
    interpolation = sampler.get("interpolation", "LINEAR")
    if not isinstance(interpolation, str) or interpolation not in _INTERPOLATIONS:
        raise ContractError(f"{label} interpolation {interpolation!r} is unsupported")
    input_index, output_index = sampler.get("input"), sampler.get("output")
    if (isinstance(input_index, bool) or not isinstance(input_index, int)
            or isinstance(output_index, bool) or not isinstance(output_index, int)):
        raise ContractError(f"{label} sampler accessors are invalid")
    try:
        times = _numbers(glb.accessor_values(input_index), label=f"{label} timestamps")
        raw = _numbers(glb.accessor_values(output_index), label=f"{label} output")
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ContractError(f"{label} sampler accessor data is malformed") from exc
    if times.ndim != 2 or times.shape[1:] != (1,):
        raise ContractError(f"{label} timestamps must be SCALAR rows")
    times = times[:, 0]
    if len(times) < 2 or np.any(np.diff(times) <= 0):
        raise ContractError(f"{label} timeline must be strictly increasing with two keys")
    width = _PATH_WIDTH[path]
    if interpolation == "LINEAR":
        if raw.shape != (len(times), width):
            raise ContractError(f"{label} LINEAR output shape does not match its timeline")
        values, incoming, outgoing = raw, None, None
    else:
        if raw.shape != (3 * len(times), width):
            raise ContractError(f"{label} CUBICSPLINE output must contain in/value/out records for every key")
        grouped = raw.reshape((len(times), 3, width))
        incoming, values, outgoing = grouped[:, 0], grouped[:, 1], grouped[:, 2]
    if path == "rotation" and np.any(np.linalg.norm(values, axis=1) <= 1.0e-15):
        raise ContractError(f"{label} contains a zero quaternion value")
    return TrsTrack(times=times, values=values, path=path, interpolation=interpolation,
                    in_tangents=incoming, out_tangents=outgoing)


def read_animation_tracks(
    glb: Glb,
    animation_name: str,
    *,
    require_common_timeline: bool,
) -> tuple[dict[tuple[int, str], TrsTrack], np.ndarray]:
    """Read a uniquely named TRS animation and reject duplicate targets."""
    animations = glb.document.get("animations", [])
    if not isinstance(animations, list) or any(not isinstance(item, Mapping) for item in animations):
        raise ContractError("animation table must be an array of objects")
    matches = [item for item in animations if item.get("name") == animation_name]
    if len(matches) != 1:
        raise ContractError("animation reader requires exactly one named animation")
    animation = matches[0]
    channels, samplers = animation.get("channels"), animation.get("samplers")
    if not isinstance(channels, list) or not isinstance(samplers, list):
        raise ContractError("animation channels and samplers must be arrays")
    tracks: dict[tuple[int, str], TrsTrack] = {}
    timeline: np.ndarray | None = None
    for channel in channels:
        if not isinstance(channel, Mapping) or not isinstance(channel.get("target"), Mapping):
            raise ContractError("animation channel is malformed")
        target = channel["target"]
        node, path, sampler_index = target.get("node"), target.get("path"), channel.get("sampler")
        if (isinstance(node, bool) or not isinstance(node, int) or node < 0 or node >= len(glb.nodes)
                or not isinstance(path, str) or path not in _PATH_WIDTH
                or isinstance(sampler_index, bool) or not isinstance(sampler_index, int)
                or sampler_index < 0 or sampler_index >= len(samplers)
                or not isinstance(samplers[sampler_index], Mapping)):
            raise ContractError("animation target or sampler is invalid")
        key = (node, path)
        if key in tracks:
            raise ContractError("animation duplicates a node/property channel")
        track = read_trs_sampler(glb, samplers[sampler_index], path, label=f"animation {node}.{path}")
        if timeline is None:
            timeline = track.times
        elif require_common_timeline and not np.array_equal(timeline, track.times):
            raise ContractError("animation channels do not share one timeline")
        tracks[key] = track
    if timeline is None:
        raise ContractError("animation has no TRS channels")
    return tracks, timeline.copy()
