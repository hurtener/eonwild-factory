"""Clock contracts shared by native review and FBX diagnostic transport.

The package clock, rather than an importer-selected Action range, owns every
preview/export endpoint.  A transport may be re-based at zero for an FBX
consumer, but it is never scaled, clipped, or extended to do so.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real


SOURCE_FPS = 120


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f'invalid {label}')
    return float(value)


@dataclass(frozen=True)
class TransportClock:
    """An exact source interval and a zero-based FBX transport interval."""

    source_start_frame: float
    source_end_frame: float
    duration_s: float
    source_fps: int = SOURCE_FPS

    @property
    def duration_frames(self) -> float:
        return self.duration_s * self.source_fps

    @property
    def transport_start_frame(self) -> float:
        return 0.0

    @property
    def transport_end_frame(self) -> float:
        return self.duration_frames

    @property
    def bake_step_frames(self) -> float:
        """A step no larger than one source frame that includes the endpoint.

        Blender's FBX baker otherwise stops at the previous integral source
        frame when a valid clip ends between source ticks.  This changes only
        sampling density; transport key times retain their exact source clock.
        """
        return self.duration_frames / math.ceil(self.duration_frames)

    def receipt(self) -> dict[str, float | int | str]:
        return {
            'source_fps': self.source_fps,
            'source_frame_start': self.source_start_frame,
            'source_frame_end': self.source_end_frame,
            'source_duration_s': self.duration_s,
            'transport_frame_start': self.transport_start_frame,
            'transport_frame_end': self.transport_end_frame,
            'transport_duration_s': self.duration_s,
            'bake_step_frames': self.bake_step_frames,
            'endpoint_policy': 'exact declared endpoint; no retime, truncation, or held sample',
        }


def transport_clock(source_start_frame: object, source_end_frame: object,
                    duration_s: object, source_fps: object = SOURCE_FPS) -> TransportClock:
    """Validate imported coverage against the declared duration and re-base it.

    A tiny numerical tolerance only covers GLTF/Blender float conversion. It
    never rounds the transport endpoint, treats a nearby source frame as the
    terminal pose, or permits an NLA time-scale correction.
    """
    start = _number(source_start_frame, 'source frame start')
    end = _number(source_end_frame, 'source frame end')
    duration = _number(duration_s, 'source duration')
    if duration <= 0:
        raise ValueError('invalid source duration')
    if isinstance(source_fps, bool) or type(source_fps) is not int or not 1 <= source_fps <= 1000:
        raise ValueError('invalid source frame rate')
    if end <= start:
        raise ValueError('source action has no positive duration')
    expected = duration * source_fps
    actual = end - start
    if abs(actual - expected) > 64 * math.ulp(max(1.0, abs(actual), abs(expected))):
        raise ValueError(f'imported duration changed: {actual / source_fps} != {duration}')
    return TransportClock(start, end, duration, source_fps)
