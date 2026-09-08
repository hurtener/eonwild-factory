#!/usr/bin/env python3
"""Retain exact-input, every-native-row constant-target diagnostics."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

from eonwild_motion.factory.animal import (
    apply_uniform_geometry_scale,
    load_animal_instance,
    scaled_contact_profile,
    verify_source_calibration,
)
from eonwild_motion.factory.compiler import load_recipe, validate_plan
from eonwild_motion.factory.io import frame_axes
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.articulation_profile import load_articulation_profile
from eonwild_motion.planning.grounded_gait import (
    build_grounded_plan,
    load_grounded_gait,
)
from eonwild_motion.solve.constant_skin_targets import (
    CanonicalConstantSkinTargetLaw,
    ConstantSkinTargetUnavailable,
)
from eonwild_motion.solve.gaze import calibrate_rostral_direction
from eonwild_motion.solve.performance import decorate_plan, load_performance
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
from eonwild_motion.solve.support_anchors import CanonicalSupportAnchorProvider


INPUT_ROOT = Path("/Volumes/m2-extended-disk/Repos/eonwild-factory")
CODE_ROOT = Path(
    "/Volumes/m2-extended-disk/Repos/eonwild-task-storage/"
    "01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/"
    "eonwild-canonical-constant-skin-target-law"
)
OUTPUT_ROOT = Path(
    "/Volumes/m2-extended-disk/Repos/eonwild-task-storage/"
    "01a07d0e-00b8-7a51-9095-c2da82025521/out/"
    "constant-skin-law-exact-cycles"
)
EXPECTED = {
    "walk.v3.json": {
        "recipe": "0e9c04f6e38d5d523cd354577ed82650846cf4edae3d1cddfacf76906530c783",
        "performance": "ade6d37243d4b9597c9d2c15a86a667b5528654aca3998315abe7f2f06a968be",
    },
    "tarbosaurus-pin-552-1-adult-walk.v9.json": {
        "recipe": "f55da91847dc63489f9655cfc3641bee665bf8ce6122755a61748d98fabf3ccd",
        "performance": "e133819dddf19bd224ddec7419687208e01abf8f3906fa147837813710dc2dfc",
    },
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def git(*args: str, root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def file_identity(path: Path, declared: str | None = None) -> dict[str, Any]:
    raw = path.read_bytes()
    actual = sha256(raw)
    if declared is not None and actual != declared:
        raise RuntimeError(f"hash mismatch for {path}: {actual} != {declared}")
    return {"path": str(path), "sha256": actual, "bytes": len(raw)}


def pose_sha256(value: Any) -> str:
    return sha256(
        np.asarray(value.translations, dtype="<f8").tobytes()
        + np.asarray(value.rotations, dtype="<f8").tobytes()
    )


def run_recipe(recipe_name: str) -> dict[str, Any]:
    recipe_path = INPUT_ROOT / "recipes/heavy-biped" / recipe_name
    recipe_identity = file_identity(recipe_path, EXPECTED[recipe_name]["recipe"])
    recipe, paths = load_recipe(recipe_path, INPUT_ROOT)
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    inputs = {
        name: file_identity(path, recipe[name]["sha256"])
        for name, path in paths.items()
    }
    if inputs["performance_profile"]["sha256"] != EXPECTED[recipe_name]["performance"]:
        raise RuntimeError(f"unexpected performance profile for {recipe_name}")

    source = Glb.from_bytes(snapshots["source"])
    roles = json.loads(snapshots["rig"])["roles"]
    contact = json.loads(snapshots["contact_profile"])
    forward, up = frame_axes(recipe["forward_axis"], recipe["up_axis"])
    animal = None
    if "animal" in snapshots:
        animal = load_animal_instance(
            json.loads(snapshots["animal"]),
            source_sha256=recipe["source"]["sha256"],
        )
        verify_source_calibration(animal, source, roles, contact, forward, up)
        apply_uniform_geometry_scale(source, animal["uniform_scale"])
        contact = scaled_contact_profile(contact, animal["uniform_scale"])

    gait = load_grounded_gait(json.loads(snapshots["program_profile"]))
    solver = AirborneGait(
        step_period_s=gait.step_period_s,
        cycles=gait.cycles,
        sample_hz=gait.sample_hz,
        swing_hip_lift_degrees=gait.swing_hip_lift_degrees,
    )
    articulation = (
        load_articulation_profile(json.loads(snapshots["articulation_profile"]))
        if "articulation_profile" in snapshots
        else None
    )
    height = geometry_height(source, roles, up)
    authored_performance = load_performance(
        json.loads(snapshots["performance_profile"])
    )
    effective_performance = replace(
        authored_performance, canonical_support_anchors=True
    )
    plan = decorate_plan(
        build_grounded_plan(gait, height), effective_performance
    )
    plan["gaze_calibration"] = calibrate_rostral_direction(
        source,
        roles=roles,
        contact_profile=contact,
        forward_axis=forward,
        up_axis=up,
    )
    validate_plan(plan, recipe["program"])

    provider = CanonicalSupportAnchorProvider.build(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=gait,
        transition=None,
        plan=plan,
        contact_profile=contact,
        up_axis=tuple(up),
        forward_axis=tuple(forward),
        articulation_profile=articulation,
    )
    query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=gait,
        transition=None,
        plan=plan,
        up_axis=tuple(up),
        forward_axis=tuple(forward),
        source_clip=None,
        legacy_overlay=False,
        articulation_profile=articulation,
        contact_profile=contact,
    )
    law = CanonicalConstantSkinTargetLaw.build(
        query,
        provider,
        source=source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=gait,
        transition=None,
        plan=plan,
        contact_profile=contact,
        up_axis=tuple(up),
        forward_axis=tuple(forward),
        articulation_profile=articulation,
    )

    rows = []
    for index, source_row in enumerate(plan["samples"]):
        time_s = float(source_row["time_s"])
        value = law.value(time_s)
        retained = {
            "index": index,
            "time_s": time_s,
            "status": value.status,
            "source_row_sha256": sha256(canonical(jsonable(source_row))),
            "source_contacts": {
                side: bool(source_row["feet"][side]["contact"])
                for side in ("left", "right")
            },
            "observations": jsonable(value.observations),
            "branch_witness": jsonable(value.branch_witness),
        }
        if isinstance(value, ConstantSkinTargetUnavailable):
            retained["reason"] = value.reason
        else:
            retained.update(
                {
                    "checked_row_sha256": sha256(
                        canonical(jsonable(value.row))
                    ),
                    "pose_sha256": pose_sha256(value.pose),
                    "pose_checks": {
                        "maximum_foot_target_residual_m": float(
                            value.pose.maximum_foot_target_residual_m
                        ),
                        "maximum_unreachable_extension_m": float(
                            value.pose.maximum_unreachable_extension_m
                        ),
                        "maximum_articulation_envelope_violation_degrees": float(
                            value.pose.maximum_articulation_envelope_violation_degrees
                        ),
                    },
                    "corrections_m": {
                        side: value.corrections_m[side].tolist()
                        for side in ("left", "right")
                    },
                }
            )
        rows.append(retained)
        print(f"{recipe_name} {index + 1}/{len(plan['samples'])} {value.status}", flush=True)

    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in sorted({row["status"] for row in rows})
    }
    document_state = sha256(canonical(source.document))
    result = {
        "schema": "eonwild.motion.constant-skin-law.exact-cycle.v1",
        "classification": "non-emitting pointwise diagnostic; no derivative, branch-stability, global-C1, visual, Unity, or production authority",
        "recipe": recipe_identity,
        "recipe_id": recipe["id"],
        "input_repository": {
            "path": str(INPUT_ROOT),
            "head": git("rev-parse", "HEAD", root=INPUT_ROOT),
        },
        "inputs": inputs,
        "admitted_source": {
            "raw_sha256": sha256(source.raw),
            "current_document_sha256": document_state,
            "binary_sha256": sha256(source.binary),
            "uniform_scale": 1.0 if animal is None else animal["uniform_scale"],
            "body_height_m": height,
        },
        "authored_performance": asdict(authored_performance),
        "effective_performance": asdict(effective_performance),
        "only_diagnostic_override": {"canonical_support_anchors": True},
        "effective_plan_sha256": sha256(canonical(jsonable(plan))),
        "gaze_calibration": jsonable(plan["gaze_calibration"]),
        "gaze_calibration_sha256": sha256(
            canonical(jsonable(plan["gaze_calibration"]))
        ),
        "articulation_profile": (
            None if articulation is None else articulation.receipt()
        ),
        "scaled_contact_profile_sha256": sha256(canonical(contact)),
        "provider": provider.receipt(),
        "calibration_sha256": law._calibration_sha256,
        "query_binding_sha256": law._query_binding_sha256,
        "calibration_query_binding_sha256": law._calibration_query_binding_sha256,
        "native_row_count": len(rows),
        "status_counts": counts,
        "rows": rows,
    }
    return result


def main() -> None:
    if git("status", "--porcelain", root=CODE_ROOT):
        raise RuntimeError("code worktree must be clean before evidence execution")
    code_head = git("rev-parse", "HEAD", root=CODE_ROOT)
    driver = Path(__file__).resolve()
    common = {
        "code": {
            "path": str(CODE_ROOT),
            "head": code_head,
            "files": {
                str(path.relative_to(CODE_ROOT)): file_identity(path)
                for path in (
                    CODE_ROOT
                    / "src/eonwild_motion/solve/constant_skin_targets.py",
                    CODE_ROOT / "src/eonwild_motion/solve/source_motion_query.py",
                    CODE_ROOT / "src/eonwild_motion/solve/support_anchors.py",
                    CODE_ROOT / "src/eonwild_motion/solve/airborne_gait.py",
                )
            },
        },
        "driver": file_identity(driver),
        "python": sys.version,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifests = []
    for recipe_name in EXPECTED:
        result = {**common, **run_recipe(recipe_name)}
        output = OUTPUT_ROOT / recipe_name.replace(".json", "-exact-cycle.json")
        output.write_bytes(canonical(result) + b"\n")
        manifests.append(file_identity(output))
    manifest = {
        "schema": "eonwild.motion.constant-skin-law.exact-cycle-set.v1",
        "code_head": code_head,
        "driver": file_identity(driver),
        "outputs": manifests,
    }
    path = OUTPUT_ROOT / "manifest.json"
    path.write_bytes(canonical(manifest) + b"\n")
    print(json.dumps({"manifest": file_identity(path), **manifest}, indent=2))


if __name__ == "__main__":
    main()
