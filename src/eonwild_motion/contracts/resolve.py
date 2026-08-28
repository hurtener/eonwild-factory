from __future__ import annotations

from pathlib import Path
import json
from typing import Any
from dataclasses import replace

from .. import __version__
from ..errors import ContractError
from ..hashing import sha256_file, sha256_json
from ..paths import repository_root
from .load import load_and_validate
from .models import ContractDocument, ResolvedProfile


CHANNEL_NAMES = frozenset({"stable", "working"})


def profile_repository(profile_selector: str | Path) -> Path:
    if str(profile_selector) in CHANNEL_NAMES:
        return repository_root(Path.cwd())
    return repository_root(Path(profile_selector))


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


def _resolve_explicit_profile(profile_path: Path) -> ResolvedProfile:
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
        selector=str(profile_path),
    )


def resolve_profile(
    profile_selector: str | Path,
    *,
    repository: Path | None = None,
    channel_state_path: Path | None = None,
) -> ResolvedProfile:
    selector = str(profile_selector)
    if selector not in CHANNEL_NAMES:
        return _resolve_explicit_profile(Path(profile_selector))
    repository = (repository or repository_root(Path.cwd())).resolve()
    state_path = (
        channel_state_path.resolve()
        if channel_state_path is not None
        else repository / "profiles/channels/state.json"
    )
    state = load_and_validate(state_path, repository=repository)
    if state["engineVersion"] != __version__:
        raise ContractError(
            f"channel engine version {state['engineVersion']} does not match {__version__}"
        )
    entry = state[selector]
    profile_path, profile_sha = _verify_reference(
        repository, entry["profile"], label=f"channel {selector} profile"
    )
    resolved = _resolve_explicit_profile(profile_path)
    if resolved.profile_sha256 != profile_sha:
        raise ContractError(f"channel {selector} profile hash is stale")
    if resolved.lock_sha256 != entry["profileLockSha256"]:
        raise ContractError(f"channel {selector} profile lock is stale")
    if selector == "stable":
        manifest_path, manifest_sha = _verify_reference(
            repository, entry["release"]["manifest"], label="stable release manifest"
        )
        artifact_path, artifact_sha = _verify_reference(
            repository, entry["release"]["artifact"], label="stable artifact"
        )
        if manifest_path == resolved.source_manifest_path:
            if (
                manifest_sha != resolved.source_manifest_sha256
                or artifact_path != resolved.approved_output_path
                or artifact_sha != resolved.approved_output_sha256
            ):
                raise ContractError("initial stable release does not match profile")
        else:
            release_root = repository / "releases"
            if release_root not in manifest_path.parents:
                raise ContractError("stable release manifest is outside releases")
            manifest = load_and_validate(manifest_path, repository=repository)
            manifest_artifact = (manifest_path.parent / manifest["artifact"]["path"]).resolve()
            if manifest["release"] != resolved.profile["id"]:
                raise ContractError("stable release ID does not match profile")
            if manifest["engine"] != __version__:
                raise ContractError("stable release engine version mismatch")
            if manifest["profile"] != {
                "path": str(resolved.profile_path.relative_to(repository)),
                "sha256": resolved.profile_sha256,
            }:
                raise ContractError("stable release profile does not match channel")
            if manifest_artifact != artifact_path or manifest_path.parent not in artifact_path.parents:
                raise ContractError("stable artifact path does not match release manifest")
            if manifest["artifact"]["sha256"] != artifact_sha:
                raise ContractError("stable artifact hash does not match release manifest")
            if artifact_sha != resolved.approved_output_sha256:
                raise ContractError("stable artifact does not match approved profile output")
            resolved = replace(
                resolved,
                approved_output_path=artifact_path,
                approved_output_sha256=artifact_sha,
            )
    elif entry["basedOnStable"] != state["stable"]["historyId"]:
        raise ContractError("working channel base does not match stable history")
    state_sha = sha256_file(state_path)
    try:
        state_identity = str(state_path.relative_to(repository))
    except ValueError:
        state_identity = str(state_path)
    channel = {
        "name": selector,
        "statePath": state_identity,
        "stateSha256": state_sha,
        "generation": state["generation"],
        "iteration": entry.get("iteration"),
        "revision": entry["revision"],
        "historyId": entry.get("historyId", entry.get("basedOnStable")),
    }
    lock = {
        "schema": "eonwild.motion.resolved-channel-profile.v1",
        "profileLockSha256": resolved.lock_sha256,
        "channel": {
            key: value for key, value in channel.items() if key != "statePath"
        },
    }
    return replace(
        resolved,
        lock=lock,
        lock_sha256=sha256_json(lock),
        selector=selector,
        channel=channel,
    )
