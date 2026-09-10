"""Pure morphology-aware resolution for opt-in grounded locomotion intent."""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any, Mapping, Sequence

from ..contracts.v9_models import canonical_hash
from ..errors import ContractError
from .grounded_gait import GroundedGait, touchdown_reach
from .parameters import gait_parameters


POLICY_SCHEMA = "eonwild.motion.locomotion-response-policy.v1"
RESOLUTION_SCHEMA = "eonwild.motion.grounded-intent-resolution.v1"
SUPPORT_SCHEMA = "eonwild.motion.neutral-support-geometry.v1"
_SIDES = ("left", "right")


def _object(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ContractError(f"{label} must contain exactly {sorted(keys)}")
    return value


def _number(value: Any, label: str, *, minimum: float | None = None,
            maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be finite numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be finite numeric")
    if minimum is not None and result < minimum:
        raise ContractError(f"{label} is below its supported minimum")
    if maximum is not None and result > maximum:
        raise ContractError(f"{label} exceeds its supported maximum")
    return result


def _sha256(value: Any, label: str) -> str:
    if (not isinstance(value, str) or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)):
        raise ContractError(f"{label} must be a lowercase SHA-256")
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_plain(item) for item in value]
    return value


def _axis(value: Any, expected: tuple[float, float, float], label: str) -> None:
    if (not isinstance(value, Sequence) or isinstance(value, (str, bytes))
            or len(value) != 3
            or any(isinstance(item, bool) or not isinstance(item, (int, float))
                   or not math.isfinite(item) for item in value)
            or tuple(float(item) for item in value) != expected):
        raise ContractError(f"{label} differs from the admitted canonical frame")


@dataclass(frozen=True)
class ResolvedGroundedIntent:
    gait: GroundedGait
    canonical_parameters: tuple[tuple[str, Any], ...]
    requested_step_length_m: float
    resolved_step_length_m: float
    limiting_side: str | None
    side_evidence: tuple[tuple[str, float, float, float], ...]
    policy_sha256: str
    animal_support_sha256: str
    source_geometry_sha256: str
    placement_mode: str = "centered_stance_duty_factor"

    def receipt(self) -> dict[str, Any]:
        """Return a detached JSON-compatible resolution record."""
        receipt = {
            "schema": "eonwild.motion.resolved-grounded-intent.v1",
            "source_geometry_sha256": self.source_geometry_sha256,
            "policy_sha256": self.policy_sha256,
            "animal_support_sha256": self.animal_support_sha256,
            "requested_step_length_m": self.requested_step_length_m,
            "resolved_step_length_m": self.resolved_step_length_m,
            "limiting_side": self.limiting_side,
            "limiting_event": "canonical_touchdown" if self.limiting_side else None,
            "resolved_gait_parameters": dict(self.canonical_parameters),
            "sides": {
                side: ({
                    "requested_reach_margin_m": requested_margin,
                    "resolved_reach_margin_m": resolved_margin,
                    "maximum_step_length_m": maximum_step,
                } if self.placement_mode == "centered_stance_duty_factor" else {
                    "requested_reach_margin_m": requested_margin,
                    "resolved_reach_margin_m": resolved_margin,
                    "fixed_touchdown_reach_m": maximum_step,
                })
                for side, requested_margin, resolved_margin, maximum_step
                in self.side_evidence
            },
            "classification": (
                "source-bound authored kinematic intent resolution; "
                "not anatomical, force, collision, or motion acceptance"
            ),
            "requires_resolved_source_query_verification": True,
        }
        if self.placement_mode != "centered_stance_duty_factor":
            receipt["placement_mode"] = self.placement_mode
        return receipt


