"""Source-bound pointwise skin-target laws.

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
    grounded_touchdown_target,
    solve_airborne_plan_sample,
)
from ..layers.leg_contact_resolve_v3 import _rotation_from_matrix
from .skin_rig import SkinRig, rotation_matrix
from .joint_contact_control import JointContactTrial, solve_loaded_contact_controls
from .source_motion_query import SourceMotionQuery, SourceMotionUnavailable, _thaw
from .support_anchors import CanonicalSupportAnchorProvider, _digest
from ..planning.grounded_gait import GroundedGait, smooth as _smooth

_TARGET_GAP_M = 0.0001
_TOLERANCE_M = 0.0002
_IK_TOLERANCE_M = 0.001
_ARTICULATION_TOLERANCE_DEGREES = 0.01
_DAMPING = 0.85
_MAX_CORRECTION_BODY_HEIGHTS = 0.06
_SEMANTIC_FOOT_FRAME_LAW = "canonical_semantic_foot_frame_targets.v2"
_JOINT_CONTACT_LAW = "canonical_semantic_joint_contact_targets.v3"
_CONSTANT_LAW = "canonical_constant_skin_targets.v1"
_FRAME_MAPPING_TOLERANCE_M = 1e-10
_FRAME_MAPPING_MAX_ITERATIONS = 40
_FRAME_MAPPING_DAMPING = 0.5
_SUPPORT_ADMISSION_POLICY_ID = "canonical_touchdown_fixed_band.v2"
_SUPPORT_BAND_M = 0.00125
_BUILD_TOKEN = object()


def _semantic_law(value: str) -> bool:
    return value in (_SEMANTIC_FOOT_FRAME_LAW, _JOINT_CONTACT_LAW)


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


def _source_unavailable_error(result: SourceMotionUnavailable) -> ContractError:
    return ContractError(
        "constant skin target source value is unavailable: "
        f"status={result.status} time_s={result.time_s!r} reason={result.reason}"
    )


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
    """A selected, source-bound skin-target law bound to one actual query."""

    def __init__(
        self,
        query: SourceMotionQuery,
        calibration_query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
        skin: SkinRig,
        constants: Mapping[str, np.ndarray],
        *,
        law_id: str = _CONSTANT_LAW,
        local_material_references: Mapping[str, np.ndarray] | None = None,
        support_patch_indices: Mapping[str, tuple[int, ...]] | None = None,
        joint_contact_end_controls: Mapping[str, np.ndarray] | None = None,
        joint_contact_lift_references: Mapping[str, np.ndarray] | None = None,
        boundary_residuals_m: Mapping[str, Mapping[str, float]] | None = None,
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
        if law_id not in (_CONSTANT_LAW, _SEMANTIC_FOOT_FRAME_LAW, _JOINT_CONTACT_LAW):
            raise ContractError("unsupported skin target law")
        self._law_id = law_id
        if _semantic_law(law_id):
            if local_material_references is None or set(local_material_references) != {"left", "right"}:
                raise ContractError("semantic foot-frame law requires bilateral local material references")
            self._local_material_references = MappingProxyType(
                {side: _readonly_vector(local_material_references[side]) for side in ("left", "right")}
            )
            if support_patch_indices is None or set(support_patch_indices) != {"left", "right"}:
                raise ContractError("semantic foot-frame law requires bilateral frozen support membership")
            frozen_support = {}
            for side in ("left", "right"):
                indices = tuple(int(value) for value in support_patch_indices[side])
                patch_count = len(provider.anchor_for(side).material_vertex_indices)
                if len(indices) < 3 or len(set(indices)) != len(indices) or any(
                    value < 0 or value >= patch_count for value in indices
                ):
                    raise ContractError(
                        "semantic foot-frame support membership requires at least "
                        f"three distinct valid material vertices: side={side} count={len(indices)}"
                    )
                frozen_support[side] = indices
            self._support_patch_indices = MappingProxyType(frozen_support)
            if law_id == _JOINT_CONTACT_LAW:
                if joint_contact_end_controls is None or set(joint_contact_end_controls) != {"left", "right"}:
                    raise ContractError("joint contact law requires bilateral endpoint controls")
                frozen_controls = {}
                for side in ("left", "right"):
                    control = np.asarray(joint_contact_end_controls[side], dtype=float)
                    if control.shape != (4,) or not np.isfinite(control).all():
                        raise ContractError("joint contact endpoint controls must be finite 4-vectors")
                    control = np.array(control, copy=True); control.setflags(write=False)
                    frozen_controls[side] = control
                self._joint_contact_end_controls = MappingProxyType(frozen_controls)
                if joint_contact_lift_references is not None and set(joint_contact_lift_references) != {"left", "right"}:
                    raise ContractError("joint contact lift references must be bilateral")
                self._joint_contact_lift_references = (
                    None if joint_contact_lift_references is None else MappingProxyType({
                        side: _readonly_vector(joint_contact_lift_references[side])
                        for side in ("left", "right")
                    })
                )
            else:
                self._joint_contact_end_controls = None
                self._joint_contact_lift_references = None
        else:
            if local_material_references is not None:
                raise ContractError("constant skin target law does not accept foot-frame references")
            self._local_material_references = None
            if support_patch_indices is not None:
                raise ContractError("constant skin target law does not accept support membership")
            self._support_patch_indices = None
            self._joint_contact_end_controls = None
            self._joint_contact_lift_references = None
        self._boundary_residuals_m = _freeze_data(
            {} if boundary_residuals_m is None else boundary_residuals_m
        )
        self._calibration_sha256 = self._constants_sha256()
        self._law_binding_sha256 = self._current_law_binding_sha256()
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
                "body_support_control": (
                    query.body_support_control_receipt()
                    if hasattr(query, "body_support_control_receipt")
                    else None
                ),
            }
        )

    def frozen_anchor_binding_sha256(self) -> str:
        """Digest exact immutable anchor/template authority across query rebinds."""
        return _digest({
            "provider": self._provider.receipt(),
            "anchors": {
                side: {
                    "origin_m": self._provider.anchor_for(side).material_origin_m.tolist(),
                    "material_vertex_indices": list(self._provider.anchor_for(side).material_vertex_indices),
                    "support_positions": (
                        None if self._support_patch_indices is None
                        else list(self._support_patch_indices[side])
                    ),
                    "local_material_reference": (
                        None if self._local_material_references is None
                        else self._local_material_references[side].tolist()
                    ),
                    "joint_contact_lift_reference": (
                        None if self._joint_contact_lift_references is None
                        else self._joint_contact_lift_references[side].tolist()
                    ),
                }
                for side in ("left", "right")
            },
        })

    def with_query(self, query: SourceMotionQuery) -> "CanonicalConstantSkinTargetLaw":
        """Rebind one final pose query without recalibrating frozen geometry."""
        self._validate_integrity()
        self._validate_actual_query(query, self._provider)
        return type(self)(
            query, self._calibration_query, self._provider, self._skin,
            self._constants, law_id=self._law_id,
            local_material_references=self._local_material_references,
            support_patch_indices=self._support_patch_indices,
            joint_contact_end_controls=self._joint_contact_end_controls,
            joint_contact_lift_references=self._joint_contact_lift_references,
            boundary_residuals_m=self._boundary_residuals_m,
            _token=_BUILD_TOKEN,
        )

    def _constants_sha256(self) -> str:
        return hashlib.sha256(
            b"".join(
                np.asarray(self._constants[side], dtype="<f8").tobytes()
                for side in ("left", "right")
            )
        ).hexdigest()

    def _current_law_binding_sha256(self) -> str:
        return _digest({
            "law_id": self._law_id,
            "constants": {
                side: self._constants[side].tolist() for side in ("left", "right")
            },
            "local_material_references": (
                None
                if self._local_material_references is None
                else {
                    side: self._local_material_references[side].tolist()
                    for side in ("left", "right")
                }
            ),
            "support_patch_indices": (
                None
                if self._support_patch_indices is None
                else {
                    side: list(self._support_patch_indices[side])
                    for side in ("left", "right")
                }
            ),
            "joint_contact_policy_end_controls": (
                None if self._joint_contact_end_controls is None else {
                    side: self._joint_contact_end_controls[side].tolist()
                    for side in ("left", "right")
                }
            ),
            "joint_contact_lift_references": (
                None if self._joint_contact_lift_references is None else {
                    side: self._joint_contact_lift_references[side].tolist()
                    for side in ("left", "right")
                }
            ),
            "joint_contact_policy": (
                None if self._law_id != _JOINT_CONTACT_LAW else {
                    "policy_id": "source_joint_contact_minimax.v1",
                    "target_offset_envelope_body_m": _MAX_CORRECTION_BODY_HEIGHTS,
                    "pitch_domain_degrees": [-45.0, 85.0],
                    "counterrotation_domain_degrees": [-45.0, 45.0],
                    "swing_release_fraction": 0.35,
                }
            ),
            "support_admission_policy": (
                None
                if not _semantic_law(self._law_id)
                else {
                    "policy_id": _SUPPORT_ADMISSION_POLICY_ID,
                    "fixed_band_m": _SUPPORT_BAND_M,
                }
            ),
            "boundary_residuals_m": _thaw(self._boundary_residuals_m),
        })

    def _validate_integrity(self) -> None:
        if self._constants_sha256() != self._calibration_sha256:
            raise ContractError(
                "constant skin target calibration differs from validated values"
            )
        if self._current_law_binding_sha256() != self._law_binding_sha256:
            raise ContractError("skin target law binding differs from validated values")
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
        law_id: str = _CONSTANT_LAW,
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
        if law_id not in (_CONSTANT_LAW, _SEMANTIC_FOOT_FRAME_LAW, _JOINT_CONTACT_LAW):
            raise ContractError("unsupported skin target law")
        constants = {side: np.zeros(3) for side in ("left", "right")}
        if _semantic_law(law_id):
            references = cls._build_local_material_references(
                calibration_query, provider, skin
            )
            support_indices = cls._build_support_patch_indices(
                calibration_query, provider
            )
            boundary_residuals = cls._validate_foot_frame_boundaries(
                calibration_query, provider, skin, references
            )
            endpoint_controls = (
                {side: np.zeros(4) for side in ("left", "right")}
                if law_id == _JOINT_CONTACT_LAW else None
            )
            law = cls(
                query,
                calibration_query,
                provider,
                skin,
                constants,
                law_id=law_id,
                local_material_references=references,
                support_patch_indices=support_indices,
                joint_contact_end_controls=endpoint_controls,
                boundary_residuals_m=boundary_residuals,
                _token=_BUILD_TOKEN,
            )
            if law_id == _JOINT_CONTACT_LAW:
                period = 2.0 * calibration_query._locomotion_gait.step_period_s
                endpoint_controls = {}
                for side, offset in (("left", 0.0), ("right", calibration_query._locomotion_gait.step_period_s)):
                    lift = (offset + period * calibration_query._locomotion_gait.duty_factor) % period
                    endpoint_controls[side] = law._solve_joint_contact_endpoint(
                        calibration_query, side, lift
                    )
                law = cls(
                    query, calibration_query, provider, skin, constants,
                    law_id=law_id,
                    local_material_references=references,
                    support_patch_indices=support_indices,
                    joint_contact_end_controls=endpoint_controls,
                    boundary_residuals_m=boundary_residuals,
                    _token=_BUILD_TOKEN,
                )
                lift_references = law._build_joint_contact_lift_references(
                    calibration_query
                )
                law = cls(
                    query, calibration_query, provider, skin, constants,
                    law_id=law_id,
                    local_material_references=references,
                    support_patch_indices=support_indices,
                    joint_contact_end_controls=endpoint_controls,
                    joint_contact_lift_references=lift_references,
                    boundary_residuals_m=boundary_residuals,
                    _token=_BUILD_TOKEN,
                )
            validation_phases = [
                provider.anchor_for("left").touchdown_phase_s,
                provider.anchor_for("right").touchdown_phase_s,
            ]
            if law_id == _JOINT_CONTACT_LAW:
                period = 2.0 * calibration_query._locomotion_gait.step_period_s
                validation_phases.extend(
                    (offset + period * calibration_query._locomotion_gait.duty_factor) % period
                    for offset in (0.0, calibration_query._locomotion_gait.step_period_s)
                )
            for phase in validation_phases:
                checked = law._observe_at(phase, query=calibration_query)
                if isinstance(checked, ConstantSkinTargetUnavailable):
                    raise ContractError(
                        "semantic foot-frame target calibration failed: "
                        f"time_s={phase!r} {checked.reason}; "
                        f"observations={_thaw(checked.observations)!r}; "
                        "joint_contact_endpoint_controls="
                        f"{None if law._joint_contact_end_controls is None else {side: law._joint_contact_end_controls[side].tolist() for side in ('left', 'right')}!r}"
                    )
            return law
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
            law_id=law_id,
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
    def _build_support_patch_indices(
        query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
    ) -> dict[str, tuple[int, ...]]:
        """Freeze canonical touchdown support membership before any trial solve."""
        up_index = int(np.argmax(np.abs(query.context.up)))
        result = {}
        for side in ("left", "right"):
            anchor = provider.anchor_for(side)
            origin = anchor.material_origin_m
            floor = float(origin[:, up_index].min())
            selected = []
            seen_vertices = set()
            for index in np.flatnonzero(
                origin[:, up_index] <= floor + _SUPPORT_BAND_M
            ):
                vertex_id = anchor.material_vertex_indices[int(index)]
                if vertex_id not in seen_vertices:
                    selected.append(int(index))
                    seen_vertices.add(vertex_id)
            result[side] = tuple(selected)
        return result

    @staticmethod
    def _foot_frame(
        query: SourceMotionQuery, worlds: np.ndarray, side: str
    ) -> tuple[np.ndarray, np.ndarray]:
        node = query.context.legs[side][-1]
        matrix = np.asarray(worlds[node], dtype=float)
        return (
            np.asarray(matrix[:3, 3], dtype=float),
            rotation_matrix(_rotation_from_matrix(worlds[node])),
        )

    @classmethod
    def _build_local_material_references(
        cls,
        query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
        skin: SkinRig,
    ) -> dict[str, np.ndarray]:
        """Bind one fixed source material witness in each semantic MTP frame."""
        references = {}
        up_index = int(np.argmax(np.abs(query.context.up)))
        gait = query._locomotion_gait
        if not isinstance(gait, GroundedGait):
            raise ContractError("semantic foot-frame law requires grounded locomotion")
        cycle = 2.0 * gait.step_period_s
        for side, offset in (("left", 0.0), ("right", gait.step_period_s)):
            anchor = provider.anchor_for(side)
            lift_off = (offset + cycle * gait.duty_factor) % cycle
            result = query._evaluate_owned(
                lift_off,
                side="left_limit",
                target_offsets={foot: [0.0, 0.0, 0.0] for foot in ("left", "right")},
            )
            if isinstance(result, SourceMotionUnavailable):
                raise _source_unavailable_error(result)
            row = _thaw(result.row)
            effector, rotation = cls._foot_frame(
                query, np.asarray(result.worlds), side
            )
            target_patch = (
                anchor.material_origin_m
                + query.context.forward * row["feet"][side]["forward_m"]
            )
            target = np.asarray(
                target_patch[anchor.lowest_patch_index], dtype=float
            )
            anchor_gap = float(target[up_index] - skin.ground)
            target += query.context.up * (_TARGET_GAP_M - anchor_gap)
            raw_row = deepcopy(row)
            for foot in raw_row["feet"].values():
                foot.pop("target_offset_m", None)
            declared = grounded_touchdown_target(
                query.context,
                raw_row,
                side=side,
                body_response_sample=query._body_sample(None, raw_row),
            )
            declared_effector = np.asarray(
                declared["target_foot_world_m"], dtype=float
            )
            references[side] = rotation.T @ (target - declared_effector)
        return references

    @classmethod
    def _validate_foot_frame_boundaries(
        cls,
        query: SourceMotionQuery,
        provider: CanonicalSupportAnchorProvider,
        skin: SkinRig,
        references: Mapping[str, np.ndarray],
    ) -> dict[str, dict[str, float]]:
        gait = query._locomotion_gait
        if not isinstance(gait, GroundedGait):
            raise ContractError("semantic foot-frame law requires grounded locomotion")
        cycle = 2.0 * gait.step_period_s
        zero = {side: [0.0, 0.0, 0.0] for side in ("left", "right")}
        up_index = int(np.argmax(np.abs(query.context.up)))
        residuals = {}
        for side, offset in (("left", 0.0), ("right", gait.step_period_s)):
            lift = (offset + cycle * gait.duty_factor) % cycle
            touchdown = offset % cycle
            if touchdown <= lift:
                touchdown += cycle
            side_residuals = {}
            for label, time_s in (("lift_off", lift), ("touchdown", touchdown)):
                result = query._evaluate_owned(
                    time_s, side="left_limit", target_offsets=zero
                )
                if isinstance(result, SourceMotionUnavailable):
                    raise _source_unavailable_error(result)
                row = _thaw(result.row)
                for foot in row["feet"].values():
                    foot.pop("target_offset_m", None)
                _, rotation = cls._foot_frame(query, np.asarray(result.worlds), side)
                declared = grounded_touchdown_target(
                    query.context,
                    row,
                    side=side,
                    body_response_sample=query._body_sample(None, row),
                )
                transported = (
                    np.asarray(declared["target_foot_world_m"], dtype=float)
                    + rotation @ references[side]
                )
                anchor = provider.anchor_for(side)
                support = np.asarray(
                    anchor.material_origin_m[anchor.lowest_patch_index], dtype=float
                ) + query.context.forward * row["feet"][side]["forward_m"]
                anchor_gap = float(
                    anchor.material_origin_m[anchor.lowest_patch_index][up_index]
                    - skin.ground
                )
                support += query.context.up * (_TARGET_GAP_M - anchor_gap)
                value = float(np.linalg.norm(transported - support))
                if value > _TOLERANCE_M:
                    raise ContractError(
                        f"semantic foot-frame {side} {label} target is incompatible with support anchor"
                    )
                side_residuals[f"{label}_m"] = value
            residuals[side] = side_residuals
        return residuals

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
            raise _source_unavailable_error(result)
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

    def _observe_semantic_foot_frame_pair(
        self, query: SourceMotionQuery, time_s: float
    ) -> dict[str, dict[str, Any]]:
        """Map a target-owned material path through a fixed semantic MTP frame."""
        zero = {side: np.zeros(3) for side in ("left", "right")}
        result = query.evaluate_with_target_offsets(time_s, zero)
        if isinstance(result, SourceMotionUnavailable):
            raise _source_unavailable_error(result)
        row = _thaw(result.row)
        joint_coordinates = None
        if self._law_id == _JOINT_CONTACT_LAW:
            joint_coordinates = {}
            controls = {}
            peak = float(query._locomotion_gait.push_off_pitch_degrees)
            for side in ("left", "right"):
                foot = row["feet"][side]
                if foot["contact"]:
                    gain = 0.0 if peak == 0.0 else float(np.clip(foot["foot_pitch_degrees"] / peak, 0.0, 1.0))
                else:
                    gain = 1.0 - _smooth(float(foot["swing_phase"]) / 0.35)
                endpoint = self._joint_contact_end_controls[side]
                values = np.asarray([
                    foot["foot_pitch_degrees"] + gain * (endpoint[0] - peak),
                    gain * endpoint[1], gain * endpoint[2], gain * endpoint[3],
                ])
                joint_coordinates[side] = values
                controls[side] = {
                    "authored_pitch_degrees": float(values[0]),
                    "foot_counterrotation_degrees": float(values[1]),
                    "target_offset_m": (
                        query.context.forward * values[2] + query.context.up * values[3]
                    ).tolist(),
                }
            result = query.evaluate_with_joint_contact_controls(time_s, controls)
            if isinstance(result, SourceMotionUnavailable):
                raise _source_unavailable_error(result)
            row = _thaw(result.row)
        nominal_worlds = np.asarray(result.worlds)
        targets: dict[str, np.ndarray] = {}
        support_targets: dict[str, np.ndarray | None] = {}
        corrections: dict[str, np.ndarray] = {}
        up_index = int(np.argmax(np.abs(query.context.up)))
        for side in ("left", "right"):
            anchor = self._provider.anchor_for(side)
            target_patch = (
                anchor.material_origin_m
                + query.context.forward * row["feet"][side]["forward_m"]
            )
            base_gap = float(
                anchor.material_origin_m[anchor.lowest_patch_index][up_index]
                - self._skin.ground
            )
            target_patch = target_patch + query.context.up * (_TARGET_GAP_M - base_gap)
            _, rotation = self._foot_frame(query, nominal_worlds, side)
            if row["feet"][side]["contact"]:
                material_target = np.asarray(
                    target_patch[anchor.lowest_patch_index], dtype=float
                )
                support_targets[side] = target_patch
            else:
                raw_row = deepcopy(row)
                for foot in raw_row["feet"].values():
                    foot.pop("target_offset_m", None)
                declared = grounded_touchdown_target(
                    query.context,
                    raw_row,
                    side=side,
                    body_response_sample=query._body_sample(
                        query._exact_index(time_s), raw_row
                    ),
                )
                declared_effector = np.asarray(
                    declared["target_foot_world_m"], dtype=float
                )
                local_reference = self._local_material_references[side]
                if self._joint_contact_lift_references is not None:
                    blend = _smooth(float(np.clip(row["feet"][side]["swing_phase"], 0.0, 1.0)))
                    local_reference = (
                        (1.0 - blend) * self._joint_contact_lift_references[side]
                        + blend * local_reference
                    )
                material_target = (
                    declared_effector
                    + rotation @ local_reference
                )
                support_targets[side] = None
            targets[side] = material_target
            corrections[side] = (
                np.zeros(3)
                if joint_coordinates is None
                else query.context.forward * joint_coordinates[side][2]
                + query.context.up * joint_coordinates[side][3]
            )

        pose = result.pose
        worlds = nominal_worlds
        residuals = {
            side: np.full(3, math.inf) for side in ("left", "right")
        }
        loaded_max_residuals = {side: math.inf for side in ("left", "right")}
        for _ in range(_FRAME_MAPPING_MAX_ITERATIONS):
            correction_norms = {
                side: float(np.linalg.norm(value))
                for side, value in corrections.items()
            }
            envelope = _MAX_CORRECTION_BODY_HEIGHTS * query.context.body_height
            if max(correction_norms.values()) > envelope:
                side = max(correction_norms, key=correction_norms.get)
                raise ContractError(
                    "semantic foot-frame correction exceeds the solver envelope: "
                    f"side={side} time_s={time_s!r} "
                    f"correction_m={correction_norms[side]!r} envelope_m={envelope!r}"
                )
            if joint_coordinates is None:
                solved = query.evaluate_with_target_offsets(time_s, corrections)
            else:
                controls = {}
                for side in ("left", "right"):
                    values = joint_coordinates[side]
                    offset = corrections[side]
                    envelope = _MAX_CORRECTION_BODY_HEIGHTS * query.context.body_height
                    if np.linalg.norm(offset) > envelope:
                        raise ContractError("joint contact target offset exceeds body-height envelope")
                    controls[side] = {
                        "authored_pitch_degrees": float(values[0]),
                        "foot_counterrotation_degrees": float(values[1]),
                        "target_offset_m": np.asarray(offset, dtype=float).tolist(),
                    }
                solved = query.evaluate_with_joint_contact_controls(time_s, controls)
            if isinstance(solved, SourceMotionUnavailable):
                raise _source_unavailable_error(solved)
            row = _thaw(solved.row)
            pose = solved.pose
            worlds = np.asarray(solved.worlds)
            for side in ("left", "right"):
                anchor = self._provider.anchor_for(side)
                patch = self._patch(self._skin, worlds, side)
                if support_targets[side] is not None:
                    target_patch = support_targets[side]
                    active = np.asarray(self._support_patch_indices[side], dtype=int)
                    vertex_errors = target_patch[active] - patch[active]
                    error = 0.5 * (
                        vertex_errors.max(0) + vertex_errors.min(0)
                    )
                    loaded_max_residuals[side] = float(
                        np.linalg.norm(vertex_errors, axis=1).max()
                    )
                    gap = float(patch[:, up_index].min() - self._skin.ground)
                    error -= query.context.up * float(error @ query.context.up)
                    error += query.context.up * (_TARGET_GAP_M - gap)
                    residuals[side] = error
                else:
                    witness = patch[anchor.lowest_patch_index]
                    error = targets[side] - witness
                    # T(t) is authoritative in all three axes.  The full patch
                    # contributes only the floor inequality in addition to the
                    # transported material-witness equality.
                    requested_gap = _TARGET_GAP_M
                    gap = float(patch[:, up_index].min() - self._skin.ground)
                    error += query.context.up * max(0.0, requested_gap - gap)
                    residuals[side] = error
            if max(np.linalg.norm(value) for value in residuals.values()) <= (
                _FRAME_MAPPING_TOLERANCE_M
            ):
                break
            corrections = {
                side: corrections[side] + _FRAME_MAPPING_DAMPING * residuals[side]
                for side in ("left", "right")
            }

        data = {}
        for side in ("left", "right"):
            patch = self._patch(self._skin, worlds, side)
            data[side] = {
                "loaded": bool(row["feet"][side]["contact"]),
                "required_correction_m": residuals[side],
                "material_mapping_residual_m": float(
                    np.linalg.norm(residuals[side])
                ),
                "loaded_material_max_residual_m": (
                    loaded_max_residuals[side]
                    if row["feet"][side]["contact"]
                    else 0.0
                ),
                "gap_m": float(patch[:, up_index].min() - self._skin.ground),
                "pose": pose,
                "row": row,
                "correction_m": corrections[side],
                "material_witness_m": patch[anchor.lowest_patch_index].tolist(),
                "semantic_target_m": targets[side].tolist(),
            }
        return data

    def _build_joint_contact_lift_references(
        self, query: SourceMotionQuery
    ) -> dict[str, np.ndarray]:
        """Bind the emitted constrained lift witness in its semantic MTP frame."""
        cycle = 2.0 * query._locomotion_gait.step_period_s
        zero = {foot: [0.0, 0.0, 0.0] for foot in ("left", "right")}
        references = {}
        for side, offset in (("left", 0.0), ("right", query._locomotion_gait.step_period_s)):
            lift = (offset + cycle * query._locomotion_gait.duty_factor) % cycle
            nominal = query._evaluate_owned(lift, side="left_limit", target_offsets=zero)
            if isinstance(nominal, SourceMotionUnavailable):
                raise _source_unavailable_error(nominal)
            row = _thaw(nominal.row)
            peak = float(query._locomotion_gait.push_off_pitch_degrees)
            controls = {}
            for foot_side in ("left", "right"):
                foot = row["feet"][foot_side]
                gain = (
                    0.0 if peak == 0.0
                    else float(np.clip(foot["foot_pitch_degrees"] / peak, 0.0, 1.0))
                ) if foot["contact"] else 1.0 - _smooth(float(foot["swing_phase"]) / 0.35)
                endpoint = self._joint_contact_end_controls[foot_side]
                values = np.asarray([
                    foot["foot_pitch_degrees"] + gain * (endpoint[0] - peak),
                    gain * endpoint[1], gain * endpoint[2], gain * endpoint[3],
                ])
                controls[foot_side] = {
                    "authored_pitch_degrees": float(values[0]),
                    "foot_counterrotation_degrees": float(values[1]),
                    "target_offset_m": (
                        query.context.forward * values[2]
                        + query.context.up * values[3]
                    ).tolist(),
                }
            solved = query.evaluate_with_joint_contact_controls(
                lift, controls, side="left_limit"
            )
            if isinstance(solved, SourceMotionUnavailable):
                raise _source_unavailable_error(solved)
            worlds = np.asarray(solved.worlds)
            patch = self._patch(self._skin, worlds, side)
            anchor = self._provider.anchor_for(side)
            effector, rotation = self._foot_frame(query, worlds, side)
            references[side] = rotation.T @ (
                patch[anchor.lowest_patch_index] - effector
            )
        return references

    def _solve_joint_contact_endpoint(
        self, query: SourceMotionQuery, side: str, time_s: float
    ) -> np.ndarray:
        zero = {foot_side: [0.0, 0.0, 0.0] for foot_side in ("left", "right")}
        nominal = query._evaluate_owned(
            time_s, side="left_limit", target_offsets=zero
        )
        if isinstance(nominal, SourceMotionUnavailable):
            raise _source_unavailable_error(nominal)
        row = _thaw(nominal.row)
        fixed = {
            foot_side: np.asarray([
                row["feet"][foot_side]["foot_pitch_degrees"], 0.0, 0.0, 0.0
            ], dtype=float)
            for foot_side in ("left", "right")
        }

        def controls_for(active_side: str, x: np.ndarray) -> dict[str, Any]:
            envelope = _MAX_CORRECTION_BODY_HEIGHTS * query.context.body_height
            if np.linalg.norm(x[2:]) > envelope:
                raise ContractError("joint contact target offset exceeds body-height envelope")
            controls = {}
            for foot_side in ("left", "right"):
                values = x if foot_side == active_side else fixed[foot_side]
                controls[foot_side] = {
                    "authored_pitch_degrees": float(values[0]),
                    "foot_counterrotation_degrees": float(values[1]),
                    "target_offset_m": (
                        query.context.forward * float(values[2])
                        + query.context.up * float(values[3])
                    ).tolist(),
                }
            return controls

        def evaluate(active_side: str, x: np.ndarray) -> JointContactTrial:
            controls = controls_for(active_side, x)
            solved = query.evaluate_with_joint_contact_controls(
                time_s, controls, side="left_limit"
            )
            if isinstance(solved, SourceMotionUnavailable):
                raise _source_unavailable_error(solved)
            anchor = self._provider.anchor_for(active_side)
            patch = self._patch(self._skin, np.asarray(solved.worlds), active_side)
            full_skin = self._skin.skin(np.asarray(solved.worlds))
            target = anchor.material_origin_m + query.context.forward * row["feet"][active_side]["forward_m"]
            up_i = int(np.argmax(np.abs(query.context.up)))
            base_gap = anchor.material_origin_m[anchor.lowest_patch_index][up_i] - self._skin.ground
            target = target + query.context.up * (_TARGET_GAP_M - base_gap)
            active = np.asarray(self._support_patch_indices[active_side], dtype=int)
            foot = solved.pose.feet[active_side]
            return JointContactTrial(
                patch[active] - target[active], target[active],
                float(full_skin[:, up_i].min() - self._skin.ground),
                float(foot["foot_target_residual_m"]),
                float(solved.pose.maximum_unreachable_extension_m),
                float(solved.pose.maximum_articulation_envelope_violation_degrees),
                float(foot["solved_foot_pitch_degrees"]),
            )
        active_sides = tuple(
            foot_side for foot_side in ("left", "right")
            if row["feet"][foot_side]["contact"]
        )
        for _ in range(2):
            for active_side in active_sides:
                solution = solve_loaded_contact_controls(
                    lambda x, active_side=active_side: evaluate(active_side, x),
                    declared_pitch_degrees=float(row["feet"][active_side]["foot_pitch_degrees"]),
                )
                fixed[active_side] = np.asarray(solution.coordinates, dtype=float)

        controls = controls_for(side, fixed[side])
        solved = query.evaluate_with_joint_contact_controls(
            time_s, controls, side="left_limit"
        )
        if isinstance(solved, SourceMotionUnavailable):
            raise _source_unavailable_error(solved)
        worlds = np.asarray(solved.worlds)
        up_i = int(np.argmax(np.abs(query.context.up)))
        full_skin = self._skin.skin(worlds)
        full_argmin = int(np.argmin(full_skin[:, up_i]))
        full_gap = float(full_skin[full_argmin, up_i] - self._skin.ground)
        failures = []
        for active_side in active_sides:
            trial = evaluate(active_side, fixed[active_side])
            maximum = float(np.linalg.norm(trial.material_errors_m, axis=1).max())
            if maximum > _TOLERANCE_M:
                failures.append(f"{active_side} residual={maximum!r}")
        final_ik = max(
            float(solved.pose.feet[foot_side]["foot_target_residual_m"])
            for foot_side in active_sides
        )
        final_extension = float(solved.pose.maximum_unreachable_extension_m)
        final_articulation = float(
            solved.pose.maximum_articulation_envelope_violation_degrees
        )
        self._require_joint_endpoint_final(
            time_s=time_s,
            full_gap_m=full_gap,
            full_argmin_vertex=full_argmin,
            ik_residual_m=final_ik,
            extension_m=final_extension,
            articulation_degrees=final_articulation,
            contact_failures=failures,
        )
        return np.asarray(fixed[side], dtype=float)

    @staticmethod
    def _require_joint_endpoint_final(
        *,
        time_s: float,
        full_gap_m: float,
        full_argmin_vertex: int,
        ik_residual_m: float,
        extension_m: float,
        articulation_degrees: float,
        contact_failures: list[str],
    ) -> None:
        """Reject an optimizer fallback unless the exact combined pose is feasible."""
        if (
            full_gap_m < _TARGET_GAP_M
            or ik_residual_m > _IK_TOLERANCE_M
            or extension_m > _IK_TOLERANCE_M
            or articulation_degrees > _ARTICULATION_TOLERANCE_DEGREES
            or contact_failures
        ):
            raise ContractError(
                "bilateral joint contact endpoint is unavailable: "
                f"time_s={time_s!r} full_skin_gap_m={full_gap_m!r} "
                f"full_skin_argmin_vertex={full_argmin_vertex!r} "
                f"ik_residual_m={ik_residual_m!r} extension_m={extension_m!r} "
                f"articulation_degrees={articulation_degrees!r} "
                + "; ".join(contact_failures)
            )

    @staticmethod
    def _failure_reason(side: str, observation: Mapping[str, Any]) -> str | None:
        numeric = (
            observation["residual_m"],
            observation["minimum_gap_m"],
            observation["ik_target_residual_m"],
            observation["unreachable_extension_m"],
            observation["articulation_violation_degrees"],
            observation.get("loaded_material_max_residual_m", 0.0),
        )
        if not all(math.isfinite(float(value)) for value in numeric):
            return f"{side} pointwise geometry contains non-finite values"
        mapping_residual = observation.get("material_mapping_residual_m")
        if (
            mapping_residual is not None
            and mapping_residual > _FRAME_MAPPING_TOLERANCE_M
        ):
            return f"{side} semantic foot-frame mapping did not converge"
        loaded_residual = observation.get(
            "loaded_material_max_residual_m", observation["residual_m"]
        )
        if observation["loaded"] and loaded_residual > _TOLERANCE_M:
            return f"{side} loaded residual exceeds refinement tolerance"
        numerical_gap_tolerance = (
            _FRAME_MAPPING_TOLERANCE_M
            if observation.get("material_mapping_residual_m") is not None
            else 0.0
        )
        if (
            not observation["loaded"]
            and observation["minimum_gap_m"] + numerical_gap_tolerance
            < _TARGET_GAP_M
        ):
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
        if _semantic_law(self._law_id):
            return self._observe_semantic_foot_frame_pair(query, time_s)
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
                authored_material_integrity_proved=True,
            )
        if isinstance(result, SourceMotionUnavailable):
            raise _source_unavailable_error(result)
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
            if "material_mapping_residual_m" in value:
                observation["material_mapping_residual_m"] = float(
                    value["material_mapping_residual_m"]
                )
            if "loaded_material_max_residual_m" in value:
                observation["loaded_material_max_residual_m"] = float(
                    value["loaded_material_max_residual_m"]
                )
            for name in ("material_witness_m", "semantic_target_m"):
                if name in value:
                    observation[name] = list(value[name])
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

        corrections = MappingProxyType({
            side: _readonly_vector(
                data[side].get("correction_m", self._constants[side])
            )
            for side in ("left", "right")
        })
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

    def receipt(self) -> dict[str, Any]:
        self._validate_integrity()
        if self._law_id == _CONSTANT_LAW:
            return {
                "law_id": self._law_id,
                "binding_sha256": self._law_binding_sha256,
                "classification": (
                    "pointwise checked values; derivative and global-C1 authority unavailable"
                ),
            }
        return {
            "law_id": self._law_id,
            "binding_sha256": (
                _digest({
                    "law_binding_sha256": self._law_binding_sha256,
                    "query_binding_sha256": self._query_binding_sha256,
                })
                if self._law_id == _JOINT_CONTACT_LAW
                else self._law_binding_sha256
            ),
            "law_binding_sha256": (
                self._law_binding_sha256
                if self._law_id == _JOINT_CONTACT_LAW else None
            ),
            "query_binding_sha256": (
                self._query_binding_sha256
                if self._law_id == _JOINT_CONTACT_LAW else None
            ),
            "material_reference": "provider-fixed full-skin vertex in semantic MTP local frame",
            "swing_target": "E_declared(t) + R_declared(t) * local_material_reference",
            "support_target": "immutable canonical material support subset; full sole/toe skin floor",
            "joint_contact_policy": (
                None if self._joint_contact_end_controls is None else {
                    "policy_id": "source_joint_contact_minimax.v1",
                    "endpoint_controls": {
                        side: self._joint_contact_end_controls[side].tolist()
                        for side in ("left", "right")
                    },
                    "lift_material_references_mtp_local_m": {
                        side: self._joint_contact_lift_references[side].tolist()
                        for side in ("left", "right")
                    },
                    "swing_reference_transport": "smooth_lift_to_touchdown_mtp_local.v1",
                    "target_offset_envelope_body_heights": _MAX_CORRECTION_BODY_HEIGHTS,
                    "swing_release_fraction": 0.35,
                }
            ),
            "loaded_support_membership": {
                "policy_id": _SUPPORT_ADMISSION_POLICY_ID,
                "selection": "canonical touchdown vertices within fixed support band",
                "support_band_m": _SUPPORT_BAND_M,
                "sides": {
                    side: {
                        "count": len(self._support_patch_indices[side]),
                        "region_counts": {
                            "sole": sum(
                                index < len(self._skin.foot_regions[side]["sole"])
                                for index in self._support_patch_indices[side]
                            ),
                            "toe": sum(
                                index >= len(self._skin.foot_regions[side]["sole"])
                                for index in self._support_patch_indices[side]
                            ),
                        },
                        "material_vertex_ids_sha256": hashlib.sha256(
                            np.asarray(
                                [
                                    self._provider.anchor_for(side).material_vertex_indices[
                                        index
                                    ]
                                    for index in self._support_patch_indices[side]
                                ],
                                dtype="<i8",
                            ).tobytes()
                        ).hexdigest(),
                        "anchor_array_positions_sha256": hashlib.sha256(
                            np.asarray(
                                self._support_patch_indices[side], dtype="<i8"
                            ).tobytes()
                        ).hexdigest(),
                    }
                    for side in ("left", "right")
                },
            },
            "boundary_residuals_m": _thaw(self._boundary_residuals_m),
            "mapping_tolerance_m": _FRAME_MAPPING_TOLERANCE_M,
            "floor_target_gap_m": _TARGET_GAP_M,
            "correction_envelope_body_heights": _MAX_CORRECTION_BODY_HEIGHTS,
            "body_height_use": "correction envelope normalization only",
            "mass_coupling": False,
            "force_or_torque_claim": False,
            "classification": (
                "shared kinematic geometric contact foundation; full serialized, visual, "
                "body-support, dynamics, and Unity validation remain separate"
            ),
        }


__all__ = [
    "CanonicalConstantSkinTargetLaw",
    "ConstantSkinTargetUnavailable",
    "ConstantSkinTargetValue",
]


_DEFAULT_OBSERVE = CanonicalConstantSkinTargetLaw._observe.__func__
