"""Candidate compiler from locked neutral geometry and versioned programs.

Generation, final mechanical evidence, perceptual review and Unity parity are
separate. This module never imports historical experiment builders or grants
production approval. Baked GLBs are outputs, not the reusable program itself.
"""
from __future__ import annotations

import json
from pathlib import Path
import platform
import shutil
import tempfile
from typing import Any

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from ..planning.airborne_gait import AirborneGait, build_airborne_plan, load_airborne_gait
from ..planning.grounded_gait import build_grounded_plan, load_grounded_gait
from ..solve.airborne_gait import solve_airborne_gait, evaluate_airborne_skin_with_authority
from ..solve.whole_body_gait_transition import _encode
from .io import digest, frame_axes, json_bytes, locked_file, read_json, write_json
from .quality import (emitted_articulation_envelopes, emitted_rotation_rates,
                      emitted_cyclic_continuity, require_supported_geometry, solver_checks)
from .source import geometry_height
from .animal import (apply_uniform_geometry_scale,biomechanics_report,
    load_animal_instance,scaled_contact_profile,verify_source_calibration)
from ..solve.performance import load_performance, decorate_plan
from ..solve.skin_targets import solve_with_skin_targets, evaluate_skin
from ..solve.support_anchors import CanonicalSupportAnchorProvider
from ..planning.supported_action import load_supported_action
from ..planning.gait_transition import load_gait_transition, build_transition_plan
from ..planning.articulation_profile import load_articulation_profile
from ..solve.supported_action import solve_supported_action
from ..solve.gaze import calibrate_rostral_direction

SCHEMA = "eonwild.motion.factory-recipe.v1"
PROGRAMS = ("airborne_gait", "grounded_gait", "supported_action", "gait_transition")


def load_recipe(path: Path, root: Path) -> tuple[dict, dict[str, Path]]:
    recipe = read_json(path)
    required = {"schema", "id", "version", "family", "program", "source", "rig", "program_profile", "forward_axis", "up_axis"}
    if not isinstance(recipe, dict) or set(recipe) - required - {"animal", "contact_profile", "performance_profile", "gait_profile", "articulation_profile", "description", "supersedes"} or not required <= set(recipe):
        raise ContractError("recipe contains missing or unknown fields")
    if recipe["schema"] != SCHEMA or recipe["program"] not in PROGRAMS:
        raise ContractError("unsupported recipe schema or program")
    if not isinstance(recipe["id"], str) or not recipe["id"] or not isinstance(recipe["family"], str) or not recipe["family"]:
        raise ContractError("recipe id and family are required")
    if type(recipe["version"]) is not int or recipe["version"] < 1:
        raise ContractError("recipe version must be a positive integer")
    frame_axes(recipe["forward_axis"], recipe["up_axis"])
    paths = {key: locked_file(root, recipe[key]) for key in ("source", "rig", "program_profile")}
    if "animal" in recipe:
        paths["animal"] = locked_file(root, recipe["animal"])
    if "contact_profile" in recipe:
        paths["contact_profile"] = locked_file(root, recipe["contact_profile"])
    if "performance_profile" in recipe:
        paths["performance_profile"] = locked_file(root, recipe["performance_profile"])
    if "articulation_profile" in recipe:
        if recipe["program"] == "supported_action":
            raise ContractError("supported actions retain their own support limits")
        paths["articulation_profile"] = locked_file(root, recipe["articulation_profile"])
    if "gait_profile" in recipe:
        if recipe["program"] != "gait_transition":
            raise ContractError("only gait transitions accept a separate locomotion profile")
        paths["gait_profile"] = locked_file(root, recipe["gait_profile"])
    elif recipe["program"] == "gait_transition":
        raise ContractError("gait transition requires a locked locomotion profile")
    return recipe, paths


