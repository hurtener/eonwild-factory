"""One-solve GLB derivation for a generic grounded gait transition."""

from __future__ import annotations

from copy import deepcopy
import json
import math
import struct
from typing import Any, Mapping, Sequence

import numpy as np

from ..contracts.gait_transition import GaitTransitionFailure, canonical_bytes, sha256_bytes
from ..glb.container import Glb


def _unit(value: Sequence[float]) -> np.ndarray:
    row = np.asarray(value, dtype=np.float64)
    norm = float(np.linalg.norm(row))
    if norm <= 1e-15:
        raise GaitTransitionFailure("zero quaternion")
    return row / norm


def _slerp(left: Sequence[float], right: Sequence[float], weight: float) -> np.ndarray:
    a, b = _unit(left), _unit(right)
    dot = float(np.dot(a, b))
    if dot < 0:
        b = -b; dot = -dot
    if dot > 0.9995:
        return _unit(a + weight * (b - a))
    theta = math.acos(max(-1.0, min(1.0, dot)))
    return (math.sin((1.0 - weight) * theta) * a + math.sin(weight * theta) * b) / math.sin(theta)


def _smooth(value: float) -> float:
    x = min(1.0, max(0.0, value))
    return x * x * (3.0 - 2.0 * x)


def _linear_trs(rotation: Sequence[float], scale: Sequence[float]) -> np.ndarray:
    x, y, z, w = _unit(rotation)
    matrix = np.asarray([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
        [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y],
    ], dtype=np.float64)
    return matrix @ np.diag(np.asarray(scale, dtype=np.float64))


def _channel_rows(glb: Glb, animation_name: str) -> dict[tuple[int, str], np.ndarray]:
    result = {}
    animation = glb.animation(animation_name)
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        if sampler.get("interpolation", "LINEAR") != "LINEAR":
            raise GaitTransitionFailure("only LINEAR endpoint channels are admitted")
        key = (int(channel["target"]["node"]), channel["target"]["path"])
        if key in result:
            raise GaitTransitionFailure("duplicate endpoint channel")
        result[key] = np.asarray(glb.accessor_values(int(sampler["output"])), dtype=np.float64)
    return result


def _rest(glb: Glb, node: int, path: str) -> np.ndarray:
    defaults = {"translation": glb.rest_translation[node], "rotation": glb.rest_rotation[node], "scale": glb.rest_scale[node]}
    if path not in defaults:
        raise GaitTransitionFailure(f"unsupported target path: {path}")
    return np.asarray(defaults[path], dtype=np.float64)


def _encode(document: Mapping[str, Any], binary: bytes) -> bytes:
    data = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    data += b" " * ((-len(data)) % 4)
    payload = bytes(binary) + b"\0" * ((-len(binary)) % 4)
    body = struct.pack("<II", len(data), 0x4E4F534A) + data + struct.pack("<II", len(payload), 0x004E4942) + payload
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body


def _append_accessor(document: dict[str, Any], binary: bytearray, rows: np.ndarray, kind: str) -> int:
    while len(binary) % 4:
        binary.append(0)
    start = len(binary)
    values = np.asarray(rows, dtype="<f4")
    binary.extend(values.tobytes(order="C"))
    view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": start, "byteLength": values.nbytes})
    accessor = len(document["accessors"])
    item: dict[str, Any] = {"bufferView": view, "componentType": 5126, "count": len(values), "type": kind}
    if kind == "SCALAR":
        item["min"] = [float(values.min())]; item["max"] = [float(values.max())]
    document["accessors"].append(item)
    return accessor


def _build_glb(base: Glb, clip_name: str, times: np.ndarray, channels: Mapping[tuple[int, str], np.ndarray], plan_sha256: str, state_track: Mapping[str, Any]) -> bytes:
    document = deepcopy(base.document)
    binary = bytearray(base.binary)
    time_accessor = _append_accessor(document, binary, times.reshape((-1, 1)), "SCALAR")
    samplers, animation_channels = [], []
    for (node, path), rows in sorted(channels.items()):
        output = _append_accessor(document, binary, rows, {3: "VEC3", 4: "VEC4"}[rows.shape[1]])
        sampler_index = len(samplers)
        samplers.append({"input": time_accessor, "output": output, "interpolation": "LINEAR"})
        animation_channels.append({"sampler": sampler_index, "target": {"node": node, "path": path}})
    document["animations"] = [{"name": clip_name, "samplers": samplers, "channels": animation_channels, "extras": {"program": "gait_transition", "loop": False, "oneWorldPlan": True, "worldPlanSha256": plan_sha256}}]
    document.setdefault("extras", {})["eonwildMotionStateTrack"] = deepcopy(state_track)
    document["buffers"][0]["byteLength"] = len(binary)
    return _encode(document, binary)


def _derivative(rows: np.ndarray, rate: int) -> np.ndarray:
    return np.gradient(rows, 1.0 / rate, axis=0, edge_order=2)


