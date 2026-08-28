from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from eonwild_motion.contracts.resolve import resolve_profile
from eonwild_motion.errors import ValidationFailure
from eonwild_motion.glb.container import Glb
from eonwild_motion.pipeline.validate import (
    validate_animation_contract,
    validate_source_package,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles/v8.2/profile.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mismatched_timeline(source: Path, target: Path, clip_name: str) -> None:
    raw = source.read_bytes()
    cursor = 12
    chunks = []
    document = None
    while cursor < len(raw):
        length, kind = struct.unpack_from("<II", raw, cursor)
        cursor += 8
        payload = raw[cursor:cursor + length]
        cursor += length
        if kind == 0x4E4F534A:
            document = json.loads(payload.decode("utf-8"))
        chunks.append((kind, payload))
    animation = next(
        item for item in document["animations"] if item.get("name") == clip_name
    )
    channels = [
        channel
        for channel in animation["channels"]
        if channel["target"]["path"] == "rotation"
    ]
    sampler = animation["samplers"][channels[1]["sampler"]]
    shifted = copy.deepcopy(document["accessors"][int(sampler["input"])])
    shifted["byteOffset"] = int(shifted.get("byteOffset", 0)) + 4
    shifted["count"] = int(shifted["count"]) - 1
    document["accessors"].append(shifted)
    sampler["input"] = len(document["accessors"]) - 1
    rebuilt = []
    for kind, payload in chunks:
        if kind == 0x4E4F534A:
            payload = json.dumps(document, separators=(",", ":")).encode()
            payload += b" " * ((-len(payload)) % 4)
        rebuilt.append(struct.pack("<II", len(payload), kind) + payload)
    body = b"".join(rebuilt)
    target.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)


class ContractNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolved = resolve_profile(PROFILE)
        cls.glb = Glb(cls.resolved.approved_output_path)

    def assert_rig_failure(self, mutate):
        rig = copy.deepcopy(self.resolved.rig)
        mutate(rig)
        with self.assertRaises(ValidationFailure):
            validate_animation_contract(self.glb, rig, self.resolved.motion)

    def test_bad_expected_parent(self):
        self.assert_rig_failure(
            lambda rig: rig["expectedParents"].__setitem__("pelvis", "chest")
        )

    def test_step_interpolation(self):
        self.assert_rig_failure(
            lambda rig: rig["accessorContract"].__setitem__("interpolation", "STEP")
        )

    def test_cubic_spline_interpolation(self):
        self.assert_rig_failure(
            lambda rig: rig["accessorContract"].__setitem__(
                "interpolation", "CUBICSPLINE"
            )
        )

    def test_common_timeline_false(self):
        self.assert_rig_failure(
            lambda rig: rig["accessorContract"].__setitem__(
                "commonTimeline", False
            )
        )

    def test_bad_component_type(self):
        self.assert_rig_failure(
            lambda rig: rig["accessorContract"].__setitem__("componentType", 5123)
        )

    def test_bad_value_type(self):
        self.assert_rig_failure(
            lambda rig: rig["accessorContract"].__setitem__("type", "VEC3")
        )

    def test_bad_stride(self):
        self.assert_rig_failure(
            lambda rig: rig["accessorContract"].__setitem__("byteStride", 12)
        )

    def test_mismatched_common_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mismatch.glb"
            mismatched_timeline(
                self.resolved.input_path,
                path,
                self.resolved.motion["clips"][0]["name"],
            )
            with self.assertRaises(ValidationFailure):
                validate_animation_contract(
                    Glb(path), self.resolved.rig, self.resolved.motion
                )

    def _package_with_extra(self, *, large: bool) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / "good.txt"
            regular.write_text("good")
            manifest = {
                "selfHashConvention": "manifest excluded",
                "inventory": {
                    "good.txt": {"sha256": sha(regular)}
                },
            }
            manifest_path = root / "RELEASE_MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest))
            cache = root / "scripts/__pycache__"
            cache.mkdir(parents=True)
            bad = cache / ("oversized.pyc" if large else "small.pyc")
            if large:
                with bad.open("wb") as handle:
                    handle.truncate(100 * 1024 * 1024 + 1)
            else:
                bad.write_bytes(b"cache")
            with self.assertRaises(ValidationFailure):
                validate_source_package(root, manifest_path)

    def test_small_pycache(self):
        self._package_with_extra(large=False)

    def test_oversized_pyc(self):
        self._package_with_extra(large=True)

    def test_zero_bounds_fails_blender_stage(self):
        resolved = self.resolved.runtime_document()
        resolved["layers"] = copy.deepcopy(resolved["layers"])
        resolved["layers"][0]["bounds"]["chestLocalDeltaDegrees"] = 0
        resolved["layers"][0]["bounds"]["neckLocalDeltaDegrees"] = 0
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "resolved": resolved,
                        "outputPath": str(root / "candidate.glb"),
                        "stageReportPath": str(root / "stage.json"),
                    }
                )
            )
            process = subprocess.run(
                [
                    "blender",
                    "--background",
                    "--python-exit-code",
                    "1",
                    "--python",
                    str(ROOT / "src/eonwild_motion/blender/entrypoint.py"),
                    "--",
                    "build",
                    "--request",
                    str(request),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("local delta bound exceeded", process.stderr)


if __name__ == "__main__":
    unittest.main()