def validate_plan(plan: dict, program: str) -> None:
    samples = plan.get("samples", [])
    if len(samples) < 2 or float(samples[0]["time_s"]) != 0:
        raise ContractError("motion plan must begin at zero and contain at least two samples")
    previous = -1.0
    double_support = False
    for row in samples:
        time = row["time_s"]
        if isinstance(time, bool) or not np.isfinite(time) or time <= previous:
            raise ContractError("plan samples must have strictly increasing finite times")
        previous = time
        contacts = [row["feet"][side]["contact"] for side in ("left", "right")]
        if any(type(value) is not bool for value in contacts):
            raise ContractError("contact state must be boolean")
        support = sum(contacts)
        if type(row["support_count"]) is not int or row["support_count"] != support or type(row["flight"]) is not bool or row["flight"] != (support == 0):
            raise ContractError("plan contact, support and flight disagree")
        double_support |= support == 2
        if (program == "grounded_gait" or plan.get("locomotion_program") == "grounded_gait") and support == 0:
            raise ContractError("grounded gait must not fly")
    if program == "grounded_gait" and not double_support:
        raise ContractError("grounded gait must include double support")


def event_track(plan: dict) -> list[dict]:
    events = []
    previous = {side: plan["samples"][0]["feet"][side]["contact"] for side in ("left", "right")}
    for row in plan["samples"][1:]:
        for side in previous:
            contact = row["feet"][side]["contact"]
            if contact != previous[side]:
                events.append({"time_s": row["time_s"], "name": ("L" if side == "left" else "R") + ("_FOOT_CONTACT" if contact else "_FOOT_RELEASE"), "side": side,
                               "kind": "animation_cue", "authoritative_world_fact": False})
            previous[side] = contact
    return events


def tag_output(raw: bytes, recipe: dict, plan: dict, suffix: str) -> bytes:
    glb = Glb.from_bytes(raw)
    animation = glb.document["animations"][0]
    animation["name"] = recipe["id"] + "." + suffix
    animation.setdefault("extras", {}).update(program=recipe["program"], loop=plan.get("loop", True),
        plan_sha256=digest(json_bytes(plan)), root_motion=(suffix == "root_motion"))
    glb.document.setdefault("extras", {})["eonwildMotionStateTrack"] = {
        "program": recipe["program"], "samples": [{"time_s": row["time_s"], "flight": row["flight"],
        "support_count": row["support_count"], "contacts": {side: row["feet"][side]["contact"] for side in ("left", "right")}} for row in plan["samples"]]}
    return _encode(glb.document, glb.binary)


