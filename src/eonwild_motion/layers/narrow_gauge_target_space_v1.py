"""Generic target-space planning for the V9 narrow-gauge walk layer.

The planner only turns measured contact-centroid facts into target points.  It
does not know a species, a mesh, or a preferred joint.  A downstream solver is
responsible for proving that the targets are reachable without translation or
foot sliding.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any, Mapping, Sequence

from ..errors import ContractError


Vec3 = tuple[float, float, float]


def _number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be a finite number")
    return result


def _vec3(value: Any, *, label: str) -> Vec3:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ContractError(f"{label} must contain exactly three numbers")
    return tuple(_number(item, label=f"{label}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]


def _sub(left: Vec3, right: Vec3) -> Vec3:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _dot(left: Vec3, right: Vec3) -> float:
    return sum(a * b for a, b in zip(left, right))


def _scale(value: Vec3, factor: float) -> Vec3:
    return tuple(item * factor for item in value)  # type: ignore[return-value]


def _add(left: Vec3, right: Vec3) -> Vec3:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


@dataclass(frozen=True)
class TargetSample:
    """A measured body-frame contact target and its lateral correction."""

    time_s: float
    hip_center_m: Vec3
    contact_point_m: Vec3
    foot_root_m: Vec3
    target_lateral_m: float
    correction_lateral_m: float
    # The toe centroid is optional for the small synthetic planner API.  The
    # GLB path supplies it from the measured foot mask.
    toe_centroid_m: Vec3 | None = None
    # ``anchor_point_m`` is the explicitly selected active rigid-foot witness
    # for the downstream solver.  A cyclic walk may choose the distal toe for
    # every phase so an active-contact/toe fallback switch cannot manufacture
    # a velocity spike at touchdown or toe-off.  Synthetic callers may omit it
    # and use ``contact_point_m`` as the anchor.
    anchor_point_m: Vec3 | None = None
    # These fields preserve the clip-specific dense contact facts used by the
    # retarget layer.  ``contact_point_m`` is the active contact centroid for
    # PLANTED and the explicit toe fallback for SWING; no state is inferred
    # from species or from a foot-root residual.
    sole_centroid_m: Vec3 | None = None
    contact_state: str = "SWING"
    correction_phase: str = "UNLOCKED"
    stance_lane_offset_m: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "time_s": self.time_s,
            "hip_center_m": list(self.hip_center_m),
            "contact_point_m": list(self.contact_point_m),
            "foot_root_m": list(self.foot_root_m),
            "target_lateral_m": self.target_lateral_m,
            "correction_lateral_m": self.correction_lateral_m,
            "toe_centroid_m": None if self.toe_centroid_m is None else list(self.toe_centroid_m),
            "anchor_point_m": None if self.anchor_point_m is None else list(self.anchor_point_m),
            "sole_centroid_m": None if self.sole_centroid_m is None else list(self.sole_centroid_m),
            "contact_state": self.contact_state,
            "correction_phase": self.correction_phase,
            "stance_lane_offset_m": self.stance_lane_offset_m,
        }


def _quintic_smoothstep(value: float) -> float:
    amount = max(0.0, min(1.0, float(value)))
    return amount * amount * amount * (10.0 + amount * (-15.0 + 6.0 * amount))


def _phase_locked_corrections(
    samples: Sequence[TargetSample],
    *,
    label: str,
) -> tuple[tuple[float, ...], tuple[str, ...], tuple[float | None, ...]]:
    """Lock each cyclic stance offset and blend only across swing."""

    count = len(samples)
    if count < 2:
        return (
            tuple(sample.correction_lateral_m for sample in samples),
            tuple("UNLOCKED" for _ in samples),
            tuple(None for _ in samples),
        )
    duplicated_terminal = samples[0].contact_state == samples[-1].contact_state
    cycle_count = count - 1 if duplicated_terminal else count
    states = tuple(samples[index].contact_state for index in range(cycle_count))
    if set(states) != {"PLANTED", "SWING"}:
        return (
            tuple(sample.correction_lateral_m for sample in samples),
            tuple("UNLOCKED" for _ in samples),
            tuple(None for _ in samples),
        )
    transitions = [index for index in range(cycle_count) if states[index] != states[index - 1]]
    if len(transitions) < 2 or len(transitions) % 2:
        raise ContractError(f"{label}: cyclic contact mask does not alternate complete PLANTED/SWING runs")
    start = transitions[0]
    runs: list[tuple[str, tuple[int, ...]]] = []
    cursor = start
    while True:
        state = states[cursor]
        indices: list[int] = []
        while states[cursor] == state:
            indices.append(cursor)
            cursor = (cursor + 1) % cycle_count
            if cursor == start:
                break
        runs.append((state, tuple(indices)))
        if cursor == start:
            break
    if any(runs[index][0] == runs[index - 1][0] for index in range(len(runs))):
        raise ContractError(f"{label}: cyclic contact runs do not alternate")

    corrections = [float(sample.correction_lateral_m) for sample in samples]
    phases = ["UNLOCKED"] * count
    stance_offsets: list[float | None] = [None] * count
    planted_offsets: dict[int, float] = {}
    for run_index, (state, indices) in enumerate(runs):
        if state != "PLANTED":
            continue
        touchdown = indices[0]
        offset = float(samples[touchdown].correction_lateral_m)
        planted_offsets[run_index] = offset
        for index in indices:
            corrections[index] = offset
            phases[index] = "STANCE_LOCK"
            stance_offsets[index] = offset

    for run_index, (state, indices) in enumerate(runs):
        if state != "SWING":
            continue
        previous_offset = planted_offsets[(run_index - 1) % len(runs)]
        next_offset = planted_offsets[(run_index + 1) % len(runs)]
        denominator = len(indices) + 1
        for ordinal, index in enumerate(indices, start=1):
            amount = _quintic_smoothstep(ordinal / denominator)
            corrections[index] = previous_offset + amount * (next_offset - previous_offset)
            phases[index] = "SWING_QUINTIC_TRANSFER"
            stance_offsets[index] = next_offset

    if duplicated_terminal:
        corrections[-1] = corrections[0]
        phases[-1] = phases[0]
        stance_offsets[-1] = stance_offsets[0]
    return tuple(corrections), tuple(phases), tuple(stance_offsets)


def _sample_point(sample: Mapping[str, Any], *, label: str) -> Vec3:
    value = sample.get("contact_point_m")
    if value is None:
        value = sample.get("fallback_point_m")
    if value is None:
        raise ContractError(f"{label} requires a contact point or explicit fallback point")
    return _vec3(value, label=f"{label}.contact_point_m")


def plan_contact_targets(
    samples: Sequence[Mapping[str, Any]],
    *,
    lateral_axis: Sequence[float],
    hip_height_m: float,
    side_sign: float,
    label: str,
    target_lane_center_separation_over_hip_height: float | None = None,
    target_support_width_over_hip_height: float | None = None,
) -> tuple[TargetSample, ...]:
    """Plan a side's target contact-centroid line from measured facts.

    The midpoint is the measured hip centre. The target value is the lateral
    separation between the two planner lane centres, not simultaneous
    stance-support width and not successive step width. ``side_sign`` is profile data
    stabilized by the anatomical hip axis; foot positions never determine the
    sign.  The target is expressed in metres, and every frame retains the
    measured longitudinal/vertical position for a later rotation-only solve.
    """

    axis = _vec3(lateral_axis, label=f"{label}.lateral_axis")
    axis_norm = math.sqrt(_dot(axis, axis))
    if axis_norm <= 1.0e-12:
        raise ContractError(f"{label}.lateral_axis is zero")
    axis = _scale(axis, 1.0 / axis_norm)
    height = _number(hip_height_m, label=f"{label}.hip_height_m")
    if (
        target_lane_center_separation_over_hip_height is not None
        and target_support_width_over_hip_height is not None
    ):
        raise ContractError(
            f"{label} cannot provide both lane-centre and legacy support-width planner fields"
        )
    if target_lane_center_separation_over_hip_height is None:
        if target_support_width_over_hip_height is None:
            raise ContractError(
                f"{label}.target_lane_center_separation_over_hip_height is required"
            )
        # Explicit V1-only adapter.  The legacy name represented this exact
        # lane-centre planner input; it was never an observed simultaneous
        # support-width measurement. V2 profiles are strictly rejected before
        # they can reach this adapter.
        target_lane_center_separation_over_hip_height = (
            target_support_width_over_hip_height
        )
    lane_center_separation_ratio = _number(
        target_lane_center_separation_over_hip_height,
        label=f"{label}.target_lane_center_separation_over_hip_height",
    )
    sign = _number(side_sign, label=f"{label}.side_sign")
    if height <= 0.0 or lane_center_separation_ratio < 0.0 or sign == 0.0:
        raise ContractError(f"{label} target parameters are outside their finite domain")
    if not samples:
        raise ContractError(f"{label} has no measured samples")
    target_lateral = sign * lane_center_separation_ratio * height * 0.5
    output: list[TargetSample] = []
    previous_time = -math.inf
    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping):
            raise ContractError(f"{label} sample {index} must be an object")
        time_s = _number(sample.get("time_s"), label=f"{label}[{index}].time_s")
        if time_s <= previous_time:
            raise ContractError(f"{label} sample times must be strictly increasing")
        previous_time = time_s
        hip_center = _vec3(sample.get("hip_center_m"), label=f"{label}[{index}].hip_center_m")
        contact_point = _sample_point(sample, label=f"{label}[{index}]")
        foot_root = _vec3(sample.get("foot_root_m"), label=f"{label}[{index}].foot_root_m")
        toe_value = sample.get("toe_centroid_m")
        toe_centroid = (
            None
            if toe_value is None
            else _vec3(toe_value, label=f"{label}[{index}].toe_centroid_m")
        )
        sole_value = sample.get("sole_centroid_m")
        sole_centroid = (
            None
            if sole_value is None
            else _vec3(sole_value, label=f"{label}[{index}].sole_centroid_m")
        )
        anchor_value = sample.get("anchor_point_m")
        anchor_point = (
            None
            if anchor_value is None
            else _vec3(anchor_value, label=f"{label}[{index}].anchor_point_m")
        )
        contact_state = sample.get("contact_state", "SWING")
        if contact_state not in {"PLANTED", "SWING", "PRECONTACT", "ROCKER", "RELEASE"}:
            raise ContractError(f"{label}[{index}].contact_state is not a supported phase")
        correction_reference_value = sample.get("correction_reference_m")
        correction_reference = (
            contact_point
            if correction_reference_value is None
            else _vec3(
                correction_reference_value,
                label=f"{label}[{index}].correction_reference_m",
            )
        )
        measured_lateral = _dot(_sub(correction_reference, hip_center), axis)
        correction = target_lateral - measured_lateral
        output.append(
            TargetSample(
                time_s=time_s,
                hip_center_m=hip_center,
                contact_point_m=contact_point,
                foot_root_m=foot_root,
                target_lateral_m=target_lateral,
                correction_lateral_m=correction,
                toe_centroid_m=toe_centroid,
                anchor_point_m=anchor_point,
                sole_centroid_m=sole_centroid,
                contact_state=str(contact_state),
            )
        )
    planned = tuple(output)
    corrections, phases, stance_offsets = _phase_locked_corrections(planned, label=label)
    return tuple(
        replace(
            sample,
            correction_lateral_m=correction,
            correction_phase=phase,
            stance_lane_offset_m=stance_offset,
        )
        for sample, correction, phase, stance_offset in zip(
            planned,
            corrections,
            phases,
            stance_offsets,
        )
    )


def interpolate_correction(samples: Sequence[TargetSample], time_s: float) -> float:
    """Linearly interpolate a measured target correction at an animation key."""

    if not samples:
        raise ContractError("cannot interpolate an empty target plan")
    time_value = _number(time_s, label="target interpolation time_s")
    if time_value <= samples[0].time_s:
        return samples[0].correction_lateral_m
    if time_value >= samples[-1].time_s:
        return samples[-1].correction_lateral_m
    for left, right in zip(samples, samples[1:]):
        if left.time_s <= time_value <= right.time_s:
            span = right.time_s - left.time_s
            fraction = (time_value - left.time_s) / span
            return left.correction_lateral_m + fraction * (
                right.correction_lateral_m - left.correction_lateral_m
            )
    raise ContractError("target interpolation failed to locate its time interval")


def target_lateral_from_correction(
    contact_point: Sequence[float],
    hip_center: Sequence[float],
    lateral_axis: Sequence[float],
    correction_lateral_m: float,
) -> Vec3:
    """Return a point translated only in the measured lateral direction."""

    point = _vec3(contact_point, label="contact_point")
    _vec3(hip_center, label="hip_center")
    axis = _vec3(lateral_axis, label="lateral_axis")
    axis = _scale(axis, 1.0 / math.sqrt(_dot(axis, axis)))
    _number(correction_lateral_m, label="correction_lateral_m")
    return _add(point, _scale(axis, correction_lateral_m))
