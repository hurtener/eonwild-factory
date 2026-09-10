"""Bind body-support trials to the shared final source geometry law."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from ..solve.body_support_control import BodySupportControl
from ..solve.constant_skin_targets import (
    CanonicalConstantSkinTargetLaw,
    ConstantSkinTargetUnavailable,
)
from ..solve.source_motion_query import SourceMotionQuery, _freeze_data
from .body_support_bridge import FinalGeometrySample
from .body_support_coordinator import BodyDelta, COEFFICIENT_COUNT


@dataclass(frozen=True)
class _BoundTrial:
    coefficients: tuple[float, ...]
    control: BodySupportControl
    law: CanonicalConstantSkinTargetLaw


class SourceFinalGeometryAdapter:
    """Evaluate one coefficient vector through the final post-leg skin law.

    The admitted law and its calibration query stay fixed.  Each distinct
    coefficient tuple creates a controlled clone of the retained source query
    and rebinds the existing law templates to that query without recalibration.
    """

    def __init__(
        self,
        neutral_query: SourceMotionQuery,
        frozen_law: CanonicalConstantSkinTargetLaw,
    ) -> None:
        if type(neutral_query) is not SourceMotionQuery:
            raise ContractError("source body-support adapter requires an owned query")
        if type(frozen_law) is not CanonicalConstantSkinTargetLaw:
            raise ContractError("source body-support adapter requires an owned skin law")
        if (
            frozen_law.receipt()["law_id"]
            != "canonical_semantic_joint_contact_targets.v3"
        ):
            raise ContractError("source body-support adapter requires the final v3 skin law")
        if neutral_query.body_support_control_receipt() is not None:
            raise ContractError("source body-support adapter calibration query must be neutral")
        # with_query validates that this is the exact request retained by the
        # law.  It must not rebuild provider anchors or calibration templates.
        if frozen_law.with_query(neutral_query).receipt() != frozen_law.receipt():
            raise ContractError("source body-support law does not retain its neutral query")
        anchor = frozen_law.frozen_anchor_binding_sha256()
        if not _digest(anchor):
            raise ContractError("source body-support law has no frozen anchor binding")
        self._neutral_query = neutral_query
        self._frozen_law = frozen_law
        self._frozen_anchor_sha256 = anchor
        self._cache: dict[tuple[float, ...], _BoundTrial] = {}

    @property
    def frozen_anchor_sha256(self) -> str:
        return self._frozen_anchor_sha256

    @property
    def body_control_cycle_s(self) -> float:
        return float(self._neutral_query._plan["same_foot_cycle_s"])

    @property
    def body_height_m(self) -> float:
        return float(self._neutral_query.context.body_height)

    def _bound_trial(self, coefficients: Sequence[float]) -> _BoundTrial:
        owned = _coefficients(coefficients)
        cached = self._cache.get(owned)
        if cached is not None:
            return cached
        query = self._neutral_query
        control = BodySupportControl.build(
            owned,
            same_foot_cycle_s=float(query._plan["same_foot_cycle_s"]),
            body_height_m=query.context.body_height,
            up_axis=query.context.up,
            forward_axis=query.context.forward,
        )
        controlled_query = query.with_body_support_control(control)
        law = self._frozen_law.with_query(controlled_query)
        if law.frozen_anchor_binding_sha256() != self._frozen_anchor_sha256:
            raise ContractError("body-support trial changed its frozen material anchors")
        trial = _BoundTrial(owned, control, law)
        self._cache[owned] = trial
        return trial

    def binding_receipt(self, coefficients: Sequence[float]) -> Mapping[str, Any]:
        """Return the exact body, law, and unchanged-anchor trial bindings."""
        trial = self._bound_trial(coefficients)
        self._validate_trial_anchor(trial)
        law_receipt = trial.law.receipt()
        return _freeze_data(
            {
                "body_support_control": trial.control.receipt(),
                "skin_target_law": law_receipt,
                "query_binding_sha256": law_receipt["query_binding_sha256"],
                "final_law_binding_sha256": law_receipt["binding_sha256"],
                "frozen_anchor_sha256": self._frozen_anchor_sha256,
            }
        )

    def law_for_coefficients(
        self, coefficients: Sequence[float]
    ) -> CanonicalConstantSkinTargetLaw:
        """Return the validated query-bound final law without recalibration."""
        trial = self._bound_trial(coefficients)
        self._validate_trial_anchor(trial)
        trial.law.receipt()
        return trial.law

    def __call__(
        self,
        coefficients: tuple[float, ...],
        supplied_delta: BodyDelta,
        time_s: float,
    ) -> FinalGeometrySample:
        trial = self._bound_trial(coefficients)
        self._validate_trial_anchor(trial)
        expected_delta = trial.control.delta(time_s)
        if type(supplied_delta) is not BodyDelta or supplied_delta != expected_delta:
            raise ContractError(
                "source body-support trial delta differs from its bound coefficients"
            )
        value = trial.law.value(time_s)
        if isinstance(value, ConstantSkinTargetUnavailable):
            raise ContractError(
                "source body-support trial failed final geometry: " + value.reason
            )
        worlds = trial.law._skin.world(
            value.pose.translations,
            value.pose.rotations,
            trial.law._query.context.base_s,
        )
        law_receipt = trial.law.receipt()
        floor_target_gap = float(law_receipt["floor_target_gap_m"])
        mapping_tolerance = float(law_receipt["mapping_tolerance_m"])
        full_skin = np.asarray(trial.law._skin.skin(worlds), dtype=float)
        up_index = int(np.argmax(np.abs(trial.law._query.context.up)))
        _require_full_skin_floor(
            full_skin,
            up_index=up_index,
            ground_m=trial.law._skin.ground,
            target_gap_m=floor_target_gap,
            numerical_tolerance_m=mapping_tolerance,
        )
        support_points = []
        for side in ("left", "right"):
            patch = trial.law._patch(trial.law._skin, worlds, side)
            observed_gap = float(patch[:, up_index].min() - trial.law._skin.ground)
            recorded_gap = float(value.observations[side]["minimum_gap_m"])
            if (
                not bool(value.observations[side]["clearance_ok"])
                or not math.isclose(
                    observed_gap, recorded_gap, rel_tol=0.0, abs_tol=1e-12
                )
            ):
                raise ContractError(
                    "source body-support trial final skin differs from its law witness"
                )
            if bool(value.row["feet"][side]["contact"]):
                support_points.extend(
                    patch[np.asarray(trial.law._support_patch_indices[side], dtype=int)]
                )
        if not support_points:
            raise ContractError("source body-support trial has no active material support")
        named_worlds = _named_world_matrices(
            trial.law._query, worlds, trial.law._skin.joints
        )
        return FinalGeometrySample(
            time_s=float(time_s),
            joint_world_matrices=named_worlds,
            support_points_m=tuple(
                tuple(float(component) for component in point)
                for point in support_points
            ),
            frozen_anchor_sha256=self._frozen_anchor_sha256,
            final_geometry_passed=True,
        )

    def _validate_trial_anchor(self, trial: _BoundTrial) -> None:
        if trial.law.frozen_anchor_binding_sha256() != self._frozen_anchor_sha256:
            raise ContractError("body-support trial changed its frozen material anchors")


def _coefficients(value: Sequence[float]) -> tuple[float, ...]:
    try:
        owned_input = tuple(value)
    except TypeError:
        owned_input = ()
    contains_boolean = any(
        isinstance(item, (bool, np.bool_)) for item in owned_input
    )
    try:
        raw = np.asarray(owned_input)
    except (TypeError, ValueError) as exc:
        raise ContractError("source body-support adapter requires 12 finite coefficients") from exc
    if (
        contains_boolean
        or raw.shape != (COEFFICIENT_COUNT,)
        or raw.dtype.kind not in "fiu"
        or not np.isfinite(raw).all()
    ):
        raise ContractError("source body-support adapter requires 12 finite coefficients")
    return tuple(float(component) for component in raw)


def _require_full_skin_floor(
    points: np.ndarray,
    *,
    up_index: int,
    ground_m: float,
    target_gap_m: float,
    numerical_tolerance_m: float,
) -> None:
    if (
        points.ndim != 2
        or points.shape[1:] != (3,)
        or not len(points)
        or not np.isfinite(points).all()
    ):
        raise ContractError("source body-support trial full posed skin is invalid")
    full_skin_gap = float(points[:, up_index].min() - ground_m)
    if full_skin_gap + numerical_tolerance_m < target_gap_m:
        raise ContractError(
            "source body-support trial full posed skin violates its fixed floor: "
            f"gap_m={full_skin_gap!r} target_m={target_gap_m!r} "
            f"numerical_tolerance_m={numerical_tolerance_m!r}"
        )


def _digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _named_world_matrices(
    query: SourceMotionQuery, worlds: np.ndarray, joint_indices: Sequence[int]
) -> Mapping[str, tuple[tuple[float, ...], ...]]:
    result = {}
    for index in joint_indices:
        node = query._source.document["nodes"][int(index)]
        name = node.get("name")
        if not isinstance(name, str) or not name:
            raise ContractError("source body-support deform joint has no stable name")
        if name in result:
            raise ContractError("source body-support deform joint names are not unique")
        matrix = np.asarray(worlds[index], dtype=float)
        if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
            raise ContractError("source body-support joint matrix is invalid")
        result[name] = tuple(
            tuple(float(component) for component in row) for row in matrix
        )
    return MappingProxyType(result)


__all__ = ["SourceFinalGeometryAdapter"]
