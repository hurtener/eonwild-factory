"""Strict JSON admission for the first V9 contract slice."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..errors import ContractError
from ..hashing import sha256_file
from .v9_models import (
    CANONICAL_COORDINATE_SYSTEM,
    CANONICAL_FAMILY,
    V9_SCHEMA_IDS,
    canonical_hash,
    ensure_finite,
)


SCHEMA_FILES = {
    V9_SCHEMA_IDS["intent"]: "motion-intent.v1.schema.json",
    V9_SCHEMA_IDS["program"]: "motion-program.v1.schema.json",
    V9_SCHEMA_IDS["body"]: "body-instance-profile.v1.schema.json",
    V9_SCHEMA_IDS["contact"]: "contact-state.v1.schema.json",
    V9_SCHEMA_IDS["plan"]: "centroidal-contact-plan.v1.schema.json",
    V9_SCHEMA_IDS["evidence"]: "stationary-support-evidence.v1.schema.json",
}


def default_repository() -> Path:
    return Path(__file__).resolve().parents[3]


def _reject_non_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


def _parse_json_float(value: str) -> float:
    """Parse JSON decimals without allowing exponent overflow to become inf."""

    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number {value} is not finite")
    return parsed


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_non_json_constant,
            parse_float=_parse_json_float,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read V9 JSON contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"V9 contract root must be an object: {path}")
    return value


def _format_errors(errors: Sequence[Any]) -> str:
    return "; ".join(
        f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in errors
    )


def _require_canonical_coordinate(document: Mapping[str, Any], *, label: str) -> None:
    coordinate = document.get("coordinate_system")
    if coordinate != CANONICAL_COORDINATE_SYSTEM:
        raise ContractError(
            f"{label}: coordinate system must explicitly use metres, seconds, kilograms, right-handed Y-up, forward -Z"
        )


def _require_grounded_intent(document: Mapping[str, Any], *, label: str) -> None:
    desired = document["desired_motion"]
    condition = document["condition"]
    velocity = document["current_state"]["linear_velocity_mps"]
    if desired["kind"] != "stationary_support":
        raise ContractError(f"{label}: only stationary_support is admitted by this slice")
    if condition["grounded"] is not True or condition["allow_airborne"] is not False:
        raise ContractError(f"{label}: stationary support must be grounded and non-airborne")
    if any(abs(float(value)) > 1e-12 for value in velocity):
        raise ContractError(f"{label}: stationary support requires zero current velocity")
    if document["environment"]["gravity_mps2"] != [0.0, -9.81, 0.0]:
        raise ContractError(f"{label}: stationary support requires canonical gravity [0,-9.81,0]")
    if document["environment"]["surface_normal"] != [0.0, 1.0, 0.0]:
        raise ContractError(f"{label}: stationary support requires canonical ground normal")


def _require_body_semantics(document: Mapping[str, Any], *, label: str) -> None:
    if document["family"] != CANONICAL_FAMILY:
        raise ContractError(
            f"{label}: family {document['family']!r} is not the canonical V9 family"
        )
    segments = document["segments"]
    ids = [segment["id"] for segment in segments]
    if len(ids) != len(set(ids)):
        raise ContractError(f"{label}: segment IDs must be unique")
    if document["segment_com_frame"] != "body":
        raise ContractError(f"{label}: segment COM points must declare the common body frame")
    parent_by_id = {segment["id"]: segment["parent_id"] for segment in segments}
    roots = [segment_id for segment_id, parent in parent_by_id.items() if parent is None]
    if len(roots) != 1:
        raise ContractError(f"{label}: topology must contain exactly one root segment")
    for segment_id, parent in parent_by_id.items():
        if parent == segment_id:
            raise ContractError(f"{label}: segment {segment_id!r} cannot parent itself")
        if parent is not None and parent not in parent_by_id:
            raise ContractError(
                f"{label}: segment {segment_id!r} references missing parent {parent!r}"
            )
    for segment_id in parent_by_id:
        visited: set[str] = set()
        current: str | None = segment_id
        while current is not None:
            if current in visited:
                raise ContractError(f"{label}: segment topology contains a cycle")
            visited.add(current)
            current = parent_by_id[current]
    mass = document["mass"]
    fractions = [float(segment["mass_fraction"]) for segment in segments]
    fraction_sum = math.fsum(fractions)
    if not math.isclose(fraction_sum, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ContractError(f"{label}: segment mass fractions must sum to exactly one within 1e-9")
    if not math.isclose(
        float(mass["mass_fraction_sum"]), fraction_sum, rel_tol=0.0, abs_tol=1e-9
    ):
        raise ContractError(f"{label}: declared mass_fraction_sum does not match segments")
    policy = mass["absolute_policy"]
    if policy == "normalized_only":
        if mass["absolute_dynamics_enabled"] is not False or mass["total_mass_kg"] is not None:
            raise ContractError(
                f"{label}: normalized-only profiles cannot enable absolute dynamics or declare kilograms"
            )
    elif policy == "fixture_absolute_allowed":
        if mass["absolute_dynamics_enabled"] is not True or not isinstance(
            mass["total_mass_kg"], (int, float)
        ):
            raise ContractError(f"{label}: absolute fixture policy requires a positive reviewed mass")
        provenance = document["provenance"]
        if (
            provenance["kind"] != "synthetic_fixture"
            or provenance["status"] != "fixture"
            or provenance["scientific_claims"] is not False
        ):
            raise ContractError(
                f"{label}: absolute dynamics require explicit synthetic fixture provenance"
            )
    else:
        raise ContractError(f"{label}: unknown absolute dynamics policy")


def _require_program_semantics(document: Mapping[str, Any], *, label: str) -> None:
    if document["kind"] != "stationary_support":
        raise ContractError(f"{label}: program kind is not admitted by this slice")
    if document["invariants"] != {
        "grounded_only": True,
        "airborne_allowed": False,
        "zero_velocity": True,
    }:
        raise ContractError(f"{label}: program invariants must be grounded and zero-velocity")
    effectors = [
        effector
        for phase in document["phase_template"]
        for effector in phase["contact_effectors"]
    ]
    if len(effectors) != len(set(effectors)):
        raise ContractError(f"{label}: program contact effectors must be unique")


def _require_contact_semantics(document: Mapping[str, Any], *, label: str) -> None:
    if document["state"] != "loaded":
        raise ContractError(f"{label}: only loaded grounded contacts are admitted")
    if document["patch"]["frame"] != "body":
        raise ContractError(f"{label}: contact patch frame must be the declared body frame")
    if document["patch"]["normal"] != [0.0, 1.0, 0.0]:
        raise ContractError(f"{label}: contact normal must be canonical ground normal")


def _require_plan_semantics(document: Mapping[str, Any], *, label: str) -> None:
    contacts = document["contacts"]
    if len({contact["effector"] for contact in contacts}) != len(contacts):
        raise ContractError(f"{label}: plan contact effectors must be unique")
    if any(contact["state"] != "loaded" for contact in contacts):
        raise ContractError(f"{label}: plan contains an unloaded contact")
    if any(contact["patch"]["frame"] != "body" for contact in contacts):
        raise ContractError(f"{label}: plan contact patch frames must be the body frame")
    if any(contact["patch"]["normal"] != [0.0, 1.0, 0.0] for contact in contacts):
        raise ContractError(f"{label}: plan contact normals must be canonical ground normals")
    load_sum = math.fsum(float(contact["load_fraction"]) for contact in contacts)
    if not math.isclose(load_sum, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ContractError(f"{label}: plan contact loads must sum to one within 1e-9")
    expected_effectors = sorted(contact["effector"] for contact in contacts)
    support = document["support"]
    if sorted(support["contact_effectors"]) != expected_effectors:
        raise ContractError(f"{label}: support effectors do not match contacts")
    if support["normal"] != [0.0, 1.0, 0.0]:
        raise ContractError(f"{label}: support normal must be canonical ground normal")
    if support["contact_centroid_frame"] != "body":
        raise ContractError(f"{label}: contact centroid frame must be the body frame")
    if support["evaluation"] != "bookkeeping_only":
        raise ContractError(f"{label}: support evaluation is not a physical feasibility proof")
    if document["gravity_mps2"] != [0.0, -9.81, 0.0]:
        raise ContractError(f"{label}: plan gravity must be canonical [0,-9.81,0]")
    centroidal = document["centroidal_state"]
    if centroidal["com_frame"] != "body":
        raise ContractError(f"{label}: COM must remain explicitly in the body frame")
    feasibility = document["feasibility"]
    if feasibility["physics_evaluated"] is not False:
        raise ContractError(f"{label}: stationary support physics must remain unevaluated")
    if centroidal["mass_mode"] == "normalized":
        if centroidal["mass_kg"] is not None or feasibility["absolute_dynamics_enabled"]:
            raise ContractError(f"{label}: normalized plan cannot claim absolute mass or dynamics")
    elif centroidal["mass_mode"] == "absolute":
        if centroidal["mass_kg"] is None or not feasibility["absolute_dynamics_enabled"]:
            raise ContractError(f"{label}: absolute plan requires enabled absolute fixture dynamics")
        provenance = document["provenance"]
        if (
            provenance["status"] != "fixture"
            or provenance["kind"] != "synthetic_fixture"
            or provenance["scientific_claims"] is not False
        ):
            raise ContractError(
                f"{label}: absolute dynamics require explicit synthetic fixture provenance"
            )


def _require_evidence_manifest(
    document: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    repository: Path,
    label: str,
) -> None:
    manifest = document["evidence"]["input_manifest"]
    required = {"intent", "program", "body"}
    if not required.issubset(manifest):
        raise ContractError(f"{label}: input manifest must include intent, program, and body")
    contact_keys = sorted(
        key[len("contact_") :]
        for key in manifest
        if key.startswith("contact_")
    )
    if len(contact_keys) < 2 or any(not key for key in contact_keys):
        raise ContractError(
            f"{label}: input manifest must include at least two uniquely named contacts"
        )
    root = repository.resolve()
    expected_schemas = {
        "intent": V9_SCHEMA_IDS["intent"],
        "program": V9_SCHEMA_IDS["program"],
        "body": V9_SCHEMA_IDS["body"],
    }
    for name, entry in manifest.items():
        path = (root / entry["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ContractError(
                f"{label}: input manifest path is outside repository or missing: {name}"
            )
        if sha256_file(path) != entry["sha256"]:
            raise ContractError(f"{label}: input manifest hash mismatch: {name}")

    source_documents = {
        name: load_v9_document(
            (root / entry["path"]).resolve(),
            repository=root,
            expected_schema=(
                V9_SCHEMA_IDS["contact"]
                if name.startswith("contact_")
                else expected_schemas[name]
            ),
        )
        for name, entry in manifest.items()
    }
    if source_documents["intent"]["id"] != plan["intent_id"]:
        raise ContractError(f"{label}: intent manifest identity does not match plan")
    if source_documents["program"]["id"] != plan["program_id"]:
        raise ContractError(f"{label}: program manifest identity does not match plan")
    if source_documents["body"]["profile_id"] != plan["body_profile_id"]:
        raise ContractError(f"{label}: body manifest identity does not match plan")

    plan_contacts = {contact["effector"]: contact for contact in plan["contacts"]}
    manifest_contacts = {
        name[len("contact_") :]: source_documents[name]
        for name in manifest
        if name.startswith("contact_")
    }
    if set(manifest_contacts) != set(plan_contacts):
        raise ContractError(f"{label}: contact manifest set does not match plan contacts")
    for effector, source in manifest_contacts.items():
        plan_contact = plan_contacts[effector]
        if source["effector"] != effector or source["state"] != plan_contact["state"]:
            raise ContractError(
                f"{label}: contact manifest identity/state does not match plan: {effector}"
            )
        if source["id"] != plan_contact["contact_id"]:
            raise ContractError(
                f"{label}: contact manifest source identity does not match plan: {effector}"
            )
        if (
            source["time_s"] != plan_contact["time_s"]
            or source["load_fraction"] != plan_contact["load_fraction"]
            or source["patch"] != plan_contact["patch"]
        ):
            raise ContractError(
                f"{label}: contact manifest payload does not match plan: {effector}"
            )


def _require_semantics(document: Mapping[str, Any], *, label: str) -> None:
    schema = document["schema"]
    if schema != V9_SCHEMA_IDS["evidence"]:
        _require_canonical_coordinate(document, label=label)
    if schema == V9_SCHEMA_IDS["intent"]:
        _require_grounded_intent(document, label=label)
    elif schema == V9_SCHEMA_IDS["program"]:
        _require_program_semantics(document, label=label)
    elif schema == V9_SCHEMA_IDS["body"]:
        _require_body_semantics(document, label=label)
    elif schema == V9_SCHEMA_IDS["contact"]:
        _require_contact_semantics(document, label=label)
    elif schema == V9_SCHEMA_IDS["plan"]:
        _require_plan_semantics(document, label=label)


def validate_v9_document(
    document: Mapping[str, Any],
    *,
    repository: Path | None = None,
    expected_schema: str | None = None,
    label: str = "V9 contract",
) -> dict[str, Any]:
    """Validate and return a canonical V9 document without coercion."""

    if not isinstance(document, Mapping):
        raise ContractError(f"{label}: contract root must be an object")
    ensure_finite(document, label=f"{label} before schema admission")
    schema_id = document.get("schema")
    if not isinstance(schema_id, str) or not schema_id:
        raise ContractError(f"{label}: missing schema; V9 documents must be versioned")
    if expected_schema is not None and schema_id != expected_schema:
        raise ContractError(
            f"{label}: expected schema {expected_schema!r}, got {schema_id!r}"
        )
    filename = SCHEMA_FILES.get(schema_id)
    if filename is None:
        raise ContractError(f"{label}: unknown V9 schema {schema_id!r}")
    root = default_repository() if repository is None else repository
    schema_path = root / "schemas/motion/v9" / filename
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label}: cannot read schema {schema_path}: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(document)),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ContractError(f"{label}: schema validation failed: {_format_errors(errors)}")
    normalized = dict(document)
    ensure_finite(normalized, label=f"{label} after schema admission")
    _require_semantics(normalized, label=label)
    if schema_id == V9_SCHEMA_IDS["evidence"]:
        plan = normalized["plan"]
        validate_v9_document(
            plan,
            repository=root,
            expected_schema=V9_SCHEMA_IDS["plan"],
            label=f"{label}.plan",
        )
        _require_evidence_manifest(normalized, plan, repository=root, label=label)
        evidence = normalized["evidence"]
        if evidence["plan_sha256"] != canonical_hash(plan):
            raise ContractError(f"{label}: evidence plan hash does not match embedded plan")
        evidence_without_hash = dict(evidence)
        evidence_without_hash.pop("evidence_sha256", None)
        if evidence["evidence_sha256"] != canonical_hash(evidence_without_hash):
            raise ContractError(f"{label}: evidence hash does not match evidence fields")
    return normalized


def load_v9_document(
    path: Path,
    *,
    repository: Path | None = None,
    expected_schema: str | None = None,
) -> dict[str, Any]:
    document = read_json(path)
    return validate_v9_document(
        document,
        repository=repository,
        expected_schema=expected_schema,
        label=str(path),
    )
