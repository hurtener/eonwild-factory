from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/diagnose_support_resultant.py"
ASSUMPTIONS = ROOT / "profiles/v9/tarbosaurus-pin-552-1-support-resultant-engineering.v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run([sys.executable, str(TOOL), *arguments], cwd=ROOT, env=environment, text=True, capture_output=True)


def test_cli_configuration_drives_90_10_double_support(tmp_path: Path):
    profile = json.loads(ASSUMPTIONS.read_text())
    profile["engineering_model"]["contact_load_alternatives"]["double_support"][1] = {"leading": 0.9, "trailing": 0.1}
    source = tmp_path / "assumptions.json"
    output = tmp_path / "configuration.json"
    source.write_text(json.dumps(profile))
    completed = run_cli("--assumptions", str(source), "--configuration-only", "--output", str(output))
    assert completed.returncode == 0, completed.stderr
    result = json.loads(output.read_text())
    assert result["loads"]["double_support"][1] == {"leading": 0.9, "trailing": 0.1}


def test_cli_configuration_drives_joint_origin_only(tmp_path: Path):
    profile = json.loads(ASSUMPTIONS.read_text())
    profile["engineering_model"]["local_com_alternatives"] = ["semantic_joint_origin"]
    source = tmp_path / "assumptions.json"
    output = tmp_path / "configuration.json"
    source.write_text(json.dumps(profile))
    completed = run_cli("--assumptions", str(source), "--configuration-only", "--output", str(output))
    assert completed.returncode == 0, completed.stderr
    result = json.loads(output.read_text())
    assert result["models"] == [{"id": "baseline_joint_origin", "local_com_variant": "semantic_joint_origin", "mass_variant": "baseline"}]


def test_cli_rejects_mutated_consumed_biomechanics_before_output(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    recipe = json.loads((ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v9.json").read_text())
    documents = {
        "recipe.json": recipe,
        "runtime.json": {},
        "plan.json": {},
        "biomechanics.json": {"geometry": {"uniform_scale": 1.0, "actual_semantic_pelvis_to_toe_plane_m": 2.0}},
    }
    for name, value in documents.items():
        (package / name).write_text(json.dumps(value))
    (package / "root_motion.glb").write_bytes(b"not reached")
    support = tmp_path / "support.json"
    support.write_text("{}")
    profile = json.loads(ASSUMPTIONS.read_text())
    profile["source"] = {
        "root_motion_glb_sha256": sha(package / "root_motion.glb"),
        "plan_sha256": sha(package / "plan.json"),
        "recipe_sha256": sha(package / "recipe.json"),
        "runtime_sha256": sha(package / "runtime.json"),
        "biomechanics_sha256": sha(package / "biomechanics.json"),
        "animal_profile_sha256": sha(ROOT / recipe["animal"]["path"]),
        "contact_profile_sha256": sha(ROOT / recipe["contact_profile"]["path"]),
        "provisional_segment_profile_sha256": sha(ROOT / profile["engineering_model"]["segment_profile"]),
        "support_geometry_audit_sha256": sha(support),
    }
    assumptions = tmp_path / "assumptions.json"
    assumptions.write_text(json.dumps(profile))
    documents["biomechanics.json"]["geometry"]["uniform_scale"] = 1.2
    (package / "biomechanics.json").write_text(json.dumps(documents["biomechanics.json"]))
    output = tmp_path / "result.json"
    completed = run_cli("--package", str(package), "--support-audit", str(support), "--assumptions", str(assumptions), "--output", str(output))
    assert completed.returncode != 0
    assert "source identity mismatch" in completed.stderr
    assert not output.exists()
