from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from ..contracts.load import load_and_validate, validate_document
from ..contracts.resolve import resolve_profile
from ..errors import ValidationFailure
from ..hashing import sha256_file, write_json
from .context import git_source_state
from .validate import validate_candidate


def promote_run(
    *,
    run_dir: Path,
    destination: Path,
    approvals_path: Path,
    source_state: Callable[[Path], dict[str, object]] = git_source_state,
) -> dict:
    if destination.exists():
        raise ValidationFailure(f"promotion destination already exists: {destination}")
    run_report_path = run_dir / "run-report.json"
    resolved_path = run_dir / "resolved-profile.json"
    if not run_report_path.is_file() or not resolved_path.is_file():
        raise ValidationFailure("promotion run is missing report or resolved profile")
    for evidence_name in ("validation.json", "comparison.json"):
        if not (run_dir / evidence_name).is_file():
            raise ValidationFailure(
                f"promotion run is missing required evidence: {evidence_name}"
            )
    run_report = json.loads(run_report_path.read_text())
    runtime = json.loads(resolved_path.read_text())
    if run_report.get("status") != "PASS" or run_report.get("command") != "build":
        raise ValidationFailure("only a passing build run can be promoted")
    if run_report.get("source", {}).get("dirty") is not False:
        raise ValidationFailure("build run source lock is dirty")
    repository = Path(runtime["repository"]).resolve()
    current = source_state(repository)
    if current.get("dirty") is not False:
        raise ValidationFailure("current source tree is dirty")
    if current.get("gitHead") != run_report["source"].get("gitHead"):
        raise ValidationFailure("current source head differs from build lock")
    resolved = resolve_profile(Path(runtime["profilePath"]))
    if resolved.lock_sha256 != runtime.get("lockSha256"):
        raise ValidationFailure("resolved profile lock hash mismatch")
    approvals = load_and_validate(approvals_path, repository=repository)
    implementer = str(run_report["source"].get("implementer", ""))
    reviewers = {
        approvals["technical"]["reviewer"],
        approvals["visual"]["reviewer"],
    }
    if len(reviewers) != 2 or implementer in reviewers:
        raise ValidationFailure("promotion approvals are not independent")
    artifact = Path(run_report["outputs"][0]["path"])
    artifact_hash = sha256_file(artifact)
    if artifact_hash != resolved.approved_output_sha256:
        raise ValidationFailure("promotion artifact hash mismatch")
    validation = validate_candidate(resolved, artifact)
    if resolved.species["provenance"].get("status") != "complete":
        raise ValidationFailure("species provenance is incomplete")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=destination.name + ".", dir=destination.parent)
    )
    try:
        artifact_dir = temporary / "artifacts" / artifact_hash[:2]
        artifact_dir.mkdir(parents=True)
        promoted_artifact = artifact_dir / f"{artifact_hash}.glb"
        shutil.copyfile(artifact, promoted_artifact)
        shutil.copyfile(approvals_path, temporary / "approvals.json")
        evidence_dir = temporary / "evidence"
        evidence_dir.mkdir()
        for name in ("validation.json", "comparison.json", "render.json"):
            source = run_dir / name
            if source.is_file():
                shutil.copyfile(source, evidence_dir / name)
        manifest = {
            "schema": "eonwild.motion.artifact-manifest.v1",
            "release": resolved.profile["id"],
            "engine": run_report["source"].get("engineVersion"),
            "gitHead": run_report["source"]["gitHead"],
            "lockSha256": resolved.lock_sha256,
            "artifact": {
                "path": str(promoted_artifact.relative_to(temporary)),
                "sha256": artifact_hash,
            },
            "input": {
                "path": str(resolved.input_path.relative_to(repository)),
                "sha256": resolved.input_sha256,
            },
            "profile": {
                "path": str(resolved.profile_path.relative_to(repository)),
                "sha256": resolved.profile_sha256,
            },
            "provenance": resolved.species["provenance"],
            "validation": validation,
            "approvals": approvals,
        }
        validate_document(
            manifest, repository=repository, label="promotion manifest"
        )
        write_json(temporary / "manifest.json", manifest)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "status": "PASS",
        "destination": str(destination),
        "artifactSha256": artifact_hash,
        "manifest": str(destination / "manifest.json"),
    }
