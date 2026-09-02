#!/usr/bin/env python3
"""Task-local side and front-three-quarter Bite preview renderer."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.eonwild_motion.blender import render_walk_review as renderer  # noqa: E402


renderer.VIEWS["front"] = Vector((0.0, -1.0, 0.10))
renderer.VIEWS["rear"] = Vector((0.0, 1.0, 0.10))
_original_import = renderer.import_character
_original_bounds = renderer.bounds
_original_camera = renderer.frame_camera
_preview_point: Vector | None = None


def import_character_with_preview_target(
    path: Path, clip_name: str, frame_count: int, fps: int
):
    global _preview_point
    root, objects, timeline = _original_import(path, clip_name, frame_count, fps)
    profile = json.loads((TASK / "profile.json").read_text())
    semantics = json.loads((ROOT / profile["semantic_rig"]["path"]).read_text())[
        "roles"
    ]
    armatures = [obj for obj in objects if obj.type == "ARMATURE"]
    for armature in armatures:
        bones = armature.pose.bones
        if semantics["head"] in bones and semantics["pelvis"] in bones:
            forward = (
                armature.matrix_world @ bones[semantics["head"]].head
                - armature.matrix_world @ bones[semantics["pelvis"]].head
            )
            forward.z = 0.0
            forward.normalize()
            renderer.VIEWS["front"] = forward + Vector((0.0, 0.0, 0.10))
            renderer.VIEWS["rear"] = -forward + Vector((0.0, 0.0, 0.10))
            break
    else:
        raise ValueError(
            "cannot resolve neutral semantic head/pelvis for front/rear camera"
        )
    receipt = json.loads(path.with_name("receipt.json").read_text())
    target = receipt["target"]
    canonical = Vector(target["world_position_m"])
    location = Vector((canonical.x, -canonical.z, canonical.y))
    _preview_point = location.copy()
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24,
        ring_count=12,
        radius=float(target["preview_prop_radius_m"]),
        location=location,
    )
    sphere = bpy.context.object
    sphere.name = "v9-bite-preview-target-prop-not-mechanics"
    material = bpy.data.materials.new("v9-bite-preview-target-orange")
    material.diffuse_color = (0.95, 0.22, 0.06, 1.0)
    material.roughness = 0.7
    sphere.data.materials.append(material)
    objects.append(sphere)
    timeline["previewTargetProp"] = {
        "authority": "preview-only-not-mechanics-or-content",
        "canonicalWorldPositionM": list(canonical),
        "radiusM": float(target["preview_prop_radius_m"]),
    }
    return root, objects, timeline


def bounds_with_preview_target(objects, *, extra_points=()):
    points = tuple(extra_points)
    if _preview_point is not None:
        points += (_preview_point,)
    return _original_bounds(objects, extra_points=points)


renderer.import_character = import_character_with_preview_target
renderer.bounds = bounds_with_preview_target


def landscape_camera(camera, direction, objects, aspect, **kwargs):
    scene = bpy.context.scene
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    original_frame = scene.frame_current
    union = []
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low, high = _original_bounds(objects)
        union.extend((low, high))
    scene.frame_set(original_frame)
    bpy.context.view_layer.update()
    union.extend(kwargs.get("extra_points", ()))
    facts = _original_camera(camera, direction, objects, 960 / 540, extra_points=union)
    # Blender AUTO sensor fit uses horizontal orthographic width in landscape.
    camera.data.ortho_scale = (
        max(facts["horizontalSpan"], facts["verticalSpan"] * 960 / 540) * 1.18
    )
    facts["orthoScale"] = camera.data.ortho_scale
    facts["framing"] = "all-frame union with ground prop, horizontal landscape fit"
    return facts


renderer.frame_camera = landscape_camera


if __name__ == "__main__":
    raise SystemExit(renderer.main())
