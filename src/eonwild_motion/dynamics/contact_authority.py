"""Skinned sole/toe patch as the contact authority.

The skeleton (ankle marker, toe-joint plane) is a planning proxy only.
Final contact truth is the deformed skin: actual sole/toe vertices against
the fixed ground plane. This module evaluates per-loaded-phase facts:

* penetration depth and gap (min signed distance to the fixed floor),
* persistent ground-plane velocity — vertices within ``tolerance_m`` of
  the floor in *both* frames of a pair (``ground_plane_velocity_witness``
  semantics from ``solve/airborne_gait.py``),
* patch drift (persistent-point displacement) and yaw (patch heading
  change) per loaded phase.

Fail-closed rules:

* a loaded phase with ``persistent_point_count == 0`` is UNKNOWN contact,
  never a zero-skate pass — the gate FAILs;
* penetration beyond tolerance FAILs;
* persistent tangential velocity beyond the skate threshold FAILs.

Band-relative speeds (vertices merely near the lifted patch minimum) are
reported as informational deformation context only and must never be
presented as ground-slip evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from .centroidal import _finite

SCHEMA = "eonwild.motion.v9.contact-authority.v1"


@dataclass(frozen=True)
class PatchFrame:
    """One foot's skinned world vertices at one timestamp."""

    time_s: float
    sole_m: tuple[tuple[float, float, float], ...]
    toe_m: tuple[tuple[float, float, float], ...]


def _as_array(points: Sequence[Sequence[float]], *, label: str) -> np.ndarray:
    rows = []
    for i, point in enumerate(points):
        if len(point) != 3:
            raise ContractError(f"{label}[{i}] must contain exactly three numbers")
        rows.append([_finite(float(v), label=f"{label}[{i}]") for v in point])
    if not rows:
        raise ContractError(f"{label} must be non-empty")
    return np.asarray(rows, dtype=float)


def ground_plane_witness(
    previous: np.ndarray,
    current: np.ndarray,
    *,
    up_axis: int,
    ground_m: float,
    tolerance_m: float,
    delta_time_s: float,
) -> dict[str, Any]:
    """Fixed-ground occupancy between two aligned vertex sets.

    Only vertices within ``tolerance_m`` of the *fixed floor* in both
    frames count. Empty occupancy is unknown velocity (``None``), never
    a zero-skate pass.
    """
    if delta_time_s <= 0.0 or len(previous) != len(current) or len(previous) == 0:
        raise ContractError("ground-plane witness needs aligned points and positive dt")
    if tolerance_m <= 0.0:
        raise ContractError("ground-plane tolerance must be positive")
    active = (np.abs(previous[:, up_axis] - ground_m) <= tolerance_m) & (
        np.abs(current[:, up_axis] - ground_m) <= tolerance_m
    )
    ids = np.flatnonzero(active)
    if len(ids) == 0:
        return {
            "persistent_point_count": 0,
            "maximum_velocity_mps": None,
            "maximum_tangential_velocity_mps": None,
        }
    velocity = (current[ids] - previous[ids]) / delta_time_s
    speeds = np.linalg.norm(velocity, axis=1)
    local = int(speeds.argmax())
    tangential = velocity.copy()
    tangential[:, up_axis] = 0.0
    return {
        "persistent_point_count": int(len(ids)),
        "persistent_indices": sorted(int(i) for i in ids),
        "maximum_velocity_mps": float(speeds[local]),
        "maximum_tangential_velocity_mps": float(np.linalg.norm(tangential, axis=1).max()),
        "point_index": int(ids[local]),
    }


def patch_heading_yaw_deg(previous: np.ndarray, current: np.ndarray, *, up_axis: int) -> float:
    """Yaw change (degrees) of a patch's principal ground-plane axis."""
    for points in (previous, current):
        if len(points) < 2:
            return 0.0
    axes = (1, 2, 0) if up_axis == 0 else (0, 2) if up_axis == 1 else (0, 1)
    try:
        prev = previous[:, list(axes)] - previous[:, list(axes)].mean(axis=0)
        curr = current[:, list(axes)] - current[:, list(axes)].mean(axis=0)
        _, _, prev_vt = np.linalg.svd(prev, full_matrices=False)
        _, _, curr_vt = np.linalg.svd(curr, full_matrices=False)
    except Exception as exc:
        raise ContractError(f"patch yaw SVD failed: {exc}") from exc
    dot = float(np.clip(abs(prev_vt[0] @ curr_vt[0]), -1.0, 1.0))
    return math.degrees(math.acos(dot))


@dataclass(frozen=True)
class AuthorityThresholds:
    penetration_tolerance_m: float = 0.0005
    skate_velocity_mps: float = 0.35
    drift_per_phase_m: float = 0.02
    yaw_per_phase_deg: float = 6.0
    ground_tolerance_m: float = 0.001
    up_axis: int = 1
    ground_m: float = 0.0

    def __post_init__(self) -> None:
        for key in (
            "penetration_tolerance_m",
            "skate_velocity_mps",
            "drift_per_phase_m",
            "yaw_per_phase_deg",
            "ground_tolerance_m",
        ):
            value = float(getattr(self, key))
            if not math.isfinite(value) or value < 0.0:
                raise ContractError(f"authority threshold {key} must be non-negative and finite")
        if self.up_axis not in (0, 1, 2):
            raise ContractError("authority up axis must be 0, 1 or 2")
        _finite(float(self.ground_m), label="authority ground_m")


