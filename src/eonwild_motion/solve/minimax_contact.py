"""Deterministic minimum enclosing balls for three-dimensional residuals."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import random
from typing import Any

import numpy as np

from ..errors import ContractError


@dataclass(frozen=True)
class MinimaxContactBall:
    """The translation center and maximum distance for unique residual rows.

    ``unique_residual_count`` is not contact cardinality: distinct physical
    contacts can have the same residual vector. Contact membership and support
    dimension remain the caller's separately bound source geometry.
    """

    center_m: tuple[float, float, float]
    radius_m: float
    unique_residual_count: int


def _candidate(points: np.ndarray) -> tuple[np.ndarray, float] | None:
    count = len(points)
    if count == 1:
        center = points[0].copy()
    elif count == 2:
        center = 0.5 * (points[0] + points[1])
    elif count == 3:
        offsets = points[1:] - points[0]
        gram = offsets @ offsets.T
        if np.linalg.matrix_rank(gram) < 2:
            return None
        center = points[0] + np.linalg.solve(gram, 0.5 * np.diag(gram)) @ offsets
    elif count == 4:
        offsets = points[1:] - points[0]
        if np.linalg.matrix_rank(offsets) < 3:
            return None
        center = points[0] + np.linalg.solve(
            offsets, 0.5 * np.einsum("ij,ij->i", offsets, offsets)
        )
    else:
        raise AssertionError("a three-dimensional ball has at most four supports")
    radius = float(np.linalg.norm(points - center, axis=1).max())
    return center, radius


def _contains(center: np.ndarray, radius: float, points: np.ndarray) -> bool:
    scale = max(1.0, float(np.abs(points).max()), float(np.abs(center).max()), radius)
    tolerance = 128.0 * np.finfo(float).eps * scale
    return bool(np.all(np.linalg.norm(points - center, axis=1) <= radius + tolerance))


def _boundary_ball(points: np.ndarray) -> tuple[np.ndarray, float]:
    best: tuple[np.ndarray, float] | None = None
    # The boundary has at most four points. Enumerating its constant 15 subsets
    # handles coincident, collinear, coplanar, and obtuse configurations without
    # enumerating subsets of the full input.
    for size in range(1, len(points) + 1):
        for indices in itertools.combinations(range(len(points)), size):
            candidate = _candidate(points[list(indices)])
            if candidate is None or not _contains(*candidate, points):
                continue
            key = (candidate[1], *candidate[0])
            if best is None or key < (best[1], *best[0]):
                best = candidate
    if best is None:
        raise ContractError("minimum enclosing residual ball is numerically indeterminate")
    return best


def _outside(ball: tuple[np.ndarray, float], point: np.ndarray) -> bool:
    return not _contains(ball[0], ball[1], point[None, :])


def minimum_enclosing_residual_ball(residuals_m: Any) -> MinimaxContactBall:
    """Return the exact fixed-dimension minimax center for finite 3D residuals.

    Duplicate rows are removed before solving, so both the result and
    ``unique_residual_count`` describe distinct error vectors. It deliberately
    does not report physical contact count or support-hull cardinality.
    A content-derived shuffle gives the randomized incremental algorithm its
    expected linear behavior while retaining deterministic, query-order
    independent output. The caller must apply ``-center_m`` as a candidate and
    rerun every geometry, IK, floor, and articulation constraint.
    """

    try:
        raw = np.asarray(residuals_m, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ContractError("contact residuals must be finite three-dimensional points") from exc
    if raw.ndim != 2 or raw.shape[1:] != (3,) or len(raw) == 0:
        raise ContractError("contact residuals must be a non-empty N by 3 array")
    if not np.isfinite(raw).all():
        raise ContractError("contact residuals must be finite three-dimensional points")
    # Differences are squared by the ball construction. This explicit input
    # bound keeps every subtraction, dot product, and norm in finite float64
    # arithmetic rather than accepting a finite value that later overflows.
    safe_magnitude = np.sqrt(np.finfo(float).max) / 4.0
    if float(np.abs(raw).max()) > safe_magnitude:
        raise ContractError("contact residuals exceed the finite arithmetic bound")

    points = np.unique(np.where(raw == 0.0, 0.0, raw), axis=0)
    digest = hashlib.sha256(np.asarray(points, dtype="<f8").tobytes()).digest()
    order = list(range(len(points)))
    random.Random(int.from_bytes(digest[:16], "big")).shuffle(order)
    points = points[order]

    ball = _boundary_ball(points[:1])
    for i, point in enumerate(points):
        if not _outside(ball, point):
            continue
        ball = _boundary_ball(points[[i]])
        for j in range(i):
            if not _outside(ball, points[j]):
                continue
            ball = _boundary_ball(points[[i, j]])
            for k in range(j):
                if not _outside(ball, points[k]):
                    continue
                ball = _boundary_ball(points[[i, j, k]])
                for l in range(k):
                    if _outside(ball, points[l]):
                        ball = _boundary_ball(points[[i, j, k, l]])

    center, _ = ball
    radius = float(np.linalg.norm(points - center, axis=1).max())
    if not np.isfinite(center).all() or not np.isfinite(radius):
        raise ContractError("minimum enclosing residual ball produced a non-finite result")
    if not _contains(center, radius, points):
        raise ContractError("minimum enclosing residual ball failed containment verification")
    return MinimaxContactBall(
        center_m=tuple(float(value) for value in center),
        radius_m=radius,
        unique_residual_count=len(points),
    )


__all__ = ["MinimaxContactBall", "minimum_enclosing_residual_ball"]
