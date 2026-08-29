"""Immutable models for the first, grounded V9 contract slice.

The models deliberately contain no animal-specific behavior.  The JSON
schemas and loader own admission; these classes provide a small typed view for
the planner after admission has succeeded.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from ..errors import ContractError
from ..hashing import sha256_json


V9_SCHEMA_IDS = {
    "intent": "eonwild.motion.v9.motion-intent.v1",
    "program": "eonwild.motion.v9.motion-program.v1",
    "body": "eonwild.motion.v9.body-instance-profile.v1",
    "contact": "eonwild.motion.v9.contact-state.v1",
    "plan": "eonwild.motion.v9.centroidal-contact-plan.v1",
    "evidence": "eonwild.motion.v9.stationary-support-evidence.v1",
}

CANONICAL_FAMILY = "heavy_predatory_biped"
CANONICAL_COORDINATE_SYSTEM = {
    "units": "m",
    "time_units": "s",
    "mass_units": "kg",
    "handedness": "right",
    "up_axis": "Y",
    "forward_axis": "-Z",
}

Vec3 = tuple[float, float, float]


def _number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be a finite number")
    return result


def ensure_finite(value: Any, *, label: str = "V9 value") -> None:
    """Reject non-finite numbers recursively before validation or hashing."""

    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        try:
            finite = math.isfinite(value)
        except (OverflowError, TypeError) as exc:
            raise ContractError(f"{label}: number is not finite") from exc
        if not finite:
            raise ContractError(f"{label}: number is not finite")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ContractError(f"{label}: object keys must be strings")
            ensure_finite(child, label=f"{label}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            ensure_finite(child, label=f"{label}[{index}]")
        return
    raise ContractError(f"{label}: unsupported value type {type(value).__name__}")


def _vec3(value: Any, *, label: str) -> Vec3:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ContractError(f"{label} must contain exactly three numbers")
    return tuple(_number(item, label=f"{label}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]


def canonical_hash(value: Any) -> str:
    """Return the repository's deterministic JSON hash for a V9 value."""

    ensure_finite(value, label="canonical V9 value")
    return sha256_json(value)


@dataclass(frozen=True)
class CoordinateSystem:
    units: str
    time_units: str
    mass_units: str
    handedness: str
    up_axis: str
    forward_axis: str

    @classmethod
    def from_document(cls, value: Mapping[str, Any], *, label: str) -> "CoordinateSystem":
        if dict(value) != CANONICAL_COORDINATE_SYSTEM:
            raise ContractError(
                f"{label}: coordinate system must be canonical metres/right/Y-up/-Z"
            )
        return cls(**CANONICAL_COORDINATE_SYSTEM)

    def as_dict(self) -> dict[str, str]:
        return {
            "units": self.units,
            "time_units": self.time_units,
            "mass_units": self.mass_units,
            "handedness": self.handedness,
            "up_axis": self.up_axis,
            "forward_axis": self.forward_axis,
        }


@dataclass(frozen=True)
class MotionIntent:
    id: str
    coordinate_system: CoordinateSystem
    kind: str
    duration_s: float
    grounded: bool
    allow_airborne: bool
    linear_velocity_mps: Vec3

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "MotionIntent":
        return cls(
            id=str(document["id"]),
            coordinate_system=CoordinateSystem.from_document(
                document["coordinate_system"], label="motion intent"
            ),
            kind=str(document["desired_motion"]["kind"]),
            duration_s=_number(
                document["desired_motion"]["duration_s"], label="intent duration_s"
            ),
            grounded=bool(document["condition"]["grounded"]),
            allow_airborne=bool(document["condition"]["allow_airborne"]),
            linear_velocity_mps=_vec3(
                document["current_state"]["linear_velocity_mps"],
                label="intent linear_velocity_mps",
            ),
        )


@dataclass(frozen=True)
class ProgramPhase:
    id: str
    duration_s: float
    contact_effectors: tuple[str, ...]


