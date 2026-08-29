"""A small grounded contact/centroidal plan for the V9 contract slice.

This is contract composition and deterministic bookkeeping.  It is not a
whole-body dynamics solver and it intentionally does not emit animation data.
Segment COM points are already-resolved common body-frame inputs; this slice
does not apply hierarchy or world transforms.
"""

from __future__ import annotations

import json
from math import fsum, isclose
from pathlib import Path
from typing import Any, Sequence

from ..contracts.v9_loader import (
    default_repository,
    load_v9_document,
    validate_v9_document,
)
from ..contracts.v9_models import (
    BodyInstanceProfile,
    ContactState,
    MotionIntent,
    MotionProgram,
    StationarySupportResult,
    V9_SCHEMA_IDS,
    canonical_hash,
    ensure_finite,
)
from ..errors import ContractError
from ..hashing import sha256_file


def _close(left: float, right: float, *, label: str) -> None:
    if not isclose(left, right, rel_tol=0.0, abs_tol=1e-9):
        raise ContractError(f"{label}: expected {right}, got {left}")


def _check_coordinate_documents(
    intent: MotionIntent,
    program: MotionProgram,
    body: BodyInstanceProfile,
    contacts: Sequence[ContactState],
) -> None:
    expected = intent.coordinate_system.as_dict()
    documents = [
        ("program", program.coordinate_system.as_dict()),
        ("body profile", body.coordinate_system.as_dict()),
        *[(f"contact {contact.id}", contact.coordinate_system.as_dict()) for contact in contacts],
    ]
    for label, coordinate in documents:
        if coordinate != expected:
            raise ContractError(f"{label}: coordinate system does not match intent")


def _check_inputs(
    intent: MotionIntent,
    program: MotionProgram,
    body: BodyInstanceProfile,
    contacts: Sequence[ContactState],
) -> None:
    if intent.kind != program.kind:
        raise ContractError("intent and program motion kinds do not match")
    if not intent.grounded or intent.allow_airborne:
        raise ContractError("stationary support cannot admit airborne state")
    if not program.invariants["grounded_only"] or program.invariants["airborne_allowed"]:
        raise ContractError("stationary support program must remain grounded")
    if not contacts:
        raise ContractError("stationary support requires at least two loaded contacts")
    phase_duration = fsum(phase.duration_s for phase in program.phases)
    _close(phase_duration, intent.duration_s, label="program duration")
    declared_effectors = {
        effector for phase in program.phases for effector in phase.contact_effectors
    }
    actual_effectors = {contact.effector for contact in contacts}
    if len(actual_effectors) < 2:
        raise ContractError("stationary support requires at least two distinct effectors")
    if actual_effectors != declared_effectors:
        raise ContractError("program and contact effectors do not match")
    if len(actual_effectors) != len(contacts):
        raise ContractError("contact effectors must be unique")
    for contact in contacts:
        if contact.time_s > intent.duration_s:
            raise ContractError(f"contact {contact.id}: time is outside intent duration")
        if contact.state != "loaded" or contact.normal != (0.0, 1.0, 0.0):
            raise ContractError(f"contact {contact.id}: unsupported grounded state")
    _close(
        fsum(contact.load_fraction for contact in contacts),
        1.0,
        label="contact load fractions",
    )


def _centroidal_state(body: BodyInstanceProfile) -> tuple[list[float], float | None]:
    com = [
        # The profile contract guarantees that these are common body-frame
        # points.  A world-frame transform belongs to a later solver stage.
        fsum(segment.mass_fraction * segment.com_body_m[index] for segment in body.segments)
        for index in range(3)
    ]
    mass = body.total_mass_kg if body.absolute_dynamics_enabled else None
    return com, mass


def _contact_payload(contact: ContactState) -> dict[str, Any]:
    return {
        "contact_id": contact.id,
        "effector": contact.effector,
        "state": contact.state,
        "time_s": contact.time_s,
        "load_fraction": contact.load_fraction,
        "patch": {
            "frame": "body",
            "point_m": list(contact.point_m),
            "normal": list(contact.normal),
            "friction_coefficient": contact.friction_coefficient,
        },
    }