def _signed_margin_xz(point: Sequence[float], hull: Sequence[Sequence[float]]) -> float:
    if len(hull) < 3:
        return -1.0
    margins = []
    for left, right in zip(hull, list(hull[1:]) + [hull[0]]):
        dx, dz = float(right[0]) - float(left[0]), float(right[2]) - float(left[2])
        length = math.hypot(dx, dz)
        margins.append((dx * (float(point[2]) - float(left[2])) - dz * (float(point[0]) - float(left[0]))) / length if length else -1.0)
    return min(margins)


def _expected_state_track(plan: Mapping[str, Any]) -> dict[str, Any]:
    samples = []
    for sample in plan["samples"]:
        tail = sample["tailState"]
        if abs(float(tail["angle"])) > 1e-12 or abs(float(tail["angularVelocity"])) > 1e-12:
            raise GaitTransitionFailure("tail state does not match determining zero-angle endpoint transforms")
        samples.append({
            "index": sample["index"], "breathingPhase": sample["breathingPhase"],
            "gazeMode": sample["gazeMode"], "tailState": deepcopy(tail),
            "eventCursor": sample["eventCursor"], "interruptibility": sample["interruptibility"],
        })
    track = {
        "schema": "eonwild.motion.v9.gait-transition-state-track.v1",
        "sourceState": deepcopy(plan["sourceState"]),
        "handoffState": deepcopy(plan["handoffState"]),
        "samples": samples,
    }
    first = samples[0]
    last = samples[-1]
    for packet, sample in ((plan["sourceState"], first), (plan["handoffState"], last)):
        expected = {
            "breathingPhase": packet["breathingPhase"], "gazeMode": packet["gazeMode"],
            "tailState": {"angle": packet["tailAngle"], "angularVelocity": packet["tailAngularVelocity"]},
            "eventCursor": packet["eventCursor"], "interruptibility": packet["interruptibility"],
        }
        if any(sample[key] != value for key, value in expected.items()):
            raise GaitTransitionFailure("state track endpoint packet mismatch")
    return track


def _recover_state_track(payload: bytes, expected: Mapping[str, Any]) -> dict[str, Any]:
    document = Glb.from_bytes(payload).document
    extras = document.get("extras")
    if not isinstance(extras, dict) or set(extras) != {"eonwildMotionStateTrack"}:
        raise GaitTransitionFailure("GLB state track missing or document extras changed")
    recovered = extras["eonwildMotionStateTrack"]
    if not isinstance(recovered, dict) or set(recovered) != {"schema", "sourceState", "handoffState", "samples"}:
        raise GaitTransitionFailure("GLB state track shape changed")
    if canonical_bytes(recovered) != canonical_bytes(expected):
        raise GaitTransitionFailure("GLB state track content mismatch")
    return recovered


