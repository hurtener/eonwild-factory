from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from ..contracts.models import ResolvedProfile
from ..contracts.semantic import expanded_channels
from ..errors import ValidationFailure
from ..glb.container import Glb
from ..hashing import sha256_file


MAX_PACKAGE_FILE_BYTES = 100 * 1024 * 1024
REJECTED_COMPONENTS = {
    "__pycache__",
    ".cache",
    ".pytest_cache",
    "cache",
    "caches",
    "tmp",
    "temp",
    "temporary",
    "rejected",
    "rejects",
}
REJECTED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".temp", ".bak", ".rej"}


def _document_value(document: dict[str, Any], selector: str) -> Any:
    value: Any = document
    for component in selector.split("."):
        if not isinstance(value, dict) or component not in value:
            raise ValidationFailure(f"contact evidence selector missing: {selector}")
        value = value[component]
    return value


def contact_inheritance_facts(resolved: ResolvedProfile) -> dict[str, Any]:
    try:
        evidence = json.loads(resolved.contact_evidence_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"contact evidence is unreadable: {exc}") from exc
    contract = resolved.motion["invariants"]["contactContract"]
    true_facts = {
        selector: _document_value(evidence, selector)
        for selector in contract["requiredTruePaths"]
    }
    zero_facts = {
        selector: _document_value(evidence, selector)
        for selector in contract["requiredZeroPaths"]
    }
    if any(value is not True for value in true_facts.values()):
        raise ValidationFailure("required contact authority check is not true")
    if any(float(value) != 0.0 for value in zero_facts.values()):
        raise ValidationFailure("required contact authority metric is not zero")
    return {
        "status": "PASS",
        "proof": contract["proof"],
        "authority": {
            "path": str(resolved.contact_evidence_path),
            "sha256": resolved.contact_evidence_sha256,
        },
        "requiredTrue": true_facts,
        "requiredZero": zero_facts,
        "protectedChannelsByteExact": True,
    }


def _rejected(relative: Path) -> bool:
    parts = [part.lower() for part in relative.parts]
    return (
        any(part in REJECTED_COMPONENTS for part in parts)
        or relative.suffix.lower() in REJECTED_SUFFIXES
        or any(
            part.startswith(("rejected-", "rejected_", "temp-", "temp_"))
            for part in parts
        )
    )


def validate_source_package(root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text())
    inventory = manifest.get("inventory")
    if not isinstance(inventory, dict) or not manifest.get("selfHashConvention"):
        raise ValidationFailure("source release manifest inventory is invalid")
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.resolve() != manifest_path.resolve()
    ]
    actual = {str(path.relative_to(root)) for path in files}
    expected = set(inventory)
    forbidden = sorted(
        str(path.relative_to(root))
        for path in files
        if _rejected(path.relative_to(root))
    )
    oversized = sorted(
        str(path.relative_to(root))
        for path in files
        if path.stat().st_size > MAX_PACKAGE_FILE_BYTES
    )
    mismatches = []
    for relative, facts in inventory.items():
        path = root / relative
        if not path.is_file() or sha256_file(path) != facts.get("sha256"):
            mismatches.append(relative)
    checks = {
        "inventoryExact": actual == expected,
        "inventoryHashes": not mismatches,
        "noForbiddenPaths": not forbidden,
        "noOversizedFiles": not oversized,
    }
    if not all(checks.values()):
        raise ValidationFailure(
            "source package failed: "
            + json.dumps(
                {
                    "checks": checks,
                    "missing": sorted(expected - actual),
                    "unexpected": sorted(actual - expected),
                    "hashMismatches": mismatches,
                    "forbidden": forbidden,
                    "oversized": oversized,
                },
                sort_keys=True,
            )
        )
    return {
        "checks": checks,
        "inventoryCount": len(inventory),
        "forbiddenPaths": forbidden,
        "oversizedFiles": oversized,
    }


def _parent_selector(rig: dict[str, Any], selector: str) -> str:
    roles = rig["roles"]
    if selector == "spine_parent":
        return rig["spineParent"]
    if selector.startswith("neck:"):
        try:
            return roles["neck"][int(selector.split(":", 1)[1])]
        except (ValueError, IndexError) as exc:
            raise ValidationFailure(f"invalid parent selector: {selector}") from exc
    value = roles.get(selector)
    if not isinstance(value, str):
        raise ValidationFailure(f"invalid parent selector: {selector}")
    return value


