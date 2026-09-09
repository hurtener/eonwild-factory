"""Pinned-Blender regression for fractional FBX transport endpoints."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def test_blender_fbx_transport_preserves_fractional_endpoint_and_pose(tmp_path):
    blender = shutil.which("blender")
    assert blender is not None, "the real Blender tool is required"
    root = Path(__file__).resolve().parents[1]
    probe = tmp_path / "fbx_transport_probe.py"
    probe.write_text(
        """
import json
import math
from pathlib import Path
import sys

import bpy

root = Path(sys.argv[-2])
output = Path(sys.argv[-1])
sys.path.insert(0, str(root / "tools"))
from preview_clock import transport_clock
from render_candidate import export_transport

assert bpy.app.version[:2] == (5, 2), bpy.app.version_string
results = []
for index, (start, end) in enumerate(((0.0, 295.20001220703125), (3.5, 153.75))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = 120, 1
    bpy.ops.object.armature_add()
    armature = bpy.context.object
    armature.name = "TransportArmature"
    armature.location = (0, 0, 0)
    armature.keyframe_insert(data_path="location", frame=start)
    armature.location = (1, 0, 0)
    armature.keyframe_insert(data_path="location", frame=end)
    action = list(bpy.data.actions)
    assert len(action) == 1 and tuple(action[0].frame_range) == (start, end)

    clock = transport_clock(start, end, (end - start) / 120.0, 120)
    result = export_transport(scene, action, clock, output / f"transport-{index}.fbx")
    assert result["nla_scale"] == 1.0
    assert result["reopened_duration_s"] == clock.duration_s
    imported = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    poses = []
    for frame in (
        result["reopened_frame_start"],
        result["reopened_frame_start"] + clock.duration_frames / 2,
        result["reopened_frame_end"],
    ):
        integer = math.floor(frame)
        bpy.context.scene.frame_set(integer, subframe=frame - integer)
        poses.append(float(imported.location.x))
    assert abs(poses[0]) < 1e-7
    assert abs(poses[1] - .5) < 1e-5
    assert abs(poses[2] - 1.0) < 1e-7
    results.append({"start": start, "end": end, "poses": poses, **result})
print("FBX_TRANSPORT_PROOF " + json.dumps(results, sort_keys=True))
"""
    )
    completed = subprocess.run(
        [blender, "--background", "--factory-startup", "--python", str(probe),
         "--", str(root), str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout[-6000:]
    assert "FBX_TRANSPORT_PROOF " in completed.stdout
