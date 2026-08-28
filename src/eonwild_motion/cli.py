from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess
from typing import Any

from . import __version__
from .contracts.load import validate_document
from .contracts.resolve import resolve_profile
from .hashing import sha256_file, write_json
from .paths import default_work_root, repository_root
from .pipeline.build import invoke_blender_build
from .pipeline.compare import compare_artifacts
from .pipeline.context import create_orphan_run_context, create_run_context, git_source_state
from .pipeline.promote import promote_run
from .pipeline.render import invoke_blender_render
from .pipeline.validate import validate_candidate
from .reports import emit_report, now_utc


def _unknown_source() -> dict[str, Any]:
    return {
        "gitHead": None,
        "dirty": None,
        "implementer": None,
        "engineVersion": __version__,
    }


def _source(repository: Path) -> dict[str, Any]:
    state = git_source_state(repository)
    implementer = subprocess.check_output(
        ["git", "config", "--get", "user.email"], cwd=repository, text=True
    ).strip()
    return {**state, "implementer": implementer, "engineVersion": __version__}


def _profile(resolved) -> dict[str, str]:
    return {
        "id": resolved.profile["id"],
        "sha256": resolved.profile_sha256,
        "lockSha256": resolved.lock_sha256,
    }


def _tools(*, blender: str | None = None, validator: str | None = None) -> dict[str, Any]:
    return {
        "engine": __version__,
        "python": platform.python_version(),
        "blender": blender,
        "gltfValidator": validator,
    }


def _runtime_document(resolved) -> dict[str, Any]:
    return {
        **resolved.runtime_document(),
        "repository": str(resolved.repository),
        "profilePath": str(resolved.profile_path),
    }


def _output(report: dict, explicit: Path | None) -> None:
    if explicit is not None:
        write_json(explicit, report)
    print(json.dumps(report, indent=2, sort_keys=True))


def _context_or_fallback(repository: Path | None, work_root: Path, command: str):
    if repository is not None:
        try:
            return create_run_context(repository, work_root, command)
        except Exception:
            return create_run_context(repository, default_work_root(), command)
    return create_orphan_run_context(default_work_root(), command)


def _bind_evidence(document: dict, *, run_id: str, source: dict) -> dict:
    document["runId"] = run_id
    document["source"] = {"gitHead": source["gitHead"]}
    return document


def _write_resolved(context, resolved) -> None:
    write_json(context.run_dir / "resolved-profile.json", _runtime_document(resolved))


def _render_one(
    *,
    resolved,
    artifact: Path,
    output: Path,
    stage_report: Path,
    log_path: Path,
    context,
    source: dict,
) -> dict:
    clip = resolved.motion["clips"][0]
    request = stage_report.with_name(stage_report.stem + "-request.json")
    write_json(
        request,
        {
            "schema": "eonwild.motion.render-request.v1",
            "runId": context.run_id,
            "profile": _profile(resolved),
            "source": {"gitHead": source["gitHead"]},
            "artifactPath": str(artifact),
            "artifactSha256": sha256_file(artifact),
            "clipSemanticId": clip["semanticId"],
            "clipName": clip["name"],
            "renderSet": resolved.render_set,
            "renderSetBinding": {
                "id": resolved.render_set["id"],
                "sha256": resolved.documents["renderSet"].sha256,
            },
            "outputPath": str(output),
            "stageReportPath": str(stage_report),
        },
    )
    render = invoke_blender_render(
        repository=resolved.repository, request_path=request, log_path=log_path
    )
    validate_document(render, repository=resolved.repository, label="render evidence")
    if render["media"]["fileSha256"] != sha256_file(output):
        raise ValueError("render evidence file hash mismatch")
    return render


def _comparison_bundle(*, resolved, baseline: Path, candidate: Path, context, source):
    media_dir = context.run_dir / "review/media"
    baseline_render = _render_one(
        resolved=resolved,
        artifact=baseline,
        output=media_dir / "baseline.png",
        stage_report=context.run_dir / "render-baseline.json",
        log_path=context.run_dir / "blender-render-baseline.log",
        context=context,
        source=source,
    )
    candidate_render = _render_one(
        resolved=resolved,
        artifact=candidate,
        output=media_dir / "candidate.png",
        stage_report=context.run_dir / "render.json",
        log_path=context.run_dir / "blender-render-candidate.log",
        context=context,
        source=source,
    )
    comparison = compare_artifacts(
        resolved,
        baseline,
        candidate,
        baseline_render=baseline_render,
        candidate_render=candidate_render,
        run_id=context.run_id,
        source=source,
        review_path=context.run_dir / "review/index.html",
    )
    validate_document(comparison, repository=resolved.repository, label="comparison evidence")
    return baseline_render, candidate_render, comparison