def build_stationary_support_plan(
    intent_path: Path,
    program_path: Path,
    body_path: Path,
    contact_paths: Sequence[Path],
    *,
    repository: Path | None = None,
    report_path: Path | None = None,
) -> StationarySupportResult:
    """Resolve strict inputs and return a deterministic grounded plan.

    ``report_path`` is optional so callers can keep generated evidence in a
    temporary/build directory.  No repository release state is written.
    """

    root = default_repository() if repository is None else repository
    intent_document = load_v9_document(
        intent_path,
        repository=root,
        expected_schema=V9_SCHEMA_IDS["intent"],
    )
    program_document = load_v9_document(
        program_path,
        repository=root,
        expected_schema=V9_SCHEMA_IDS["program"],
    )
    body_document = load_v9_document(
        body_path,
        repository=root,
        expected_schema=V9_SCHEMA_IDS["body"],
    )
    if len(contact_paths) < 2:
        raise ContractError("stationary support requires at least two contact documents")
    contact_documents = [
        load_v9_document(
            path,
            repository=root,
            expected_schema=V9_SCHEMA_IDS["contact"],
        )
        for path in contact_paths
    ]

    intent = MotionIntent.from_document(intent_document)
    program = MotionProgram.from_document(program_document)
    body = BodyInstanceProfile.from_document(body_document)
    contacts = tuple(ContactState.from_document(document) for document in contact_documents)
    _check_coordinate_documents(intent, program, body, contacts)
    _check_inputs(intent, program, body, contacts)

    ordered_contacts = tuple(sorted(contacts, key=lambda contact: contact.effector))
    com, mass = _centroidal_state(body)
    contact_centroid = [
        fsum(contact.load_fraction * contact.point_m[index] for contact in ordered_contacts)
        for index in range(3)
    ]
    plan: dict[str, Any] = {
        "schema": V9_SCHEMA_IDS["plan"],
        "plan_id": f"{program.id}:{intent.id}:{body.profile_id}",
        "intent_id": intent.id,
        "program_id": program.id,
        "body_profile_id": body.profile_id,
        "coordinate_system": intent.coordinate_system.as_dict(),
        "gravity_mps2": [0.0, -9.81, 0.0],
        "grounded": True,
        "contacts": [_contact_payload(contact) for contact in ordered_contacts],
        "centroidal_state": {
            "mass_mode": body.mass_mode,
            "mass_kg": mass,
            "com_frame": "body",
            "com_m": com,
            "linear_momentum_kg_mps": [0.0, 0.0, 0.0],
            "angular_momentum_kg_m2ps": [0.0, 0.0, 0.0],
        },
        "support": {
            "contact_effectors": [contact.effector for contact in ordered_contacts],
            "net_load_fraction": 1.0,
            "normal": [0.0, 1.0, 0.0],
            "contact_centroid_m": contact_centroid,
            "contact_centroid_frame": "body",
            "evaluation": "bookkeeping_only",
        },
        "feasibility": {
            "status": "grounded_support_only",
            "absolute_dynamics_enabled": body.absolute_dynamics_enabled,
            "physics_evaluated": False,
            "reason": (
                "normalized mass; absolute dynamics disabled by profile policy"
                if not body.absolute_dynamics_enabled
                else "synthetic fixture absolute mass; stationary support only"
            ),
        },
        "provenance": {
            "source": "eonwild_motion_v9_stationary_support",
            "status": body.provenance_status,
            "kind": body_document["provenance"]["kind"],
            "scientific_claims": False,
        },
    }
    plan = validate_v9_document(
        plan,
        repository=root,
        expected_schema=V9_SCHEMA_IDS["plan"],
        label="stationary support plan",
    )
    def manifest_entry(path: Path) -> dict[str, str]:
        resolved = path.resolve()
        repository_root = root.resolve()
        try:
            relative = resolved.relative_to(repository_root).as_posix()
        except ValueError as exc:
            raise ContractError(
                f"input {path} must be inside the repository for reproducible evidence"
            ) from exc
        return {"path": relative, "sha256": sha256_file(resolved)}

    input_manifest: dict[str, dict[str, str]] = {
        "intent": manifest_entry(intent_path),
        "program": manifest_entry(program_path),
        "body": manifest_entry(body_path),
    }
    contact_path_by_effector = {
        document["effector"]: path
        for document, path in zip(contact_documents, contact_paths)
    }
    input_manifest.update(
        {
            f"contact_{contact.effector}": manifest_entry(
                contact_path_by_effector[contact.effector]
            )
            for contact in ordered_contacts
        }
    )
    if len(input_manifest) != 3 + len(ordered_contacts):
        raise ContractError("input manifest contact names must be unique")
    plan_sha = canonical_hash(plan)
    evidence_base: dict[str, Any] = {
        "status": "PASS",
        "scope": "contract_and_grounded_support_only",
        "plan_sha256": plan_sha,
        "input_manifest": input_manifest,
        "checks": {
            "strict_contracts": True,
            "canonical_axes": True,
            "canonical_gravity": True,
            "grounded_contacts": True,
            "deterministic_com": True,
            "body_frame_com": True,
            "support_physics_unevaluated": True,
            "absolute_dynamics_policy": True,
        },
    }
    evidence_sha = canonical_hash(evidence_base)
    evidence = {**evidence_base, "evidence_sha256": evidence_sha}
    result = StationarySupportResult(
        plan=plan,
        evidence=evidence,
        plan_sha256=plan_sha,
        evidence_sha256=evidence_sha,
    )
    if report_path is not None:
        write_stationary_support_report(result, report_path, repository=root)
    return result


def write_stationary_support_report(
    result: StationarySupportResult,
    path: Path,
    *,
    repository: Path | None = None,
) -> None:
    """Validate and write a deterministic evidence envelope to ``path``."""

    root = default_repository() if repository is None else repository
    validate_v9_document(
        result.report,
        repository=root,
        expected_schema=V9_SCHEMA_IDS["evidence"],
        label="stationary support evidence",
    )
    ensure_finite(result.report, label="stationary support report")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(
            result.report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
