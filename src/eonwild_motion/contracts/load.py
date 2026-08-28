from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..errors import ContractError


SCHEMA_FILES = {
    "eonwild.motion.semantic-rig.v1": "semantic-rig.v1.schema.json",
    "eonwild.motion.family.v1": "family.v1.schema.json",
    "eonwild.motion.species.v1": "species.v1.schema.json",
    "eonwild.motion.motion-spec.v1": "motion-spec.v1.schema.json",
    "eonwild.motion.motion-layer.v1": "motion-layer.v1.schema.json",
    "eonwild.motion.render-set.v1": "render-set.v1.schema.json",
    "eonwild.motion.release-profile.v1": "release-profile.v1.schema.json",
    "eonwild.motion.run-report.v1": "run-report.v1.schema.json",
    "eonwild.motion.promotion.v1": "promotion.v1.schema.json",
    "eonwild.motion.artifact-manifest.v1": "artifact-manifest.v1.schema.json",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"contract root must be an object: {path}")
    return value


def validate_document(
    document: dict[str, Any], *, repository: Path, label: str
) -> None:
    schema_id = document.get("schema")
    filename = SCHEMA_FILES.get(schema_id)
    if filename is None:
        raise ContractError(f"{label}: unknown schema {schema_id!r}")
    schema = read_json(repository / "schemas/motion" / filename)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ContractError(f"{label}: schema validation failed: {details}")


def load_and_validate(path: Path, *, repository: Path) -> dict[str, Any]:
    document = read_json(path)
    validate_document(document, repository=repository, label=str(path))
    return document
