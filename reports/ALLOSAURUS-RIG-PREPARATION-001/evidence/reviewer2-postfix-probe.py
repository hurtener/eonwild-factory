#!/usr/bin/env python3
"""Narrow reviewer-2 closure probes for rig preparation 55cd2b6."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.rig_preparation import prepare_rig
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.whole_body_gait_transition import _encode


ARC = Path("/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521")
ROOT = ARC / "worktrees/eonwild-shared-motion-set-release-validation"
FIXTURE = ROOT / "assets/sha256/2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f.glb"
INCOMING = ARC / "incoming/allosaurus/91d9816b6bbaeb1037f3e9cbf253261799d8a4121efd91e0e2185f76908a6bf7.glb"
CANDIDATE = ARC / "out/allosaurus-rig-preparation-v2-candidate/geometry.glb"
CONFIG = ROOT / "catalog/rig-preparation/allosaurus-incoming.v1.json"
OUT = Path(__file__).resolve().parent
HEAD = "55cd2b64bcfd1e315277d025f78cecf6927274e1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fixture_config(source: Glb) -> dict:
    return {
        "schema": "eonwild.motion.rig-preparation.v1",
        "id": "reviewer2-fixture.v1",
        "source_sha256": digest(source.raw),
        "skin_index": 0,
        "coordinate": {"frame": "source_world", "lateral": [1, 0, 0],
                       "up": [0, 1, 0], "forward": [0, 0, 1]},
        "reparents": [{"node": "Bone_011", "new_parent": "Bone_003"}],
        "pivot_relocations": [{
            "node": "Bone_010", "world_origin_m": [-0.38, 1.4, 0.72],
            "basis": "measured_source_world",
        }],
        "articulations": [{
            "role": "jaw_lower", "node": "Bone_074", "parent": "Bone_035",
            "descendants": ["Bone_073"], "axis": [1.0, 0.0, 0.0],
            "axis_frame": "joint_parent_local",
        }],
        "weight_transfers": [],
        "evidence": [{"kind": "fixture", "reference": "reviewer2", "claim": "probe"}],
        "limitations": ["reviewer fixture only"],
    }


def second_skin(source: Glb) -> Glb:
    document = deepcopy(source.document)
    document["skins"].append(deepcopy(document["skins"][0]))
    return Glb.from_bytes(_encode(document, source.binary))


def rejection(call, match: str) -> dict:
    try:
        call()
    except ContractError as exc:
        message = str(exc)
        return {"rejected": True, "error": message, "matched": match in message}
    return {"rejected": False, "error": None, "matched": False}


def run() -> dict:
    fixture = Glb(FIXTURE)
    shifted_binary = bytearray(fixture.binary)
    ibm = fixture.document["skins"][0]["inverseBindMatrices"]
    offset, _, _ = fixture.accessor_region(ibm)
    at = offset + 12 * 4
    struct.pack_into("<f", shifted_binary, at,
                     struct.unpack_from("<f", shifted_binary, at)[0] + 0.01)
    shifted = Glb.from_bytes(_encode(deepcopy(fixture.document), bytes(shifted_binary)))

    duplicate = fixture_config(fixture)
    duplicate["articulations"].append({
        **deepcopy(duplicate["articulations"][0]),
        "role": "second_role",
        "axis": [-1.0, 0.0, 0.0],
    })

    incoming = Glb(INCOMING)
    config = json.loads(CONFIG.read_text())
    regenerated, receipt = prepare_rig(incoming, config)
    candidate = CANDIDATE.read_bytes()
    return {
        "schema": "eonwild.motion.rig-preparation-reviewer2-closure.v1",
        "reviewed_head": HEAD,
        "reviewed_tree": "f1307185e741060a198deb257f70273feb2a6a4d",
        "fixture_sha256": digest(fixture.raw),
        "closures": {
            "noncanonical_input": rejection(
                lambda: prepare_rig(shifted, fixture_config(shifted)),
                "not canonical POSITION"),
            "multiple_skins": rejection(
                lambda: prepare_rig(second_skin(fixture), fixture_config(second_skin(fixture))),
                "exactly one skin"),
            "duplicate_articulation_node": rejection(
                lambda: prepare_rig(fixture, duplicate),
                "roles and nodes"),
        },
        "production_candidate": {
            "input_sha256": digest(incoming.raw),
            "config_sha256": digest(CONFIG.read_bytes()),
            "candidate_sha256": digest(candidate),
            "regenerated_sha256": digest(regenerated),
            "byte_identical": regenerated == candidate,
            "receipt_output_sha256": receipt["output_source_sha256"],
            "input_neutral_skin_error_m": receipt["measurements"]["maximum_input_neutral_skin_error_m"],
            "output_neutral_skin_error_m": receipt["measurements"]["maximum_reopened_neutral_skin_error_m"],
            "output_world_matrix_error": receipt["measurements"]["maximum_reopened_world_matrix_error"],
            "weight_transfer": receipt["weight_transfers"][0],
        },
    }


if __name__ == "__main__":
    result = run()
    assert all(row["rejected"] and row["matched"] for row in result["closures"].values())
    assert result["production_candidate"]["byte_identical"]
    assert result["production_candidate"]["candidate_sha256"] == result["production_candidate"]["receipt_output_sha256"]
    output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    (OUT / "result.json").write_text(output)
    print(output, end="")