def _failure(
    *, command: str, args, exc: Exception, repository: Path | None, context, source: dict,
    resolved=None, started: str,
) -> int:
    context = context or _context_or_fallback(repository, args.work_root, command)
    if repository is not None:
        schema_repository = repository
    else:
        try:
            schema_repository = repository_root(Path.cwd())
        except Exception:
            schema_repository = None
    report = emit_report(
        context.run_dir / "run-report.json",
        command=command,
        status="FAIL",
        run_id=context.run_id,
        errors=[str(exc)],
        source=source,
        profile=_profile(resolved) if resolved else None,
        tool_versions=_tools(),
        repository=schema_repository,
        started_at=started,
    )
    _output(report, getattr(args, "json_output", None))
    return 1


def command_build(args) -> int:
    started, repository, context, resolved = now_utc(), None, None, None
    source = _unknown_source()
    try:
        repository = repository_root(args.profile)
        context = create_run_context(repository, args.work_root, "build")
        source = _source(repository)
        resolved = resolve_profile(args.profile)
        _write_resolved(context, resolved)
        artifact = context.run_dir / "artifacts/candidate.glb"
        stage_path = context.run_dir / "build-stage.json"
        request = context.run_dir / "build-request.json"
        write_json(request, {"schema": "eonwild.motion.build-request.v1", "resolved": resolved.runtime_document(), "outputPath": str(artifact), "stageReportPath": str(stage_path)})
        stage = invoke_blender_build(repository=repository, request_path=request, log_path=context.run_dir / "blender-build.log")
        validation = _bind_evidence(validate_candidate(resolved, artifact), run_id=context.run_id, source=source)
        validate_document(validation, repository=repository, label="validation evidence")
        baseline_render, render, comparison = _comparison_bundle(
            resolved=resolved, baseline=resolved.input_path, candidate=artifact, context=context, source=source
        )
        write_json(context.run_dir / "validation.json", validation)
        write_json(context.run_dir / "comparison.json", comparison)
        report = emit_report(
            context.run_dir / "run-report.json", command="build", status="PASS", run_id=context.run_id,
            inputs=[{"path": str(resolved.input_path), "sha256": resolved.input_sha256, "kind": "immutable-glb"}],
            outputs=[
                {"path": str(artifact), "sha256": sha256_file(artifact), "kind": "candidate-glb"},
                {"path": render["media"]["path"], "sha256": render["media"]["fileSha256"], "kind": "canonical-fixed-camera-png"},
                {"path": comparison["review"]["path"], "sha256": comparison["review"]["sha256"], "kind": "static-review-html"},
            ],
            metrics={"lockSha256": resolved.lock_sha256, "buildStage": stage, "validation": validation, "comparison": comparison, "render": render, "baselineRender": baseline_render},
            checks={"exactApprovedSha256": True, "independentValidation": True, "deterministicMedia": True, "browsableReview": True},
            source=source, profile=_profile(resolved), tool_versions=_tools(blender=render["blenderVersion"], validator=validation["gltfValidator"]["version"]), repository=repository, started_at=started,
        )
    except Exception as exc:
        return _failure(command="build", args=args, exc=exc, repository=repository, context=context, source=source, resolved=resolved, started=started)
    _output(report, args.json_output)
    return 0


def command_validate(args) -> int:
    started, repository, context, resolved = now_utc(), None, None, None
    source = _unknown_source()
    try:
        repository = repository_root(args.profile)
        context = create_run_context(repository, args.work_root, "validate")
        source = _source(repository)
        resolved = resolve_profile(args.profile)
        _write_resolved(context, resolved)
        artifact = args.artifact.resolve()
        validation = _bind_evidence(validate_candidate(resolved, artifact), run_id=context.run_id, source=source)
        validate_document(validation, repository=repository, label="validation evidence")
        write_json(context.run_dir / "validation.json", validation)
        report = emit_report(
            context.run_dir / "run-report.json", command="validate", status="PASS", run_id=context.run_id,
            inputs=[{"path": str(artifact), "sha256": sha256_file(artifact), "kind": "candidate-glb"}], metrics=validation,
            checks={"allValidators": True}, source=source, profile=_profile(resolved),
            tool_versions=_tools(validator=validation["gltfValidator"]["version"]), repository=repository, started_at=started,
        )
    except Exception as exc:
        return _failure(command="validate", args=args, exc=exc, repository=repository, context=context, source=source, resolved=resolved, started=started)
    _output(report, args.json_output)
    return 0


