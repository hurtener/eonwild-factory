from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from eonwild_motion.contracts.resolve import resolve_profile
from eonwild_motion.errors import ContractError, ValidationFailure
from eonwild_motion.pipeline.channels import update_stable_channel


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "profiles/channels/state.json"


class ChannelContractTests(unittest.TestCase):
    def fixture(self, directory: Path, mutate=None) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        state = json.loads(STATE.read_text())
        if mutate is not None:
            mutate(state)
        path = directory / "state.json"
        path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        return path

    def test_stable_working_and_explicit_resolution(self):
        stable = resolve_profile("stable")
        working = resolve_profile("working")
        explicit = resolve_profile(ROOT / "profiles/v8.2/profile.json")
        self.assertEqual(stable.approved_output_sha256, explicit.approved_output_sha256)
        self.assertEqual(working.approved_output_sha256, explicit.approved_output_sha256)
        self.assertEqual(stable.channel["name"], "stable")
        self.assertEqual(working.channel["name"], "working")
        self.assertEqual(working.channel["iteration"], 0)
        self.assertNotEqual(stable.lock_sha256, working.lock_sha256)
        self.assertNotEqual(working.lock_sha256, explicit.lock_sha256)

    def test_missing_invalid_stale_and_engine_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            with self.assertRaises(ContractError):
                resolve_profile("working", repository=ROOT, channel_state_path=directory / "missing.json")
            invalid = directory / "invalid.json"
            invalid.write_text("{}\n")
            with self.assertRaises(ContractError):
                resolve_profile("working", repository=ROOT, channel_state_path=invalid)
            stale = self.fixture(
                directory / "stale",
                lambda state: state["working"]["profile"].__setitem__("sha256", "0" * 64),
            )
            with self.assertRaises(ContractError):
                resolve_profile("working", repository=ROOT, channel_state_path=stale)
            mismatch = self.fixture(
                directory / "mismatch",
                lambda state: state.__setitem__("engineVersion", "9.9.9"),
            )
            with self.assertRaises(ContractError):
                resolve_profile("working", repository=ROOT, channel_state_path=mismatch)

            stale_stable = self.fixture(
                directory / "stale-stable",
                lambda state: state["stable"]["release"]["artifact"].__setitem__(
                    "sha256", "0" * 64
                ),
            )
            with self.assertRaises(ContractError):
                resolve_profile("stable", repository=ROOT, channel_state_path=stale_stable)

    def test_iteration_or_revision_mutation_changes_resolved_lock(self):
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            first_path = self.fixture(directory / "first")
            second_path = self.fixture(
                directory / "second",
                lambda state: state["working"].update({"iteration": 1, "revision": 2}),
            )
            first = resolve_profile("working", repository=ROOT, channel_state_path=first_path)
            second = resolve_profile("working", repository=ROOT, channel_state_path=second_path)
            self.assertNotEqual(first.lock_sha256, second.lock_sha256)
            self.assertEqual(second.profile_binding()["iteration"], 1)
            self.assertEqual(second.profile_binding()["revision"], 2)

    def test_stable_update_retains_history_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory_name:
            root = Path(directory_name)
            state_path = self.fixture(root)
            original = state_path.read_bytes()
            resolved = resolve_profile("working", repository=ROOT, channel_state_path=state_path)
            manifest = root / "promotion-manifest.json"
            manifest.write_text("approved promotion fixture\n")
            result = update_stable_channel(
                state_path=state_path,
                repository=ROOT,
                resolved=resolved,
                promotion_manifest_path=manifest,
            )
            updated = json.loads(state_path.read_text())
            self.assertEqual(updated["generation"], 2)
            self.assertEqual(updated["stable"]["revision"], 2)
            history = Path(result["historyPath"])
            self.assertTrue(history.is_file())
            self.assertEqual(
                json.loads(history.read_text())["priorStateSha256"],
                hashlib.sha256(original).hexdigest(),
            )
            state_path.write_bytes(original)
            with self.assertRaises(ValidationFailure):
                update_stable_channel(
                    state_path=state_path,
                    repository=ROOT,
                    resolved=resolved,
                    promotion_manifest_path=manifest,
                )

    def test_engine_has_no_branch_or_future_version_assumptions(self):
        forbidden = ("codex/", "refs/heads", "git branch", "v8.3", "V8.3")
        for path in (ROOT / "src/eonwild_motion").rglob("*.py"):
            source = path.read_text()
            for marker in forbidden:
                self.assertNotIn(marker, source, f"{marker} leaked into {path}")


if __name__ == "__main__":
    unittest.main()
