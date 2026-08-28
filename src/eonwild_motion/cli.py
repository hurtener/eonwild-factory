from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from . import __version__
from .contracts.resolve import resolve_profile
from .errors import MotionError
from .hashing import sha256_file, write_json
from .paths import default_work_root, repository_root
from .pipeline.build import invoke_blender_build
from .pipeline.compare import compare_artifacts
from .pipeline.context import create_run_context, git_source_state
from .pipeline.promote import promote_run
from .pipeline.render import invoke_blender_render
from .pipeline.validate import validate_candidate
from .reports import emit_report, now_utc


def _source(repository: Path) -> dict:
    state = git_source_state(repository)
    implementer = subprocess.check_output(
        ["git", "config", "--get", "user.email"],
        cwd=repository,
        text=True,
    ).strip()
    return {
        **state,
        "implementer": implementer,
        "engineVersion": __version__,
    }


def _runtime_document(resolved) -> dict:
    return {
        **resolved.runtime_document(),
        "repository": str(resolved.repository),
        "profilePath": str(resolved.profile_path),
    }


def _output(report: dict, explicit: Path | None) -> None:
    if explicit is not None:
        write_json(explicit, report)
    print(json.dumps(report, indent=2, sort_keys=True))


def command_build(args) -> int:
    repository = repository_root(args.profile)
    context = create_run_context(repository, args.work_root, "build")
    started = now_utc()
    source = _source(repository)
    resolved = None
    try:
        resolved = resolve_profile(args.profile)
        runtime_path = context.run_dir / "resolved-profile.json"
        write_json(runtime_path, _runtime_document(resolved))
        artifact = context.run_dir / "artifacts/candidate.glb"
        stage_report = context.run_dir / "build-stage.json"
        request_path = context.run_dir / "build-request.json"
        write_json(
            request_path,
            {
                "schema": "eonwild.motion.build-request.v1",
                "resolved": resolved.runtime_document(),
                "outputPath": str(artifact),
                "stageReportPath": str(stage_report),
            },
        )
        stage = invoke_blender_build(
            repository=resolved.repository,
            request_path=request_path,
            log_path=context.run_dir / "blender-build.log",
        )
        validation = validate_candidate(resolved, artifact)
        comparison = compare_artifacts(
            resolved, resolved.input_path, artifact
        )
        write_json(context.run_dir / "validation.json", validation)
        write_json(context.run_dir / "comparison.json", comparison)
        report = emit_report(
            context.run_dir / "run-report.json",
            command="build",
            status="PASS",
            run_id=context.run_id,
            inputs=[
                {
                    "path": str(resolved.input_path),
                    "sha256": resolved.input_sha256,
                    "kind": "immutable-glb",
                }
            ],
            outputs=[
                {
                    "path": str(artifact),
                    "sha256": sha256_file(artifact),
                    "kind": "candidate-glb",
                }
            ],
            metrics={
                "lockSha256": resolved.lock_sha256,
                "buildStage": stage,
                "validation": validation,
            },
            checks={"exactApprovedSha256": True, "independentValidation": True},
            source=source,
            started_at=started,
        )
    except Exception as exc:
        report = emit_report(
            context.run_dir / "run-report.json",
            command="build",
            status="FAIL",
            run_id=context.run_id,
            errors=[str(exc)],
            metrics={
                "lockSha256": resolved.lock_sha256 if resolved else None
            },
            source=source,
            started_at=started,
        )
        _output(report, args.json_output)
        return 1
    _output(report, args.json_output)
    return 0


def command_validate(args) -> int:
    repository = repository_root(args.profile)
    context = create_run_context(repository, args.work_root, "validate")
    source = _source(repository)
    try:
        resolved = resolve_profile(args.profile)
        validation = validate_candidate(resolved, args.artifact.resolve())
        write_json(context.run_dir / "validation.json", validation)
        report = emit_report(
            context.run_dir / "run-report.json",
            command="validate",
            status="PASS",
            run_id=context.run_id,
            inputs=[
                {
                    "path": str(args.artifact.resolve()),
                    "sha256": sha256_file(args.artifact.resolve()),
                    "kind": "candidate-glb",
                }
            ],
            metrics=validation,
            checks={"allValidators": True},
            source=source,
        )
    except Exception as exc:
        report = emit_report(
            context.run_dir / "run-report.json",
            command="validate",
            status="FAIL",
            run_id=context.run_id,
            errors=[str(exc)],
            source=source,
        )
        _output(report, args.json_output)
        return 1
    _output(report, args.json_output)
    return 0


