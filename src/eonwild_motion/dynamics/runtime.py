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

    def loop_safe(self, seam_state: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Loop seam check: windows plus, when given, full endpoint state.

        With ``seam_state`` (``{"opening": {...}, "closing": {...}}`` each
        carrying ``root_position_m``, ``root_orientation``,
        ``linear_velocity_mps``, ``contacts`` and ``overlay``), the seam
        must agree on pose, velocity, contacts and overlays per spec
        section 14 — windows alone are the fallback, not the proof.
        """
        opening = self.active_windows(0.0)
        closing = self.active_windows(self.duration_s)
        result: dict[str, Any] = {
            "seam_windows_match": opening == closing,
            "opening": opening,
            "closing": closing,
            "event_count": len(self.events),
        }
        if seam_state is not None:
            try:
                first, last = seam_state["opening"], seam_state["closing"]
            except (KeyError, TypeError) as exc:
                raise ContractError(f"seam state needs opening/closing: {exc}") from exc
            dp = np.asarray(first["root_position_m"], dtype=float) - np.asarray(last["root_position_m"], dtype=float)
            dv = np.asarray(first["linear_velocity_mps"], dtype=float) - np.asarray(last["linear_velocity_mps"], dtype=float)
            a = np.asarray(first["root_orientation"], dtype=float)
            b = np.asarray(last["root_orientation"], dtype=float)
            angle = 2.0 * math.acos(max(-1.0, min(1.0, abs(float(a @ b)))))
            result.update(
                {
                    "position_seam_m": float(np.linalg.norm(dp)),
                    "orientation_seam_deg": math.degrees(angle),
                    "velocity_seam_mps": float(np.linalg.norm(dv)),
                    "contacts_match": dict(first["contacts"]) == dict(last["contacts"]),
                    "overlay_match": dict(first.get("overlay", {})) == dict(last.get("overlay", {})),
                }
            )
            result["seam_state_match"] = bool(
                result["position_seam_m"] <= 1e-6
                and result["orientation_seam_deg"] <= 1e-4
                and result["velocity_seam_mps"] <= 1e-6
                and result["contacts_match"]
                and result["overlay_match"]
            )
        return result


def footprints_from_authority(
    authority: Mapping[str, Any],
    per_foot: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    load_kg_per_foot: float = 750.0,
) -> list[Event]:
    """Footprint + dust events from evaluated contact phases.

    A multi-ton animal on soil leaves prints: every PASS loaded phase
    emits a ``FOOT_PRINT`` point event at touchdown carrying centroid,
    print depth, yaw and peak ground velocity — the exact payload a game
    runtime needs to spawn decals, deform terrain or puff dust. Phases
    without a centroid (e.g. single-frame failures) emit nothing rather
    than a fabricated position.
    """
    load = _finite(load_kg_per_foot, label="load_kg_per_foot")
    if load <= 0.0:
        raise ContractError("footprint load must be positive")
    phases_by_foot = per_foot
    if not isinstance(authority, Mapping) or not isinstance(phases_by_foot, Mapping):
        raise ContractError("footprint emission needs authority and per-foot phases")
    events: list[Event] = []
    for foot, phases in phases_by_foot.items():
        if not isinstance(foot, str) or not foot:
            raise ContractError("footprint foot identity must be a non-empty string")
        for phase in phases:
            if not isinstance(phase, Mapping):
                raise ContractError("footprint phase must be an object")
            if phase.get("verdict") != "PASS":
                continue
            centroid = phase.get("contact_centroid_m")
            if centroid is None:
                continue
            events.append(
                Event(
                    name="FOOT_PRINT",
                    kind=POINT,
                    time_s=float(phase["start_time_s"]),
                    payload={
                        "foot": foot,
                        "contact_centroid_m": [float(v) for v in centroid],
                        "print_depth_m": float(phase.get("print_depth_m", 0.0)),
                        "substrate": str(phase.get("substrate", "hard")),
                        "yaw_deg": phase.get("yaw_deg"),
                        "peak_ground_velocity_mps": phase.get("max_persistent_velocity_mps"),
                        "load_kg": load,
                    },
                )
            )
    return sorted(events, key=lambda e: (e.time_s, e.name))


def interpolate_com_plans(    plan_a: Sequence[Mapping[str, Any]],
    plan_b: Sequence[Mapping[str, Any]],
    *,
    alpha: float,
) -> list[dict[str, Any]]:
    """Blend two compatible baked COM plans preserving phase and velocity.

    Plans must share sample count and timestamps (same phase grid —
    runtime parameterizes, it never retimes). Positions blend linearly;
    velocities are the analytic Hermite derivative of the blended
    position curve, so ``com_velocity == d(com)/dt`` and ``P = M·ċ``
    hold by construction in every blend (blending the velocity channel
    independently would break that identity).
    """
    blend = _finite(alpha, label="alpha")
    if not 0.0 <= blend <= 1.0:
        raise ContractError("blend alpha must lie in [0, 1]")
    if len(plan_a) != len(plan_b) or not plan_a:
        raise ContractError("runtime interpolation needs two non-empty equal plans")
    times: list[float] = []
    pos_a: list[np.ndarray] = []
    pos_b: list[np.ndarray] = []
    vel_a: list[np.ndarray] = []
    vel_b: list[np.ndarray] = []
    for a, b in zip(plan_a, plan_b):
        if abs(float(a["time_s"]) - float(b["time_s"])) > 1e-9:
            raise ContractError("runtime plans must share the phase grid")
        times.append(float(a["time_s"]))
        pos_a.append(np.asarray(a["com_m"], dtype=float))
        pos_b.append(np.asarray(b["com_m"], dtype=float))
        vel_a.append(np.asarray(a["com_velocity_mps"], dtype=float))
        vel_b.append(np.asarray(b["com_velocity_mps"], dtype=float))
    blended_pos = [(1 - blend) * pa + blend * pb for pa, pb in zip(pos_a, pos_b)]
    blended_vel_end = [(1 - blend) * va + blend * vb for va, vb in zip(vel_a, vel_b)]
    out = []
    count = len(times)
    for i in range(count):
        if count == 1:
            vel = blended_vel_end[0]
        elif i == 0:
            # Forward Hermite derivative over the first interval.
            dt = times[1] - times[0]
            vel = _hermite_velocity(blended_pos[0], blended_pos[1],
                                    blended_vel_end[0], blended_vel_end[1], dt, 0.0)
        elif i == count - 1:
            dt = times[-1] - times[-2]
            vel = _hermite_velocity(blended_pos[-2], blended_pos[-1],
                                    blended_vel_end[-2], blended_vel_end[-1], dt, 1.0)
        else:
            # Central: average of the adjacent interval endpoint derivatives.
            dt0, dt1 = times[i] - times[i - 1], times[i + 1] - times[i]
            v0 = _hermite_velocity(blended_pos[i - 1], blended_pos[i],
                                   blended_vel_end[i - 1], blended_vel_end[i], dt0, 1.0)
            v1 = _hermite_velocity(blended_pos[i], blended_pos[i + 1],
                                   blended_vel_end[i], blended_vel_end[i + 1], dt1, 0.0)
            vel = (v0 * dt1 + v1 * dt0) / (dt0 + dt1)
        out.append(
            {
                "time_s": times[i],
                "com_m": [float(v) for v in blended_pos[i]],
                "com_velocity_mps": [float(v) for v in vel],
            }
        )
    return out


def _hermite_velocity(
    p0: np.ndarray, p1: np.ndarray, v0: np.ndarray, v1: np.ndarray, dt: float, t: float
) -> np.ndarray:
    """Derivative of the cubic Hermite position curve at ``t`` in [0, 1]."""
    if dt <= 0.0:
        raise ContractError("runtime plan timeline must be strictly increasing")
    dh00 = 6 * t * t - 6 * t
    dh10 = 3 * t * t - 4 * t + 1
    dh01 = -6 * t * t + 6 * t
    dh11 = 3 * t * t - 2 * t
    return (dh00 * p0 + dh10 * dt * v0 + dh01 * p1 + dh11 * dt * v1) / dt


__all__ = [
    "CONDITION",
    "NON_INTERRUPTIBLE",
    "POINT",
    "WINDOW",
    "Event",
    "RuntimeTrack",
    "footprints_from_authority",
    "interpolate_com_plans",
]