def validate_animation_contract(glb: Glb, rig: dict, motion: dict) -> dict[str, Any]:
    roles = rig["roles"]
    expected = rig["expectedParents"]
    pairs = [
        (roles["pelvis"], _parent_selector(rig, expected["pelvis"])),
        (roles["chest"], _parent_selector(rig, expected["chest"])),
        *[
            (name, _parent_selector(rig, selector))
            for name, selector in zip(roles["neck"], expected["neck"])
        ],
        (roles["head"], _parent_selector(rig, expected["head"])),
    ]
    if len(roles["neck"]) != len(expected["neck"]):
        raise ValidationFailure("neck parent contract length mismatch")
    for name, parent in pairs:
        if glb.node_parent_name(name) != parent:
            raise ValidationFailure(f"hierarchy contract mismatch for {name}")
    contract = rig["accessorContract"]
    if contract["commonTimeline"] is not True:
        raise ValidationFailure("commonTimeline must be true")
    clip_facts = {}
    for clip in motion["clips"]:
        timeline = None
        channel_count = 0
        for name, sampler in glb.rotation_channels(clip["name"]):
            if sampler.get("interpolation", "LINEAR") != contract["interpolation"]:
                raise ValidationFailure(f"interpolation contract mismatch for {name}")
            output = int(sampler["output"])
            item, view, width, component_size, _ = glb.accessor_layout(output)
            stride = int(view.get("byteStride", width * component_size))
            if (
                item["componentType"] != contract["componentType"]
                or item["type"] != contract["type"]
                or stride != contract["byteStride"]
            ):
                raise ValidationFailure(f"accessor contract mismatch for {name}")
            current = glb.accessor_values(int(sampler["input"]))
            if timeline is None:
                timeline = current
            elif timeline != current:
                raise ValidationFailure(
                    f"common timeline contract mismatch for {clip['semanticId']}"
                )
            if len(glb.accessor_values(output)) != len(current):
                raise ValidationFailure("rotation/timeline count mismatch")
            channel_count += 1
        if not channel_count:
            raise ValidationFailure("motion clip has no rotation channels")
        clip_facts[clip["semanticId"]] = {
            "rotationChannels": channel_count,
            "samples": len(timeline or []),
        }
    return clip_facts


def artifact_difference(
    base: Glb, candidate: Glb, rig: dict, motion: dict, layers: list[dict]
) -> dict[str, Any]:
    if base.document != candidate.document:
        raise ValidationFailure("candidate GLB JSON differs from immutable input")
    allowed_nodes = {
        node
        for layer in layers
        for node, property_name in expanded_channels(rig["roles"], layer["writes"])
        if property_name == "rotation"
    }
    changed = []
    allowed_bin_positions: set[int] = set()
    for clip in motion["clips"]:
        base_accessors = base.rotation_accessors(clip["name"])
        candidate_accessors = candidate.rotation_accessors(clip["name"])
        if set(base_accessors) != set(candidate_accessors):
            raise ValidationFailure("rotation channel set changed")
        for name, accessor in base_accessors.items():
            if base.accessor_bytes(accessor) != candidate.accessor_bytes(
                candidate_accessors[name]
            ):
                changed.append(f"{clip['semanticId']}/{name}")
                if name not in allowed_nodes:
                    raise ValidationFailure(f"undeclared rotation changed: {name}")
            if name in allowed_nodes:
                offset, count, stride = base.accessor_region(accessor)
                item, _, width, component_size, _ = base.accessor_layout(accessor)
                item_size = width * component_size
                for row in range(count):
                    allowed_bin_positions.update(
                        range(offset + row * stride, offset + row * stride + item_size)
                    )
    if not changed:
        raise ValidationFailure("candidate has no approved changes")
    if len(base.binary) != len(candidate.binary):
        raise ValidationFailure("candidate BIN length changed")
    outside = [
        index
        for index, (left, right) in enumerate(zip(base.binary, candidate.binary))
        if left != right and index not in allowed_bin_positions
    ]
    if outside:
        raise ValidationFailure(
            f"candidate changed {len(outside)} bytes outside declared accessors"
        )
    return {
        "jsonEquivalent": True,
        "changedRotationAccessors": changed,
        "allowedNodes": sorted(allowed_nodes),
        "outsideDeclaredByteChanges": 0,
    }


def gltf_validation(path: Path, allowed_warnings: list[str]) -> dict[str, Any]:
    process = subprocess.run(
        ["gltf_validator", "-o", str(path)],
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise ValidationFailure("glTF Validator did not emit JSON") from exc
    issues = report.get("issues", {})
    codes = sorted(
        message["code"]
        for message in issues.get("messages", [])
        if message.get("severity") == 1
    )
    if process.returncode != 0 or issues.get("numErrors") != 0:
        raise ValidationFailure("glTF Validator reported errors")
    if codes != sorted(allowed_warnings):
        raise ValidationFailure(
            f"glTF warning allowlist mismatch: expected {allowed_warnings}, got {codes}"
        )
    return {
        "version": report.get("validatorVersion"),
        "errors": issues.get("numErrors"),
        "warnings": issues.get("numWarnings"),
        "warningCodes": codes,
    }


def validate_candidate(
    resolved: ResolvedProfile, candidate_path: Path
) -> dict[str, Any]:
    if sha256_file(candidate_path) != resolved.approved_output_sha256:
        raise ValidationFailure("candidate hash does not match approved profile")
    package = validate_source_package(
        resolved.source_release_root, resolved.source_manifest_path
    )
    base = Glb(resolved.input_path)
    candidate = Glb(candidate_path)
    contract = validate_animation_contract(candidate, resolved.rig, resolved.motion)
    differences = artifact_difference(
        base,
        candidate,
        resolved.rig,
        resolved.motion,
        [layer.data for layer in resolved.layers],
    )
    gltf = gltf_validation(
        candidate_path,
        resolved.motion["invariants"].get("allowedGltfWarnings", []),
    )
    return {
        "schema": "eonwild.motion.validation-report.v1",
        "status": "PASS",
        "profile": resolved.profile_binding(),
        "artifact": {
            "path": str(candidate_path),
            "sha256": sha256_file(candidate_path),
        },
        "package": package,
        "animationContract": contract,
        "difference": differences,
        "staticFacts": {
            "status": "PASS",
            "jsonEquivalent": differences["jsonEquivalent"],
            "outsideDeclaredByteChanges": differences[
                "outsideDeclaredByteChanges"
            ],
        },
        "contactFacts": contact_inheritance_facts(resolved),
        "gltfValidator": gltf,
    }
