"""Bounded support-aware pelvis accommodation before mouth and limb solving.

A forward pull must not extend a planted leg beyond its declared knee range.
This reduced-order geometric planner lowers the pelvis, not the floor or foot
anchors. It is not a force, COM, or muscle simulation. Final articulation and
skinned contact remain independent mandatory checks.
"""
from __future__ import annotations
import math
from numbers import Real
import numpy as np
from ..errors import ContractError


def positive_part(value: float, band: float) -> float:
    """Conservative C2 smoothing of max(0,x), exact outside [-band,band]."""
    if value <= -band:
        return 0.0
    if value >= band:
        return float(value)
    u = (value + band) / (2 * band)
    return float(2 * band * (u**6 - 3*u**5 + 2.5*u**4))


def support_balance(hips, anchors, segment_lengths, *, up_axis,
                    knee_max_degrees: float, maximum_drop_m: float,
                    activation_band_m: float) -> tuple[np.ndarray, dict]:
    """Return a minimal smoothed downward translation satisfying reach bounds.

    Inputs are world-space hip/ankle anchors and upper/lower segment lengths.
    The knee interior angle supplies the reach radius; straight-leg length is
    not treated as an acceptable standing pose. Impossible support explicitly
    requests a reposition rather than dragging the anchor or stretching bones.
    """
    hips = np.asarray(hips, dtype=float)
    anchors = np.asarray(anchors, dtype=float)
    lengths = np.asarray(segment_lengths, dtype=float)
    up = np.asarray(up_axis, dtype=float)
    if (hips.ndim != 2 or hips.shape[1] != 3 or not len(hips) or anchors.shape != hips.shape
        or lengths.shape != (len(hips), 2) or up.shape != (3,)
        or not all(np.isfinite(a).all() for a in (hips, anchors, lengths, up))
        or np.any(lengths <= 0) or abs(np.linalg.norm(up) - 1) > 1e-8):
        raise ContractError('support balance requires finite aligned geometry and a unit up axis')
    for value in (knee_max_degrees, maximum_drop_m, activation_band_m):
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ContractError('support balance limits must be finite numeric')
    if not 0 < knee_max_degrees < 180 or not 0 < activation_band_m <= maximum_drop_m:
        raise ContractError('invalid support balance envelope')
    radii_squared = lengths[:,0]**2 + lengths[:,1]**2 - 2*lengths[:,0]*lengths[:,1]*math.cos(math.radians(knee_max_degrees))
    delta = hips - anchors
    vertical = delta @ up
    horizontal = delta - vertical[:,None] * up
    horizontal_squared = np.sum(horizontal * horizontal, axis=1)
    if np.any(horizontal_squared >= radii_squared):
        raise ContractError('support geometry needs a reposition; lowering cannot recover horizontal reach')
    required = vertical - np.sqrt(radii_squared - horizontal_squared)
    # Smooth the most limiting leg conservatively. With two legs this operation
    # is symmetric; no independent per-leg pelvis offsets are introduced.
    limiting = float(required[0])
    for item in required[1:]:
        limiting += positive_part(float(item) - limiting, activation_band_m)
    drop = positive_part(limiting, activation_band_m)
    if drop > maximum_drop_m:
        raise ContractError('support balance exceeds its pelvis envelope; explicit reposition is required')
    translation = -up * drop
    final_distance = np.linalg.norm(delta + translation, axis=1)
    radii = np.sqrt(radii_squared)
    if np.any(final_distance > radii + 1e-8):
        raise ContractError('support balance cannot satisfy all planted reach constraints')
    return translation, {'classification': 'bounded geometric pelvis accommodation before oral/limb constraints',
        'translation_world_m': translation.tolist(), 'drop_m': drop,
        'maximum_drop_m': float(maximum_drop_m), 'knee_max_degrees': float(knee_max_degrees),
        'initial_hip_anchor_distances_m': np.linalg.norm(delta,axis=1).tolist(),
        'allowed_distances_m': radii.tolist(), 'planned_distances_m': final_distance.tolist(),
        'anchors_moved': False, 'floor_moved': False}
