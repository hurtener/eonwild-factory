"""Strict bindings for licensed, raw authored-motion reference inputs."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..errors import ContractError
from .io import digest, locked_file


SCHEMA = "eonwild.motion.authored-material-reference.v1"
MODEL = "authored_material_contact.v1"
RETIME = "phase_preserving.v1"
CLEARANCE_SCHEMA = "eonwild.motion.authored-material-clearance-policy.v1"


def _decode_descriptor(raw: bytes) -> Mapping[str, Any]:
    import json
    try:
        value = json.loads(
            raw,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ContractError(f"non-finite authored reference JSON: {token}")
            ),
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(f"authored material reference is invalid JSON: {exc}") from exc
    return validate_reference(value)


def validate_clearance_policy(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "schema", "id", "version", "model",
        "maximum_clearance_body_heights", "classification",
    }:
        raise ContractError("authored material clearance policy shape is invalid")
    amount = value.get("maximum_clearance_body_heights")
    if (
        value.get("schema") != CLEARANCE_SCHEMA
        or value.get("model") != "body_height_fraction.v1"
        or not isinstance(value.get("id"), str)
        or not value["id"]
        or type(value.get("version")) is not int
        or value["version"] < 1
        or isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or not math.isfinite(float(amount))
        or not 0 < float(amount)
        or value.get("classification") != "source_backed_engineering_candidate"
    ):
        raise ContractError("authored material clearance policy is unsupported")
    return value


def validate_reference(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "schema", "id", "version", "source", "capsule", "adapter"
    }:
        raise ContractError("authored material reference shape is invalid")
    if value.get("schema") != SCHEMA:
        raise ContractError("unsupported authored material reference schema")
    if not isinstance(value.get("id"), str) or not value["id"]:
        raise ContractError("authored material reference id is required")
    if type(value.get("version")) is not int or value["version"] < 1:
        raise ContractError("authored material reference version is invalid")
    for name in ("source", "capsule"):
        binding = value[name]
        if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
            raise ContractError(f"authored material reference {name} binding is invalid")
    if value["adapter"] != {
        "model": MODEL, "version": 1, "retime_policy": RETIME
    }:
        raise ContractError("authored material reference adapter is unsupported")
    return value


@dataclass(frozen=True)
class AcquiredReferenceInputs:
    descriptor_bytes: bytes
    source_bytes: bytes
    capsule_bytes: bytes

    def __post_init__(self) -> None:
        descriptor = self.descriptor
        if (
            digest(self.source_bytes) != descriptor["source"]["sha256"]
            or digest(self.capsule_bytes) != descriptor["capsule"]["sha256"]
        ):
            raise ContractError(
                "authored material reference payload differs from its descriptor snapshot"
            )

    @property
    def descriptor(self) -> Mapping[str, Any]:
        return _decode_descriptor(self.descriptor_bytes)

    @property
    def binding(self) -> dict[str, Any]:
        value = self.descriptor
        return {
            "identity": {key: value[key] for key in ("id", "version")},
            "descriptor_sha256": digest(self.descriptor_bytes),
            "source_sha256": digest(self.source_bytes),
            "capsule_sha256": digest(self.capsule_bytes),
            "model": value["adapter"]["model"],
            "retime_policy": value["adapter"]["retime_policy"],
        }


def resolve_reference(root: Path, binding: Mapping[str, Any]) -> AcquiredReferenceInputs:
    descriptor_path = locked_file(root, binding)
    descriptor_bytes = descriptor_path.read_bytes()
    # Parse the exact captured bytes. A second descriptor read would split the
    # authority for its nested source and capsule bindings under replacement.
    descriptor = _decode_descriptor(descriptor_bytes)
    source_path = locked_file(root, descriptor["source"])
    capsule_path = locked_file(root, descriptor["capsule"])
    result = AcquiredReferenceInputs(
        descriptor_bytes=descriptor_bytes,
        source_bytes=source_path.read_bytes(),
        capsule_bytes=capsule_path.read_bytes(),
    )
    if (
        result.binding["descriptor_sha256"] != binding["sha256"]
        or result.binding["source_sha256"] != descriptor["source"]["sha256"]
        or result.binding["capsule_sha256"] != descriptor["capsule"]["sha256"]
    ):
        raise ContractError("authored material reference changed during resolution")
    return result


def packaged_reference(path: Path) -> AcquiredReferenceInputs:
    return AcquiredReferenceInputs(
        descriptor_bytes=(path / "authored-material-reference.json").read_bytes(),
        source_bytes=(path / "authored-material-source.bin").read_bytes(),
        capsule_bytes=(path / "authored-material-path.json").read_bytes(),
    )
