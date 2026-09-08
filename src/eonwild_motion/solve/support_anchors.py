"""Bound canonical material anchors for source-owned locomotion events.

This provider changes only which already-defined material reference a skin
refinement uses.  It never searches an emitted grid, interpolates a correction,
or changes a gait/contact law.  Omitted callers retain the historical
first-loaded-row reference exactly.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..factory.source_identity import validate_frozen_source_with_uniform_scale
from ..glb.container import Glb
from ..planning.airborne_gait import AirborneGait, build_airborne_plan, sample_airborne_gait
from ..planning.gait_transition import GaitTransition, build_transition_plan
from ..planning.grounded_gait import GroundedGait, build_grounded_plan, sample_grounded_gait
from ..planning.parameters import gait_parameters
from .airborne_gait import (
    build_airborne_solve_context,
    driven_body_response,
    solve_airborne_plan_sample,
)
from .performance import _performance_from_parameters, decorate_plan
from .skin_rig import SkinRig


@dataclass(frozen=True)
class CanonicalSupportAnchor:
    """One exact sustained-family touchdown material reference."""

    side: str
    gait_family_sha256: str
    touchdown_phase_s: float
    contact_side_convention: str
    lowest_patch_index: int
    material_origin_m: np.ndarray
    material_vertex_indices: tuple[int, ...]


class CanonicalSupportAnchorProvider:
    """Evaluate stable support anchors from the bound source gait law.

    The provider is intentionally constructed with the compiler's already-bound
    gait objects.  It does not attempt to infer a locomotion family from plan
    rows, and transition rows never replace the sustained source event.
    """

    def __init__(self, anchors: Mapping[str, CanonicalSupportAnchor]) -> None:
        if set(anchors) != {"left", "right"}:
            raise ContractError("canonical support anchors require both semantic feet")
        self._anchors = MappingProxyType(dict(anchors))

    @classmethod
    def build(
        cls,
        source: Glb,
        *,
        semantic_roles: Mapping[str, Any],
        solver_gait: AirborneGait,
        locomotion_gait: GroundedGait | AirborneGait,
        transition: GaitTransition | None,
        plan: Mapping[str, Any],
        contact_profile: Mapping[str, Any],
        up_axis: tuple[float, float, float],
        forward_axis: tuple[float, float, float],
        articulation_profile: Any = None,
    ) -> "CanonicalSupportAnchorProvider":
        if not isinstance(source, Glb):
            raise ContractError("canonical support anchors require an admitted source")
        if not isinstance(solver_gait, AirborneGait) or not isinstance(
            locomotion_gait, (GroundedGait, AirborneGait)
        ):
            raise ContractError("canonical support anchors require bound solver and locomotion gaits")
        if transition is not None and not isinstance(transition, GaitTransition):
            raise ContractError("canonical support anchors require a validated transition")
        if not isinstance(plan, Mapping) or not isinstance(contact_profile, Mapping):
            raise ContractError("canonical support anchors require bound plan and contact data")
        try:
            source_hash = contact_profile["source"]["sha256"]
        except (KeyError, TypeError) as exc:
            raise ContractError("canonical support anchors require contact source provenance") from exc
        validate_frozen_source_with_uniform_scale(source, source_hash)
        cls._validate_active_program(plan, locomotion_gait, transition)
        body_height = cls._body_height(plan)
        sustained = cls._sustained_plan(locomotion_gait, body_height, plan)
        context = build_airborne_solve_context(
            source,
            source_clip=None,
            semantic_roles=semantic_roles,
            gait=solver_gait,
            up_axis=up_axis,
            plan=sustained,
            forward_axis=forward_axis,
            legacy_overlay=False,
            articulation_profile=articulation_profile,
        )
        if not math.isclose(context.body_height, body_height, rel_tol=0, abs_tol=1e-10):
            raise ContractError("canonical support anchor plan height differs from source geometry")
        skin = SkinRig(source, semantic_roles, context.forward, context.up, contact_profile)
        response = driven_body_response(solver_gait, sustained, semantic_roles)
        family_sha256 = cls._family_sha256(locomotion_gait)
        anchors: dict[str, CanonicalSupportAnchor] = {}
        for side, phase in (("left", 0.0), ("right", locomotion_gait.step_period_s)):
            row = cls._exact_sustained_row(locomotion_gait, sustained, phase, body_height)
            body = cls._body_at(response, sustained, phase)
            pose = solve_airborne_plan_sample(context, row, body_response_sample=body)
            worlds = skin.world(pose.translations, pose.rotations, context.base_s)
            patch, vertex_ids = cls._material_patch(skin, worlds, side)
            lowest = int(np.argmin(patch[:, cls._up_index(contact_profile)]))
            origin = np.asarray(patch - context.forward * row["feet"][side]["forward_m"], dtype=float)
            origin.setflags(write=False)
            anchors[side] = CanonicalSupportAnchor(
                side=side,
                gait_family_sha256=family_sha256,
                touchdown_phase_s=float(phase),
                contact_side_convention="right_continuous_touchdown",
                lowest_patch_index=lowest,
                material_origin_m=origin,
                material_vertex_indices=vertex_ids,
            )
        return cls(anchors)

    @staticmethod
    def _family_sha256(gait: GroundedGait | AirborneGait) -> str:
        """Hash support-law controls, excluding sampling and clip-domain clocks.

        ``sample_hz``, ``cycles``, and handoff sampling only decide retained
        output rows or transition interfaces. They do not define either
        sustained-foot touchdown law, so they must not split one anchor family.
        Active-program validation above still binds those values where they are
        relevant to the requested compile.
        """
        values = dict(gait_parameters(gait))
        for key in (
            "sample_hz",
            "cycles",
            "handoff_phase_fraction",
            "handoff_sample_hz",
            "boundary_sample_hz",
        ):
            values.pop(key, None)
        return hashlib.sha256(
            json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _body_height(plan: Mapping[str, Any]) -> float:
        value = plan.get("body_height_m")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ContractError("canonical support anchors require positive finite plan height")
        return float(value)

    @staticmethod
    def _same(actual: Any, expected: Any, label: str) -> None:
        if isinstance(expected, Mapping):
            if not isinstance(actual, Mapping) or set(actual) != set(expected):
                raise ContractError(f"canonical support anchor {label} differs from bound program")
            for key in expected:
                CanonicalSupportAnchorProvider._same(actual[key], expected[key], f"{label}.{key}")
            return
        if isinstance(expected, (list, tuple)):
            if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
                raise ContractError(f"canonical support anchor {label} differs from bound program")
            for index, value in enumerate(expected):
                CanonicalSupportAnchorProvider._same(actual[index], value, f"{label}[{index}]")
            return
        if isinstance(expected, bool):
            equal = type(actual) is bool and actual is expected
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            equal = (not isinstance(actual, bool) and isinstance(actual, (int, float))
                     and math.isfinite(float(actual))
                     and math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-10))
        else:
            equal = actual == expected
        if not equal:
            raise ContractError(f"canonical support anchor {label} differs from bound program")

    @classmethod
    def _validate_active_program(
        cls,
        plan: Mapping[str, Any],
        gait: GroundedGait | AirborneGait,
        transition: GaitTransition | None,
    ) -> None:
        expected_program = "grounded_gait" if isinstance(gait, GroundedGait) else "airborne_gait"
        if transition is None:
            if plan.get("program") != expected_program:
                raise ContractError("canonical support anchors require the bound locomotion program")
            cls._same(plan.get("parameters"), gait_parameters(gait), "locomotion parameters")
            return
        if (plan.get("program") != "gait_transition"
                or plan.get("locomotion_program") != expected_program):
            raise ContractError("canonical support anchors require the bound transition program")
        expected = build_transition_plan(transition, gait, cls._body_height(plan))
        for key in ("parameters", "transition_parameters", "transition_contract", "same_foot_cycle_s", "duration_s"):
            cls._same(plan.get(key), expected.get(key), key)

    @staticmethod
    def _sustained_plan(
        gait: GroundedGait | AirborneGait,
        body_height: float,
        active_plan: Mapping[str, Any],
    ) -> dict[str, Any]:
        result = (build_grounded_plan(gait, body_height)
                  if isinstance(gait, GroundedGait)
                  else build_airborne_plan(gait, body_height))
        result["program"] = "grounded_gait" if isinstance(gait, GroundedGait) else "airborne_gait"
        if "performance" in active_plan:
            performance = _performance_from_parameters(active_plan["performance"])
            result = decorate_plan(result, performance)
        if "gaze_calibration" in active_plan:
            result["gaze_calibration"] = deepcopy(active_plan["gaze_calibration"])
        return result

    @staticmethod
    def _exact_sustained_row(
        gait: GroundedGait | AirborneGait,
        sustained: Mapping[str, Any],
        phase: float,
        body_height: float,
    ) -> dict[str, Any]:
        row = (sample_grounded_gait(gait, phase, body_height)
               if isinstance(gait, GroundedGait)
               else sample_airborne_gait(gait, phase, body_height))
        # Performance decoration is the only existing row decoration that
        # carries into the constrained limb solve.  Reuse its established
        # declaration instead of deriving a new contact detail here.
        if "performance" in sustained:
            from ..planning.foot_articulation import declare_pad_recovery_sample
            declare_pad_recovery_sample(sustained["parameters"], row)
        return row

    @staticmethod
    def _body_at(response: Mapping[str, Any] | None, plan: Mapping[str, Any], time_s: float) -> Mapping[str, Any] | None:
        if response is None:
            return None
        for index, row in enumerate(plan["samples"]):
            if math.isclose(float(row["time_s"]), time_s, rel_tol=0, abs_tol=1e-12):
                return response["samples"][index]
        raise ContractError("canonical support anchor event is missing from sustained source clock")

    @staticmethod
    def _up_index(contact_profile: Mapping[str, Any]) -> int:
        try:
            value = contact_profile["geometry"]["ground"]["up_axis"]
        except (KeyError, TypeError) as exc:
            raise ContractError("canonical support anchors require a fixed contact floor") from exc
        if value not in {"X", "Y", "Z"}:
            raise ContractError("canonical support anchors require a cardinal contact floor")
        return {"X": 0, "Y": 1, "Z": 2}[value]

    @staticmethod
    def _material_patch(skin: SkinRig, worlds: np.ndarray, side: str) -> tuple[np.ndarray, tuple[int, ...]]:
        try:
            regions = skin.foot_regions[side]
        except (AttributeError, KeyError) as exc:
            raise ContractError("canonical support anchors require stable sole and toe masks") from exc
        ids = tuple(int(index) for region in ("sole", "toe") for index in regions[region])
        patch = np.vstack([skin.skin(worlds, regions[region]) for region in ("sole", "toe")])
        if patch.ndim != 2 or patch.shape[1] != 3 or len(patch) != len(ids) or not np.isfinite(patch).all():
            raise ContractError("canonical support anchor material patch is invalid")
        return patch, ids

    def anchor_for(self, side: str) -> CanonicalSupportAnchor:
        if side not in ("left", "right"):
            raise ContractError("canonical support anchor side must be left or right")
        return self._anchors[side]

    def receipt(self) -> dict[str, Any]:
        """Bound event and patch identity, never a contact-quality verdict."""
        return {
            "classification": (
                "exact sustained source-law touchdown material reference; "
                "not an emitted-contact, dynamics, or visual acceptance claim"
            ),
            "sides": {
                side: {
                    "touchdown_phase_s": anchor.touchdown_phase_s,
                    "gait_family_sha256": anchor.gait_family_sha256,
                    "contact_side_convention": anchor.contact_side_convention,
                    "lowest_patch_index": anchor.lowest_patch_index,
                    "material_vertex_count": len(anchor.material_vertex_indices),
                    "material_vertex_indices_sha256": hashlib.sha256(
                        np.asarray(anchor.material_vertex_indices, dtype="<i8").tobytes()
                    ).hexdigest(),
                }
                for side, anchor in self._anchors.items()
            },
        }
