"""Focused invariants for the source-bound standing catalog migration helper."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from eonwild_motion.factory.io import digest, json_bytes
from eonwild_motion.factory.animal import load_animal_instance
from eonwild_motion.glb.container import Glb


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/regenerate_allosaurus_standing_catalog.py"
SPEC = importlib.util.spec_from_file_location("standing_catalog_tool", TOOL)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def document(path: Path) -> dict:
    return json.loads(path.read_text())


def test_current_allosaurus_measurement_and_catalog_binding_boundary():
    source_path = ROOT / "assets/sha256" / f"{MODULE.CURRENT_SOURCE_SHA256}.glb"
    source = Glb(source_path)
    roles = document(ROOT / MODULE.RIG)["roles"]
    measured = MODULE.geometry_measurements(source, roles)
    assert measured["material_floor_m"] == pytest.approx(-1.1810426247380787e-09, abs=1e-12)
    assert measured["skin_length_m"] == pytest.approx(4.958295123108622, abs=2e-12)
    assert measured["pelvis_to_skin_floor_m"] == pytest.approx(1.0727360373389463, abs=2e-12)
    for side in MODULE.SIDES:
        assert measured["sides"][side]["segment_lengths_m"] == pytest.approx(
            [0.42167160569123197, 0.371804734443526, 0.2060755040561382],
            abs=2e-12,
        )
        assert measured["sides"][side]["knee_degrees"] == pytest.approx(
            162.40674193203094, abs=2e-10
        )

    old_neutral = document(ROOT / MODULE.CURRENT_NEUTRAL)["neutral_jaw_calibration"]
    documents = MODULE.catalog_documents(
        ROOT,
        MODULE.CURRENT_SOURCE_SHA256,
        measured,
        old_neutral["measured_minimum_gap_m"],
        old_neutral["measured_body_height_m"],
    )
    baseline = documents[MODULE.NEW_BASELINE]
    motion_set = documents[MODULE.NEW_SET]
    assert baseline["source"]["sha256"] == MODULE.CURRENT_SOURCE_SHA256
    assert baseline["animal"]["sha256"] == digest(json_bytes(documents[MODULE.NEW_ANIMAL]))
    assert baseline["contact_profile"]["sha256"] == digest(json_bytes(documents[MODULE.NEW_CONTACT]))
    assert baseline["neutral_pose_profile"]["sha256"] == digest(json_bytes(documents[MODULE.NEW_NEUTRAL]))
    assert baseline["locomotion_response_policy"]["regimes"]["grounded"][
        "neutral_support_profile"
    ]["sha256"] == digest(json_bytes(documents[MODULE.NEW_SUPPORT]))
    runtime_animal = load_animal_instance(
        documents[MODULE.NEW_ANIMAL], source_sha256=MODULE.CURRENT_SOURCE_SHA256
    )
    for side in MODULE.SIDES:
        assert documents[MODULE.NEW_SUPPORT]["sides"][side]["upper_length_m"] == pytest.approx(
            measured["sides"][side]["segment_lengths_m"][0] * runtime_animal["uniform_scale"]
        )
        assert documents[MODULE.NEW_SUPPORT]["sides"][side]["lower_length_m"] == pytest.approx(
            measured["sides"][side]["segment_lengths_m"][1] * runtime_animal["uniform_scale"]
        )
    assert motion_set["baseline"]["sha256"] == digest(json_bytes(baseline))
    assert [entry["name"] for entry in motion_set["motions"]] == ["walk", "fast-walk"]


def test_identity_standing_delta_is_exactly_zero():
    source = Glb(ROOT / "assets/sha256" / f"{MODULE.CURRENT_SOURCE_SHA256}.glb")
    roles = document(ROOT / MODULE.RIG)["roles"]
    measured = MODULE.geometry_measurements(source, roles)
    delta = MODULE.standing_delta(measured, measured)
    assert delta["material_floor_delta_m"] == 0.0
    assert delta["maximum_segment_length_delta_m"] == 0.0
    assert delta["maximum_distal_translation_residual_m"] == 0.0
    assert delta["maximum_distal_rotation_residual_degrees"] == 0.0
    for side in MODULE.SIDES:
        assert delta["sides"][side]["knee_body_relative_to_hip_delta_m"] == [0.0, 0.0, 0.0]


def test_catalog_version_selectors_bind_wider_standing_inputs_and_next_catalog():
    selected = MODULE.build_catalog_paths(
        current_profile_version=5,
        current_motion_version=6,
        output_profile_version=6,
        output_motion_version=7,
        standing_config=Path(
            "catalog/standing-preparation/allosaurus-engineering-standing.v4.json"
        ),
        standing_contact=Path("catalog/contacts/allosaurus-engineering.v4.json"),
    )
    assert selected.current_animal.name.endswith(".adult.v5.json")
    assert selected.current_baseline.name.endswith("locomotion.v6.json")
    assert selected.new_animal.name.endswith(".adult.v6.json")
    assert selected.new_baseline.name.endswith("locomotion.v7.json")
    assert selected.standing_config.name.endswith("standing.v4.json")
    assert selected.standing_contact.name.endswith("engineering.v4.json")

    source = Glb(ROOT / "assets/sha256" / f"{MODULE.CURRENT_SOURCE_SHA256}.glb")
    roles = document(ROOT / MODULE.RIG)["roles"]
    measured = MODULE.geometry_measurements(source, roles)
    neutral = document(ROOT / selected.current_neutral)["neutral_jaw_calibration"]
    documents = MODULE.catalog_documents(
        ROOT,
        MODULE.CURRENT_SOURCE_SHA256,
        measured,
        neutral["measured_minimum_gap_m"],
        neutral["measured_body_height_m"],
        paths=selected,
    )
    assert documents[selected.new_animal]["id"].endswith(".adult.v6")
    assert documents[selected.new_contact]["version"] == 6
    assert documents[selected.new_baseline]["id"].endswith("locomotion.v7")
    assert documents[selected.new_set]["id"].endswith("motion-set.v7")
    assert documents[selected.new_set]["baseline"]["path"] == selected.new_baseline.as_posix()