def evaluate_emitted(glb: Glb, source: Glb, roles: dict, plan: dict, forward: Any, *, in_place: bool = False) -> dict:
    """Reopen actual float32 channels. Skeleton proxies are labeled explicitly."""
    clip = glb.document["animations"][0]["name"]
    tracks, times = _clip_state(glb, clip)
    if len(times) != len(plan["samples"]) or not np.allclose(times, [r["time_s"] for r in plan["samples"]], rtol=0, atol=2e-6):
        raise ContractError("emitted timeline differs from the authoritative plan")
    root, pelvis = (glb.name_to_node[roles[name]] for name in ("root", "pelvis"))
    neutral = _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale)
    base_root = np.asarray(_world_position(neutral[root]))
    base_t, base_s = np.asarray(source.rest_translation), np.asarray(source.rest_scale)
    protected = [i for i in range(len(source.nodes)) if i not in (root, pelvis)]
    max_root_error = max_attachment = max_scale_error = max_tip_drift = 0.0
    first_r = last_r = None
    previous_tips, previous_row = {}, None
    forward = np.asarray(forward, dtype=float)
    for i, row in enumerate(plan["samples"]):
        t, r, s = map(np.asarray, _pose(glb, tracks, i))
        if not all(np.isfinite(array).all() for array in (t, r, s)):
            raise ContractError("emitted non-finite pose")
        norms = np.linalg.norm(r, axis=1)
        if np.max(np.abs(norms - 1)) > 1e-4:
            raise ContractError("emitted non-unit quaternion")
        r = r / norms[:, None]
        first_r = r.copy() if first_r is None else first_r
        last_r = r
        max_attachment = max(max_attachment, float(np.max(np.abs(t[protected] - base_t[protected]))))
        max_scale_error = max(max_scale_error, float(np.max(np.abs(s - base_s))))
        worlds = _world_matrices(glb, t.tolist(), r.tolist(), s.tolist())
        expected = base_root + forward * (0 if in_place else row["root_forward_m"])
        max_root_error = max(max_root_error, float(np.linalg.norm(np.asarray(_world_position(worlds[root])) - expected)))
        for side in ("left", "right"):
            tips = np.asarray([_world_position(worlds[glb.name_to_node[chain[-1]]]) for chain in roles["legs"][side]["toeChains"]])
            if in_place:
                tips += forward * row["root_forward_m"]
            if previous_row is not None and row["feet"][side]["contact"] and previous_row["feet"][side]["contact"]:
                planned_delta = np.asarray(row["feet"][side].get("target_offset_m", [0.,0.,0.])) - np.asarray(previous_row["feet"][side].get("target_offset_m", [0.,0.,0.]))
                max_tip_drift = max(max_tip_drift, float(np.linalg.norm(tips - previous_tips[side] - planned_delta, axis=1).max()))
            previous_tips[side] = tips
        previous_row = row
    max_seam = float(np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(first_r * last_r, axis=1)), 0, 1))).max())
    checks = {"root_matches_plan": max_root_error <= 2e-5, "attachments_unchanged": max_attachment <= 2e-6,
              "scales_unchanged": max_scale_error <= 2e-6, "rotation_loop_closed": max_seam <= 0.5,
              "skeleton_contact_stationary": max_tip_drift <= 0.001}
    if not plan.get("loop", True):
        del checks["rotation_loop_closed"]
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "maximum_root_error_m": max_root_error, "maximum_attachment_error_m": max_attachment,
            "maximum_scale_error": max_scale_error, "maximum_rotation_seam_degrees": max_seam,
            "maximum_planted_digit_step_drift_m": max_tip_drift,
            "classification": "reopened skeleton target-relative proxy; explicit pre-solve skin offsets accounted for, final material contact independently checked"}


def engine_fingerprint() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in sorted(root.rglob("*.py"))}


_ENGINE_AT_IMPORT = engine_fingerprint()


