from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from eonwild_motion.contracts.resolve import resolve_profile
from eonwild_motion.errors import ValidationFailure
from eonwild_motion.hashing import sha256_file
from eonwild_motion.pipeline.promote import promote_run


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles/v8.2/profile.json"
APPROVED_SHA = "a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5"


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
        cls.builds = []
        for index in range(2):
            work = cls.root / f"build-{index}"
            process = cli(
                "build",
                "--profile",
                str(PROFILE),
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

    def test_validate_and_compare_commands(self):
        artifact = self.builds[0][1]["outputs"][0]["path"]
        validate_work = self.root / "validate"
        validate = cli(
            "validate",
            "--profile",
            str(PROFILE),
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
            str(PROFILE),
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
            comparison["difference"]["outsideDeclaredByteChanges"], 0
        )

    def test_real_blender_render(self):
        artifact = self.builds[0][1]["outputs"][0]["path"]
        render_work = self.root / "render"
        render = cli(
            "render",
            "--profile",
            str(PROFILE),
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

    def test_nonpromotion_commands_leave_source_status_unchanged(self):
        after = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
        )
        self.assertEqual(after, self.before_status)

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


if __name__ == "__main__":
    unittest.main()
