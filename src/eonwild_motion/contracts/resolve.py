from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from ..errors import ContractError
from ..hashing import sha256_file, sha256_json
from ..paths import repository_root
from .load import load_and_validate
from .models import ContractDocument, ResolvedProfile


def _resolve_repo_path(repository: Path, relative: str) -> Path:
    path = (repository / relative).resolve()
    if path != repository and repository not in path.parents:
        raise ContractError(f"path escapes repository: {relative}")
    if not path.is_file():
        raise ContractError(f"referenced file does not exist: {relative}")
    return path


def _verify_reference(
    repository: Path, reference: dict[str, str], *, label: str
) -> tuple[Path, str]:
    path = _resolve_repo_path(repository, reference["path"])
    actual = sha256_file(path)
    if actual != reference["sha256"]:
        raise ContractError(
            f"{label} hash mismatch: expected {reference['sha256']}, got {actual}"
        )
    return path, actual


def _semantic_role(rig: dict[str, Any], selector: str) -> str:
    roles = rig["roles"]
    cursor: Any = roles
    for component in selector.split("."):
        if isinstance(cursor, dict) and component in cursor:
            cursor = cursor[component]
        else:
            raise ContractError(f"unknown semantic role selector: {selector}")
    if not isinstance(cursor, str):
        raise ContractError(f"semantic selector is not a node: {selector}")
    return cursor


def _validate_semantics(
    rig: dict[str, Any],
    family: dict[str, Any],
    species: dict[str, Any],
    motion: dict[str, Any],
    layers: list[dict[str, Any]],
) -> None:
    if species["family"] != family["id"]:
        raise ContractError("species/family ID mismatch")
    if species["rig"] != rig["id"]:
        raise ContractError("species/rig ID mismatch")
    if motion["family"] != family["id"]:
        raise ContractError("motion/family ID mismatch")
    if motion["id"] not in family["supportedMotions"]:
        raise ContractError("motion is not supported by family")
    for selector in family["requiredRoles"]:
        _semantic_role(rig, selector)
    implementations = [layer["implementation"] for layer in layers]
    if len(implementations) != len(set(implementations)):
        raise ContractError("duplicate layer implementation")
    stages = family["layerStages"]
    prior = -1
    written: set[str] = set()
    for layer in layers:
        if layer["stage"] not in stages:
            raise ContractError(f"layer stage is not supported: {layer['stage']}")
        current = stages.index(layer["stage"])
        if current < prior:
            raise ContractError("layer stage order is not monotonic")
        prior = current
        overlap = written.intersection(layer["writes"])
        if overlap:
            raise ContractError(f"overlapping layer writes: {sorted(overlap)}")
        written.update(layer["writes"])
        for selector in (*layer["reads"], *layer["writes"]):
            role = selector.removesuffix(".rotation").removesuffix(".translation")
            if role.endswith(".*"):
                role = role[:-2]
            cursor: Any = rig["roles"]
            for component in role.split("."):
                if isinstance(cursor, dict) and component in cursor:
                    cursor = cursor[component]
                else:
                    raise ContractError(
                        f"layer references unknown semantic role: {selector}"
                    )


def resolve_profile(profile_path: Path) -> ResolvedProfile:
    profile_path = profile_path.resolve()
    repository = repository_root(profile_path)
    profile = load_and_validate(profile_path, repository=repository)
    profile_sha = sha256_file(profile_path)
    documents: dict[str, ContractDocument] = {}
    for key in ("rig", "family", "species", "motion", "renderSet"):
        path, digest = _verify_reference(repository, profile[key], label=key)
        data = load_and_validate(path, repository=repository)
        documents[key] = ContractDocument(
            kind=key,
            path=str(path.relative_to(repository)),
            sha256=digest,
            data=data,
        )
    layers = []
    for index, reference in enumerate(profile["layers"]):
        path, digest = _verify_reference(
            repository, reference, label=f"layers[{index}]"
        )
        data = load_and_validate(path, repository=repository)
        layers.append(
            ContractDocument(
                kind="layer",
                path=str(path.relative_to(repository)),
                sha256=digest,
                data=data,
            )
        )
    input_path, input_sha = _verify_reference(
        repository, profile["input"], label="input"
    )
    approved_path, approved_sha = _verify_reference(
        repository, profile["approvedOutput"], label="approvedOutput"
    )
    source_root = (repository / profile["sourceRelease"]["root"]).resolve()
    if source_root != repository and repository not in source_root.parents:
        raise ContractError("source release root escapes repository")
    manifest_path, manifest_sha = _verify_reference(
        repository, profile["sourceRelease"]["manifest"], label="source manifest"
    )
    if source_root not in manifest_path.parents:
        raise ContractError("source manifest is outside source release root")
    contact_path, contact_sha = _verify_reference(
        repository, profile["contactEvidence"], label="contact evidence"
    )
    if source_root not in contact_path.parents:
        raise ContractError("contact evidence is outside source release root")
    _validate_semantics(
        documents["rig"].data,
        documents["family"].data,
        documents["species"].data,
        documents["motion"].data,
        [layer.data for layer in layers],
    )
    lock = {
        "schema": "eonwild.motion.resolved-profile.v1",
        "profile": {
            "path": str(profile_path.relative_to(repository)),
            "sha256": profile_sha,
            "id": profile["id"],
            "version": profile["version"],
        },
        "documents": {
            key: {"path": value.path, "sha256": value.sha256, "id": value.data["id"]}
            for key, value in documents.items()
        },
        "layers": [
            {"path": layer.path, "sha256": layer.sha256, "id": layer.data["id"]}
            for layer in layers
        ],
        "input": profile["input"],
        "approvedOutput": profile["approvedOutput"],
        "sourceManifest": profile["sourceRelease"]["manifest"],
        "contactEvidence": profile["contactEvidence"],
    }
    lock_sha = sha256_json(lock)
    lock_path = profile_path.with_name("profile.lock.json")
    if not lock_path.is_file():
        raise ContractError(f"profile lock is missing: {lock_path}")
    try:
        stored_lock = json.loads(lock_path.read_text())
    except json.JSONDecodeError as exc:
        raise ContractError(f"profile lock is invalid JSON: {lock_path}") from exc
    if stored_lock != {**lock, "lockSha256": lock_sha}:
        raise ContractError("profile lock is dirty or does not match its references")
    return ResolvedProfile(
        repository=repository,
        profile_path=profile_path,
        profile=profile,
        profile_sha256=profile_sha,
        documents=documents,
        layers=tuple(layers),
        input_path=input_path,
        input_sha256=input_sha,
        approved_output_path=approved_path,
        approved_output_sha256=approved_sha,
        source_release_root=source_root,
        source_manifest_path=manifest_path,
        source_manifest_sha256=manifest_sha,
        contact_evidence_path=contact_path,
        contact_evidence_sha256=contact_sha,
        lock=lock,
        lock_sha256=lock_sha,
    )