def compile_recipe(recipe_path: Path, *, root: Path, output: Path) -> dict:
    engine_identity = engine_fingerprint()
    if engine_identity != _ENGINE_AT_IMPORT:
        raise ContractError("engine sources changed since import; restart the compiler")
    root, recipe_path, output = root.resolve(), recipe_path.resolve(), output.resolve()
    if output.exists():
        raise ContractError("candidate output already exists; never overwrite an existing take")
    recipe_bytes = recipe_path.read_bytes()
    recipe, paths = load_recipe(recipe_path, root)
    if json.loads(recipe_bytes) != recipe:
        raise ContractError("recipe changed during input resolution")
    # Compile only from bytes whose hashes were checked, not later rereads.
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    for name, raw in snapshots.items():
        if digest(raw) != recipe[name]["sha256"]:
            raise ContractError(f"input changed during snapshot: {name}")
    source = Glb.from_bytes(snapshots["source"])
    require_supported_geometry(source)
    if source.document.get("animations"):
        raise ContractError("factory source must be admitted neutral geometry, not a prior animation")
    geometry = source.document.get("extras", {}).get("eonwildGeometry", {})
    forward, up = frame_axes(recipe["forward_axis"], recipe["up_axis"])
    declared_forward, declared_up = frame_axes(geometry.get("forward_axis"), geometry.get("up_axis"))
    if not np.allclose(declared_forward, forward) or not np.allclose(declared_up, up):
        raise ContractError("recipe coordinate frame differs from admitted geometry")
    roles = json.loads(snapshots["rig"])["roles"]
    contact_profile = json.loads(snapshots["contact_profile"]) if "contact_profile" in snapshots else None
    animal = None
    if "animal" in snapshots:
        if "contact_profile" not in snapshots:
            raise ContractError("animal geometry calibration requires a locked contact profile")
        animal = load_animal_instance(json.loads(snapshots["animal"]),source_sha256=recipe["source"]["sha256"])
        verify_source_calibration(animal,source,roles,contact_profile,forward,up)
        apply_uniform_geometry_scale(source,animal["uniform_scale"])
        contact_profile = scaled_contact_profile(contact_profile,animal["uniform_scale"])
        require_supported_geometry(source)
    profile = json.loads(snapshots["program_profile"])
    articulation_profile = (load_articulation_profile(json.loads(snapshots["articulation_profile"]))
                            if "articulation_profile" in snapshots else None)
    height = geometry_height(source, roles, up)
    supported = recipe["program"] == "supported_action"
    locomotion_gait = None
    transition = None
    if recipe["program"] == "airborne_gait":
        gait = load_airborne_gait(profile)
        locomotion_gait = gait
        plan = build_airborne_plan(gait, height)
        plan["program"] = "airborne_gait"
    elif recipe["program"] == "gait_transition":
        transition = load_gait_transition(profile)
        locomotion = json.loads(snapshots["gait_profile"])
        if locomotion.get("schema") == "eonwild.motion.v9.grounded-gait.v1":
            grounded = load_grounded_gait(locomotion)
            locomotion_gait = grounded
            gait = AirborneGait(step_period_s=grounded.step_period_s, cycles=grounded.cycles,
                sample_hz=transition.sample_hz, swing_hip_lift_degrees=grounded.swing_hip_lift_degrees)
            plan = build_transition_plan(transition, grounded, height)
        else:
            gait = load_airborne_gait(locomotion)
            locomotion_gait = gait
            plan = build_transition_plan(transition, gait, height)
    elif not supported:
        grounded = load_grounded_gait(profile)
        locomotion_gait = grounded
        plan = build_grounded_plan(grounded, height)
        # Only articulation settings are reused. plan_override prevents the
        # airborne support schedule from being evaluated for grounded walking.
        gait = AirborneGait(step_period_s=grounded.step_period_s, cycles=grounded.cycles,
                           sample_hz=grounded.sample_hz, swing_hip_lift_degrees=grounded.swing_hip_lift_degrees)
    if supported:
        if "contact_profile" not in snapshots or "performance_profile" in snapshots:
            raise ContractError("supported actions require contact data and their own performance channels")
        action = load_supported_action(profile)
        gait = AirborneGait(max_joint_angular_velocity_degrees_per_s=action.max_joint_rate_degrees_per_second)
        root_raw, inplace_raw, plan, receipt = solve_supported_action(source, semantic_roles=roles, action=action,
            contact_profile=contact_profile, up_axis=up, forward_axis=forward, body_height_m=height)
    if "performance_profile" in snapshots:
        plan = decorate_plan(plan, load_performance(json.loads(snapshots["performance_profile"])))
        if "contact_profile" not in snapshots:
            raise ContractError("forward attention requires locked geometry calibration")
        plan["gaze_calibration"] = calibrate_rostral_direction(source, roles=roles,
            contact_profile=contact_profile, forward_axis=forward, up_axis=up)
    validate_plan(plan, recipe["program"])
    biomechanics = biomechanics_report(animal,plan,actual_semantic_height_m=height) if animal else None
    if supported:
        pass  # Already solved by the persistent-support program above.
    elif plan.get("performance", {}).get("skin_refinement", False):
        if "contact_profile" not in snapshots:
            raise ContractError("skin refinement requires a locked contact profile")
        support_anchor_provider = None
        if plan["performance"].get("canonical_support_anchors") is True:
            if locomotion_gait is None:
                raise ContractError("canonical support anchors require bound locomotion gait")
            support_anchor_provider = CanonicalSupportAnchorProvider.build(
                source, semantic_roles=roles, solver_gait=gait,
                locomotion_gait=locomotion_gait, transition=transition, plan=plan,
                contact_profile=contact_profile, up_axis=tuple(up),
                forward_axis=tuple(forward), articulation_profile=articulation_profile)
        root_raw, inplace_raw, plan, receipt = solve_with_skin_targets(source, semantic_roles=roles,
            gait=gait, up_axis=up, forward_axis=forward, plan=plan,
            contact_profile=contact_profile, articulation_profile=articulation_profile,
            canonical_support_anchor_provider=support_anchor_provider)
    else:
        root_raw, inplace_raw, _, receipt = solve_airborne_gait(source, source_clip=None,
            semantic_roles=roles, gait=gait, up_axis=tuple(up), forward_axis=tuple(forward),
            plan_override=plan, legacy_overlay=False, articulation_profile=articulation_profile)
    root_raw, inplace_raw = (tag_output(raw, recipe, plan, mode) for raw, mode in ((root_raw, "root_motion"), (inplace_raw, "in_place")))
    outputs = {"root_motion": Glb.from_bytes(root_raw), "in_place": Glb.from_bytes(inplace_raw)}
    evaluated = {mode: evaluate_emitted(glb, source, roles, plan, forward, in_place=(mode == "in_place")) for mode, glb in outputs.items()}
    rates = {mode: emitted_rotation_rates(glb, gait.max_joint_angular_velocity_degrees_per_s) for mode, glb in outputs.items()}
    continuity = {mode: emitted_cyclic_continuity(glb, loop=plan.get("loop", True)) for mode, glb in outputs.items()}
    articulation = None
    if articulation_profile is not None:
        articulation = {
            mode: emitted_articulation_envelopes(
                glb, semantic_roles=roles, plan=plan,
                profile=articulation_profile, forward_axis=forward, up_axis=up,
            )
            for mode, glb in outputs.items()
        }
    feasibility = solver_checks(receipt)
    surface = {"verdict": "NOT_MEASURED", "reason": "no bound skinned contact profile"}
    if "contact_profile" in snapshots:
        try:
            facts = evaluate_airborne_skin_with_authority(outputs["root_motion"],
                contact_profile=contact_profile, gait=gait, body_height_m=height,
                clip_name=recipe["id"] + ".root_motion", plan_override=plan)
            surface = {"verdict": facts["contact_authority_v1"]["verdict"], "authority": facts["contact_authority_v1"],
                       "maximum_penetration_m": facts["maximum_foot_surface_penetration_m"],
                       "planned_stance_without_contact_samples": facts["planned_stance_without_surface_contact_samples"]}
        except (ContractError, ValueError, KeyError, StopIteration) as exc:
            surface = {"verdict": "FAIL", "reason": f"final skinned evaluation failed: {exc}"}
    if ("performance_profile" in snapshots or supported) and "contact_profile" in snapshots:
        surface = evaluate_skin(outputs["root_motion"], contact_profile, plan)
    in_place_surface = {"verdict": "NOT_MEASURED", "reason": "no bound skinned contact profile"}
    if "contact_profile" in snapshots:
        try:
            origin_travel = plan["samples"][0]["root_forward_m"]
            offsets = [forward * (row["root_forward_m"] - origin_travel) for row in plan["samples"]]
            in_place_surface = evaluate_skin(outputs["in_place"], contact_profile, plan,
                world_offsets=offsets)
        except (ContractError, ValueError, KeyError, StopIteration) as exc:
            in_place_surface = {"verdict": "FAIL", "reason": f"in-place skinned reconstruction failed: {exc}"}
    receipt["final_skinned_contact_gate"] = "PASS" if surface["verdict"] == in_place_surface["verdict"] == "PASS" else "FAIL"
    receipt["final_skinned_contact_scope"] = "both reopened serialized exports; in-place plus planned motor travel; locked floor and full skin influences"
    refinement_ok = receipt.get("skin_target_refinement", {}).get("converged", True) and receipt.get("oral_contact", {"status":"PASS"})["status"] == "PASS"
    articulation_ok = articulation is None or all(row["status"] == "PASS" for row in articulation.values())
    technical = (refinement_ok and articulation_ok and all(row["status"] == "PASS" for row in evaluated.values()) and
                 all(row["status"] == "PASS" for row in rates.values()) and
                 all(row["status"] in ("PASS", "NOT_APPLICABLE") for row in continuity.values()) and feasibility["status"] == "PASS" and surface["verdict"] == "PASS" and in_place_surface["verdict"] == "PASS")
    validation = {"schema": "eonwild.motion.factory-validation.v1", "technical_status": "PASS" if technical else "BLOCKED",
        "outputs": evaluated, "rotation_rates": rates, "cyclic_continuity": continuity, "solver_feasibility": feasibility, "skinned_contact": surface, "in_place_skinned_contact": in_place_surface,
        "oral_contact": receipt.get("oral_contact"),
        "visual_review": "PENDING", "unity_parity": "NOT_RUN", "production_approved": False}
    if articulation is not None:
        validation["articulation_envelopes"] = articulation
        receipt["final_emitted_articulation_gate"] = "PASS" if articulation_ok else "FAIL"
        receipt["final_emitted_articulation_scope"] = "both reopened serialized exports"
    if engine_fingerprint() != engine_identity:
        raise ContractError("engine sources changed during compilation; no candidate published")
    lock = {"schema": "eonwild.motion.factory-lock.v1", "recipe_sha256": digest(recipe_bytes),
            "inputs": {name: recipe[name] for name in paths}, "engine_files": engine_identity,
            "tools": {"python": platform.python_version(), "numpy": np.__version__}}
    state = {"schema": "eonwild.motion.runtime-data.v1", "program": recipe["program"], "family": recipe["family"],
        "units": "m", "time_units": "s", "handedness": "right", "forward_axis": forward.tolist(), "up_axis": up.tolist(),
        "root_authority": "choose motor OR applied root motion, never both", "rig_roles": roles,
        "duration_s": plan["samples"][-1]["time_s"], "loop": plan.get("loop", True),
        "initial_contacts": {side: plan["samples"][0]["feet"][side]["contact"] for side in ("left", "right")},
        "events": sorted(event_track(plan) + plan.get("events", []), key=lambda e: e["time_s"]), "plan_sha256": digest(json_bytes(plan)),
        "world_interaction_authority": "runtime decides contact, damage, grip resistance and release",
        "unity_import_status": "NOT_VERIFIED", "transition_contract": plan.get("transition_contract"),
        "ground_plane": (contact_profile["geometry"]["ground"] if contact_profile else None),
        "animal": ({"id":animal["document"]["id"],"specimen":animal["document"]["specimen"],
            "uniform_geometry_scale":animal["uniform_scale"],"semantic_pelvis_to_toe_plane_m":height,
            "biological_validation":"NOT_VALIDATED"} if animal else None)}
    if articulation_profile is not None:
        state["articulation_profile"] = articulation_profile.receipt()
    payloads = {"root_motion.glb": root_raw, "in_place.glb": inplace_raw, "plan.json": json_bytes(plan),
        "solver-receipt.json": json_bytes(receipt), "runtime.json": json_bytes(state),
        "validation.json": json_bytes(validation), "inputs.lock.json": json_bytes(lock), "recipe.json": recipe_bytes}
    if articulation_profile is not None:
        payloads["articulation-profile.json"] = snapshots["articulation_profile"]
    if biomechanics is not None:
        payloads["animal.json"] = snapshots["animal"]
        payloads["biomechanics.json"] = json_bytes(biomechanics)
    manifest = {"schema": "eonwild.motion.factory-package.v1", "id": recipe["id"], "version": recipe["version"],
        "status": "CANDIDATE", "production_approved": False, "technical_status": validation["technical_status"],
        "files": {name: digest(data) for name, data in payloads.items()},
        "claims": {"physical": False, "scientific": False, "biological": False}}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".motion-stage-", dir=output.parent))
    try:
        for name, data in payloads.items():
            (stage / name).write_bytes(data)
        write_json(stage / "manifest.json", manifest)
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return manifest


