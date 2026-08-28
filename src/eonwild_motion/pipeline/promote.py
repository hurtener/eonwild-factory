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
from .channels import ensure_release_destination, update_stable_channel
from .validate import validate_candidate


def promote_run(
    *,
    run_dir: Path,
    destination: Path,
    approvals_path: Path,
    source_state: Callable[[Path], dict[str, object]] = git_source_state,
    update_stable: bool = False,
    channel_state_path: Path | None = None,
) -> dict:
    if destination.exists():
        raise ValidationFailure(f"promotion destination already exists: {destination}")
    run_report_path = run_dir / "run-report.json"
    resolved_path = run_dir / "resolved-profile.json"
    if not run_report_path.is_file() or not resolved_path.is_file():
        raise ValidationFailure("promotion run is missing report or resolved profile")
    for evidence_name in (
        "validation.json",
        "comparison.json",
        "render.json",
        "render-baseline.json",
    ):
        if not (run_dir / evidence_name).is_file():
            raise ValidationFailure(
                f"promotion run is missing required evidence: {evidence_name}"
            )
    run_report = load_and_validate(run_report_path, repository=Path(json.loads(resolved_path.read_text())["repository"]))
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
    selector = runtime.get("profileSelector", runtime["profilePath"])
    runtime_channel_state = (
        Path(runtime["channelStatePath"]).resolve()
        if runtime.get("channelStatePath")
        else None
    )
    if channel_state_path is not None and runtime_channel_state != channel_state_path.resolve():
        raise ValidationFailure("promotion channel-state path differs from build lock")
    resolved = resolve_profile(
        selector,
        repository=repository,
        channel_state_path=runtime_channel_state,
    )
    if resolved.lock_sha256 != runtime.get("lockSha256"):
        raise ValidationFailure("resolved profile lock hash mismatch")
    expected_profile = resolved.profile_binding()
    if run_report.get("profile") != expected_profile:
        raise ValidationFailure("build run profile binding mismatch")
    evidence = {
        name: load_and_validate(run_dir / name, repository=repository)
        for name in (
            "validation.json",
            "comparison.json",
            "render.json",
            "render-baseline.json",
        )
    }
    for name, document in evidence.items():
        if document.get("status") != "PASS":
            raise ValidationFailure(f"evidence is not PASS: {name}")
        if document.get("runId") != run_report["runId"]:
            raise ValidationFailure(f"evidence run binding mismatch: {name}")
        if document.get("profile") != expected_profile:
            raise ValidationFailure(f"evidence profile binding mismatch: {name}")
        if document.get("source", {}).get("gitHead") != run_report["source"]["gitHead"]:
            raise ValidationFailure(f"evidence source binding mismatch: {name}")
    approvals = load_and_validate(approvals_path, repository=repository)
    implementer = str(run_report["source"].get("implementer", ""))
    reviewers = {
        approvals["technical"]["reviewer"],
        approvals["visual"]["reviewer"],
    }
    if len(reviewers) != 2 or implementer in reviewers:
        raise ValidationFailure("promotion approvals are not independent")
    outputs_by_kind = {}
    for output in run_report["outputs"]:
        kind = output["kind"]
        if kind in outputs_by_kind:
            raise ValidationFailure(f"duplicate build output kind: {kind}")
        outputs_by_kind[kind] = output
    required_output_kinds = {
        "candidate-glb",
        "canonical-fixed-camera-png",
        "static-review-html",
    }
    if not required_output_kinds.issubset(outputs_by_kind):
        raise ValidationFailure("build run is missing required artifact/media outputs")
    artifact = Path(outputs_by_kind["candidate-glb"]["path"]).resolve()
    artifact_hash = sha256_file(artifact)
    if artifact_hash != resolved.approved_output_sha256:
        raise ValidationFailure("promotion artifact hash mismatch")
    if outputs_by_kind["candidate-glb"]["sha256"] != artifact_hash:
        raise ValidationFailure("build output artifact hash binding mismatch")
    validation = validate_candidate(resolved, artifact)
    validation_evidence = evidence["validation.json"]
    comparison_evidence = evidence["comparison.json"]
    render_evidence = evidence["render.json"]
    baseline_render_evidence = evidence["render-baseline.json"]
    for key, value in validation.items():
        if validation_evidence.get(key) != value:
            raise ValidationFailure(f"validation evidence is stale at {key}")
    if validation_evidence["artifact"]["sha256"] != artifact_hash:
        raise ValidationFailure("validation artifact binding mismatch")
    if Path(validation_evidence["artifact"]["path"]).resolve() != artifact:
        raise ValidationFailure("validation artifact path binding mismatch")
    if comparison_evidence["candidate"]["sha256"] != artifact_hash:
        raise ValidationFailure("comparison candidate binding mismatch")
    if Path(comparison_evidence["candidate"]["path"]).resolve() != artifact:
        raise ValidationFailure("comparison candidate path binding mismatch")
    if comparison_evidence["baseline"]["sha256"] != resolved.input_sha256:
        raise ValidationFailure("comparison baseline binding mismatch")
    if Path(comparison_evidence["baseline"]["path"]).resolve() != resolved.input_path:
        raise ValidationFailure("comparison baseline path binding mismatch")
    if render_evidence["artifact"]["sha256"] != artifact_hash:
        raise ValidationFailure("render artifact binding mismatch")
    if Path(render_evidence["artifact"]["path"]).resolve() != artifact:
        raise ValidationFailure("render artifact path binding mismatch")
    if baseline_render_evidence["artifact"]["sha256"] != resolved.input_sha256:
        raise ValidationFailure("baseline render artifact binding mismatch")
    if Path(baseline_render_evidence["artifact"]["path"]).resolve() != resolved.input_path:
        raise ValidationFailure("baseline render artifact path binding mismatch")
    expected_render_set = {
        "id": resolved.render_set["id"],
        "sha256": resolved.documents["renderSet"].sha256,
    }
    expected_clip = resolved.motion["clips"][0]["semanticId"]
    for document in (render_evidence, baseline_render_evidence):
        if document["renderSet"] != expected_render_set:
            raise ValidationFailure("render-set binding mismatch")
        if document["clipSemanticId"] != expected_clip:
            raise ValidationFailure("render clip binding mismatch")
        if document["frame"] != resolved.render_set["frame"]:
            raise ValidationFailure("render frame binding mismatch")
        if document["media"]["width"] != resolved.render_set["width"] or document["media"]["height"] != resolved.render_set["height"]:
            raise ValidationFailure("render dimensions binding mismatch")
        if document["camera"]["viewDirection"] != resolved.render_set["viewDirection"] or document["camera"]["margin"] != resolved.render_set["margin"]:
            raise ValidationFailure("render camera binding mismatch")
    required_pass_facts = (
        validation_evidence["staticFacts"],
        validation_evidence["contactFacts"],
        comparison_evidence["structural"],
        comparison_evidence["accessor"],
        comparison_evidence["staticFacts"],
        comparison_evidence["contactFacts"],
        comparison_evidence["media"],
    )
    if any(facts.get("status") != "PASS" for facts in required_pass_facts):
        raise ValidationFailure("required static/contact/media facts are not PASS")
    if comparison_evidence["contactFacts"] != validation["contactFacts"]:
        raise ValidationFailure("comparison contact facts are stale")
    if validation_evidence["difference"].get("outsideDeclaredByteChanges") != 0:
        raise ValidationFailure("validation static equivalence is stale")
    if comparison_evidence["structural"].get("outsideDeclaredByteChanges") != 0:
        raise ValidationFailure("comparison structural equivalence is stale")
    for document in (render_evidence, baseline_render_evidence):
        media_path = Path(document["media"]["path"]).resolve()
        if run_dir.resolve() not in media_path.parents or not media_path.is_file():
            raise ValidationFailure("render media is outside or missing from build run")
        if sha256_file(media_path) != document["media"]["fileSha256"]:
            raise ValidationFailure("render media hash mismatch")
    if comparison_evidence["media"]["candidate"] != render_evidence["media"]:
        raise ValidationFailure("comparison candidate media binding mismatch")
    if comparison_evidence["media"]["baseline"] != baseline_render_evidence["media"]:
        raise ValidationFailure("comparison baseline media binding mismatch")
    review_path = Path(comparison_evidence["review"]["path"]).resolve()
    if run_dir.resolve() not in review_path.parents or not review_path.is_file():
        raise ValidationFailure("comparison review is outside or missing from build run")
    if sha256_file(review_path) != comparison_evidence["review"]["sha256"]:
        raise ValidationFailure("comparison review hash mismatch")
    candidate_output = outputs_by_kind["canonical-fixed-camera-png"]
    if Path(candidate_output["path"]).resolve() != Path(render_evidence["media"]["path"]).resolve() or candidate_output["sha256"] != render_evidence["media"]["fileSha256"]:
        raise ValidationFailure("build output render binding mismatch")
    review_output = outputs_by_kind["static-review-html"]
    if Path(review_output["path"]).resolve() != review_path or review_output["sha256"] != comparison_evidence["review"]["sha256"]:
        raise ValidationFailure("build output review binding mismatch")
    if resolved.species["provenance"].get("status") != "complete":
        raise ValidationFailure("species provenance is incomplete")
    if update_stable:
        ensure_release_destination(repository, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=destination.name + ".", dir=destination.parent)
    )
    destination_installed = False
    try:
        artifact_dir = temporary / "artifacts" / artifact_hash[:2]
        artifact_dir.mkdir(parents=True)
        promoted_artifact = artifact_dir / f"{artifact_hash}.glb"
        shutil.copyfile(artifact, promoted_artifact)
        shutil.copyfile(approvals_path, temporary / "approvals.json")
        evidence_dir = temporary / "evidence"
        evidence_dir.mkdir()
        for name in (
            "validation.json",
            "comparison.json",
            "render.json",
            "render-baseline.json",
        ):
            source = run_dir / name
            if source.is_file():
                shutil.copyfile(source, evidence_dir / name)
        media_dir = evidence_dir / "media"
        media_dir.mkdir()
        shutil.copyfile(
            Path(render_evidence["media"]["path"]), media_dir / "candidate.png"
        )
        shutil.copyfile(
            Path(baseline_render_evidence["media"]["path"]),
            media_dir / "baseline.png",
        )
        shutil.copyfile(review_path, evidence_dir / "review.html")
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
            "evidence": {
                name: {"sha256": sha256_file(run_dir / name)}
                for name in evidence
            },
            "media": {
                "candidate": {
                    **render_evidence["media"],
                    "path": "evidence/media/candidate.png",
                },
                "baseline": {
                    **baseline_render_evidence["media"],
                    "path": "evidence/media/baseline.png",
                },
                "review": {
                    **comparison_evidence["review"],
                    "path": "evidence/review.html",
                },
            },
            "approvals": approvals,
            "channel": expected_profile,
        }
        validate_document(
            manifest, repository=repository, label="promotion manifest"
        )
        write_json(temporary / "manifest.json", manifest)
        temporary.replace(destination)
        destination_installed = True
        channel_update = None
        if update_stable:
            if runtime_channel_state is None:
                raise ValidationFailure("stable update requires a channel build")
            channel_update = update_stable_channel(
                state_path=runtime_channel_state,
                repository=repository,
                resolved=resolved,
                promotion_manifest_path=destination / "manifest.json",
            )
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        if destination_installed:
            shutil.rmtree(destination, ignore_errors=True)
        raise
    return {
        "status": "PASS",
        "destination": str(destination),
        "artifactSha256": artifact_hash,
        "manifest": str(destination / "manifest.json"),
        "channelUpdate": channel_update,
    }
