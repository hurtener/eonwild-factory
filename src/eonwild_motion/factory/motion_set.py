"""Strict shared bindings for a versioned animal motion set.

Motion intents describe choreography only.  Geometry, semantic rig, animal,
contact, articulation, frame, and shared performance policy are admitted once
by the set's baseline and cannot be overridden by an intent.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from ..errors import ContractError
from .io import bind, digest, frame_axes, locked_file, read_json


SET_SCHEMA = "eonwild.motion.motion-set.v1"
BASELINE_SCHEMA = "eonwild.motion.motion-baseline.v1"
INTENT_SCHEMA = "eonwild.motion.motion-intent.v1"
SUPPORTED_PROGRAMS = ("grounded_gait", "gait_transition")

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
    result = _document(
        value,
        fields={"schema", "id", "version", "baseline", "motions"},
        schema=SET_SCHEMA,
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
        if not isinstance(name, str) or not name:
            raise ContractError("motion set entry name is required")
        names.append(name)
    if len(names) != len(set(names)):
        raise ContractError("motion set entry names must be unique")
    return result


def _validate_baseline(value: Any) -> Mapping[str, Any]:
    from ..solve.gait_response import load_gait_response_policy

    fields = {
        "schema", "id", "version", "family", "forward_axis", "up_axis",
        "supported_programs", "gait_response_policy", "solve_policy",
        *_BASELINE_SHARED_FIELDS,
    }
    result = _document(
        value, fields=fields, schema=BASELINE_SCHEMA, label="motion baseline"
    )
    if not isinstance(result["family"], str) or not result["family"]:
        raise ContractError("motion baseline family is required")
    frame_axes(result["forward_axis"], result["up_axis"])
    programs = result["supported_programs"]
    if (
        not isinstance(programs, list)
        or not programs
        or any(program not in SUPPORTED_PROGRAMS for program in programs)
        or len(programs) != len(set(programs))
    ):
        raise ContractError("motion baseline has unsupported or repeated capabilities")
    load_gait_response_policy(result["gait_response_policy"])
    solve = result["solve_policy"]
    if (
        not isinstance(solve, Mapping)
        or set(solve) != {
            "schema", "representation", "canonical_support_anchors",
            "skin_target_law", "skin_refinement",
        }
        or solve.get("schema") != "eonwild.motion.solve-policy.v1"
        or solve.get("representation") != "CUBICSPLINE"
        or solve.get("canonical_support_anchors") is not True
        or solve.get("skin_target_law") != "canonical_constant_skin_targets.v1"
        or solve.get("skin_refinement") is not True
    ):
        raise ContractError("motion baseline requires the supported explicit solve policy")
    return result


def _validate_intent(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("motion intent must be a mapping")
    required = {"schema", "id", "version", "program", "program_profile"}
    optional = {"gait_profile", "description", "supersedes"}
    if not required <= set(value) or set(value) - required - optional:
        raise ContractError("motion intent contains missing or unknown fields")
    result = _document(
        value,
        fields=set(value),
        schema=INTENT_SCHEMA,
        label="motion intent",
    )
    program = result["program"]
    if program not in SUPPORTED_PROGRAMS:
        raise ContractError("motion intent program is outside baseline capabilities")
    if (program == "gait_transition") != ("gait_profile" in result):
        raise ContractError("only gait-transition intents require a gait profile")
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


def _recipe(baseline: Mapping[str, Any], intent: Mapping[str, Any]) -> dict[str, Any]:
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
    for key in ("gait_profile", "description", "supersedes"):
        if key in intent:
            recipe[key] = intent[key]
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

    @property
    def payloads(self) -> dict[str, bytes]:
        return {
            _PROVENANCE_FILES["set"]: self.set_bytes,
            _PROVENANCE_FILES["baseline"]: self.baseline_bytes,
            _PROVENANCE_FILES["intent"]: self.intent_bytes,
        }

    @property
    def lock(self) -> dict[str, Any]:
        set_document = json.loads(self.set_bytes)
        baseline = json.loads(self.baseline_bytes)
        intent = json.loads(self.intent_bytes)
        return {
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

    @property
    def gait_response_policy(self) -> Mapping[str, Any]:
        return json.loads(self.baseline_bytes)["gait_response_policy"]

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
    resolutions = []
    for motion in motions:
        entry = _select_intent(set_document, motion)
        intent_path = locked_file(root, entry["intent"])
        intent_bytes = intent_path.read_bytes()
        if digest(intent_bytes) != entry["intent"]["sha256"]:
            raise ContractError("motion intent changed during resolution")
        intent = _validate_intent(json.loads(intent_bytes))
        locked_file(root, intent["program_profile"])
        if "gait_profile" in intent:
            locked_file(root, intent["gait_profile"])
        resolutions.append(MotionSetResolution(
            motion=motion,
            recipe=_recipe(baseline, intent),
            set_binding=set_binding,
            baseline_binding=dict(set_document["baseline"]),
            intent_binding=dict(entry["intent"]),
            set_bytes=set_bytes,
            baseline_bytes=baseline_bytes,
            intent_bytes=intent_bytes,
            neutral_pose_bytes=neutral_pose_bytes,
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
) -> dict[str, Any]:
    """Reconstruct a package recipe solely from its authored snapshots."""
    try:
        set_document = _validate_set(json.loads(set_bytes))
        baseline = _validate_baseline(json.loads(baseline_bytes))
        intent = _validate_intent(json.loads(intent_bytes))
    except (TypeError, ValueError) as exc:
        raise ContractError(f"motion set provenance is not valid JSON: {exc}") from exc
    if not isinstance(resolution_lock, Mapping) or set(resolution_lock) != {
        "motion", "set", "baseline", "intent", "identities"
    }:
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
    set_binding = resolution_lock["set"]
    if (
        not isinstance(set_binding, Mapping)
        or set(set_binding) != {"path", "sha256"}
        or digest(set_bytes) != set_binding.get("sha256")
    ):
        raise ContractError("motion set snapshot differs from its resolution lock")
    return _recipe(baseline, intent)