@dataclass(frozen=True)
class MotionProgram:
    id: str
    version: int
    kind: str
    coordinate_system: CoordinateSystem
    purpose: str
    phases: tuple[ProgramPhase, ...]
    invariants: Mapping[str, bool]

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "MotionProgram":
        phases = tuple(
            ProgramPhase(
                id=str(phase["id"]),
                duration_s=_number(phase["duration_s"], label="program phase duration_s"),
                contact_effectors=tuple(str(item) for item in phase["contact_effectors"]),
            )
            for phase in document["phase_template"]
        )
        return cls(
            id=str(document["id"]),
            version=int(document["version"]),
            kind=str(document["kind"]),
            coordinate_system=CoordinateSystem.from_document(
                document["coordinate_system"], label="motion program"
            ),
            purpose=str(document["purpose"]),
            phases=phases,
            invariants={
                "grounded_only": bool(document["invariants"]["grounded_only"]),
                "airborne_allowed": bool(document["invariants"]["airborne_allowed"]),
                "zero_velocity": bool(document["invariants"]["zero_velocity"]),
            },
        )


@dataclass(frozen=True)
class SegmentMassProperties:
    id: str
    parent_id: str | None
    role: str
    mass_fraction: float
    com_body_m: Vec3
    inertia_diagonal_normalized: Vec3


@dataclass(frozen=True)
class BodyInstanceProfile:
    profile_id: str
    family: str
    taxon: str
    coordinate_system: CoordinateSystem
    dimensions: Mapping[str, float | None]
    segment_com_frame: str
    mass_mode: str
    total_mass_kg: float | None
    mass_fraction_sum: float
    absolute_dynamics_enabled: bool
    absolute_policy: str
    provenance_status: str
    segments: tuple[SegmentMassProperties, ...]

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "BodyInstanceProfile":
        mass = document["mass"]
        segments = tuple(
            SegmentMassProperties(
                id=str(segment["id"]),
                parent_id=segment["parent_id"],
                role=str(segment["role"]),
                mass_fraction=_number(
                    segment["mass_fraction"], label="segment mass_fraction"
                ),
                com_body_m=_vec3(segment["com_body_m"], label="segment com_body_m"),
                inertia_diagonal_normalized=_vec3(
                    segment["inertia_diagonal_normalized"],
                    label="segment inertia_diagonal_normalized",
                ),
            )
            for segment in document["segments"]
        )
        total_mass = mass["total_mass_kg"]
        return cls(
            profile_id=str(document["profile_id"]),
            family=str(document["family"]),
            taxon=str(document["taxon"]),
            coordinate_system=CoordinateSystem.from_document(
                document["coordinate_system"], label="body profile"
            ),
            dimensions={
                key: None if value is None else _number(value, label=f"dimensions.{key}")
                for key, value in document["dimensions"].items()
            },
            segment_com_frame=str(document["segment_com_frame"]),
            mass_mode=str(mass["mode"]),
            total_mass_kg=None if total_mass is None else _number(total_mass, label="total_mass_kg"),
            mass_fraction_sum=_number(
                mass["mass_fraction_sum"], label="mass_fraction_sum"
            ),
            absolute_dynamics_enabled=bool(mass["absolute_dynamics_enabled"]),
            absolute_policy=str(mass["absolute_policy"]),
            provenance_status=str(document["provenance"]["status"]),
            segments=segments,
        )


@dataclass(frozen=True)
class ContactState:
    id: str
    coordinate_system: CoordinateSystem
    effector: str
    state: str
    time_s: float
    load_fraction: float
    point_m: Vec3
    normal: Vec3
    friction_coefficient: float

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "ContactState":
        patch = document["patch"]
        return cls(
            id=str(document["id"]),
            coordinate_system=CoordinateSystem.from_document(
                document["coordinate_system"], label="contact state"
            ),
            effector=str(document["effector"]),
            state=str(document["state"]),
            time_s=_number(document["time_s"], label="contact time_s"),
            load_fraction=_number(
                document["load_fraction"], label="contact load_fraction"
            ),
            point_m=_vec3(patch["point_m"], label="contact point_m"),
            normal=_vec3(patch["normal"], label="contact normal"),
            friction_coefficient=_number(
                patch["friction_coefficient"], label="contact friction_coefficient"
            ),
        )


@dataclass(frozen=True)
class StationarySupportResult:
    plan: dict[str, Any]
    evidence: dict[str, Any]
    plan_sha256: str
    evidence_sha256: str

    @property
    def report(self) -> dict[str, Any]:
        return {
            "schema": V9_SCHEMA_IDS["evidence"],
            "report_id": f"stationary-support:{self.plan['plan_id']}",
            "plan": self.plan,
            "evidence": self.evidence,
        }