def command_compare(args) -> int:
    started, repository, context, resolved = now_utc(), None, None, None
    source = _unknown_source()
    try:
        repository = repository_root(args.profile)
        context = create_run_context(repository, args.work_root, "compare")
        source = _source(repository)
        resolved = resolve_profile(args.profile)
        _write_resolved(context, resolved)
        baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
        _, render, comparison = _comparison_bundle(resolved=resolved, baseline=baseline, candidate=candidate, context=context, source=source)
        write_json(context.run_dir / "comparison.json", comparison)
        report = emit_report(
            context.run_dir / "run-report.json", command="compare", status="PASS", run_id=context.run_id,
            inputs=[{"path": str(baseline), "sha256": sha256_file(baseline), "kind": "baseline-glb"}, {"path": str(candidate), "sha256": sha256_file(candidate), "kind": "candidate-glb"}],
            outputs=[{"path": comparison["review"]["path"], "sha256": comparison["review"]["sha256"], "kind": "static-review-html"}],
            metrics=comparison, checks={"technicalComparison": True, "declaredContactFacts": True, "mediaComparison": True, "browsableReview": True},
            source=source, profile=_profile(resolved), tool_versions=_tools(blender=render["blenderVersion"]), repository=repository, started_at=started,
        )
    except Exception as exc:
        return _failure(command="compare", args=args, exc=exc, repository=repository, context=context, source=source, resolved=resolved, started=started)
    _output(report, args.json_output)
    return 0


def command_render(args) -> int:
    started, repository, context, resolved = now_utc(), None, None, None
    source = _unknown_source()
    try:
        repository = repository_root(args.profile)
        context = create_run_context(repository, args.work_root, "render")
        source = _source(repository)
        resolved = resolve_profile(args.profile)
        _write_resolved(context, resolved)
        artifact = args.artifact.resolve()
        render = _render_one(resolved=resolved, artifact=artifact, output=context.run_dir / "renders/review.png", stage_report=context.run_dir / "render.json", log_path=context.run_dir / "blender-render.log", context=context, source=source)
        report = emit_report(
            context.run_dir / "run-report.json", command="render", status="PASS", run_id=context.run_id,
            inputs=[{"path": str(artifact), "sha256": sha256_file(artifact), "kind": "candidate-glb"}],
            outputs=[{"path": render["media"]["path"], "sha256": render["media"]["fileSha256"], "kind": "canonical-fixed-camera-png"}],
            metrics=render, checks={"realBlenderRender": True, "canonicalPng": True}, source=source, profile=_profile(resolved), tool_versions=_tools(blender=render["blenderVersion"]), repository=repository, started_at=started,
        )
    except Exception as exc:
        return _failure(command="render", args=args, exc=exc, repository=repository, context=context, source=source, resolved=resolved, started=started)
    _output(report, args.json_output)
    return 0


def command_promote(args) -> int:
    started, repository, context, resolved = now_utc(), None, None, None
    source = _unknown_source()
    try:
        runtime = json.loads((args.run.resolve() / "resolved-profile.json").read_text())
        repository = Path(runtime["repository"]).resolve()
        context = create_run_context(repository, args.work_root, "promote")
        source = _source(repository)
        resolved = resolve_profile(Path(runtime["profilePath"]))
        result = promote_run(run_dir=args.run.resolve(), destination=args.destination.resolve(), approvals_path=args.approvals.resolve())
        report = emit_report(
            context.run_dir / "run-report.json", command="promote", status="PASS", run_id=context.run_id,
            inputs=[{"path": str(args.run.resolve()), "sha256": None, "kind": "passing-build-run"}, {"path": str(args.approvals.resolve()), "sha256": sha256_file(args.approvals.resolve()), "kind": "independent-approvals"}],
            outputs=[{"path": result["destination"], "sha256": result["artifactSha256"], "kind": "immutable-release-directory"}], metrics=result,
            checks={"approvalGate": True, "noOverwrite": True, "sourceLock": True, "artifactHash": True, "provenance": True, "evidenceBinding": True},
            source=source, profile=_profile(resolved), tool_versions=_tools(), repository=repository, started_at=started,
        )
    except Exception as exc:
        return _failure(command="promote", args=args, exc=exc, repository=repository, context=context, source=source, resolved=resolved, started=started)
    _output(report, args.json_output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eonwild-motion")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("build", command_build), ("validate", command_validate), ("compare", command_compare), ("render", command_render)):
        command = subparsers.add_parser(name)
        command.add_argument("--profile", type=Path, required=True)
        command.add_argument("--work-root", type=Path, default=default_work_root())
        command.add_argument("--json-output", type=Path)
        command.set_defaults(handler=handler)
    subparsers.choices["validate"].add_argument("--artifact", type=Path, required=True)
    subparsers.choices["compare"].add_argument("--baseline", type=Path, required=True)
    subparsers.choices["compare"].add_argument("--candidate", type=Path, required=True)
    subparsers.choices["render"].add_argument("--artifact", type=Path, required=True)
    promote = subparsers.add_parser("promote")
    promote.add_argument("--run", type=Path, required=True)
    promote.add_argument("--destination", type=Path, required=True)
    promote.add_argument("--approvals", type=Path, required=True)
    promote.add_argument("--work-root", type=Path, default=default_work_root())
    promote.add_argument("--json-output", type=Path)
    promote.set_defaults(handler=command_promote)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except Exception as exc:
        return _failure(command=args.command, args=args, exc=exc, repository=None, context=None, source=_unknown_source(), started=now_utc())


if __name__ == "__main__":
    raise SystemExit(main())
