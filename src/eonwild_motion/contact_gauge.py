"""Deterministic, read-only V9 contact and gauge measurements.

The module has two deliberately separate concerns:

* a small generic frame-sequence analyzer, which is the executable contract
  and is easy to exercise with synthetic data; and
* a glTF adapter that evaluates an existing skinned animation into that same
  frame shape without writing the source artifact.

This is measurement and contract validation only.  It is not a contact solver,
support-polygon proof, whole-body dynamics implementation, or motion editor.
All source-specific names live in a data profile, never in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import struct
from typing import Any, Mapping, Sequence

from .contracts.v9_models import CANONICAL_COORDINATE_SYSTEM, canonical_hash, ensure_finite
from .errors import ContractError, ValidationFailure
from .glb.animation import TrsTrack, read_animation_tracks
from .glb.container import Glb
from .hashing import sha256_file, write_json


Vec3 = tuple[float, float, float]
Mat4 = tuple[tuple[float, float, float, float], ...]

POLICY_SCHEMA = "eonwild.motion.family_narrow_gauge_contract.v1"
POLICY_SCHEMA_V2 = "eonwild.motion.family_narrow_gauge_contract.v2"
POLICY_SCHEMA_V3 = "eonwild.motion.family_narrow_gauge_contract.v3"
REPORT_SCHEMA = "eonwild.motion.v9.contact-gauge-report.v1"
SOURCE_SCHEMA = "eonwild.motion.v9.contact-gauge-source.v1"

_POLICY_KEYS = {
    "schema",
    "status",
    "scientificClaim",
    "speciesHardcode",
    "purpose",
    "evidenceBoundary",
    "normalization",
    "metrics",
    "familyCalibration",
    "gaitStates",
    "acceptanceGates",
    "primarySources",
    "recommendedEvidence",
}
_POLICY_V2_KEYS = _POLICY_KEYS | {
    "predecessor",
    "metricSemantics",
    "plannerTargets",
    "calibrationEvidence",
}
_POLICY_V3_KEYS = _POLICY_V2_KEYS | {
    "laneExtensionEvidence",
    "plannerRecommendation",
}
_SOURCE_KEYS = {
    "schema",
    "coordinate_system",
    "source",
    "geometry",
    "sampling",
    "thresholds",
}
_COORDINATE_SYSTEM = dict(CANONICAL_COORDINATE_SYSTEM)
_IDENTITY: Mat4 = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)
_GLB_CONTAINER_ERRORS = (
    AttributeError,
    IndexError,
    KeyError,
    TypeError,
    ValueError,
    OverflowError,
    struct.error,
    ValidationFailure,
)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


def _parse_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number {value} is not finite")
    return parsed


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
            parse_float=_parse_json_float,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contact/gauge JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"contact/gauge JSON root must be an object: {path}")
    ensure_finite(value, label=str(path))
    return value


def _resolve_repository_path(candidate: Path, root: Path, *, label: str) -> Path:
    """Resolve an admission path and reject symlink escapes from the repository."""

    try:
        resolved = Path(candidate).resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ContractError(f"{label} path must be inside the repository") from exc
    return resolved


def _keys(value: Mapping[str, Any], expected: set[str], *, label: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        raise ContractError(f"{label}: missing fields {missing}")
    if unknown:
        raise ContractError(f"{label}: unknown fields {unknown}")


def _number(value: Any, *, label: str, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be a finite number")
    if minimum is not None and result < minimum:
        raise ContractError(f"{label} must be >= {minimum}")
    return result


def _vec3(value: Any, *, label: str) -> Vec3:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ContractError(f"{label} must contain exactly three numbers")
    return tuple(_number(item, label=f"{label}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]


def _add(left: Vec3, right: Vec3) -> Vec3:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _sub(left: Vec3, right: Vec3) -> Vec3:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _scale(value: Vec3, factor: float) -> Vec3:
    return tuple(item * factor for item in value)  # type: ignore[return-value]


def _dot(left: Vec3, right: Vec3) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(left: Vec3, right: Vec3) -> Vec3:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _norm(value: Vec3) -> float:
    return math.sqrt(_dot(value, value))


def _unit(value: Vec3, *, label: str, epsilon: float = 1.0e-12) -> Vec3:
    length = _norm(value)
    if not math.isfinite(length) or length <= epsilon:
        raise ContractError(f"{label} is zero or non-finite")
    return _scale(value, 1.0 / length)


def _project_ground(value: Vec3, up: Vec3) -> Vec3:
    return _sub(value, _scale(up, _dot(value, up)))


def _median(values: Sequence[float]) -> float:
    if not values:
        raise ContractError("cannot summarize an empty measurement")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ContractError("cannot summarize an empty measurement")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _stats(values: Sequence[float], *, unit: str) -> dict[str, Any]:
    if not values:
        raise ContractError("measurement has no valid samples")
    finite = [_number(value, label="measurement") for value in values]
    return {
        "count": len(finite),
        "unit": unit,
        "min": min(finite),
        "q05": _quantile(finite, 0.05),
        "median": _median(finite),
        "q95": _quantile(finite, 0.95),
        "max": max(finite),
    }


def _stats_or_unevaluated(
    values: Sequence[float],
    *,
    unit: str,
    reason: str,
) -> dict[str, Any] | None:
    return _stats(values, unit=unit) if values else None


def _point(value: Any, *, label: str) -> Vec3:
    if isinstance(value, Mapping):
        if set(value) != {"point_m", "weight"}:
            raise ContractError(f"{label}: point must contain point_m and weight")
        coordinate = _vec3(value["point_m"], label=f"{label}.point_m")
        weight = _number(value["weight"], label=f"{label}.weight", minimum=0.0)
        if weight <= 0.0:
            raise ContractError(f"{label}.weight must be > 0")
        return coordinate, weight  # type: ignore[return-value]
    raise ContractError(f"{label}: point must be an object")


def _weighted_centroid(points: Sequence[tuple[Vec3, float]], *, label: str) -> Vec3:
    if not points:
        raise ContractError(f"{label}: no points")
    total = math.fsum(weight for _, weight in points)
    if total <= 0.0 or not math.isfinite(total):
        raise ContractError(f"{label}: invalid point weights")
    return tuple(
        math.fsum(point[index] * weight for point, weight in points) / total
        for index in range(3)
    )  # type: ignore[return-value]


@dataclass(frozen=True)
class _FootFrame:
    side: str
    axis_origin_m: Vec3
    sole_points: tuple[tuple[Vec3, float], ...]
    toe_points: tuple[tuple[Vec3, float], ...]

    @property
    def all_points(self) -> tuple[tuple[Vec3, float], ...]:
        return self.sole_points + self.toe_points


@dataclass(frozen=True)
class _Frame:
    time_s: float
    root_m: Vec3
    hip_left_m: Vec3
    hip_right_m: Vec3
    feet: Mapping[str, _FootFrame]

    @property
    def hip_center_m(self) -> Vec3:
        return _scale(_add(self.hip_left_m, self.hip_right_m), 0.5)


@dataclass(frozen=True)
class ContactGaugeResult:
    """Immutable result carrying the report and its canonical hash."""

    report: dict[str, Any]
    report_sha256: str

    def write(self, path: Path) -> None:
        write_json(path, self.report)


def _validate_policy_common(policy: Mapping[str, Any]) -> None:
    """Validate facts shared by the immutable V1 and additive V2 policies."""

    if policy["scientificClaim"] is not False or policy["speciesHardcode"] is not False:
        raise ContractError("narrow-gauge policy must remain non-scientific and species-neutral")

    normalization = policy["normalization"]
    if not isinstance(normalization, Mapping):
        raise ContractError("narrow-gauge policy normalization must be an object")
    required_normalization = {"hipHeightH", "localGroundFrame", "contactCentroids"}
    if not required_normalization.issubset(normalization):
        raise ContractError("narrow-gauge policy normalization is incomplete")
    hip_height = normalization["hipHeightH"]
    if not isinstance(hip_height, Mapping) or hip_height.get("unit") != "metres":
        raise ContractError("hip-height policy must declare metres")
    local_frame = normalization["localGroundFrame"]
    if not isinstance(local_frame, Mapping):
        raise ContractError("local ground frame policy must be an object")
    if "measured" not in str(local_frame.get("travelTangentT", "")):
        raise ContractError("travel tangent policy must be measured")
    if "cross(up" not in str(local_frame.get("lateralL", "")):
        raise ContractError("lateral axis policy must derive from up and travel")
    centroids = normalization["contactCentroids"]
    if not isinstance(centroids, Mapping):
        raise ContractError("contact centroid policy must be an object")
    requirements = set(centroids.get("maskRequirements", []))
    required_requirements = {
        "record vertex IDs and weight threshold",
        "record floor-gap tolerance",
        "record contact velocity threshold",
    }
    if not required_requirements.issubset(requirements):
        raise ContractError("contact centroid policy does not require deterministic masks and thresholds")

    metrics = policy["metrics"]
    if not isinstance(metrics, Mapping):
        raise ContractError("narrow-gauge policy metrics must be an object")
    for metric in (
        "stanceSupportWidthNormalized",
        "stepWidthNormalized",
        "footHeadingPsi",
        "contactQuality",
    ):
        if metric not in metrics:
            raise ContractError(f"narrow-gauge policy is missing {metric}")
    gates = policy["acceptanceGates"]
    if not isinstance(gates, Mapping) or not isinstance(gates.get("sampling"), Mapping):
        raise ContractError("narrow-gauge policy sampling gate is missing")
    sampling = gates["sampling"]
    if sampling.get("quantilesRequired") != [0.05, 0.5, 0.95] or sampling.get("allMetricsFinite") is not True:
        raise ContractError("narrow-gauge policy quantiles or finite-number gate is not canonical")
    gait_states = policy["gaitStates"]
    if not isinstance(gait_states, Mapping) or "straight_walk" not in gait_states:
        raise ContractError("narrow-gauge policy must include straight_walk")


def _validate_policy_v2(policy: Mapping[str, Any]) -> None:
    """Require planner inputs and observed metrics to remain disjoint."""

    predecessor = policy["predecessor"]
    if not isinstance(predecessor, Mapping):
        raise ContractError("V2 narrow-gauge predecessor must be an object")
    _keys(predecessor, {"path", "sha256", "schema"}, label="V2 narrow-gauge predecessor")
    if predecessor["schema"] != POLICY_SCHEMA:
        raise ContractError("V2 narrow-gauge predecessor must identify the V1 policy")
    if not isinstance(predecessor["path"], str) or not predecessor["path"]:
        raise ContractError("V2 narrow-gauge predecessor path is required")
    predecessor_sha = predecessor["sha256"]
    if not isinstance(predecessor_sha, str) or len(predecessor_sha) != 64:
        raise ContractError("V2 narrow-gauge predecessor SHA-256 is malformed")
    try:
        int(predecessor_sha, 16)
    except ValueError as exc:
        raise ContractError("V2 narrow-gauge predecessor SHA-256 is malformed") from exc

    semantics = policy["metricSemantics"]
    if not isinstance(semantics, Mapping):
        raise ContractError("V2 narrow-gauge metricSemantics must be an object")
    required_semantics = {
        "targetLaneCenterSeparationNormalized": "planner_input",
        "stanceSupportWidthNormalized": "measured_simultaneous_support",
        "stepWidthNormalized": "measured_successive_contralateral_footfalls",
    }
    _keys(semantics, set(required_semantics), label="V2 narrow-gauge metricSemantics")
    observed_kinds: set[str] = set()
    for name, expected_kind in required_semantics.items():
        value = semantics[name]
        if not isinstance(value, Mapping):
            raise ContractError(f"V2 narrow-gauge semantic {name} must be an object")
        _keys(
            value,
            {"kind", "normalizer", "definition", "admissionRole"},
            label=f"V2 narrow-gauge semantic {name}",
        )
        if value["kind"] != expected_kind or value["normalizer"] != "H":
            raise ContractError(f"V2 narrow-gauge semantic {name} has the wrong kind or normalizer")
        if not isinstance(value["definition"], str) or not value["definition"].strip():
            raise ContractError(f"V2 narrow-gauge semantic {name} requires a definition")
        if name == "targetLaneCenterSeparationNormalized":
            if value["admissionRole"] != "planner_domain_only_not_observed_metric":
                raise ContractError("V2 planner semantic must be admitted only as a planner domain")
        else:
            if value["admissionRole"] != "measured_output_only_not_planner_domain":
                raise ContractError(f"V2 observed semantic {name} must not admit planner targets")
            observed_kinds.add(str(value["kind"]))
    if len(observed_kinds) != 2:
        raise ContractError("V2 stance-support and step-width semantics must remain distinct")

    planner_targets = policy["plannerTargets"]
    if not isinstance(planner_targets, Mapping) or set(planner_targets) != {"straight_walk"}:
        raise ContractError("V2 narrow-gauge plannerTargets must define straight_walk only")
    straight = planner_targets["straight_walk"]
    if not isinstance(straight, Mapping):
        raise ContractError("V2 straight-walk planner target must be an object")
    _keys(
        straight,
        {
            "semantic",
            "targetLaneCenterSeparationHHardEnvelope",
            "profileOwnsCandidateDomain",
            "classification",
            "observedMetricGateSeparationRequired",
        },
        label="V2 straight-walk planner target",
    )
    if straight["semantic"] != "targetLaneCenterSeparationNormalized":
        raise ContractError("V2 planner target must use targetLaneCenterSeparationNormalized")
    envelope = straight["targetLaneCenterSeparationHHardEnvelope"]
    if not isinstance(envelope, list) or len(envelope) != 2:
        raise ContractError("V2 planner target hard envelope must contain two values")
    lower = _number(envelope[0], label="V2 planner target hard-envelope lower", minimum=0.0)
    upper = _number(envelope[1], label="V2 planner target hard-envelope upper", minimum=0.0)
    if upper <= lower:
        raise ContractError("V2 planner target hard envelope must be increasing")
    if straight["profileOwnsCandidateDomain"] is not True:
        raise ContractError("V2 planner candidate domain must remain profile-owned")
    if straight["observedMetricGateSeparationRequired"] is not True:
        raise ContractError("V2 planner admission must remain separate from observed metrics")
    if straight["classification"] not in {
        "engineering_calibration",
        "art_direction_calibration",
    }:
        raise ContractError("V2 planner target must be labeled engineering or art-direction calibration")

    calibration = policy["calibrationEvidence"]
    if not isinstance(calibration, Mapping):
        raise ContractError("V2 calibrationEvidence must be an object")
    _keys(
        calibration,
        {
            "sourcePath",
            "sourceSha256",
            "plannerInputTargetLaneCenterSeparationH",
            "observedStanceSupportWidthHApproxRange",
            "observedStepWidthHApproxRange",
            "classification",
            "scientificClaim",
        },
        label="V2 calibrationEvidence",
    )
    if calibration["scientificClaim"] is not False:
        raise ContractError("V2 calibration evidence must remain non-scientific")
    if calibration["classification"] not in {
        "engineering_measurement",
        "art_direction_measurement",
    }:
        raise ContractError("V2 calibration evidence must retain an engineering or art-direction label")
    _number(
        calibration["plannerInputTargetLaneCenterSeparationH"],
        label="V2 calibration planner input",
        minimum=0.0,
    )
    for key in (
        "observedStanceSupportWidthHApproxRange",
        "observedStepWidthHApproxRange",
    ):
        observed = calibration[key]
        if not isinstance(observed, list) or len(observed) != 2:
            raise ContractError(f"V2 calibration {key} must contain two values")
        observed_lower = _number(observed[0], label=f"V2 calibration {key} lower", minimum=0.0)
        observed_upper = _number(observed[1], label=f"V2 calibration {key} upper", minimum=0.0)
        if observed_upper < observed_lower:
            raise ContractError(f"V2 calibration {key} must be ordered")


def _validate_policy_v3(policy: Mapping[str, Any]) -> None:
    """Validate the additive planner-envelope extension without gate drift."""

    predecessor = policy["predecessor"]
    if not isinstance(predecessor, Mapping):
        raise ContractError("V3 narrow-gauge predecessor must be an object")
    _keys(predecessor, {"path", "sha256", "schema"}, label="V3 narrow-gauge predecessor")
    if predecessor.get("schema") != POLICY_SCHEMA_V2:
        raise ContractError("V3 narrow-gauge predecessor must identify the V2 policy")
    if not isinstance(predecessor.get("path"), str) or not predecessor["path"]:
        raise ContractError("V3 narrow-gauge predecessor path is required")
    predecessor_sha = predecessor.get("sha256")
    if not isinstance(predecessor_sha, str) or len(predecessor_sha) != 64:
        raise ContractError("V3 narrow-gauge predecessor SHA-256 is malformed")
    try:
        int(predecessor_sha, 16)
    except ValueError as exc:
        raise ContractError("V3 narrow-gauge predecessor SHA-256 is malformed") from exc

    # Reuse the mature V2 semantic/planner/calibration validation while
    # validating V3's own predecessor separately above.
    v2_shape = {key: policy[key] for key in _POLICY_V2_KEYS}
    v2_shape["predecessor"] = {
        "path": "immutable-v1-placeholder.json",
        "sha256": "0" * 64,
        "schema": POLICY_SCHEMA,
    }
    _validate_policy_v2(v2_shape)

    planner = policy["plannerTargets"]["straight_walk"]
    if planner["targetLaneCenterSeparationHHardEnvelope"] != [0.0, 0.36]:
        raise ContractError("V3 planner hard envelope must be exactly 0.0..0.36 H")
    extension = policy["laneExtensionEvidence"]
    if not isinstance(extension, Mapping):
        raise ContractError("V3 lane-extension evidence must be an object")
    _keys(
        extension,
        {"sourcePath", "sourceSha256", "classification", "scientificClaim", "fitDisposition"},
        label="V3 lane-extension evidence",
    )
    if extension["scientificClaim"] is not False:
        raise ContractError("V3 lane-extension evidence must remain non-scientific")
    if extension["classification"] != "engineering_fit_evidence":
        raise ContractError("V3 lane-extension evidence classification is unsupported")
    if extension["fitDisposition"] != "planner_extension_only_not_candidate_acceptance":
        raise ContractError("V3 lane-extension fit may not imply candidate acceptance")
    recommendation = policy["plannerRecommendation"]
    if recommendation != {
        "gaitState": "straight_walk",
        "targetLaneCenterSeparationH": 0.35,
        "automaticSelection": False,
        "classification": "engineering_art_direction_recommendation",
    }:
        raise ContractError("V3 planner recommendation must be 0.35 H with no auto-selection")


def _validate_narrow_gauge_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate immutable V1 or additive V2/V3 semantics without coercion."""

    if not isinstance(policy, Mapping):
        raise ContractError("narrow-gauge policy must be an object")
    schema = policy.get("schema")
    if schema == POLICY_SCHEMA:
        _keys(policy, _POLICY_KEYS, label="narrow-gauge policy")
        if policy["status"] != "PROVISIONAL_ENGINEERING_CONTRACT":
            raise ContractError("V1 narrow-gauge policy must remain provisional")
    elif schema == POLICY_SCHEMA_V2:
        _keys(policy, _POLICY_V2_KEYS, label="narrow-gauge policy")
        if policy["status"] != "PROVISIONAL_ENGINEERING_CALIBRATION_POLICY":
            raise ContractError("V2 narrow-gauge policy must remain provisional calibration")
    elif schema == POLICY_SCHEMA_V3:
        _keys(policy, _POLICY_V3_KEYS, label="narrow-gauge policy")
        if policy["status"] != "PROVISIONAL_ENGINEERING_CALIBRATION_POLICY":
            raise ContractError("V3 narrow-gauge policy must remain provisional calibration")
    else:
        raise ContractError("narrow-gauge policy schema is not an accepted version")
    _validate_policy_common(policy)
    if schema == POLICY_SCHEMA_V2:
        _validate_policy_v2(policy)
    elif schema == POLICY_SCHEMA_V3:
        _validate_policy_v3(policy)
    return dict(policy)


