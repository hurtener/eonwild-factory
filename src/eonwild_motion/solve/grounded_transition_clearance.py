"""Geometry-derived swing clearance for grounded gait transitions."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..planning.grounded_gait import GroundedGait, sample_grounded_gait
from .airborne_gait import solve_airborne_plan_sample, _world_matrices


POLICY = "material_floor_scaled_excess.v1"
TARGET_GAP_M = 0.0001
_HEIGHT_TOLERANCE_M = 1e-6
_MONOTONIC_TOLERANCE_M = 1e-8
_MAX_ITERATIONS = 20
_BUILD_TOKEN = object()


class GroundedTransitionClearanceUnavailable(RuntimeError):
    """The bound distal solve cannot establish a safe material floor."""


def _monotone_floor(measure: Any, ceiling: float, side: str) -> float:
    """Find the first safe height while checking the measured solve branch."""
    lo, hi = 0.0, float(ceiling)
    gap_lo, _ = measure(lo)
    if gap_lo >= TARGET_GAP_M:
        return 0.0

    def checked(height: float, lower_gap: float, upper_gap: float) -> float:
        gap, _ = measure(height)
        if (
            gap < lower_gap - _MONOTONIC_TOLERANCE_M
            or gap > upper_gap + _MONOTONIC_TOLERANCE_M
        ):
            raise GroundedTransitionClearanceUnavailable(
                f"{side} transition material gap is nonmonotone"
            )
        return gap

    gap_hi = checked(hi, gap_lo, math.inf)
    if gap_hi < TARGET_GAP_M:
        raise GroundedTransitionClearanceUnavailable(
            f"{side} transition steady target does not clear the material floor"
        )
    for _ in range(_MAX_ITERATIONS):
        fraction = (TARGET_GAP_M - gap_lo) / (gap_hi - gap_lo)
        mid = lo + fraction * (hi - lo)
        if not lo < mid < hi or hi - lo <= _HEIGHT_TOLERANCE_M:
            return hi
        gap_mid = checked(mid, gap_lo, gap_hi)
        if gap_mid >= TARGET_GAP_M:
            return mid
        lo, gap_lo = mid, gap_mid
    return hi


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class GroundedTransitionClearanceResolver:
    """Apply transition gain to clearance above the actual skinned floor.

    The resolver owns the already calibrated raw query/law. It uses a
    safeguarded secant bracket and validates every sampled gap monotonically;
    changes in the minimum material vertex are allowed when the measured gap
    remains monotone. Cached rows are keyed by the complete authored row and
    returned as detached copies.
    """

    def __init__(
        self, law: Any, locomotion_gait: GroundedGait, *, _token: object | None = None
    ) -> None:
        if _token is not _BUILD_TOKEN:
            raise ContractError("transition clearance resolver requires a validated build")
        self._law = law
        self._gait = locomotion_gait
        self._cache: dict[str, bytes] = {}
        self._solve_count = 0

    @classmethod
    def build(cls, law: Any, locomotion_gait: GroundedGait) -> "GroundedTransitionClearanceResolver":
        from .constant_skin_targets import CanonicalConstantSkinTargetLaw

        if type(law) is not CanonicalConstantSkinTargetLaw:
            raise ContractError("transition clearance requires the canonical constant target law")
        if not isinstance(locomotion_gait, GroundedGait):
            raise ContractError("transition clearance requires a grounded locomotion gait")
        if law._query._transition is None or law._query._locomotion_gait != locomotion_gait:
            raise ContractError("transition clearance gait differs from its calibrated query")
        law._validate_integrity()
        return cls(law, locomotion_gait, _token=_BUILD_TOKEN)

    def binding(self) -> Mapping[str, Any]:
        self._law._validate_integrity()
        return MappingProxyType({
            "policy": POLICY,
            "target_gap_m": TARGET_GAP_M,
            "raw_query_binding_sha256": self._law._query_binding_sha256,
            "constant_offsets_sha256": self._law._calibration_sha256,
            "locomotion_parameters": MappingProxyType(
                dict(self._law._query._plan["parameters"])
            ),
        })

    def validate_for_query(
        self,
        source: Any,
        *,
        semantic_roles: Mapping[str, Any],
        solver_gait: Any,
        locomotion_gait: Any,
        transition: Any,
        plan: Mapping[str, Any],
        contact_profile: Mapping[str, Any] | None,
        up_axis: Any,
        forward_axis: Any,
        articulation_profile: Any,
        source_clip: str | None,
        legacy_overlay: bool,
    ) -> None:
        if source_clip is not None or legacy_overlay is not False or contact_profile is None:
            raise ContractError("transition clearance requires canonical bound source geometry")
        provider = self._law._provider
        request = {
            "source": source,
            "semantic_roles": semantic_roles,
            "solver_gait": solver_gait,
            "locomotion_gait": locomotion_gait,
            "transition": transition,
            "plan": plan,
            "contact_profile": contact_profile,
            "up_axis": up_axis,
            "forward_axis": forward_axis,
            "articulation_profile": articulation_profile,
        }
        provider.validate_for_consumption(**request)
        from .constant_skin_targets import CanonicalConstantSkinTargetLaw

        expected = CanonicalConstantSkinTargetLaw._query_request(self._law._query)
        actual_inputs, actual_ids = provider._binding_inputs(**request)
        expected_inputs, expected_ids = provider._binding_inputs(**expected)
        from .support_anchors import _digest

        if _digest((actual_inputs, actual_ids)) != _digest((expected_inputs, expected_ids)):
            raise ContractError(
                "transition clearance resolver differs from the receiving source query"
            )

    @property
    def solve_count(self) -> int:
        return self._solve_count

    def _gap(self, row: Mapping[str, Any], side: str, height: float) -> tuple[float, int]:
        owned = deepcopy(row)
        owned["feet"][side]["height_m"] = float(height)
        for foot_side in ("left", "right"):
            owned["feet"][foot_side]["target_offset_m"] = np.asarray(
                self._law._constants[foot_side], dtype=float
            ).tolist()
        query = self._law._query
        pose = solve_airborne_plan_sample(
            query.context,
            owned,
            body_response_sample=query._body_sample(
                query._exact_index(float(owned["time_s"])), owned
            ),
        )
        worlds = np.asarray(
            _world_matrices(
                query._source,
                pose.translations,
                pose.rotations,
                query.context.base_s,
            )
        )
        ids = np.unique(np.concatenate([
            self._law._skin.foot_regions[side]["sole"],
            self._law._skin.foot_regions[side]["toe"],
        ]))
        points = self._law._skin.skin(worlds, ids)
        gaps = points @ query.context.up - self._law._skin.ground
        index = int(np.argmin(gaps))
        self._solve_count += 1
        gap = float(gaps[index])
        if not math.isfinite(gap):
            raise GroundedTransitionClearanceUnavailable(
                "transition clearance material gap is non-finite"
            )
        return gap, int(ids[index])

    def _floor(self, row: Mapping[str, Any], side: str, ceiling: float) -> float:
        return _monotone_floor(
            lambda height: self._gap(row, side, height), ceiling, side
        )

    def resolve(self, row: Mapping[str, Any]) -> dict[str, Any]:
        """Resolve one row after independently validating the owned context."""
        self._law._validate_integrity()
        return self._resolve_owned(row)

    def _resolve_owned(self, row: Mapping[str, Any]) -> dict[str, Any]:
        """Resolve after the containing constant law proved this binding."""
        key = _digest(row)
        cached = self._cache.get(key)
        if cached is not None:
            return json.loads(cached)
        result = deepcopy(row)
        time_s = float(result["time_s"])
        phase = float(result.get("locomotion_time_s", time_s))
        steady = sample_grounded_gait(
            self._gait, phase, self._law._query.context.body_height
        )
        heights: dict[str, float] = {}
        for side in ("left", "right"):
            foot = result["feet"][side]
            if foot["contact"]:
                continue
            authored = float(foot["height_m"])
            steady_height = float(steady["feet"][side]["height_m"])
            if not all(math.isfinite(v) and v >= 0 for v in (authored, steady_height)):
                raise GroundedTransitionClearanceUnavailable(
                    f"{side} transition clearance height is invalid"
                )
            if math.isclose(authored, steady_height, rel_tol=0, abs_tol=1e-12):
                heights[side] = authored
                continue
            if steady_height <= 1e-12 or authored > steady_height + 1e-12:
                raise GroundedTransitionClearanceUnavailable(
                    f"{side} transition clearance gain is outside the steady target"
                )
            scale = min(1.0, max(0.0, authored / steady_height))
            # Each side's material floor is measured against the same authored
            # row. This avoids silently making the second foot depend on the
            # first foot's correction while the final checked solve remains
            # joint across both feet.
            floor = self._floor(row, side, steady_height)
            heights[side] = max(
                authored, floor + scale * max(0.0, steady_height - floor)
            )
        for side, height in heights.items():
            result["feet"][side]["height_m"] = height
        self._cache[key] = json.dumps(
            result, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        return deepcopy(result)


__all__ = [
    "GroundedTransitionClearanceResolver",
    "GroundedTransitionClearanceUnavailable",
    "POLICY",
    "TARGET_GAP_M",
]