def verify_package(path: Path) -> dict:
    manifest = read_json(path / "manifest.json")
    if manifest.get("schema") != "eonwild.motion.factory-package.v1":
        raise ContractError("unsupported package manifest")
    recipe = read_json(path / "recipe.json")
    required = {"root_motion.glb", "in_place.glb", "plan.json", "solver-receipt.json", "runtime.json", "validation.json", "inputs.lock.json", "recipe.json"}
    if "articulation_profile" in recipe:
        required.add("articulation-profile.json")
    if "animal" in recipe:
        required.update(("animal.json","biomechanics.json"))
    if set(manifest.get("files", {})) != required:
        raise ContractError("package inventory is incomplete or has unknown entries")
    for name, sha in manifest["files"].items():
        locked_file(path, {"path": name, "sha256": sha})
    validation = read_json(path / "validation.json")
    if manifest["technical_status"] != validation["technical_status"]:
        raise ContractError("manifest and validation disagree")
    lock = read_json(path / "inputs.lock.json")
    receipt = read_json(path / "solver-receipt.json")
    runtime = read_json(path / "runtime.json")
    if "articulation_profile" in recipe:
        if lock.get("inputs", {}).get("articulation_profile") != recipe["articulation_profile"]:
            raise ContractError("articulation profile binding is not preserved in the input lock")
        profile_bytes = (path / "articulation-profile.json").read_bytes()
        if digest(profile_bytes) != recipe["articulation_profile"]["sha256"]:
            raise ContractError("packaged articulation profile differs from its recipe binding")
        articulation_profile = load_articulation_profile(read_json(path / "articulation-profile.json"))
        summary = receipt.get("articulation_profile")
        checks = validation.get("articulation_envelopes")
        plan = read_json(path / "plan.json")
        repeated = {
            mode: emitted_articulation_envelopes(
                Glb.from_bytes((path / f"{mode}.glb").read_bytes()),
                semantic_roles=runtime.get("rig_roles"), plan=plan,
                profile=articulation_profile,
                forward_axis=runtime.get("forward_axis"), up_axis=runtime.get("up_axis"),
            )
            for mode in ("root_motion", "in_place")
        }
        if (not isinstance(summary, dict) or summary != articulation_profile.receipt()
                or runtime.get("articulation_profile") != summary
                or not isinstance(checks, dict) or set(checks) != {"root_motion", "in_place"}
                or any(check.get("profile") != summary for check in checks.values())
                or checks != repeated
                or receipt.get("final_emitted_articulation_gate") !=
                   ("PASS" if all(check.get("status") == "PASS" for check in checks.values()) else "FAIL")):
            raise ContractError("articulation profile provenance or final emitted gate is inconsistent")
        if any(check["status"] != "PASS" for check in repeated.values()) and validation["technical_status"] == "PASS":
            raise ContractError("technical status ignores a final articulation failure")
    elif any("articulation_profile" in item for item in (lock.get("inputs", {}), receipt, runtime)) or "articulation_envelopes" in validation:
        raise ContractError("unbound articulation profile metadata is not allowed")
    from .metadata import require_metadata
    require_metadata(path, manifest)
    return {"integrity": "PASS", "technical_status": validation["technical_status"],
            "visual_review": validation["visual_review"], "unity_parity": validation["unity_parity"], "production_approved": False}