def load_narrow_gauge_policy(path: Path) -> dict[str, Any]:
    """Load an accepted policy and verify additive predecessor bindings."""

    resolved = Path(path).resolve(strict=False)
    policy = _validate_narrow_gauge_policy(_read_json(resolved))
    if policy["schema"] == POLICY_SCHEMA_V2:
        predecessor = policy["predecessor"]
        repository = Path(__file__).resolve().parents[2]
        predecessor_path = _resolve_repository_path(
            repository / predecessor["path"],
            repository,
            label="V2 narrow-gauge predecessor",
        )
        if (
            not predecessor_path.is_file()
            or sha256_file(predecessor_path) != predecessor["sha256"]
        ):
            raise ContractError("V2 narrow-gauge predecessor is missing or hash-mismatched")
        predecessor_policy = _validate_narrow_gauge_policy(_read_json(predecessor_path))
        if predecessor_policy["schema"] != POLICY_SCHEMA:
            raise ContractError("V2 narrow-gauge predecessor is not the immutable V1 policy")
        calibration = policy["calibrationEvidence"]
        calibration_path = _resolve_repository_path(
            repository / calibration["sourcePath"],
            repository,
            label="V2 narrow-gauge calibration evidence",
        )
        calibration_sha = calibration["sourceSha256"]
        if (
            not isinstance(calibration_sha, str)
            or len(calibration_sha) != 64
            or not calibration_path.is_file()
            or sha256_file(calibration_path) != calibration_sha
        ):
            raise ContractError("V2 narrow-gauge calibration evidence is missing or hash-mismatched")
    elif policy["schema"] == POLICY_SCHEMA_V3:
        predecessor = policy["predecessor"]
        repository = Path(__file__).resolve().parents[2]
        predecessor_path = _resolve_repository_path(
            repository / predecessor["path"],
            repository,
            label="V3 narrow-gauge predecessor",
        )
        if (
            not predecessor_path.is_file()
            or sha256_file(predecessor_path) != predecessor["sha256"]
        ):
            raise ContractError("V3 narrow-gauge predecessor is missing or hash-mismatched")
        predecessor_policy = load_narrow_gauge_policy(predecessor_path)
        if predecessor_policy["schema"] != POLICY_SCHEMA_V2:
            raise ContractError("V3 narrow-gauge predecessor is not the immutable V2 policy")
        unchanged_fields = (
            "status",
            "scientificClaim",
            "speciesHardcode",
            "purpose",
            "evidenceBoundary",
            "normalization",
            "metrics",
            "familyCalibration",
            "gaitStates",
            "acceptanceGates",
            "primarySources",
            "recommendedEvidence",
            "metricSemantics",
            "calibrationEvidence",
        )
        drift = [
            field for field in unchanged_fields
            if policy[field] != predecessor_policy[field]
        ]
        if drift:
            raise ContractError(
                f"V3 narrow-gauge policy changed predecessor semantics/gates: {drift}"
            )
        predecessor_planner = predecessor_policy["plannerTargets"]["straight_walk"]
        current_planner = policy["plannerTargets"]["straight_walk"]
        if {
            key: value for key, value in current_planner.items()
            if key != "targetLaneCenterSeparationHHardEnvelope"
        } != {
            key: value for key, value in predecessor_planner.items()
            if key != "targetLaneCenterSeparationHHardEnvelope"
        }:
            raise ContractError("V3 planner extension changed non-envelope semantics")
        extension = policy["laneExtensionEvidence"]
        evidence_path = _resolve_repository_path(
            repository / extension["sourcePath"],
            repository,
            label="V3 lane-extension evidence",
        )
        evidence_sha = extension["sourceSha256"]
        if (
            not isinstance(evidence_sha, str)
            or len(evidence_sha) != 64
            or not evidence_path.is_file()
            or sha256_file(evidence_path) != evidence_sha
        ):
            raise ContractError("V3 lane-extension evidence is missing or hash-mismatched")
    return policy