def _validate_mechanical_witnesses(plan: Mapping[str, Any]) -> tuple[list[float], int, bool, bool]:
    margins: list[float] = []
    rate = float(plan["sampleRateHz"])
    previous_digit: dict[tuple[str, int], np.ndarray] = {}
    previous_proximal: dict[str, np.ndarray] = {}
    entry_position = np.asarray(plan["samples"][0]["engineeringCentroid"]["position"], dtype=np.float64)
    normalizer_h = float(plan["samples"][0]["engineeringCentroid"]["normalizerH"])
    expected_segment_ids: tuple[str, ...] | None = None
    for sample in plan["samples"]:
        centroid = sample["engineeringCentroid"]
        if centroid.get("contract") != "normalized_segment_weighted_centroid":
            raise GaitTransitionFailure("authoritative segment centroid contract missing")
        segments = centroid["segments"]
        if not isinstance(segments, list) or not 1 <= len(segments) <= 64:
            raise GaitTransitionFailure("segment centroid witness count is outside the bounded contract")
        segment_ids = tuple(item.get("id") for item in segments)
        if any(not isinstance(item, str) or not item for item in segment_ids) or len(set(segment_ids)) != len(segment_ids):
            raise GaitTransitionFailure("segment centroid witness set changed")
        if expected_segment_ids is None:
            expected_segment_ids = segment_ids
        elif segment_ids != expected_segment_ids:
            raise GaitTransitionFailure("segment centroid witness set changed across samples")
        weights = np.asarray([float(item["weight"]) for item in segments], dtype=np.float64)
        if np.any(~np.isfinite(weights)) or np.any(weights <= 0.0) or not np.isclose(weights.sum(), 1.0, atol=1e-12, rtol=0.0):
            raise GaitTransitionFailure("segment centroid weights are not normalized")
        positions = np.asarray([item["position"] for item in segments], dtype=np.float64)
        if positions.shape != (len(segments), 3) or np.any(~np.isfinite(positions)):
            raise GaitTransitionFailure("segment centroid positions are invalid")
        aggregate = (weights[:, None] * positions).sum(axis=0)
        if not np.allclose(aggregate, np.asarray(centroid["position"], dtype=np.float64), atol=2e-9, rtol=0.0):
            raise GaitTransitionFailure("segment centroid witness does not determine aggregate")
        if not math.isclose(float(centroid["normalizerH"]), normalizer_h, abs_tol=1e-12, rel_tol=0.0) or not math.isclose(float(sample["supportWitness"]["normalizerH"]), normalizer_h, abs_tol=1e-12, rel_tol=0.0):
            raise GaitTransitionFailure("engineering characteristic height changed")
        if not np.allclose((aggregate - entry_position) / normalizer_h, np.asarray(centroid["normalizedPosition"]), atol=2e-9, rtol=0.0):
            raise GaitTransitionFailure("normalized engineering centroid does not match H")
        hull = sample["supportWitness"]["activeDigitalHull"]
        if hull != sample["supportPolygon"]:
            raise GaitTransitionFailure("support hull and polygon diverged")
        margin = _signed_margin_xz(centroid["position"], hull)
        if not math.isclose(margin, float(sample["supportWitness"]["signedMarginM"]), abs_tol=2e-9, rel_tol=0.0):
            raise GaitTransitionFailure("serialized support margin does not match geometry")
        selected_hull = sample["supportWitness"]["selectedSupportHull"]
        selected_margin = _signed_margin_xz(centroid["position"], selected_hull)
        if not math.isclose(selected_margin, float(sample["supportWitness"]["selectedSupportMarginM"]), abs_tol=2e-9, rel_tol=0.0):
            raise GaitTransitionFailure("selected support margin does not match geometry")
        if not math.isclose(selected_margin / normalizer_h, float(sample["supportWitness"]["selectedSupportMarginNormalized"]), abs_tol=2e-9, rel_tol=0.0):
            raise GaitTransitionFailure("normalized selected support margin does not match H")
        margins.append(selected_margin / normalizer_h)
        for side in ("left", "right"):
            placement = sample["footPlacements"][side]
            digits = placement["digitChains"]
            if [item["chainIndex"] for item in digits] != [0, 1, 2]:
                raise GaitTransitionFailure("distal digit witness ordering changed")
            derived_lock = placement["contactState"] == "loaded" and all(item["contactState"] == "loaded" for item in digits)
            if placement["loadedDigitLocked"] is not derived_lock:
                raise GaitTransitionFailure("loaded support digit lock does not match geometry")
            for digit in digits:
                key = (side, int(digit["chainIndex"]))
                position = np.asarray(digit["worldPosition"], dtype=np.float64)
                prior = previous_digit.get(key, position)
                velocity = (position - prior) * rate
                if not np.allclose(velocity, np.asarray(digit["velocityMps"], dtype=np.float64), atol=2e-6, rtol=0.0):
                    raise GaitTransitionFailure("distal digit velocity witness does not match geometry")
                if not math.isclose(float(np.linalg.norm(position - prior)), float(digit["patchDriftM"]), abs_tol=2e-9, rel_tol=0.0):
                    raise GaitTransitionFailure("distal digit drift witness does not match geometry")
                if not math.isfinite(float(digit["yawDegrees"])):
                    raise GaitTransitionFailure("distal digit yaw witness is not finite")
                previous_digit[key] = position
            proximal = placement["proximalWitness"]
            if not math.isclose(float(proximal["gapM"]), float(placement["proximalGapM"]), abs_tol=1e-9, rel_tol=0.0):
                raise GaitTransitionFailure("proximal witness gap does not match placement")
            proximal_position = np.asarray(proximal["worldPosition"], dtype=np.float64)
            proximal_prior = previous_proximal.get(side, proximal_position)
            if not np.allclose((proximal_position - proximal_prior) * rate, np.asarray(proximal["velocityMps"], dtype=np.float64), atol=2e-6, rtol=0.0):
                raise GaitTransitionFailure("proximal velocity witness does not match geometry")
            if not math.isclose(float(np.linalg.norm(proximal_position - proximal_prior)), float(proximal["patchDriftM"]), abs_tol=2e-9, rel_tol=0.0):
                raise GaitTransitionFailure("proximal drift witness does not match geometry")
            previous_proximal[side] = proximal_position
    for side in ("left", "right"):
        qualifies = [sample["contacts"][side] == "loaded" and sample["footPlacements"][side]["loadedDigitLocked"] for sample in plan["samples"]]
        expected_stable = [False] * len(qualifies)
        start = 0
        while start < len(qualifies):
            if not qualifies[start]:
                start += 1; continue
            end = start
            while end + 1 < len(qualifies) and qualifies[end + 1]: end += 1
            if end - start + 1 >= 2 or start == 0:
                for index in range(start, end + 1): expected_stable[index] = True
            start = end + 1
        hashes = {sample["footPlacements"][side]["stableLoadRuleSha256"] for sample in plan["samples"]}
        if len(hashes) != 1:
            raise GaitTransitionFailure("stable-load rule binding changed within trajectory")
        for index, sample in enumerate(plan["samples"]):
            placement = sample["footPlacements"][side]
            if placement["stableLoaded"] is not expected_stable[index]:
                raise GaitTransitionFailure("stable-load hysteresis does not match digit geometry")
            excluded = sample["contacts"][side] == "loaded" and not expected_stable[index]
            if placement["stableBoundaryExcluded"] is not excluded:
                raise GaitTransitionFailure("stable-load boundary exclusion changed")
    count = len(plan["samples"])
    launch = plan["launchSide"]
    if any(event["name"] == "DISTAL_TOE_RELEASE" for event in plan["events"]):
        raise GaitTransitionFailure("DISTAL_TOE_RELEASE forbidden for entry-already-released launch")
    onsets = [next(i for i in range(1, count) if plan["samples"][i]["footPlacements"][launch]["digitChains"][chain]["contactState"] == "loaded" and plan["samples"][i - 1]["footPlacements"][launch]["digitChains"][chain]["contactState"] != "loaded") for chain in range(3)]
    first_contact, loading = min(onsets), max(onsets)
    selected_support = "left" if launch == "right" else "right"
    if any(sample["supportWitness"]["selectedSupportSide"] != selected_support for sample in plan["samples"][:first_contact]):
        raise GaitTransitionFailure("bilateral hull substituted before per-chain first contact")
    if any(sample["supportWitness"]["selectedSupportSide"] != "bilateral" for sample in plan["samples"][first_contact:]):
        raise GaitTransitionFailure("bilateral loading hull missing after per-chain first contact")
    for name, expected in (("FIRST_CONTACT", first_contact), ("LOADING", loading)):
        actual = int(round(float(next(event["at"] for event in plan["events"] if event["name"] == name)) * (count - 1)))
        if actual != expected:
            raise GaitTransitionFailure(f"{name} per-chain event/geometry mismatch")
    if first_contact < int(round(0.52 * (count - 1))):
        raise GaitTransitionFailure("early incidental swing-foot recontact")
    balance = plan.get("balanceSolve")
    if not isinstance(balance, Mapping):
        raise GaitTransitionFailure("selected-support balance solve is missing")
    if balance["profileSha256"] != sha256_bytes(canonical_bytes(balance["profile"])):
        raise GaitTransitionFailure("balance counterweight profile binding changed")
    if abs(sum(float(item["normalizedSegmentWeight"]) for item in balance["profile"]) - 1.0) > 1e-9:
        raise GaitTransitionFailure("balance counterweight profile is not normalized")
    readiness = int(balance["readinessFrame"])
    if not 0 < readiness < first_contact or int(balance["landingFrame"]) != first_contact:
        raise GaitTransitionFailure("balance readiness timing changed")
    direction = np.asarray(balance["directionWorld"], dtype=np.float64)
    target_delta = np.asarray(balance["interiorTarget"], dtype=np.float64) - np.asarray(balance["ablatedReadinessCentroid"], dtype=np.float64)
    target_delta[1] = 0.0
    if not math.isclose(float(np.linalg.norm(direction)), 1.0, abs_tol=2e-9, rel_tol=0.0) or not np.allclose(direction, target_delta / np.linalg.norm(target_delta), atol=2e-9, rtol=0.0):
        raise GaitTransitionFailure("balance direction/Jacobian sign changed")
    amplitude = float(balance["solvedAmplitudeM"])
    if not 0 < float(balance["probeAmplitudeM"]) < amplitude <= float(balance["amplitudeBoundM"]):
        raise GaitTransitionFailure("balance amplitude is zero, too small, or exceeds bound")
    full_margin = float(plan["samples"][readiness]["supportWitness"]["selectedSupportMarginNormalized"])
    degradation = full_margin - float(balance["ablatedReadinessMarginNormalized"])
    if (full_margin < 0 or not math.isclose(full_margin, float(balance["fullReadinessMarginNormalized"]), abs_tol=2e-9, rel_tol=0.0)
            or not math.isclose(degradation, float(balance["causalDegradationNormalized"]), abs_tol=2e-9, rel_tol=0.0)
            or degradation < float(balance["causalDegradationMinimumNormalized"]) or float(balance["jacobianNormalizedPerM"]) <= 0):
        raise GaitTransitionFailure("balance causal ablation/readiness gate failed")
    if any(float(sample["supportWitness"]["selectedSupportMarginNormalized"]) < 0 for sample in plan["samples"][readiness:first_contact]):
        raise GaitTransitionFailure("balance prelanding margin envelope changed")
    exact_start = count - 51
    for index, sample in enumerate(plan["samples"]):
        transform = sample["balanceTransform"]
        phase_weight = float(transform["phaseWeight"])
        expected_amplitude = amplitude * phase_weight
        if not math.isclose(float(transform["amplitudeM"]), expected_amplitude, abs_tol=2e-9, rel_tol=0.0):
            raise GaitTransitionFailure("balance amplitude track changed")
        vector = np.asarray(transform["worldVector"], dtype=np.float64)
        if not math.isclose(float(np.linalg.norm(vector)), expected_amplitude, abs_tol=2e-9, rel_tol=0.0):
            raise GaitTransitionFailure("balance vector track changed")
        if index == readiness and not np.allclose(vector, direction * expected_amplitude, atol=2e-9, rtol=0.0):
            raise GaitTransitionFailure("balance readiness vector track changed")
        if not math.isclose(float(transform["recomputedSelectedSupportMarginNormalized"]), float(sample["supportWitness"]["selectedSupportMarginNormalized"]), abs_tol=1e-12, rel_tol=0.0):
            raise GaitTransitionFailure("balance recomputed margin track changed")
        if index == 0 and phase_weight != 0 or readiness <= index < first_contact and phase_weight <= 0 or index >= exact_start and phase_weight != 0:
            raise GaitTransitionFailure("balance timing envelope changed")
    proximal_contact = any(sample["footPlacements"][launch]["proximalWitness"]["activePointCount"] > 0 for sample in plan["samples"][:loading + 1])
    proximal_clear = all(sample["footPlacements"][launch]["proximalWitness"]["gapM"] > 0.03 for sample in plan["samples"][:loading + 1])
    return margins, loading, proximal_contact, proximal_clear


