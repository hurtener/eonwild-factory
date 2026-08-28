from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid
from contextlib import contextmanager
import shutil
from dataclasses import replace

from eonwild_motion.contracts.resolve import resolve_profile
from eonwild_motion.errors import ValidationFailure
from eonwild_motion.hashing import sha256_file
from eonwild_motion.pipeline.channels import update_stable_channel
from eonwild_motion.pipeline.promote import promote_run
from eonwild_motion.pipeline.validate import contact_inheritance_facts
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles/v8.2/profile.json"
APPROVED_SHA = "b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03"


def cli(*arguments: str) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "eonwild_motion", *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )


def one_run(work_root: Path, command: str) -> Path:
    runs = list((work_root / "runs").glob(f"*-{command}-*"))
    if len(runs) != 1:
        raise AssertionError(f"expected one {command} run, got {runs}")
    return runs[0]


def assert_run_report(test: unittest.TestCase, report: dict) -> None:
    schema = json.loads(
        (ROOT / "schemas/motion/run-report.v1.schema.json").read_text()
    )
    errors = list(Draft202012Validator(schema).iter_errors(report))
    test.assertEqual(errors, [], [error.message for error in errors])


@contextmanager
def replaced(path: Path, content: bytes | None):
    original = path.read_bytes()
    try:
        if content is None:
            path.unlink()
        else:
            path.write_bytes(content)
        yield
    finally:
        path.write_bytes(original)


class VerticalSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.before_status = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
        )
        cls.channel_state_bytes = (ROOT / "profiles/channels/state.json").read_bytes()
        cls.builds = []
        for index in range(2):
            work = cls.root / f"build-{index}"
            process = cli(
                "build",
                "--profile",
                "working",
                "--work-root",
                str(work),
            )
            if process.returncode != 0:
                raise AssertionError(process.stdout + process.stderr)
            run = one_run(work, "build")
            report = json.loads((run / "run-report.json").read_text())
            cls.builds.append((run, report))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_exact_double_build_determinism(self):
        hashes = [report["outputs"][0]["sha256"] for _, report in self.builds]
        self.assertEqual(hashes, [APPROVED_SHA, APPROVED_SHA])
        locks = [report["metrics"]["lockSha256"] for _, report in self.builds]
        self.assertEqual(locks[0], locks[1])
        first = Path(self.builds[0][1]["outputs"][0]["path"])
        second = Path(self.builds[1][1]["outputs"][0]["path"])
        self.assertEqual(first.read_bytes(), second.read_bytes())
        for _, report in self.builds:
            self.assertEqual(report["profile"]["channel"], "working")
            self.assertEqual(report["profile"]["iteration"], 1)
            self.assertEqual(report["profile"]["revision"], 2)
        render_reports = [json.loads((run / "render.json").read_text()) for run, _ in self.builds]
        self.assertEqual(
            render_reports[0]["media"]["fileSha256"],
            render_reports[1]["media"]["fileSha256"],
        )
        self.assertEqual(
            render_reports[0]["media"]["pixelContentSha256"],
            render_reports[1]["media"]["pixelContentSha256"],
        )
        self.assertEqual(
            Path(render_reports[0]["media"]["path"]).read_bytes(),
            Path(render_reports[1]["media"]["path"]).read_bytes(),
        )

    def test_validate_and_compare_commands(self):
        artifact = self.builds[0][1]["outputs"][0]["path"]
        validate_work = self.root / "validate"
        validate = cli(
            "validate",
            "--profile",
            "working",
            "--artifact",
            artifact,
            "--work-root",
            str(validate_work),
        )
        self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
        compare_work = self.root / "compare"
        resolved = resolve_profile(PROFILE)
        compare = cli(
            "compare",
            "--profile",
            "working",
            "--baseline",
            str(resolved.input_path),
            "--candidate",
            artifact,
            "--work-root",
            str(compare_work),
        )
        self.assertEqual(compare.returncode, 0, compare.stdout + compare.stderr)
        comparison = json.loads(
            (one_run(compare_work, "compare") / "comparison.json").read_text()
        )
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(
            comparison["structural"]["outsideDeclaredByteChanges"], 0
        )
        self.assertEqual(comparison["contactFacts"]["status"], "PASS")
        self.assertEqual(comparison["media"]["status"], "PASS")
        review = Path(comparison["review"]["path"])
        self.assertIn("does not grant visual approval", review.read_text())

    def test_normative_evidence_fails_closed_on_controlled_corruption(self):
        resolved = resolve_profile("working")
        original = json.loads(resolved.contact_evidence_path.read_text())

        def reject(mutator):
            document = json.loads(json.dumps(original))
            mutator(document)
            path = self.root / f"corrupt-{uuid.uuid4().hex}.json"
            path.write_text(json.dumps(document))
            corrupted = replace(
                resolved,
                contact_evidence_path=path,
                contact_evidence_sha256=sha256_file(path),
            )
            with self.assertRaises(ValidationFailure):
                contact_inheritance_facts(corrupted)

        reject(lambda value: value.update(status="FAIL"))
        reject(lambda value: value.update(artifactSha256="0" * 64))
        reject(lambda value: value.update(selectedScale=999))
        reject(lambda value: value.update(metrics={key: None for key in value["metrics"]}))
        reject(lambda value: value["metrics"].pop("strideMetres"))
        reject(lambda value: value["metrics"].update(strideMetres=float("nan")))
        reject(lambda value: value["evidence"].update(thresholds=value["evidence"]["sweep"]))
        reject(lambda value: value["evidence"].pop("sweep"))

    def test_normative_evidence_rejects_cross_document_corruption(self):
        resolved = resolve_profile("working")
        threshold_path = ROOT / "reports/PROCEDURAL-ENGINE-V8-3/evaluation/thresholds.json"
        sweep_path = ROOT / "reports/PROCEDURAL-ENGINE-V8-3/evidence/amplitude-sweep.json"
        witness_path = ROOT / "reports/PROCEDURAL-ENGINE-V8-3/evidence/final-skinned-witnesses.json"

        thresholds = json.loads(threshold_path.read_text())
        thresholds["basis"]["sourceStableArtifactSha256"] = "0" * 64
        with replaced(threshold_path, (json.dumps(thresholds) + "\n").encode()):
            with self.assertRaises(ValidationFailure):
                contact_inheritance_facts(resolved)

        sweep = json.loads(sweep_path.read_text())
        sweep["scales"][0]["status"] = "FAIL"
        with replaced(sweep_path, (json.dumps(sweep) + "\n").encode()):
            with self.assertRaises(ValidationFailure):
                contact_inheritance_facts(resolved)

        sweep = json.loads(sweep_path.read_text())
        sweep["selectedScale"] = 0.625
        with replaced(sweep_path, (json.dumps(sweep) + "\n").encode()):
            with self.assertRaises(ValidationFailure):
                contact_inheritance_facts(resolved)

        witness = json.loads(witness_path.read_text())
        witness["maxEuclideanRegressionMetres"] = 0.5
        with replaced(witness_path, (json.dumps(witness) + "\n").encode()):
            with self.assertRaises(ValidationFailure):
                contact_inheritance_facts(resolved)

    def test_real_blender_render(self):
        artifact = self.builds[0][1]["outputs"][0]["path"]
        render_work = self.root / "render"
        render = cli(
            "render",
            "--profile",
            "working",
            "--artifact",
            artifact,
            "--work-root",
            str(render_work),
        )
        self.assertEqual(render.returncode, 0, render.stdout + render.stderr)
        report = json.loads(
            (one_run(render_work, "render") / "run-report.json").read_text()
        )
        image = Path(report["outputs"][0]["path"])
        self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(report["metrics"]["blenderVersion"], "5.2.0 LTS")
        self.assertEqual(report["metrics"]["media"]["fileSha256"], sha256_file(image))
        assert_run_report(self, report)

    def test_nonpromotion_commands_leave_source_status_unchanged(self):
        after = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
        )
        self.assertEqual(after, self.before_status)
        self.assertEqual(
            (ROOT / "profiles/channels/state.json").read_bytes(),
            self.channel_state_bytes,
        )
        self.assertFalse((ROOT / "profiles/channels/history").exists())

    def test_promotion_gates_and_no_overwrite(self):
        run, report = self.builds[0]
        report["source"]["dirty"] = False
        (run / "run-report.json").write_text(json.dumps(report))
        approvals = self.root / "approvals.json"
        approvals.write_text(
            json.dumps(
                {
                    "schema": "eonwild.motion.promotion.v1",
                    "technical": {
                        "status": "APPROVED",
                        "reviewer": "technical-reviewer",
                    },
                    "visual": {
                        "status": "APPROVED",
                        "reviewer": "visual-reviewer",
                    },
                }
            )
        )
        destination = self.root / "promoted-release"
        state = lambda _: {
            "dirty": False,
            "gitHead": report["source"]["gitHead"],
        }
        promoted = promote_run(
            run_dir=run,
            destination=destination,
            approvals_path=approvals,
            source_state=state,
        )
        self.assertEqual(promoted["artifactSha256"], APPROVED_SHA)
        self.assertTrue((destination / "manifest.json").is_file())
        self.assertTrue((destination / "evidence/media/candidate.png").is_file())
        with self.assertRaises(ValidationFailure):
            promote_run(
                run_dir=run,
                destination=destination,
                approvals_path=approvals,
                source_state=state,
            )
        with self.assertRaises(ValidationFailure):
            promote_run(
                run_dir=run,
                destination=self.root / "dirty-release",
                approvals_path=approvals,
                source_state=lambda _: {
                    "dirty": True,
                    "gitHead": report["source"]["gitHead"],
                },
            )
        artifact = Path(report["outputs"][0]["path"])
        original = artifact.read_bytes()
        try:
            artifact.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            with self.assertRaises(ValidationFailure):
                promote_run(
                    run_dir=run,
                    destination=self.root / "hash-release",
                    approvals_path=approvals,
                    source_state=state,
                )
        finally:
            artifact.write_bytes(original)
        channel_root = self.root / "approved-channel-update"
        channel_root.mkdir()
        channel_state = channel_root / "state.json"
        shutil.copyfile(ROOT / "profiles/channels/state.json", channel_state)
        runtime_path = run / "resolved-profile.json"
        runtime = json.loads(runtime_path.read_text())
        runtime["channelStatePath"] = str(channel_state)
        release_root = ROOT / "releases"
        release_root_existed = release_root.exists()
        release_root.mkdir(exist_ok=True)
        if not release_root_existed:
            self.addCleanup(release_root.rmdir)
        stable_destination = release_root / f"test-{uuid.uuid4().hex}"
        self.addCleanup(shutil.rmtree, stable_destination, True)
        with replaced(runtime_path, (json.dumps(runtime, indent=2, sort_keys=True) + "\n").encode()):
            channel_promotion = promote_run(
                run_dir=run,
                destination=stable_destination,
                approvals_path=approvals,
                source_state=state,
                update_stable=True,
                channel_state_path=channel_state,
            )
        self.assertEqual(channel_promotion["channelUpdate"]["generation"], 2)
        self.assertEqual(json.loads(channel_state.read_text())["generation"], 2)
        self.assertTrue(Path(channel_promotion["channelUpdate"]["historyPath"]).is_file())
        updated_state = json.loads(channel_state.read_text())
        self.assertEqual(
            ROOT / updated_state["stable"]["release"]["manifest"]["path"],
            stable_destination / "manifest.json",
        )
        self.assertEqual(
            ROOT / updated_state["stable"]["release"]["artifact"]["path"],
            Path(channel_promotion["channelUpdate"]["artifactPath"]),
        )
        stable = resolve_profile("stable", repository=ROOT, channel_state_path=channel_state)
        self.assertEqual(stable.approved_output_path, Path(channel_promotion["channelUpdate"]["artifactPath"]))

        rollback_root = channel_root / "rollback"
        rollback_root.mkdir()
        rollback_state = rollback_root / "state.json"
        shutil.copyfile(ROOT / "profiles/channels/state.json", rollback_state)
        rollback_original = rollback_state.read_bytes()
        rollback_runtime = json.loads(runtime_path.read_text())
        rollback_runtime["channelStatePath"] = str(rollback_state)
        rollback_destination = release_root / f"test-rollback-{uuid.uuid4().hex}"
        self.addCleanup(shutil.rmtree, rollback_destination, True)

        def inject_after_history(**kwargs):
            def fail(operation):
                if operation == "history-installed":
                    raise OSError("injected failure after history install")

            return update_stable_channel(**kwargs, operation_hook=fail)

        with patch(
            "eonwild_motion.pipeline.promote.update_stable_channel",
            side_effect=inject_after_history,
        ):
            with replaced(
                runtime_path,
                (json.dumps(rollback_runtime, indent=2, sort_keys=True) + "\n").encode(),
            ):
                with self.assertRaises(OSError):
                    promote_run(
                        run_dir=run,
                        destination=rollback_destination,
                        approvals_path=approvals,
                        source_state=state,
                        update_stable=True,
                        channel_state_path=rollback_state,
                    )
        self.assertFalse(rollback_destination.exists())
        self.assertEqual(rollback_state.read_bytes(), rollback_original)
        self.assertFalse((rollback_state.parent / "history").exists())
        with replaced(
            runtime_path,
            (json.dumps(rollback_runtime, indent=2, sort_keys=True) + "\n").encode(),
        ):
            retry = promote_run(
                run_dir=run,
                destination=rollback_destination,
                approvals_path=approvals,
                source_state=state,
                update_stable=True,
                channel_state_path=rollback_state,
            )
        self.assertEqual(retry["channelUpdate"]["generation"], 2)
        self.assertTrue(rollback_destination.is_dir())

    def test_promotion_rejects_untrusted_evidence(self):
        run, report = self.builds[1]
        report["source"]["dirty"] = False
        (run / "run-report.json").write_text(json.dumps(report))
        approvals = self.root / "evidence-approvals.json"
        approvals.write_text(json.dumps({
            "schema": "eonwild.motion.promotion.v1",
            "technical": {"status": "APPROVED", "reviewer": "reviewer-a"},
            "visual": {"status": "APPROVED", "reviewer": "reviewer-b"},
        }))
        state = lambda _: {"dirty": False, "gitHead": report["source"]["gitHead"]}
        validation = run / "validation.json"
        comparison = run / "comparison.json"
        render = run / "render.json"
        stripped_validation = json.loads(validation.read_text())
        stripped_validation["contactFacts"] = {"status": "PASS"}
        cases = [
            ("empty", validation, b"{}\n"),
            ("malformed", validation, b"{not json"),
            ("failing", validation, validation.read_bytes().replace(b'"PASS"', b'"FAIL"', 1)),
            ("cross-run", comparison, comparison.read_bytes().replace(report["runId"].encode(), b"another-run")),
            ("wrong-artifact", render, render.read_bytes().replace(APPROVED_SHA.encode(), ("0" * 64).encode())),
            ("missing-render", render, None),
            ("stripped-contact-facts", validation, json.dumps(stripped_validation).encode()),
        ]
        for name, path, content in cases:
            with self.subTest(name=name), replaced(path, content):
                with self.assertRaises((ValidationFailure, Exception)):
                    promote_run(
                        run_dir=run,
                        destination=self.root / f"rejected-{name}",
                        approvals_path=approvals,
                        source_state=state,
                    )

    def test_all_success_and_precontext_failure_reports_validate(self):
        for run, report in self.builds:
            assert_run_report(self, report)
        work = self.root / "missing-profile"
        process = cli(
            "build",
            "--profile",
            str(self.root / "does-not-exist/profile.json"),
            "--work-root",
            str(work),
        )
        self.assertNotEqual(process.returncode, 0)
        failure = json.loads(process.stdout)
        self.assertEqual(failure["status"], "FAIL")
        assert_run_report(self, failure)
        promotion_work = self.root / "missing-promotion"
        missing = cli(
            "promote",
            "--run",
            str(self.root / "missing-run"),
            "--destination",
            str(self.root / "never-created"),
            "--approvals",
            str(self.root / "missing-approvals.json"),
            "--work-root",
            str(promotion_work),
        )
        self.assertNotEqual(missing.returncode, 0)
        assert_run_report(self, json.loads(missing.stdout))
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = str(ROOT / "src")
        outside = subprocess.run(
            [
                sys.executable,
                "-m",
                "eonwild_motion",
                "build",
                "--profile",
                str(self.root / "also-missing.json"),
                "--work-root",
                str(self.root / "outside-cwd-work"),
            ],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(outside.returncode, 0)
        assert_run_report(self, json.loads(outside.stdout))


if __name__ == "__main__":
    unittest.main()
