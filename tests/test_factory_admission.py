"""Public admission and archival integrity regressions."""
from pathlib import Path
import hashlib
import json

from eonwild_motion.factory.__main__ import main
from eonwild_motion.glb.container import Glb
from test_v9_airborne_gait import fixture


def test_public_admission_is_portable_and_immutable(tmp_path):
    source, roles = fixture()
    glb, rig = tmp_path / "source.glb", tmp_path / "rig.json"
    glb.write_bytes(source.raw)
    rig.write_text(json.dumps({"roles": roles}))
    out = tmp_path / "admitted"
    argv = ["admit", "--source", str(glb), "--rig", str(rig), "--forward", "0", "0", "1", "--output", str(out)]
    assert main(argv) == 0
    neutral = Glb(out / "geometry.glb")
    assert not neutral.document.get("animations")
    receipt = json.loads((out / "admission.json").read_text())
    assert receipt["files"]["geometry.glb"] == hashlib.sha256((out / "geometry.glb").read_bytes()).hexdigest()
    assert main(argv) == 1


def test_public_admission_rejects_unknown_forward(tmp_path):
    source, roles = fixture()
    (tmp_path / "source.glb").write_bytes(source.raw)
    (tmp_path / "rig.json").write_text(json.dumps({"roles": roles}))
    assert main(["admit", "--source", str(tmp_path / "source.glb"), "--rig", str(tmp_path / "rig.json"), "--output", str(tmp_path / "bad")]) == 1
    assert not (tmp_path / "bad").exists()


def test_retired_capsule_preserves_its_original_inventory():
    root = Path(__file__).resolve().parents[1]
    capsule = root / "legacy/capsules/v8.2"
    manifest = json.loads((capsule / "RELEASE_MANIFEST.json").read_text())
    for name, entry in manifest["inventory"].items():
        assert hashlib.sha256((capsule / name).read_bytes()).hexdigest() == entry["sha256"], name
    assert not (root / "procedural-animation-toolkit(v8)").exists()
    assert not (root / "procedural-animation-toolkit(v8.1)").exists()
    assert not (root / "procedural-animation-toolkit(v8.2)").exists()
