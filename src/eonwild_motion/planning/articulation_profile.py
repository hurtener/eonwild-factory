"""Versioned support/swing articulation guardrails for gait solvers.

Profiles are semantic inputs, never species branches.  Their evidence labels
state what the numbers mean; the word ``hard`` only means fail-closed to the
solver and must not be read as a fossil-derived range-of-motion claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import math
from typing import Any, Mapping

from ..dynamics.capacity import JointEnvelope
from ..errors import ContractError

SCHEMA = "eonwild.motion.v9.articulation-profile.v1"
CLASSIFICATION = "engineering_guardrails_not_biological_rom"
ANGLE_CONVENTIONS = {
    "hip_sagittal_degrees": "world sagittal thigh inclination from down: negative rearward; positive forward",
    "knee_interior_degrees": "0 fully folded; 180 straight",
    "ankle_interior_degrees": "0 fully folded; 180 straight",
}
_JOINTS = tuple(ANGLE_CONVENTIONS)
_EVIDENCE_STATUSES = {
    "unresolved",
    "engineering_selected",
    "comparative_anatomy_informed",
    "synthetic_test_only",
}


@dataclass(frozen=True)
class ArticulationProfile:
    profile_id: str
    version: int
    classification: str
    angle_conventions: Mapping[str, str]
    evidence: Mapping[str, Any]
    support: Mapping[str, JointEnvelope]
    swing: Mapping[str, JointEnvelope]

    def phase(self, *, contact: bool) -> Mapping[str, JointEnvelope]:
        if type(contact) is not bool:
            raise ContractError("articulation phase selection requires boolean contact")
        return self.support if contact else self.swing

    def effective(self, *, contact: bool, swing_phase: Any) -> Mapping[str, JointEnvelope]:
        """C2 release/approach blend from loaded to free-swing guardrails."""
        if type(contact) is not bool:
            raise ContractError("articulation phase selection requires boolean contact")
        if contact:
            support_weight = 1.0
        else:
            u = _finite(swing_phase, "articulation swing phase")
            if not -1e-12 <= u <= 1.0 + 1e-12:
                raise ContractError("articulation swing phase must lie within 0..1")
            u = max(0.0, min(1.0, u))
            x = max(0.0, min(1.0, min(u, 1.0 - u) / .18))
            free_weight = x * x * x * (10.0 + x * (-15.0 + 6.0 * x))
            support_weight = 1.0 - free_weight
        if support_weight == 1.0:
            return self.support
        if support_weight == 0.0:
            return self.swing
        result = {}
        for joint in _JOINTS:
            loaded, free = self.support[joint], self.swing[joint]
            def mix(a: float, b: float) -> float:
                return support_weight * a + (1.0 - support_weight) * b
            result[joint] = JointEnvelope(
                joint,
                mix(loaded.hard_min_deg, free.hard_min_deg),
                mix(loaded.hard_max_deg, free.hard_max_deg),
                mix(loaded.preferred_min_deg, free.preferred_min_deg),
                mix(loaded.preferred_max_deg, free.preferred_max_deg),
                contraction_per_load_bw=0.0,
                contraction_per_speed=0.0,
            )
        return result

    def receipt(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.profile_id,
            "version": self.version,
            "classification": self.classification,
            "angle_conventions": dict(self.angle_conventions),
            "evidence_status": self.evidence["status"],
            "limitations": list(self.evidence["limitations"]),
            "evidence": deepcopy(dict(self.evidence)),
            "solver_scope": "scalar sagittal engineering guardrails; not a pelvis-relative hip JCS or 6DoF joint model; load/speed conditioning is not implemented",
            "phase_transfer": "support guardrails blend C2 to swing guardrails over the existing 0.18 release and approach partition",
        }


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"{label} must be finite numeric")
    return float(value)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def _pair(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ContractError(f"{label} must contain exactly two degree values")
    return _finite(value[0], label), _finite(value[1], label)


def _load_envelope(raw: Any, joint: str, phase: str) -> JointEnvelope:
    required = {"hard_degrees", "preferred_degrees"}
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ContractError(f"{phase} {joint} envelope contains missing or unknown fields")
    hard = _pair(raw["hard_degrees"], f"{phase} {joint} hard_degrees")
    preferred = _pair(raw["preferred_degrees"], f"{phase} {joint} preferred_degrees")
    if joint != "hip_sagittal_degrees" and not (0.0 <= hard[0] < hard[1] <= 180.0):
        raise ContractError(f"{phase} {joint} interior angles must lie within 0..180 degrees")
    if joint == "hip_sagittal_degrees" and not (-180.0 < hard[0] < hard[1] < 180.0):
        raise ContractError(f"{phase} hip sagittal angles must lie within -180..180 degrees")
    return JointEnvelope(joint, *hard, *preferred,
                         contraction_per_load_bw=0.0,
                         contraction_per_speed=0.0)


def _load_phase(raw: Any, phase: str) -> dict[str, JointEnvelope]:
    if not isinstance(raw, Mapping) or set(raw) != set(_JOINTS):
        raise ContractError(f"{phase} articulation envelope must define exactly {', '.join(_JOINTS)}")
    return {joint: _load_envelope(raw[joint], joint, phase) for joint in _JOINTS}


def load_articulation_profile(raw: Any) -> ArticulationProfile:
    required = {"schema", "id", "version", "classification", "angle_conventions", "evidence", "envelopes"}
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ContractError("articulation profile contains missing or unknown fields")
    if raw["schema"] != SCHEMA or raw["classification"] != CLASSIFICATION:
        raise ContractError("unsupported articulation profile schema or classification")
    profile_id = _text(raw["id"], "articulation profile id")
    if type(raw["version"]) is not int or raw["version"] < 1:
        raise ContractError("articulation profile version must be a positive integer")
    conventions = raw["angle_conventions"]
    if not isinstance(conventions, Mapping) or dict(conventions) != ANGLE_CONVENTIONS:
        raise ContractError("articulation profile angle conventions are missing or ambiguous")
    evidence = raw["evidence"]
    if not isinstance(evidence, Mapping) or set(evidence) != {"status", "sources", "limitations"}:
        raise ContractError("articulation profile evidence contains missing or unknown fields")
    status = _text(evidence["status"], "articulation evidence status")
    if status not in _EVIDENCE_STATUSES:
        raise ContractError("unsupported articulation evidence status")
    if not isinstance(evidence["sources"], list) or not evidence["sources"]:
        raise ContractError("articulation evidence requires at least one scoped source")
    for source in evidence["sources"]:
        if not isinstance(source, Mapping) or set(source) != {"citation", "locator", "scope"}:
            raise ContractError("articulation evidence source contains missing or unknown fields")
        for field in source:
            _text(source[field], f"articulation evidence source {field}")
    if not isinstance(evidence["limitations"], list) or not evidence["limitations"]:
        raise ContractError("articulation evidence requires explicit limitations")
    for limitation in evidence["limitations"]:
        _text(limitation, "articulation evidence limitation")
    envelopes = raw["envelopes"]
    if not isinstance(envelopes, Mapping) or set(envelopes) != {"support", "swing"}:
        raise ContractError("articulation envelopes must separate support and swing")
    return ArticulationProfile(profile_id, raw["version"], raw["classification"],
                               dict(conventions), dict(evidence),
                               _load_phase(envelopes["support"], "support"),
                               _load_phase(envelopes["swing"], "swing"))


__all__ = ["ANGLE_CONVENTIONS", "ArticulationProfile", "CLASSIFICATION", "SCHEMA", "load_articulation_profile"]
