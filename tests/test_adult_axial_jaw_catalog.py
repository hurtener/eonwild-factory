"""Bindings for the combined adult axial-clock and neutral-jaw candidate."""
from __future__ import annotations

import json
from pathlib import Path

from eonwild_motion.factory.io import digest
from eonwild_motion.solve.performance import load_performance


ROOT = Path(__file__).resolve().parents[1]
V8_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v8.json"
V9_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v9.json"
JAW = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v7.json"
COMBINED = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v8.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_combined_performance_adds_only_the_closed_axial_clock_to_jaw_v7():
    before, after = load(JAW), load(COMBINED)
    assert after["classification"] == before["classification"]
    assert after["reference"] == before["reference"]
    assert set(after["parameters"]) - set(before["parameters"]) == {
        "support_timed_axial_carrier"}
    assert after["parameters"]["support_timed_axial_carrier"] is True
    assert {key: value for key, value in after["parameters"].items()
            if key != "support_timed_axial_carrier"} == before["parameters"]
    loaded = load_performance(after)
    assert loaded.support_timed_axial_carrier is True
    assert loaded.neutral_jaw_calibration is not None


def test_v9_recipe_changes_only_versioned_metadata_and_performance_binding():
    before, after = load(V8_RECIPE), load(V9_RECIPE)
    assert after["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v9"
    assert after["version"] == 9
    assert after["supersedes"] == before["id"]
    for key in set(before) - {"id", "version", "supersedes", "description",
                              "performance_profile"}:
        assert after[key] == before[key]
    assert after["performance_profile"]["path"] == (
        "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v8.json")


def test_v9_hash_binds_every_declared_input():
    recipe = load(V9_RECIPE)
    for key in ("source", "rig", "animal", "program_profile", "contact_profile",
                "performance_profile", "articulation_profile"):
        reference = recipe[key]
        assert digest((ROOT / reference["path"]).read_bytes()) == reference["sha256"]


def test_ci_and_animal_benchmark_select_both_bind_and_combined_candidates():
    workflow = (ROOT / ".github/workflows/factory-baseline.yml").read_text()
    verifier = (ROOT / "tools/verify_catalog.py").read_text()
    for name in (
        "tarbosaurus-pin-552-1-adult-walk.v8",
        "tarbosaurus-pin-552-1-adult-walk.v9",
    ):
        assert workflow.count(name) == 3
        assert f"'{name}'" in verifier
