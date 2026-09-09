"""Source-surface authored motion adapted into the existing target row solver."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
from types import MappingProxyType
from typing import Any, Mapping

from ..errors import ContractError
from ..planning.foot_articulation import recovery_pitch
from ..planning.grounded_gait import GroundedGait, smooth
from .support_anchors import _digest

TARGET_MATERIAL_GAP_M = 0.0001
TARGET_RESIDUAL_LIMIT_M = 0.001
MATERIAL_EFFECTOR_RESOLUTION = "material_floor_and_local_joint_feasibility.v3"
MATERIAL_CLEARANCE_POLICY_SCHEMA = (
    "eonwild.motion.authored-material-clearance-policy.v1"
)
MATERIAL_CLEARANCE_POLICY_MODEL = "body_height_fraction.v1"


def _query_identity(query: Any) -> str:
    return _digest(
        {
            "source_raw_sha256": __import__("hashlib")
            .sha256(query._source.raw)
            .hexdigest(),
            "source_document": query._source.document,
            "source_binary_sha256": __import__("hashlib")
            .sha256(query._source.binary)
            .hexdigest(),
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
        }
    )


def _finite(value: Any, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ContractError(f"authored material contact {label} must be finite numeric")
    return float(value)


def _linear(values: tuple[float, ...], phase: float) -> float:
    intervals = len(values) - 1
    x = (phase % 1.0) * intervals
    left = min(int(math.floor(x)), intervals - 1)
    u = x - left
    return values[left] * (1 - u) + values[left + 1] * u


def _material_clearance_policy(
    value: Mapping[str, Any] | None, *, body_height_m: float
) -> tuple[Mapping[str, Any], float]:
    expected = {
        "schema",
        "id",
        "version",
        "model",
        "maximum_clearance_body_heights",
        "classification",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ContractError(
            "authored material contact needs a complete material-clearance policy"
        )
    if value["schema"] != MATERIAL_CLEARANCE_POLICY_SCHEMA:
        raise ContractError("authored material-clearance policy schema is unsupported")
    if value["model"] != MATERIAL_CLEARANCE_POLICY_MODEL:
        raise ContractError("authored material-clearance policy model is unsupported")
    if not isinstance(value["id"], str) or not value["id"].strip():
        raise ContractError("authored material-clearance policy id is invalid")
    if type(value["version"]) is not int or value["version"] <= 0:
        raise ContractError("authored material-clearance policy version is invalid")
    if value["classification"] != "source_backed_engineering_candidate":
        raise ContractError(
            "authored material-clearance policy classification is unsupported"
        )
    fraction = _finite(
        value["maximum_clearance_body_heights"],
        "maximum clearance body heights",
    )
    if fraction <= 0:
        raise ContractError(
            "authored material-clearance policy maximum must be positive"
        )
    height = _finite(body_height_m, "body height")
    if height <= 0:
        raise ContractError("authored material contact body height must be positive")
    return MappingProxyType(deepcopy(dict(value))), fraction * height


@dataclass(frozen=True)
class _SidePath:
    contact: tuple[bool, ...]
    clearance_m: tuple[float, ...]
    forward_m: tuple[float, ...]
    foot_pitch_degrees: tuple[float, ...]
    swing_phase: tuple[float, ...]
    touchdown_index: int
    toe_off_index: int


class AuthoredMaterialContactAdapter:
    """Immutable source-material path bound to one target query configuration."""

    def __init__(
        self,
        *,
        binding: str,
        capsule: Mapping[str, Any],
        paths: Mapping[str, _SidePath],
        scale: float,
        retime_policy: str,
        material_clearance_policy: Mapping[str, Any],
        target_maximum_material_clearance_m: float,
    ):
        self._query_binding_sha256 = binding
        self._capsule = MappingProxyType(deepcopy(dict(capsule)))
        self._capsule_sha256 = _digest(capsule)
        self._paths = MappingProxyType(dict(paths))
        self._scale = scale
        self._retime_policy = retime_policy
        self._material_clearance_policy = material_clearance_policy
        self._material_clearance_policy_sha256 = _digest(material_clearance_policy)
        self._target_maximum_material_clearance_m = (
            target_maximum_material_clearance_m
        )
        self._integrity_sha256 = self._current_integrity_sha256()

    def _current_integrity_sha256(self) -> str:
        return _digest(
            {
                "capsule_sha256": self._capsule_sha256,
                "query_binding_sha256": self._query_binding_sha256,
                "clearance_scale": self._scale,
                "retime_policy": self._retime_policy,
                "material_clearance_policy": self._material_clearance_policy,
                "target_maximum_material_clearance_m": (
                    self._target_maximum_material_clearance_m
                ),
                "paths": {
                    side: {
                        "contact": path.contact,
                        "clearance_m": path.clearance_m,
                        "forward_m": path.forward_m,
                        "foot_pitch_degrees": path.foot_pitch_degrees,
                        "swing_phase": path.swing_phase,
                        "touchdown_index": path.touchdown_index,
                        "toe_off_index": path.toe_off_index,
                    }
                    for side, path in self._paths.items()
                },
            }
        )

    @classmethod
    def build(
        cls,
        query: Any,
        capsule: Mapping[str, Any],
        *,
        authored_source: bytes,
        body_height_m: float,
        material_clearance_policy: Mapping[str, Any] | None = None,
        retime_policy: str = "phase_preserving.v1",
    ) -> "AuthoredMaterialContactAdapter":
        if (
            not isinstance(capsule, Mapping)
            or capsule.get("schema") != "eonwild.motion.authored-material-path.v1"
        ):
            raise ContractError(
                "authored material contact needs a v1 source-surface capsule"
            )
        if capsule.get("source_geometry_sha256") != capsule.get(
            "measured_source_sha256"
        ):
            raise ContractError(
                "authored material contact capsule source identity is inconsistent"
            )
        if not isinstance(authored_source, bytes) or hashlib.sha256(
            authored_source
        ).hexdigest() != capsule.get("source_geometry_sha256"):
            raise ContractError(
                "authored material contact source bytes differ from the measured source"
            )
        count = capsule.get("interval_count")
        if type(count) is not int or count < 3:
            raise ContractError(
                "authored material contact interval count must be integer >= 3"
            )
        fps = _finite(capsule.get("fps"), "fps")
        if fps <= 0 or not math.isclose(
            _finite(capsule.get("duration_s"), "duration"),
            count / fps,
            rel_tol=0,
            abs_tol=1e-12,
        ):
            raise ContractError(
                "authored material contact source clock is inconsistent"
            )
        if retime_policy != "phase_preserving.v1":
            raise ContractError(
                "authored material contact requires phase-preserving retiming"
            )
        if type(query._locomotion_gait) is not GroundedGait:
            raise ContractError(
                "authored material contact currently requires grounded locomotion"
            )
        if not math.isclose(
            _finite(body_height_m, "body height"),
            query._context.body_height,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise ContractError(
                "authored material contact body height differs from its source query"
            )
        policy, target_maximum = _material_clearance_policy(
            material_clearance_policy,
            body_height_m=body_height_m,
        )
        raw_feet = capsule.get("feet")
        if not isinstance(raw_feet, Mapping) or set(raw_feet) != {"left", "right"}:
            raise ContractError("authored material contact requires bilateral paths")
        parsed: dict[str, dict[str, Any]] = {}
        for side in ("left", "right"):
            raw = raw_feet[side]
            expected = {
                "contact",
                "clearance_m",
                "forward_progress",
                "foot_pitch_degrees",
                "swing_phase",
                "touchdown_index",
                "toe_off_index",
            }
            if not isinstance(raw, Mapping) or set(raw) != expected:
                raise ContractError(
                    "authored material contact foot path shape is invalid"
                )
            arrays: dict[str, tuple[Any, ...]] = {}
            for name in (
                "clearance_m",
                "forward_progress",
                "foot_pitch_degrees",
                "swing_phase",
            ):
                value = raw[name]
                if not isinstance(value, list) or len(value) != count + 1:
                    raise ContractError(
                        "authored material contact path length differs from its clock"
                    )
                arrays[name] = tuple(_finite(v, f"{side} {name}") for v in value)
                if not math.isclose(
                    arrays[name][0], arrays[name][-1], rel_tol=0, abs_tol=1e-10
                ):
                    raise ContractError(
                        "authored material contact source path is not closed"
                    )
            contact = raw["contact"]
            if (
                not isinstance(contact, list)
                or len(contact) != count + 1
                or any(type(v) is not bool for v in contact)
                or contact[0] is not contact[-1]
            ):
                raise ContractError("authored material contact contact path is invalid")
            arrays["contact"] = tuple(contact)
            touchdown, toeoff = raw["touchdown_index"], raw["toe_off_index"]
            if (
                type(touchdown) is not int
                or type(toeoff) is not int
                or not 0 <= touchdown < count
                or not 0 <= toeoff < count
                or touchdown == toeoff
            ):
                raise ContractError(
                    "authored material contact event indices are invalid"
                )
            if not arrays["contact"][touchdown] or not arrays["contact"][toeoff]:
                raise ContractError(
                    "authored material contact events must be loaded keys"
                )
            expected_contact = []
            index = touchdown
            while True:
                expected_contact.append(index)
                if index == toeoff:
                    break
                index = (index + 1) % count
            expected_contact_set = set(expected_contact)
            if any(
                arrays["contact"][index] is not (index in expected_contact_set)
                for index in range(count)
            ):
                raise ContractError(
                    "authored material contact path contradicts its event indices"
                )
            swing_intervals = (touchdown - toeoff) % count
            for index in range(count + 1):
                loaded = arrays["contact"][index]
                clearance = arrays["clearance_m"][index]
                swing = arrays["swing_phase"][index]
                if clearance < -1e-12 or not 0 <= swing <= 1:
                    raise ContractError(
                        "authored material contact clearance or phase is invalid"
                    )
                if loaded and (abs(clearance) > 1e-10 or abs(swing) > 1e-10):
                    raise ContractError(
                        "authored loaded keys must have zero clearance and swing phase"
                    )
                if not loaded and not 0 < swing < 1:
                    raise ContractError(
                        "authored swing keys require an interior swing phase"
                    )
                expected_swing = (
                    0.0
                    if loaded
                    else ((index - toeoff) % count) / swing_intervals
                )
                if not math.isclose(
                    swing, expected_swing, rel_tol=0.0, abs_tol=1e-10
                ):
                    raise ContractError(
                        "authored material contact swing phase contradicts its events"
                    )
            parsed[side] = {
                **arrays,
                "touchdown_index": touchdown,
                "toe_off_index": toeoff,
            }

        duration = query._times[-1] - query._times[0]
        source_maximum = max(max(parsed[s]["clearance_m"]) for s in ("left", "right"))
        if source_maximum <= 1e-12 or target_maximum <= 1e-12:
            raise ContractError(
                "authored material contact needs nonzero source and target swing clearance"
            )
        if any(
            not (
                parsed["left"]["contact"][index]
                or parsed["right"]["contact"][index]
            )
            for index in range(count)
        ):
            raise ContractError(
                "grounded authored material contact cannot declare a flight key"
            )
        scale = target_maximum / source_maximum
        paths = {}
        for side in ("left", "right"):
            raw = parsed[side]
            td = raw["touchdown_index"]
            toe = raw["toe_off_index"]
            touchdown_time = query._times[0] + duration * td / count
            current_anchor = query._sample_row(touchdown_time, apply_clearance=False)[
                "feet"
            ][side]["forward_m"]
            cycle_travel = (
                query._sample_row(query._times[0] + duration, apply_clearance=False)[
                    "root_forward_m"
                ]
                - query._sample_row(query._times[0], apply_clearance=False)[
                    "root_forward_m"
                ]
            )
            forward = []
            for index in range(count):
                time = query._times[0] + duration * index / count
                root = query._sample_row(time, apply_clearance=False)["root_forward_m"]
                if raw["contact"][index]:
                    anchor = (
                        current_anchor - cycle_travel if index < td else current_anchor
                    )
                else:
                    progress = raw["forward_progress"][index]
                    if toe < td:
                        anchor = current_anchor - cycle_travel * (1 - progress)
                    else:
                        anchor = current_anchor + cycle_travel * progress
                forward.append(float(anchor - root))
            forward.append(forward[0])
            paths[side] = _SidePath(
                contact=raw["contact"],
                clearance_m=raw["clearance_m"],
                forward_m=tuple(forward),
                foot_pitch_degrees=raw["foot_pitch_degrees"],
                swing_phase=raw["swing_phase"],
                touchdown_index=td,
                toe_off_index=toe,
            )
        return cls(
            binding=_query_identity(query),
            capsule=capsule,
            paths=paths,
            scale=scale,
            retime_policy=retime_policy,
            material_clearance_policy=policy,
            target_maximum_material_clearance_m=target_maximum,
        )

    def validate_for_query(self, query: Any) -> None:
        if _query_identity(query) != self._query_binding_sha256:
            raise ContractError(
                "authored material contact adapter belongs to another source query"
            )
        if _digest(self._capsule) != self._capsule_sha256:
            raise ContractError(
                "authored material contact capsule differs from its validated values"
            )
        if self._current_integrity_sha256() != self._integrity_sha256:
            raise ContractError(
                "authored material contact derived path differs from its validated values"
            )

    def resolve(
        self, query: Any, row: Mapping[str, Any], time_s: float
    ) -> dict[str, Any]:
        self.validate_for_query(query)
        return self._resolve_owned(query, row, time_s)

    def _resolve_owned(
        self, query: Any, row: Mapping[str, Any], time_s: float
    ) -> dict[str, Any]:
        result = deepcopy(dict(row))
        duration = query._times[-1] - query._times[0]
        phase = (time_s - query._times[0]) / duration
        cycle_index = math.floor(phase)
        cycle_phase = phase - cycle_index
        interval_count = len(self._paths["left"].contact) - 1
        x = cycle_phase * interval_count
        nearest_key = round(x)
        if math.isclose(x, nearest_key, rel_tol=0.0, abs_tol=1e-12):
            x = float(nearest_key % interval_count)
        key = int(math.floor(x))
        at_key = x == key
        for side in ("left", "right"):
            path = self._paths[side]
            # Contact owns complete key-to-key intervals. A switch is legal only
            # at a retained zero-clearance event key; interpolation on either
            # adjacent swing interval therefore approaches zero continuously.
            contact = path.contact[key] and (at_key or path.contact[key + 1])
            foot = result["feet"][side]
            foot["contact"] = bool(contact)
            foot["height_m"] = (
                0.0 if contact else self._scale * _linear(path.clearance_m, phase)
            )
            foot["authored_material_clearance_m"] = float(foot["height_m"])
            foot["forward_m"] = result["root_forward_m"] + _linear(
                path.forward_m, phase
            )
            foot["foot_pitch_degrees"] = _linear(path.foot_pitch_degrees, phase)
            swing_intervals = (path.touchdown_index - path.toe_off_index) % (
                len(path.contact) - 1
            )
            foot["swing_phase"] = (
                0.0
                if contact
                else ((x - path.toe_off_index) % (len(path.contact) - 1))
                / swing_intervals
            )
            touchdown_cycle = cycle_index + path.touchdown_index / interval_count
            if touchdown_cycle > phase + 1e-12:
                touchdown_cycle -= 1
            foot["touchdown_time_s"] = query._times[0] + duration * touchdown_cycle
            gait = query._locomotion_gait
            if contact:
                foot["toe_flex_degrees"] = 0.0
            elif gait.toe_recovery_peak_fraction is not None:
                foot["toe_flex_degrees"] = -recovery_pitch(
                    foot["swing_phase"],
                    gait.toe_flex_degrees,
                    gait.toe_recovery_peak_fraction,
                )
            else:
                recovery = math.sin(math.pi * smooth(foot["swing_phase"])) ** 2
                foot["toe_flex_degrees"] = gait.toe_flex_degrees * recovery
            for name in tuple(foot):
                if name.startswith("metatarsal_recovery_"):
                    foot.pop(name)
            foot.pop("target_offset_m", None)
        result["support_count"] = sum(
            int(result["feet"][s]["contact"]) for s in ("left", "right")
        )
        result["flight"] = result["support_count"] == 0
        result["stage"] = (
            "FLIGHT"
            if result["flight"]
            else "DOUBLE_SUPPORT"
            if result["support_count"] == 2
            else "SINGLE_SUPPORT"
        )
        return result

    def binding(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema": "eonwild.motion.authored-material-contact-binding.v1",
                "capsule_sha256": self._capsule_sha256,
                "query_binding_sha256": self._query_binding_sha256,
                "clearance_scale": self._scale,
                "retime_policy": self._retime_policy,
                "material_clearance_policy_sha256": (
                    self._material_clearance_policy_sha256
                ),
                "material_clearance_policy": self._material_clearance_policy,
                "target_maximum_material_clearance_m": (
                    self._target_maximum_material_clearance_m
                ),
                "material_effector_resolution": MATERIAL_EFFECTOR_RESOLUTION,
                "target_material_gap_m": TARGET_MATERIAL_GAP_M,
                "target_residual_limit_m": TARGET_RESIDUAL_LIMIT_M,
                "source_fps": float(self._capsule["fps"]),
                "source_interval_count": int(self._capsule["interval_count"]),
                "source_duration_s": float(self._capsule["duration_s"]),
            }
        )