def load_contact_gauge_source(path: Path) -> dict[str, Any]:
    """Load a strict source-binding profile; names remain data, not code."""

    source = _read_json(path)
    _keys(source, _SOURCE_KEYS, label="contact/gauge source profile")
    if source["schema"] != SOURCE_SCHEMA:
        raise ContractError("contact/gauge source profile schema is unsupported")
    if source["coordinate_system"] != _COORDINATE_SYSTEM:
        raise ContractError("contact/gauge source profile coordinate system is not canonical")

    source_binding = source["source"]
    if not isinstance(source_binding, Mapping):
        raise ContractError("contact/gauge source binding must be an object")
    _keys(source_binding, {"path", "sha256", "clips"}, label="source binding")
    if not isinstance(source_binding["path"], str) or not isinstance(source_binding["sha256"], str):
        raise ContractError("source binding path and sha256 must be strings")
    clips = source_binding["clips"]
    if not isinstance(clips, Mapping) or set(clips) != {"root_motion", "in_place"}:
        raise ContractError("source binding must name root_motion and in_place clips")
    if any(not isinstance(value, str) or not value for value in clips.values()):
        raise ContractError("source clip names must be non-empty strings")

    geometry = source["geometry"]
    if not isinstance(geometry, Mapping):
        raise ContractError("source geometry must be an object")
    _keys(
        geometry,
        {
            "mesh_node",
            "position_accessor",
            "joint_accessors",
            "weight_accessors",
            "skin_index",
            "landmarks",
            "feet",
            "ground",
        },
        label="source geometry",
    )
    for key in ("mesh_node",):
        if not isinstance(geometry[key], str) or not geometry[key]:
            raise ContractError(f"source geometry {key} must be a non-empty string")
    for key in ("position_accessor", "skin_index"):
        if not isinstance(geometry[key], int) or isinstance(geometry[key], bool) or geometry[key] < 0:
            raise ContractError(f"source geometry {key} must be a non-negative integer")
    for key in ("joint_accessors", "weight_accessors"):
        value = geometry[key]
        if (
            not isinstance(value, list)
            or len(value) != 3
            or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in value)
        ):
            raise ContractError(f"source geometry {key} must contain three accessor indices")

    landmarks = geometry["landmarks"]
    if not isinstance(landmarks, Mapping):
        raise ContractError("source landmarks must be an object")
    _keys(
        landmarks,
        {"root_node", "hip_left_node", "hip_right_node", "foot_roots"},
        label="source landmarks",
    )
    for key in ("root_node", "hip_left_node", "hip_right_node"):
        if not isinstance(landmarks[key], str) or not landmarks[key]:
            raise ContractError(f"source landmark {key} must be a non-empty string")
    foot_roots = landmarks["foot_roots"]
    if not isinstance(foot_roots, Mapping) or set(foot_roots) != {"left", "right"}:
        raise ContractError("source landmarks must provide left and right foot roots")
    if any(not isinstance(value, str) or not value for value in foot_roots.values()):
        raise ContractError("source foot root names must be non-empty strings")

    feet = geometry["feet"]
    if not isinstance(feet, Mapping) or set(feet) != {"left", "right"}:
        raise ContractError("source geometry must provide exactly left and right masks")
    for side, mask in feet.items():
        if not isinstance(mask, Mapping):
            raise ContractError(f"source {side} mask must be an object")
        _keys(mask, {"side", "sole_joints", "toe_joints", "weight_threshold"}, label=f"source {side} mask")
        if mask["side"] != side:
            raise ContractError(f"source {side} mask has a mismatched side identity")
        for key in ("sole_joints", "toe_joints"):
            if (
                not isinstance(mask[key], list)
                or not mask[key]
                or any(not isinstance(item, str) or not item for item in mask[key])
                or len(mask[key]) != len(set(mask[key]))
            ):
                raise ContractError(f"source {side} {key} must contain unique names")
        _number(mask["weight_threshold"], label=f"source {side} weight_threshold", minimum=0.0)
        if float(mask["weight_threshold"]) > 1.0:
            raise ContractError(f"source {side} weight_threshold must be <= 1")

    ground = geometry["ground"]
    if not isinstance(ground, Mapping):
        raise ContractError("source ground must be an object")
    _keys(ground, {"up_axis", "level_m"}, label="source ground")
    if ground["up_axis"] != "Y":
        raise ContractError("source ground must declare canonical Y up")
    _number(ground["level_m"], label="source ground level_m")

    sampling = source["sampling"]
    if not isinstance(sampling, Mapping):
        raise ContractError("source sampling must be an object")
    _keys(sampling, {"mode", "count"}, label="source sampling")
    if sampling["mode"] != "uniform_time" or not isinstance(sampling["count"], int) or sampling["count"] < 2:
        raise ContractError("source sampling must request at least two uniform_time samples")

    thresholds = source["thresholds"]
    if not isinstance(thresholds, Mapping):
        raise ContractError("source thresholds must be an object")
    _keys(
        thresholds,
        {
            "floor_gap_tolerance_m",
            "contact_relative_velocity_mps",
            "toe_off_gap_m",
            "minimum_active_points",
            "travel_epsilon_mps",
            "crossover_epsilon_m",
        },
        label="source thresholds",
    )
    for key in (
        "floor_gap_tolerance_m",
        "contact_relative_velocity_mps",
        "toe_off_gap_m",
        "travel_epsilon_mps",
        "crossover_epsilon_m",
    ):
        _number(thresholds[key], label=f"source thresholds.{key}", minimum=0.0)
    if not isinstance(thresholds["minimum_active_points"], int) or thresholds["minimum_active_points"] < 1:
        raise ContractError("source thresholds.minimum_active_points must be a positive integer")
    return source


def _coerce_frames(frames: Sequence[Mapping[str, Any]]) -> tuple[_Frame, ...]:
    if not isinstance(frames, Sequence) or isinstance(frames, (str, bytes)) or len(frames) < 2:
        raise ContractError("contact/gauge analysis requires at least two frames")
    output: list[_Frame] = []
    previous_time = -math.inf
    for frame_index, value in enumerate(frames):
        if not isinstance(value, Mapping):
            raise ContractError(f"frame {frame_index} must be an object")
        required = {"time_s", "root_m", "hip_left_m", "hip_right_m", "feet"}
        missing = required - set(value)
        unknown = set(value) - required
        if missing or unknown:
            raise ContractError(f"frame {frame_index}: missing {sorted(missing)}, unknown {sorted(unknown)}")
        time_s = _number(value["time_s"], label=f"frame {frame_index}.time_s", minimum=0.0)
        if time_s <= previous_time:
            raise ContractError("frame times must be strictly increasing")
        previous_time = time_s
        feet = value["feet"]
        if not isinstance(feet, Mapping) or set(feet) != {"left", "right"}:
            raise ContractError("each frame must contain exactly left and right feet")
        parsed_feet: dict[str, _FootFrame] = {}
        for side in ("left", "right"):
            foot = feet[side]
            if not isinstance(foot, Mapping):
                raise ContractError(f"frame {frame_index} {side} foot must be an object")
            required_foot = {"axis_origin_m", "sole_points", "toe_points"}
            missing_foot = required_foot - set(foot)
            unknown_foot = set(foot) - required_foot
            if missing_foot or unknown_foot:
                raise ContractError(f"frame {frame_index} {side}: missing {sorted(missing_foot)}, unknown {sorted(unknown_foot)}")
            sole = foot["sole_points"]
            toe = foot["toe_points"]
            if not isinstance(sole, list) or not sole or not isinstance(toe, list) or not toe:
                raise ContractError(f"frame {frame_index} {side}: sole and toe masks must be non-empty")
            parsed_feet[side] = _FootFrame(
                side=side,
                axis_origin_m=_vec3(foot["axis_origin_m"], label=f"frame {frame_index}.{side}.axis_origin_m"),
                sole_points=tuple(_point(item, label=f"frame {frame_index}.{side}.sole_points[{index}]") for index, item in enumerate(sole)),
                toe_points=tuple(_point(item, label=f"frame {frame_index}.{side}.toe_points[{index}]") for index, item in enumerate(toe)),
            )
        output.append(
            _Frame(
                time_s=time_s,
                root_m=_vec3(value["root_m"], label=f"frame {frame_index}.root_m"),
                hip_left_m=_vec3(value["hip_left_m"], label=f"frame {frame_index}.hip_left_m"),
                hip_right_m=_vec3(value["hip_right_m"], label=f"frame {frame_index}.hip_right_m"),
                feet=parsed_feet,
            )
        )
    return tuple(output)


def _validate_thresholds(thresholds: Mapping[str, Any]) -> dict[str, float | int]:
    expected = {
        "floor_gap_tolerance_m",
        "contact_relative_velocity_mps",
        "toe_off_gap_m",
        "minimum_active_points",
        "travel_epsilon_mps",
        "crossover_epsilon_m",
    }
    _keys(thresholds, expected, label="analysis thresholds")
    result: dict[str, float | int] = {}
    for key in expected - {"minimum_active_points"}:
        result[key] = _number(thresholds[key], label=f"analysis thresholds.{key}", minimum=0.0)
    points = thresholds["minimum_active_points"]
    if not isinstance(points, int) or isinstance(points, bool) or points < 1:
        raise ContractError("analysis thresholds.minimum_active_points must be a positive integer")
    result["minimum_active_points"] = points
    if float(result["toe_off_gap_m"]) < float(result["floor_gap_tolerance_m"]):
        raise ContractError("toe_off_gap_m cannot be smaller than floor_gap_tolerance_m")
    return result


def _derive_travel_frame(
    frames: Sequence[_Frame],
    *,
    up: Vec3,
    travel_epsilon_mps: float,
) -> tuple[Vec3, Vec3, float]:
    elapsed = frames[-1].time_s - frames[0].time_s
    displacement = _project_ground(_sub(frames[-1].root_m, frames[0].root_m), up)
    average_velocity = _scale(displacement, 1.0 / elapsed)
    speed = _norm(average_velocity)
    if not math.isfinite(speed) or speed <= travel_epsilon_mps:
        raise ContractError("measured travel is zero; a tangent cannot be inferred")
    travel = _unit(average_velocity, label="measured travel tangent")

    return travel, _derive_anatomical_lateral(frames, up=up, travel=travel), speed