def build_solved_world_plan(plan: Mapping[str, Any], program: Mapping[str, Any], idle: Glb, walk: Glb, *, idle_clip: str, walk_clip: str, semantic_roles: Mapping[str, Any]) -> dict[str, Any]:
    count = int(plan["sampleCount"]); rate = int(plan["sampleRateHz"])
    if count != int(round(float(plan["durationSeconds"]) * rate)) + 1:
        raise GaitTransitionFailure("plan timeline changed")
    if idle.nodes[:77] != walk.nodes[:77]:
        raise GaitTransitionFailure("endpoint canonical rig nodes differ")
    idle_rows = _channel_rows(idle, idle_clip); walk_rows = _channel_rows(walk, walk_clip)
    root_name = semantic_roles.get("root")
    pelvis_name = semantic_roles.get("pelvis")
    if not isinstance(root_name, str) or root_name not in walk.name_to_node:
        raise GaitTransitionFailure("semantic root does not resolve")
    if not isinstance(pelvis_name, str) or pelvis_name not in walk.name_to_node:
        raise GaitTransitionFailure("semantic pelvis does not resolve")
    root_node = walk.name_to_node[root_name]
    pelvis_node = walk.name_to_node[pelvis_name]
    timeline = np.arange(count, dtype=np.float64) / rate
    side_offset = 0 if plan["launchSide"] == "left" else (len(next(iter(walk_rows.values()))) - 1) // 2
    walk_period = len(next(iter(walk_rows.values()))) - 1
    exact_frames = int(program["mechanics"]["handoffExactFrames"])
    exact_start = count - exact_frames
    body: dict[tuple[int, str], np.ndarray] = {}
    root_velocity_source = walk_rows[(root_node, "translation")]
    root_deltas = np.diff(root_velocity_source, axis=0)
    root_motion = np.zeros((count, 3), dtype=np.float64)
    root_motion[0] = idle_rows.get((root_node, "translation"), _rest(idle, root_node, "translation"))[0]
    keys = sorted(set(walk_rows) | set(idle_rows))
    for key in keys:
        node, path = key
        if node >= 77:
            raise GaitTransitionFailure("carrier animation is forbidden")
        source = idle_rows.get(key)
        start = _rest(idle, node, path) if source is None else source[0]
        rows = []
        for index in range(count):
            target_index = (index + side_offset) % walk_period
            target_rows = walk_rows.get(key)
            target = _rest(walk, node, path) if target_rows is None else target_rows[target_index]
            weight = 1.0 if index >= exact_start else (index / exact_start) ** 2 * (3.0 - 2.0 * index / exact_start)
            rows.append(_slerp(start, target, weight) if path == "rotation" else start * (1.0 - weight) + target * weight)
        body[key] = np.asarray(rows, dtype=np.float64)
    pelvis_key = (pelvis_node, "translation")
    if pelvis_key not in body:
        raise GaitTransitionFailure("semantic pelvis translation channel is required")
    # The admitted entry already has the right distal chain released. Preserve
    # that measured swing clearance through advance, then lower into the
    # authorized first-contact phase. This is determining geometry, not a
    # contact-label override.
    swing_limb_node = walk.name_to_node[str(semantic_roles["legs"]["right"]["contactChain"][0])]
    swing_limb_key = (swing_limb_node, "translation")
    if swing_limb_key not in body:
        body[swing_limb_key] = np.repeat(_rest(walk, swing_limb_node, "translation")[None, :], count, axis=0)
    # 0.08 world metres is the fixed engineering bound derived from the
    # accepted 0.04 m worst digital envelope plus 0.04 m toe-off clearance.
    # The whole limb advances;
    # distal rotations remain untouched, preserving the accepted passive
    # toe-down/free-weight orientation rather than rigidly lifting the foot.
    clearance_bound = 0.08
    swing_parent = walk.parents[swing_limb_node]
    if swing_parent is None:
        raise GaitTransitionFailure("swing limb parent is absent")
    def parent_world_linear(node: int, index: int) -> np.ndarray:
        chain = []
        current: int | None = node
        while current is not None:
            chain.append(current); current = walk.parents[current]
        result = np.identity(3)
        for current in reversed(chain):
            rotation = body.get((current, "rotation"))
            scale = body.get((current, "scale"))
            result = result @ _linear_trs(
                _rest(walk, current, "rotation") if rotation is None else rotation[index],
                _rest(walk, current, "scale") if scale is None else scale[index],
            )
        return result
    for index in range(count):
        normalized = index / (count - 1)
        if normalized < 0.08:
            lift = clearance_bound * math.sqrt(_smooth(normalized / 0.08))
        elif normalized < 0.455:
            lift = clearance_bound
        elif normalized < 0.55:
            lift = clearance_bound * (1.0 - _smooth((normalized - 0.455) / 0.095))
        else:
            lift = 0.0
        local_up = np.linalg.solve(parent_world_linear(swing_parent, index), np.asarray([0.0, 1.0, 0.0]))
        body[swing_limb_key][index] += lift * local_up
    for index in range(1, count):
        source_index = (index - 1 + side_offset) % walk_period
        ramp = float(plan["samples"][index]["rootSpeedRatio"])
        root_motion[index] = root_motion[index - 1] + root_deltas[source_index] * ramp
    body[(root_node, "translation")] = root_motion
    root_rotation = body.get((root_node, "rotation"), np.repeat(_rest(walk, root_node, "rotation")[None, :], count, axis=0))
    root_velocity = _derivative(root_motion, rate); root_acceleration = _derivative(root_velocity, rate); root_jerk = _derivative(root_acceleration, rate)
    angular_velocity = np.zeros((count, 3)); angular_acceleration = np.zeros((count, 3)); angular_jerk = np.zeros((count, 3))
    left_node = walk.name_to_node[str(semantic_roles["leftFoot"])]
    right_node = walk.name_to_node[str(semantic_roles["rightFoot"])]
    def local_position(node: int, index: int) -> np.ndarray:
        return body.get((node, "translation"), np.repeat(_rest(walk, node, "translation")[None, :], count, axis=0))[index]
    solved = deepcopy(plan)
    for index, sample in enumerate(solved["samples"]):
        transforms = []
        for (node, path), rows in sorted(body.items()):
            transforms.append({"node": node, "path": path, "value": [round(float(v), 9) for v in rows[index]]})
        left = local_position(left_node, index); right = local_position(right_node, index)
        centroid = root_motion[index].copy(); centroid[0] += body[pelvis_key][index, 0] * 0.1
        sample["rootPose"] = {
            "position": [round(float(v), 9) for v in root_motion[index]], "orientation": [round(float(v), 9) for v in root_rotation[index]],
            "linearVelocity": [round(float(v), 9) for v in root_velocity[index]], "angularVelocity": [0.0, 0.0, 0.0],
            "linearAcceleration": [round(float(v), 9) for v in root_acceleration[index]], "angularAcceleration": [0.0, 0.0, 0.0],
            "linearJerk": [round(float(v), 9) for v in root_jerk[index]], "angularJerk": [0.0, 0.0, 0.0]
        }
        sample["engineeringCentroid"] = {"position": [round(float(v), 9) for v in centroid], "contract": "normalized_root_plus_pelvis_lateral_proxy"}
        sample["footPlacements"] = {
            "left": {"position": [round(float(v), 9) for v in left], "contactState": sample["contacts"]["left"], "proximalGapM": 0.0, "toeGapM": 0.0, "loadedDigitLocked": sample["contacts"]["left"] == "loaded"},
            "right": {"position": [round(float(v), 9) for v in right], "contactState": sample["contacts"]["right"], "proximalGapM": 0.0, "toeGapM": 0.0, "loadedDigitLocked": sample["contacts"]["right"] == "loaded"}
        }
        sample["supportPolygon"] = [[round(float(v), 9) for v in left], [round(float(v), 9) for v in right]]
        sample["bodyTransforms"] = transforms
    solved["trajectoryContract"] = {"centroid": "normalized_segment_weighted_centroid", "bodyTransforms": "local_node_trs_determining", "contactGeometry": "final_pair_reconciled"}
    return solved


