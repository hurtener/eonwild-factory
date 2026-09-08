"""Verify task-owned exact Blender playback against bound expected skin arrays.

Run with Blender, for example::

  blender --background --factory-startup --python tools/verify_blender_native_playback.py -- \
    --request out/native-playback-request.json --output out/native-playback-result.json

The request binds immutable GLBs, ``.npy`` expected arrays, source seconds and
one same-index error threshold.  The expected arrays remain independent input;
this verifier never regenerates or adjusts them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eonwild_motion.blender.native_playback import import_gltf_for_native_playback


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_number(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    request_path, output = args.request.resolve(), args.output.resolve()

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant in playback request: {value}")

    request = json.loads(request_path.read_text(), parse_constant=reject_constant)
    modes = request.get("modes")
    limit = _finite_number(
        request.get("maximum_same_index_error_limit_m"), label="error limit"
    )
    if not isinstance(modes, dict) or not modes or limit <= 0.0:
        raise ValueError("playback request modes or error limit is invalid")

    result = {
        key: value for key, value in request.items() if key != "modes"
    }
    result.update(
        schema="eonwild.motion.blender-native-playback-parity.v1",
        blender_version=bpy.app.version_string,
        request_sha256=_sha(request_path),
        verifier_sha256=_sha(Path(__file__)),
        modes={},
    )
    for mode, row in sorted(modes.items()):
        if not isinstance(row, dict):
            raise ValueError(f"playback request mode is malformed: {mode}")
        source, expected_path = Path(row["glb"]), Path(row["expected"])
        if _sha(source) != row.get("glb_sha256"):
            raise ValueError(f"playback source hash changed: {mode}")
        if _sha(expected_path) != row.get("expected_sha256"):
            raise ValueError(f"playback expected-array hash changed: {mode}")
        times = row.get("times_s")
        if not isinstance(times, list) or not times:
            raise ValueError(f"playback sample times are missing: {mode}")
        sample_times = [
            _finite_number(value, label=f"{mode} time[{index}]")
            for index, value in enumerate(times)
        ]
        expected = np.load(expected_path, allow_pickle=False)
        if expected.ndim != 3 or expected.shape[0] != len(sample_times) or expected.shape[2] != 3:
            raise ValueError(f"playback expected-array shape is invalid: {mode}")

        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1
        playback = import_gltf_for_native_playback(source)
        if playback is None:
            raise ValueError(f"playback parity request is not CUBICSPLINE: {mode}")
        meshes = [
            item
            for item in scene.objects
            if item.type == "MESH" and len(item.data.vertices) == expected.shape[1]
        ]
        if len(meshes) != 1:
            raise ValueError(f"playback cannot uniquely resolve expected mesh: {mode}")
        mesh = meshes[0]
        records = []
        for index, time_s in enumerate(sample_times):
            playback.apply(time_s)
            dependency_graph = bpy.context.evaluated_depsgraph_get()
            evaluated = mesh.evaluated_get(dependency_graph)
            evaluated_mesh = evaluated.to_mesh()
            try:
                actual = np.asarray(
                    [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices],
                    dtype=float,
                )
            finally:
                evaluated.to_mesh_clear()
            if actual.shape != expected[index].shape or not np.isfinite(actual).all():
                raise ValueError(f"playback evaluated mesh is malformed: {mode}")
            errors = np.linalg.norm(actual - expected[index], axis=1)
            witness = int(np.argmax(errors))
            records.append(
                {
                    "time_s": time_s,
                    "maximum_same_index_error_m": float(errors[witness]),
                    "rms_same_index_error_m": float(np.sqrt(np.mean(errors**2))),
                    "worst_vertex": witness,
                    "actual_m": actual[witness].tolist(),
                    "expected_m": expected[index, witness].tolist(),
                }
            )
        maximum = max(row["maximum_same_index_error_m"] for row in records)
        result["modes"][mode] = {
            "glb_sha256": _sha(source),
            "expected_sha256": _sha(expected_path),
            "vertex_count": int(expected.shape[1]),
            "sample_count": len(records),
            "maximum_same_index_error_m": maximum,
            "samples": records,
            "native_playback": playback.receipt(),
            "status": "PASS" if maximum <= limit else "FAIL",
        }
    result["status"] = (
        "PASS"
        if all(row["status"] == "PASS" for row in result["modes"].values())
        else "FAIL"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    if result["status"] != "PASS":
        raise RuntimeError("task-owned native Blender playback parity failed")


if __name__ == "__main__":
    main()
