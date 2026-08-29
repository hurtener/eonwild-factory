"""Explicit, fail-closed boundary for documents from the V9 handoff pack.

The handoff pack predates the canonical V9 JSON contract used by this slice.
This module intentionally does not guess at aliases, units, axes, or fields.
Callers must supply a complete, explicit top-level field map and a declared
source schema.  Values are copied without conversion; semantic validation is
performed by :mod:`v9_loader` after migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..errors import ContractError
from .v9_models import CANONICAL_COORDINATE_SYSTEM, CANONICAL_FAMILY, ensure_finite


@dataclass(frozen=True)
class ExplicitMigration:
    source_schema: str
    target_schema: str
    field_map: Mapping[str, str]


def _reject_legacy_aliases(value: Any, *, label: str) -> None:
    """Reject known V8/pack aliases instead of silently changing meaning."""

    if isinstance(value, Mapping):
        family = value.get("family")
        if family is not None and family != CANONICAL_FAMILY:
            raise ContractError(
                f"{label}: family alias {family!r} is not the canonical V9 family"
            )
        coordinates = value.get("coordinate_system")
        if coordinates is not None and coordinates != CANONICAL_COORDINATE_SYSTEM:
            raise ContractError(
                f"{label}: coordinate/units aliases require an explicit reviewed migration"
            )
        for key, child in value.items():
            _reject_legacy_aliases(child, label=f"{label}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_legacy_aliases(child, label=f"{label}[{index}]")


def migrate_document(
    document: Mapping[str, Any],
    migration: ExplicitMigration,
    *,
    label: str = "V9 migration",
) -> dict[str, Any]:
    """Apply an explicit field-only migration.

    Every source key other than ``schema`` must occur in ``field_map``.  The
    operation never fills defaults, renames an unknown field, converts units,
    or maps a family/axis alias.  A caller can then pass the returned object to
    ``load_v9_document`` for target-schema validation.
    """

    if not isinstance(document, Mapping):
        raise ContractError(f"{label}: document root must be an object")
    ensure_finite(document, label=f"{label} before migration")
    if not isinstance(migration.source_schema, str) or not migration.source_schema:
        raise ContractError(f"{label}: source schema declaration is required")
    if not isinstance(migration.target_schema, str) or not migration.target_schema:
        raise ContractError(f"{label}: target schema declaration is required")
    source_schema = document.get("schema")
    if source_schema is None:
        raise ContractError(
            f"{label}: missing schema; an explicit source schema is required"
        )
    if source_schema != migration.source_schema:
        raise ContractError(
            f"{label}: expected source schema {migration.source_schema!r}, got {source_schema!r}"
        )
    if not migration.field_map:
        raise ContractError(f"{label}: complete explicit field map is required")
    source_keys = set(document) - {"schema"}
    unmapped = sorted(source_keys - set(migration.field_map))
    if unmapped:
        raise ContractError(f"{label}: unmapped source fields: {', '.join(unmapped)}")
    destinations = list(migration.field_map.values())
    if any(not isinstance(key, str) or not key for key in destinations):
        raise ContractError(f"{label}: migration destinations must be non-empty strings")
    if len(destinations) != len(set(destinations)):
        raise ContractError(f"{label}: migration destination collision")

    _reject_legacy_aliases(document, label=label)
    result: dict[str, Any] = {"schema": migration.target_schema}
    for source_key in sorted(source_keys):
        result[migration.field_map[source_key]] = document[source_key]
    return result


def require_explicit_source_schema(
    document: Mapping[str, Any], *, label: str = "V9 migration"
) -> str:
    """Return a declared source schema, rejecting the pack's unversioned docs."""

    source_schema = document.get("schema") if isinstance(document, Mapping) else None
    if not isinstance(source_schema, str) or not source_schema:
        raise ContractError(
            f"{label}: missing schema; handoff-pack documents require an explicit migration declaration"
        )
    return source_schema
