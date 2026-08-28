from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from eonwild_motion.contracts.resolve import resolve_profile
from eonwild_motion.errors import ContractError
from eonwild_motion.hashing import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles/v8.2/profile.json"


class ContractTests(unittest.TestCase):
    def test_profile_resolves_to_committed_lock(self):
        resolved = resolve_profile(PROFILE)
        stored = json.loads(PROFILE.with_name("profile.lock.json").read_text())
        self.assertEqual(stored["lockSha256"], resolved.lock_sha256)
        self.assertEqual(stored["profile"]["sha256"], resolved.profile_sha256)
        self.assertEqual(resolved.family["status"], "provisional")

    def test_engine_source_has_no_release_specific_literals(self):
        forbidden = ("Bone_", "PROC_", "Tarbosaurus", "tarbosaurus", "a2cf73", "v8.2")
        for path in (ROOT / "src/eonwild_motion").rglob("*.py"):
            text = path.read_text()
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{marker} leaked into {path}")

    def test_dirty_profile_reference_fails_closed(self):
        original = sha256_file

        def drift(path):
            if path.name.endswith("semantic-rig.json"):
                return "0" * 64
            return original(path)

        with patch("eonwild_motion.contracts.resolve.sha256_file", side_effect=drift):
            with self.assertRaises(ContractError):
                resolve_profile(PROFILE)


if __name__ == "__main__":
    unittest.main()
