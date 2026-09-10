"""Candidate compiler from locked neutral geometry and versioned programs.

Generation, final mechanical evidence, perceptual review and Unity parity are
separate. This module never imports historical experiment builders or grants
production approval. Baked GLBs are outputs, not the reusable program itself.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import json
import math
from pathlib import Path
import platform
import shutil
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np

from ..contracts.v9_models import canonical_hash
from ..errors import ContractError
from ..glb.container import Glb
from ..glb.animation import read_animation_tracks
from ..layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from ..planning.airborne_gait import (
    AirborneGait,
    build_airborne_plan,
    load_airborne_choreography,
    load_airborne_gait,
)
from ..planning.grounded_gait import GroundedGait, build_grounded_plan, load_grounded_gait
from ..planning.parameters import gait_parameters
from ..solve.airborne_gait import solve_airborne_gait, evaluate_airborne_skin_with_authority
from ..solve.whole_body_gait_transition import _encode
from .io import confined, digest, frame_axes, json_bytes, locked_file, read_json, write_json
from .quality import (emitted_articulation_envelopes, emitted_rotation_rates,
                      emitted_cyclic_continuity, require_supported_geometry, solver_checks)
from .source import geometry_height
from .animal import (apply_uniform_geometry_scale,biomechanics_report,
    load_animal_instance,scaled_contact_profile,verify_source_calibration)
from ..solve.performance import load_performance, decorate_plan
from ..solve.gait_response import (
    assemble_baseline_performance,
    resolve_gait_response,
)
from ..solve.locomotion_regime_response import (
    airborne_response_receipt,
    decorate_airborne_response_plan,
    load_airborne_body_response_policy,
)
from ..planning.grounded_intent_resolution import (
    measure_grounded_touchdown_geometry,
    resolve_grounded_intent,
)
from ..solve.skin_targets import solve_with_skin_targets, evaluate_skin
from ..solve.support_anchors import CanonicalSupportAnchorProvider
from ..solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from ..solve.source_motion_query import SourceMotionQuery, _thaw
from ..solve.authored_material_contact import AuthoredMaterialContactAdapter
from ..solve.grounded_transition_clearance import (
    GroundedTransitionClearanceResolver,
    POLICY as GROUNDED_TRANSITION_CLEARANCE_POLICY,
    TARGET_GAP_M as GROUNDED_TRANSITION_TARGET_GAP_M,
)
from ..planning.supported_action import load_supported_action
from ..planning.gait_transition import load_gait_transition, build_transition_plan
from ..planning.articulation_profile import load_articulation_profile
from ..solve.supported_action import solve_supported_action
from ..solve.gaze import calibrate_rostral_direction
from .source_cubic import emit_source_cubics, serialized_key_midpoint_times
from .motion_set import (
    MotionSetResolution,
    reconstruct_motion_set,
    resolve_motion_set,
    resolve_motion_set_selection,
)
from .acquired_reference import packaged_reference, validate_clearance_policy
from .body_support import (
    BODY_SUPPORT_POLICY,
    BodySupportCompilation,
    body_support_payloads,
    coordinate_body_support,
)

SCHEMA = "eonwild.motion.factory-recipe.v1"
PROGRAMS = ("airborne_gait", "grounded_gait", "supported_action", "gait_transition")


def _airborne_gait_with_shared_articulation(
    gait: AirborneGait, articulation: Any
) -> AirborneGait:
    """Adapt closed solver scalars to one baseline-owned articulation profile."""
    if articulation is None:
        raise ContractError("v2 airborne locomotion requires shared articulation")
    phases = (articulation.support, articulation.swing)
    knee_min = min(phase["knee_interior_degrees"].hard_min_deg for phase in phases)
    knee_max = max(phase["knee_interior_degrees"].hard_max_deg for phase in phases)
    ankle_min = min(phase["ankle_interior_degrees"].hard_min_deg for phase in phases)
    ankle_max = max(phase["ankle_interior_degrees"].hard_max_deg for phase in phases)
    hip_min = min(phase["hip_sagittal_degrees"].hard_min_deg for phase in phases)
    hip_max = max(phase["hip_sagittal_degrees"].hard_max_deg for phase in phases)
    # AirborneGait's compatibility scalar is open at 180 while the authoritative
    # articulation profile admits the closed engineering endpoint. The profile
    # remains the final per-row authority; nextafter only represents it in the
    # older scalar contract.
    def open_max(value: float) -> float:
        return math.nextafter(180.0, -math.inf) if value == 180.0 else value
    return replace(
        gait,
        knee_min_interior_degrees=knee_min,
        knee_max_interior_degrees=open_max(knee_max),
        ankle_min_interior_degrees=ankle_min,
        ankle_max_interior_degrees=open_max(ankle_max),
        hip_extension_limit_degrees=max(1e-12, -hip_min),
        hip_flexion_limit_degrees=max(0.0, hip_max),
    )


def _measure_bound_grounded_touchdown_geometry(
    source: Glb,
    *,
    roles: dict,
    contact_profile: dict,
    locomotion_gait: GroundedGait,
    articulation_profile: Any,
    performance: Any,
    gait_response_policy: dict,
    source_geometry_sha256: str,
    body_height_m: float,
    up: np.ndarray,
    forward: np.ndarray,
) -> dict:
    """Measure the source-owned touchdown request used by v2 resolution."""
    provisional_performance, _ = resolve_gait_response(
        performance, locomotion_gait, gait_response_policy
    )
    provisional_performance = replace(
        provisional_performance,
        canonical_support_anchors=True,
        skin_refinement=True,
    )
    observation_plan = decorate_plan(
        build_grounded_plan(locomotion_gait, body_height_m),
        provisional_performance,
    )
    observation_solver_gait = AirborneGait(
        step_period_s=locomotion_gait.step_period_s,
        cycles=locomotion_gait.cycles,
        sample_hz=locomotion_gait.sample_hz,
        swing_hip_lift_degrees=locomotion_gait.swing_hip_lift_degrees,
    )
    observation_query = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=observation_solver_gait,
        locomotion_gait=locomotion_gait,
        plan=observation_plan,
        contact_profile=contact_profile,
        up_axis=tuple(up),
        forward_axis=tuple(forward),
        source_clip=None,
        legacy_overlay=False,
        articulation_profile=articulation_profile,
    )
    observations = {
        "source_geometry_sha256": source_geometry_sha256,
        "body_height_m": body_height_m,
        "gait_parameters_sha256": canonical_hash(
            gait_parameters(locomotion_gait)
        ),
        "sides": {
            "left": _thaw(
                observation_query.grounded_touchdown_observation(0.0, "left")
            ),
            "right": _thaw(
                observation_query.grounded_touchdown_observation(
                    locomotion_gait.step_period_s, "right"
                )
            ),
        },
    }
    return measure_grounded_touchdown_geometry(locomotion_gait, observations)


def _grounded_source_query_plan(
    source: Glb,
    *,
    gait: GroundedGait,
    body_height_m: float,
    performance: Any,
    roles: dict,
    contact_profile: dict,
    forward: Any,
    up: Any,
    solve_policy: dict,
) -> dict:
    """Rebuild the pre-emission plan that owns an acquired adapter binding."""
    result = decorate_plan(build_grounded_plan(gait, body_height_m), performance)
    result["gaze_calibration"] = calibrate_rostral_direction(
        source,
        roles=roles,
        contact_profile=contact_profile,
        forward_axis=forward,
        up_axis=up,
    )
    result["solve_policy"] = dict(solve_policy)
    validate_plan(result, "grounded_gait")
    return result


def _load_recipe_document(recipe: Any, root: Path) -> tuple[dict, dict[str, Path]]:
    required = {"schema", "id", "version", "family", "program", "source", "rig", "program_profile", "forward_axis", "up_axis"}
    if not isinstance(recipe, dict) or set(recipe) - required - {"animal", "contact_profile", "performance_profile", "gait_profile", "articulation_profile", "description", "supersedes", "authored_material_reference", "steady_motion"} or not required <= set(recipe):
        raise ContractError("recipe contains missing or unknown fields")
    if recipe["schema"] != SCHEMA or recipe["program"] not in PROGRAMS:
        raise ContractError("unsupported recipe schema or program")
    if "steady_motion" in recipe and recipe["program"] != "gait_transition":
        raise ContractError("steady motion is supported only by gait-transition recipes")
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
    if "authored_material_reference" in recipe:
        if recipe["program"] != "grounded_gait" and not (
            recipe["program"] == "gait_transition"
            and isinstance(recipe.get("steady_motion"), str)
        ):
            raise ContractError(
                "authored material reference is currently supported only for steady grounded gait"
            )
        paths["authored_material_reference"] = locked_file(
            root, recipe["authored_material_reference"]
        )
    return recipe, paths


def load_recipe(path: Path, root: Path) -> tuple[dict, dict[str, Path]]:
    return _load_recipe_document(read_json(path), root)


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


def _coordinate_selected_body_support(
    *,
    resolution: MotionSetResolution | None,
    snapshots: Mapping[str, bytes],
    query: SourceMotionQuery,
    law: CanonicalConstantSkinTargetLaw,
    plan: Mapping[str, Any],
    forward_axis: Sequence[float],
    up_axis: Sequence[float],
    unavailable_checkpoint: Path | None = None,
    recipe_bytes: bytes | None = None,
    engine_identity: Mapping[str, str] | None = None,
) -> BodySupportCompilation | None:
    """Route only the explicit shared body-support solve policy."""
    if resolution is None or "body_support_coordinator" not in resolution.solve_policy:
        return None
    if resolution.solve_policy["body_support_coordinator"] != BODY_SUPPORT_POLICY:
        raise ContractError("motion-set body-support coordinator policy is unsupported")
    if "rig" not in snapshots or "animal" not in snapshots:
        raise ContractError(
            "body-support coordination requires bound rig and animal snapshots"
        )
    compilation = coordinate_body_support(
        source_bytes=snapshots["source"],
        rig_bytes=snapshots["rig"],
        animal_bytes=snapshots["animal"],
        query=query,
        law=law,
        plan=plan,
        forward_axis=forward_axis,
        up_axis=up_axis,
    )
    if compilation.solution.status != "AVAILABLE":
        if unavailable_checkpoint is not None:
            if recipe_bytes is None or engine_identity is None:
                raise ContractError(
                    "body-support unavailable checkpoint lacks compiler provenance"
                )
            _write_body_support_unavailable_checkpoint(
                unavailable_checkpoint,
                compilation=compilation,
                recipe_bytes=recipe_bytes,
                snapshots=snapshots,
                engine_identity=engine_identity,
            )
        raise ContractError(
            "body-support coordination unavailable: " + str(compilation.solution.reason)
        )
    if compilation.law is None:
        raise ContractError("body-support coordination omitted its accepted final law")
    return compilation


def _write_body_support_unavailable_checkpoint(
    checkpoint: Path,
    *,
    compilation: BodySupportCompilation,
    recipe_bytes: bytes,
    snapshots: Mapping[str, bytes],
    engine_identity: Mapping[str, str],
) -> None:
    """Preserve a source-bound unavailable result before emission can begin."""
    payloads = body_support_payloads(compilation)
    manifest = {
        "schema": "eonwild.motion.body-support-unavailable-checkpoint.v1",
        "kind": "pre_emission_body_support_diagnostic",
        "status": "UNAVAILABLE",
        "technical_status": "BLOCKED",
        "production_approved": False,
        "recipe_sha256": digest(recipe_bytes),
        "inputs": {name: digest(raw) for name, raw in snapshots.items()},
        "engine_files": dict(engine_identity),
        "reason": compilation.solution.reason,
        "files": {name: digest(raw) for name, raw in payloads.items()},
    }
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=".body-support-unavailable-", dir=checkpoint.parent)
    )
    try:
        for name, raw in payloads.items():
            (stage / name).write_bytes(raw)
        write_json(stage / "manifest.json", manifest)
        stage.rename(checkpoint)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def compile_recipe(
    recipe_path: Path | None,
    *,
    root: Path,
    output: Path,
    interpolation: str = "LINEAR",
    emission_checkpoint: Path | None = None,
    _motion_set_resolution: MotionSetResolution | None = None,
) -> dict:
    if interpolation not in ("LINEAR", "CUBICSPLINE"):
        raise ContractError("emission interpolation must be LINEAR or CUBICSPLINE")
    cubic = interpolation == "CUBICSPLINE"
    if _motion_set_resolution is not None and not cubic:
        raise ContractError(
            "motion-set solve policy currently requires CUBICSPLINE output"
        )
    if emission_checkpoint is not None and not cubic:
        raise ContractError("emission checkpoint is only available for CUBICSPLINE")
    engine_identity = engine_fingerprint()
    if engine_identity != _ENGINE_AT_IMPORT:
        raise ContractError("engine sources changed since import; restart the compiler")
    root, output = root.resolve(), output.resolve()
    if _motion_set_resolution is None:
        if recipe_path is None:
            raise ContractError("legacy compilation requires a recipe path")
        recipe_path = recipe_path.resolve()
    checkpoint = (
        None if emission_checkpoint is None else emission_checkpoint.resolve()
    )
    if output.exists():
        raise ContractError("candidate output already exists; never overwrite an existing take")
    if checkpoint is not None and checkpoint.exists():
        raise ContractError("emission checkpoint already exists; never overwrite evidence")
    if _motion_set_resolution is None:
        assert recipe_path is not None
        recipe_bytes = recipe_path.read_bytes()
        recipe, paths = load_recipe(recipe_path, root)
        if json.loads(recipe_bytes) != recipe:
            raise ContractError("recipe changed during input resolution")
    else:
        recipe = reconstruct_motion_set(
            set_bytes=_motion_set_resolution.set_bytes,
            baseline_bytes=_motion_set_resolution.baseline_bytes,
            intent_bytes=_motion_set_resolution.intent_bytes,
            steady_intent_bytes=_motion_set_resolution.steady_intent_bytes,
            resolution_lock=_motion_set_resolution.lock,
        )
        if recipe != _motion_set_resolution.recipe:
            raise ContractError("motion-set resolution was mutated before compilation")
        recipe_bytes = json_bytes(recipe)
        recipe, paths = _load_recipe_document(recipe, root)
    if (
        "authored_material_reference" in recipe
        and _motion_set_resolution is None
    ):
        raise ContractError(
            "authored material reference requires compile-set provenance"
        )
    # Compile only from bytes whose hashes were checked, not later rereads.
    motion_set_v2 = (
        _motion_set_resolution is not None
        and json.loads(_motion_set_resolution.baseline_bytes).get("schema")
        == "eonwild.motion.motion-baseline.v2"
    )
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
        gait = (
            load_airborne_choreography(profile)
            if motion_set_v2 else load_airborne_gait(profile)
        )
        if motion_set_v2:
            gait = _airborne_gait_with_shared_articulation(
                gait, articulation_profile
            )
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
            gait = (
                load_airborne_choreography(locomotion)
                if motion_set_v2 else load_airborne_gait(locomotion)
            )
            if motion_set_v2:
                gait = _airborne_gait_with_shared_articulation(
                    gait, articulation_profile
                )
            locomotion_gait = gait
            plan = build_transition_plan(
                transition,
                gait,
                height,
                include_performance_gain_derivative=motion_set_v2,
            )
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
    baseline_performance_resolution = None
    acquired_binding = None
    grounded_touchdown_geometry = None
    grounded_intent_resolution = None
    if "performance_profile" in snapshots:
        if _motion_set_resolution is not None:
            performance, assembly_receipt = assemble_baseline_performance(
                json.loads(snapshots["performance_profile"]),
                json.loads(_motion_set_resolution.neutral_pose_bytes),
            )
            if (
                assembly_receipt["neutral_pose"]["source_geometry_sha256"]
                != recipe["source"]["sha256"]
            ):
                raise ContractError(
                    "neutral-pose calibration differs from baseline source geometry"
                )
            if motion_set_v2:
                response_policy = _motion_set_resolution.locomotion_response_policy
                assert response_policy is not None
                if isinstance(locomotion_gait, GroundedGait):
                    if animal is None:
                        raise ContractError(
                            "v2 grounded intent resolution requires a bound animal"
                        )
                    grounded_policy = response_policy["regimes"]["grounded"]
                    solve_policy = _motion_set_resolution.solve_policy
                    if (
                        solve_policy["canonical_support_anchors"] is not True
                        or solve_policy["skin_refinement"] is not True
                    ):
                        raise ContractError(
                            "v2 grounded geometry requires canonical refined solve policy"
                        )
                    grounded_touchdown_geometry = (
                        _measure_bound_grounded_touchdown_geometry(
                            source,
                            roles=roles,
                            contact_profile=contact_profile,
                            locomotion_gait=locomotion_gait,
                            articulation_profile=articulation_profile,
                            performance=performance,
                            gait_response_policy=grounded_policy[
                                "body_response"
                            ]["gait_response"],
                            source_geometry_sha256=recipe["source"]["sha256"],
                            body_height_m=height,
                            up=up,
                            forward=forward,
                        )
                    )
                    resolved = resolve_grounded_intent(
                        locomotion_gait,
                        body_height_m=height,
                        animal_hindlimb_length_m=animal["hindlimb_length_m"],
                        source_geometry_sha256=recipe["source"]["sha256"],
                        neutral_support_geometry=json.loads(
                            _motion_set_resolution.neutral_support_bytes
                        ),
                        family_policy=json.loads(
                            _motion_set_resolution.locomotion_response_bytes
                        ),
                        touchdown_geometry=grounded_touchdown_geometry,
                    )
                    locomotion_gait = resolved.gait
                    grounded_intent_resolution = resolved.receipt()
                    if transition is None:
                        plan = build_grounded_plan(locomotion_gait, height)
                    else:
                        plan = build_transition_plan(
                            transition, locomotion_gait, height
                        )
                    performance, gait_receipt = resolve_gait_response(
                        performance,
                        locomotion_gait,
                        grounded_policy["body_response"]["gait_response"],
                    )
                    airborne_policy = None
                elif isinstance(locomotion_gait, AirborneGait):
                    airborne_policy = response_policy["regimes"]["airborne"][
                        "body_response"
                    ]
                    gait_receipt = None
                else:
                    raise ContractError("v2 motion set has no locomotion gait")
            else:
                if not isinstance(locomotion_gait, GroundedGait):
                    raise ContractError(
                        "motion-set gait response requires grounded locomotion"
                    )
                performance, gait_receipt = resolve_gait_response(
                    performance,
                    locomotion_gait,
                    _motion_set_resolution.gait_response_policy,
                )
            solve_policy = _motion_set_resolution.solve_policy
            performance = replace(
                performance,
                canonical_support_anchors=solve_policy["canonical_support_anchors"],
                skin_refinement=solve_policy["skin_refinement"],
            )
            baseline_performance_resolution = {
                "assembly": assembly_receipt,
                **(
                    ({"airborne_body_response": None}
                     if isinstance(locomotion_gait, AirborneGait)
                     else {
                         "gait_response": gait_receipt,
                         "grounded_intent": grounded_intent_resolution,
                     })
                    if motion_set_v2
                    else {"gait_response": gait_receipt}
                ),
            }
        elif cubic:
            performance = load_performance(
                json.loads(snapshots["performance_profile"])
            )
            performance = replace(
                performance, canonical_support_anchors=True, skin_refinement=True
            )
        else:
            performance = load_performance(
                json.loads(snapshots["performance_profile"])
            )
        if motion_set_v2 and isinstance(locomotion_gait, AirborneGait):
            plan = decorate_airborne_response_plan(
                plan, performance, locomotion_gait, airborne_policy
            )
            baseline_performance_resolution["airborne_body_response"] = plan[
                "airborne_body_response"
            ]["resolution"]
        else:
            plan = decorate_plan(plan, performance)
        if "contact_profile" not in snapshots:
            raise ContractError("forward attention requires locked geometry calibration")
        plan["gaze_calibration"] = calibrate_rostral_direction(source, roles=roles,
            contact_profile=contact_profile, forward_axis=forward, up_axis=up)
    if _motion_set_resolution is not None:
        plan["solve_policy"] = dict(_motion_set_resolution.solve_policy)
    validate_plan(plan, recipe["program"])
    biomechanics = biomechanics_report(animal,plan,actual_semantic_height_m=height) if animal else None
    midpoint_plan = None
    body_support_compilation = None
    if supported:
        if cubic:
            raise ContractError("source CUBICSPLINE emission requires grounded locomotion")
        pass  # Already solved by the persistent-support program above.
    elif cubic:
        transition_steady_adapter = None
        transition_steady_query = None
        if (
            "performance_profile" not in snapshots
            or contact_profile is None
            or locomotion_gait is None
            or plan.get("performance", {}).get("canonical_support_anchors") is not True
        ):
            raise ContractError(
                "source CUBICSPLINE emission requires performance, contact, locomotion, and canonical anchors"
            )
        support_anchor_provider = CanonicalSupportAnchorProvider.build(
            source,
            semantic_roles=roles,
            solver_gait=gait,
            locomotion_gait=locomotion_gait,
            transition=transition,
            plan=plan,
            contact_profile=contact_profile,
            up_axis=tuple(up),
            forward_axis=tuple(forward),
            articulation_profile=articulation_profile,
        )
        query = SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=gait,
            locomotion_gait=locomotion_gait,
            transition=transition,
            plan=plan,
            contact_profile=contact_profile,
            up_axis=tuple(up),
            forward_axis=tuple(forward),
            source_clip=None,
            legacy_overlay=False,
            articulation_profile=articulation_profile,
        )
        if (
            _motion_set_resolution is not None
            and _motion_set_resolution.acquired_reference is not None
        ):
            reference = _motion_set_resolution.acquired_reference
            if _motion_set_resolution.authored_material_clearance_bytes is None:
                raise ContractError(
                    "authored material reference lacks baseline clearance policy"
                )
            descriptor = reference.descriptor
            source_query_plan = _grounded_source_query_plan(
                source,
                gait=locomotion_gait,
                body_height_m=height,
                performance=performance,
                roles=roles,
                contact_profile=contact_profile,
                forward=forward,
                up=up,
                solve_policy=dict(_motion_set_resolution.solve_policy),
            )
            if transition is None and source_query_plan != plan:
                raise ContractError(
                    "acquired reference source-query plan differs from baseline assembly"
                )
            steady_solver_gait = AirborneGait(
                step_period_s=locomotion_gait.step_period_s,
                cycles=locomotion_gait.cycles,
                sample_hz=locomotion_gait.sample_hz,
                swing_hip_lift_degrees=locomotion_gait.swing_hip_lift_degrees,
            )
            steady_query = (
                query
                if transition is None
                else SourceMotionQuery(
                    source,
                    semantic_roles=roles,
                    solver_gait=steady_solver_gait,
                    locomotion_gait=locomotion_gait,
                    transition=None,
                    plan=source_query_plan,
                    contact_profile=contact_profile,
                    up_axis=tuple(up),
                    forward_axis=tuple(forward),
                    source_clip=None,
                    legacy_overlay=False,
                    articulation_profile=articulation_profile,
                )
            )
            steady_adapter = AuthoredMaterialContactAdapter.build(
                steady_query,
                json.loads(reference.capsule_bytes),
                authored_source=reference.source_bytes,
                retime_policy=descriptor["adapter"]["retime_policy"],
                body_height_m=height,
                material_clearance_policy=json.loads(
                    _motion_set_resolution.authored_material_clearance_bytes
                ),
            )
            transition_steady_adapter = steady_adapter
            transition_steady_query = SourceMotionQuery(
                source,
                semantic_roles=roles,
                solver_gait=steady_solver_gait,
                locomotion_gait=locomotion_gait,
                transition=None,
                plan=source_query_plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                source_clip=None,
                legacy_overlay=False,
                articulation_profile=articulation_profile,
                authored_material_contact=steady_adapter,
            )
            adapter = steady_adapter if transition is None else None
            if adapter is not None:
                query = SourceMotionQuery(
                    source,
                    semantic_roles=roles,
                    solver_gait=gait,
                    locomotion_gait=locomotion_gait,
                    transition=transition,
                    plan=plan,
                    contact_profile=contact_profile,
                    up_axis=tuple(up),
                    forward_axis=tuple(forward),
                    source_clip=None,
                    legacy_overlay=False,
                    articulation_profile=articulation_profile,
                    authored_material_contact=adapter,
                )
                acquired_binding = {
                    **reference.binding,
                    "adapter": _thaw(adapter.binding()),
                }
        law = CanonicalConstantSkinTargetLaw.build(
            query,
            support_anchor_provider,
            source=source,
            semantic_roles=roles,
            solver_gait=gait,
            locomotion_gait=locomotion_gait,
            transition=transition,
            plan=plan,
            contact_profile=contact_profile,
            up_axis=tuple(up),
            forward_axis=tuple(forward),
            articulation_profile=articulation_profile,
            law_id=(
                _motion_set_resolution.solve_policy["skin_target_law"]
                if _motion_set_resolution is not None
                else "canonical_constant_skin_targets.v1"
            ),
        )
        transition_clearance = None
        if transition is not None and (
            _motion_set_resolution is not None
            and _motion_set_resolution.solve_policy.get("grounded_transition_clearance")
            == GROUNDED_TRANSITION_CLEARANCE_POLICY
        ):
            transition_clearance = GroundedTransitionClearanceResolver.build(
                law, locomotion_gait
            )
            query = SourceMotionQuery(
                source,
                semantic_roles=roles,
                solver_gait=gait,
                locomotion_gait=locomotion_gait,
                transition=transition,
                plan=plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                source_clip=None,
                legacy_overlay=False,
                articulation_profile=articulation_profile,
                transition_clearance=transition_clearance,
            )
            if transition_steady_adapter is not None:
                adapter = AuthoredMaterialContactAdapter.for_transition(
                    transition_steady_adapter,
                    steady_query=transition_steady_query,
                    transition_query=query,
                )
                query = SourceMotionQuery(
                    source,
                    semantic_roles=roles,
                    solver_gait=gait,
                    locomotion_gait=locomotion_gait,
                    transition=transition,
                    plan=plan,
                    contact_profile=contact_profile,
                    up_axis=tuple(up),
                    forward_axis=tuple(forward),
                    source_clip=None,
                    legacy_overlay=False,
                    articulation_profile=articulation_profile,
                    transition_clearance=transition_clearance,
                    authored_material_contact=adapter,
                )
                acquired_binding = {
                    **reference.binding,
                    "adapter": _thaw(adapter.binding()),
                }
            law = CanonicalConstantSkinTargetLaw.build(
                query,
                support_anchor_provider,
                source=source,
                semantic_roles=roles,
                solver_gait=gait,
                locomotion_gait=locomotion_gait,
                transition=transition,
                plan=plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                articulation_profile=articulation_profile,
                law_id=(
                    _motion_set_resolution.solve_policy["skin_target_law"]
                    if _motion_set_resolution is not None
                    else "canonical_constant_skin_targets.v1"
                ),
            )
        body_support_compilation = _coordinate_selected_body_support(
            resolution=_motion_set_resolution,
            snapshots=snapshots,
            query=query,
            law=law,
            plan=plan,
            forward_axis=forward,
            up_axis=up,
            unavailable_checkpoint=checkpoint,
            recipe_bytes=recipe_bytes,
            engine_identity=engine_identity,
        )
        if body_support_compilation is not None:
            law = body_support_compilation.law
        emission = emit_source_cubics(
            source, law, plan, root_node=source.name_to_node[roles["root"]]
        )
        # A checked source law can touch a hard articulation boundary while a
        # Hermite interval between its valid keys overshoots it. Iteratively
        # insert only source-derived failing midpoints, reusing all checked
        # source values. Candidates whose first serialized curve passes retain
        # their exact animation bytes.
        refinement_times: set[float] = set()
        refinement_attempts = []
        refinement_stop = "NOT_APPLICABLE"
        while articulation_profile is not None:
            attempt_checks = {}
            next_times: set[float] = set()
            check_plan = _thaw(emission.midpoint_plan)
            for mode, raw, clip in (
                ("root_motion", emission.root_motion, "V9_SOURCE_CUBIC_ROOT_MOTION"),
                ("in_place", emission.in_place, "V9_SOURCE_CUBIC_IN_PLACE"),
            ):
                emitted = Glb.from_bytes(raw)
                sample_times = serialized_key_midpoint_times(emitted, clip)
                check = emitted_articulation_envelopes(
                    emitted,
                    semantic_roles=roles,
                    plan=check_plan,
                    profile=articulation_profile,
                    forward_axis=forward,
                    up_axis=up,
                    sample_times=sample_times,
                )
                attempt_checks[mode] = check
                witness = check.get("witness")
                if check["status"] == "FAIL" and witness is not None:
                    next_times.add(float(witness["time_s"]))
            refinement_attempts.append({
                "inserted_key_count": len(refinement_times),
                "midpoint_articulation": attempt_checks,
            })
            if all(check["status"] == "PASS" for check in attempt_checks.values()):
                refinement_stop = "PASS"
                break
            eligible = sorted(next_times - refinement_times)
            remaining = 8 - len(refinement_times)
            if not eligible:
                refinement_stop = "NO_ELIGIBLE_SOURCE_MIDPOINT"
                break
            if remaining <= 0:
                refinement_stop = "INSERTION_BUDGET_EXHAUSTED"
                break
            refinement_times.update(eligible[:remaining])
            emission = emit_source_cubics(
                source,
                law,
                plan,
                root_node=source.name_to_node[roles["root"]],
                additional_key_times=tuple(sorted(refinement_times)),
                reuse=emission,
            )
        plan = _thaw(emission.plan)
        midpoint_plan = _thaw(emission.midpoint_plan)
        # Reuse the existing receipt construction against the identical
        # constant-offset key rows. The returned LINEAR bytes are discarded.
        _, _, _, receipt = solve_airborne_gait(
            source,
            source_clip=None,
            semantic_roles=roles,
            gait=gait,
            up_axis=tuple(up),
            forward_axis=tuple(forward),
            plan_override=plan,
            legacy_overlay=False,
            articulation_profile=articulation_profile,
        )
        receipt["source_cubic_tangent_estimate"] = _thaw(
            emission.tangent_estimate
        )
        receipt["source_cubic_key_refinement"] = {
            "classification": (
                "bounded iterative insertion of source-derived failing midpoint keys; "
                "no clipped rotations or relaxed limits"
            ),
            "maximum_inserted_keys": 8,
            "inserted_times_s": sorted(refinement_times),
            "stop_reason": refinement_stop,
            "attempts": refinement_attempts,
        }
        if law.receipt()["law_id"] == "canonical_constant_skin_targets.v1":
            # Preserve the accepted v1 receipt byte-for-byte.  The richer
            # binding receipt belongs only to newly selected laws.
            receipt["constant_skin_target_law"] = {
                "status": "AVAILABLE_AT_ALL_KEYS_STENCILS_AND_MIDPOINTS",
                "classification": (
                    "pointwise checked values; derivative and global-C1 authority unavailable"
                ),
            }
        else:
            receipt["constant_skin_target_law"] = {
                "status": "AVAILABLE_AT_ALL_KEYS_STENCILS_AND_MIDPOINTS",
                **law.receipt(),
            }
        if body_support_compilation is not None:
            receipt["body_support_coordination"] = dict(
                body_support_compilation.receipt
            )
        if transition_clearance is not None:
            receipt["grounded_transition_clearance"] = {
                "policy": GROUNDED_TRANSITION_CLEARANCE_POLICY,
                "target_gap_m": GROUNDED_TRANSITION_TARGET_GAP_M,
                "geometry_pose_solve_count": transition_clearance.solve_count,
                "classification": (
                    "pointwise geometry-derived material floor; sampled monotonicity "
                    "checks do not claim global branch authority"
                ),
            }
        root_raw, inplace_raw = emission.root_motion, emission.in_place
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
            canonical_support_anchor_provider=support_anchor_provider,
            canonical_locomotion_gait=locomotion_gait,
            canonical_transition=transition)
    else:
        root_raw, inplace_raw, _, receipt = solve_airborne_gait(source, source_clip=None,
            semantic_roles=roles, gait=gait, up_axis=tuple(up), forward_axis=tuple(forward),
            plan_override=plan, legacy_overlay=False, articulation_profile=articulation_profile)
    root_raw, inplace_raw = (tag_output(raw, recipe, plan, mode) for raw, mode in ((root_raw, "root_motion"), (inplace_raw, "in_place")))
    outputs = {"root_motion": Glb.from_bytes(root_raw), "in_place": Glb.from_bytes(inplace_raw)}
    if checkpoint is not None:
        assert cubic and midpoint_plan is not None
        # Keep the pre-gate bytes directly consumable by the native-time review
        # tool.  This is a diagnostic sidecar built from the same in-memory
        # plan, normalized frame, semantic roles and scaled contact plane that
        # produced the checkpoint GLBs; it is not a technical result.
        checkpoint_runtime = {
            "schema": "eonwild.motion.runtime-data.v1",
            "program": recipe["program"],
            "family": recipe["family"],
            "units": "m",
            "time_units": "s",
            "handedness": "right",
            "forward_axis": forward.tolist(),
            "up_axis": up.tolist(),
            "root_authority": "choose motor OR applied root motion, never both",
            "rig_roles": roles,
            "duration_s": plan["samples"][-1]["time_s"],
            "loop": plan.get("loop", True),
            "initial_contacts": {
                side: plan["samples"][0]["feet"][side]["contact"]
                for side in ("left", "right")
            },
            "events": sorted(
                event_track(plan) + plan.get("events", []),
                key=lambda event: event["time_s"],
            ),
            "plan_sha256": digest(json_bytes(plan)),
            "world_interaction_authority": (
                "runtime decides contact, damage, grip resistance and release"
            ),
            "unity_import_status": "NOT_VERIFIED",
            "transition_contract": plan.get("transition_contract"),
            "ground_plane": contact_profile["geometry"]["ground"],
            "animal": (
                {
                    "id": animal["document"]["id"],
                    "specimen": animal["document"]["specimen"],
                    "uniform_geometry_scale": animal["uniform_scale"],
                    "semantic_pelvis_to_toe_plane_m": height,
                    "biological_validation": "NOT_VALIDATED",
                }
                if animal
                else None
            ),
            "body_height_m": height,
            "interpolation": interpolation,
            "diagnostic_scope": (
                "pre-gate source-derived CUBICSPLINE emission; native-time "
                "review metadata only"
            ),
            "technical_status": "NOT_EVALUATED",
            "production_approved": False,
        }
        checkpoint_payloads = {
            "root_motion.glb": root_raw,
            "in_place.glb": inplace_raw,
            "plan.json": json_bytes(plan),
            "cubic-midpoint-plan.json": json_bytes(midpoint_plan),
            "tangent-estimate.json": json_bytes(
                receipt["source_cubic_tangent_estimate"]
            ),
            "runtime.json": json_bytes(checkpoint_runtime),
        }
        if body_support_compilation is not None:
            checkpoint_runtime["body_support_coordination"] = {
                "policy_id": BODY_SUPPORT_POLICY,
                "status": body_support_compilation.solution.status,
                "final_law_binding_sha256": body_support_compilation.receipt[
                    "accepted_binding"
                ]["final_law_binding_sha256"],
                "frozen_anchor_sha256": body_support_compilation.receipt[
                    "frozen_anchor_sha256"
                ],
                "emitted_full_mesh_floor": "NOT_RUN",
                "serialized_dynamics_parity": "NOT_RUN",
            }
            checkpoint_payloads["runtime.json"] = json_bytes(checkpoint_runtime)
            checkpoint_payloads.update(
                body_support_payloads(body_support_compilation)
            )
        checkpoint_manifest = {
            "schema": "eonwild.motion.source-cubic-emission-checkpoint.v1",
            "kind": "pre_gate_source_cubic_diagnostic",
            "classification": "pre-gate emitted bytes for reproducible diagnostics; not a candidate acceptance result",
            "status": "DIAGNOSTIC",
            "technical_status": "NOT_EVALUATED",
            "visual_review": "PENDING",
            "unity_parity": "NOT_RUN",
            "production_approved": False,
            "claims": {"physical": False, "scientific": False, "biological": False},
            "recipe_sha256": digest(recipe_bytes),
            "inputs": {name: digest(raw) for name, raw in snapshots.items()},
            "engine_files": engine_identity,
            "files": {
                name: digest(raw) for name, raw in checkpoint_payloads.items()
            },
        }
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_stage = Path(
            tempfile.mkdtemp(prefix=".source-cubic-checkpoint-", dir=checkpoint.parent)
        )
        try:
            for name, raw in checkpoint_payloads.items():
                (checkpoint_stage / name).write_bytes(raw)
            write_json(checkpoint_stage / "manifest.json", checkpoint_manifest)
            checkpoint_stage.rename(checkpoint)
        except BaseException:
            shutil.rmtree(checkpoint_stage, ignore_errors=True)
            raise
    cubic_sample_times = None
    if cubic:
        cubic_sample_times = serialized_key_midpoint_times(
            outputs["root_motion"], recipe["id"] + ".root_motion"
        )
    evaluated = {mode: evaluate_emitted(glb, source, roles, plan, forward, in_place=(mode == "in_place")) for mode, glb in outputs.items()}
    rates = {mode: emitted_rotation_rates(glb, gait.max_joint_angular_velocity_degrees_per_s) for mode, glb in outputs.items()}
    continuity = {mode: emitted_cyclic_continuity(glb, loop=plan.get("loop", True)) for mode, glb in outputs.items()}
    articulation = None
    midpoint_articulation = None
    if articulation_profile is not None:
        articulation = {
            mode: emitted_articulation_envelopes(
                glb, semantic_roles=roles, plan=plan,
                profile=articulation_profile, forward_axis=forward, up_axis=up,
            )
            for mode, glb in outputs.items()
        }
        if cubic:
            assert midpoint_plan is not None
            assert cubic_sample_times is not None
            midpoint_articulation = {
                mode: emitted_articulation_envelopes(
                    glb, semantic_roles=roles, plan=midpoint_plan,
                    profile=articulation_profile, forward_axis=forward,
                    up_axis=up, sample_times=cubic_sample_times,
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
    midpoint_surface = None
    midpoint_in_place_surface = None
    if cubic and contact_profile is not None:
        assert midpoint_plan is not None
        assert cubic_sample_times is not None
        midpoint_surface = evaluate_skin(
            outputs["root_motion"], contact_profile, midpoint_plan,
            sample_times=cubic_sample_times,
        )
        origin_travel = midpoint_plan["samples"][0]["root_forward_m"]
        midpoint_offsets = [
            forward * (row["root_forward_m"] - origin_travel)
            for row in midpoint_plan["samples"]
        ]
        midpoint_in_place_surface = evaluate_skin(
            outputs["in_place"], contact_profile, midpoint_plan,
            world_offsets=midpoint_offsets, sample_times=cubic_sample_times,
        )
    receipt["final_skinned_contact_gate"] = "PASS" if surface["verdict"] == in_place_surface["verdict"] == "PASS" else "FAIL"
    receipt["final_skinned_contact_scope"] = "both reopened serialized exports; in-place plus planned motor travel; locked floor and full skin influences"
    refinement_ok = receipt.get("skin_target_refinement", {}).get("converged", True) and receipt.get("oral_contact", {"status":"PASS"})["status"] == "PASS"
    articulation_ok = (
        articulation is None
        or (
            all(row["status"] == "PASS" for row in articulation.values())
            and (
                midpoint_articulation is None
                or all(row["status"] == "PASS" for row in midpoint_articulation.values())
            )
        )
    )
    midpoint_ok = (
        midpoint_surface is None
        or (
            midpoint_surface["verdict"] == "PASS"
            and midpoint_in_place_surface is not None
            and midpoint_in_place_surface["verdict"] == "PASS"
        )
    )
    body_support_emitted_ok = body_support_compilation is None
    technical = (refinement_ok and articulation_ok and all(row["status"] == "PASS" for row in evaluated.values()) and
                 all(row["status"] == "PASS" for row in rates.values()) and
                 all(row["status"] in ("PASS", "NOT_APPLICABLE") for row in continuity.values()) and feasibility["status"] == "PASS" and surface["verdict"] == "PASS" and in_place_surface["verdict"] == "PASS" and midpoint_ok and body_support_emitted_ok)
    validation = {"schema": "eonwild.motion.factory-validation.v1", "technical_status": "PASS" if technical else "BLOCKED",
        "outputs": evaluated, "rotation_rates": rates, "cyclic_continuity": continuity, "solver_feasibility": feasibility, "skinned_contact": surface, "in_place_skinned_contact": in_place_surface,
        "oral_contact": receipt.get("oral_contact"),
        "visual_review": "PENDING", "unity_parity": "NOT_RUN", "production_approved": False}
    if cubic:
        validation["cubic_midpoint_skinned_contact"] = {
            "root_motion": midpoint_surface,
            "in_place": midpoint_in_place_surface,
        }
        validation["cubic_midpoint_articulation_envelopes"] = midpoint_articulation
    if body_support_compilation is not None:
        validation["body_support_coordination"] = {
            "source_sampled_dynamics": body_support_compilation.receipt[
                "source_sampled_dynamics"
            ],
            "source_sampled_final_geometry": body_support_compilation.receipt[
                "source_sampled_final_geometry"
            ],
            "emitted_full_mesh_floor": "NOT_RUN",
            "serialized_dynamics_parity": "NOT_RUN",
            "status": "BLOCKED_PENDING_EMITTED_MEASUREMENT",
        }
    if articulation is not None:
        validation["articulation_envelopes"] = articulation
        receipt["final_emitted_articulation_gate"] = "PASS" if articulation_ok else "FAIL"
        receipt["final_emitted_articulation_scope"] = "both reopened serialized exports"
    if engine_fingerprint() != engine_identity:
        raise ContractError("engine sources changed during compilation; no candidate published")
    lock = {"schema": "eonwild.motion.factory-lock.v1", "recipe_sha256": digest(recipe_bytes),
            "inputs": {name: recipe[name] for name in paths}, "engine_files": engine_identity,
            "tools": {"python": platform.python_version(), "numpy": np.__version__}}
    if _motion_set_resolution is not None:
        lock["motion_set_resolution"] = _motion_set_resolution.lock
    if cubic:
        lock["emission"] = {"interpolation": interpolation,
                            "source_tangent_stencil_s": .001,
                            "convergence_stencil_s": .0005}
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
    if cubic:
        state["interpolation"] = interpolation
    if _motion_set_resolution is not None:
        state["motion_set"] = _motion_set_resolution.lock["identities"]
        state["solve_policy"] = dict(_motion_set_resolution.solve_policy)
        receipt["solve_policy"] = dict(_motion_set_resolution.solve_policy)
        receipt["baseline_performance_resolution"] = (
            baseline_performance_resolution
        )
        if acquired_binding is not None:
            state["authored_material_reference"] = acquired_binding
            receipt["authored_material_reference"] = acquired_binding
        if body_support_compilation is not None:
            state["body_support_coordination"] = {
                "policy_id": BODY_SUPPORT_POLICY,
                "status": body_support_compilation.solution.status,
                "source_sampled_dynamics": body_support_compilation.receipt[
                    "source_sampled_dynamics"
                ],
                "serialized_dynamics_parity": "NOT_RUN",
            }
    if articulation_profile is not None:
        state["articulation_profile"] = articulation_profile.receipt()
    payloads = {"root_motion.glb": root_raw, "in_place.glb": inplace_raw, "plan.json": json_bytes(plan),
        "solver-receipt.json": json_bytes(receipt), "runtime.json": json_bytes(state),
        "validation.json": json_bytes(validation), "inputs.lock.json": json_bytes(lock), "recipe.json": recipe_bytes}
    if cubic:
        assert midpoint_plan is not None
        payloads["cubic-midpoint-plan.json"] = json_bytes(midpoint_plan)
    if articulation_profile is not None:
        payloads["articulation-profile.json"] = snapshots["articulation_profile"]
    if biomechanics is not None:
        payloads["animal.json"] = snapshots["animal"]
        payloads["biomechanics.json"] = json_bytes(biomechanics)
    if body_support_compilation is not None:
        payloads.update(body_support_payloads(body_support_compilation))
    if _motion_set_resolution is not None:
        payloads.update(_motion_set_resolution.payloads)
        payloads["performance-profile.json"] = snapshots["performance_profile"]
        payloads["neutral-pose-profile.json"] = (
            _motion_set_resolution.neutral_pose_bytes
        )
        if motion_set_v2:
            # Verification replays source-owned v2 resolution from immutable
            # package inputs. A hash of derived coordinates is not authority.
            payloads["source.glb"] = snapshots["source"]
            payloads["rig.json"] = snapshots["rig"]
            payloads["contact-profile.json"] = snapshots["contact_profile"]
        if grounded_touchdown_geometry is not None:
            payloads["grounded-touchdown-geometry.json"] = json_bytes(
                grounded_touchdown_geometry
            )
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


def compile_motion_set(
    motion_set_path: Path,
    motion: str,
    *,
    root: Path,
    output: Path,
    interpolation: str = "CUBICSPLINE",
    emission_checkpoint: Path | None = None,
) -> dict:
    """Compile one selected motion through its single shared baseline."""
    resolution = resolve_motion_set(root, motion_set_path, motion)
    return compile_recipe(
        None,
        root=root,
        output=output,
        interpolation=interpolation,
        emission_checkpoint=emission_checkpoint,
        _motion_set_resolution=resolution,
    )


def compile_motion_set_selection(
    motion_set_path: Path,
    motions: list[str],
    *,
    root: Path,
    output: Path,
    interpolation: str = "CUBICSPLINE",
) -> dict[str, dict]:
    """Compile selected intents from one immutable set/baseline resolution."""
    if interpolation != "CUBICSPLINE":
        raise ContractError(
            "motion-set solve policy currently requires CUBICSPLINE output"
        )
    output = output.resolve()
    if output.exists():
        raise ContractError("motion-set output already exists; never overwrite")
    resolutions = resolve_motion_set_selection(root, motion_set_path, motions)
    destinations = {
        resolution.motion: confined(output, resolution.motion)
        for resolution in resolutions
    }
    output.mkdir(parents=True)
    results = {}
    for resolution in resolutions:
        package = destinations[resolution.motion]
        results[resolution.motion] = compile_recipe(
            None,
            root=root,
            output=package,
            interpolation=interpolation,
            _motion_set_resolution=resolution,
        )
    return results


def _serialized_interpolation(glb: Glb) -> str:
    animations = glb.document.get("animations")
    if (
        not isinstance(animations, list)
        or len(animations) != 1
        or not isinstance(animations[0].get("name"), str)
    ):
        raise ContractError("package interpolation requires one named animation")
    tracks, _ = read_animation_tracks(
        glb, animations[0]["name"], require_common_timeline=True
    )
    modes = {track.interpolation for track in tracks.values()}
    if len(modes) != 1:
        raise ContractError("package mixes serialized interpolation modes")
    return modes.pop()


def _midpoint_contact_verdict(result: Any, *, sample_count: int) -> str:
    expected = {
        "verdict", "authority", "maximum_penetration_m",
        "maximum_stance_gap_m", "ground_level_m", "sample_count",
        "classification",
    }
    if not isinstance(result, dict) or set(result) != expected:
        raise ContractError("CUBICSPLINE midpoint contact result shape is invalid")
    verdict = result.get("verdict")
    if verdict not in {"PASS", "FAIL"}:
        raise ContractError("CUBICSPLINE midpoint contact verdict is invalid")
    if type(result.get("sample_count")) is not int or result["sample_count"] != sample_count:
        raise ContractError("CUBICSPLINE midpoint contact sample count is invalid")
    for field in (
        "maximum_penetration_m", "maximum_stance_gap_m", "ground_level_m"
    ):
        value = result.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ContractError("CUBICSPLINE midpoint contact scalar is invalid")
    if result["maximum_penetration_m"] < 0:
        raise ContractError("CUBICSPLINE midpoint penetration is invalid")
    if result.get("classification") != (
        "final serialized skin, fixed floor, full multi-influence weights, "
        "unchanged engineering thresholds"
    ):
        raise ContractError("CUBICSPLINE midpoint contact classification is invalid")
    authority = result.get("authority")
    per_foot = authority.get("per_foot") if isinstance(authority, dict) else None
    if (
        not isinstance(authority, dict)
        or set(authority) != {"per_foot"}
        or not isinstance(per_foot, dict)
        or set(per_foot) != {"left", "right"}
        or any(
            not isinstance(foot, dict)
            or foot.get("verdict") not in {"PASS", "FAIL"}
            for foot in per_foot.values()
        )
    ):
        raise ContractError("CUBICSPLINE midpoint contact authority is invalid")
    if verdict == "PASS" and any(
        foot["verdict"] != "PASS" for foot in per_foot.values()
    ):
        raise ContractError("CUBICSPLINE midpoint contact verdict is inconsistent")
    return verdict


def _verify_motion_set_provenance(
    path: Path,
    *,
    recipe: dict,
    lock: dict,
    runtime: dict,
    receipt: dict,
    plan: dict,
) -> None:
    resolution_lock = lock.get("motion_set_resolution")
    reconstructed = reconstruct_motion_set(
        set_bytes=(path / "motion-set.json").read_bytes(),
        baseline_bytes=(path / "motion-baseline.json").read_bytes(),
        intent_bytes=(path / "motion-intent.json").read_bytes(),
        steady_intent_bytes=(
            (path / "steady-motion-intent.json").read_bytes()
            if (path / "steady-motion-intent.json").exists()
            else None
        ),
        resolution_lock=resolution_lock,
    )
    if reconstructed != recipe:
        raise ContractError("motion set snapshots do not reconstruct recipe")
    baseline = read_json(path / "motion-baseline.json")
    baseline_v2 = baseline.get("schema") == "eonwild.motion.motion-baseline.v2"
    solve_policy = baseline["solve_policy"]
    style_bytes = (path / "performance-profile.json").read_bytes()
    neutral_bytes = (path / "neutral-pose-profile.json").read_bytes()
    if (
        digest(style_bytes) != baseline["performance_profile"]["sha256"]
        or digest(neutral_bytes) != baseline["neutral_pose_profile"]["sha256"]
    ):
        raise ContractError("motion baseline profile snapshots differ")
    performance, assembly_receipt = assemble_baseline_performance(
        json.loads(style_bytes), json.loads(neutral_bytes)
    )
    if (
        assembly_receipt["neutral_pose"]["source_geometry_sha256"]
        != recipe["source"]["sha256"]
    ):
        raise ContractError("motion baseline neutral calibration source differs")
    intent = read_json(path / "motion-intent.json")
    grounded_response = baseline.get("locomotion_response_policy", {}).get(
        "regimes", {}
    ).get("grounded", {})
    has_clearance_policy = "authored_material_clearance" in grounded_response
    clearance_path = path / "authored-material-clearance-policy.json"
    if has_clearance_policy:
        clearance_bytes = clearance_path.read_bytes()
        validate_clearance_policy(json.loads(clearance_bytes))
        if (
            digest(clearance_bytes)
            != grounded_response["authored_material_clearance"]["sha256"]
            or resolution_lock.get("authored_material_clearance_policy_sha256")
            != digest(clearance_bytes)
        ):
            raise ContractError("authored material clearance policy provenance differs")
    elif (
        clearance_path.exists()
        or "authored_material_clearance_policy_sha256" in resolution_lock
    ):
        raise ContractError("unbound authored material clearance policy is not allowed")
    reference_intent = intent
    if "steady_motion" in intent:
        reference_intent = read_json(path / "steady-motion-intent.json")
    if "authored_material_reference" in recipe:
        reference = packaged_reference(path)
        if not has_clearance_policy:
            raise ContractError("authored material reference lacks clearance policy")
        reference_binding = reference.binding
        if (
            digest(reference.descriptor_bytes)
            != reference_intent["authored_material_reference"]["sha256"]
            or resolution_lock.get("authored_material_reference")
            != reference_binding
        ):
            raise ContractError("authored material reference provenance differs")
        declared = reference.descriptor
        if (
            digest(reference.source_bytes) != declared["source"]["sha256"]
            or digest(reference.capsule_bytes) != declared["capsule"]["sha256"]
        ):
            raise ContractError("authored material reference payload differs")
        runtime_reference = runtime.get("authored_material_reference")
        receipt_reference = receipt.get("authored_material_reference")
        if (
            not isinstance(runtime_reference, dict)
            or runtime_reference != receipt_reference
            or {key: runtime_reference[key] for key in reference_binding}
            != reference_binding
        ):
            raise ContractError("authored material adapter binding is inconsistent")
    elif (
        "authored_material_reference" in resolution_lock
        or "authored_material_reference" in runtime
        or "authored_material_reference" in receipt
    ):
        raise ContractError("unbound authored material reference is not allowed")
    program_bytes = (path / "program-profile.json").read_bytes()
    if digest(program_bytes) != intent["program_profile"]["sha256"]:
        raise ContractError("motion intent program snapshot differs")
    if recipe["program"] == "grounded_gait":
        if (path / "gait-profile.json").exists():
            raise ContractError("grounded intent contains a transition gait snapshot")
        gait = load_grounded_gait(json.loads(program_bytes))
        transition = None
    elif recipe["program"] == "gait_transition":
        transition = load_gait_transition(json.loads(program_bytes))
        gait_bytes = (path / "gait-profile.json").read_bytes()
        if digest(gait_bytes) != intent["gait_profile"]["sha256"]:
            raise ContractError("motion intent gait snapshot differs")
        gait_document = json.loads(gait_bytes)
        gait = (
            load_airborne_choreography(gait_document)
            if baseline_v2
            and gait_document.get("schema")
            == "eonwild.motion.airborne-choreography.v1"
            else load_grounded_gait(gait_document)
        )
        if baseline_v2 and isinstance(gait, AirborneGait):
            gait = _airborne_gait_with_shared_articulation(
                gait,
                load_articulation_profile(
                    read_json(path / "articulation-profile.json")
                ),
            )
    elif recipe["program"] == "airborne_gait" and baseline_v2:
        if (path / "gait-profile.json").exists():
            raise ContractError("airborne intent contains a transition gait snapshot")
        gait = load_airborne_choreography(json.loads(program_bytes))
        gait = _airborne_gait_with_shared_articulation(
            gait,
            load_articulation_profile(read_json(path / "articulation-profile.json")),
        )
        transition = None
    else:
        raise ContractError("motion set contains an unsupported program")
    response_policy = baseline.get("locomotion_response_policy")
    if baseline_v2:
        if not isinstance(response_policy, dict):
            raise ContractError("v2 motion baseline response policy is missing")
        grounded_policy = response_policy["regimes"]["grounded"]
        policy_bytes = (path / "locomotion-response-policy.json").read_bytes()
        support_bytes = (path / "neutral-support-profile.json").read_bytes()
        if (
            digest(policy_bytes) != grounded_policy["intent_resolution"]["sha256"]
            or digest(support_bytes)
            != grounded_policy["neutral_support_profile"]["sha256"]
        ):
            raise ContractError("v2 motion response snapshots differ from baseline")
        if isinstance(gait, GroundedGait):
            geometry_path = path / "grounded-touchdown-geometry.json"
            if not geometry_path.exists():
                raise ContractError("v2 grounded package lacks touchdown geometry evidence")
            source_bytes = (path / "source.glb").read_bytes()
            rig_bytes = (path / "rig.json").read_bytes()
            contact_bytes = (path / "contact-profile.json").read_bytes()
            animal_bytes = (path / "animal.json").read_bytes()
            articulation_bytes = (path / "articulation-profile.json").read_bytes()
            if (
                digest(source_bytes) != recipe["source"]["sha256"]
                or digest(rig_bytes) != recipe["rig"]["sha256"]
                or digest(contact_bytes) != recipe["contact_profile"]["sha256"]
                or digest(animal_bytes) != recipe["animal"]["sha256"]
                or digest(articulation_bytes)
                != recipe["articulation_profile"]["sha256"]
            ):
                raise ContractError(
                    "v2 grounded source authority differs from baseline inputs"
                )
            source = Glb.from_bytes(source_bytes)
            require_supported_geometry(source)
            if source.document.get("animations"):
                raise ContractError(
                    "v2 grounded source authority contains prior animation"
                )
            roles = json.loads(rig_bytes)["roles"]
            contact_profile = json.loads(contact_bytes)
            forward, up = frame_axes(
                recipe["forward_axis"], recipe["up_axis"]
            )
            animal = load_animal_instance(
                json.loads(animal_bytes),
                source_sha256=recipe["source"]["sha256"],
            )
            verify_source_calibration(
                animal, source, roles, contact_profile, forward, up
            )
            apply_uniform_geometry_scale(source, animal["uniform_scale"])
            contact_profile = scaled_contact_profile(
                contact_profile, animal["uniform_scale"]
            )
            require_supported_geometry(source)
            body_height = geometry_height(source, roles, up)
            if not math.isclose(
                body_height,
                float(plan["body_height_m"]),
                rel_tol=0,
                abs_tol=1e-10,
            ):
                raise ContractError(
                    "v2 grounded source height differs from packaged plan"
                )
            articulation_profile = load_articulation_profile(
                json.loads(articulation_bytes)
            )
            authored_gait = gait
            expected_geometry = _measure_bound_grounded_touchdown_geometry(
                source,
                roles=roles,
                contact_profile=contact_profile,
                locomotion_gait=authored_gait,
                articulation_profile=articulation_profile,
                performance=performance,
                gait_response_policy=grounded_policy["body_response"][
                    "gait_response"
                ],
                source_geometry_sha256=recipe["source"]["sha256"],
                body_height_m=body_height,
                up=up,
                forward=forward,
            )
            if read_json(geometry_path) != expected_geometry:
                raise ContractError(
                    "v2 grounded touchdown geometry differs from source authority"
                )
            resolved = resolve_grounded_intent(
                authored_gait,
                body_height_m=float(plan["body_height_m"]),
                animal_hindlimb_length_m=animal["hindlimb_length_m"],
                source_geometry_sha256=recipe["source"]["sha256"],
                neutral_support_geometry=json.loads(support_bytes),
                family_policy=json.loads(policy_bytes),
                touchdown_geometry=expected_geometry,
            )
            gait = resolved.gait
            performance, gait_receipt = resolve_gait_response(
                performance,
                gait,
                grounded_policy["body_response"]["gait_response"],
            )
            expected_resolution = {
                "assembly": assembly_receipt,
                "gait_response": gait_receipt,
                "grounded_intent": resolved.receipt(),
            }
        else:
            airborne_document = response_policy["regimes"]["airborne"][
                "body_response"
            ]
            airborne_policy = load_airborne_body_response_policy(airborne_document)
            expected_airborne_receipt = airborne_response_receipt(gait, airborne_policy)
            expected_airborne = {
                "policy": airborne_document,
                "resolution": expected_airborne_receipt,
            }
            if plan.get("airborne_body_response") != expected_airborne:
                raise ContractError("airborne response differs from its baseline policy")
            expected_resolution = {
                "assembly": assembly_receipt,
                "airborne_body_response": expected_airborne_receipt,
            }
    else:
        performance, gait_receipt = resolve_gait_response(
            performance, gait, baseline["gait_response_policy"]
        )
        expected_resolution = {
            "assembly": assembly_receipt,
            "gait_response": gait_receipt,
        }
    if plan.get("parameters") != gait_parameters(gait):
        raise ContractError("motion plan parameters differ from the bound gait snapshot")
    if transition is not None and plan.get("transition_parameters") != gait_parameters(
        transition
    ):
        raise ContractError(
            "motion plan transition parameters differ from the bound program snapshot"
        )
    performance = replace(
        performance,
        canonical_support_anchors=solve_policy["canonical_support_anchors"],
        skin_refinement=solve_policy["skin_refinement"],
    )
    if "authored_material_reference" in recipe:
        solver_gait = AirborneGait(
            step_period_s=gait.step_period_s,
            cycles=gait.cycles,
            sample_hz=gait.sample_hz,
            swing_hip_lift_degrees=gait.swing_hip_lift_degrees,
        )
        source_query_plan = _grounded_source_query_plan(
            source,
            gait=gait,
            body_height_m=body_height,
            performance=performance,
            roles=roles,
            contact_profile=contact_profile,
            forward=forward,
            up=up,
            solve_policy=solve_policy,
        )
        bare_query = SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver_gait,
            locomotion_gait=gait,
            transition=None,
            plan=source_query_plan,
            contact_profile=contact_profile,
            up_axis=tuple(up),
            forward_axis=tuple(forward),
            source_clip=None,
            legacy_overlay=False,
            articulation_profile=articulation_profile,
        )
        steady_adapter = AuthoredMaterialContactAdapter.build(
            bare_query,
            json.loads(reference.capsule_bytes),
            authored_source=reference.source_bytes,
            retime_policy=reference.descriptor["adapter"]["retime_policy"],
            body_height_m=body_height,
            material_clearance_policy=json.loads(clearance_bytes),
        )
        if transition is None:
            expected_adapter = steady_adapter
        else:
            support_provider = CanonicalSupportAnchorProvider.build(
                source,
                semantic_roles=roles,
                solver_gait=solver_gait,
                locomotion_gait=gait,
                transition=transition,
                plan=plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                articulation_profile=articulation_profile,
            )
            raw_transition_query = SourceMotionQuery(
                source,
                semantic_roles=roles,
                solver_gait=solver_gait,
                locomotion_gait=gait,
                transition=transition,
                plan=plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                source_clip=None,
                legacy_overlay=False,
                articulation_profile=articulation_profile,
            )
            raw_transition_law = CanonicalConstantSkinTargetLaw.build(
                raw_transition_query,
                support_provider,
                source=source,
                semantic_roles=roles,
                solver_gait=solver_gait,
                locomotion_gait=gait,
                transition=transition,
                plan=plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                articulation_profile=articulation_profile,
            )
            clearance = GroundedTransitionClearanceResolver.build(
                raw_transition_law, gait
            )
            transition_query = SourceMotionQuery(
                source,
                semantic_roles=roles,
                solver_gait=solver_gait,
                locomotion_gait=gait,
                transition=transition,
                plan=plan,
                contact_profile=contact_profile,
                up_axis=tuple(up),
                forward_axis=tuple(forward),
                source_clip=None,
                legacy_overlay=False,
                articulation_profile=articulation_profile,
                transition_clearance=clearance,
            )
            expected_adapter = AuthoredMaterialContactAdapter.for_transition(
                steady_adapter,
                steady_query=SourceMotionQuery(
                    source,
                    semantic_roles=roles,
                    solver_gait=solver_gait,
                    locomotion_gait=gait,
                    transition=None,
                    plan=source_query_plan,
                    contact_profile=contact_profile,
                    up_axis=tuple(up),
                    forward_axis=tuple(forward),
                    source_clip=None,
                    legacy_overlay=False,
                    articulation_profile=articulation_profile,
                    authored_material_contact=steady_adapter,
                ),
                transition_query=transition_query,
            )
        expected_reference = {
            **reference.binding,
            "adapter": _thaw(expected_adapter.binding()),
        }
        if runtime_reference != expected_reference:
            raise ContractError(
                "authored material adapter does not replay from package inputs"
            )
    expected_parameters = {
        key: value for key, value in asdict(performance).items()
        if value is not None and not (
            (key == "pelvis_forward_velocity_modulation_fraction" and value == 0)
            or (key == "neutral_jaw_calibration" and value["close_degrees"] == 0)
        )
    }
    expected_parameters = json.loads(json_bytes(expected_parameters))
    if (
        runtime.get("motion_set") != resolution_lock["identities"]
        or runtime.get("solve_policy") != solve_policy
        or receipt.get("solve_policy") != solve_policy
        or plan.get("solve_policy") != solve_policy
        or plan.get("performance") != expected_parameters
        or receipt.get("baseline_performance_resolution") != expected_resolution
    ):
        raise ContractError("motion set solve policy provenance is inconsistent")


def _expected_motion_set_provenance_files(
    path: Path, baseline_snapshot: dict | None, recipe: dict
) -> set[str]:
    universe = {
        "motion-set.json", "motion-baseline.json", "motion-intent.json",
        "steady-motion-intent.json",
        "performance-profile.json", "neutral-pose-profile.json",
        "program-profile.json", "gait-profile.json",
        "locomotion-response-policy.json", "neutral-support-profile.json",
        "grounded-touchdown-geometry.json",
        "source.glb", "rig.json", "contact-profile.json",
        "authored-material-reference.json", "authored-material-source.bin",
        "authored-material-path.json",
        "authored-material-clearance-policy.json",
    }
    expected = universe - {"gait-profile.json"}
    if recipe.get("steady_motion") is None:
        expected.discard("steady-motion-intent.json")
    if baseline_snapshot is None or baseline_snapshot.get("schema") != (
        "eonwild.motion.motion-baseline.v2"
    ):
        expected -= {
            "locomotion-response-policy.json",
            "neutral-support-profile.json",
            "grounded-touchdown-geometry.json",
            "source.glb", "rig.json", "contact-profile.json",
        }
    else:
        airborne_v2 = recipe.get("program") == "airborne_gait"
        if recipe.get("program") == "gait_transition" and (
            path / "gait-profile.json"
        ).exists():
            airborne_v2 = read_json(path / "gait-profile.json").get("schema") == (
                "eonwild.motion.airborne-choreography.v1"
            )
        if airborne_v2:
            expected.discard("grounded-touchdown-geometry.json")
    if recipe.get("authored_material_reference") is None:
        expected -= {
            "authored-material-reference.json", "authored-material-source.bin",
            "authored-material-path.json",
        }
    if (
        baseline_snapshot is None
        or "authored_material_clearance" not in baseline_snapshot.get(
            "locomotion_response_policy", {}
        ).get("regimes", {}).get("grounded", {})
    ):
        expected.discard("authored-material-clearance-policy.json")
    if recipe.get("program") == "gait_transition":
        expected.add("gait-profile.json")
    return expected


def verify_package(path: Path) -> dict:
    manifest = read_json(path / "manifest.json")
    if manifest.get("schema") != "eonwild.motion.factory-package.v1":
        raise ContractError("unsupported package manifest")
    recipe = read_json(path / "recipe.json")
    required = {"root_motion.glb", "in_place.glb", "plan.json", "solver-receipt.json", "runtime.json", "validation.json", "inputs.lock.json", "recipe.json"}
    provenance_universe = {
        "motion-set.json", "motion-baseline.json", "motion-intent.json",
        "steady-motion-intent.json",
        "performance-profile.json", "neutral-pose-profile.json",
        "program-profile.json", "gait-profile.json",
        "locomotion-response-policy.json", "neutral-support-profile.json",
        "grounded-touchdown-geometry.json", "source.glb", "rig.json",
        "contact-profile.json", "authored-material-reference.json",
        "authored-material-source.bin", "authored-material-path.json",
        "authored-material-clearance-policy.json",
    }
    present_provenance = provenance_universe & set(manifest.get("files", {}))
    if recipe.get("authored_material_reference") is not None and not present_provenance:
        raise ContractError(
            "authored material reference requires compile-set package provenance"
        )
    baseline_snapshot = (
        read_json(path / "motion-baseline.json")
        if "motion-baseline.json" in present_provenance else None
    )
    expected_provenance = _expected_motion_set_provenance_files(
        path, baseline_snapshot, recipe
    )
    if present_provenance and present_provenance != expected_provenance:
        raise ContractError("motion set package provenance is incomplete")
    required.update(present_provenance)
    if "cubic-midpoint-plan.json" in manifest.get("files", {}):
        required.add("cubic-midpoint-plan.json")
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
    resolution_lock = lock.get("motion_set_resolution")
    if present_provenance:
        plan = read_json(path / "plan.json")
        _verify_motion_set_provenance(
            path, recipe=recipe, lock=lock, runtime=runtime,
            receipt=receipt, plan=plan,
        )
    elif (
        resolution_lock is not None
        or "motion_set" in runtime
        or "solve_policy" in runtime
        or "solve_policy" in receipt
    ):
        raise ContractError("unbound motion set provenance is not allowed")
    interpolation = runtime.get("interpolation", "LINEAR")
    if interpolation not in ("LINEAR", "CUBICSPLINE"):
        raise ContractError("package declares unsupported interpolation")
    serialized_interpolation = {}
    for mode in ("root_motion", "in_place"):
        glb = Glb.from_bytes((path / f"{mode}.glb").read_bytes())
        serialized_interpolation[mode] = _serialized_interpolation(glb)
    if set(serialized_interpolation.values()) != {interpolation}:
        raise ContractError(
            "package interpolation declaration differs from serialized exports"
        )
    is_cubic = interpolation == "CUBICSPLINE"
    has_midpoint_plan = "cubic-midpoint-plan.json" in manifest["files"]
    if is_cubic != has_midpoint_plan:
        raise ContractError("CUBICSPLINE package lacks midpoint plan evidence")
    emission = lock.get("emission")
    if is_cubic:
        if (
            not isinstance(emission, dict)
            or set(emission) != {
                "interpolation", "source_tangent_stencil_s",
                "convergence_stencil_s",
            }
            or emission.get("interpolation") != "CUBICSPLINE"
            or emission.get("source_tangent_stencil_s") != 0.001
            or emission.get("convergence_stencil_s") != 0.0005
        ):
            raise ContractError("CUBICSPLINE package lacks bound emission metadata")
        midpoint_plan = read_json(path / "cubic-midpoint-plan.json")
        root_glb = Glb.from_bytes((path / "root_motion.glb").read_bytes())
        midpoint_times = serialized_key_midpoint_times(
            root_glb, recipe["id"] + ".root_motion"
        )
        midpoint_rows = midpoint_plan.get("samples")
        if (
            not isinstance(midpoint_rows, list)
            or len(midpoint_rows) != len(midpoint_times)
            or any(not isinstance(row, dict) for row in midpoint_rows)
            or not np.allclose(
                midpoint_times,
                [row.get("time_s") for row in midpoint_rows],
                rtol=0,
                atol=2e-6,
            )
        ):
            raise ContractError("CUBICSPLINE midpoint plan timeline is inconsistent")
        midpoint_contact = validation.get("cubic_midpoint_skinned_contact")
        if not isinstance(midpoint_contact, dict) or set(midpoint_contact) != {
            "root_motion", "in_place"
        }:
            raise ContractError("CUBICSPLINE package lacks midpoint contact evidence")
        midpoint_verdicts = {
            mode: _midpoint_contact_verdict(
                result, sample_count=len(midpoint_times)
            )
            for mode, result in midpoint_contact.items()
        }
        if (
            "FAIL" in midpoint_verdicts.values()
            and validation.get("technical_status") == "PASS"
        ):
            raise ContractError("technical status ignores midpoint contact failure")
    elif emission is not None:
        raise ContractError("LINEAR package contains CUBICSPLINE emission metadata")
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
        repeated_midpoint = None
        if is_cubic:
            repeated_midpoint = {
                mode: emitted_articulation_envelopes(
                    Glb.from_bytes((path / f"{mode}.glb").read_bytes()),
                    semantic_roles=runtime.get("rig_roles"), plan=midpoint_plan,
                    profile=articulation_profile,
                    forward_axis=runtime.get("forward_axis"),
                    up_axis=runtime.get("up_axis"), sample_times=midpoint_times,
                )
                for mode in ("root_motion", "in_place")
            }
            if validation.get("cubic_midpoint_articulation_envelopes") != repeated_midpoint:
                raise ContractError("CUBICSPLINE midpoint articulation evidence is inconsistent")
        expected_articulation_pass = (
            all(check.get("status") == "PASS" for check in repeated.values())
            and (
                repeated_midpoint is None
                or all(check.get("status") == "PASS" for check in repeated_midpoint.values())
            )
        )
        if (not isinstance(summary, dict) or summary != articulation_profile.receipt()
                or runtime.get("articulation_profile") != summary
                or not isinstance(checks, dict) or set(checks) != {"root_motion", "in_place"}
                or any(check.get("profile") != summary for check in checks.values())
                or checks != repeated
                or receipt.get("final_emitted_articulation_gate") !=
                   ("PASS" if expected_articulation_pass else "FAIL")):
            raise ContractError("articulation profile provenance or final emitted gate is inconsistent")
        if not expected_articulation_pass and validation["technical_status"] == "PASS":
            raise ContractError("technical status ignores a final articulation failure")
    elif any("articulation_profile" in item for item in (lock.get("inputs", {}), receipt, runtime)) or "articulation_envelopes" in validation:
        raise ContractError("unbound articulation profile metadata is not allowed")
    from .metadata import require_metadata
    require_metadata(path, manifest)
    return {"integrity": "PASS", "technical_status": validation["technical_status"],
            "visual_review": validation["visual_review"], "unity_parity": validation["unity_parity"], "production_approved": False}
