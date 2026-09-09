"""Source-surface authored motion adapted into the existing target row solver."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
from types import MappingProxyType
from typing import Any, Mapping

from ..errors import ContractError
from .support_anchors import _digest


def _query_identity(query: Any) -> str:
    return _digest({
        "source_raw_sha256": __import__("hashlib").sha256(query._source.raw).hexdigest(),
        "source_document": query._source.document,
        "source_binary_sha256": __import__("hashlib").sha256(query._source.binary).hexdigest(),
        "roles": query._roles,
        "solver_gait": query._solver_gait,
        "locomotion_gait": query._locomotion_gait,
        "transition": query._transition,
        "plan": query._plan,
        "contact_profile": query._contact_profile,
        "up_axis": query._up_axis,
        "forward_axis": query._forward_axis,
        "source_clip": query._source_clip,
        "legacy_overlay": query._legacy_overlay,
        "articulation_profile": query.context.articulation_profile,
        "transition_clearance": (
            None
            if query._transition_clearance is None
            else query._transition_clearance.binding()
        ),
    })


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ContractError(f"authored material contact {label} must be finite numeric")
    return float(value)


def _linear(values: tuple[float, ...], phase: float) -> float:
    intervals = len(values) - 1
    x = (phase % 1.0) * intervals
    left = min(int(math.floor(x)), intervals - 1)
    u = x - left
    return values[left] * (1 - u) + values[left + 1] * u


@dataclass(frozen=True)
class _SidePath:
    clearance_m: tuple[float, ...]
    forward_m: tuple[float, ...]
    foot_pitch_degrees: tuple[float, ...]
    contact_forward_m: float


class AuthoredMaterialContactAdapter:
    """Immutable source-material path bound to one target query configuration."""

    def __init__(self, *, binding: str, capsule: Mapping[str, Any], paths: Mapping[str, _SidePath], scale: float, contact_tolerance_m: float):
        self._query_binding_sha256 = binding
        self._capsule = MappingProxyType(deepcopy(dict(capsule)))
        self._capsule_sha256 = _digest(capsule)
        self._paths = MappingProxyType(dict(paths))
        self._scale = scale
        self._contact_tolerance_m = contact_tolerance_m

    @classmethod
    def build(
        cls,
        query: Any,
        capsule: Mapping[str, Any],
        *,
        authored_source: bytes,
        spatial_scale: Any,
        contact_tolerance_ratio: Any = 0.02,
    ) -> "AuthoredMaterialContactAdapter":
        if not isinstance(capsule, Mapping) or capsule.get("schema") != "eonwild.motion.authored-material-path.v1":
            raise ContractError("authored material contact needs a v1 source-surface capsule")
        if capsule.get("source_geometry_sha256") != capsule.get("measured_source_sha256"):
            raise ContractError("authored material contact capsule source identity is inconsistent")
        if not isinstance(authored_source, bytes) or hashlib.sha256(
            authored_source
        ).hexdigest() != capsule.get("source_geometry_sha256"):
            raise ContractError(
                "authored material contact source bytes differ from the measured source"
            )
        count = capsule.get("interval_count")
        if type(count) is not int or count < 3:
            raise ContractError("authored material contact interval count must be integer >= 3")
        fps = _finite(capsule.get("fps"), "fps")
        if fps <= 0 or not math.isclose(_finite(capsule.get("duration_s"), "duration"), count / fps, rel_tol=0, abs_tol=1e-12):
            raise ContractError("authored material contact source clock is inconsistent")
        scale = _finite(spatial_scale, "spatial scale")
        tolerance_ratio = _finite(contact_tolerance_ratio, "contact tolerance ratio")
        if not 0 < scale <= 100 or not 0 <= tolerance_ratio <= .1:
            raise ContractError("authored material contact adaptation bounds are invalid")
        raw_feet = capsule.get("feet")
        if not isinstance(raw_feet, Mapping) or set(raw_feet) != {"left", "right"}:
            raise ContractError("authored material contact requires bilateral paths")
        parsed = {}
        maxima = []
        for side in ("left", "right"):
            raw = raw_feet[side]
            if not isinstance(raw, Mapping) or set(raw) != {"clearance_m", "forward_m", "foot_pitch_degrees"}:
                raise ContractError("authored material contact foot path shape is invalid")
            arrays = {}
            for name in raw:
                value = raw[name]
                if not isinstance(value, list) or len(value) != count + 1:
                    raise ContractError("authored material contact path length differs from its clock")
                arrays[name] = tuple(_finite(v, f"{side} {name}") for v in value)
                if not math.isclose(arrays[name][0], arrays[name][-1], rel_tol=0, abs_tol=1e-10):
                    raise ContractError("authored material contact source path is not closed")
            if min(arrays["clearance_m"]) < -1e-10:
                raise ContractError("authored material contact clearance cannot be negative")
            maxima.append(max(arrays["clearance_m"]))
            parsed[side] = arrays
        contact_tolerance = tolerance_ratio * max(maxima)
        # A side is support-authoritative when its evaluated material surface is
        # the lower one; near-equal surfaces retain honest double support.
        contacts = {side: [] for side in ("left", "right")}
        for index in range(count + 1):
            left = parsed["left"]["clearance_m"][index]
            right = parsed["right"]["clearance_m"][index]
            contacts["left"].append(left <= right + contact_tolerance)
            contacts["right"].append(right <= left + contact_tolerance)
        paths = {}
        duration = query._times[-1] - query._times[0]
        for side in ("left", "right"):
            indices = [i for i, active in enumerate(contacts[side][:-1]) if active]
            if not indices:
                raise ContractError("authored material contact infers no support for one side")
            touchdown = min(indices, key=lambda i: parsed[side]["clearance_m"][i])
            target_time = query._times[0] + duration * touchdown / count
            row = query._sample_row(target_time, apply_clearance=False)
            base_relative = row["feet"][side]["forward_m"] - row["root_forward_m"]
            source_forward = parsed[side]["forward_m"][touchdown]
            paths[side] = _SidePath(
                parsed[side]["clearance_m"],
                tuple(base_relative + scale * (v - source_forward) for v in parsed[side]["forward_m"]),
                parsed[side]["foot_pitch_degrees"],
                base_relative,
            )
        return cls(
            binding=_query_identity(query),
            capsule=capsule,
            paths=paths,
            scale=scale,
            contact_tolerance_m=contact_tolerance,
        )

    def validate_for_query(self, query: Any) -> None:
        if _query_identity(query) != self._query_binding_sha256:
            raise ContractError("authored material contact adapter belongs to another source query")
        if _digest(self._capsule) != self._capsule_sha256:
            raise ContractError("authored material contact capsule differs from its validated values")

    def resolve(self, query: Any, row: Mapping[str, Any], time_s: float) -> dict[str, Any]:
        self.validate_for_query(query)
        return self._resolve_owned(query, row, time_s)

    def _resolve_owned(
        self, query: Any, row: Mapping[str, Any], time_s: float
    ) -> dict[str, Any]:
        result = deepcopy(dict(row))
        duration = query._times[-1] - query._times[0]
        phase = (time_s - query._times[0]) / duration
        clearances = {s: _linear(self._paths[s].clearance_m, phase) for s in ("left", "right")}
        contact = {
            "left": clearances["left"] <= clearances["right"] + self._contact_tolerance_m,
            "right": clearances["right"] <= clearances["left"] + self._contact_tolerance_m,
        }
        for side in ("left", "right"):
            foot = result["feet"][side]
            foot["contact"] = contact[side]
            foot["height_m"] = 0.0 if contact[side] else self._scale * clearances[side]
            foot["forward_m"] = result["root_forward_m"] + _linear(self._paths[side].forward_m, phase)
            foot["foot_pitch_degrees"] = _linear(self._paths[side].foot_pitch_degrees, phase)
            foot.pop("target_offset_m", None)
        return result

    def binding(self) -> Mapping[str, Any]:
        return MappingProxyType({"schema": "eonwild.motion.authored-material-contact-binding.v1", "capsule_sha256": self._capsule_sha256, "query_binding_sha256": self._query_binding_sha256, "spatial_scale": self._scale, "contact_tolerance_m": self._contact_tolerance_m})
