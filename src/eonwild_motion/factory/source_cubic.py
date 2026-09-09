"""Opt-in glTF CUBICSPLINE emission from checked source-time poses.

Tangents are numerical estimates of the bound source law.  They are serialized
in glTF units per second and are not derivative, branch, or global-C1 authority.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Callable, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..glb.animation import read_animation_tracks
from ..solve.airborne_gait import _freeze_data
from ..solve.constant_skin_targets import (
    CanonicalConstantSkinTargetLaw,
    ConstantSkinTargetUnavailable,
)
from ..solve.source_motion_query import _thaw
from ..solve.whole_body_gait_transition import _append_accessor, _encode


@dataclass(frozen=True)
class SourceCubicEmission:
    root_motion: bytes
    in_place: bytes
    plan: Mapping[str, Any]
    midpoint_plan: Mapping[str, Any]
    tangent_estimate: Mapping[str, Any]
    _checked_values: Mapping[float, Any] = field(repr=False, compare=False)
    _law_identity: int = field(repr=False, compare=False)
    _source_sha256: str = field(repr=False, compare=False)
    _input_plan_sha256: str = field(repr=False, compare=False)
    _stencils: tuple[float, float] = field(repr=False, compare=False)


def serialized_key_midpoint_times(glb: Glb, animation_name: str) -> list[float]:
    """Return exact decoded float32 keys interleaved with interval midpoints."""
    _, keys = read_animation_tracks(
        glb, animation_name, require_common_timeline=True
    )
    return [
        item
        for left, right in zip(keys[:-1], keys[1:])
        for item in (float(left), float((left + right) * .5))
    ] + [float(keys[-1])]


def one_sided_estimate(
    evaluate: Callable[[float], np.ndarray],
    time_s: float,
    *,
    direction: int,
    step_s: float,
) -> np.ndarray:
    """Second-order one-sided numerical derivative in units per second."""
    if direction not in (-1, 1):
        raise ContractError("source tangent direction must be -1 or 1")
    if not math.isfinite(time_s) or not math.isfinite(step_s) or step_s <= 0:
        raise ContractError("source tangent time and stencil must be finite")
    center = np.asarray(evaluate(time_s), dtype=float)
    near = np.asarray(evaluate(time_s + direction * step_s), dtype=float)
    far = np.asarray(evaluate(time_s + direction * 2 * step_s), dtype=float)
    if center.shape != near.shape or center.shape != far.shape:
        raise ContractError("source tangent samples must have one shape")
    if not all(np.isfinite(value).all() for value in (center, near, far)):
        raise ContractError("source tangent samples must be finite")
    return direction * (-3 * center + 4 * near - far) / (2 * step_s)


def _align_quaternions(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    if result.ndim != 3 or result.shape[2] != 4:
        raise ContractError("source rotations must be key by node by xyzw")
    norms = np.linalg.norm(result, axis=2)
    if not np.isfinite(result).all() or np.any(norms <= 1e-15):
        raise ContractError("source rotations must be finite nonzero quaternions")
    result /= norms[:, :, None]
    for index in range(1, len(result)):
        flip = np.sum(result[index - 1] * result[index], axis=1) < 0
        result[index, flip] *= -1
    return result


def _project_quaternion_tangent(anchor: np.ndarray, tangent: np.ndarray) -> np.ndarray:
    return tangent - anchor * np.sum(anchor * tangent, axis=1)[:, None]


def _build_cubic_glb(
    base: Glb,
    clip_name: str,
    times: np.ndarray,
    channels: Mapping[tuple[int, str], tuple[np.ndarray, np.ndarray, np.ndarray]],
    *,
    plan_sha256: str,
    state_track: Mapping[str, Any],
) -> bytes:
    document = deepcopy(base.document)
    binary = bytearray(base.binary)
    time_accessor = _append_accessor(
        document, binary, times.reshape((-1, 1)), "SCALAR"
    )
    samplers, animation_channels = [], []
    for (node, path), (incoming, values, outgoing) in sorted(channels.items()):
        if incoming.shape != values.shape or outgoing.shape != values.shape:
            raise ContractError("CUBICSPLINE tangent and value shapes must match")
        records = np.stack((incoming, values, outgoing), axis=1).reshape(
            (-1, values.shape[1])
        )
        output = _append_accessor(
            document,
            binary,
            records,
            {3: "VEC3", 4: "VEC4"}[values.shape[1]],
        )
        sampler = len(samplers)
        samplers.append(
            {
                "input": time_accessor,
                "output": output,
                "interpolation": "CUBICSPLINE",
            }
        )
        animation_channels.append(
            {"sampler": sampler, "target": {"node": node, "path": path}}
        )
    document["animations"] = [
        {
            "name": clip_name,
            "samplers": samplers,
            "channels": animation_channels,
            "extras": {
                "program": state_track["program"],
                "loop": bool(state_track.get("loop", True)),
                "sourceTangentEstimate": True,
                "planSha256": plan_sha256,
            },
        }
    ]
    document.setdefault("extras", {})["eonwildMotionStateTrack"] = deepcopy(
        state_track
    )
    document["buffers"][0]["byteLength"] = len(binary)
    return _encode(document, binary)


def emit_source_cubics(
    source: Glb,
    law: CanonicalConstantSkinTargetLaw,
    plan: Mapping[str, Any],
    *,
    root_node: int,
    stencil_s: float = 0.001,
    convergence_stencil_s: float = 0.0005,
    additional_key_times: tuple[float, ...] = (),
    reuse: SourceCubicEmission | None = None,
) -> SourceCubicEmission:
    """Evaluate one bound law at keys and one-sided source-time stencils."""
    if not isinstance(source, Glb) or not isinstance(law, CanonicalConstantSkinTargetLaw):
        raise ContractError("source cubic emission requires bound source and law")
    if (
        not math.isfinite(stencil_s)
        or not math.isfinite(convergence_stencil_s)
        or stencil_s <= 0
        or convergence_stencil_s <= 0
        or convergence_stencil_s >= stencil_s
    ):
        raise ContractError("source cubic stencils must be finite positive and ordered")
    rows = plan.get("samples")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ContractError("source cubic emission requires a retained plan")
    input_times = np.asarray([row["time_s"] for row in rows], dtype=float)
    if not np.isfinite(input_times).all() or np.any(np.diff(input_times) <= 0):
        raise ContractError("source cubic timeline must be finite and increasing")
    input_plan_sha256 = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    source_sha256 = hashlib.sha256(source.raw).hexdigest()
    if (not isinstance(additional_key_times, tuple)
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(value) for value in additional_key_times)):
        raise ContractError("source cubic additional keys must be a finite tuple")
    if any(not input_times[0] < value < input_times[-1]
           for value in additional_key_times):
        raise ContractError("source cubic additional keys must lie inside the source timeline")
    times = np.asarray(sorted({
        *(float(value) for value in input_times),
        *(float(value) for value in additional_key_times),
    }), dtype=float)
    if not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ContractError("source cubic timeline must be finite and increasing")
    midpoint_times = (times[:-1] + times[1:]) * 0.5
    requested = {float(value) for value in np.concatenate((times, midpoint_times))}
    for index, raw_time in enumerate(times):
        time_s = float(raw_time)
        for direction in (-1, 1):
            if (direction < 0 and index == 0) or (
                direction > 0 and index == len(times) - 1
            ):
                continue
            for step_s in (stencil_s, convergence_stencil_s):
                requested.add(time_s + direction * step_s)
                requested.add(time_s + direction * 2 * step_s)
    cache: dict[float, Any] = {}
    if reuse is not None:
        if (not isinstance(reuse, SourceCubicEmission)
                or reuse._law_identity != id(law)
                or reuse._source_sha256 != source_sha256
                or reuse._input_plan_sha256 != input_plan_sha256
                or reuse._stencils != (stencil_s, convergence_stencil_s)):
            raise ContractError("source cubic reuse differs from the bound source law")
        cache.update(reuse._checked_values)
    ordered_times = tuple(sorted(requested - set(cache)))
    batch = law.values(ordered_times) if ordered_times else ()
    for time_s, value in zip(ordered_times, batch):
        if isinstance(value, ConstantSkinTargetUnavailable):
            raise ContractError(
                f"source cubic checked value unavailable at {time_s}: {value.reason}"
            )
        cache[time_s] = value

    def checked(time_s: float):
        key = float(time_s)
        if key not in cache:
            raise ContractError("source cubic requested an unbound stencil time")
        return cache[key]

    key_values = [checked(float(time_s)) for time_s in times]
    translations = np.asarray([value.pose.translations for value in key_values])
    rotations = _align_quaternions(
        np.asarray([value.pose.rotations for value in key_values])
    )
    if translations.shape != (len(times), len(source.nodes), 3):
        raise ContractError("source cubic translations do not cover every node")

    def sample(path: str, anchor_index: int, time_s: float) -> np.ndarray:
        value = checked(time_s)
        result = np.asarray(
            value.pose.translations if path == "translation" else value.pose.rotations,
            dtype=float,
        )
        if path == "rotation":
            norms = np.linalg.norm(result, axis=1)
            if np.any(norms <= 1e-15):
                raise ContractError("source cubic sample contains zero quaternion")
            result = result / norms[:, None]
            flip = np.sum(result * rotations[anchor_index], axis=1) < 0
            result[flip] *= -1
        return result

    channel_data: dict[tuple[int, str], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    convergence = {"translation_m_per_s": 0.0, "rotation_xyzw_per_s": 0.0}
    for path, values in (("translation", translations), ("rotation", rotations)):
        incoming = np.zeros_like(values)
        outgoing = np.zeros_like(values)
        for index, time_s in enumerate(times):
            def evaluator(item: float, *, p: str = path, i: int = index):
                return sample(p, i, item)
            if index > 0:
                incoming[index] = one_sided_estimate(
                    evaluator, float(time_s), direction=-1, step_s=stencil_s
                )
                narrower = one_sided_estimate(
                    evaluator,
                    float(time_s),
                    direction=-1,
                    step_s=convergence_stencil_s,
                )
                convergence[
                    "translation_m_per_s" if path == "translation" else "rotation_xyzw_per_s"
                ] = max(
                    convergence[
                        "translation_m_per_s" if path == "translation" else "rotation_xyzw_per_s"
                    ],
                    float(np.max(np.linalg.norm(incoming[index] - narrower, axis=1))),
                )
            if index < len(times) - 1:
                outgoing[index] = one_sided_estimate(
                    evaluator, float(time_s), direction=1, step_s=stencil_s
                )
                narrower = one_sided_estimate(
                    evaluator,
                    float(time_s),
                    direction=1,
                    step_s=convergence_stencil_s,
                )
                convergence[
                    "translation_m_per_s" if path == "translation" else "rotation_xyzw_per_s"
                ] = max(
                    convergence[
                        "translation_m_per_s" if path == "translation" else "rotation_xyzw_per_s"
                    ],
                    float(np.max(np.linalg.norm(outgoing[index] - narrower, axis=1))),
                )
        if path == "rotation":
            incoming = np.asarray(
                [_project_quaternion_tangent(anchor, tangent)
                 for anchor, tangent in zip(rotations, incoming)]
            )
            outgoing = np.asarray(
                [_project_quaternion_tangent(anchor, tangent)
                 for anchor, tangent in zip(rotations, outgoing)]
            )
        for node in range(len(source.nodes)):
            channel_data[node, path] = (
                incoming[:, node], values[:, node], outgoing[:, node]
            )

    emitted_plan = deepcopy(plan)
    emitted_plan["samples"] = [_thaw(value.row) for value in key_values]
    midpoint_values = [checked(float(time_s)) for time_s in midpoint_times]
    midpoint_plan = deepcopy(emitted_plan)
    combined = [
        item
        for pair in zip(
            emitted_plan["samples"][:-1],
            [_thaw(value.row) for value in midpoint_values],
        )
        for item in pair
    ] + [emitted_plan["samples"][-1]]
    midpoint_plan["samples"] = combined
    midpoint_plan["duration_s"] = emitted_plan["duration_s"]

    digest = hashlib.sha256(
        json.dumps(emitted_plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    state = {
        "program": emitted_plan.get("program", "airborne_gait"),
        "loop": emitted_plan.get("loop", True),
        "samples": [
            {
                "time_s": row["time_s"],
                "flight": row["flight"],
                "support_count": row["support_count"],
            }
            for row in emitted_plan["samples"]
        ],
    }
    root_raw = _build_cubic_glb(
        source,
        "V9_SOURCE_CUBIC_ROOT_MOTION",
        times,
        channel_data,
        plan_sha256=digest,
        state_track=state,
    )
    in_place_channels = deepcopy(channel_data)
    root_in = np.zeros_like(translations[:, root_node])
    root_value = np.repeat(translations[0:1, root_node], len(times), axis=0)
    in_place_channels[root_node, "translation"] = (root_in, root_value, root_in.copy())
    in_place_raw = _build_cubic_glb(
        source,
        "V9_SOURCE_CUBIC_IN_PLACE",
        times,
        in_place_channels,
        plan_sha256=digest,
        state_track=state,
    )
    diagnostic = _freeze_data(
        {
            "classification": (
                "second-order one-sided numerical estimates of checked source-time "
                "values; no analytic derivative, branch, or global-C1 authority"
            ),
            "stencil_s": stencil_s,
            "convergence_stencil_s": convergence_stencil_s,
            "checked_source_time_count": len(cache),
            "new_checked_source_time_count": len(ordered_times),
            "key_count": len(times),
            "additional_key_count": len(times) - len(input_times),
            "midpoint_count": len(midpoint_times),
            "maximum_stencil_difference": convergence,
            "quaternion_tangent_units": "xyzw components per second before normalized glTF playback",
            "translation_tangent_units": "metres per second",
            "unused_boundary_records": "zero first incoming and final outgoing records",
        }
    )
    return SourceCubicEmission(
        root_raw, in_place_raw, _freeze_data(emitted_plan),
        _freeze_data(midpoint_plan), diagnostic, dict(cache), id(law),
        source_sha256, input_plan_sha256,
        (stencil_s, convergence_stencil_s),
    )


__all__ = [
    "SourceCubicEmission", "emit_source_cubics", "one_sided_estimate",
    "serialized_key_midpoint_times",
]