def _derive_anatomical_lateral(
    frames: Sequence[_Frame],
    *,
    up: Vec3,
    travel: Vec3,
) -> Vec3:
    """Derive the signed lateral axis from hip geometry for one clip."""

    # A hip-left minus hip-right vector supplies the anatomical sign.  Project
    # it onto the ground plane and remove any travel component before
    # aggregating over the whole window; foot positions are deliberately not
    # used, because an initially crossed stance must not redefine left/right.
    anatomical_lateral_samples: list[Vec3] = []
    for frame in frames:
        hip_delta = _project_ground(_sub(frame.hip_left_m, frame.hip_right_m), up)
        orthogonal = _project_ground(_sub(hip_delta, _scale(travel, _dot(hip_delta, travel))), up)
        if _norm(orthogonal) > 1.0e-12:
            anatomical_lateral_samples.append(_unit(orthogonal, label="anatomical lateral sample"))
    if not anatomical_lateral_samples:
        raise ContractError("anatomical hip lateral geometry is zero")
    anatomical_lateral = _unit(
        tuple(
            math.fsum(sample[index] for sample in anatomical_lateral_samples)
            for index in range(3)
        ),
        label="anatomical lateral axis",
    )  # type: ignore[arg-type]
    # The aggregate is already orthogonal to travel/up; re-project once to
    # keep the emitted basis numerically orthonormal after finite precision.
    lateral = _unit(
        _project_ground(_sub(anatomical_lateral, _scale(travel, _dot(anatomical_lateral, travel))), up),
        label="anatomical lateral axis",
    )
    return lateral


def _orient_anatomical_lateral(
    frames: Sequence[_Frame],
    *,
    up: Vec3,
    travel: Vec3,
    orientation_basis: Sequence[float] | None = None,
) -> tuple[Vec3, str]:
    """Derive hip geometry and stabilize only its sign when hash-bound.

    A whole-leg retarget can move the named hip landmarks across the
    midline.  Re-normalizing that reflected vector would silently swap the
    meaning of the profile's left/right roles and make a valid narrow track
    look like crossover.  The direction still comes from the current clip's
    named hip geometry; an admitted source basis only fixes the handed sign
    for comparisons across an animation patch.
    """

    derived = _derive_anatomical_lateral(frames, up=up, travel=travel)
    if orientation_basis is None:
        return derived, "clip-specific named hip left-right geometry"
    reference = _unit(
        _project_ground(_vec3(orientation_basis, label="anatomical lateral orientation basis"), up),
        label="anatomical lateral orientation basis",
    )
    if _dot(derived, reference) < 0.0:
        derived = _scale(derived, -1.0)
    return derived, "clip-specific named hip geometry, sign-stabilized to hash-bound baseline basis"


def _finite_difference(points: Sequence[Vec3], times: Sequence[float], *, label: str) -> tuple[Vec3, ...]:
    """Return forward/centered/backward velocities on an irregular timeline."""

    if len(points) != len(times) or len(points) < 2:
        raise ContractError(f"{label} requires at least two aligned samples")
    velocities: list[Vec3] = []
    last_index = len(points) - 1
    for index in range(len(points)):
        if index == 0:
            left, right = 0, 1
        elif index == last_index:
            left, right = last_index - 1, last_index
        else:
            left, right = index - 1, index + 1
        delta_time = times[right] - times[left]
        if delta_time <= 0.0:
            raise ContractError(f"{label} timestamps must be strictly increasing")
        velocities.append(_scale(_sub(points[right], points[left]), 1.0 / delta_time))
    return tuple(velocities)


def _uniform_times(start: float, end: float, count: int, *, label: str) -> tuple[float, ...]:
    start_time = _number(start, label=f"{label} start")
    end_time = _number(end, label=f"{label} end")
    if count < 2 or end_time <= start_time:
        raise ContractError(f"{label} must have at least two increasing bounds")
    duration = end_time - start_time
    return tuple(start_time + duration * index / (count - 1) for index in range(count))


_TOUCHDOWN_TIME_EPSILON_S = 1.0e-12


def _successive_contralateral_touchdown_pairs(
    events: Sequence[tuple[float, str, Vec3]],
) -> tuple[tuple[tuple[float, str, Vec3], tuple[float, str, Vec3]], ...]:
    """Pair only adjacent, alternating touchdown events with elapsed time.

    Events are supplied in chronological frame/side order.  A bilateral onset
    at one timestamp has no temporal ordering and therefore cannot form a
    step-width pair; the strict positive epsilon also rejects timestamps that
    only differ by floating-point noise.  Keeping the previous event for each
    adjacent comparison preserves the observed alternation/order instead of
    pairing arbitrary events by side.
    """

    pairs: list[tuple[tuple[float, str, Vec3], tuple[float, str, Vec3]]] = []
    previous: tuple[float, str, Vec3] | None = None
    for current in events:
        if previous is not None:
            elapsed = current[0] - previous[0]
            if elapsed > _TOUCHDOWN_TIME_EPSILON_S and current[1] != previous[1]:
                pairs.append((previous, current))
        previous = current
    return tuple(pairs)


def _normalize_skin_weights(
    joint_accessors: Sequence[Sequence[Sequence[Any]]],
    weight_accessors: Sequence[Sequence[Sequence[Any]]],
    *,
    vertex_count: int,
    joint_count: int,
) -> tuple[tuple[tuple[int, float], ...], ...]:
    """Validate and normalize all combined skin influences before evaluation."""

    if len(joint_accessors) != len(weight_accessors):
        raise ContractError("source joint and weight accessor counts differ")
    influences: list[tuple[tuple[int, float], ...]] = []
    for vertex_index in range(vertex_count):
        rows: list[tuple[int, float]] = []
        for joint_accessor, weight_accessor in zip(joint_accessors, weight_accessors):
            if len(joint_accessor) != vertex_count or len(weight_accessor) != vertex_count:
                raise ContractError("source skin accessor row count is invalid")
            joint_row = joint_accessor[vertex_index]
            weight_row = weight_accessor[vertex_index]
            if not isinstance(joint_row, (list, tuple)) or not isinstance(weight_row, (list, tuple)):
                raise ContractError("source joint and weight rows must be arrays")
            if len(joint_row) != len(weight_row):
                raise ContractError("source joint and weight row widths differ")
            for joint_slot, weight in zip(joint_row, weight_row):
                if (
                    isinstance(joint_slot, bool)
                    or not isinstance(joint_slot, int)
                    or joint_slot < 0
                    or joint_slot >= joint_count
                ):
                    raise ContractError("source vertex references an invalid skin joint")
                numeric_weight = _number(weight, label="source vertex weight", minimum=0.0)
                if numeric_weight > 0.0:
                    rows.append((joint_slot, numeric_weight))
        if not rows:
            raise ContractError("source vertex has no positive combined skin weight")
        total_weight = math.fsum(weight for _, weight in rows)
        if not math.isfinite(total_weight) or total_weight <= 0.0:
            raise ContractError("source vertex has an invalid combined skin weight")
        normalized_rows = tuple(
            (joint_slot, weight / total_weight) for joint_slot, weight in rows
        )
        normalized_sum = math.fsum(weight for _, weight in normalized_rows)
        if not math.isfinite(normalized_sum) or normalized_sum <= 0.0:
            raise ContractError("source vertex skin-weight normalization is non-finite")
        influences.append(normalized_rows)
    return tuple(influences)


def _window_payload(states: Sequence[bool], times: Sequence[float], *, target: bool) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    start: int | None = None
    for index, state in enumerate(states + (False,)):
        if state == target and start is None:
            start = index
        elif state != target and start is not None:
            end = index - 1
            windows.append(
                {
                    "start_frame": start,
                    "end_frame": end,
                    "start_time_s": times[start],
                    "end_time_s": times[end],
                    "duration_s": times[end] - times[start],
                }
            )
            start = None
    return windows


def _toe_off_payload(states: Sequence[bool], times: Sequence[float]) -> list[dict[str, Any]]:
    return [
        {
            "event": "toe_off",
            "frame": index,
            "time_s": times[index],
        }
        for index, (previous, current) in enumerate(zip(states, states[1:]), start=1)
        if previous and not current
    ]


def _planted_window_metrics(
    states: Sequence[bool],
    times: Sequence[float],
    *,
    contact_centroids: Sequence[Vec3 | None],
    sole_centroids: Sequence[Vec3],
    toe_centroids: Sequence[Vec3],
    hip_height_m: float,
    up: Vec3,
    minimum_frames: int = 3,
) -> list[dict[str, Any]]:
    """Persist dense, reproducible sole/toe/contact slide facts per plant.

    The source animation may already contain contact drift.  This function
    records that measured fact; the candidate pipeline compares candidate
    windows with its hash-bound baseline using the policy's regression bound.
    A foot-root residual is intentionally not used as a substitute for these
    mask-centroid paths.
    """

    if not (
        len(states)
        == len(times)
        == len(contact_centroids)
        == len(sole_centroids)
        == len(toe_centroids)
    ):
        raise ContractError("planted-window arrays must have one value per frame")
    height = _number(hip_height_m, label="planted-window hip height")
    if height <= 0.0:
        raise ContractError("planted-window hip height must be positive")
    if not isinstance(minimum_frames, int) or isinstance(minimum_frames, bool) or minimum_frames < 2:
        raise ContractError("planted-window minimum frame count must be at least two")

    def segment_slide(points: Sequence[Vec3], start: int, end: int, *, label: str) -> dict[str, Any]:
        values = [
            _norm(_project_ground(_sub(points[index], points[index - 1]), up))
            for index in range(start + 1, end + 1)
        ]
        path_m = math.fsum(values)
        net_m = _norm(_project_ground(_sub(points[end], points[start]), up))
        step_stats = _stats(values, unit="m") if values else None
        normalized = [value / height for value in values]
        normalized_stats = _stats(normalized, unit="ratio") if normalized else None
        return {
            "label": label,
            "step_count": len(values),
            "step_slide_m": step_stats,
            "step_slide_over_hip_height": normalized_stats,
            "path_m": path_m,
            "path_over_hip_height": path_m / height,
            "net_displacement_m": net_m,
            "net_displacement_over_hip_height": net_m / height,
            "max_step_m": max(values) if values else 0.0,
            "max_step_over_hip_height": max(normalized) if normalized else 0.0,
        }

    windows: list[dict[str, Any]] = []
    start: int | None = None
    for index, state in enumerate(tuple(states) + (False,)):
        if state and start is None:
            start = index
            continue
        if state or start is None:
            continue
        end = index - 1
        frame_count = end - start + 1
        window: dict[str, Any] = {
            "start_frame": start,
            "end_frame": end,
            "start_time_s": times[start],
            "end_time_s": times[end],
            "duration_s": times[end] - times[start],
            "frame_count": frame_count,
            "state": "PLANTED" if frame_count >= minimum_frames else "SHORT_PLANT_UNEVALUATED",
        }
        if frame_count >= minimum_frames:
            contact_points = [contact_centroids[item] for item in range(start, end + 1)]
            if any(point is None for point in contact_points):
                raise ContractError("a planted state window is missing a contact centroid")
            window["slide"] = {
                "contact": segment_slide(
                    tuple(point for point in contact_points if point is not None),
                    0,
                    frame_count - 1,
                    label="contact_centroid",
                ),
                "sole": segment_slide(sole_centroids, start, end, label="sole_centroid"),
                "toe": segment_slide(toe_centroids, start, end, label="toe_centroid"),
            }
        else:
            window["reason"] = "contact state did not persist for the minimum dense window"
        windows.append(window)
        start = None
    # A short or synthetic probe may contain no qualifying planted window.
    # Preserve its measured contact states and explicit short-window records;
    # the candidate pipeline rejects such input at its planted-slide gate,
    # while the generic frame analyzer can still report other valid metrics.
    return windows


