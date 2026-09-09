"""Non-emitting, pointwise constant skin-target diagnostics.

One vector per semantic foot is calibrated at the canonical source touchdowns
and applied unchanged at every requested source time. The existing row solver
does not expose derivative, branch-stability, or global-C1 authority; none is
claimed here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from .airborne_gait import (
    SolvedAirbornePose,
    _freeze_data,
    _world_matrices,
    solve_airborne_plan_sample,
)
from .skin_rig import SkinRig
from .source_motion_query import SourceMotionQuery, SourceMotionUnavailable, _thaw
from .support_anchors import CanonicalSupportAnchorProvider, _digest

_TARGET_GAP_M = 0.0001
_TOLERANCE_M = 0.0002
_IK_TOLERANCE_M = 0.001
_ARTICULATION_TOLERANCE_DEGREES = 0.01
_DAMPING = 0.85
_MAX_CORRECTION_BODY_HEIGHTS = 0.06
_BUILD_TOKEN = object()


def _readonly_vector(value: Any) -> np.ndarray:
    result = np.array(value, dtype=float, copy=True)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractError("constant skin target requires finite per-side vectors")
    result.setflags(write=False)
    return result


def _finite_time(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError("constant skin target time must be finite numeric")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ContractError("constant skin target time must be finite numeric") from exc
    if not math.isfinite(result):
        raise ContractError("constant skin target time must be finite numeric")
    return result


@dataclass(frozen=True)
class ConstantSkinTargetUnavailable:
    status: str
    time_s: float
    reason: str
    observations: Mapping[str, Any]
    branch_witness: Mapping[str, Any]


@dataclass(frozen=True)
class ConstantSkinTargetValue:
    status: str
    time_s: float
    row: Mapping[str, Any]
    pose: SolvedAirbornePose
    corrections_m: Mapping[str, np.ndarray]
    observations: Mapping[str, Any]
    branch_witness: Mapping[str, Any]


class CanonicalConstantSkinTargetLaw:
    """Per-side canonical-touchdown constants bound to one actual query."""

    def __init__(
        self,
        query: SourceMotionQuery,
        calibration_query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
        skin: SkinRig,
        constants: Mapping[str, np.ndarray],
        *,
        _token: object | None = None,
    ) -> None:
        if _token is not _BUILD_TOKEN:
            raise ContractError(
                "constant skin target law requires validated build calibration"
            )
        if set(constants) != {"left", "right"}:
            raise ContractError("constant skin target requires left and right vectors")
        self._query = query
        self._calibration_query = calibration_query
        self._provider = provider
        self._skin = skin
        self._constants = MappingProxyType(
            {side: _readonly_vector(constants[side]) for side in ("left", "right")}
        )
        self._calibration_sha256 = self._constants_sha256()
        self._query_binding_sha256 = self._current_query_binding_sha256(query)
        self._calibration_query_binding_sha256 = self._current_query_binding_sha256(
            calibration_query
        )

    @staticmethod
    def _query_request(query: SourceMotionQuery) -> dict[str, Any]:
        if not isinstance(query, SourceMotionQuery):
            raise ContractError("constant skin target requires a source motion query")
        if query._source_clip is not None or query._legacy_overlay is not False:
            raise ContractError(
                "constant skin target query requires canonical source geometry without clip or overlay"
            )
        if query._contact_profile is None:
            raise ContractError("constant skin target query requires bound contact data")
        return {
            "source": query._source,
            "semantic_roles": _thaw(query._roles),
            "solver_gait": query._solver_gait,
            "locomotion_gait": query._locomotion_gait,
            "transition": query._transition,
            "plan": _thaw(query._plan),
            "contact_profile": _thaw(query._contact_profile),
            "up_axis": query._up_axis,
            "forward_axis": query._forward_axis,
            "articulation_profile": query.context.articulation_profile,
        }

    @classmethod
    def _validate_actual_query(
        cls,
        query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
    ) -> None:
        provider.validate_for_consumption(**cls._query_request(query))

    def _current_query_binding_sha256(self, query: SourceMotionQuery) -> str:
        request = self._query_request(query)
        if query._authored_material_contact is not None:
            query._authored_material_contact.validate_for_query(query)
        inputs, material_ids = self._provider._binding_inputs(**request)
        return _digest(
            {
                "provider_request": inputs,
                "material_vertex_indices": material_ids,
                "source_clip": query._source_clip,
                "legacy_overlay": query._legacy_overlay,
                "transition_clearance": (
                    None
                    if query._transition_clearance is None
                    else query._transition_clearance.binding()
                ),
                "authored_material_contact": (
                    None
                    if query._authored_material_contact is None
                    else query._authored_material_contact.binding()
                ),
            }
        )

    def _constants_sha256(self) -> str:
        return hashlib.sha256(
            b"".join(
                np.asarray(self._constants[side], dtype="<f8").tobytes()
                for side in ("left", "right")
            )
        ).hexdigest()

    def _validate_integrity(self) -> None:
        if self._constants_sha256() != self._calibration_sha256:
            raise ContractError(
                "constant skin target calibration differs from validated values"
            )
        if self._current_query_binding_sha256(self._query) != self._query_binding_sha256:
            raise ContractError(
                "constant skin target query differs from its validated request"
            )
        if (
            self._current_query_binding_sha256(self._calibration_query)
            != self._calibration_query_binding_sha256
        ):
            raise ContractError(
                "constant skin target calibration query differs from validated values"
            )

    @classmethod
    def build(
        cls,
        query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
        *,
        source: Any,
        semantic_roles: Mapping[str, Any],
        solver_gait: Any,
        locomotion_gait: Any,
        transition: Any,
        plan: Mapping[str, Any],
        contact_profile: Mapping[str, Any],
        up_axis: tuple[float, float, float],
        forward_axis: tuple[float, float, float],
        articulation_profile: Any = None,
        iterations: int = 7,
    ) -> CanonicalConstantSkinTargetLaw:
        if type(iterations) is not int or iterations < 1:
            raise ContractError(
                "constant skin target iterations must be positive integer"
            )
        if not isinstance(query, SourceMotionQuery):
            raise ContractError("constant skin target requires a source motion query")
        if query.refined:
            raise ContractError(
                "constant skin target requires an unrefined source query"
            )

        # The explicit compile request and the actual retained query must both
        # match the same sealed provider request. This binds the real evaluator
        # without inventing another planner or trusting a parallel argument list.
        provider.validate_for_consumption(
            source,
            semantic_roles=semantic_roles,
            solver_gait=solver_gait,
            locomotion_gait=locomotion_gait,
            transition=transition,
            plan=plan,
            contact_profile=contact_profile,
            up_axis=up_axis,
            forward_axis=forward_axis,
            articulation_profile=articulation_profile,
        )
        cls._validate_actual_query(query, provider)

        request = cls._query_request(query)
        sustained_plan = provider._sustained_plan(
            query._locomotion_gait,
            query.context.body_height,
            request["plan"],
        )
        calibration_query = SourceMotionQuery(
            request["source"],
            semantic_roles=request["semantic_roles"],
            solver_gait=request["solver_gait"],
            locomotion_gait=request["locomotion_gait"],
            transition=None,
            plan=sustained_plan,
            up_axis=request["up_axis"],
            forward_axis=request["forward_axis"],
            source_clip=None,
            legacy_overlay=False,
            articulation_profile=request["articulation_profile"],
            contact_profile=request["contact_profile"],
        )
        skin = SkinRig(
            request["source"],
            request["semantic_roles"],
            query.context.forward,
            query.context.up,
            request["contact_profile"],
        )
        constants = {side: np.zeros(3) for side in ("left", "right")}
        for _ in range(iterations):
            updates = {}
            for side in ("left", "right"):
                value = cls._observe(
                    calibration_query,
                    provider,
                    skin,
                    side,
                    provider.anchor_for(side).touchdown_phase_s,
                    constants,
                )
                if not value["loaded"]:
                    raise ContractError("canonical touchdown must be loaded")
                updates[side] = _DAMPING * value["required_correction_m"]
            for side in constants:
                constants[side] += updates[side]
            if (
                max(np.linalg.norm(value) for value in constants.values())
                > _MAX_CORRECTION_BODY_HEIGHTS * query.context.body_height
            ):
                raise ContractError(
                    "constant skin target exceeded body-normalized correction envelope"
                )
            if max(np.linalg.norm(value) for value in updates.values()) <= _TOLERANCE_M:
                break

        law = cls(
            query,
            calibration_query,
            provider,
            skin,
            constants,
            _token=_BUILD_TOKEN,
        )
        # At each canonical event, apply both constants and jointly admit every
        # loaded foot plus every unloaded foot's clearance.
        for phase in (
            provider.anchor_for("left").touchdown_phase_s,
            provider.anchor_for("right").touchdown_phase_s,
        ):
            checked = law._observe_at(phase, query=calibration_query)
            if isinstance(checked, ConstantSkinTargetUnavailable):
                raise ContractError(
                    f"constant skin target calibration failed: {checked.reason}"
                )
        return law

    @staticmethod
    def _patch(skin: SkinRig, worlds: np.ndarray, side: str) -> np.ndarray:
        return np.vstack(
            [
                skin.skin(worlds, skin.foot_regions[side][region])
                for region in ("sole", "toe")
            ]
        )

    @classmethod
    def _observe(
        cls,
        query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
        skin: SkinRig,
        side: str,
        time_s: float,
        constants: Mapping[str, np.ndarray],
    ) -> dict[str, Any]:
        result = query.evaluate(time_s)
        if isinstance(result, SourceMotionUnavailable):
            raise ContractError("constant skin target source value is unavailable")
        row = _thaw(result.row)
        for foot_side, value in constants.items():
            row["feet"][foot_side]["target_offset_m"] = np.asarray(
                value, dtype=float
            ).tolist()
        pose = solve_airborne_plan_sample(
            query.context,
            row,
            body_response_sample=query._body_sample(query._exact_index(time_s), row),
        )
        worlds = np.asarray(
            _world_matrices(
                query._source,
                pose.translations,
                pose.rotations,
                query.context.base_s,
            ),
            dtype=float,
        )
        patch = cls._patch(skin, worlds, side)
        anchor = provider.anchor_for(side)
        target = (
            anchor.material_origin_m
            + query.context.forward * row["feet"][side]["forward_m"]
        )
        up_index = int(np.argmax(np.abs(query.context.up)))
        active = patch[:, up_index] <= patch[:, up_index].min() + 0.001
        error = 0.5 * (
            (target[active] - patch[active]).max(0)
            + (target[active] - patch[active]).min(0)
        )
        up = query.context.up
        gap = float(patch[:, up_index].min() - skin.ground)
        error -= up * float(error @ up)
        error += up * (_TARGET_GAP_M - gap)
        return {
            "loaded": bool(row["feet"][side]["contact"]),
            "required_correction_m": error,
            "gap_m": gap,
            "pose": pose,
            "row": row,
        }

    @staticmethod
    def _failure_reason(side: str, observation: Mapping[str, Any]) -> str | None:
        numeric = (
            observation["residual_m"],
            observation["minimum_gap_m"],
            observation["ik_target_residual_m"],
            observation["unreachable_extension_m"],
            observation["articulation_violation_degrees"],
        )
        if not all(math.isfinite(float(value)) for value in numeric):
            return f"{side} pointwise geometry contains non-finite values"
        if observation["loaded"] and observation["residual_m"] > _TOLERANCE_M:
            return f"{side} loaded residual exceeds refinement tolerance"
        if not observation["loaded"] and observation["minimum_gap_m"] < _TARGET_GAP_M:
            return f"{side} swing clearance is below target gap"
        if abs(observation["ik_target_residual_m"]) > _IK_TOLERANCE_M:
            return f"{side} foot target residual exceeds solver tolerance"
        if observation["unreachable_extension_m"] > _IK_TOLERANCE_M:
            return f"{side} target requires unreachable IK extension"
        if (
            observation["articulation_violation_degrees"]
            > _ARTICULATION_TOLERANCE_DEGREES
        ):
            return f"{side} target violates articulation envelope"
        return None

    def _observe_pair(
        self, query: SourceMotionQuery, time_s: float
    ) -> dict[str, dict[str, Any]]:
        """Reuse one owned query and row solve for the two material patches."""
        if query._transition_clearance is None:
            result = query.evaluate_with_target_offsets(time_s, self._constants)
        else:
            # value()/values() already proved the final query binding, which
            # includes the resolver and its raw calibrated law. Avoid hashing
            # that immutable source request again for every time in the batch.
            result = query._evaluate_owned(
                _finite_time(time_s),
                side="value",
                target_offsets=query._target_offsets(self._constants),
                transition_clearance_integrity_proved=True,
            )
        if isinstance(result, SourceMotionUnavailable):
            raise ContractError("constant skin target source value is unavailable")
        row = _thaw(result.row)
        pose = result.pose
        worlds = np.asarray(result.worlds)
        up_index = int(np.argmax(np.abs(query.context.up)))
        data = {}
        for side in ("left", "right"):
            patch = self._patch(self._skin, worlds, side)
            target = (
                self._provider.anchor_for(side).material_origin_m
                + query.context.forward * row["feet"][side]["forward_m"]
            )
            active = patch[:, up_index] <= patch[:, up_index].min() + 0.001
            error = 0.5 * (
                (target[active] - patch[active]).max(0)
                + (target[active] - patch[active]).min(0)
            )
            gap = float(patch[:, up_index].min() - self._skin.ground)
            error -= query.context.up * float(error @ query.context.up)
            error += query.context.up * (_TARGET_GAP_M - gap)
            data[side] = {
                "loaded": bool(row["feet"][side]["contact"]),
                "required_correction_m": error,
                "gap_m": gap,
                "pose": pose,
                "row": row,
            }
        return data

    def _observe_at(
        self, time_s: float, *, query: SourceMotionQuery | None = None
    ) -> ConstantSkinTargetValue | ConstantSkinTargetUnavailable:
        active_query = self._query if query is None else query
        observer = getattr(self._observe, "__func__", None)
        owned_evaluate = (
            type(active_query) is SourceMotionQuery
            and getattr(active_query.evaluate, "__func__", None)
            is SourceMotionQuery.evaluate
            and getattr(
                active_query.evaluate_with_target_offsets, "__func__", None
            )
            is SourceMotionQuery.evaluate_with_target_offsets
        )
        if observer is _DEFAULT_OBSERVE and owned_evaluate:
            data = self._observe_pair(active_query, time_s)
        else:
            # Preserve independently injected failure witnesses and subclasses.
            data = {
                side: self._observe(
                    active_query,
                    self._provider,
                    self._skin,
                    side,
                    time_s,
                    self._constants,
                )
                for side in ("left", "right")
            }
        observations: dict[str, Any] = {}
        failures = []
        for side, value in data.items():
            foot = value["pose"].feet[side]
            observation = {
                "loaded": value["loaded"],
                "residual_m": float(
                    np.linalg.norm(value["required_correction_m"])
                ),
                "minimum_gap_m": value["gap_m"],
                "clearance_ok": value["gap_m"] >= _TARGET_GAP_M,
                "ik_target_residual_m": float(foot["foot_target_residual_m"]),
                "unreachable_extension_m": float(
                    value["pose"].maximum_unreachable_extension_m
                ),
                "articulation_violation_degrees": max(
                    float(foot["articulation_envelope_violation_degrees"]),
                    float(
                        value[
                            "pose"
                        ].maximum_articulation_envelope_violation_degrees
                    ),
                ),
            }
            observations[side] = observation
            reason = self._failure_reason(side, observation)
            if reason is not None:
                failures.append(reason)

        branch = _freeze_data(
            {
                "status": "BRANCH_DERIVATIVE_AND_GLOBAL_C1_AUTHORITY_UNAVAILABLE_FROM_EXISTING_ROW_SOLVER",
                "pointwise_value_required_no_branch_authority": True,
            }
        )
        frozen_observations = _freeze_data(observations)
        if failures:
            return ConstantSkinTargetUnavailable(
                "UNAVAILABLE",
                float(time_s),
                "; ".join(failures),
                frozen_observations,
                branch,
            )

        corrections = MappingProxyType(
            {
                side: _readonly_vector(value)
                for side, value in self._constants.items()
            }
        )
        return ConstantSkinTargetValue(
            "AVAILABLE",
            float(time_s),
            _freeze_data(data["left"]["row"]),
            deepcopy(data["left"]["pose"]),
            corrections,
            frozen_observations,
            branch,
        )

    def value(
        self, time_s: Any
    ) -> ConstantSkinTargetValue | ConstantSkinTargetUnavailable:
        time = _finite_time(time_s)
        self._validate_integrity()
        return self._observe_at(time)

    def values(
        self, times_s: Any
    ) -> tuple[ConstantSkinTargetValue | ConstantSkinTargetUnavailable, ...]:
        """Check an owned immutable request batch after one integrity proof."""
        if isinstance(times_s, (str, bytes)):
            raise ContractError("constant skin target times must be an iterable")
        try:
            times = tuple(_finite_time(value) for value in times_s)
        except TypeError as exc:
            raise ContractError(
                "constant skin target times must be an iterable"
            ) from exc
        if not times:
            raise ContractError("constant skin target times must not be empty")
        self._validate_integrity()
        return tuple(self._observe_at(time) for time in times)


__all__ = [
    "CanonicalConstantSkinTargetLaw",
    "ConstantSkinTargetUnavailable",
    "ConstantSkinTargetValue",
]


_DEFAULT_OBSERVE = CanonicalConstantSkinTargetLaw._observe.__func__
