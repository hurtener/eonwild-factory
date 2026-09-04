"""Minimal offline-to-runtime contract: events and plan interpolation.

Factory/offline owns mass estimation, trajectory solve, contact schedule,
whole-body IK, validation renders and baking. Runtime owns selection,
parameterization, phase-preserving blends, bounded terrain/contact IK and
event dispatch. This module is the seam between them:

* :class:`Event` — point (``L_FOOT_CONTACT``), window
  (``HEAD_TARGET_WINDOW``) and condition (``CONTACT_MISSED``) vocabulary;
* :class:`RuntimeTrack` — interruptibility as phase/window state
  (``NON_INTERRUPTIBLE`` windows), loop-safety queries, deterministic
  dispatch for gameplay/audio/particles;
* :func:`interpolate_com_plans` — parameterize between compatible baked
  plans preserving phase and COM velocity (cubic Hermite), so runtime
  never re-solves dynamics in the browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from .centroidal import _finite

POINT = "point"
WINDOW = "window"
CONDITION = "condition"

NON_INTERRUPTIBLE = "NON_INTERRUPTIBLE"


@dataclass(frozen=True)
class Event:
    name: str
    kind: str  # point | window_start | window_end | condition
    time_s: float
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ContractError("event name must be a non-empty string")
        if self.kind not in (POINT, "window_start", "window_end", CONDITION):
            raise ContractError(f"event kind {self.kind!r} is unsupported")
        _finite(self.time_s, label=f"event {self.name} time_s")
        if self.time_s < 0.0:
            raise ContractError("event time must be non-negative")


@dataclass
class RuntimeTrack:
    """Deterministic runtime event track baked offline, dispatched live."""

    duration_s: float
    events: list[Event] = field(default_factory=list)
    windows: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        _finite(self.duration_s, label="track duration")
        if self.duration_s <= 0.0:
            raise ContractError("track duration must be positive")

    def add_window(self, name: str, start_s: float, end_s: float) -> None:
        start, end = _finite(start_s, label="window start"), _finite(end_s, label="window end")
        if not 0.0 <= start < end <= self.duration_s:
            raise ContractError(f"window {name!r} is outside the track")
        if not name:
            raise ContractError("window name must be non-empty")
        self.windows.append({"name": name, "start_s": start, "end_s": end})

    def active_windows(self, time_s: float) -> list[str]:
        t = _finite(time_s, label="query time")
        return sorted(w["name"] for w in self.windows if w["start_s"] <= t <= w["end_s"])

    def interruptible(self, time_s: float) -> bool:
        return NON_INTERRUPTIBLE not in self.active_windows(time_s)

    def dispatch(self, previous_s: float, current_s: float) -> list[Event]:
        """Events due in (previous, current]: gameplay/audio/particle cues."""
        prev, curr = _finite(previous_s, label="previous"), _finite(current_s, label="current")
        if not 0.0 <= prev <= curr <= self.duration_s:
            raise ContractError("dispatch window is out of range")
        due = [e for e in self.events if prev < e.time_s <= curr]
        return sorted(due, key=lambda e: (e.time_s, e.name))

    def loop_safe(self) -> dict[str, Any]:
        """Loop seam check: first/last windows and conditions must agree."""
        opening = self.active_windows(0.0)
        closing = self.active_windows(self.duration_s)
        return {
            "seam_windows_match": opening == closing,
            "opening": opening,
            "closing": closing,
            "event_count": len(self.events),
        }


def interpolate_com_plans(
    plan_a: Sequence[Mapping[str, Any]],
    plan_b: Sequence[Mapping[str, Any]],
    *,
    alpha: float,
) -> list[dict[str, Any]]:
    """Blend two compatible baked COM plans preserving phase and velocity.

    Plans must share sample count and timestamps (same phase grid —
    runtime parameterizes, it never retimes). Positions blend linearly;
    velocities blend linearly (both endpoints already C1 inside their own
    plans, so the blend preserves the velocity channel instead of
    differentiating the blended positions and inventing motion).
    """
    blend = _finite(alpha, label="alpha")
    if not 0.0 <= blend <= 1.0:
        raise ContractError("blend alpha must lie in [0, 1]")
    if len(plan_a) != len(plan_b) or not plan_a:
        raise ContractError("runtime interpolation needs two non-empty equal plans")
    out = []
    for a, b in zip(plan_a, plan_b):
        if abs(float(a["time_s"]) - float(b["time_s"])) > 1e-9:
            raise ContractError("runtime plans must share the phase grid")
        pa, pb = np.asarray(a["com_m"], dtype=float), np.asarray(b["com_m"], dtype=float)
        va, vb = np.asarray(a["com_velocity_mps"], dtype=float), np.asarray(b["com_velocity_mps"], dtype=float)
        out.append(
            {
                "time_s": float(a["time_s"]),
                "com_m": [float(v) for v in (1 - blend) * pa + blend * pb],
                "com_velocity_mps": [float(v) for v in (1 - blend) * va + blend * vb],
            }
        )
    return out


__all__ = [
    "CONDITION",
    "NON_INTERRUPTIBLE",
    "POINT",
    "WINDOW",
    "Event",
    "RuntimeTrack",
    "interpolate_com_plans",
]
