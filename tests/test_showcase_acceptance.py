"""A good-looking preview must never hide mechanical or missing evidence."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from eonwild_motion.errors import ContractError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eonwild_showcase_under_test", ROOT / "tools/build_showcase.py")
showcase = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(showcase)


def passing_row():
    return {"generation": "PASS", "integrity": {"integrity": "PASS", "technical_status": "PASS"},
            "renders": {view: {"status": "PASS"} for view in showcase.VIEWS}}


def compile_fake(recipe, *, root, output):
    output.mkdir()
    (output / "validation.json").write_text(json.dumps({"technical_status": "BLOCKED"}))
    return {"files": {}}


class ShowcaseAcceptanceTests(unittest.TestCase):
    def test_mechanical_rejection_survives_successful_renders(self):
        row = passing_row()
        row["integrity"]["technical_status"] = "BLOCKED"
        self.assertEqual(showcase.exit_status([row], required_views=showcase.VIEWS), 2)

    def test_missing_integrity_or_acceptance_never_passes(self):
        for field in ("integrity", "technical_status"):
            row = passing_row()
            del row["integrity"][field]
            with self.subTest(field=field):
                self.assertNotEqual(showcase.exit_status([row]), 0)
        for value in (None, [], "PASS"):
            row = passing_row()
            row["integrity"] = value
            self.assertEqual(showcase.exit_status([row]), 1)

    def test_missing_or_failed_requested_view_is_failure(self):
        for view in showcase.VIEWS:
            for missing in (False, True):
                row = passing_row()
                if missing:
                    del row["renders"][view]
                else:
                    row["renders"][view]["status"] = "FAIL"
                with self.subTest(view=view, missing=missing):
                    self.assertEqual(showcase.exit_status([row], required_views=showcase.VIEWS), 1)

    def test_reference_failure_cannot_be_replaced_by_unlocked_candidate(self):
        row = passing_row()
        row["reference_renders"] = deepcopy(row["renders"])
        del row["reference_renders"]["rear"]
        self.assertEqual(showcase.exit_status([row], required_views=showcase.VIEWS), 1)

    def test_generation_failure_and_empty_result_are_errors(self):
        self.assertEqual(showcase.exit_status([]), 1)
        self.assertEqual(showcase.exit_status([passing_row(), {"generation": "FAIL"}]), 1)

    def test_valid_nonrendered_generation_has_separate_technical_status(self):
        self.assertEqual(showcase.exit_status([passing_row()]), 0)
        self.assertEqual(showcase.exit_status([passing_row()], required_views=showcase.VIEWS), 0)

    def test_cli_preserves_blocked_package_and_returns_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "showcase"
            with patch.object(showcase, "compile_recipe", side_effect=compile_fake), patch.object(
                    showcase, "verify_package", return_value={"integrity": "PASS", "technical_status": "BLOCKED"}):
                code = showcase.main(["--output", str(output), "--recipes", "walk.v2"])
            self.assertEqual(code, 2)
            self.assertTrue((output / "walk.v2/validation.json").is_file())
            summary = json.loads((output / "showcase.json").read_text())
            self.assertEqual(summary["exit_code"], 2)
            self.assertIs(summary["production_approved"], False)
            self.assertEqual(summary["unity_validation"], "NOT_RUN")

    def test_post_render_mutation_is_rejected_by_fresh_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "showcase"
            with patch.object(showcase, "compile_recipe", side_effect=compile_fake), patch.object(
                    showcase, "verify_package", side_effect=[
                        {"integrity": "PASS", "technical_status": "BLOCKED"},
                        ContractError("package hash changed after render")]) as verify, patch.object(
                    showcase, "render_view", return_value={"status": "PASS"}):
                code = showcase.main(["--output", str(output), "--recipes", "walk.v2", "--render", "--views", "side"])
            self.assertEqual(verify.call_count, 2)
            self.assertEqual(code, 1)
            summary = json.loads((output / "showcase.json").read_text())
            self.assertIn("hash changed after render", summary["results"][0]["error"])

    def test_invalid_or_repeated_recipe_cannot_create_output(self):
        for names in (("../walk.v2",), ("walk.v2", "walk.v2")):
            with tempfile.TemporaryDirectory() as folder:
                output = Path(folder) / "must-not-exist"
                with self.assertRaises(SystemExit):
                    showcase.main(["--output", str(output), "--recipes", *names])
                self.assertFalse(output.exists())

    def test_renderer_timeout_is_not_a_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(showcase.subprocess, "run", side_effect=subprocess.TimeoutExpired("blender", 1800, output=b"partial frames")):
                result = showcase.render_view(root / "package", root / "views/side", root=ROOT,
                    blender="blender", view="side", mode="root_motion", fps=24, fbx=False)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("RENDER_TIMEOUT", Path(result["log"]).read_text())


if __name__ == "__main__":
    unittest.main()
