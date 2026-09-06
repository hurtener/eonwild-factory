from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from eonwild_motion.errors import MotionError
from eonwild_motion.pipeline.build import invoke_blender_build


class BlenderFailureDiagnosticsTests(unittest.TestCase):
    def test_failure_preserves_full_log_and_actionable_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = "old progress\n" * 1000
            error = "ValidationFailure: approved output hash mismatch\n"
            process = subprocess.CompletedProcess(["blender"], 1, output, error)
            with patch("eonwild_motion.pipeline.build.subprocess.run", return_value=process):
                with self.assertRaises(MotionError) as caught:
                    invoke_blender_build(repository=root, request_path=root / "request.json", log_path=root / "blender.log")
            self.assertEqual((root / "blender.log").read_text(), output + error)
            message = str(caught.exception)
            self.assertIn("Blender build failed with exit 1", message)
            self.assertTrue(message.endswith((output + error)[-4000:]))
            self.assertLess(len(message), 4400)

    def test_empty_failure_does_not_invent_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("eonwild_motion.pipeline.build.subprocess.run", return_value=subprocess.CompletedProcess(["blender"], 139, "", "")):
                with self.assertRaises(MotionError) as caught:
                    invoke_blender_build(repository=root, request_path=root / "request.json", log_path=root / "blender.log")
            self.assertIn("exit 139", str(caught.exception))
            self.assertNotIn("output tail", str(caught.exception))
            self.assertEqual((root / "blender.log").read_text(), "")

    def test_success_still_requires_a_passing_stage_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, stage = root / "request.json", root / "stage.json"
            request.write_text(json.dumps({"stageReportPath": str(stage)}))
            process = subprocess.CompletedProcess(["blender"], 0, "completed", "")
            with patch("eonwild_motion.pipeline.build.subprocess.run", return_value=process):
                with self.assertRaisesRegex(MotionError, "did not emit"):
                    invoke_blender_build(repository=root, request_path=request, log_path=root / "blender.log")
                stage.write_text(json.dumps({"status": "FAIL"}))
                with self.assertRaisesRegex(MotionError, "did not pass"):
                    invoke_blender_build(repository=root, request_path=request, log_path=root / "blender.log")
                expected = {"status": "PASS", "outputSha256": "unchanged-test-witness"}
                stage.write_text(json.dumps(expected))
                self.assertEqual(invoke_blender_build(repository=root, request_path=request, log_path=root / "blender.log"), expected)


if __name__ == "__main__":
    unittest.main()
