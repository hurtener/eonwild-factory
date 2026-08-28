from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .. import __version__
from ..contracts.load import load_and_validate, validate_document
from ..contracts.models import ResolvedProfile
from ..errors import ValidationFailure
from ..hashing import sha256_file, write_json


def _relative(repository: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repository.resolve()))
    except ValueError as exc:
        raise ValidationFailure(f"stable release path is outside repository: {path}") from exc


def update_stable_channel(
    *,
    state_path: Path,
    repository: Path,
    resolved: ResolvedProfile,
    promotion_manifest_path: Path,
) -> dict:
    if resolved.channel is None or resolved.channel["name"] != "working":
        raise ValidationFailure("only a working-channel build can update stable")
    state_path = state_path.resolve()
    state = load_and_validate(state_path, repository=repository)
    if state["engineVersion"] != __version__:
        raise ValidationFailure("channel state engine version mismatch")
    prior_sha = sha256_file(state_path)
    if prior_sha != resolved.channel["stateSha256"]:
        raise ValidationFailure("channel state changed after build")
    if state["generation"] != resolved.channel["generation"]:
        raise ValidationFailure("channel generation changed after build")
    if state["working"]["revision"] != resolved.channel["revision"]:
        raise ValidationFailure("working revision changed after build")
    next_generation = int(state["generation"]) + 1
    history_id = (
        f"stable-{next_generation:04d}-{resolved.approved_output_sha256[:12]}"
    )
    history_dir = state_path.parent / "history"
    history_path = history_dir / f"{history_id}.json"
    if history_path.exists():
        raise ValidationFailure(f"stable history already exists: {history_path}")
    promotion_manifest_sha = sha256_file(promotion_manifest_path)
    history = {
        "schema": "eonwild.motion.channel-history.v1",
        "historyId": history_id,
        "priorStateSha256": prior_sha,
        "priorGeneration": state["generation"],
        "priorStable": state["stable"],
        "replacement": {
            "profileSha256": resolved.profile_sha256,
            "profileLockSha256": resolved.lock["profileLockSha256"],
            "artifactSha256": resolved.approved_output_sha256,
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
            "path": _relative(repository, resolved.profile_path),
            "sha256": resolved.profile_sha256,
        },
        "profileLockSha256": resolved.lock["profileLockSha256"],
        "release": {
            "id": resolved.profile["id"],
            "manifest": {
                "path": _relative(repository, resolved.source_manifest_path),
                "sha256": resolved.source_manifest_sha256,
            },
            "artifact": {
                "path": _relative(repository, resolved.approved_output_path),
                "sha256": resolved.approved_output_sha256,
            },
        },
    }
    updated["working"]["basedOnStable"] = history_id
    validate_document(updated, repository=repository, label="updated channel state")
    history_dir.mkdir(parents=True, exist_ok=True)
    write_json(history_path, history)
    write_json(state_path, updated)
    return {
        "status": "PASS",
        "historyPath": str(history_path),
        "historySha256": sha256_file(history_path),
        "priorStateSha256": prior_sha,
        "stateSha256": sha256_file(state_path),
        "generation": next_generation,
        "stableRevision": updated["stable"]["revision"],
        "historyId": history_id,
    }
