from __future__ import annotations

from collections.abc import Iterable
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..contracts.models import ResolvedProfile
from ..errors import ValidationFailure
from ..hashing import sha256_file


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"{label} is unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationFailure(f"{label} must be an object")
    return value


def _reference(repository: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValidationFailure(f"{label} path is missing")
    path = (repository / value).resolve()
    if path != repository and repository not in path.parents:
        raise ValidationFailure(f"{label} path escapes repository")
    if not path.is_file():
        raise ValidationFailure(f"{label} does not exist: {value}")
    return path


def _schema(resolved: ResolvedProfile, document: dict, name: str) -> None:
    schema = _load_json(
        resolved.repository / "schemas/motion" / name,
        f"{name} schema",
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.path),
    )
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise ValidationFailure(
            f"normative evidence schema failure at {location}: {errors[0].message}"
        )


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationFailure(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValidationFailure(f"{label} must be finite")
    return result


def _same(left: Any, right: Any, label: str, tolerance: float = 1e-12) -> None:
    if abs(_finite(left, label) - _finite(right, label)) > tolerance:
        raise ValidationFailure(f"{label} cross-document mismatch")


def _bounded(value: Any, bounds: dict[str, Any], label: str) -> None:
    number = _finite(value, label)
    if number < _finite(bounds["min"], f"{label}.min") or number > _finite(
        bounds["max"], f"{label}.max"
    ):
        raise ValidationFailure(f"{label} is outside normative bounds")


def _walk(root: dict[str, Any], selector: str) -> Any:
    value: Any = root
    for part in selector.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValidationFailure(f"normative metric missing: {selector}")
        value = value[part]
    return value


def _all_true(values: Iterable[Any]) -> bool:
    values = list(values)
    return bool(values) and all(value is True for value in values)


def _role_allowed(role: str, writes: list[str]) -> bool:
    for write in writes:
        pattern = write.removesuffix(".rotation").removesuffix(".translation")
        if pattern.endswith(".*") and role.startswith(pattern[:-1]):
            return True
        if role == pattern:
            return True
    return False


def _validate_layer_metrics(
    resolved: ResolvedProfile,
    layer_metrics: dict[str, Any],
    selected_scale: float,
) -> dict[str, Any]:
    implementations = [layer.data["implementation"] for layer in resolved.layers]
    if set(layer_metrics) != set(implementations):
        raise ValidationFailure("layer metrics implementation set mismatch")
    clips = {clip["semanticId"] for clip in resolved.motion["clips"]}
    manifests: dict[str, list[str]] = {}
    for layer in resolved.layers:
        implementation = layer.data["implementation"]
        metrics = layer_metrics[implementation]
        if set(metrics) != clips:
            raise ValidationFailure(f"{implementation} metric clip set mismatch")
        declared_scale = layer.data.get("parameters", {}).get("amplitudeScale")
        if declared_scale is not None:
            _same(declared_scale, selected_scale, f"{implementation}.amplitudeScale")
        for clip, facts in metrics.items():
            if "amplitudeScale" in facts:
                _same(facts["amplitudeScale"], selected_scale, f"{implementation}.{clip}.scale")
            manifest = facts.get("deltaManifest")
            if manifest is None:
                continue
            if not isinstance(manifest, list) or not manifest:
                raise ValidationFailure("counterbalance delta manifest is missing")
            roles = []
            for index, entry in enumerate(manifest):
                if not isinstance(entry, dict):
                    raise ValidationFailure("counterbalance manifest entry is invalid")
                role = entry.get("semantic_role")
                if not isinstance(role, str) or not _role_allowed(role, layer.data["writes"]):
                    raise ValidationFailure(f"undeclared semantic role in delta manifest: {role}")
                if entry.get("rotation_delta_only") is not True:
                    raise ValidationFailure("counterbalance manifest is not rotation-only")
                _same(entry.get("shared_sweep_scale"), selected_scale, f"manifest[{index}].scale")
                for field in ("phase_offset_cycles", "max_adjacent_delta_degrees", "max_second_difference_degrees", "loop_seam"):
                    _finite(entry.get(field), f"manifest[{index}].{field}")
                for field in ("p2p_degrees", "mean_degrees"):
                    vector = entry.get(field)
                    if not isinstance(vector, list) or len(vector) != 3:
                        raise ValidationFailure(f"manifest[{index}].{field} must be VEC3")
                    for component in vector:
                        _finite(component, f"manifest[{index}].{field}")
                roles.append(role)
            if len(roles) != len(set(roles)):
                raise ValidationFailure("counterbalance manifest repeats semantic roles")
            manifests[clip] = sorted(roles)
    if manifests and len({tuple(value) for value in manifests.values()}) != 1:
        raise ValidationFailure("counterbalance semantic ownership differs by clip")
    return {"implementations": implementations, "semanticRolesByClip": manifests}


def evaluate_normative_evidence(
    resolved: ResolvedProfile,
    evidence: dict[str, Any],
    *,
    candidate_path: Path | None = None,
    declared_schema: str,
) -> dict[str, Any]:
    _schema(resolved, evidence, "normative-evaluation.v1.schema.json")
    if evidence.get("schema") != declared_schema:
        raise ValidationFailure("normative evaluation schema declaration mismatch")
    if evidence["status"] != "PASS":
        raise ValidationFailure("normative evaluation status is not PASS")
    candidate_path = (candidate_path or resolved.approved_output_path).resolve()
    candidate_sha = sha256_file(candidate_path)
    if candidate_sha != resolved.approved_output_sha256 or evidence["artifactSha256"] != candidate_sha:
        raise ValidationFailure("normative candidate artifact identity mismatch")

    references = evidence["evidence"]
    sweep_path = _reference(resolved.repository, references["sweep"], "amplitude sweep")
    layer_path = _reference(resolved.repository, references["layerMetrics"], "layer metrics")
    witness_path = _reference(resolved.repository, references["finalSkinnedWitnesses"], "final-skinned witnesses")
    threshold_path = _reference(resolved.repository, references["thresholds"], "normative thresholds")
    sweep = _load_json(sweep_path, "amplitude sweep")
    layer_metrics = _load_json(layer_path, "layer metrics")
    witnesses = _load_json(witness_path, "final-skinned witnesses")
    thresholds = _load_json(threshold_path, "normative thresholds")
    _schema(resolved, sweep, "amplitude-sweep.v1.schema.json")
    _schema(resolved, witnesses, "final-skinned-comparison.v1.schema.json")
    _schema(resolved, thresholds, "balance-thresholds.v1.schema.json")

    if thresholds["basis"]["sourceStableArtifactSha256"] != resolved.input_sha256:
        raise ValidationFailure("normative threshold baseline identity mismatch")
    declared_scales = [float(value) for value in thresholds["boundedAmplitudeSweep"]["amplitudeScaleAscending"]]
    actual_scales = [_finite(item["scale"], "sweep.scale") for item in sweep["scales"]]
    if actual_scales != declared_scales or actual_scales != sorted(set(actual_scales)):
        raise ValidationFailure("amplitude sweep scale set/order mismatch")
    passing = []
    for item in sweep["scales"]:
        expected_status = "PASS" if _all_true(item["checks"].values()) else "FAIL"
        if item["status"] != expected_status:
            raise ValidationFailure("amplitude sweep status contradicts hard gates")
        if expected_status == "PASS":
            passing.append(float(item["scale"]))
    if not passing:
        raise ValidationFailure("amplitude sweep has no passing candidate")
    winner = max(passing)
    selected_scale = _finite(evidence["selectedScale"], "selectedScale")
    _same(sweep["selectedScale"], winner, "sweep.selectedScale")
    _same(selected_scale, winner, "evaluation.selectedScale")
    selected = next(item for item in sweep["scales"] if float(item["scale"]) == winner)
    if selected["sha256"] != candidate_sha:
        raise ValidationFailure("selected sweep artifact does not match candidate")
    ownership = _validate_layer_metrics(resolved, layer_metrics, selected_scale)

    metric_pairs = {
        "pelvisP2PByHipHeight.lateral": "pelvisTranslation.lateral_x",
        "pelvisP2PByHipHeight.vertical": "pelvisTranslation.vertical_y",
        "pelvisP2PByHipHeight.sagittal": "pelvisTranslation.sagittal_z",
        "pelvisRotationP2PDegrees.pitch": "pelvisRotation.pitch_x",
        "pelvisRotationP2PDegrees.yaw": "pelvisRotation.yaw_y",
        "pelvisRotationP2PDegrees.roll": "pelvisRotation.roll_z",
        "chestRelativeP2PDegrees.pitch": "chest.pitch_x",
        "chestRelativeP2PDegrees.yaw": "chest.yaw_y",
        "chestRelativeP2PDegrees.roll": "chest.roll_z",
        "tailYawP2PDegrees.base": "tailYaw.base",
        "tailYawP2PDegrees.mid": "tailYaw.mid",
        "tailYawP2PDegrees.tip": "tailYaw.tip",
        "headWorldP2PDegrees.pitch": "head.pitch_x",
        "headWorldP2PDegrees.yaw": "head.yaw_y",
        "headWorldP2PDegrees.roll": "head.roll_z",
        "chestPelvisRollPearson": "corr",
        "maxFootWorldErrorMetres": "maxFootWorldErrorM",
        "maxUpperAdjacentDeltaDegrees": "worstAdjacent",
        "maxUpperSecondDifferenceDegrees": "worstSecond",
    }
    metrics = evidence["metrics"]
    for output_selector, sweep_selector in metric_pairs.items():
        _same(_walk(metrics, output_selector), _walk(selected["metrics"], sweep_selector), output_selector)
    _bounded(metrics["pelvisP2PByHipHeight"]["lateral"], thresholds["pelvisProgression"]["lateralP2PByHipHeight"], "pelvis lateral")
    _bounded(metrics["pelvisP2PByHipHeight"]["vertical"], thresholds["pelvisProgression"]["verticalP2PByHipHeight"], "pelvis vertical")
    _bounded(metrics["pelvisRotationP2PDegrees"]["roll"], thresholds["pelvisProgression"]["rollP2PDegrees"], "pelvis roll")
    for axis, value in metrics["headWorldP2PDegrees"].items():
        if _finite(value, f"head.{axis}") > _finite(thresholds["upperBodyCounterbalanceAndSeam"]["headWorldP2PDegreesMax"][axis], f"head limit.{axis}"):
            raise ValidationFailure(f"head {axis} exceeds normative maximum")
    _same(metrics["strideMetres"], thresholds["v8_2Baseline"]["strideMetres"], "stride", 1e-6)
    _same(metrics["speedKilometresPerHour"], thresholds["v8_2Baseline"]["speedKilometresPerHour"], "speed", 1e-6)

    if witnesses["status"] != "PASS":
        raise ValidationFailure("final-skinned witness status is not PASS")
    if witnesses["baseline"]["samples"] != witnesses["candidate"]["samples"] or witnesses["denseSamples"] != witnesses["baseline"]["samples"]:
        raise ValidationFailure("final-skinned witness sample counts mismatch")
    if witnesses["baseline"]["meshVertices"] != witnesses["candidate"]["meshVertices"]:
        raise ValidationFailure("final-skinned mesh vertex counts mismatch")
    axis_max = max(_finite(value, "final-skinned axis") for value in witnesses["maxAxisRegressionMetres"].values())
    euclidean = _finite(witnesses["maxEuclideanRegressionMetres"], "final-skinned Euclidean")
    contact_limits = thresholds["finalSkinnedContactAndTrajectory"]
    _same(witnesses["thresholds"]["worstAxisMetresMax"], contact_limits["phaseMatchedV8_2TrajectoryWorstAxisRegressionMetresMax"], "witness axis threshold")
    _same(witnesses["thresholds"]["euclideanMetresMax"], contact_limits["phaseMatchedV8_2TrajectoryEuclideanRegressionMetresMax"], "witness Euclidean threshold")
    if axis_max > float(witnesses["thresholds"]["worstAxisMetresMax"]) or euclidean > float(witnesses["thresholds"]["euclideanMetresMax"]):
        raise ValidationFailure("final-skinned witness regression exceeds threshold")
    _same(metrics["finalSkinnedMaxAxisRegressionMetres"], axis_max, "final-skinned axis metric")
    _same(metrics["finalSkinnedMaxEuclideanRegressionMetres"], euclidean, "final-skinned Euclidean metric")
    _same(metrics["finalSkinnedDenseSamples"], witnesses["denseSamples"], "final-skinned sample metric")

    bundle_path = resolved.contact_evidence_path.parent.parent / "evidence.json"
    media_facts: dict[str, Any] = {"status": "NOT_DECLARED"}
    if bundle_path.is_file():
        bundle = _load_json(bundle_path, "evidence bundle")
        if _reference(resolved.repository, bundle["evidence"]["machineEvaluation"], "machine evaluation") != resolved.contact_evidence_path:
            raise ValidationFailure("evidence bundle machine report binding mismatch")
        media_path = _reference(resolved.repository, bundle["evidence"]["mediaManifest"], "media manifest")
        media = _load_json(media_path, "media manifest")
        if media.get("status") != "PASS":
            raise ValidationFailure("media manifest status is not PASS")
        for relative, digest in media.get("videos", {}).items():
            path = resolved.contact_evidence_path.parent.parent / "media" / relative
            if sha256_file(path) != digest:
                raise ValidationFailure(f"media hash mismatch: {relative}")
        review = _reference(resolved.repository, media["reviewPage"]["path"], "review page")
        if sha256_file(review) != media["reviewPage"]["sha256"]:
            raise ValidationFailure("review page hash mismatch")
        media_facts = {"status": "PASS", "manifestSha256": sha256_file(media_path), "reviewSha256": sha256_file(review)}

    return {
        "status": "PASS",
        "candidate": {"path": str(candidate_path), "sha256": candidate_sha},
        "baselineSha256": resolved.input_sha256,
        "selectedScale": selected_scale,
        "thresholds": {"path": str(threshold_path), "sha256": sha256_file(threshold_path)},
        "sweep": {"path": str(sweep_path), "sha256": sha256_file(sweep_path), "winner": winner},
        "layerMetrics": {"path": str(layer_path), "sha256": sha256_file(layer_path), **ownership},
        "finalSkinnedWitnesses": {"path": str(witness_path), "sha256": sha256_file(witness_path), "denseSamples": witnesses["denseSamples"]},
        "media": media_facts,
    }
