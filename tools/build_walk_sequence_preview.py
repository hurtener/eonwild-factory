#!/usr/bin/env python3
"""Emit a source-driven connected walking diagnostic for visual review."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np


class QueryCaptured(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plain(value):
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if hasattr(value, "items"):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--motion-set", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mass-receipt", type=Path, required=True)
    args = parser.parse_args()
    repo, target = args.repo.resolve(), args.output.resolve()
    if target.exists():
        raise RuntimeError(f"refusing to overwrite {target}")
    sys.path.insert(0, str(repo / "src"))

    from eonwild_motion.factory.compiler import compile_motion_set
    from eonwild_motion.glb.animation import read_animation_tracks
    from eonwild_motion.glb.container import Glb
    from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
    from eonwild_motion.solve.source_motion_query import SourceMotionResult
    from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _encode

    captured = {}

    def intercept(cls, query, provider, **kwargs):
        captured.update(query=query, provider=provider, kwargs=kwargs, law=original(query, provider, **kwargs))
        raise QueryCaptured("captured after rolling material contact build")

    original = CanonicalConstantSkinTargetLaw.build
    CanonicalConstantSkinTargetLaw.build = classmethod(intercept)
    try:
        try:
            compile_motion_set(
                args.motion_set.resolve(), "walk", root=repo,
                output=target.parent / (target.name + ".never-published"),
            )
        except QueryCaptured:
            pass
    finally:
        CanonicalConstantSkinTargetLaw.build = original
    if set(captured) != {"query", "provider", "kwargs", "law"}:
        raise RuntimeError("compiler did not reach SourceMotionQuery interception")

    mass_receipt = json.loads(args.mass_receipt.read_text())
    coefficients = tuple(mass_receipt["solution"]["coefficients"])
    if not any(abs(c) > 1e-12 for c in coefficients):
        raise RuntimeError("mass solution is zero; cannot label it a mass-corrected preview")
    from eonwild_motion.solve.body_support_control import BodySupportControl
    neutral_query = captured["query"]
    control = BodySupportControl.build(coefficients,
        same_foot_cycle_s=float(neutral_query._plan["same_foot_cycle_s"]),
        body_height_m=neutral_query.context.body_height,
        up_axis=neutral_query.context.up, forward_axis=neutral_query.context.forward)
    controlled_query = neutral_query.with_body_support_control(control)
    captured["law"] = captured["law"].with_query(controlled_query)
    current_anchor = captured["law"].frozen_anchor_binding_sha256()
    if mass_receipt["frozen_anchor_sha256"] is None:
        if mass_receipt["status"] != "OPTIMIZATION_IN_PROGRESS":
            raise RuntimeError("completed mass receipt lacks its frozen anchor")
        mass_receipt["frozen_anchor_sha256"] = current_anchor
        mass_receipt["preview_binding"] = "current admitted source and frozen contact plan; intermediate coefficients from running optimizer"
    elif current_anchor != mass_receipt["frozen_anchor_sha256"]:
        raise RuntimeError("mass correction belongs to another contact choreography")
    captured["query"] = controlled_query
    query = captured["query"]
    source = captured["kwargs"]["source"]
    plan = plain(captured["kwargs"]["plan"])
    from eonwild_motion.planning.locomotion_sequence import WalkSequence
    from eonwild_motion.solve.locomotion_sequence import SequenceEvaluator
    sequence = WalkSequence(query._locomotion_gait, query.context.body_height, plan['parameters'])
    duration = sequence.duration
    times = np.unique(np.concatenate((np.linspace(0., duration, round(duration*60)+1), sequence.bounds)))
    evaluator = SequenceEvaluator(neutral_query, sequence, captured['law']._skin, captured['provider'], control)
    poses, rows, checks = [], [], []
    print('Evaluating connected source sequence', duration, len(times), flush=True)
    for i,(row,pose,check) in enumerate(evaluator.emit_samples(times)):
        poses.append(pose); rows.append(row); checks.append(check)
        if i % 120 == 0: print('Solved', i, '/', len(times), flush=True)
    plan['samples'] = rows
    plan['loop'] = False
    plan['sequence'] = {'stages':sequence.stages, 'boundaries_s':sequence.bounds, 'faster_cadence_ratio':sequence.rate}
    target.parent.mkdir(parents=True, exist_ok=True)
    translations = np.asarray([pose.translations for pose in poses], dtype=np.float64)
    rotations = np.asarray([pose.rotations for pose in poses], dtype=np.float64)
    rotations /= np.linalg.norm(rotations, axis=2)[:, :, None]
    for index in range(1, len(rotations)):
        flip = np.sum(rotations[index - 1] * rotations[index], axis=1) < 0
        rotations[index, flip] *= -1

    document = deepcopy(source.document)
    binary = bytearray(source.binary)
    time_accessor = _append_accessor(document, binary, times.reshape((-1, 1)), "SCALAR")
    samplers, channels = [], []
    for node in range(len(source.nodes)):
        for path, values in (("translation", translations[:, node]), ("rotation", rotations[:, node])):
            output = _append_accessor(document, binary, values, "VEC3" if path == "translation" else "VEC4")
            sampler = len(samplers)
            samplers.append({"input": time_accessor, "output": output, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler, "target": {"node": node, "path": path}})
    clip = target.name + ".root_motion"
    document["animations"] = [{
        "name": clip,
        "samplers": samplers,
        "channels": channels,
        "extras": {
            "diagnostic": "CONTACT_MASS_CORRECTED_DIAGNOSTIC",
            "program": "grounded_gait",
            "loop": bool(plan.get("loop", True)),
            "finalContactCorrections": "APPLIED_SOURCE_LAW",
            "massCoupling": "APPLIED_ENGINEERING_PROXY",
        },
    }]
    document.setdefault("extras", {})["eonwildDiagnostic"] = {
        "status": "CONTACT_MASS_CORRECTED_DIAGNOSTIC",
        "production": False,
        "visual": "PENDING",
        "finalContactCorrections": "APPLIED_SOURCE_LAW",
        "massCoupling": "APPLIED_ENGINEERING_PROXY",
        "sharedFinalLaw": "NOT_CLAIMED",
    }
    document["buffers"][0]["byteLength"] = len(binary)
    glb_bytes = _encode(document, binary)

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    set_bytes = args.motion_set.resolve().read_bytes()
    intent = json.loads(set_bytes)["motions"][0]["intent"]
    capture = {
        "schema": "eonwild.motion.diagnostic-query-capture.v1",
        "status": "CONTACT_MASS_CORRECTED_DIAGNOSTIC",
        "production": False,
        "compiler_commit": commit,
        "interception": "frozen contact law rebound to recorded mass-solver coefficients",
        "motion_set": {"path": str(args.motion_set.resolve().relative_to(repo)), "sha256": digest(set_bytes)},
        "shared_walk_intent": intent,
        "query_class": type(query).__name__,
        "provider_class": type(captured["provider"]).__name__,
        "source_sha256": digest(source.raw),
        "plan_sha256": digest(canonical(plan)),
        "sampling": {"source_keys_per_second": 60, "review_fps": 24, "key_count": len(times), "start_s": 0.0, "end_s": duration, "timeline": "inclusive native extent"},
        "limitations": {"final_contact_corrections": "APPLIED_SOURCE_LAW", "mass_coupling": "APPLIED_ENGINEERING_PROXY", "shared_final_law": "NOT_CLAIMED", "visual": "PENDING"},
    }
    runtime = {
        "schema": "eonwild.motion.runtime-data.v1",
        "program": "grounded_gait",
        "family": plain(captured["kwargs"].get("locomotion_gait").__class__.__name__),
        "units": "m", "time_units": "s", "handedness": "right",
        "forward_axis": plain(captured["kwargs"]["forward_axis"]),
        "up_axis": plain(captured["kwargs"]["up_axis"]),
        "root_authority": "applied root motion diagnostic preview",
        "rig_roles": plain(captured["kwargs"]["semantic_roles"]),
        "duration_s": duration, "loop": bool(plan.get("loop", True)),
        "initial_contacts": {side: bool(plan["samples"][0]["feet"][side]["contact"]) for side in ("left", "right")},
        "events": [], "plan_sha256": capture["plan_sha256"],
        "world_interaction_authority": "runtime decides contact, damage, grip resistance and release",
        "unity_import_status": "NOT_VERIFIED", "transition_contract": None,
        "ground_plane": plain(captured["kwargs"].get("contact_profile", {}).get("geometry", {}).get("ground")),
        "diagnostic_status": "CONTACT_MASS_CORRECTED_DIAGNOSTIC", "production": False,
        "final_contact_corrections": "APPLIED_SOURCE_LAW", "mass_coupling": "APPLIED_ENGINEERING_PROXY", "visual": "PENDING",
    }
    payloads = {
        "root_motion.glb": glb_bytes,
        "body-support-coordination.json": canonical(mass_receipt),
        "sequence-contact-samples.json": canonical({"times":times.tolist(),"samples":checks}),
        "approved-walk-contact-law.json": canonical(captured["law"].receipt()),
        "runtime.json": canonical(runtime),
        "plan.json": canonical(plan),
        "compiler-query-capture.json": canonical(capture),
    }
    manifest = {
        "schema": "eonwild.motion.diagnostic-package.v1", "id": target.name,
        "status": "CONTACT_MASS_CORRECTED_DIAGNOSTIC", "production": False,
        "technical_status": "NOT_RUN", "visual": "PENDING",
        "final_contact_corrections": "APPLIED_SOURCE_LAW", "mass_coupling": "APPLIED_ENGINEERING_PROXY",
        "files": {name: digest(data) for name, data in payloads.items()},
    }
    stage = Path(tempfile.mkdtemp(prefix=".query-preview-", dir=target.parent))
    try:
        for name, data in payloads.items():
            (stage / name).write_bytes(data)
        (stage / "manifest.json").write_bytes(canonical(manifest))
        stage.rename(target)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    reopened = Glb(target / "root_motion.glb")
    tracks, timeline = read_animation_tracks(reopened, clip, require_common_timeline=True)
    if len(tracks) != 2 * len(reopened.nodes) or not np.isclose(timeline[0], 0.0) or not np.isclose(timeline[-1], duration):
        raise RuntimeError("reopened diagnostic tracks or native clock differ")
    print(json.dumps({"package": str(target), "source_sha256": capture["source_sha256"], "plan_sha256": capture["plan_sha256"], "duration_s": duration, "keys": len(timeline), "tracks": len(tracks), "reopen": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
