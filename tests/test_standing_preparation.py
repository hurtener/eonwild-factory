from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.standing_preparation import prepare_standing_pose
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.whole_body_gait_transition import _encode
from eonwild_motion.solve.skin_rig import SkinRig


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "assets/sha256/f1ac3ddebc2b8471af1a55439d0631ed0d350a750e59edaa661a9cd76ced4684.glb"
)
RIG = ROOT / "catalog/rigs/allosaurus-engineering.v2.json"
CONTACT = ROOT / "catalog/contacts/allosaurus-engineering.v4.json"
CONFIG = ROOT / "catalog/standing-preparation/allosaurus-engineering-standing.v1.json"
WIDE_CONFIG = (
    ROOT / "catalog/standing-preparation/allosaurus-engineering-standing.v3.json"
)


def inputs():
    source = Glb(SOURCE)
    roles = json.loads(RIG.read_text())["roles"]
    contact = json.loads(CONTACT.read_text())
    config = json.loads(CONFIG.read_text())
    return source, roles, contact, config


def test_actual_allosaurus_standing_is_deterministic_bound_and_bilateral():
    source, roles, contact, config = inputs()
    first, receipt = prepare_standing_pose(
        source, semantic_roles=roles, contact_profile=contact, config=config
    )
    second, second_receipt = prepare_standing_pose(
        Glb(SOURCE),
        semantic_roles=deepcopy(roles),
        contact_profile=deepcopy(contact),
        config=deepcopy(config),
    )
    assert first == second
    assert receipt == second_receipt
    result = Glb.from_bytes(first)
    assert result.binary == source.binary
    assert (
        result.document["skins"][0]["inverseBindMatrices"]
        == (source.document["skins"][0]["inverseBindMatrices"])
    )
    assert not result.document.get("animations")
    assert receipt["output_source_sha256"] == hashlib.sha256(first).hexdigest()
    for side in ("left", "right"):
        assert receipt["angles_degrees"]["after"][side][
            "hip_sagittal_degrees"
        ] == pytest.approx(30.0, abs=3e-5)
        assert receipt["angles_degrees"]["after"][side][
            "knee_interior_degrees"
        ] == pytest.approx(125.0, abs=5e-5)
        assert receipt["angles_degrees"]["after"][side][
            "metatarsus_sagittal_degrees"
        ] == pytest.approx(
            receipt["realized_metatarsus_sagittal_degrees"][side], abs=2e-5
        )
        assert (
            abs(
                receipt["bilateral_material_minimum_m"][side]
                - receipt["material_ground_m"]
            )
            < 5e-5
        )
    changed_contact = deepcopy(contact)
    changed_contact["source"]["path"] = "derived-standing-source.glb"
    changed_contact["source"]["sha256"] = receipt["output_source_sha256"]
    skin = SkinRig(result, roles, (0, 0, 1), (0, 1, 0), changed_contact)
    points = skin.skin(skin.neutral_world)
    assert all(
        abs(float(points[indices, 1].min()) - skin.ground) < 5e-5
        for indices in skin.foot_masks.values()
    )
    assert receipt["maximum_retained_pad_toe_orientation_matrix_difference"] < 3e-6
    assert receipt["pelvis_height_change_m"] < 0
    assert receipt["stance_widths_m"]["after"] == pytest.approx(
        receipt["stance_widths_m"]["before"], abs=2e-6
    )


def test_actual_allosaurus_standing_width_is_rotational_and_ordered():
    source, roles, contact, _ = inputs()
    config = json.loads(WIDE_CONFIG.read_text())
    raw, receipt = prepare_standing_pose(
        source, semantic_roles=roles, contact_profile=contact, config=config
    )
    assert raw
    policy = receipt["stance_width_policy"]
    assert policy["model"] == "length_weighted_semantic_lateral_rotation.v1"
    assert policy["translations_or_stretch_applied"] is False
    assert policy["target_over_hindlimb"] == pytest.approx(0.376)
    assert receipt["stance_widths_m"]["after"]["mtp"] == pytest.approx(
        policy["target_mtp_width_m"], abs=2e-6
    )
    assert (
        receipt["stance_widths_m"]["after"]["mtp"]
        > (receipt["stance_widths_m"]["before"]["mtp"])
    )
    assert receipt["segment_length_validation"]["maximum_difference_m"] < 2e-6
    order = policy["lateral_order_sign"]
    for joint in ("hip", "knee", "ankle", "mtp"):
        coordinates = receipt["lateral_joint_coordinates_m"]["after"]
        assert (coordinates["right"][joint] - coordinates["left"][joint]) * order > 0