def evaluate_contact_authority(
    frames: Sequence[PatchFrame],
    loaded: Sequence[bool],
    *,
    thresholds: AuthorityThresholds = AuthorityThresholds(),
) -> dict[str, Any]:
    """Evaluate the skinned contact authority over one foot's timeline.

    ``frames`` and ``loaded`` (planned contact per frame) must align.
    Returns per-phase facts plus an overall PASS/FAIL verdict under the
    fail-closed rules documented above.
    """
    if len(frames) != len(loaded) or len(frames) < 2:
        raise ContractError("contact authority needs at least two aligned frames")
    times = [_finite(float(f.time_s), label="frame time") for f in frames]
    if any(b - a <= 0.0 for a, b in zip(times, times[1:])):
        raise ContractError("contact authority timeline must be strictly increasing")

    up, ground = thresholds.up_axis, thresholds.ground_m
    minima: list[float] = []
    phases: list[dict[str, Any]] = []
    start: int | None = None
    for index, is_loaded in enumerate(list(loaded) + [False]):
        if is_loaded and start is None:
            start = index
            continue
        if is_loaded or start is None:
            continue
        end = index - 1
        frame_count = end - start + 1
        if frame_count < 2:
            # A single frame cannot establish persistent contact — there is
            # no pair to witness. Fail closed, never vacuous PASS.
            phases.append(
                {
                    "start_frame": start,
                    "end_frame": end,
                    "start_time_s": times[start],
                    "end_time_s": times[end],
                    "minimum_gap_m": None,
                    "max_persistent_velocity_mps": None,
                    "persistent_point_total": 0,
                    "unknown_pairs": 0,
                    "drift_m": 0.0,
                    "yaw_deg": None,
                    "verdict": "FAIL",
                    "reasons": ["single-frame phase cannot establish persistent contact"],
                }
            )
            start = None
            continue
        worst_pen = 0.0
        worst_speed: float | None = 0.0
        total_drift = 0.0
        max_pair_yaw = 0.0
        persistent_total = 0
        unknown_pairs = 0
        pair_count = 0
        for k in range(start, end + 1):
            verts = np.vstack(
                [_as_array(frames[k].sole_m, label="sole"), _as_array(frames[k].toe_m, label="toe")]
            )
            gap = float(verts[:, up].min() - ground)
            minima.append(gap)
            worst_pen = max(worst_pen, -gap)
            if k > start:
                prev = np.vstack(
                    [_as_array(frames[k - 1].sole_m, label="sole"), _as_array(frames[k - 1].toe_m, label="toe")]
                )
                witness = ground_plane_witness(
                    prev, verts, up_axis=up, ground_m=ground,
                    tolerance_m=thresholds.ground_tolerance_m,
                    delta_time_s=times[k] - times[k - 1],
                )
                pair_count += 1
                if witness["persistent_point_count"] == 0:
                    unknown_pairs += 1
                else:
                    persistent_total += witness["persistent_point_count"]
                    speed = float(witness["maximum_tangential_velocity_mps"] or 0.0)
                    worst_speed = max(float(worst_speed or 0.0), speed)
                    total_drift += speed * (times[k] - times[k - 1])
                    # Yaw is measured on the persistent set only: witness
                    # motion of points that actually stayed at the floor.
                    ids = witness["persistent_indices"]
                    if len(ids) >= 2:
                        max_pair_yaw = max(
                            max_pair_yaw,
                            patch_heading_yaw_deg(prev[ids], verts[ids], up_axis=up),
                        )
        reasons: list[str] = []
        if unknown_pairs > 0:
            reasons.append(f"{unknown_pairs}/{pair_count} pairs have no persistent ground points (unknown contact)")
        if worst_pen > thresholds.penetration_tolerance_m:
            reasons.append(f"penetration {worst_pen:.6f} m exceeds tolerance")
        if worst_speed is not None and worst_speed > thresholds.skate_velocity_mps:
            reasons.append(f"persistent skate {worst_speed:.3f} m/s exceeds threshold")
        if total_drift > thresholds.drift_per_phase_m:
            reasons.append(f"patch drift {total_drift:.4f} m exceeds threshold")
        if max_pair_yaw > thresholds.yaw_per_phase_deg:
            reasons.append(f"persistent patch yaw {max_pair_yaw:.2f} deg exceeds threshold")
        phases.append(
            {
                "start_frame": start,
                "end_frame": end,
                "start_time_s": times[start],
                "end_time_s": times[end],
                "minimum_gap_m": min(
                    float(np.vstack([_as_array(frames[k].sole_m, label="sole"), _as_array(frames[k].toe_m, label="toe")])[:, up].min() - ground)
                    for k in range(start, end + 1)
                ),
                "max_penetration_m": worst_pen,
                "max_persistent_velocity_mps": worst_speed,
                "persistent_point_total": persistent_total,
                "unknown_pairs": unknown_pairs,
                "drift_m": total_drift,
                "yaw_deg": max_pair_yaw,
                "verdict": "PASS" if not reasons else "FAIL",
                "reasons": reasons,
            }
        )
        start = None

    overall_reasons: list[str] = []
    if not phases:
        overall_reasons.append("no loaded phases evaluated")
    for phase in phases:
        overall_reasons.extend(f"phase {phase['start_frame']}-{phase['end_frame']}: {r}" for r in phase["reasons"])
    return {
        "schema": SCHEMA,
        "phase_count": len(phases),
        "phases": phases,
        "global_minimum_gap_m": min(minima) if minima else None,
        "verdict": "PASS" if not overall_reasons else "FAIL",
        "reasons": overall_reasons,
        "classification": "skinned patch authority; band-relative speeds excluded from verdict",
    }


__all__ = [
    "AuthorityThresholds",
    "PatchFrame",
    "evaluate_contact_authority",
    "ground_plane_witness",
    "patch_heading_yaw_deg",
]