def command_compare(args) -> int:
    repository = repository_root(args.profile)
    context = create_run_context(repository, args.work_root, "compare")
    source = _source(repository)
    try:
        resolved = resolve_profile(args.profile)
        comparison = compare_artifacts(
            resolved, args.baseline.resolve(), args.candidate.resolve()
        )
        write_json(context.run_dir / "comparison.json", comparison)
        report = emit_report(
            context.run_dir / "run-report.json",
            command="compare",
            status="PASS",
            run_id=context.run_id,
            inputs=[
                {"path": str(args.baseline.resolve()), "kind": "baseline-glb"},
                {"path": str(args.candidate.resolve()), "kind": "candidate-glb"},
            ],
            metrics=comparison,
            checks={"technicalComparison": True},
            source=source,
        )
    except Exception as exc:
        report = emit_report(
            context.run_dir / "run-report.json",
            command="compare",
            status="FAIL",
            run_id=context.run_id,
            errors=[str(exc)],
            source=source,
        )
        _output(report, args.json_output)
        return 1
    _output(report, args.json_output)
    return 0


def command_render(args) -> int:
    repository = repository_root(args.profile)
    context = create_run_context(repository, args.work_root, "render")
    source = _source(repository)
    try:
        resolved = resolve_profile(args.profile)
        clip = resolved.motion["clips"][0]
        output = context.run_dir / "renders/review.png"
        request = context.run_dir / "render-request.json"
        write_json(
            request,
            {
                "schema": "eonwild.motion.render-request.v1",
                "artifactPath": str(args.artifact.resolve()),
                "clipSemanticId": clip["semanticId"],
                "clipName": clip["name"],
                "renderSet": resolved.render_set,
                "outputPath": str(output),
                "stageReportPath": str(context.run_dir / "render.json"),
            },
        )
        render = invoke_blender_render(
            repository=resolved.repository,
            request_path=request,
            log_path=context.run_dir / "blender-render.log",
        )
        report = emit_report(
            context.run_dir / "run-report.json",
            command="render",
            status="PASS",
            run_id=context.run_id,
            inputs=[
                {
                    "path": str(args.artifact.resolve()),
                    "sha256": sha256_file(args.artifact.resolve()),
                    "kind": "candidate-glb",
                }
            ],
            outputs=[
                {
                    "path": str(output),
                    "sha256": sha256_file(output),
                    "kind": "fixed-camera-png",
                }
            ],
            metrics=render,
            checks={"realBlenderRender": True},
            source=source,
        )
    except Exception as exc:
        report = emit_report(
            context.run_dir / "run-report.json",
            command="render",
            status="FAIL",
            run_id=context.run_id,
            errors=[str(exc)],
            source=source,
        )
        _output(report, args.json_output)
        return 1
    _output(report, args.json_output)
    return 0


def command_promote(args) -> int:
    source = {}
    context = None
    started = now_utc()
    try:
        runtime = json.loads(
            (args.run.resolve() / "resolved-profile.json").read_text()
        )
        repository = Path(runtime["repository"]).resolve()
        context = create_run_context(repository, args.work_root, "promote")
        source = _source(repository)
        result = promote_run(
            run_dir=args.run.resolve(),
            destination=args.destination.resolve(),
            approvals_path=args.approvals.resolve(),
        )
        report = emit_report(
            context.run_dir / "run-report.json",
            command="promote",
            status="PASS",
            run_id=context.run_id,
            inputs=[
                {"path": str(args.run.resolve()), "kind": "passing-build-run"},
                {
                    "path": str(args.approvals.resolve()),
                    "kind": "independent-approvals",
                },
            ],
            outputs=[
                {
                    "path": result["destination"],
                    "sha256": result["artifactSha256"],
                    "kind": "immutable-release-directory",
                }
            ],
            metrics=result,
            checks={
                "approvalGate": True,
                "noOverwrite": True,
                "sourceLock": True,
                "artifactHash": True,
                "provenance": True,
            },
            source=source,
            started_at=started,
        )
    except Exception as exc:
        if context is None:
            result = {"status": "FAIL", "error": str(exc)}
            _output(result, args.json_output)
            return 1
        report = emit_report(
            context.run_dir / "run-report.json",
            command="promote",
            status="FAIL",
            run_id=context.run_id,
            errors=[str(exc)],
            source=source,
            started_at=started,
        )
        _output(report, args.json_output)
        return 1
    _output(report, args.json_output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eonwild-motion")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, handler in (
        ("build", command_build),
        ("validate", command_validate),
        ("compare", command_compare),
        ("render", command_render),
    ):
        command = subparsers.add_parser(name)
        command.add_argument("--profile", type=Path, required=True)
        command.add_argument("--work-root", type=Path, default=default_work_root())
        command.add_argument("--json-output", type=Path)
        command.set_defaults(handler=handler)
    subparsers.choices["validate"].add_argument(
        "--artifact", type=Path, required=True
    )
    subparsers.choices["compare"].add_argument(
        "--baseline", type=Path, required=True
    )
    subparsers.choices["compare"].add_argument(
        "--candidate", type=Path, required=True
    )
    subparsers.choices["render"].add_argument(
        "--artifact", type=Path, required=True
    )
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
    except MotionError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
