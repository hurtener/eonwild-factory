"""Bindings for the bounded adult recovered-bind diagnostic."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eonwild_motion.factory.animal import load_animal_instance, verify_source_calibration
from eonwild_motion.factory.io import digest
from eonwild_motion.glb.container import Glb


ROOT = Path(__file__).resolve().parents[1]
V7_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v7.json"
V8_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v8.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_v8_changes_only_bind_geometry_and_its_bound_calibration():
    before, after = load(V7_RECIPE), load(V8_RECIPE)
    assert after["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v8"
    assert after["version"] == 8
    assert after["supersedes"] == before["id"]
    for key in ("rig", "program_profile", "performance_profile",
                "articulation_profile", "program", "family", "up_axis"):
        assert after[key] == before[key]
    assert after["forward_axis"] == [0.0, 0.0, 1.0]
    assert {"source", "animal", "contact_profile"} == {
        key for key in ("source", "animal", "contact_profile")
        if after[key] != before[key]
    }


def test_v8_hash_binds_every_declared_input():
    recipe = load(V8_RECIPE)
    for key in ("source", "rig", "animal", "program_profile", "contact_profile",
                "performance_profile", "articulation_profile"):
        reference = recipe[key]
        assert digest((ROOT / reference["path"]).read_bytes()) == reference["sha256"]


def test_v8_recovered_source_and_contact_share_explicit_frame_and_floor():
    recipe = load(V8_RECIPE)
    source = Glb.from_bytes((ROOT / recipe["source"]["path"]).read_bytes())
    geometry = source.document["extras"]["eonwildGeometry"]
    contact = load(ROOT / recipe["contact_profile"]["path"])
    assert source.document.get("animations", []) == []
    assert geometry["forward_axis"] == recipe["forward_axis"] == [0.0, 0.0, 1.0]
    assert geometry["up_axis"] == recipe["up_axis"] == [0.0, 1.0, 0.0]
    assert contact["coordinate_system"]["forward_axis"] == "+Z"
    assert {key: contact["source"][key] for key in ("path", "sha256")} == recipe["source"]
    assert np.isclose(contact["geometry"]["ground"]["level_m"], 8.663434924195463e-08,
                      rtol=0, atol=1e-15)


def test_v8_animal_measurements_reopen_from_bound_source():
    recipe = load(V8_RECIPE)
    source = Glb.from_bytes((ROOT / recipe["source"]["path"]).read_bytes())
    roles = load(ROOT / recipe["rig"]["path"])["roles"]
    contact = load(ROOT / recipe["contact_profile"]["path"])
    animal = load_animal_instance(load(ROOT / recipe["animal"]["path"]),
                                  source_sha256=recipe["source"]["sha256"])
    measured = verify_source_calibration(
        animal, source, roles, contact,
        np.asarray(recipe["forward_axis"]), np.asarray(recipe["up_axis"]),
    )
    assert measured == animal["source_measurements_m"]
    assert any("not been validated as corresponding" in row
               for row in animal["document"]["limitations"])