@pytest.mark.parametrize(
    "case",
    [
        "hash",
        "topology",
        "angle",
        "unknown",
        "nonuniform_scale",
        "reflected_scale",
        "zero_segment",
        "width",
    ],
)
def test_standing_rejects_unbound_or_incompatible_inputs(case):
    source, roles, contact, config = inputs()
    if case == "hash":
        config["source_sha256"] = "0" * 64
    elif case == "topology":
        roles["legs"]["left"]["contactChain"][1:3] = reversed(
            roles["legs"]["left"]["contactChain"][1:3]
        )
    elif case == "angle":
        config["knee_interior_degrees"] = 180.0
    elif case == "width":
        config["stance_width_over_hindlimb"] = 1.01
    elif case in {"nonuniform_scale", "reflected_scale", "zero_segment"}:
        document = deepcopy(source.document)
        root = source.name_to_node[roles["root"]]
        if case == "nonuniform_scale":
            document["nodes"][root]["scale"] = [1.1, 1.0, 0.9]
        elif case == "reflected_scale":
            document["nodes"][root]["scale"] = [-1.0, 1.0, 1.0]
        else:
            knee = source.name_to_node[roles["legs"]["left"]["contactChain"][1]]
            document["nodes"][knee]["translation"] = [0.0, 0.0, 0.0]
        source = Glb.from_bytes(_encode(document, source.binary))
        config["source_sha256"] = hashlib.sha256(source.raw).hexdigest()
        contact["source"]["sha256"] = config["source_sha256"]
    else:
        config["per_clip_offset"] = 1
    with pytest.raises(ContractError):
        prepare_standing_pose(
            source, semantic_roles=roles, contact_profile=contact, config=config
        )


def test_standing_pose_uses_semantic_names_not_literal_bone_constants():
    source, roles, contact, config = inputs()
    config = json.loads(WIDE_CONFIG.read_text())
    original_raw, _ = prepare_standing_pose(
        source,
        semantic_roles=deepcopy(roles),
        contact_profile=deepcopy(contact),
        config=deepcopy(config),
    )
    document = deepcopy(source.document)
    renamed = {}
    for side in ("left", "right"):
        for index, name in enumerate(roles["legs"][side]["contactChain"]):
            new = f"{side}_joint_{index}"
            document["nodes"][source.name_to_node[name]]["name"] = new
            renamed[name] = new
            roles["legs"][side]["contactChain"][index] = new
    for side in ("left", "right"):
        mask = contact["geometry"]["feet"][side]
        mask["sole_joints"] = [renamed.get(name, name) for name in mask["sole_joints"]]
    changed = Glb.from_bytes(_encode(document, source.binary))
    config["source_sha256"] = hashlib.sha256(changed.raw).hexdigest()
    contact["source"]["sha256"] = config["source_sha256"]
    contact["source"]["path"] = "renamed.glb"
    raw, receipt = prepare_standing_pose(
        changed, semantic_roles=roles, contact_profile=contact, config=config
    )
    assert raw
    assert receipt["angles_degrees"]["after"]["left"][
        "knee_interior_degrees"
    ] == pytest.approx(129.0, abs=5e-5)
    original = Glb.from_bytes(original_raw)
    result = Glb.from_bytes(raw)
    original_contact = deepcopy(json.loads(CONTACT.read_text()))
    original_contact["source"] = {
        **original_contact["source"],
        "path": "original-standing.glb",
        "sha256": hashlib.sha256(original_raw).hexdigest(),
    }
    renamed_contact = deepcopy(contact)
    renamed_contact["source"] = {
        **renamed_contact["source"],
        "path": "renamed-standing.glb",
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    original_skin = SkinRig(
        original,
        json.loads(RIG.read_text())["roles"],
        (0, 0, 1),
        (0, 1, 0),
        original_contact,
    )
    renamed_skin = SkinRig(result, roles, (0, 0, 1), (0, 1, 0), renamed_contact)
    assert renamed_skin.skin(renamed_skin.neutral_world) == pytest.approx(
        original_skin.skin(original_skin.neutral_world), abs=3e-6
    )


def test_standing_pose_respects_rotated_scaled_source_world_frame():
    source, roles, contact, config = inputs()
    config = json.loads(WIDE_CONFIG.read_text())
    document = deepcopy(source.document)
    root = source.name_to_node[roles["root"]]
    node = document["nodes"][root]
    node["rotation"] = [0.0, 1.0, 0.0, 0.0]
    node["scale"] = [value * 1.1 for value in source.rest_scale[root]]
    node["translation"] = [0.3, 0.4, -0.2]
    changed = Glb.from_bytes(_encode(document, source.binary))
    changed_sha = hashlib.sha256(changed.raw).hexdigest()
    config["source_sha256"] = changed_sha
    config["coordinate"]["lateral"] = [-1.0, 0.0, 0.0]
    config["coordinate"]["forward"] = [0.0, 0.0, -1.0]
    contact["source"] = {
        **contact["source"],
        "path": "rotated-scaled.glb",
        "sha256": changed_sha,
    }
    raw, receipt = prepare_standing_pose(
        changed, semantic_roles=roles, contact_profile=contact, config=config
    )
    assert raw
    for side in ("left", "right"):
        assert receipt["angles_degrees"]["after"][side][
            "hip_sagittal_degrees"
        ] == pytest.approx(30.0, abs=3e-5)
        assert receipt["angles_degrees"]["after"][side][
            "knee_interior_degrees"
        ] == pytest.approx(129.0, abs=5e-5)
        assert receipt["angles_degrees"]["after"][side][
            "metatarsus_sagittal_degrees"
        ] == pytest.approx(
            receipt["realized_metatarsus_sagittal_degrees"][side], abs=2e-5
        )
    assert receipt["stance_widths_m"]["after"]["mtp"] == pytest.approx(
        receipt["stance_width_policy"]["target_mtp_width_m"], abs=2e-6
    )
    assert receipt["segment_length_validation"]["maximum_difference_m"] < 2e-6