def measure_grounded_touchdown_geometry(
    gait: GroundedGait,
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    """Convert exact source-query touchdown observations to a zero-step basis."""
    if type(gait) is not GroundedGait:
        raise ContractError("touchdown measurement requires exact GroundedGait")
    observed = _object(observations, {
        "source_geometry_sha256", "body_height_m", "gait_parameters_sha256", "sides",
    }, "grounded touchdown observations")
    source_hash = _sha256(observed["source_geometry_sha256"], "touchdown source geometry")
    body_height = _number(observed["body_height_m"], "touchdown body height", minimum=1e-9)
    gait_hash = _sha256(observed["gait_parameters_sha256"], "touchdown gait parameters")
    if gait_hash != canonical_hash(gait_parameters(gait)):
        raise ContractError("touchdown observations are stale for the grounded gait")
    sides = _object(observed["sides"], set(_SIDES), "grounded touchdown observation sides")
    output: dict[str, Any] = {}
    for side in _SIDES:
        row = _object(sides[side], {
            "source_geometry_sha256", "body_height_m", "gait_parameters_sha256",
            "side", "event", "time_s", "coordinate", "hip_world_m",
            "target_ankle_world_m",
        }, f"{side} touchdown observation")
        if (row["source_geometry_sha256"] != source_hash
                or row["gait_parameters_sha256"] != gait_hash
                or row["side"] != side or row["event"] != "canonical_touchdown"
                or not math.isclose(_number(row["body_height_m"], f"{side} body height"),
                                    body_height, rel_tol=0.0, abs_tol=1e-12)):
            raise ContractError(f"{side} touchdown observation binding differs")
        _number(row["time_s"], f"{side} touchdown time", minimum=0.0)
        expected_time = 0.0 if side == "left" else gait.step_period_s
        if not math.isclose(float(row["time_s"]), expected_time,
                            rel_tol=0.0, abs_tol=1e-10):
            raise ContractError(f"{side} observation is not at its canonical touchdown time")
        coordinate = _object(row["coordinate"], {
            "lateral", "up", "forward",
        }, f"{side} touchdown coordinate")
        _axis(coordinate["lateral"], (1.0, 0.0, 0.0), f"{side} lateral axis")
        _axis(coordinate["up"], (0.0, 1.0, 0.0), f"{side} up axis")
        _axis(coordinate["forward"], (0.0, 0.0, 1.0), f"{side} forward axis")
        vectors = []
        for label in ("hip_world_m", "target_ankle_world_m"):
            value = row[label]
            if (not isinstance(value, Sequence) or isinstance(value, (str, bytes))
                    or len(value) != 3):
                raise ContractError(f"{side} {label} must have three components")
            vectors.append(tuple(
                _number(item, f"{side} {label}[{index}]")
                for index, item in enumerate(value)
            ))
        hip, ankle = vectors
        relative = [ankle[index] - hip[index] for index in range(3)]
        relative[2] -= touchdown_reach(gait, body_height)
        output[side] = {
            "event": "canonical_touchdown",
            "zero_step_ankle_from_hip_m": relative,
        }
    return {
        "source_geometry_sha256": source_hash,
        "body_height_m": body_height,
        "gait_parameters_sha256": gait_hash,
        "sides": output,
    }


def resolve_grounded_intent(
    gait: GroundedGait,
    *,
    body_height_m: float,
    animal_hindlimb_length_m: float,
    source_geometry_sha256: str,
    neutral_support_geometry: Mapping[str, Any],
    family_policy: Mapping[str, Any],
    touchdown_geometry: Mapping[str, Any],
) -> ResolvedGroundedIntent:
    """Resolve one grounded gait against declared touchdown geometry.

    ``touchdown_geometry`` supplies the source-query displacement from hip to
    target ankle when its authored touchdown placement is zero. Its lateral/up/forward
    components must be expressed in the admitted animal frame. The operation
    is deterministic and has no access to previous frames or solver state.
    """
    if type(gait) is not GroundedGait:
        raise ContractError("morphology-aware grounded intent requires exact GroundedGait")
    body_height = _number(body_height_m, "body height", minimum=1e-9)
    hindlimb = _number(animal_hindlimb_length_m, "animal hindlimb length", minimum=1e-9)
    source_hash = _sha256(source_geometry_sha256, "source geometry")
    policy_document = _object(family_policy, {
        "schema", "id", "version", "grounded_intent_resolution",
    }, "locomotion response policy")
    if (policy_document["schema"] != POLICY_SCHEMA
            or not isinstance(policy_document["id"], str) or not policy_document["id"]
            or type(policy_document["version"]) is not int
            or policy_document["version"] < 1):
        raise ContractError("unsupported locomotion response policy")
    policy = _object(policy_document["grounded_intent_resolution"], {
        "schema", "source_reference", "input_step_length_body_heights",
        "step_length_hindlimb_ratio", "touchdown_mapping",
        "reference_preservation_tolerance_m", "classification",
    }, "grounded family policy")
    if (policy["schema"] != RESOLUTION_SCHEMA
            or policy["touchdown_mapping"] != "centered_stance_duty_factor"
            or not isinstance(policy["classification"], str) or not policy["classification"]):
        raise ContractError("unsupported grounded family intent policy")
    reference = _object(policy["source_reference"], {
        "source_geometry_sha256", "hindlimb_length_m", "body_height_m",
        "step_length_m", "evidence",
    }, "grounded family source reference")
    _sha256(reference["source_geometry_sha256"], "family reference source geometry")
    for key in ("hindlimb_length_m", "body_height_m", "step_length_m"):
        _number(reference[key], f"family reference {key}", minimum=1e-9)
    if not isinstance(reference["evidence"], str) or not reference["evidence"]:
        raise ContractError("grounded family source reference needs evidence")
    input_step = _number(
        policy["input_step_length_body_heights"], "family input step", minimum=1e-9,
    )
    ratio = _number(
        policy["step_length_hindlimb_ratio"], "family hindlimb-relative step",
        minimum=1e-9, maximum=1.0,
    )
    tolerance = _number(
        policy["reference_preservation_tolerance_m"],
        "family reference preservation tolerance", minimum=0.0, maximum=1e-4,
    )
    derived_ratio = float(reference["step_length_m"]) / float(reference["hindlimb_length_m"])
    if not math.isclose(ratio, derived_ratio, rel_tol=0.0, abs_tol=1e-12):
        raise ContractError("family hindlimb-relative step differs from its reference")
    if not math.isclose(
        float(reference["step_length_m"]) / float(reference["body_height_m"]),
        input_step, rel_tol=0.0, abs_tol=1e-12,
    ):
        raise ContractError("family body-height step differs from its reference")
    intent_step = abs(gait.step_length_body_heights)
    if intent_step > input_step + 1e-12:
        raise ContractError("grounded gait step exceeds the bound family input")
    direction = math.copysign(1.0, gait.step_length_body_heights)

    support = _object(neutral_support_geometry, {
        "schema", "id", "version", "source_geometry_sha256", "hindlimb_length_m",
        "coordinate", "sides", "limitations",
    }, "animal neutral support geometry")
    if (support["schema"] != SUPPORT_SCHEMA
            or not isinstance(support["id"], str) or not support["id"]
            or type(support["version"]) is not int or support["version"] < 1
            or _sha256(
        support["source_geometry_sha256"], "animal support source geometry"
    ) != source_hash):
        raise ContractError("animal neutral support geometry is not source-bound")
    if not math.isclose(
        _number(support["hindlimb_length_m"], "support hindlimb length", minimum=1e-9),
        hindlimb, rel_tol=0.0, abs_tol=1e-12,
    ):
        raise ContractError("animal support and instance hindlimb lengths differ")
    coordinate = _object(support["coordinate"], {
        "frame", "lateral", "up", "forward",
    }, "animal support coordinate")
    if coordinate["frame"] != "source_world":
        raise ContractError("animal support geometry requires the declared canonical frame")
    _axis(coordinate["lateral"], (1.0, 0.0, 0.0), "support lateral axis")
    _axis(coordinate["up"], (0.0, 1.0, 0.0), "support up axis")
    _axis(coordinate["forward"], (0.0, 0.0, 1.0), "support forward axis")
    if (not isinstance(support["limitations"], Sequence)
            or isinstance(support["limitations"], (str, bytes))
            or not support["limitations"]
            or any(not isinstance(item, str) or not item for item in support["limitations"])):
        raise ContractError("animal support geometry limitations must be explicit")
    support_sides = _object(support["sides"], set(_SIDES), "animal support sides")
    query = _object(touchdown_geometry, {
        "source_geometry_sha256", "body_height_m", "gait_parameters_sha256", "sides",
    }, "touchdown geometry")
    if _sha256(query["source_geometry_sha256"], "touchdown source geometry") != source_hash:
        raise ContractError("touchdown geometry is not bound to the admitted source")
    if not math.isclose(
        _number(query["body_height_m"], "touchdown body height", minimum=1e-9),
        body_height, rel_tol=0.0, abs_tol=1e-12,
    ):
        raise ContractError("touchdown and runtime body heights differ")
    if _sha256(query["gait_parameters_sha256"], "touchdown gait parameters") != canonical_hash(
        gait_parameters(gait)
    ):
        raise ContractError("touchdown geometry is stale for the grounded gait")
    query_sides = _object(query["sides"], set(_SIDES), "touchdown geometry sides")

    requested_step_magnitude = ratio * hindlimb * (intent_step / input_step)
    requested_step = direction * requested_step_magnitude
    resolved_step_magnitude = requested_step_magnitude
    rows: list[tuple[str, float, float, float]] = []
    parsed: list[tuple[str, float, float, float, float]] = []
    preferred_maximum_steps: dict[str, float] = {}
    for side in _SIDES:
        geometry = _object(support_sides[side], {
            "upper_length_m", "lower_length_m", "preferred_support_knee_degrees",
            "posture_evidence",
        }, f"{side} neutral support geometry")
        upper = _number(geometry["upper_length_m"], f"{side} upper length", minimum=1e-9)
        lower = _number(geometry["lower_length_m"], f"{side} lower length", minimum=1e-9)
        knee = _number(
            geometry["preferred_support_knee_degrees"], f"{side} preferred support knee",
            minimum=1.0, maximum=179.0,
        )
        if upper + lower >= hindlimb or not isinstance(
            geometry["posture_evidence"], str
        ) or not geometry["posture_evidence"]:
            raise ContractError(f"{side} neutral support geometry is inconsistent")
        query_side = _object(query_sides[side], {
            "zero_step_ankle_from_hip_m", "event",
        }, f"{side} touchdown geometry")
        if query_side["event"] != "canonical_touchdown":
            raise ContractError("touchdown geometry must describe canonical touchdown")
        vector = query_side["zero_step_ankle_from_hip_m"]
        if (not isinstance(vector, Sequence) or isinstance(vector, (str, bytes))
                or len(vector) != 3):
            raise ContractError(f"{side} touchdown vector must have three components")
        lateral, up, forward_zero = (
            _number(value, f"{side} touchdown vector[{index}]")
            for index, value in enumerate(vector)
        )
        preferred_reach = math.sqrt(
            upper * upper + lower * lower
            - 2.0 * upper * lower * math.cos(math.radians(knee))
        )
        remaining = preferred_reach * preferred_reach - lateral * lateral - up * up
        if remaining <= 0:
            raise ContractError(f"{side} neutral support posture cannot reach the touchdown plane")
        maximum_forward = math.sqrt(remaining)
        directional_zero = direction * forward_zero
        if gait.centered_stance:
            maximum_step = (maximum_forward - directional_zero) / gait.duty_factor
            if maximum_step <= 0:
                raise ContractError(f"{side} neutral support posture has no directed step envelope")
            preferred_maximum_steps[side] = maximum_step
        else:
            maximum_step = touchdown_reach(gait, body_height)
            fixed_distance = math.sqrt(
                lateral * lateral + up * up + (forward_zero + maximum_step) ** 2
            )
            if fixed_distance > preferred_reach + tolerance:
                raise ContractError(
                    f"{side} fixed touchdown placement exceeds the neutral support reach"
                )
        parsed.append((side, preferred_reach, lateral, up, forward_zero))

    limited = (
        gait.centered_stance
        and any(
            requested_step_magnitude > maximum_step + tolerance
            for maximum_step in preferred_maximum_steps.values()
        )
    )
    if not limited:
        resolved_step_magnitude = requested_step_magnitude
    # The preferred neutral-support knee is diagnostic posture evidence, not
    # authority to silently rewrite the behavior's authored stride. Preserve
    # reachable intent and report a negative preference margin when exceeded.
    resolved_step_magnitude = requested_step_magnitude
    resolved_step = requested_step
    maximum_steps: dict[str, float] = {}
    for side, preferred_reach, lateral, up, forward_zero in parsed:
        maximum_forward = math.sqrt(
            preferred_reach * preferred_reach - lateral * lateral - up * up
        )
        maximum_step = ((maximum_forward - direction * forward_zero) / gait.duty_factor
                        if gait.centered_stance else touchdown_reach(gait, body_height))
        maximum_steps[side] = maximum_step
        requested_distance = math.sqrt(
            lateral * lateral + up * up
            + (forward_zero + (gait.duty_factor * requested_step
                               if gait.centered_stance else maximum_step)) ** 2
        )
        resolved_distance = math.sqrt(
            lateral * lateral + up * up
            + (forward_zero + (gait.duty_factor * resolved_step
                               if gait.centered_stance else maximum_step)) ** 2
        )
        rows.append((side, preferred_reach - requested_distance,
                     preferred_reach - resolved_distance, maximum_step))
    limiting_side = min(maximum_steps, key=maximum_steps.get) if limited else None
    resolved_bh = resolved_step / body_height
    original_step = gait.step_length_body_heights * body_height
    preserve_reference_gait = (
        resolved_step == requested_step
        and math.isclose(resolved_step, original_step, rel_tol=0.0, abs_tol=tolerance)
    )
    resolved_gait = gait if preserve_reference_gait else replace(
        gait, step_length_body_heights=resolved_bh,
    )
    parameters = tuple(gait_parameters(resolved_gait).items())
    return ResolvedGroundedIntent(
        gait=resolved_gait,
        canonical_parameters=parameters,
        requested_step_length_m=requested_step,
        resolved_step_length_m=resolved_step,
        limiting_side=limiting_side,
        side_evidence=tuple(rows),
        policy_sha256=canonical_hash(_plain(policy_document)),
        animal_support_sha256=canonical_hash(_plain(support)),
        source_geometry_sha256=source_hash,
        placement_mode=("centered_stance_duty_factor" if gait.centered_stance
                        else "fixed_touchdown_reach_signed_stride"),
    )