def _engineering_envelope(policy: Mapping[str, Any], gait_state: str) -> dict[str, Any]:
    states = policy["gaitStates"]
    if gait_state not in states:
        raise ContractError(f"gait state {gait_state!r} is not present in the policy")
    state = states[gait_state]
    if not isinstance(state, Mapping):
        raise ContractError(f"gait state {gait_state!r} must be an object")
    envelope: dict[str, Any] = {
        "gait_state": gait_state,
        "classification": str(state.get("confidence", "engineering_prior")),
        "scientific_claim": False,
        "source_policy_status": policy["status"],
        "comparison": "informational_engineering_envelope_not_physical_acceptance",
    }
    if policy["schema"] in {POLICY_SCHEMA_V2, POLICY_SCHEMA_V3}:
        envelope["metric_semantics"] = dict(policy["metricSemantics"])
        envelope["planner_target"] = dict(policy["plannerTargets"][gait_state])
        envelope["planner_target"]["comparison"] = (
            "planner_domain_only_never_compared_to_observed_stance_or_step_envelopes"
        )
        envelope["observed_metric_envelopes"] = {
            key: state[key]
            for key in (
                "stanceSupportWidthHObservedCalibrationRange",
                "stepWidthHObservedCalibrationRange",
            )
            if key in state
        }
    for key in (
        "stanceSupportWidthHSoftBand",
        "stanceSupportWidthHHardEnvelope",
        "stanceSupportWidthHUncertainty",
        "footHeadingAbsDegreesSoftMax",
        "footHeadingUncertaintyDegrees",
        "crossover",
    ):
        if key in state:
            envelope[key] = state[key]
    return envelope