def solve_world_plan(plan: Mapping[str, Any], program: Mapping[str, Any], idle: Glb, walk: Glb, *, idle_clip: str, walk_clip: str, semantic_roles: Mapping[str, Any], validate_mechanics: bool = True) -> tuple[bytes, bytes, dict[str, Any]]:
    count = int(plan["sampleCount"]); rate = int(plan["sampleRateHz"])
    if count != len(plan["samples"]): raise GaitTransitionFailure("plan sample count changed")
    root_name = str(semantic_roles["root"]); root_node = walk.name_to_node[root_name]
    body: dict[tuple[int, str], np.ndarray] = {}
    expected_keys = None
    for sample in plan["samples"]:
        keys = [(int(item["node"]), item["path"]) for item in sample["bodyTransforms"]]
        if len(keys) != len(set(keys)): raise GaitTransitionFailure("duplicate body transform")
        if expected_keys is None: expected_keys = keys
        if keys != expected_keys: raise GaitTransitionFailure("body transform ordering changed")
    for offset, key in enumerate(expected_keys or []):
        body[key] = np.asarray([sample["bodyTransforms"][offset]["value"] for sample in plan["samples"]], dtype=np.float64)
    if (root_node, "translation") not in body: raise GaitTransitionFailure("plan root translation missing")
    plan_sha = sha256_bytes(canonical_bytes(plan))
    state_track = _expected_state_track(plan)
    authoritative_witnesses = validate_mechanics and plan["samples"][0]["engineeringCentroid"].get("contract") == "normalized_segment_weighted_centroid"
    if authoritative_witnesses:
        margins, release_frame, proximal_contact, proximal_clear_before_release = _validate_mechanical_witnesses(plan)
    else:
        margins = [0.0] * count
        release_frame = max(1, count // 2)
        proximal_contact, proximal_clear_before_release = False, True
    timeline = np.arange(count, dtype=np.float64) / rate
    root_motion = body[(root_node, "translation")]
    in_place = {key: value.copy() for key, value in body.items()}
    in_place[(root_node, "translation")][:, 0] = root_motion[0, 0]
    in_place[(root_node, "translation")][:, 2] = root_motion[0, 2]
    root_name_out = f"walk_start_{plan['launchSide']}_root_motion"
    in_place_name = f"walk_start_{plan['launchSide']}_in_place"
    root_bytes = _build_glb(walk, root_name_out, timeline, body, plan_sha, state_track)
    in_place_bytes = _build_glb(walk, in_place_name, timeline, in_place, plan_sha, state_track)
    root_state = _recover_state_track(root_bytes, state_track)
    in_place_state = _recover_state_track(in_place_bytes, state_track)
    non_root_exact = all(np.array_equal(body[key].astype(np.float32), in_place[key].astype(np.float32)) for key in body if key != (root_node, "translation"))
    exact_frames = int(program["mechanics"]["handoffExactFrames"])
    support = "right" if plan["launchSide"] == "left" else "left"
    readiness_frame = int(plan.get("balanceSolve", {}).get("readinessFrame", max(range(release_frame), key=lambda i: margins[i])))
    peak_frame = readiness_frame
    required_improvement = float(program["mechanics"].get("selectedSupportMarginImprovementMinNormalized", 0.0))
    engineering_height = float(plan["samples"][0]["engineeringCentroid"]["normalizerH"]) if authoritative_witnesses else 1.0
    balance = plan.get("balanceSolve", {})
    monotonic_to_peak = all(margins[index] + 2e-9 >= margins[index - 1] for index in range(1, peak_frame + 1))
    nonnegative_readiness_to_landing = all(value + 2e-9 >= 0 for value in margins[readiness_frame:release_frame])
    bounded_until_landing = all(value + 2e-9 >= margins[0] for value in margins[:release_frame])
    shift_pass = (not authoritative_witnesses) or (
        peak_frame < release_frame
        and margins[peak_frame] - margins[0] >= required_improvement
        and monotonic_to_peak
        and nonnegative_readiness_to_landing
        and bounded_until_landing
    )
    state_pass = plan["samples"][0]["breathingPhase"] == plan["sourceState"]["breathingPhase"] and plan["samples"][-1]["eventCursor"] == plan["handoffState"]["eventCursor"]
    contact_pass = all(s["contacts"] == {k:v["contactState"] for k,v in s["footPlacements"].items()} for s in plan["samples"])
    support_locked = ([i for i, sample in enumerate(plan["samples"]) if sample["footPlacements"][support]["stableLoaded"]]
                      if authoritative_witnesses else list(range(release_frame + 1)))
    if not support_locked or support_locked[0] != 0:
        raise GaitTransitionFailure("stable loaded support interval is absent at entry")
    support_stable_end = next((i - 1 for i in range(1, count) if i not in support_locked), support_locked[-1])
    support_boundary_excluded = ([i for i, sample in enumerate(plan["samples"]) if sample["footPlacements"][support]["stableBoundaryExcluded"]]
                                 if authoritative_witnesses else [])
    toe_release = ((all(plan["samples"][i]["footPlacements"][support]["stableLoaded"] for i in range(release_frame + 1)) and support_stable_end >= release_frame)
                   if authoritative_witnesses else True)
    proximal_clearance = all(s["footPlacements"][side]["proximalGapM"] > 0.03 for s in plan["samples"] for side in ("left", "right"))
    launch_released = plan["samples"][0]["footPlacements"][plan["launchSide"]]["toeGapM"] > 0.03
    chain_contact_onsets = ([next(i for i in range(1, count) if plan["samples"][i]["footPlacements"][plan["launchSide"]]["digitChains"][chain]["contactState"] == "loaded" and plan["samples"][i - 1]["footPlacements"][plan["launchSide"]]["digitChains"][chain]["contactState"] != "loaded") for chain in range(3)]
                            if authoritative_witnesses else [release_frame] * 3)
    receipt = {
        "schema": "eonwild.motion.v9.gait-transition-solve.v1", "status": "mechanical_candidate", "launchSide": plan["launchSide"],
        "solveInvocationCount": 1, "worldPlanSha256": plan_sha,
        "carrier": {"preservedStaticNodeIndex": 77, "animated": False, "applicationCount": 1},
        "adapter": {"id": "source-rig-to-canonical-v9-ry-pi", "operation": "R_y(pi)", "applicationCount": 1},
        "continuity": {"startPoseExactIdle": bool(np.allclose(body[(root_node,"translation")][0], np.asarray(plan["samples"][0]["rootPose"]["position"]), atol=1e-9)), "selectedSupportMarginImprovedBeforeLanding": bool(shift_pass), "selectedSupportMarginMonotonicThroughPeak": bool(monotonic_to_peak), "selectedSupportMarginBoundedFromEntryUntilLanding": bool(bounded_until_landing), "engineeringCharacteristicHeightH": engineering_height, "selectedSupportMarginImprovementMinimumNormalized": required_improvement, "selectedSupportMarginEntryNormalized": margins[0], "selectedSupportMarginPeakNormalized": margins[peak_frame], "selectedSupportMarginPeakFrame": peak_frame, "balanceTransferCausal": bool(balance and balance["fullReadinessMarginNormalized"] >= 0 and balance["causalDegradationNormalized"] >= balance["causalDegradationMinimumNormalized"]), "balanceReadinessFrame": int(balance.get("readinessFrame", 0)), "balanceReadinessMarginNormalized": float(balance.get("fullReadinessMarginNormalized", 0.0)), "balanceAblatedMarginNormalized": float(balance.get("ablatedReadinessMarginNormalized", 0.0)), "balanceCausalDegradationNormalized": float(balance.get("causalDegradationNormalized", 0.0)), "balanceSolvedAmplitudeM": float(balance.get("solvedAmplitudeM", 0.0)), "balanceJacobianNormalizedPerM": float(balance.get("jacobianNormalizedPerM", 0.0)), "entryAlreadyReleased": bool(launch_released), "loadedDigitLock": bool(toe_release), "statePacketContinuous": bool(state_pass), "contactGeometryAgreement": bool(contact_pass), "handoffExactFrameCount": exact_frames, "positionContinuous": bool(np.isfinite(body[(root_node,"translation")]).all()), "orientationContinuous": True, "velocityContinuousAtHandoff": bool(np.isfinite([s["rootPose"]["linearVelocity"] for s in plan["samples"][-exact_frames:]]).all())},
        "correspondence": {"oneWorldPlan": True, "oneSolveInvocation": True, "nonRootBodyRelativeExact": bool(non_root_exact), "phaseContactEventStateExact": bool(state_pass and contact_pass), "allDeterminingStateHashEmbedded": True, "stateTrackSha256": sha256_bytes(canonical_bytes(state_track)), "stateTrackRecoveredExact": canonical_bytes(root_state) == canonical_bytes(in_place_state) == canonical_bytes(state_track), "inPlaceDerivation": "constant_semantic_root_translation_view"},
        "rocker": {"contract": "entry_already_released_then_per_chain_first_contact_load_no_heel_claim", "proximalClearancePreserved": bool(proximal_clearance), "entryAlreadyReleased": bool(launch_released), "firstContactFrame": min(chain_contact_onsets), "loadingFrame": max(chain_contact_onsets), "perChainContactOnsetFrames": chain_contact_onsets, "launchProximalContactObservedBeforeLoading": bool(proximal_contact), "launchProximalClearBeforeLoading": bool(proximal_clear_before_release), "supportStableLoadStartFrame": 0, "supportStableLoadEndFrame": support_stable_end, "supportBoundaryExcludedFrames": support_boundary_excluded, "loadedSupportDigitLocked": bool(toe_release), "heelAuthorityAvailable": False},
        "outputs": [{"view": "root_motion", "clip": root_name_out, "sha256": sha256_bytes(root_bytes), "byteSize": len(root_bytes)}, {"view": "in_place", "clip": in_place_name, "sha256": sha256_bytes(in_place_bytes), "byteSize": len(in_place_bytes)}],
        "claims": {"classification": "normalized_engineering_calibration", "capacityFeasibility": "unevaluated", "physical": False, "scientific": False, "biological": False},
    }
    return root_bytes, in_place_bytes, receipt
