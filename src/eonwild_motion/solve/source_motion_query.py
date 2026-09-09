"""Non-emitting source-pose diagnostics for existing locomotion programs.

The query operates on source geometry, authored plans, and existing solver laws.
It never reads a completed animation, invents a skin-correction interpolation,
or authorizes an emitted CUBICSPLINE channel.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from ..contracts.v9_models import canonical_hash
from ..errors import ContractError
from ..factory.source_identity import validate_frozen_source_with_uniform_scale
from ..glb.container import Glb
from ..planning.airborne_gait import (
    AirborneGait,
    build_airborne_plan,
    sample_airborne_gait,
    sampled_handoff_phase,
)
from ..planning.foot_articulation import declare_pad_recovery_sample
from ..planning.gait_transition import (
    GaitTransition,
    _Choreography,
    build_transition_plan,
)
from ..planning.grounded_gait import GroundedGait, sample_grounded_gait
from ..planning.parameters import gait_parameters
from .airborne_gait import (
    AirborneSolveContext,
    SolvedAirbornePose,
    _freeze_data,
    _qinv,
    _qmul,
    _world_matrices,
    build_airborne_solve_context,
    driven_body_response,
    grounded_touchdown_target,
    periodic_response,
    sample_periodic_response,
    solve_airborne_plan_sample,
)
from .performance import phase_and_gain
from .skin_rig import SkinRig
from .grounded_transition_clearance import GroundedTransitionClearanceResolver
from .grounded_transition_clearance import GroundedTransitionClearanceUnavailable
from .grounded_transition_clearance import _monotone_floor
from .authored_material_contact import (
    AuthoredMaterialContactAdapter,
    TARGET_MATERIAL_GAP_M,
    TARGET_RESIDUAL_LIMIT_M,
)


CONTINUOUS_SKIN_TARGET_UNAVAILABLE = "CONTINUOUS_SKIN_TARGET_UNAVAILABLE"
BRANCH_OR_CONVERGENCE_UNAVAILABLE = "BRANCH_OR_CONVERGENCE_UNAVAILABLE"
RAW_NUMERICAL_PROBE_ONLY = "RAW_NUMERICAL_PROBE_ONLY"
TRANSITION_CLEARANCE_UNAVAILABLE = "TRANSITION_CLEARANCE_UNAVAILABLE"
AUTHORED_MATERIAL_CLEARANCE_UNAVAILABLE = (
    "AUTHORED_MATERIAL_CLEARANCE_UNAVAILABLE"
)
_AUTHORED_REACH_HEIGHT_TOLERANCE_M = 1e-6
_AUTHORED_REACH_MAX_ITERATIONS = 24
_AUTHORED_JOINT_MAX_BRACKET_STEPS = 24


def _bounded_authored_reach_height(
    measure: Any, ceiling: float, side: str
) -> float:
    """Find a reach-feasible height without asserting monotone residual magnitude.

    The leg solver caps near its reach boundary, so the residual can vary by a
    few nanometres between two already-feasible heights. Only the unchanged
    residual predicate owns admission here; the caller separately solves and
    rechecks the material floor at the combined final height.
    """
    lo, hi = 0.0, float(ceiling)
    margin_lo, _ = measure(lo)
    if margin_lo >= 0.0:
        return 0.0
    margin_hi, _ = measure(hi)
    if margin_hi < 0.0:
        raise GroundedTransitionClearanceUnavailable(
            f"{side} authored target reach has no feasible bracket"
        )
    for _ in range(_AUTHORED_REACH_MAX_ITERATIONS):
        if hi - lo <= _AUTHORED_REACH_HEIGHT_TOLERANCE_M:
            return hi
        mid = 0.5 * (lo + hi)
        margin_mid, _ = measure(mid)
        if margin_mid >= 0.0:
            hi = mid
        else:
            lo = mid
    raise GroundedTransitionClearanceUnavailable(
        f"{side} authored target reach did not converge"
    )


def _bounded_authored_joint_height(
    measure: Any,
    seed_height: float,
    ceiling: float,
    side: str,
    *,
    target_gap_m: float,
) -> float:
    """Resolve one observed safe material/reach bracket after a clamp switch.

    This is an authored-material engineering resolution for the local upward
    height component starting at the declared source height. It does not claim
    that the black-box solver is globally monotone or that the returned bracket
    is the global first or minimum feasible interval. Final package gates remain
    authoritative for continuous-time acceptance.
    """

    def admitted(sample: tuple[float, int, float, float, float]) -> bool:
        gap, _, residual, extension, articulation = sample
        return (
            gap >= target_gap_m
            and residual <= TARGET_RESIDUAL_LIMIT_M
            and extension <= TARGET_RESIDUAL_LIMIT_M
            and articulation <= 0.01
        )

    lo = max(0.0, float(seed_height))
    hi_limit = float(ceiling)
    if lo > hi_limit:
        raise GroundedTransitionClearanceUnavailable(
            f"{side} authored material joint feasibility seed exceeds its ceiling"
        )
    lo_sample = measure(lo)
    if admitted(lo_sample):
        return lo
    step = max(
        _AUTHORED_REACH_HEIGHT_TOLERANCE_M,
        target_gap_m - float(lo_sample[0]),
    )
    hi = lo
    hi_sample = lo_sample
    for _ in range(_AUTHORED_JOINT_MAX_BRACKET_STEPS):
        candidate = min(hi_limit, hi + step)
        if candidate <= hi:
            break
        hi = candidate
        hi_sample = measure(hi)
        if admitted(hi_sample):
            break
        lo = hi
        lo_sample = hi_sample
        step *= 2.0
    else:
        raise GroundedTransitionClearanceUnavailable(
            f"{side} authored material joint feasibility did not find a safe bracket"
        )
    if not admitted(hi_sample):
        raise GroundedTransitionClearanceUnavailable(
            f"{side} authored material joint feasibility has no safe bracket"
        )
    for _ in range(_AUTHORED_REACH_MAX_ITERATIONS):
        if hi - lo <= _AUTHORED_REACH_HEIGHT_TOLERANCE_M:
            break
        mid = 0.5 * (lo + hi)
        mid_sample = measure(mid)
        if admitted(mid_sample):
            hi, hi_sample = mid, mid_sample
        else:
            lo, lo_sample = mid, mid_sample
    final_sample = measure(hi)
    if not admitted(final_sample):
        raise GroundedTransitionClearanceUnavailable(
            f"{side} authored material joint feasibility final combined gates disagree"
        )
    return hi


def _readonly(value: np.ndarray) -> np.ndarray:
    copy = np.array(value, dtype=float, copy=True)
    copy.setflags(write=False)
    return copy


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, np.ndarray):
        return np.array(value, copy=True)
    return value


def _clone_source(source: Glb) -> Glb:
    if not isinstance(source, Glb):
        raise ContractError("source motion query requires a GLB source")
    # ``raw`` is the frozen geometry identity used by optional source-bound
    # admissions (for example, the neutral jaw calibration). Re-encoding the
    # current document would silently replace that identity even when the only
    # current-state difference is the explicitly admitted uniform animal scale.
    # A complete deep copy instead retains raw provenance while detaching the
    # document, binary data, topology caches, and local-rest caches together.
    return deepcopy(source)


def _finite_time(time_s: Any) -> float:
    if isinstance(time_s, bool) or not isinstance(time_s, (int, float)):
        raise ContractError("source motion query time must be finite numeric")
    try:
        value = float(time_s)
    except OverflowError as exc:
        raise ContractError("source motion query time must be finite numeric") from exc
    if not math.isfinite(value):
        raise ContractError("source motion query time must be finite numeric")
    return value


def _quaternion_log_delta(center: np.ndarray, sample: np.ndarray) -> np.ndarray:
    """Shortest sign-aligned rotation vector from ``center`` to ``sample``."""
    a, b = np.asarray(center, dtype=float), np.asarray(sample, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 4:
        raise ContractError("source quaternion derivative requires Nx4 rotations")
    an = np.linalg.norm(a, axis=1)
    bn = np.linalg.norm(b, axis=1)
    if (
        (an <= 1e-12).any()
        or (bn <= 1e-12).any()
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
    ):
        raise ContractError("source quaternion derivative has an invalid rotation")
    a, b = a / an[:, None], b / bn[:, None]
    b[np.sum(a * b, axis=1) < 0] *= -1
    out = np.zeros((len(a), 3), dtype=float)
    for index, (left, right) in enumerate(zip(a, b)):
        delta = np.asarray(_qmul(_qinv(tuple(left)), tuple(right)), dtype=float)
        if delta[3] < 0:
            delta *= -1
        sin_half = float(np.linalg.norm(delta[:3]))
        if sin_half <= 1e-14:
            out[index] = 2 * delta[:3]
        else:
            out[index] = (
                delta[:3] / sin_half * (2 * math.atan2(sin_half, float(delta[3])))
            )
    return out


@dataclass(frozen=True)
class SourceMotionUnavailable:
    status: str
    time_s: float
    reason: str


@dataclass(frozen=True)
class SourceMotionResult:
    status: str
    time_s: float
    limit_side: str
    row: Mapping[str, Any]
    pose: SolvedAirbornePose
    worlds: np.ndarray
    material_points: Mapping[str, np.ndarray] | None
    branch_witness: Mapping[str, Any]


@dataclass(frozen=True)
class SourceMotionRawProbe:
    """Unqualified source finite differences; never derivative authority."""

    status: str
    time_s: float
    side: str
    step_sizes_s: tuple[float, float, float]
    local_translation_velocity_mps: np.ndarray
    local_angular_velocity_radps: np.ndarray
    world_node_velocity_mps: np.ndarray
    material_velocity_mps: Mapping[str, np.ndarray] | None
    per_unit_deltas: Mapping[str, tuple[float, float]]
    branch_witness: Mapping[str, Any]


class SourceMotionQuery:
    """Retained, non-emitting source-pose diagnostics for a bound program.

    The query accepts off-grid source evaluation only after every retained plan
    row is proved to be the same source law at the same measured height. Skin
    refinements remain exact-key-only. Solver branch authority is not exposed
    by the row solver, so ``derivative`` is deliberately unavailable; callers
    may request a separately labelled raw numerical probe.
    """

    def __init__(
        self,
        source: Glb,
        *,
        semantic_roles: Mapping[str, Any],
        solver_gait: AirborneGait,
        locomotion_gait: GroundedGait | AirborneGait,
        plan: Mapping[str, Any],
        up_axis: tuple[float, float, float] = (0, 1, 0),
        forward_axis: tuple[float, float, float] | None = None,
        transition: GaitTransition | None = None,
        source_clip: str | None = None,
        legacy_overlay: bool = False,
        articulation_profile: Any = None,
        contact_profile: Mapping[str, Any] | None = None,
        transition_clearance: GroundedTransitionClearanceResolver | None = None,
        authored_material_contact: AuthoredMaterialContactAdapter | None = None,
    ) -> None:
        if not isinstance(solver_gait, AirborneGait):
            raise ContractError(
                "source motion query requires an AirborneGait solver contract"
            )
        if not isinstance(locomotion_gait, (GroundedGait, AirborneGait)):
            raise ContractError(
                "source motion query requires a grounded or airborne locomotion gait"
            )
        if not math.isclose(
            solver_gait.step_period_s,
            locomotion_gait.step_period_s,
            rel_tol=0,
            abs_tol=1e-12,
        ):
            raise ContractError(
                "source motion query solver cadence differs from bound locomotion program"
            )
        if transition is not None and not isinstance(transition, GaitTransition):
            raise ContractError("source motion query transition must be validated")
        if type(legacy_overlay) is not bool:
            raise ContractError("source motion query legacy_overlay must be boolean")
        if transition_clearance is not None and (
            type(transition_clearance) is not GroundedTransitionClearanceResolver
            or transition is None
            or not isinstance(locomotion_gait, GroundedGait)
        ):
            raise ContractError(
                "source motion query transition clearance requires its owned grounded transition resolver"
            )
        if transition_clearance is not None:
            transition_clearance.validate_for_query(
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
                source_clip=source_clip,
                legacy_overlay=legacy_overlay,
            )
        if (
            authored_material_contact is not None
            and type(authored_material_contact) is not AuthoredMaterialContactAdapter
        ):
            raise ContractError(
                "source motion query authored material contact must be its owned adapter"
            )
        self._validate_plan_input(plan)
        if contact_profile is not None:
            self._validate_contact_profile(contact_profile, source)
        self._source = _clone_source(source)
        self._plan = _freeze_data(plan)
        self._roles = _freeze_data(semantic_roles)
        self._solver_gait = solver_gait
        self._locomotion_gait = locomotion_gait
        self._transition = transition
        self._up_axis = tuple(up_axis)
        self._forward_axis = None if forward_axis is None else tuple(forward_axis)
        self._source_clip = source_clip
        self._legacy_overlay = legacy_overlay
        self._transition_clearance = transition_clearance
        self._authored_material_contact = authored_material_contact
        # Retain the complete owned request, rather than only the derived
        # SkinRig. Downstream source-owned diagnostics can therefore prove
        # that this actual query is the request they admitted.
        self._contact_profile = (
            None if contact_profile is None else _freeze_data(contact_profile)
        )
        self._context: AirborneSolveContext = build_airborne_solve_context(
            self._source,
            source_clip=source_clip,
            semantic_roles=self._roles,
            gait=solver_gait,
            up_axis=self._up_axis,
            plan=self._plan,
            forward_axis=self._forward_axis,
            legacy_overlay=self._legacy_overlay,
            articulation_profile=articulation_profile,
        )
        self._times = tuple(
            _finite_time(row["time_s"]) for row in self._plan["samples"]
        )
        self._choreography = (
            _Choreography(transition, locomotion_gait, self._context.body_height)
            if transition is not None
            else None
        )
        self._validate_source_binding()
        self._refined = any(
            "target_offset_m" in foot
            for row in self._plan["samples"]
            for foot in row["feet"].values()
        )
        if self._authored_material_contact is not None:
            if self._refined:
                raise ContractError(
                    "authored material contact requires an unrefined source plan"
                )
            self._authored_material_contact.validate_for_query(self)
        self._body_response = driven_body_response(solver_gait, self._plan, self._roles)
        self._skin = None
        if contact_profile is not None:
            self._skin = SkinRig(
                self._source,
                self._roles,
                self._context.forward,
                self._context.up,
                _thaw(self._contact_profile),
            )
        self._boundaries = self._canonical_boundaries()

    @staticmethod
    def _validate_plan_input(plan: Mapping[str, Any]) -> None:
        if (
            not isinstance(plan, Mapping)
            or not isinstance(plan.get("samples"), list)
            or len(plan["samples"]) < 2
        ):
            raise ContractError(
                "source motion query requires a finite plan with at least two samples"
            )
        previous = -math.inf
        for index, row in enumerate(plan["samples"]):
            if not isinstance(row, Mapping):
                raise ContractError(
                    f"source motion query plan sample {index} must be a mapping"
                )
            time = _finite_time(row.get("time_s"))
            if time <= previous:
                raise ContractError(
                    "source motion query plan times must be finite and strictly increasing"
                )
            previous = time
            feet = row.get("feet")
            if not isinstance(feet, Mapping) or set(feet) != {"left", "right"}:
                raise ContractError(
                    "source motion query plan sample requires left and right feet"
                )
            for side, foot in feet.items():
                if (
                    not isinstance(foot, Mapping)
                    or type(foot.get("contact")) is not bool
                ):
                    raise ContractError(
                        f"source motion query {side} foot must be a complete typed mapping"
                    )

    @property
    def context(self) -> AirborneSolveContext:
        return self._context

    @property
    def refined(self) -> bool:
        return self._refined

    def _exact_index(self, time_s: float) -> int | None:
        for index, value in enumerate(self._times):
            if time_s == value:
                return index
        return None

    def _validate_domain(self, time_s: float) -> None:
        if time_s < self._times[0] or time_s > self._times[-1]:
            raise ContractError(
                "source motion query time is outside the retained plan domain"
            )

    @staticmethod
    def _program_for(gait: GroundedGait | AirborneGait) -> str:
        return "grounded_gait" if isinstance(gait, GroundedGait) else "airborne_gait"

    @staticmethod
    def _require_same(actual: Any, expected: Any, label: str) -> None:
        if isinstance(expected, Mapping):
            if not isinstance(actual, Mapping) or set(actual) != set(expected):
                raise ContractError(
                    f"source motion query {label} differs from the bound source program"
                )
            for key in expected:
                SourceMotionQuery._require_same(
                    actual[key], expected[key], f"{label}.{key}"
                )
            return
        if isinstance(expected, (list, tuple)):
            if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
                raise ContractError(
                    f"source motion query {label} differs from the bound source program"
                )
            for index, value in enumerate(expected):
                SourceMotionQuery._require_same(
                    actual[index], value, f"{label}[{index}]"
                )
            return
        if isinstance(expected, bool):
            equal = type(actual) is bool and actual is expected
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            equal = (
                not isinstance(actual, bool)
                and isinstance(actual, (int, float))
                and math.isfinite(float(actual))
                and math.isclose(
                    float(actual), float(expected), rel_tol=0, abs_tol=1e-10
                )
            )
        else:
            equal = actual == expected
        if not equal:
            raise ContractError(
                f"source motion query {label} differs from the bound source program"
            )

    @staticmethod
    def _without_refinements(row: Mapping[str, Any]) -> dict[str, Any]:
        result = _thaw(row)
        for foot in result["feet"].values():
            foot.pop("target_offset_m", None)
        return result

    def _sample_row(
        self,
        time_s: float,
        *,
        apply_clearance: bool = True,
        transition_clearance_integrity_proved: bool = False,
    ) -> dict[str, Any]:
        if self._choreography is not None:
            row = self._choreography.sample(time_s)
        elif isinstance(self._locomotion_gait, GroundedGait):
            row = sample_grounded_gait(
                self._locomotion_gait, time_s, self._context.body_height
            )
        else:
            row = sample_airborne_gait(
                self._locomotion_gait, time_s, self._context.body_height
            )
        row = deepcopy(row)
        if "performance" in self._plan:
            declare_pad_recovery_sample(_thaw(self._plan["parameters"]), row)
        if apply_clearance and self._transition_clearance is not None:
            row = (
                self._transition_clearance._resolve_owned(row)
                if transition_clearance_integrity_proved
                else self._transition_clearance.resolve(row)
            )
        return row

    def _validate_source_binding(self) -> None:
        plan = self._plan
        expected_program = self._program_for(self._locomotion_gait)
        expected_schema = (
            "eonwild.motion.v9.contact-plan.v1"
            if isinstance(self._locomotion_gait, GroundedGait)
            else "eonwild.motion.v9.airborne-gait-plan.v1"
        )
        transition_program = plan.get("program") == "gait_transition"
        if plan.get("schema") != (
            "eonwild.motion.v9.contact-plan.v1"
            if transition_program
            else expected_schema
        ):
            raise ContractError(
                "source motion query requires the declared source-plan schema"
            )
        if transition_program != (self._transition is not None):
            raise ContractError(
                "source motion query transition presence differs from the retained program"
            )
        if transition_program:
            if (
                plan.get("locomotion_program") != expected_program
                or plan.get("loop") is not False
                or not isinstance(plan.get("transition_parameters"), Mapping)
                or self._transition is None
            ):
                raise ContractError(
                    "source motion query transition program differs from bound contracts"
                )
            self._require_same(
                plan["transition_parameters"],
                gait_parameters(self._transition),
                "transition parameters",
            )
            contract = plan.get("transition_contract")
            expected_contract = build_transition_plan(
                self._transition, self._locomotion_gait, self._context.body_height
            )["transition_contract"]
            self._require_same(contract, expected_contract, "transition contract")
        elif plan.get("program") != expected_program:
            raise ContractError(
                "source motion query program differs from bound locomotion gait"
            )
        if not isinstance(plan.get("parameters"), Mapping):
            raise ContractError("source motion query plan parameters must be a mapping")
        self._require_same(
            plan["parameters"],
            gait_parameters(self._locomotion_gait),
            "locomotion parameters",
        )
        height = plan.get("body_height_m")
        if (
            isinstance(height, bool)
            or not isinstance(height, (int, float))
            or not math.isfinite(height)
            or not math.isclose(
                float(height), self._context.body_height, rel_tol=0, abs_tol=1e-10
            )
        ):
            raise ContractError(
                "source motion query plan height differs from source geometry"
            )
        period = 2 * self._locomotion_gait.step_period_s
        duration = (
            self._choreography.duration
            if self._choreography is not None
            else period * self._locomotion_gait.cycles
        )
        for key, expected in (("same_foot_cycle_s", period), ("duration_s", duration)):
            value = plan.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not math.isclose(float(value), expected, rel_tol=0, abs_tol=1e-10)
            ):
                raise ContractError(
                    f"source motion query {key} differs from bound source clock"
                )
        if not math.isclose(
            self._times[0], 0.0, rel_tol=0, abs_tol=1e-12
        ) or not math.isclose(self._times[-1], duration, rel_tol=0, abs_tol=1e-10):
            raise ContractError(
                "source motion query retained plan extent differs from source clock"
            )
        for index, row in enumerate(plan["samples"]):
            expected = self._sample_row(float(row["time_s"]), apply_clearance=False)
            self._require_same(
                self._without_refinements(row), expected, f"sample[{index}]"
            )

    @staticmethod
    def _validate_contact_profile(
        contact_profile: Mapping[str, Any], source: Glb
    ) -> None:
        """Bind material witnesses to frozen geometry and admitted current state."""
        if not isinstance(contact_profile, Mapping):
            raise ContractError("source motion query contact profile must be a mapping")
        try:
            source_ref = contact_profile["source"]
            declared = source_ref["sha256"]
        except (KeyError, TypeError) as exc:
            raise ContractError(
                "source motion query contact profile requires source provenance"
            ) from exc
        if not isinstance(declared, str):
            raise ContractError("source motion query contact source hash must be text")
        # The shared admission proves both source.raw provenance and the
        # mutable snapshot. Its sole allowance is the compiler-owned uniform
        # scene-root animal scale; no position, accessor, rest-TRS, or cached
        # mapping mutation can reach SkinRig.
        validate_frozen_source_with_uniform_scale(source, declared)

    def _canonical_boundaries(self) -> tuple[float, ...]:
        start, end = self._times[0], self._times[-1]
        boundaries = {start, end}
        if self._choreography is not None:
            c = self._choreography
            boundaries.update((c.delay, c.delay + c.ramp))
            for index in range(-2, 2 * c.transition.ramp_cycles + 5):
                touchdown = index * c.step - c.clock_offset
                boundaries.update((c.delay + touchdown, c.delay + c.liftoff(touchdown)))
        else:
            step, period = (
                self._locomotion_gait.step_period_s,
                2 * self._locomotion_gait.step_period_s,
            )
            stance = (
                self._locomotion_gait.duty_factor * period
                if isinstance(self._locomotion_gait, GroundedGait)
                else step * (1 - self._locomotion_gait.flight_fraction)
            )
            for offset in (0.0, step):
                first = math.floor((start - offset) / period) - 1
                last = math.ceil((end - offset) / period) + 1
                for index in range(first, last + 1):
                    touchdown = offset + index * period
                    boundaries.update((touchdown, touchdown + stance))
            phase = sampled_handoff_phase(self._locomotion_gait)
            if phase is not None:
                for index in range(self._locomotion_gait.cycles):
                    boundaries.add(phase + index * period)
        return tuple(sorted(value for value in boundaries if start <= value <= end))

    def _continuous_body_response(
        self, row: Mapping[str, Any]
    ) -> Mapping[str, Any] | None:
        if self._body_response is None:
            return None
        phase, gain = phase_and_gain(row)
        if self._plan.get("program") == "gait_transition":
            reference = build_airborne_plan(
                self._solver_gait, self._context.body_height
            )
            clock = np.asarray(
                [item["time_s"] for item in reference["samples"]], dtype=float
            )
            scale = (
                2
                * (
                    self._solver_gait.pelvis_compression_body_heights
                    + self._solver_gait.flight_height_body_heights
                )
                * self._context.body_height
                / self._solver_gait.step_period_s
            )
            drive = np.clip(
                [
                    item["pelvis_vertical_velocity_mps"] / scale
                    for item in reference["samples"]
                ],
                -1,
                1,
            )
        else:
            clock = np.asarray(self._times, dtype=float)
            scale = (
                2
                * (
                    self._solver_gait.pelvis_compression_body_heights
                    + self._solver_gait.flight_height_body_heights
                )
                * self._context.body_height
                / self._solver_gait.step_period_s
            )
            drive = np.clip(
                [
                    item["pelvis_vertical_velocity_mps"] / scale
                    for item in self._plan["samples"]
                ],
                -1,
                1,
            )
        query = np.asarray([phase], dtype=float)

        def response(values: np.ndarray, tau: float) -> float:
            return float(sample_periodic_response(clock, values, tau, query)[0])

        chest_reference = (
            -self._solver_gait.chest_response_gain_degrees
            * periodic_response(clock, drive, self._solver_gait.body_response_time_s)
        )
        chest = -self._solver_gait.chest_response_gain_degrees * response(
            drive, self._solver_gait.body_response_time_s
        )
        counter_reference = -self._solver_gait.head_stabilization_gain * chest_reference
        counter = -self._solver_gait.head_stabilization_gain * chest
        neck = (
            0.65
            * response(counter_reference, self._solver_gait.body_response_time_s * 1.5)
            if self._roles.get("neck")
            else 0.0
        )
        angles: dict[str, float] = {}
        if self._solver_gait.chest_response_gain_degrees:
            angles[self._roles["chest"]] = chest
            angles[self._roles["head"]] = counter - neck
        if self._roles.get("neck"):
            for name in self._roles["neck"]:
                angles[name] = neck / len(self._roles["neck"])
        names = list(self._roles.get("tail", []))
        weights = np.asarray(
            [(index + 1) ** 0.6 for index in range(len(names))], dtype=float
        )
        if len(weights):
            weights /= weights.sum()
        for index, name in enumerate(names):
            tau = self._solver_gait.body_response_time_s * (
                1 + 0.6 * index / max(1, len(names) - 1)
            )
            angles[name] = (
                -self._solver_gait.tail_response_gain_degrees
                * weights[index]
                * response(drive, tau)
            )
        return MappingProxyType(
            {
                "time_s": float(row["time_s"]),
                "support_count": int(row["support_count"]),
                "normalized_vertical_motion_drive": float(
                    gain * np.interp(phase, clock, drive)
                ),
                "sagittal_node_degrees": MappingProxyType(
                    {name: float(gain * value) for name, value in angles.items()}
                ),
            }
        )

    def _body_sample(
        self, index: int | None, row: Mapping[str, Any]
    ) -> Mapping[str, Any] | None:
        if self._body_response is None:
            return None
        return (
            self._body_response["samples"][index]
            if index is not None
            else self._continuous_body_response(row)
        )

    def _branch_witness(
        self, row: Mapping[str, Any], pose: SolvedAirbornePose
    ) -> Mapping[str, Any]:
        feet = {}
        for side in ("left", "right"):
            fact = pose.feet[side]
            feet[side] = MappingProxyType(
                {
                    "contact": bool(row["feet"][side]["contact"]),
                    "swing_phase": float(row["feet"][side]["swing_phase"]),
                    "solved_foot_pitch_degrees": float(
                        fact["solved_foot_pitch_degrees"]
                    ),
                    "foot_target_residual_m": float(fact["foot_target_residual_m"]),
                    "articulation_envelope_violation_degrees": float(
                        fact["articulation_envelope_violation_degrees"]
                    ),
                    "optimizer_tie_margin": "UNAVAILABLE_FROM_EXISTING_ROW_SOLVER",
                    "active_toe_reach_correction": "UNAVAILABLE_FROM_EXISTING_ROW_SOLVER",
                }
            )
        return MappingProxyType(
            {
                "classification": "existing row-solver witnesses; no optimizer branch or slack authority is exposed",
                "feet": MappingProxyType(feet),
                "maximum_unreachable_extension_m": float(
                    pose.maximum_unreachable_extension_m
                ),
                "maximum_articulation_envelope_violation_degrees": float(
                    pose.maximum_articulation_envelope_violation_degrees
                ),
            }
        )

    def _is_boundary(self, time_s: float) -> bool:
        return any(
            math.isclose(time_s, boundary, rel_tol=0, abs_tol=1e-12)
            for boundary in self._boundaries
        )

    def _limit_time(self, time: float, side: str) -> float:
        if side == "value":
            return time
        direction = -1 if side == "left_limit" else 1
        if direction < 0 and time <= self._times[0]:
            raise ContractError("source motion query has no left limit at plan start")
        if direction > 0 and time >= self._times[-1]:
            raise ContractError("source motion query has no right limit at plan end")
        # An ULP alone may be lost by periodic phase arithmetic. This is a
        # declared source-time interior limit, not a retimed animation sample.
        scale = self._locomotion_gait.step_period_s
        epsilon = max(64 * math.ulp(time if time else 1.0), scale * 1e-9)
        candidate = time + direction * epsilon
        if not self._times[0] < candidate < self._times[-1]:
            candidate = math.nextafter(time, -math.inf if direction < 0 else math.inf)
        if candidate == time:
            raise ContractError(
                "source motion query cannot represent the requested one-sided limit"
            )
        return candidate

    def evaluate(
        self, time_s: Any, *, side: str = "value"
    ) -> SourceMotionResult | SourceMotionUnavailable:
        time = _finite_time(time_s)
        return self._evaluate_owned(time, side=side, target_offsets=None)

    def grounded_touchdown_observation(
        self, time_s: Any, side: str
    ) -> Mapping[str, Any]:
        """Expose the exact pre-refinement ankle target for one grounded touchdown."""
        if (
            type(self._locomotion_gait) is not GroundedGait
            or self._transition is not None
        ):
            raise ContractError(
                "touchdown observation requires steady grounded locomotion"
            )
        if side not in ("left", "right"):
            raise ContractError("touchdown observation side must be left or right")
        time = _finite_time(time_s)
        self._validate_domain(time)
        index = self._exact_index(time)
        row = self._sample_row(time, apply_clearance=False)
        try:
            row_foot = row["feet"][side]
            touchdown = float(row_foot["touchdown_time_s"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError("touchdown observation is incomplete") from exc
        if row_foot.get("contact") is not True or not math.isclose(
            touchdown, time, rel_tol=0.0, abs_tol=1e-10
        ):
            raise ContractError("requested source time is not a canonical touchdown")
        target = grounded_touchdown_target(
            self._context,
            row,
            side=side,
            body_response_sample=self._body_sample(index, row),
        )
        return _freeze_data(
            {
                "source_geometry_sha256": hashlib.sha256(self._source.raw).hexdigest(),
                "body_height_m": float(self._context.body_height),
                "gait_parameters_sha256": canonical_hash(
                    gait_parameters(self._locomotion_gait)
                ),
                "side": side,
                "event": "canonical_touchdown",
                "time_s": time,
                "coordinate": {
                    "lateral": self._context.lateral.tolist(),
                    "up": self._context.up.tolist(),
                    "forward": self._context.forward.tolist(),
                },
                "hip_world_m": target["hip_world_m"],
                "target_ankle_world_m": target["target_ankle_world_m"],
            }
        )

    @staticmethod
    def _target_offsets(value: Mapping[str, Any]) -> dict[str, list[float]]:
        if not isinstance(value, Mapping) or set(value) != {"left", "right"}:
            raise ContractError(
                "source motion query target offsets require left and right vectors"
            )
        result = {}
        for side in ("left", "right"):
            raw_value = value[side]
            try:
                contains_boolean = any(
                    isinstance(item, (bool, np.bool_)) for item in raw_value
                )
            except TypeError:
                contains_boolean = False
            try:
                raw = np.asarray(raw_value)
            except (TypeError, ValueError) as exc:
                raise ContractError(
                    "source motion query target offsets must be finite real vectors"
                ) from exc
            if (
                contains_boolean
                or raw.dtype.kind not in "fiu"
                or raw.shape != (3,)
                or not np.isfinite(raw).all()
            ):
                raise ContractError(
                    "source motion query target offsets must be finite real vectors"
                )
            result[side] = np.asarray(raw, dtype=float).tolist()
        return result

    def evaluate_with_target_offsets(
        self,
        time_s: Any,
        target_offsets: Mapping[str, Any],
        *,
        side: str = "value",
    ) -> SourceMotionResult | SourceMotionUnavailable:
        """Apply owned per-foot offsets before the query's single pose solve."""
        time = _finite_time(time_s)
        offsets = self._target_offsets(target_offsets)
        return self._evaluate_owned(time, side=side, target_offsets=offsets)

    def _evaluate_owned(
        self,
        time: float,
        *,
        side: str,
        target_offsets: Mapping[str, list[float]] | None,
        transition_clearance_integrity_proved: bool = False,
        authored_material_integrity_proved: bool = False,
    ) -> SourceMotionResult | SourceMotionUnavailable:
        if side not in ("value", "left_limit", "right_limit"):
            raise ContractError(
                "source motion query side must be value, left_limit, or right_limit"
            )
        self._validate_domain(time)
        if (
            self._authored_material_contact is not None
            and not authored_material_integrity_proved
        ):
            self._authored_material_contact.validate_for_query(self)
        index = self._exact_index(time)
        if self._refined and (
            target_offsets is not None or index is None or side != "value"
        ):
            return SourceMotionUnavailable(
                CONTINUOUS_SKIN_TARGET_UNAVAILABLE,
                time,
                "current skin-target refinement defines corrections only at retained plan keys and cannot accept another offset operation",
            )
        sampled_time = self._limit_time(time, side)
        if side != "value":
            index = None
        try:
            row = (
                _thaw(self._plan["samples"][index])
                if index is not None
                else self._sample_row(
                    sampled_time,
                    transition_clearance_integrity_proved=(
                        transition_clearance_integrity_proved
                    ),
                )
            )
            if index is not None and self._transition_clearance is not None:
                row = (
                    self._transition_clearance._resolve_owned(row)
                    if transition_clearance_integrity_proved
                    else self._transition_clearance.resolve(row)
                )
            if self._authored_material_contact is not None:
                row = self._authored_material_contact._resolve_owned(
                    self, row, sampled_time
                )
                if "performance" in self._plan:
                    declare_pad_recovery_sample(_thaw(self._plan["parameters"]), row)
        except GroundedTransitionClearanceUnavailable as exc:
            return SourceMotionUnavailable(
                TRANSITION_CLEARANCE_UNAVAILABLE, sampled_time, str(exc)
            )
        if target_offsets is not None:
            for foot_side in ("left", "right"):
                row["feet"][foot_side]["target_offset_m"] = list(
                    target_offsets[foot_side]
                )
        body = self._body_sample(index, row)
        material = None

        def solve_owned() -> tuple[
            SolvedAirbornePose, np.ndarray, Mapping[str, np.ndarray] | None
        ]:
            pose = solve_airborne_plan_sample(
                self._context, row, body_response_sample=body
            )
            worlds = _readonly(
                _world_matrices(
                    self._source,
                    pose.translations,
                    pose.rotations,
                    self._context.base_s,
                )
            )
            points = None
            if self._skin is not None:
                points = MappingProxyType(
                    {
                        name: _readonly(self._skin.skin(worlds, ids))
                        for name, ids in self._skin.foot_masks.items()
                    }
                )
            return pose, worlds, points

        pose, worlds, material = solve_owned()
        if self._authored_material_contact is not None and material is not None:
            up_index = int(np.argmax(np.abs(self._context.up)))

            for foot_side in ("left", "right"):
                requested_gap = TARGET_MATERIAL_GAP_M + float(
                    row["feet"][foot_side]["authored_material_clearance_m"]
                )
                declared_height = float(row["feet"][foot_side]["height_m"])

                def measure(
                    height: float,
                ) -> tuple[float, int, float, float, float]:
                    row["feet"][foot_side]["height_m"] = float(height)
                    measured_pose, _, measured = solve_owned()
                    if measured is None:
                        raise GroundedTransitionClearanceUnavailable(
                            "authored material clearance needs target skin"
                        )
                    points = measured[foot_side]
                    index = int(np.argmin(points[:, up_index]))
                    material_gap = float(
                        points[index, up_index] - self._skin.ground
                    )
                    target_residual = float(
                        measured_pose.feet[foot_side]["foot_target_residual_m"]
                    )
                    return (
                        material_gap,
                        index,
                        target_residual,
                        float(measured_pose.maximum_unreachable_extension_m),
                        float(
                            measured_pose.maximum_articulation_envelope_violation_degrees
                        ),
                    )

                try:
                    try:
                        material_height = _monotone_floor(
                            lambda height: measure(height)[:2],
                            self._context.body_height,
                            foot_side,
                            target_gap_m=requested_gap,
                            purpose="authored material clearance",
                        )
                    except GroundedTransitionClearanceUnavailable as exc:
                        if str(exc) != (
                            f"{foot_side} authored material clearance "
                            "material gap is nonmonotone"
                        ):
                            raise
                        material_height = _bounded_authored_joint_height(
                            measure,
                            declared_height,
                            self._context.body_height,
                            foot_side,
                            target_gap_m=requested_gap,
                        )

                    def measure_reach(height: float) -> tuple[float, int]:
                        _, vertex_index, residual, _, _ = measure(height)
                        return TARGET_RESIDUAL_LIMIT_M - residual, vertex_index

                    _, _, material_height_residual, _, _ = measure(material_height)
                    reach_height = 0.0
                    if material_height_residual > TARGET_RESIDUAL_LIMIT_M:
                        reach_ceiling = min(
                            self._context.body_height,
                            max(0.01, 2 * material_height_residual),
                        )
                        reach_value, _ = measure_reach(reach_ceiling)
                        while (
                            reach_value < 0.0
                            and reach_ceiling < self._context.body_height
                        ):
                            reach_ceiling = min(
                                self._context.body_height, 2 * reach_ceiling
                            )
                            reach_value, _ = measure_reach(reach_ceiling)
                        reach_height = _bounded_authored_reach_height(
                            measure_reach,
                            reach_ceiling,
                            foot_side,
                        )
                    row["feet"][foot_side]["height_m"] = max(
                        material_height, reach_height
                    )
                except GroundedTransitionClearanceUnavailable as exc:
                    return SourceMotionUnavailable(
                        AUTHORED_MATERIAL_CLEARANCE_UNAVAILABLE,
                        sampled_time,
                        str(exc),
                    )
            pose, worlds, material = solve_owned()
            for foot_side in ("left", "right"):
                requested_clearance = float(
                    row["feet"][foot_side]["authored_material_clearance_m"]
                )
                achieved_gap = float(
                    material[foot_side][:, up_index].min() - self._skin.ground
                )
                target_residual = float(
                    pose.feet[foot_side]["foot_target_residual_m"]
                )
                if (
                    achieved_gap + 1e-10
                    < TARGET_MATERIAL_GAP_M + requested_clearance
                    or target_residual > TARGET_RESIDUAL_LIMIT_M + 1e-10
                    or pose.maximum_unreachable_extension_m
                    > TARGET_RESIDUAL_LIMIT_M + 1e-10
                    or pose.maximum_articulation_envelope_violation_degrees
                    > 0.01 + 1e-10
                ):
                    return SourceMotionUnavailable(
                        AUTHORED_MATERIAL_CLEARANCE_UNAVAILABLE,
                        sampled_time,
                        f"{foot_side} final authored material and reach gates disagree",
                    )
                row["feet"][foot_side][
                    "authored_material_achieved_clearance_m"
                ] = achieved_gap - TARGET_MATERIAL_GAP_M
                row["feet"][foot_side]["authored_material_adaptation_m"] = (
                    achieved_gap
                    - TARGET_MATERIAL_GAP_M
                    - requested_clearance
                )
        return SourceMotionResult(
            "AVAILABLE",
            sampled_time,
            side,
            _freeze_data(row),
            pose,
            worlds,
            material,
            self._branch_witness(row, pose),
        )

    def derivative(
        self, time_s: Any, *, side: str = "value", initial_h_s: float = 1e-3
    ) -> SourceMotionUnavailable:
        time = _finite_time(time_s)
        if side not in ("value", "left_limit", "right_limit"):
            raise ContractError(
                "source derivative side must be value, left_limit, or right_limit"
            )
        if (
            isinstance(initial_h_s, bool)
            or not isinstance(initial_h_s, (int, float))
            or not math.isfinite(initial_h_s)
            or initial_h_s <= 0
        ):
            raise ContractError("source derivative initial_h_s must be finite positive")
        self._validate_domain(time)
        if self._refined:
            return SourceMotionUnavailable(
                CONTINUOUS_SKIN_TARGET_UNAVAILABLE,
                time,
                "current skin-target refinement has no off-grid or derivative authority",
            )
        return SourceMotionUnavailable(
            BRANCH_OR_CONVERGENCE_UNAVAILABLE,
            time,
            "existing row solver exposes no optimizer branch, residual slack, or active-toe authority; use raw_probe only as non-authoritative evidence",
        )

    @staticmethod
    def _rate(
        center: SourceMotionResult,
        left: SourceMotionResult,
        right: SourceMotionResult | None,
        step: float,
        direction: int,
    ):
        if direction < 0:
            translation = (
                np.asarray(center.pose.translations)
                - np.asarray(left.pose.translations)
            ) / step
            angular = (
                _quaternion_log_delta(
                    np.asarray(left.pose.rotations), np.asarray(center.pose.rotations)
                )
                / step
            )
            world = (center.worlds[:, :3, 3] - left.worlds[:, :3, 3]) / step
            material = (
                None
                if center.material_points is None
                else MappingProxyType(
                    {
                        key: (center.material_points[key] - left.material_points[key])
                        / step
                        for key in center.material_points
                    }
                )
            )
        elif direction > 0:
            translation = (
                np.asarray(left.pose.translations)
                - np.asarray(center.pose.translations)
            ) / step
            angular = (
                _quaternion_log_delta(
                    np.asarray(center.pose.rotations), np.asarray(left.pose.rotations)
                )
                / step
            )
            world = (left.worlds[:, :3, 3] - center.worlds[:, :3, 3]) / step
            material = (
                None
                if center.material_points is None
                else MappingProxyType(
                    {
                        key: (left.material_points[key] - center.material_points[key])
                        / step
                        for key in center.material_points
                    }
                )
            )
        else:
            assert right is not None
            translation = (
                np.asarray(right.pose.translations) - np.asarray(left.pose.translations)
            ) / (2 * step)
            angular = _quaternion_log_delta(
                np.asarray(left.pose.rotations), np.asarray(right.pose.rotations)
            ) / (2 * step)
            world = (right.worlds[:, :3, 3] - left.worlds[:, :3, 3]) / (2 * step)
            material = (
                None
                if center.material_points is None
                else MappingProxyType(
                    {
                        key: (right.material_points[key] - left.material_points[key])
                        / (2 * step)
                        for key in center.material_points
                    }
                )
            )
        if not all(np.isfinite(value).all() for value in (translation, angular, world)):
            raise ContractError("source motion raw probe produced non-finite TRS rates")
        if material is not None and any(
            not np.isfinite(value).all() for value in material.values()
        ):
            raise ContractError(
                "source motion raw probe produced non-finite material rates"
            )
        return translation, angular, world, material

    def raw_probe(
        self, time_s: Any, *, side: str = "value", initial_h_s: float = 1e-3
    ) -> SourceMotionRawProbe | SourceMotionUnavailable:
        time = _finite_time(time_s)
        if side not in ("value", "left_limit", "right_limit"):
            raise ContractError(
                "source raw probe side must be value, left_limit, or right_limit"
            )
        if (
            isinstance(initial_h_s, bool)
            or not isinstance(initial_h_s, (int, float))
            or not math.isfinite(initial_h_s)
            or initial_h_s <= 0
        ):
            raise ContractError("source raw probe initial_h_s must be finite positive")
        self._validate_domain(time)
        if self._refined:
            return SourceMotionUnavailable(
                CONTINUOUS_SKIN_TARGET_UNAVAILABLE,
                time,
                "current skin-target refinement has no off-grid probe authority",
            )
        if self._is_boundary(time) and side == "value":
            return SourceMotionUnavailable(
                BRANCH_OR_CONVERGENCE_UNAVAILABLE,
                time,
                "canonical contact or handoff event requires an explicit raw-probe side",
            )
        direction = -1 if side == "left_limit" else 1 if side == "right_limit" else 0
        center = self.evaluate(time, side=side)
        if isinstance(center, SourceMotionUnavailable):
            return center
        anchor = center.time_s
        room = (
            anchor - self._times[0]
            if direction < 0
            else self._times[-1] - anchor
            if direction > 0
            else min(anchor - self._times[0], self._times[-1] - anchor)
        )
        if direction < 0:
            other = [
                anchor - boundary
                for boundary in self._boundaries
                if boundary < anchor - 1e-12
            ]
        elif direction > 0:
            other = [
                boundary - anchor
                for boundary in self._boundaries
                if boundary > anchor + 1e-12
            ]
        else:
            other = [
                abs(anchor - boundary)
                for boundary in self._boundaries
                if abs(anchor - boundary) > 1e-12
            ]
        if other:
            room = min(room, min(other))
        h = min(float(initial_h_s), room / 8)
        if h <= 1e-10:
            return SourceMotionUnavailable(
                BRANCH_OR_CONVERGENCE_UNAVAILABLE,
                time,
                "no finite source interval remains for raw probe",
            )
        rates = []
        for divisor in (1.0, 2.0, 4.0):
            step = h / divisor
            if direction < 0:
                left = self.evaluate(anchor - step)
                if isinstance(left, SourceMotionUnavailable):
                    return left
                rates.append(self._rate(center, left, None, step, direction))
            elif direction > 0:
                right = self.evaluate(anchor + step)
                if isinstance(right, SourceMotionUnavailable):
                    return right
                rates.append(self._rate(center, right, None, step, direction))
            else:
                left, right = self.evaluate(anchor - step), self.evaluate(anchor + step)
                if isinstance(left, SourceMotionUnavailable):
                    return left
                if isinstance(right, SourceMotionUnavailable):
                    return right
                rates.append(self._rate(center, left, right, step, direction))
        labels = ("local_translation_mps", "local_angular_radps", "world_node_mps")
        raw_deltas = {
            label: (
                float(np.max(np.abs(rates[0][idx] - rates[1][idx]))),
                float(np.max(np.abs(rates[1][idx] - rates[2][idx]))),
            )
            for idx, label in enumerate(labels)
        }
        if rates[0][3] is not None:
            raw_deltas["material_mps"] = (
                max(
                    float(np.max(np.abs(rates[0][3][key] - rates[1][3][key])))
                    for key in rates[0][3]
                ),
                max(
                    float(np.max(np.abs(rates[1][3][key] - rates[2][3][key])))
                    for key in rates[1][3]
                ),
            )
        deltas = MappingProxyType(raw_deltas)
        return SourceMotionRawProbe(
            RAW_NUMERICAL_PROBE_ONLY,
            time,
            side,
            (h, h / 2, h / 4),
            _readonly(rates[-1][0]),
            _readonly(rates[-1][1]),
            _readonly(rates[-1][2]),
            None
            if rates[-1][3] is None
            else MappingProxyType(
                {key: _readonly(value) for key, value in rates[-1][3].items()}
            ),
            deltas,
            center.branch_witness,
        )
