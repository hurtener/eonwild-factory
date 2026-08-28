from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Callable

from .. import __version__
from ..contracts.load import load_and_validate, validate_document
from ..contracts.models import ResolvedProfile
from ..errors import ValidationFailure
from ..hashing import sha256_file


OperationHook = Callable[[str], None]


def _relative(repository: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repository.resolve()))
    except ValueError as exc:
        raise ValidationFailure(f"stable release path is outside repository: {path}") from exc


def ensure_release_destination(repository: Path, destination: Path) -> Path:
    release_root = repository.resolve() / "releases"
    destination = destination.resolve()
    if destination == release_root or release_root not in destination.parents:
        raise ValidationFailure(
            f"stable release destination must be below {release_root}: {destination}"
        )
    return destination


def _promoted_release(
    *, repository: Path, resolved: ResolvedProfile, manifest_path: Path
) -> tuple[dict, Path, str, Path, str]:
    manifest_path = manifest_path.resolve()
    ensure_release_destination(repository, manifest_path.parent)
    if manifest_path.name != "manifest.json":
        raise ValidationFailure("promoted stable manifest must be named manifest.json")
    manifest = load_and_validate(manifest_path, repository=repository)
    manifest_sha = sha256_file(manifest_path)
    expected_profile_path = _relative(repository, resolved.profile_path)
    if manifest["release"] != resolved.profile["id"]:
        raise ValidationFailure("promoted release ID does not match working profile")
    if manifest["engine"] != __version__:
        raise ValidationFailure("promoted release engine version mismatch")
    if manifest["profile"] != {
        "path": expected_profile_path,
        "sha256": resolved.profile_sha256,
    }:
        raise ValidationFailure("promoted release profile binding mismatch")
    if manifest["channel"] != resolved.profile_binding():
        raise ValidationFailure("promoted release channel binding mismatch")
    artifact_path = (manifest_path.parent / manifest["artifact"]["path"]).resolve()
    if manifest_path.parent not in artifact_path.parents:
        raise ValidationFailure("promoted artifact escapes release destination")
    if not artifact_path.is_file():
        raise ValidationFailure("promoted artifact is missing")
    artifact_sha = sha256_file(artifact_path)
    if artifact_sha != manifest["artifact"]["sha256"]:
        raise ValidationFailure("promoted artifact hash does not match manifest")
    if artifact_sha != resolved.approved_output_sha256:
        raise ValidationFailure("promoted artifact does not match approved working output")
    return manifest, manifest_path, manifest_sha, artifact_path, artifact_sha


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _stage_sibling(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _install_transaction(
    *,
    state_path: Path,
    prior_state: bytes,
    updated_state: dict,
    history_path: Path,
    history: dict,
    operation_hook: OperationHook | None,
) -> None:
    if not state_path.is_file():
        raise ValidationFailure(f"channel state is missing: {state_path}")
    if state_path.read_bytes() != prior_state:
        raise ValidationFailure("channel state changed before transaction staging")
    if history_path.exists():
        raise ValidationFailure(f"stable history already exists: {history_path}")
    history_directory_existed = history_path.parent.exists()
    hook = operation_hook or (lambda _operation: None)
    history_temporary: Path | None = None
    state_temporary: Path | None = None
    history_installed = False
    state_installed = False
    expected_history_sha: str | None = None
    try:
        history_temporary = _stage_sibling(history_path, _json_bytes(history))
        expected_history_sha = sha256_file(history_temporary)
        hook("history-staged")
        state_temporary = _stage_sibling(state_path, _json_bytes(updated_state))
        hook("state-staged")
        os.link(history_temporary, history_path)
        history_installed = True
        history_temporary.unlink()
        history_temporary = None
        _sync_directory(history_path.parent)
        hook("history-installed")
        if state_path.read_bytes() != prior_state:
            raise ValidationFailure("channel state changed before installation")
        os.replace(state_temporary, state_path)
        state_temporary = None
        state_installed = True
        _sync_directory(state_path.parent)
        hook("state-installed")
    except Exception as exc:
        rollback_errors: list[str] = []
        if state_installed:
            try:
                recovery = _stage_sibling(state_path, prior_state)
                os.replace(recovery, state_path)
                _sync_directory(state_path.parent)
            except Exception as rollback_exc:  # pragma: no cover - catastrophic FS failure
                rollback_errors.append(f"state restore failed: {rollback_exc}")
        if history_installed:
            try:
                if (
                    history_path.is_file()
                    and expected_history_sha is not None
                    and sha256_file(history_path) == expected_history_sha
                ):
                    history_path.unlink()
                    _sync_directory(history_path.parent)
                else:
                    rollback_errors.append("installed history identity changed")
            except Exception as rollback_exc:  # pragma: no cover - catastrophic FS failure
                rollback_errors.append(f"history removal failed: {rollback_exc}")
        for temporary in (history_temporary, state_temporary):
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        if not history_directory_existed and history_path.parent.exists():
            try:
                history_path.parent.rmdir()
            except OSError as rollback_exc:
                rollback_errors.append(f"history directory removal failed: {rollback_exc}")
        if rollback_errors:
            raise ValidationFailure(
                "channel transaction failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        if state_path.read_bytes() != prior_state or history_path.exists():
            raise ValidationFailure("channel transaction rollback verification failed") from exc
        raise


def update_stable_channel(
    *,
    state_path: Path,
    repository: Path,
    resolved: ResolvedProfile,
    promotion_manifest_path: Path,
    operation_hook: OperationHook | None = None,
) -> dict:
    if resolved.channel is None or resolved.channel["name"] != "working":
        raise ValidationFailure("only a working-channel build can update stable")
    repository = repository.resolve()
    state_path = state_path.resolve()
    state = load_and_validate(state_path, repository=repository)
    if state["engineVersion"] != __version__:
        raise ValidationFailure("channel state engine version mismatch")
    prior_state = state_path.read_bytes()
    prior_sha = sha256_file(state_path)
    if prior_sha != resolved.channel["stateSha256"]:
        raise ValidationFailure("channel state changed after build")
    if state["generation"] != resolved.channel["generation"]:
        raise ValidationFailure("channel generation changed after build")
    if state["working"]["revision"] != resolved.channel["revision"]:
        raise ValidationFailure("working revision changed after build")
    (
        manifest,
        promotion_manifest_path,
        promotion_manifest_sha,
        promoted_artifact_path,
        promoted_artifact_sha,
    ) = _promoted_release(
        repository=repository,
        resolved=resolved,
        manifest_path=promotion_manifest_path,
    )
    next_generation = int(state["generation"]) + 1
    history_id = f"stable-{next_generation:04d}-{promoted_artifact_sha[:12]}"
    history_path = state_path.parent / "history" / f"{history_id}.json"
    if history_path.exists():
        raise ValidationFailure(f"stable history already exists: {history_path}")
    history = {
        "schema": "eonwild.motion.channel-history.v1",
        "historyId": history_id,
        "priorStateSha256": prior_sha,
        "priorGeneration": state["generation"],
        "priorStable": state["stable"],
        "replacement": {
            "profileSha256": manifest["profile"]["sha256"],
            "profileLockSha256": resolved.lock["profileLockSha256"],
            "artifactSha256": promoted_artifact_sha,
            "promotionManifestSha256": promotion_manifest_sha,
        },
    }
    validate_document(history, repository=repository, label="channel history")
    updated = deepcopy(state)
    updated["generation"] = next_generation
    updated["stable"] = {
        "revision": int(state["stable"]["revision"]) + 1,
        "historyId": history_id,
        "profile": {
            "path": manifest["profile"]["path"],
            "sha256": manifest["profile"]["sha256"],
        },
        "profileLockSha256": resolved.lock["profileLockSha256"],
        "release": {
            "id": manifest["release"],
            "manifest": {
                "path": _relative(repository, promotion_manifest_path),
                "sha256": promotion_manifest_sha,
            },
            "artifact": {
                "path": _relative(repository, promoted_artifact_path),
                "sha256": promoted_artifact_sha,
            },
        },
    }
    updated["working"]["basedOnStable"] = history_id
    validate_document(updated, repository=repository, label="updated channel state")
    _install_transaction(
        state_path=state_path,
        prior_state=prior_state,
        updated_state=updated,
        history_path=history_path,
        history=history,
        operation_hook=operation_hook,
    )
    return {
        "status": "PASS",
        "historyPath": str(history_path),
        "historySha256": sha256_file(history_path),
        "priorStateSha256": prior_sha,
        "stateSha256": sha256_file(state_path),
        "generation": next_generation,
        "stableRevision": updated["stable"]["revision"],
        "historyId": history_id,
        "manifestPath": str(promotion_manifest_path),
        "manifestSha256": promotion_manifest_sha,
        "artifactPath": str(promoted_artifact_path),
        "artifactSha256": promoted_artifact_sha,
    }