def analyze_frame_sequence(
    frames: Sequence[Mapping[str, Any]],
    *,
    policy: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    source_id: str = "synthetic-frame-sequence",
    source_sha256: str | None = None,
    clip_name: str = "synthetic",
    gait_state: str = "straight_walk",
    policy_sha256: str | None = None,
    source_profile_sha256: str | None = None,
    ground_level_m: float = 0.0,
    travel_tangent_basis: Sequence[float] | None = None,
    travel_tangent_basis_source: str | None = None,
    travel_tangent_basis_sha256: str | None = None,
    lateral_axis_basis: Sequence[float] | None = None,
    lateral_axis_basis_source: str | None = None,
    lateral_axis_basis_sha256: str | None = None,
    planted_window_min_frames: int = 3,
) -> ContactGaugeResult:
    """Analyze generic frame data with no source- or species-specific branch."""

    policy = _validate_narrow_gauge_policy(policy)
    parsed_frames = _coerce_frames(frames)
    parsed_thresholds = _validate_thresholds(thresholds)
    ground_level = _number(ground_level_m, label="ground_level_m")
    engineering_envelope = _engineering_envelope(policy, gait_state)
    if gait_state == "turn":
        report: dict[str, Any] = {
            "schema": REPORT_SCHEMA,
            "status": "UNEVALUATED_UNSUPPORTED",
            "source": {
                "id": source_id,
                "clip": clip_name,
                "sha256": source_sha256,
                "read_only": True,
                "profile_sha256": source_profile_sha256,
            },
            "policy": {
                "schema": policy["schema"],
                "status": policy["status"],
                "sha256": policy_sha256,
                "scientific_claim": False,
                "species_hardcode": False,
                "metric_semantics": policy.get("metricSemantics"),
            },
            "coordinate_system": _COORDINATE_SYSTEM,
            "sampling": {
                "count": len(parsed_frames),
                "duration_s": parsed_frames[-1].time_s - parsed_frames[0].time_s,
                "mode": "frame_sequence",
                "all_numeric_values_finite": True,
            },
            "measured": None,
            "engineering_envelopes": engineering_envelope,
            "thresholds": {
                **parsed_thresholds,
                "classification": "engineering_envelope_input_not_measured_fact",
            },
            "limitations": [
                "Turn is UNEVALUATED_UNSUPPORTED in this pre-solver slice.",
                "Turn requires local curvature/tangent and explicit inner/outer contact roles; an interval-wide tangent is not admitted.",
            ],
        }
        ensure_finite(report, label="unsupported turn report")
        return ContactGaugeResult(report=report, report_sha256=canonical_hash(report))
    up = (0.0, 1.0, 0.0)
    if travel_tangent_basis is None:
        travel, _measured_lateral, travel_speed = _derive_travel_frame(
            parsed_frames,
            up=up,
            travel_epsilon_mps=float(parsed_thresholds["travel_epsilon_mps"]),
        )
        lateral, lateral_axis_derivation = _orient_anatomical_lateral(
            parsed_frames,
            up=up,
            travel=travel,
            orientation_basis=lateral_axis_basis,
        )
        tangent_basis = {
            "source": "clip_root_ground_displacement",
            "clip_motion_used": True,
            "hash_sha256": None,
        }
    else:
        if not isinstance(travel_tangent_basis_source, str) or not travel_tangent_basis_source:
            raise ContractError("an explicit travel tangent requires a provenance source")
        travel = _unit(
            _project_ground(_vec3(travel_tangent_basis, label="travel tangent basis"), up),
            label="explicit travel tangent basis",
        )
        lateral, lateral_axis_derivation = _orient_anatomical_lateral(
            parsed_frames,
            up=up,
            travel=travel,
            orientation_basis=lateral_axis_basis,
        )
        # A basis is not a measurement of this clip's travel speed.  Keep the
        # speed fact honest while allowing headings/ground projections to be
        # evaluated in a hash-bound external frame.
        travel_speed = 0.0
        tangent_basis = {
            "source": travel_tangent_basis_source,
            "clip_motion_used": False,
            "hash_sha256": travel_tangent_basis_sha256,
        }

    times = [frame.time_s for frame in parsed_frames]
    hip_heights = [_dot(frame.hip_center_m, up) - ground_level for frame in parsed_frames]
    hip_widths = [
        _norm(_project_ground(_sub(frame.hip_left_m, frame.hip_right_m), up))
        for frame in parsed_frames
    ]
    hip_height = _stats(hip_heights, unit="m")
    hip_width = _stats(hip_widths, unit="m")
    if hip_height["median"] <= 0.0 or hip_width["median"] <= 0.0:
        raise ContractError("hip height and width must be positive")
    canonical_hip_height = float(hip_height["median"])
    canonical_hip_width = float(hip_width["median"])

    per_foot: dict[str, dict[str, Any]] = {}
    frame_facts: list[dict[str, Any]] = []
    contact_states: dict[str, list[bool]] = {"left": [], "right": []}
    contact_centroids: dict[str, list[Vec3 | None]] = {"left": [], "right": []}
    contact_speeds: dict[str, list[float]] = {"left": [], "right": []}
    sole_centroids: dict[str, list[Vec3]] = {"left": [], "right": []}
    toe_centroids: dict[str, list[Vec3]] = {"left": [], "right": []}
    floor_facts: dict[str, dict[str, list[float]]] = {
        side: {
            "sole_gap": [],
            "toe_gap": [],
            "sole_penetration": [],
            "toe_penetration": [],
        }
        for side in ("left", "right")
    }
    geometric_centroids: dict[str, list[Vec3]] = {"left": [], "right": []}
    toe_centroids_for_velocity: dict[str, list[Vec3]] = {
        side: [
            _weighted_centroid(
                frame.feet[side].toe_points,
                label=f"frame {frame_index} {side} toe",
            )
            for frame_index, frame in enumerate(parsed_frames)
        ]
        for side in ("left", "right")
    }
    toe_velocities: dict[str, tuple[Vec3, ...]] = {
        side: _finite_difference(
            toe_centroids_for_velocity[side],
            times,
            label=f"{side} toe contact velocity",
        )
        for side in ("left", "right")
    }

    for frame_index, frame in enumerate(parsed_frames):
        frame_feet: dict[str, dict[str, Any]] = {}
        for side in ("left", "right"):
            foot = frame.feet[side]
            all_points = foot.all_points
            sole_centroid = _weighted_centroid(foot.sole_points, label=f"frame {frame_index} {side} sole")
            toe_centroid = toe_centroids_for_velocity[side][frame_index]
            all_centroid = _weighted_centroid(all_points, label=f"frame {frame_index} {side} mask")
            geometric_centroids[side].append(all_centroid)
            sole_centroids[side].append(sole_centroid)
            toe_centroids[side].append(toe_centroid)
            sole_gaps = [_dot(point, up) - ground_level for point, _ in foot.sole_points]
            toe_gaps = [_dot(point, up) - ground_level for point, _ in foot.toe_points]
            floor_facts[side]["sole_gap"].append(min(sole_gaps))
            floor_facts[side]["toe_gap"].append(min(toe_gaps))
            floor_facts[side]["sole_penetration"].append(max(0.0, -min(sole_gaps)))
            floor_facts[side]["toe_penetration"].append(max(0.0, -min(toe_gaps)))

            active_points = [
                (point, weight)
                for point, weight in all_points
                if _dot(point, up) - ground_level <= float(parsed_thresholds["floor_gap_tolerance_m"])
            ]
            closest_gap = min(min(sole_gaps), min(toe_gaps))
            candidate_centroid = (
                _weighted_centroid(active_points, label=f"frame {frame_index} {side} active contact")
                if len(active_points) >= int(parsed_thresholds["minimum_active_points"])
                else None
            )
            # Use forward, centered, or backward differences on the full
            # deterministic toe mask. The active subset changes as vertices
            # cross the floor tolerance; using it would manufacture a
            # touchdown speed even when the foot geometry has settled.
            # Contact velocity is measured in the ground frame. A planted foot
            # should remain near the floor even when the root-motion clip
            # advances, so subtracting root velocity would invert the meaning
            # of the contact threshold.
            relative_speed = _norm(toe_velocities[side][frame_index])
            contact = (
                candidate_centroid is not None
                and closest_gap <= float(parsed_thresholds["toe_off_gap_m"])
                and relative_speed <= float(parsed_thresholds["contact_relative_velocity_mps"])
            )
            contact_states[side].append(contact)
            contact_centroids[side].append(candidate_centroid if contact else None)
            contact_speeds[side].append(relative_speed)
            foot_axis = _project_ground(_sub(toe_centroid, foot.axis_origin_m), up)
            foot_axis = _unit(foot_axis, label=f"frame {frame_index} {side} foot axis")
            heading_radians = math.atan2(_dot(_cross(foot_axis, travel), up), _dot(foot_axis, travel))
            frame_feet[side] = {
                "side": side,
                "axis_origin_m": list(foot.axis_origin_m),
                "toe_centroid_m": list(toe_centroid),
                "sole_centroid_m": list(sole_centroid),
                "contact_centroid_m": None if not contact else list(candidate_centroid or all_centroid),
                "contact": contact,
                "contact_state": "PLANTED" if contact else "SWING",
                "relative_contact_velocity_mps": relative_speed,
                "foot_heading_degrees": math.degrees(heading_radians),
                "sole_min_gap_m": min(sole_gaps),
                "toe_min_gap_m": min(toe_gaps),
                "sole_penetration_m": max(0.0, -min(sole_gaps)),
                "toe_penetration_m": max(0.0, -min(toe_gaps)),
                "active_point_count": len(active_points),
            }

        left_contact = contact_centroids["left"][-1]
        right_contact = contact_centroids["right"][-1]
        hip_center = frame.hip_center_m
        # Track-to-midline and crossover are per-foot active-contact facts, not
        # only simultaneous bilateral support facts.  Alternating gait clips
        # otherwise produce null tracks and a vacuous ``crossover: false`` for
        # every unilateral planted frame.  Support width remains defined only
        # when both contacts are present; the pipeline uses the explicit
        # touchdown-step fallback when support is unavailable.
        left_track_signed = (
            _dot(_sub(left_contact, hip_center), lateral)
            if left_contact is not None
            else None
        )
        right_track_signed = (
            _dot(_sub(right_contact, hip_center), lateral)
            if right_contact is not None
            else None
        )
        support_width = (
            abs(left_track_signed - right_track_signed)
            if left_track_signed is not None and right_track_signed is not None
            else None
        )
        crossover = (
            (
                left_track_signed is not None
                and left_track_signed < -float(parsed_thresholds["crossover_epsilon_m"])
            )
            or (
                right_track_signed is not None
                and right_track_signed > float(parsed_thresholds["crossover_epsilon_m"])
            )
        )
        frame_facts.append(
            {
                "frame": frame_index,
                "time_s": frame.time_s,
                "root_m": list(frame.root_m),
                "hip_center_m": list(frame.hip_center_m),
                "hip_height_m": hip_heights[frame_index],
                "hip_width_m": hip_widths[frame_index],
                "left_track_to_midline_signed_m": left_track_signed,
                "right_track_to_midline_signed_m": right_track_signed,
                "support_width_m": support_width,
                "crossover": crossover,
                "feet": frame_feet,
            }
        )

    simultaneous_indices = [
        index
        for index in range(len(parsed_frames))
        if contact_centroids["left"][index] is not None and contact_centroids["right"][index] is not None
    ]
    if not simultaneous_indices and travel_tangent_basis is None:
        raise ContractError("no simultaneous bilateral contact frames for support-width measurement")
    support_widths: list[float] = []
    left_tracks: list[float] = []
    right_tracks: list[float] = []
    left_tracks_over_width: list[float] = []
    right_tracks_over_width: list[float] = []
    support_over_width: list[float] = []
    support_over_height: list[float] = []
    crossovers: list[int] = []
    for index in simultaneous_indices:
        fact = frame_facts[index]
        support = float(fact["support_width_m"])
        left_track = abs(float(fact["left_track_to_midline_signed_m"]))
        right_track = abs(float(fact["right_track_to_midline_signed_m"]))
        support_widths.append(support)
        left_tracks.append(left_track)
        right_tracks.append(right_track)
        left_tracks_over_width.append(left_track / canonical_hip_width)
        right_tracks_over_width.append(right_track / canonical_hip_width)
        support_over_width.append(support / canonical_hip_width)
        support_over_height.append(support / canonical_hip_height)
        if fact["crossover"]:
            crossovers.append(index)

    touchdown_events = [
        (parsed_frames[index].time_s, side, contact_centroids[side][index])
        for index in range(len(parsed_frames))
        for side in ("left", "right")
        if contact_centroids[side][index] is not None
        and (index == 0 or contact_centroids[side][index - 1] is None)
    ]
    # Contact centroids are filtered above, but retain the explicit guard in
    # the typed event stream so a future adapter cannot silently pass a null
    # centroid into the metric.
    typed_touchdown_events = tuple(
        (time_s, side, centroid)
        for time_s, side, centroid in touchdown_events
        if centroid is not None
    )
    touchdown_pairs = _successive_contralateral_touchdown_pairs(typed_touchdown_events)
    step_widths = [
        abs(_dot(_sub(current[2], previous[2]), lateral))
        for previous, current in touchdown_pairs
    ]
    if not step_widths:
        # A continuous bilateral support fixture can have no distinct
        # touchdown transition; keep the metric explicit rather than inventing
        # a step width from simultaneous support.
        step_widths = []
    step_width_definition = (
        "abs(dot(C_next_contact - C_previous_contralateral_contact, L)) / H; "
        "successive contralateral touchdown centroids, with H equal to the "
        "analyzed-window median hip height; pair only adjacent chronological "
        "events with alternating sides and delta_t > 1e-12 s"
    )
    step_width_normalized: dict[str, Any] = {
        "definition": step_width_definition,
        "normalizer": {
            "name": "H",
            "unit": "m",
            "value_m": canonical_hip_height,
            "scope": "analyzed_window_median",
        },
        "status": "MEASURED" if step_widths else "UNEVALUATED",
        "raw_m": None if not step_widths else _stats(step_widths, unit="m"),
        "values": (
            None
            if not step_widths
            else _stats([step / canonical_hip_height for step in step_widths], unit="ratio")
        ),
        "event_pair_count": len(step_widths),
    }
    if not step_widths:
        step_width_normalized["reason"] = (
            "No robust successive contralateral contact-centroid pair was "
            "available in this analyzed window; support width is not substituted."
        )

    heading_values = {
        side: [float(fact["feet"][side]["foot_heading_degrees"]) for fact in frame_facts]
        for side in ("left", "right")
    }
    times_by_side = {
        side: [frame.time_s for frame in parsed_frames]
        for side in ("left", "right")
    }

    for side in ("left", "right"):
        mask_count = len(parsed_frames[0].feet[side].all_points)
        sole_count = len(parsed_frames[0].feet[side].sole_points)
        toe_count = len(parsed_frames[0].feet[side].toe_points)
        per_foot[side] = {
            "mask": {
                "sole_point_count": sole_count,
                "toe_point_count": toe_count,
                "union_point_count": mask_count,
                "weight_threshold": "input-defined",
                "proxy_forbidden": "ankle_or_toe_root_origin_alone",
            },
            "track_to_midline_m": _stats_or_unevaluated(
                left_tracks if side == "left" else right_tracks,
                unit="m",
                reason="no simultaneous bilateral contact frames",
            ),
            "track_to_midline_over_hip_width": _stats_or_unevaluated(
                left_tracks_over_width if side == "left" else right_tracks_over_width,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "track_to_midline_over_hip_height": _stats_or_unevaluated(
                [
                    (left_tracks[position] if side == "left" else right_tracks[position])
                    / canonical_hip_height
                    for position, index in enumerate(simultaneous_indices)
                ],
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "foot_heading_degrees": _stats(heading_values[side], unit="degrees"),
            "floor": {
                "sole_min_gap_m": _stats(floor_facts[side]["sole_gap"], unit="m"),
                "toe_min_gap_m": _stats(floor_facts[side]["toe_gap"], unit="m"),
                "sole_penetration_m": _stats(floor_facts[side]["sole_penetration"], unit="m"),
                "toe_penetration_m": _stats(floor_facts[side]["toe_penetration"], unit="m"),
            },
            "contact_windows": _window_payload(tuple(contact_states[side]), times_by_side[side], target=True),
            "toe_off_windows": _toe_off_payload(tuple(contact_states[side]), times_by_side[side]),
            "contact_occupancy": sum(contact_states[side]) / len(contact_states[side]),
        }

    planted_windows = {
        side: _planted_window_metrics(
            contact_states[side],
            times,
            contact_centroids=contact_centroids[side],
            sole_centroids=sole_centroids[side],
            toe_centroids=toe_centroids[side],
            hip_height_m=canonical_hip_height,
            up=up,
            minimum_frames=planted_window_min_frames,
        )
        for side in ("left", "right")
    }

    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": "PASS_EXPLICIT_BASIS" if travel_tangent_basis is not None else "PASS",
        "source": {
            "id": source_id,
            "clip": clip_name,
            "sha256": source_sha256,
            "read_only": True,
            "profile_sha256": source_profile_sha256,
        },
        "policy": {
            "schema": policy["schema"],
            "status": policy["status"],
            "sha256": policy_sha256,
            "scientific_claim": False,
            "species_hardcode": False,
            "metric_semantics": policy.get("metricSemantics"),
        },
        "coordinate_system": _COORDINATE_SYSTEM,
        "sampling": {
            "count": len(parsed_frames),
            "duration_s": parsed_frames[-1].time_s - parsed_frames[0].time_s,
            "mode": "frame_sequence",
            "all_numeric_values_finite": True,
        },
        "measured": {
            "ground_level_m": ground_level,
            "travel_tangent": list(travel),
            "lateral_axis": list(lateral),
            "travel_speed_mps": travel_speed,
            "axis_derivation": (
                "measured root ground displacement plus clip-specific named hip left-right geometry"
                if travel_tangent_basis is None and lateral_axis_basis is None
                else (
                    "measured root ground displacement plus " + lateral_axis_derivation
                    if travel_tangent_basis is None
                    else "explicit hash-bound tangent basis plus " + lateral_axis_derivation
                )
            ),
            "lateral_axis_basis": {
                "source": lateral_axis_basis_source,
                "hash_sha256": lateral_axis_basis_sha256,
                "orientation_only": lateral_axis_basis is not None,
            },
            "travel_tangent_basis": tangent_basis,
            "normalization": {
                "hip_height_H_m": canonical_hip_height,
                "hip_width_W_m": canonical_hip_width,
                "window_scope": "analyzed_window_median",
                "height_ratio_definition": "all support/track/step widths divided by canonical median H",
                "width_ratio_definition": "optional gauge view divided by canonical median W",
            },
            "hip_height_m": hip_height,
            "hip_width_m": hip_width,
            "feet": per_foot,
            "stance_support_width_m": _stats_or_unevaluated(
                support_widths,
                unit="m",
                reason="no simultaneous bilateral contact frames",
            ),
            "stance_support_width_over_hip_width": _stats_or_unevaluated(
                support_over_width,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "stance_support_width_over_hip_height": _stats_or_unevaluated(
                support_over_height,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            # Explicit compatibility aliases for V1 report consumers. The
            # semantic map below forbids treating these observed simultaneous
            # support facts as planner lane-centre inputs.
            "support_width_m": _stats_or_unevaluated(
                support_widths,
                unit="m",
                reason="no simultaneous bilateral contact frames",
            ),
            "support_width_over_hip_width": _stats_or_unevaluated(
                support_over_width,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "support_width_over_hip_height": _stats_or_unevaluated(
                support_over_height,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "left_track_to_midline_over_hip_width": _stats_or_unevaluated(
                left_tracks_over_width,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "right_track_to_midline_over_hip_width": _stats_or_unevaluated(
                right_tracks_over_width,
                unit="ratio",
                reason="no simultaneous bilateral contact frames",
            ),
            "step_width_m": None if not step_widths else _stats(step_widths, unit="m"),
            "step_width_over_hip_width": (
                None
                if not step_widths
                else _stats(
                    [step / canonical_hip_width for step in step_widths],
                    unit="ratio",
                )
            ),
            "step_width_over_hip_height": step_width_normalized["values"],
            "step_width_normalized": step_width_normalized,
            "metric_semantics": {
                "target_lane_center_separation_over_hip_height": {
                    "kind": "planner_input",
                    "measured_here": False,
                    "value": None,
                },
                "stance_support_width_over_hip_height": {
                    "kind": "measured_simultaneous_support",
                    "measured_here": bool(support_widths),
                    "value_key": "stance_support_width_over_hip_height",
                },
                "step_width_over_hip_height": {
                    "kind": "measured_successive_contralateral_footfalls",
                    "measured_here": bool(step_widths),
                    "value_key": "step_width_over_hip_height",
                },
                "deprecated_aliases": {
                    "support_width_m": "stance_support_width_m",
                    "support_width_over_hip_width": "stance_support_width_over_hip_width",
                    "support_width_over_hip_height": "stance_support_width_over_hip_height",
                },
            },
            "crossover": {
                "observed": bool(crossovers),
                "frame_count": len(crossovers),
                "frames": crossovers,
                "classification": "measured_contact_geometry_fact",
            },
            "contact_window_summary": {
                side: {
                    "contact_windows": per_foot[side]["contact_windows"],
                    "toe_off_windows": per_foot[side]["toe_off_windows"],
                }
                for side in ("left", "right")
            },
            "planted_windows": planted_windows,
        },
        "engineering_envelopes": engineering_envelope,
        "thresholds": {
            **parsed_thresholds,
            "classification": "engineering_envelope_input_not_measured_fact",
        },
        "frame_facts": frame_facts,
            "limitations": [
            "Contact/gauge values are measured bookkeeping from supplied geometry and animation samples.",
            "Engineering envelopes are provisional and are not scientific or physical feasibility claims.",
            "No support polygon, friction, impulse, whole-body solve, curve adjustment, promotion, or runtime mutation is performed.",
            "Ground level and mask membership are explicit input policy; inherited penetration is reported, not corrected.",
            "Support-width statistics are unevaluated when this clip has no simultaneous bilateral contact frames; no proxy is substituted.",
            "Planner target-lane separation is an input owned by a walk profile and is never inferred from or bounded against measured stance-support or step-width output here.",
        ],
    }
    ensure_finite(report, label="contact/gauge report")
    return ContactGaugeResult(report=report, report_sha256=canonical_hash(report))


def _qnorm(quaternion: Sequence[float]) -> tuple[float, float, float, float]:
    values = tuple(_number(item, label="quaternion") for item in quaternion)
    length = math.sqrt(sum(item * item for item in values))
    if length <= 1.0e-15:
        raise ContractError("animation quaternion is zero")
    return tuple(item / length for item in values)  # type: ignore[return-value]


def _qdot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _qslerp(left: Sequence[float], right: Sequence[float], amount: float) -> tuple[float, float, float, float]:
    first = _qnorm(left)
    second = _qnorm(right)
    cosine = _qdot(first, second)
    if cosine < 0.0:
        second = tuple(-item for item in second)
        cosine = -cosine
    cosine = min(1.0, max(-1.0, cosine))
    if cosine > 0.9995:
        return _qnorm(tuple(a + (b - a) * amount for a, b in zip(first, second)))
    angle = math.acos(cosine)
    sine = math.sin(angle)
    first_scale = math.sin((1.0 - amount) * angle) / sine
    second_scale = math.sin(amount * angle) / sine
    return _qnorm(tuple(a * first_scale + b * second_scale for a, b in zip(first, second)))


def _mat_mul(left: Mat4, right: Mat4) -> Mat4:
    return tuple(
        tuple(sum(left[row][index] * right[index][column] for index in range(4)) for column in range(4))
        for row in range(4)
    )  # type: ignore[return-value]


def _mat_point(matrix: Mat4, point: Vec3) -> Vec3:
    values = (*point, 1.0)
    result = tuple(sum(matrix[row][index] * values[index] for index in range(4)) for row in range(4))
    if abs(result[3]) <= 1.0e-15:
        raise ContractError("animation transform has zero homogeneous coordinate")
    return tuple(result[index] / result[3] for index in range(3))  # type: ignore[return-value]


def _qmatrix(quaternion: Sequence[float], translation: Sequence[float], scale: Sequence[float]) -> Mat4:
    x, y, z, w = _qnorm(quaternion)
    sx, sy, sz = (_number(item, label="node scale") for item in scale)
    tx, ty, tz = (_number(item, label="node translation") for item in translation)
    return (
        ((1.0 - 2.0 * (y * y + z * z)) * sx, 2.0 * (x * y - z * w) * sy, 2.0 * (x * z + y * w) * sz, tx),
        (2.0 * (x * y + z * w) * sx, (1.0 - 2.0 * (x * x + z * z)) * sy, 2.0 * (y * z - x * w) * sz, ty),
        (2.0 * (x * z - y * w) * sx, 2.0 * (y * z + x * w) * sy, (1.0 - 2.0 * (x * x + y * y)) * sz, tz),
        (0.0, 0.0, 0.0, 1.0),
    )


def _column_major_matrix(values: Sequence[float]) -> Mat4:
    if len(values) != 16:
        raise ContractError("inverse bind matrix must contain 16 values")
    return tuple(tuple(float(values[column * 4 + row]) for column in range(4)) for row in range(4))  # type: ignore[return-value]


@dataclass(frozen=True)
class _Channel:
    track: TrsTrack

    def sample(self, time_s: float) -> tuple[float, ...]:
        return tuple(float(value) for value in self.track.sample(time_s))


def _validate_glb_document_tables(glb: Glb) -> Mapping[str, Any]:
    document = getattr(glb, "document", None)
    if not isinstance(document, Mapping):
        raise ContractError("GLB document must be an object")
    for key in ("nodes", "accessors", "bufferViews", "skins"):
        if not isinstance(document.get(key), list):
            raise ContractError(f"GLB {key} table must be an array")
    return document


def _validate_glb_node_index(glb: Glb, index: Any, *, label: str) -> int:
    document = _validate_glb_document_tables(glb)
    nodes = document["nodes"]
    if isinstance(index, bool) or not isinstance(index, int):
        raise ContractError(f"{label} node index must be an integer")
    if index < 0 or index >= len(nodes):
        raise ContractError(f"{label} node index {index} is out of range")
    if not isinstance(nodes[index], Mapping):
        raise ContractError(f"{label} node entry must be an object")
    return index


def _validate_glb_accessor_index(glb: Glb, index: Any, *, label: str) -> int:
    document = _validate_glb_document_tables(glb)
    accessors = document["accessors"]
    if isinstance(index, bool) or not isinstance(index, int):
        raise ContractError(f"{label} accessor index must be an integer")
    if index < 0 or index >= len(accessors):
        raise ContractError(
            f"{label} accessor index {index} is out of range (count {len(accessors)})"
        )
    item = accessors[index]
    if not isinstance(item, Mapping):
        raise ContractError(f"{label} accessor entry must be an object")
    return index


def _read_glb_accessor(glb: Glb, index: Any, *, label: str) -> list[tuple[float | int, ...]]:
    """Validate an accessor reference before reading its container-backed data."""

    validated_index = _validate_glb_accessor_index(glb, index, label=label)
    try:
        values = glb.accessor_values(validated_index)
    except ContractError:
        raise
    except _GLB_CONTAINER_ERRORS as exc:
        raise ContractError(f"{label} accessor data is malformed") from exc
    if not isinstance(values, list):
        raise ContractError(f"{label} accessor data must be an array")
    return values


def _animation_channels(glb: Glb, animation_name: str) -> tuple[dict[tuple[int, str], _Channel], tuple[float, ...]]:
    parsed, _ = read_animation_tracks(
        glb, animation_name, require_common_timeline=False
    )
    channels: dict[tuple[int, str], _Channel] = {}
    common_times: tuple[float, ...] | None = None
    for key, track in parsed.items():
        if track.path not in {"rotation", "translation", "scale"}:
            raise ContractError("animation contains an unsupported target")
        times = tuple(float(value) for value in track.times)
        if common_times is None:
            common_times = times
        elif common_times != times:
            # Contact sampling admits denser channels only when their temporal
            # domain remains exactly the clip domain.
            if abs(times[0] - common_times[0]) > 1.0e-6 or abs(times[-1] - common_times[-1]) > 1.0e-6:
                raise ContractError("animation channels do not share a common timeline domain")
        channels[key] = _Channel(track=track)
    if common_times is None:
        raise ContractError("animation has no channels")
    return channels, common_times


def _pose_matrices(glb: Glb, channels: Mapping[tuple[int, str], _Channel], time_s: float) -> tuple[Mat4, ...]:
    matrices: list[Mat4 | None] = [None] * len(glb.nodes)
    visiting: set[int] = set()

    def resolve(index: int) -> Mat4:
        if matrices[index] is not None:
            return matrices[index]  # type: ignore[return-value]
        if index in visiting:
            raise ContractError("node hierarchy contains a cycle")
        visiting.add(index)
        node = glb.nodes[index]
        if "matrix" in node:
            raise ContractError("matrix-authored nodes are unsupported; use explicit TRS")
        static_translation = tuple(node.get("translation", [0.0, 0.0, 0.0]))
        static_rotation = tuple(node.get("rotation", [0.0, 0.0, 0.0, 1.0]))
        static_scale = tuple(node.get("scale", [1.0, 1.0, 1.0]))
        translation = channels.get((index, "translation"))
        rotation = channels.get((index, "rotation"))
        scale = channels.get((index, "scale"))
        local = _qmatrix(
            rotation.sample(time_s) if rotation else static_rotation,
            translation.sample(time_s) if translation else static_translation,
            scale.sample(time_s) if scale else static_scale,
        )
        parent = glb.parents[index]
        matrices[index] = local if parent is None else _mat_mul(resolve(parent), local)
        visiting.remove(index)
        return matrices[index]  # type: ignore[return-value]

    for index in range(len(glb.nodes)):
        resolve(index)
    return tuple(matrix for matrix in matrices if matrix is not None)


def _source_frames(
    glb: Glb,
    source: Mapping[str, Any],
    *,
    animation_name: str,
    sample_count: int | None = None,
    sample_times: Sequence[float] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    geometry = source["geometry"]
    _validate_glb_document_tables(glb)
    profile_accessor_indices = {
        "source geometry position": geometry["position_accessor"],
        **{
            f"source geometry joint[{index}]": value
            for index, value in enumerate(geometry["joint_accessors"])
        },
        **{
            f"source geometry weight[{index}]": value
            for index, value in enumerate(geometry["weight_accessors"])
        },
    }
    for label, index in profile_accessor_indices.items():
        _validate_glb_accessor_index(glb, index, label=label)
    channels, timeline = _animation_channels(glb, animation_name)
    timeline_start = timeline[0]
    timeline_end = timeline[-1]
    if sample_count is not None and sample_times is not None:
        raise ContractError("source frame sampling cannot specify count and exact times")
    if sample_times is None:
        count = int(
            source["sampling"]["count"] if sample_count is None else sample_count
        )
        if count < 2:
            raise ContractError("source frame sampling count must be at least two")
        times = list(
            _uniform_times(
                timeline_start, timeline_end, count, label="animation timeline"
            )
        )
    else:
        times = []
        for index, value in enumerate(sample_times):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ContractError(
                    f"source exact sample time {index} must be finite"
                )
            time_s = float(value)
            if not math.isfinite(time_s):
                raise ContractError(
                    f"source exact sample time {index} must be finite"
                )
            if times and time_s <= times[-1]:
                raise ContractError("source exact sample times must be strictly increasing")
            times.append(time_s)
        count = len(times)
        if count < 2:
            raise ContractError("source exact sample times must contain at least two values")
        if (
            abs(times[0] - timeline_start) > 1.0e-9
            or abs(times[-1] - timeline_end) > 1.0e-9
        ):
            raise ContractError(
                "source exact sample times must span the complete animation timeline"
            )
        if any(
            value < timeline_start - 1.0e-9 or value > timeline_end + 1.0e-9
            for value in times
        ):
            raise ContractError("source exact sample time is outside the animation timeline")
    name_to_index = glb.name_to_node
    mesh_index = name_to_index.get(geometry["mesh_node"])
    if mesh_index is None or glb.nodes[mesh_index].get("mesh") is None:
        raise ContractError("source geometry mesh_node does not identify a mesh node")
    landmarks = geometry["landmarks"]
    required_names = {
        landmarks["root_node"],
        landmarks["hip_left_node"],
        landmarks["hip_right_node"],
        landmarks["foot_roots"]["left"],
        landmarks["foot_roots"]["right"],
    }
    for mask in geometry["feet"].values():
        required_names.update(mask["sole_joints"])
        required_names.update(mask["toe_joints"])
    missing_names = sorted(name for name in required_names if name not in name_to_index)
    if missing_names:
        raise ContractError(f"source geometry references missing nodes: {missing_names}")

    positions = _read_glb_accessor(
        glb,
        geometry["position_accessor"],
        label="source geometry position",
    )
    joint_accessors = [
        _read_glb_accessor(glb, index, label=f"source geometry joint[{row}]")
        for row, index in enumerate(geometry["joint_accessors"])
    ]
    weight_accessors = [
        _read_glb_accessor(glb, index, label=f"source geometry weight[{row}]")
        for row, index in enumerate(geometry["weight_accessors"])
    ]
    if any(len(accessor) != len(positions) for accessor in (*joint_accessors, *weight_accessors)):
        raise ContractError("source geometry accessors do not share a vertex count")
    skin_index = int(geometry["skin_index"])
    if skin_index < 0 or skin_index >= len(glb.document.get("skins", [])):
        raise ContractError("source skin index is invalid")
    skin = glb.document["skins"][skin_index]
    if not isinstance(skin, Mapping):
        raise ContractError("source skin entry must be an object")
    raw_joint_nodes = skin.get("joints", [])
    if not isinstance(raw_joint_nodes, list):
        raise ContractError("source skin joints must be an array")
    try:
        joint_nodes = [int(item) for item in raw_joint_nodes]
    except _GLB_CONTAINER_ERRORS as exc:
        raise ContractError("source skin joints are malformed") from exc
    for joint_slot, joint_node in enumerate(joint_nodes):
        _validate_glb_node_index(glb, joint_node, label=f"source skin joint[{joint_slot}]")
    inverse_accessor = skin.get("inverseBindMatrices")
    if not joint_nodes or not isinstance(inverse_accessor, int):
        raise ContractError("source skin requires joints and inverse bind matrices")
    inverse_rows = _read_glb_accessor(glb, inverse_accessor, label="source inverse-bind")
    try:
        inverse_bind = [_column_major_matrix(row) for row in inverse_rows]
    except _GLB_CONTAINER_ERRORS as exc:
        raise ContractError("source inverse-bind accessor rows are malformed") from exc
    if len(inverse_bind) != len(joint_nodes):
        raise ContractError("source inverse bind count does not match joints")
    influences = _normalize_skin_weights(
        joint_accessors,
        weight_accessors,
        vertex_count=len(positions),
        joint_count=len(joint_nodes),
    )

    masks_by_side: dict[str, dict[str, Any]] = {}
    for side, mask in geometry["feet"].items():
        sole_nodes = {name_to_index[name] for name in mask["sole_joints"]}
        toe_nodes = {name_to_index[name] for name in mask["toe_joints"]}
        threshold = float(mask["weight_threshold"])
        sole: list[tuple[int, float]] = []
        toe: list[tuple[int, float]] = []
        for vertex_index, rows in enumerate(influences):
            sole_weight = max(
                (weight for joint_slot, weight in rows if joint_nodes[joint_slot] in sole_nodes),
                default=0.0,
            )
            toe_weight = max(
                (weight for joint_slot, weight in rows if joint_nodes[joint_slot] in toe_nodes),
                default=0.0,
            )
            if sole_weight >= threshold:
                sole.append((vertex_index, sole_weight))
            if toe_weight >= threshold:
                toe.append((vertex_index, toe_weight))
        if not sole or not toe:
            raise ContractError(f"source {side} mask selected no sole or toe vertices")
        masks_by_side[side] = {
            "sole": sole,
            "toe": toe,
            "weight_threshold": threshold,
        }

    frames: list[dict[str, Any]] = []
    root_index = name_to_index[landmarks["root_node"]]
    hip_left_index = name_to_index[landmarks["hip_left_node"]]
    hip_right_index = name_to_index[landmarks["hip_right_node"]]
    foot_root_indices = {
        side: name_to_index[name]
        for side, name in landmarks["foot_roots"].items()
    }
    for time_s in times:
        pose = _pose_matrices(glb, channels, time_s)
        joint_matrices = {
            joint_node: _mat_mul(pose[joint_node], inverse_bind[slot])
            for slot, joint_node in enumerate(joint_nodes)
        }

        def skin_vertex(vertex_index: int) -> Vec3:
            position = tuple(float(item) for item in positions[vertex_index])
            result = [0.0, 0.0, 0.0]
            for joint_slot, weight in influences[vertex_index]:
                transformed = _mat_point(joint_matrices[joint_nodes[joint_slot]], position)
                for axis in range(3):
                    result[axis] += weight * transformed[axis]
            return tuple(result)  # type: ignore[return-value]

        feet: dict[str, dict[str, Any]] = {}
        for side in ("left", "right"):
            feet[side] = {
                "axis_origin_m": list(_mat_point(pose[foot_root_indices[side]], (0.0, 0.0, 0.0))),
                "sole_points": [
                    {"point_m": list(skin_vertex(vertex)), "weight": weight}
                    for vertex, weight in masks_by_side[side]["sole"]
                ],
                "toe_points": [
                    {"point_m": list(skin_vertex(vertex)), "weight": weight}
                    for vertex, weight in masks_by_side[side]["toe"]
                ],
            }
        frames.append(
            {
                "time_s": time_s,
                "root_m": list(_mat_point(pose[root_index], (0.0, 0.0, 0.0))),
                "hip_left_m": list(_mat_point(pose[hip_left_index], (0.0, 0.0, 0.0))),
                "hip_right_m": list(_mat_point(pose[hip_right_index], (0.0, 0.0, 0.0))),
                "feet": feet,
            }
        )
    return frames, {
        "duration_s": timeline_end - timeline_start,
        "timeline_start_s": timeline_start,
        "timeline_end_s": timeline_end,
        "timeline_count": len(timeline),
        "sample_count": len(times),
        "requested_sample_count": count,
        "sampling_grid": (
            "explicit_exact_times" if sample_times is not None else "uniform_count"
        ),
        "skin_weight_validation": "finite_nonnegative_positive_sum_normalized",
        "mask_counts": {
            side: {
                "sole": len(masks_by_side[side]["sole"]),
                "toe": len(masks_by_side[side]["toe"]),
                "weight_threshold": masks_by_side[side]["weight_threshold"],
                "sole_vertex_indices": [vertex for vertex, _ in masks_by_side[side]["sole"]],
                "toe_vertex_indices": [vertex for vertex, _ in masks_by_side[side]["toe"]],
            }
            for side in ("left", "right")
        },
    }


def analyze_glb(
    source_path: Path,
    source_profile_path: Path,
    policy_path: Path,
    *,
    repository: Path | None = None,
    clip_name: str | None = None,
    gait_state: str = "straight_walk",
    sample_count: int | None = None,
    sample_times: Sequence[float] | None = None,
    travel_tangent_basis: Sequence[float] | None = None,
    travel_tangent_basis_source: str | None = None,
    travel_tangent_basis_sha256: str | None = None,
    lateral_axis_basis: Sequence[float] | None = None,
    lateral_axis_basis_source: str | None = None,
    lateral_axis_basis_sha256: str | None = None,
    planted_window_min_frames: int = 3,
) -> ContactGaugeResult:
    """Evaluate one immutable GLB clip through the generic frame analyzer."""

    root = Path(__file__).resolve().parents[2] if repository is None else Path(repository)
    try:
        root_resolved = root.resolve(strict=False)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ContractError("repository path cannot be resolved") from exc
    resolved_source = _resolve_repository_path(source_path, root_resolved, label="source artifact")
    resolved_profile = _resolve_repository_path(
        source_profile_path,
        root_resolved,
        label="source profile",
    )
    resolved_policy = _resolve_repository_path(policy_path, root_resolved, label="narrow-gauge policy")
    source_profile = load_contact_gauge_source(resolved_profile)
    policy = load_narrow_gauge_policy(resolved_policy)
    expected_relative = source_profile["source"]["path"]
    expected_source = _resolve_repository_path(
        root_resolved / expected_relative,
        root_resolved,
        label="declared source artifact",
    )
    if resolved_source != expected_source:
        raise ContractError("source artifact does not match the declared profile path")
    source_hash = sha256_file(resolved_source)
    if source_hash != source_profile["source"]["sha256"]:
        raise ContractError("source artifact hash does not match its read-only profile")
    selected_clip = clip_name or source_profile["source"]["clips"]["root_motion"]
    if selected_clip not in source_profile["source"]["clips"].values():
        raise ContractError("selected clip is not declared by the source profile")
    try:
        glb = Glb(resolved_source)
    except ContractError:
        raise
    except _GLB_CONTAINER_ERRORS as exc:
        raise ContractError("GLB container is malformed") from exc
    try:
        frames, extraction = _source_frames(
            glb,
            source_profile,
            animation_name=selected_clip,
            sample_count=sample_count,
            sample_times=sample_times,
        )
    except ContractError:
        raise
    except _GLB_CONTAINER_ERRORS as exc:
        raise ContractError("GLB animation or accessor container is malformed") from exc
    result = analyze_frame_sequence(
        frames,
        policy=policy,
        thresholds=source_profile["thresholds"],
        source_id=expected_relative,
        source_sha256=source_hash,
        clip_name=selected_clip,
        gait_state=gait_state,
        policy_sha256=sha256_file(resolved_policy),
        source_profile_sha256=sha256_file(resolved_profile),
        ground_level_m=float(source_profile["geometry"]["ground"]["level_m"]),
        travel_tangent_basis=travel_tangent_basis,
        travel_tangent_basis_source=travel_tangent_basis_source,
        travel_tangent_basis_sha256=travel_tangent_basis_sha256,
        lateral_axis_basis=lateral_axis_basis,
        lateral_axis_basis_source=lateral_axis_basis_source,
        lateral_axis_basis_sha256=lateral_axis_basis_sha256,
        planted_window_min_frames=planted_window_min_frames,
    )
    result.report["sampling"].update(
        {
            "mode": source_profile["sampling"]["mode"],
            "source_timeline_count": extraction["timeline_count"],
            "source_timeline_start_s": extraction["timeline_start_s"],
            "source_timeline_end_s": extraction["timeline_end_s"],
            "source_duration_s": extraction["duration_s"],
            "sampling_grid": extraction["sampling_grid"],
            "skin_weight_validation": extraction["skin_weight_validation"],
            "mask_counts": extraction["mask_counts"],
        }
    )
    for side in ("left", "right"):
        result.report["measured"]["feet"][side]["mask"].update(
            {
                "weight_threshold": extraction["mask_counts"][side]["weight_threshold"],
                "sole_vertex_indices": extraction["mask_counts"][side]["sole_vertex_indices"],
                "toe_vertex_indices": extraction["mask_counts"][side]["toe_vertex_indices"],
            }
        )
    result.report["source"]["profile_path"] = str(
        resolved_profile.relative_to(root_resolved).as_posix()
    )
    result.report["policy"]["path"] = str(
        resolved_policy.relative_to(root_resolved).as_posix()
    )
    ensure_finite(result.report, label="contact/gauge GLB report")
    return ContactGaugeResult(report=result.report, report_sha256=canonical_hash(result.report))


__all__ = [
    "ContactGaugeResult",
    "POLICY_SCHEMA",
    "POLICY_SCHEMA_V2",
    "REPORT_SCHEMA",
    "SOURCE_SCHEMA",
    "analyze_frame_sequence",
    "analyze_glb",
    "load_contact_gauge_source",
    "load_narrow_gauge_policy",
]
