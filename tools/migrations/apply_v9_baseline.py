"""One-time migration from 8c1f5c2. Not imported by the factory.

Only the dedicated bootstrap workflow runs this. Historical artifacts and the
V8.2 release capsule keep exact bytes. Normal CI never migrates or commits.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
PIN = "8c1f5c2bfea481a56916ee6e0bfa74961ca0d141"
MARKER = ROOT / "catalog/baselines/factory-migration.json"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")
def replace_once(text, old, new):
    if text.count(old) != 1: raise RuntimeError(f"migration patch is not unique: {old[:100]}")
    return text.replace(old, new, 1)


def patch_emitter():
    path = ROOT / "src/eonwild_motion/solve/airborne_gait.py"
    text = path.read_text()
    text = replace_once(text, "source_clip: str, semantic_roles:", "source_clip: str | None, semantic_roles:")
    text = replace_once(text, "plan_override: Mapping[str, Any] | None = None) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:",
        "plan_override: Mapping[str, Any] | None = None, forward_axis: tuple[float, float, float] | None = None, legacy_overlay: bool = True) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:")
    old = '''    tracks, source_times = _clip_state(source, source_clip)
    translations, rotations, scales = _pose(source, tracks, 0)
    worlds = _world_matrices(source, translations, rotations, scales)
    final_worlds = _world_matrices(source, *_pose(source, tracks, len(source_times) - 1))
    up = _unit(up_axis)
    travel = np.asarray(_world_position(final_worlds[root])) - np.asarray(_world_position(worlds[root]))
    forward = _unit(travel - up * (travel @ up))'''
    new = '''    up = _unit(up_axis)
    if source_clip is None:
        if forward_axis is None:
            raise ContractError("neutral geometry requires an explicit forward axis")
        translations, rotations, scales = source.rest_translation, source.rest_rotation, source.rest_scale
        worlds = _world_matrices(source, translations, rotations, scales)
        travel = np.asarray(forward_axis, dtype=float)
    else:
        tracks, source_times = _clip_state(source, source_clip)
        translations, rotations, scales = _pose(source, tracks, 0)
        worlds = _world_matrices(source, translations, rotations, scales)
        final_worlds = _world_matrices(source, *_pose(source, tracks, len(source_times) - 1))
        travel = (np.asarray(forward_axis, dtype=float) if forward_axis is not None else
                  np.asarray(_world_position(final_worlds[root])) - np.asarray(_world_position(worlds[root])))
    if travel.shape != (3,) or not np.isfinite(travel).all():
        raise ContractError("forward axis must be a finite three-vector")
    forward = _unit(travel - up * (travel @ up))'''
    text = replace_once(text, old, new)
    text = replace_once(text, '''    plan = build_airborne_plan(gait, body_height)
    if plan_override is not None:
        plan = _validate_plan_override(plan_override, gait)''',
        '''    # Behavior programs own support choreography; an override never runs
    # the airborne planner. Legacy calls retain their original default path.
    plan = (build_airborne_plan(gait, body_height) if plan_override is None else
            _validate_plan_override(plan_override, gait))''')
    text = replace_once(text, '''        else:
            # Preserve the pre-existing default path''', '''        elif legacy_overlay:
            # Preserve the pre-existing default path''')
    text = replace_once(text, '    out["schema"] = "eonwild.motion.v9.airborne-gait-plan.v1"', '    out.setdefault("schema", "eonwild.motion.v9.airborne-gait-plan.v1")')
    text = replace_once(text, '    out["program"] = "airborne_gait"', '    out.setdefault("program", "airborne_gait")')
    path.write_text(text)


def retire_legacy():
    old, new = "procedural-animation-toolkit(v8.2)", "legacy/capsules/v8.2"
    before = {p.relative_to(ROOT / old).as_posix(): sha(p) for p in (ROOT / old).rglob("*") if p.is_file()}
    (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(ROOT / old), str(ROOT / new))
    assert before == {p.relative_to(ROOT / new).as_posix(): sha(p) for p in (ROOT / new).rglob("*") if p.is_file()}
    removed = []
    for folder in ("procedural-animation-toolkit(v8)", "procedural-animation-toolkit(v8.1)"):
        paths = [p for p in (ROOT / folder).rglob("*") if p.is_file()]
        removed.append({"path": folder, "files": len(paths), "bytes": sum(p.stat().st_size for p in paths), "recover_from_commit": PIN})
        shutil.rmtree(ROOT / folder)
    # Only active consumers change. Historical reports and capsule contents
    # remain evidence of the old layout, and retain their original hashes.
    for base, extension in (("tests", "*.py"), ("profiles", "*.json"), ("catalog", "*.json")):
        for p in (ROOT / base).rglob(extension):
            text = p.read_text()
            if old in text: p.write_text(text.replace(old, new))
    from eonwild_motion.hashing import sha256_json
    for version in ("v8.2", "v8.3"):
        p = ROOT / "profiles" / version / "profile.json"
        profile = json.loads(p.read_text())
        for key in ("rig", "family", "species", "motion", "renderSet", "input", "approvedOutput", "contactEvidence"):
            profile[key]["sha256"] = sha(ROOT / profile[key]["path"])
        for binding in profile["layers"]: binding["sha256"] = sha(ROOT / binding["path"])
        write(p, profile)
        lock = {"schema": "eonwild.motion.resolved-profile.v1", "profile": {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "id": profile["id"], "version": profile["version"]},
            "documents": {key: {**profile[key], "id": json.loads((ROOT / profile[key]["path"]).read_text())["id"]} for key in ("rig", "family", "species", "motion", "renderSet")},
            "layers": [{**binding, "id": json.loads((ROOT / binding["path"]).read_text())["id"]} for binding in profile["layers"]],
            "input": profile["input"], "approvedOutput": profile["approvedOutput"], "sourceManifest": profile["sourceRelease"]["manifest"], "contactEvidence": profile["contactEvidence"]}
        write(p.with_name("profile.lock.json"), {**lock, "lockSha256": sha256_json(lock)})
    p = ROOT / "profiles/channels/state.json"
    state = json.loads(p.read_text())
    for name in ("stable", "working"):
        binding = state[name]["profile"]
        pp = ROOT / binding["path"]
        binding["sha256"] = sha(pp)
        state[name]["profileLockSha256"] = json.loads(pp.with_name("profile.lock.json").read_text())["lockSha256"]
    write(p, state)
    from eonwild_motion.contracts.resolve import resolve_profile
    resolve_profile("stable", repository=ROOT)
    resolve_profile("working", repository=ROOT)
    return {"removed": removed, "relocated_capsule": {"from": old, "to": new, "unchanged_files": before}}


def admit_and_register():
    from eonwild_motion.factory.io import bind
    from eonwild_motion.factory.source import admit_geometry
    from eonwild_motion.glb.container import Glb
    folder = ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12"
    source = folder / "narrow-gauge-walk-root_motion.glb"
    assert sha(source) == "b54e3740ea451927b3b812c1be3f4ca6146cc369ad1313be7f08edd5ca741cd3"
    binding = ROOT / "profiles/v9/rig.airborne-jaw-breathing.json"
    raw, geometry = admit_geometry(Glb(source), json.loads(binding.read_text())["roles"], reference_clip="PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION")
    asset = ROOT / "assets/sha256" / (hashlib.sha256(raw).hexdigest() + ".glb")
    asset.write_bytes(raw)
    rig = ROOT / "catalog/rigs/heavy-biped.v9.json"
    rig.write_bytes(binding.read_bytes())
    contact = json.loads((folder / "candidate-contact-profile-root_motion.json").read_text())
    contact["source"] = {**bind(ROOT, asset), "clips": {"root_motion": "factory-defined", "in_place": "factory-defined"}}
    cp = ROOT / "catalog/contacts/heavy-biped.v9.json"
    write(cp, contact)
    baseline_entries = []
    profiles = [
        ("run", ROOT / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate/engineering-profile.json"),
        ("sprint", ROOT / "build/V9-AIRBORNE-SPRINT-001/review-candidate-006/candidate/engineering-profile.json")]
    for label, old in profiles:
        if not old.is_file():
            choices = list(old.parents[1].rglob("engineering-profile.json"))
            if len(choices) != 1: raise RuntimeError(f"cannot resolve unique {label} approved profile: {choices}")
            old = choices[0]
        original = json.loads(old.read_text())
        baseline_entries.append({"motion": label, "profile": bind(ROOT, old), "status": "user-approved historical take; approval does not transfer to new recipe", "reference_commit": PIN})
        for revision in (1, 2):
            profile = deepcopy(original)
            profile["status"] = "FACTORY_CANDIDATE_REQUIRES_REVIEW"
            if revision == 2:
                # Opt-in restrained response: same contact/stride choreography,
                # slower axial settling, softer breathing. No post-bake noise.
                profile["parameters"]["body_response_time_s"] = .09
                profile["parameters"]["head_stabilization_gain"] = .9
                profile["parameters"]["jaw_breathing_max_degrees"] = 3.0 if label == "run" else 2.5
            pp = ROOT / f"catalog/programs/heavy-biped.{label}.v{revision}.json"
            write(pp, profile)
            recipe = {"schema": "eonwild.motion.factory-recipe.v1", "id": f"heavy-biped.{label}.v{revision}", "version": revision,
                "family": "heavy-predatory-biped", "program": "airborne_gait", "source": bind(ROOT, asset), "rig": bind(ROOT, rig),
                "program_profile": bind(ROOT, pp), "contact_profile": bind(ROOT, cp),
                "forward_axis": geometry["forward_axis"], "up_axis": geometry["up_axis"],
                "description": "Recovered performance" if revision == 1 else "Opt-in restrained head/breathing response, not visually approved"}
            write(ROOT / f"recipes/heavy-biped/{label}.v{revision}.json", recipe)
    pp = ROOT / "catalog/programs/heavy-biped.reverse-walk.v1.json"
    write(pp, {"schema": "eonwild.motion.v9.grounded-gait.v1", "parameters": {}})
    write(ROOT / "recipes/heavy-biped/reverse-walk.v1.json", {"schema": "eonwild.motion.factory-recipe.v1", "id": "heavy-biped.reverse-walk.v1", "version": 1,
        "family": "heavy-predatory-biped", "program": "grounded_gait", "source": bind(ROOT, asset), "rig": bind(ROOT, rig),
        "program_profile": bind(ROOT, pp), "contact_profile": bind(ROOT, cp), "forward_axis": geometry["forward_axis"], "up_axis": geometry["up_axis"],
        "description": "Grounded reverse shuffle with 72 percent duty; no reversed forward-animation trick"})
    feeding = ROOT / "build/V9-FEEDING-REVIEW-003/feeding.glb"
    assert sha(feeding) == "8f70dcab8e8b56035ed0787ca15674166575213f098ec9c6579e6e8350b6d47b"
    baseline_entries.append({"motion": "feeding", "artifact": bind(ROOT, feeding), "status": "user-approved Feeding003, unchanged", "reference_commit": PIN})
    write(ROOT / "catalog/baselines/approved-takes.json", {"schema": "eonwild.motion.baselines.v1", "source_commit": PIN, "takes": baseline_entries,
        "approval_evidence": "reports/V9-THREE-MOTION-REVIEW-003/README.md"})
    return {"source": bind(ROOT, source), "neutral_geometry": bind(ROOT, asset), "admission": geometry}


def main():
    if MARKER.exists():
        print("Migration already applied; no files changed.")
        return
    patch_emitter()
    retirement = retire_legacy()
    admission = admit_and_register()
    write(MARKER, {"schema": "eonwild.motion.migration.v1", "source_commit": PIN, "retirement": retirement, "admission": admission,
        "claim": "baseline consolidation, not complete V9 or Unity acceptance"})
    print(json.dumps({"retirement": retirement["removed"], "neutral_geometry": admission["neutral_geometry"]}, indent=2))


if __name__ == "__main__": main()
