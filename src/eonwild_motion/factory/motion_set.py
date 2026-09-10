"""Strict shared bindings for a versioned animal motion set.

Motion intents describe choreography only.  Geometry, semantic rig, animal,
contact, articulation, frame, and shared performance policy are admitted once
by the set's baseline and cannot be overridden by an intent.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from ..errors import ContractError
from .io import bind, digest, frame_axes, locked_file, read_json
from .acquired_reference import (
    AcquiredReferenceInputs,
    resolve_reference,
    validate_clearance_policy,
)


SET_SCHEMA = "eonwild.motion.motion-set.v1"
BASELINE_SCHEMA = "eonwild.motion.motion-baseline.v1"
INTENT_SCHEMA = "eonwild.motion.motion-intent.v1"
SET_SCHEMA_V2 = "eonwild.motion.motion-set.v2"
BASELINE_SCHEMA_V2 = "eonwild.motion.motion-baseline.v2"
INTENT_SCHEMA_V2 = "eonwild.motion.motion-intent.v2"
SUPPORTED_PROGRAMS = ("grounded_gait", "gait_transition")
# Airborne choreography remains a typed foundation, but it is not an admitted
# motion-set capability until the source-bound recovery provider is present.
SUPPORTED_PROGRAMS_V2 = SUPPORTED_PROGRAMS

_BASELINE_SHARED_FIELDS = (
    "source",
    "rig",
    "animal",
    "contact_profile",
    "articulation_profile",
    "performance_profile",
    "neutral_pose_profile",
)
_RECIPE_SHARED_FIELDS = tuple(
    key for key in _BASELINE_SHARED_FIELDS if key != "neutral_pose_profile"
)
_PROVENANCE_FILES = {
    "set": "motion-set.json",
    "baseline": "motion-baseline.json",
    "intent": "motion-intent.json",
}


def _document(value: Any, *, fields: set[str], schema: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ContractError(f"{label} contains missing or unknown fields")
    if value.get("schema") != schema:
        raise ContractError(f"unsupported {label} schema")
    identifier = value.get("id")
    version = value.get("version")
    if not isinstance(identifier, str) or not identifier:
        raise ContractError(f"{label} id is required")
    if type(version) is not int or version < 1:
        raise ContractError(f"{label} version must be a positive integer")
    return value


def _validate_set(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or value.get("schema") not in {
        SET_SCHEMA, SET_SCHEMA_V2
    }:
        raise ContractError("unsupported motion set schema")
    result = _document(
        value,
        fields={"schema", "id", "version", "baseline", "motions"},
        schema=value["schema"],
        label="motion set",
    )
    motions = result["motions"]
    if not isinstance(motions, list) or not motions:
        raise ContractError("motion set requires a nonempty ordered motion list")
    names: list[str] = []
    for entry in motions:
        if not isinstance(entry, Mapping) or set(entry) != {"name", "intent"}:
            raise ContractError("motion set entries require exactly name and intent")
        name = entry["name"]
        if not isinstance(name, str) or re.fullmatch(r"[a-z][a-z0-9-]*", name) is None:
            raise ContractError("motion set entry name must be a safe catalog component")
        names.append(name)
    if len(names) != len(set(names)):
        raise ContractError("motion set entry names must be unique")
    return result


def _validate_baseline(value: Any) -> Mapping[str, Any]:
    from ..solve.gait_response import load_gait_response_policy

    common_fields = {
        "schema", "id", "version", "family", "forward_axis", "up_axis",
        "supported_programs", "solve_policy",
        *_BASELINE_SHARED_FIELDS,
    }
    if not isinstance(value, Mapping):
        raise ContractError("motion baseline contains missing or unknown fields")
    schema = value.get("schema")
    if schema == BASELINE_SCHEMA:
        fields = common_fields | {"gait_response_policy"}
    elif schema == BASELINE_SCHEMA_V2:
        fields = common_fields | {"locomotion_response_policy"}
    else:
        raise ContractError("unsupported motion baseline schema")
    result = _document(
        value, fields=fields, schema=schema, label="motion baseline"
    )
    if not isinstance(result["family"], str) or not result["family"]:
        raise ContractError("motion baseline family is required")
    for label in ("forward_axis", "up_axis"):
        axis = result[label]
        if (
            not isinstance(axis, list)
            or len(axis) != 3
            or any(
                isinstance(component, bool)
                or not isinstance(component, (int, float))
                or not math.isfinite(component)
                for component in axis
            )
        ):
            raise ContractError(f"motion baseline {label} must be a finite numeric vector")
    frame_axes(result["forward_axis"], result["up_axis"])
    programs = result["supported_programs"]
    if (
        not isinstance(programs, list)
        or not programs
        or any(
            program not in (
                SUPPORTED_PROGRAMS if schema == BASELINE_SCHEMA
                else SUPPORTED_PROGRAMS_V2
            )
            for program in programs
        )
        or len(programs) != len(set(programs))
    ):
        raise ContractError("motion baseline has unsupported or repeated capabilities")
    if schema == BASELINE_SCHEMA:
        load_gait_response_policy(result["gait_response_policy"])
    else:
        _validate_locomotion_response_policy(result["locomotion_response_policy"])
    solve = result["solve_policy"]
    solve_fields = {
        "schema", "representation", "canonical_support_anchors",
        "skin_target_law", "skin_refinement",
    }
    if (
        not isinstance(solve, Mapping)
        or set(solve) not in (
            solve_fields, solve_fields | {"grounded_transition_clearance"}
        )
        or solve.get("schema") != "eonwild.motion.solve-policy.v1"
        or solve.get("representation") != "CUBICSPLINE"
        or solve.get("canonical_support_anchors") is not True
        or solve.get("skin_target_law") not in (
            "canonical_constant_skin_targets.v1",
            "canonical_semantic_foot_frame_targets.v2",
        )
        or solve.get("skin_refinement") is not True
        or (
            "grounded_transition_clearance" in solve
            and solve["grounded_transition_clearance"]
            != "material_floor_scaled_excess.v1"
        )
    ):
        raise ContractError("motion baseline requires the supported explicit solve policy")
    return result


def _validate_locomotion_response_policy(value: Any) -> Mapping[str, Any]:
    from ..solve.gait_response import load_gait_response_policy
    from ..solve.locomotion_regime_response import load_airborne_body_response_policy

    if (
        not isinstance(value, Mapping)
        or set(value) != {"schema", "regimes"}
        or value.get("schema")
        != "eonwild.motion.motion-set-locomotion-response.v1"
        or not isinstance(value.get("regimes"), Mapping)
        or set(value["regimes"]) != {"grounded", "airborne"}
    ):
        raise ContractError("motion baseline locomotion response is incomplete")
    grounded = value["regimes"]["grounded"]
    airborne = value["regimes"]["airborne"]
    if (
        not isinstance(grounded, Mapping)
        or set(grounded) not in ({
            "intent_resolution", "neutral_support_profile", "body_response"
        }, {
            "intent_resolution", "neutral_support_profile", "body_response",
            "authored_material_clearance",
        })
        or not isinstance(grounded["intent_resolution"], Mapping)
        or set(grounded["intent_resolution"]) != {"path", "sha256"}
        or not isinstance(grounded["neutral_support_profile"], Mapping)
        or set(grounded["neutral_support_profile"]) != {"path", "sha256"}
        or not isinstance(grounded["body_response"], Mapping)
        or set(grounded["body_response"]) != {"model", "gait_response"}
        or grounded["body_response"].get("model")
        != "existing_grounded_shared_style.v1"
        or (
            "authored_material_clearance" in grounded
            and (
                not isinstance(grounded["authored_material_clearance"], Mapping)
                or set(grounded["authored_material_clearance"])
                != {"path", "sha256"}
            )
        )
    ):
        raise ContractError("grounded locomotion response is incomplete or unsupported")
    load_gait_response_policy(grounded["body_response"]["gait_response"])
    if (
        not isinstance(airborne, Mapping)
        or set(airborne) != {"intent_resolution", "body_response"}
        or airborne["intent_resolution"]
        != {"model": "airborne_choreography_passthrough.v1"}
    ):
        raise ContractError("airborne locomotion response is incomplete or unsupported")
    load_airborne_body_response_policy(airborne["body_response"])
    return value


def _validate_intent(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("motion intent must be a mapping")
    required = {"schema", "id", "version", "program", "program_profile"}
    optional = {"gait_profile", "description", "supersedes", "authored_material_reference", "steady_motion"}
    if not required <= set(value) or set(value) - required - optional:
        raise ContractError("motion intent contains missing or unknown fields")
    schema = value.get("schema")
    if schema not in {INTENT_SCHEMA, INTENT_SCHEMA_V2}:
        raise ContractError("unsupported motion intent schema")
    result = _document(
        value,
        fields=set(value),
        schema=schema,
        label="motion intent",
    )
    program = result["program"]
    supported = SUPPORTED_PROGRAMS if schema == INTENT_SCHEMA else SUPPORTED_PROGRAMS_V2
    if program not in supported:
        raise ContractError("motion intent program is outside baseline capabilities")
    if (program == "gait_transition") != ("gait_profile" in result):
        raise ContractError("only gait-transition intents require a gait profile")
    if "authored_material_reference" in result and program != "grounded_gait":
        raise ContractError(
            "authored material reference is currently supported only for steady grounded gait"
        )
    if "steady_motion" in result and not (
        program == "gait_transition" and schema == INTENT_SCHEMA_V2
    ):
        raise ContractError(
            "steady motion is supported only by v2 gait-transition intents"
        )
    if "steady_motion" in result and (
        not isinstance(result["steady_motion"], str)
        or re.fullmatch(r"[a-z][a-z0-9-]*", result["steady_motion"]) is None
    ):
        raise ContractError("steady motion must be a safe motion-set name")
    for label in ("description", "supersedes"):
        if label in result and (not isinstance(result[label], str) or not result[label]):
            raise ContractError(f"motion intent {label} must be a nonempty string")
    return result


def _select_intent(set_document: Mapping[str, Any], motion: str) -> Mapping[str, Any]:
    if not isinstance(motion, str) or not motion:
        raise ContractError("selected motion name is required")
    matches = [entry for entry in set_document["motions"] if entry["name"] == motion]
    if len(matches) != 1:
        raise ContractError(f"selected motion is not present in motion set: {motion}")
    return matches[0]


def _recipe(
    baseline: Mapping[str, Any],
    intent: Mapping[str, Any],
    *,
    steady_intent: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    program = intent["program"]
    if program not in baseline["supported_programs"]:
        raise ContractError("motion intent program is not admitted by its baseline")
    recipe: dict[str, Any] = {
        "schema": "eonwild.motion.factory-recipe.v1",
        "id": intent["id"],
        "version": intent["version"],
        "family": baseline["family"],
        "program": program,
        **{key: baseline[key] for key in _RECIPE_SHARED_FIELDS},
        "program_profile": intent["program_profile"],
        "forward_axis": baseline["forward_axis"],
        "up_axis": baseline["up_axis"],
    }
    for key in ("gait_profile", "description", "supersedes", "authored_material_reference", "steady_motion"):
        if key in intent:
            recipe[key] = intent[key]
    if steady_intent is not None:
        recipe["authored_material_reference"] = steady_intent["authored_material_reference"]
    return recipe


@dataclass(frozen=True)
class MotionSetResolution:
    motion: str
    recipe: dict[str, Any]
    set_binding: dict[str, str]
    baseline_binding: dict[str, str]
    intent_binding: dict[str, str]
    set_bytes: bytes
    baseline_bytes: bytes
    intent_bytes: bytes
    neutral_pose_bytes: bytes
    program_profile_bytes: bytes
    gait_profile_bytes: bytes | None
    locomotion_response_bytes: bytes | None = None
    neutral_support_bytes: bytes | None = None
    acquired_reference: AcquiredReferenceInputs | None = None
    authored_material_clearance_bytes: bytes | None = None
    steady_intent_binding: dict[str, str] | None = None
    steady_intent_bytes: bytes | None = None

    @property
    def payloads(self) -> dict[str, bytes]:
        result = {
            _PROVENANCE_FILES["set"]: self.set_bytes,
            _PROVENANCE_FILES["baseline"]: self.baseline_bytes,
            _PROVENANCE_FILES["intent"]: self.intent_bytes,
            "program-profile.json": self.program_profile_bytes,
        }
        if self.gait_profile_bytes is not None:
            result["gait-profile.json"] = self.gait_profile_bytes
        if self.locomotion_response_bytes is not None:
            result["locomotion-response-policy.json"] = self.locomotion_response_bytes
        if self.neutral_support_bytes is not None:
            result["neutral-support-profile.json"] = self.neutral_support_bytes
        if self.acquired_reference is not None:
            result.update({
                "authored-material-reference.json": self.acquired_reference.descriptor_bytes,
                "authored-material-source.bin": self.acquired_reference.source_bytes,
                "authored-material-path.json": self.acquired_reference.capsule_bytes,
            })
        if self.authored_material_clearance_bytes is not None:
            result["authored-material-clearance-policy.json"] = (
                self.authored_material_clearance_bytes
            )
        if self.steady_intent_bytes is not None:
            result["steady-motion-intent.json"] = self.steady_intent_bytes
        return result

    @property
    def lock(self) -> dict[str, Any]:
        set_document = json.loads(self.set_bytes)
        baseline = json.loads(self.baseline_bytes)
        intent = json.loads(self.intent_bytes)
        result = {
            "motion": self.motion,
            "set": self.set_binding,
            "baseline": self.baseline_binding,
            "intent": self.intent_binding,
            "identities": {
                "set": {key: set_document[key] for key in ("id", "version")},
                "baseline": {key: baseline[key] for key in ("id", "version")},
                "intent": {key: intent[key] for key in ("id", "version")},
            },
        }
        if self.acquired_reference is not None:
            result["authored_material_reference"] = self.acquired_reference.binding
        if self.authored_material_clearance_bytes is not None:
            result["authored_material_clearance_policy_sha256"] = digest(
                self.authored_material_clearance_bytes
            )
        if self.steady_intent_bytes is not None:
            steady_intent = json.loads(self.steady_intent_bytes)
            result["steady_motion_dependency"] = {
                "motion": intent["steady_motion"],
                "intent": self.steady_intent_binding,
                "identity": {key: steady_intent[key] for key in ("id", "version")},
            }
        return result

    @property
    def gait_response_policy(self) -> Mapping[str, Any]:
        baseline = json.loads(self.baseline_bytes)
        if baseline.get("schema") != BASELINE_SCHEMA:
            raise ContractError("v2 motion baseline uses regime-specific response")
        return baseline["gait_response_policy"]

    @property
    def locomotion_response_policy(self) -> Mapping[str, Any] | None:
        baseline = json.loads(self.baseline_bytes)
        return baseline.get("locomotion_response_policy")

    @property
    def solve_policy(self) -> Mapping[str, Any]:
        return json.loads(self.baseline_bytes)["solve_policy"]


def resolve_motion_set_selection(
    root: Path, set_path: Path, motions: list[str]
) -> list[MotionSetResolution]:
    """Resolve selected intents against one owned baseline snapshot."""
    if (
        not isinstance(motions, list)
        or not motions
        or any(not isinstance(motion, str) or not motion for motion in motions)
        or len(motions) != len(set(motions))
    ):
        raise ContractError("selected motion names must be a unique nonempty list")
    root = root.resolve()
    set_path = set_path.resolve()
    if not set_path.is_relative_to(root):
        raise ContractError("motion set path escapes source root")
    set_document = _validate_set(read_json(set_path))
    set_bytes = set_path.read_bytes()
    if json.loads(set_bytes) != set_document:
        raise ContractError("motion set changed during resolution")
    set_binding = bind(root, set_path)
    if digest(set_bytes) != set_binding["sha256"]:
        raise ContractError("motion set changed during resolution")
    baseline_path = locked_file(root, set_document["baseline"])
    baseline_bytes = baseline_path.read_bytes()
    if digest(baseline_bytes) != set_document["baseline"]["sha256"]:
        raise ContractError("motion baseline changed during resolution")
    baseline = _validate_baseline(json.loads(baseline_bytes))
    baseline_paths = {
        key: locked_file(root, baseline[key]) for key in _BASELINE_SHARED_FIELDS
    }
    neutral_pose_bytes = baseline_paths["neutral_pose_profile"].read_bytes()
    if digest(neutral_pose_bytes) != baseline["neutral_pose_profile"]["sha256"]:
        raise ContractError("neutral-pose profile changed during resolution")
    from ..solve.gait_response import load_neutral_pose_profile
    load_neutral_pose_profile(json.loads(neutral_pose_bytes))
    locomotion_response_bytes = None
    neutral_support_bytes = None
    authored_material_clearance_bytes = None
    if baseline["schema"] == BASELINE_SCHEMA_V2:
        grounded_response = baseline["locomotion_response_policy"]["regimes"][
            "grounded"
        ]
        response_reference = grounded_response["intent_resolution"]
        response_path = locked_file(root, response_reference)
        locomotion_response_bytes = response_path.read_bytes()
        if digest(locomotion_response_bytes) != response_reference["sha256"]:
            raise ContractError("locomotion response policy changed during resolution")
        support_reference = grounded_response["neutral_support_profile"]
        support_path = locked_file(root, support_reference)
        neutral_support_bytes = support_path.read_bytes()
        if digest(neutral_support_bytes) != support_reference["sha256"]:
            raise ContractError("neutral support profile changed during resolution")
        if "authored_material_clearance" in grounded_response:
            clearance_reference = grounded_response["authored_material_clearance"]
            clearance_path = locked_file(root, clearance_reference)
            authored_material_clearance_bytes = clearance_path.read_bytes()
            if digest(authored_material_clearance_bytes) != clearance_reference["sha256"]:
                raise ContractError("authored material clearance policy changed during resolution")
            validate_clearance_policy(json.loads(authored_material_clearance_bytes))
    resolutions = []
    for motion in motions:
        entry = _select_intent(set_document, motion)
        intent_path = locked_file(root, entry["intent"])
        intent_bytes = intent_path.read_bytes()
        if digest(intent_bytes) != entry["intent"]["sha256"]:
            raise ContractError("motion intent changed during resolution")
        intent = _validate_intent(json.loads(intent_bytes))
        expected_intent_schema = (
            INTENT_SCHEMA if baseline["schema"] == BASELINE_SCHEMA
            else INTENT_SCHEMA_V2
        )
        expected_set_schema = (
            SET_SCHEMA if baseline["schema"] == BASELINE_SCHEMA else SET_SCHEMA_V2
        )
        if (
            intent["schema"] != expected_intent_schema
            or set_document["schema"] != expected_set_schema
        ):
            raise ContractError("motion set, baseline, and intent schema versions differ")
        program_profile_path = locked_file(root, intent["program_profile"])
        program_profile_bytes = program_profile_path.read_bytes()
        if digest(program_profile_bytes) != intent["program_profile"]["sha256"]:
            raise ContractError("motion program profile changed during resolution")
        gait_profile_bytes = None
        acquired_reference = None
        steady_intent = None
        steady_intent_binding = None
        steady_intent_bytes = None
        if "gait_profile" in intent:
            gait_profile_path = locked_file(root, intent["gait_profile"])
            gait_profile_bytes = gait_profile_path.read_bytes()
            if digest(gait_profile_bytes) != intent["gait_profile"]["sha256"]:
                raise ContractError("motion gait profile changed during resolution")
            if (
                baseline["schema"] == BASELINE_SCHEMA_V2
                and json.loads(gait_profile_bytes).get("schema")
                == "eonwild.motion.airborne-choreography.v1"
            ):
                raise ContractError(
                    "v2 airborne locomotion requires a source-bound recovery provider"
                )
        reference_owner = intent
        if "steady_motion" in intent:
            if baseline["solve_policy"].get("grounded_transition_clearance") != "material_floor_scaled_excess.v1":
                raise ContractError("acquired steady transition requires grounded clearance policy")
            steady_entry = _select_intent(set_document, intent["steady_motion"])
            if steady_entry is entry:
                raise ContractError("transition steady motion cannot refer to itself")
            steady_path = locked_file(root, steady_entry["intent"])
            steady_intent_bytes = steady_path.read_bytes()
            if digest(steady_intent_bytes) != steady_entry["intent"]["sha256"]:
                raise ContractError("steady motion intent changed during resolution")
            steady_intent = _validate_intent(json.loads(steady_intent_bytes))
            if (
                steady_intent["schema"] != INTENT_SCHEMA_V2
                or steady_intent["program"] != "grounded_gait"
                or "authored_material_reference" not in steady_intent
                or intent["gait_profile"] != steady_intent["program_profile"]
            ):
                raise ContractError("transition steady motion must bind its exact acquired grounded gait")
            steady_intent_binding = dict(steady_entry["intent"])
            reference_owner = steady_intent
        if "authored_material_reference" in reference_owner:
            if authored_material_clearance_bytes is None:
                raise ContractError(
                    "authored material reference requires baseline-owned clearance policy"
                )
            acquired_reference = resolve_reference(root, reference_owner["authored_material_reference"])
        resolutions.append(MotionSetResolution(
            motion=motion,
            recipe=_recipe(baseline, intent, steady_intent=steady_intent),
            set_binding=set_binding,
            baseline_binding=dict(set_document["baseline"]),
            intent_binding=dict(entry["intent"]),
            set_bytes=set_bytes,
            baseline_bytes=baseline_bytes,
            intent_bytes=intent_bytes,
            neutral_pose_bytes=neutral_pose_bytes,
            program_profile_bytes=program_profile_bytes,
            gait_profile_bytes=gait_profile_bytes,
            locomotion_response_bytes=locomotion_response_bytes,
            neutral_support_bytes=neutral_support_bytes,
            acquired_reference=acquired_reference,
            authored_material_clearance_bytes=authored_material_clearance_bytes,
            steady_intent_binding=steady_intent_binding,
            steady_intent_bytes=steady_intent_bytes,
        ))
    if set_path.read_bytes() != set_bytes or baseline_path.read_bytes() != baseline_bytes:
        raise ContractError("motion set or baseline changed during selection")
    return resolutions


def resolve_motion_set(root: Path, set_path: Path, motion: str) -> MotionSetResolution:
    """Resolve one selected intent while retaining the exact authored bytes."""
    return resolve_motion_set_selection(root, set_path, [motion])[0]


def reconstruct_motion_set(
    *, set_bytes: bytes, baseline_bytes: bytes, intent_bytes: bytes,
    resolution_lock: Any,
    steady_intent_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Reconstruct a package recipe solely from its authored snapshots."""
    try:
        set_document = _validate_set(json.loads(set_bytes))
        baseline = _validate_baseline(json.loads(baseline_bytes))
        intent = _validate_intent(json.loads(intent_bytes))
    except (TypeError, ValueError) as exc:
        raise ContractError(f"motion set provenance is not valid JSON: {exc}") from exc
    expected = (
        (SET_SCHEMA, INTENT_SCHEMA)
        if baseline["schema"] == BASELINE_SCHEMA
        else (SET_SCHEMA_V2, INTENT_SCHEMA_V2)
    )
    if (set_document["schema"], intent["schema"]) != expected:
        raise ContractError("motion set snapshot schema versions disagree")
    if not isinstance(resolution_lock, Mapping) or set(resolution_lock) not in ({
        "motion", "set", "baseline", "intent", "identities"
    }, {
        "motion", "set", "baseline", "intent", "identities",
        "authored_material_reference"
    }, {
        "motion", "set", "baseline", "intent", "identities",
        "authored_material_reference", "authored_material_clearance_policy_sha256"
    }, {
        "motion", "set", "baseline", "intent", "identities",
        "authored_material_clearance_policy_sha256"
    }, {
        "motion", "set", "baseline", "intent", "identities",
        "authored_material_reference", "authored_material_clearance_policy_sha256",
        "steady_motion_dependency"
    }):
        raise ContractError("motion set resolution lock is incomplete")
    entry = _select_intent(set_document, resolution_lock["motion"])
    if (
        resolution_lock["baseline"] != set_document["baseline"]
        or resolution_lock["intent"] != entry["intent"]
        or digest(baseline_bytes) != set_document["baseline"].get("sha256")
        or digest(intent_bytes) != entry["intent"].get("sha256")
    ):
        raise ContractError("motion set snapshot identities disagree")
    identities = resolution_lock["identities"]
    expected_identities = {
        "set": {key: set_document[key] for key in ("id", "version")},
        "baseline": {key: baseline[key] for key in ("id", "version")},
        "intent": {key: intent[key] for key in ("id", "version")},
    }
    if identities != expected_identities:
        raise ContractError("motion set declared identities differ from snapshots")
    steady_intent = None
    dependency = resolution_lock.get("steady_motion_dependency")
    if "steady_motion" in intent:
        if steady_intent_bytes is None or not isinstance(dependency, Mapping):
            raise ContractError("steady motion dependency snapshot is missing")
        steady_entry = _select_intent(set_document, intent["steady_motion"])
        try:
            steady_intent = _validate_intent(json.loads(steady_intent_bytes))
        except (TypeError, ValueError) as exc:
            raise ContractError("steady motion dependency is not valid JSON") from exc
        if (
            set(dependency) != {"motion", "intent", "identity"}
            or dependency["motion"] != intent["steady_motion"]
            or dependency["intent"] != steady_entry["intent"]
            or digest(steady_intent_bytes) != steady_entry["intent"]["sha256"]
            or dependency["identity"]
            != {key: steady_intent[key] for key in ("id", "version")}
            or steady_intent.get("schema") != INTENT_SCHEMA_V2
            or steady_intent.get("program") != "grounded_gait"
            or "authored_material_reference" not in steady_intent
            or intent["gait_profile"] != steady_intent["program_profile"]
        ):
            raise ContractError("steady motion dependency snapshot is inconsistent")
    elif steady_intent_bytes is not None or dependency is not None:
        raise ContractError("unbound steady motion dependency is not allowed")
    has_reference = "authored_material_reference" in intent or steady_intent is not None
    if has_reference != ("authored_material_reference" in resolution_lock):
        raise ContractError("authored material reference lock is inconsistent")
    if has_reference and "authored_material_clearance_policy_sha256" not in resolution_lock:
        raise ContractError("authored material clearance policy lock is missing")
    grounded = baseline.get("locomotion_response_policy", {}).get("regimes", {}).get(
        "grounded", {}
    )
    if ("authored_material_clearance" in grounded) != (
        "authored_material_clearance_policy_sha256" in resolution_lock
    ):
        raise ContractError("authored material clearance policy lock is inconsistent")
    set_binding = resolution_lock["set"]
    if (
        not isinstance(set_binding, Mapping)
        or set(set_binding) != {"path", "sha256"}
        or digest(set_bytes) != set_binding.get("sha256")
    ):
        raise ContractError("motion set snapshot differs from its resolution lock")
    return _recipe(baseline, intent, steady_intent=steady_intent)
