from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from ..contracts.semantic import expanded_channels
from ..errors import MotionError, ValidationFailure
from ..glb.container import Glb
from ..hashing import sha256_file, write_json
from ..layers.registry import apply_registered_layer


def build_layered_bytes(base_glb: Glb, rig: dict, motion: dict, layers: list[dict]):
    glb = base_glb
    raw = bytearray(glb.raw)
    metrics = {}
    for layer in layers:
        patches, layer_metrics = apply_registered_layer(
            layer["implementation"], glb, base_glb, rig, motion, layer
        )
        allowed = expanded_channels(rig["roles"], layer["writes"])
        actual = {
            (node, property_name)
            for clip_patches in patches.values()
            for node, properties in clip_patches.items()
            for property_name in properties
        }
        if actual - allowed:
            raise ValidationFailure(
                f"layer attempted undeclared writes: {sorted(actual - allowed)}"
            )
        declared_clips = {clip["name"] for clip in motion["clips"]}
        if set(patches) != declared_clips:
            raise ValidationFailure("layer patch clip set differs from motion contract")
        for clip_name, clip_patches in patches.items():
            for node, properties in clip_patches.items():
              for property_name, patch in properties.items():
                expected_accessors = glb.animation_accessors(clip_name, property_name)
                accessor = int(patch["accessor"])
                if patch.get("property") != property_name or expected_accessors.get(node) != accessor:
                    raise ValidationFailure(
                        f"layer accessor does not own {clip_name}/{node}.{property_name}"
                    )
                offset, count, stride = glb.accessor_region(accessor)
                rows = patch["values"]
                width = 4 if property_name == "rotation" else 3
                row_bytes = width * 4
                if stride != row_bytes or rows.shape != (count, width):
                    raise ValidationFailure("patch accessor is not packed float animation data")
                start = glb.bin_start + offset
                raw[start:start + count * row_bytes] = rows.astype("<f4").tobytes()
        metrics[layer["implementation"]] = layer_metrics
        glb = Glb.from_bytes(bytes(raw))
    return bytes(raw), metrics


def execute_build_request(request_path: Path) -> dict[str, Any]:
    request = json.loads(request_path.read_text())
    resolved = request["resolved"]
    input_path = Path(resolved["inputPath"])
    output_path = Path(request["outputPath"])
    if sha256_file(input_path) != resolved["inputSha256"]:
        raise ValidationFailure("build input hash mismatch")
    glb = Glb(input_path)
    rig = resolved["documents"]["rig"]
    motion = resolved["documents"]["motion"]
    raw, metrics = build_layered_bytes(glb, rig, motion, resolved["layers"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    actual_hash = sha256_file(output_path)
    expected_hash = resolved["approvedOutputSha256"]
    if actual_hash != expected_hash:
        raise ValidationFailure(
            f"approved output hash mismatch: expected {expected_hash}, got {actual_hash}"
        )
    result = {
        "schema": "eonwild.motion.build-stage.v1",
        "status": "PASS",
        "inputSha256": resolved["inputSha256"],
        "output": str(output_path),
        "outputSha256": actual_hash,
        "lockSha256": resolved["lockSha256"],
        "metrics": metrics,
    }
    write_json(Path(request["stageReportPath"]), result)
    return result


def invoke_blender_build(
    *, repository: Path, request_path: Path, log_path: Path
) -> dict[str, Any]:
    entrypoint = (
        repository / "src/eonwild_motion/blender/entrypoint.py"
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [
            "blender",
            "--background",
            "--python-exit-code",
            "1",
            "--python",
            str(entrypoint),
            "--",
            "build",
            "--request",
            str(request_path),
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
    )
    log_path.write_text(process.stdout + process.stderr)
    if process.returncode != 0:
        raise MotionError(
            f"Blender build failed with exit {process.returncode}; see {log_path}"
        )
    request = json.loads(request_path.read_text())
    report = Path(request["stageReportPath"])
    if not report.is_file():
        raise MotionError("Blender build did not emit its stage report")
    result = json.loads(report.read_text())
    if result.get("status") != "PASS":
        raise MotionError("Blender build stage did not pass")
    return result
