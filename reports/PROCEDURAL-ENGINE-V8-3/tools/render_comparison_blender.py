#!/usr/bin/env python3
"""Render the locked 240-frame V8.2/V8.3 comparison views in Blender."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


CLIP = "PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE"
VIEWS = {
    "side": Vector((1.0, 0.0, 0.10)),
    "front": Vector((0.0, -1.0, 0.10)),
    "front-three-quarter": Vector((1.0, -1.0, 0.13)),
}


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=240)
    parser.add_argument("--fps", type=int, default=24)
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    return parser.parse_args(arguments)


def import_character(path: Path, label: str):
    before_objects = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = list(set(bpy.data.objects) - before_objects)
    actions = list(set(bpy.data.actions) - before_actions)
    armature = max((item for item in objects if item.type == "ARMATURE"), key=lambda item: len(item.data.bones))
    action = next((item for item in actions if item.name.startswith(CLIP)), None)
    if action is None:
        raise RuntimeError(f"{label}: in-place action not found")
    root = bpy.data.objects.new(f"{label}-root", None)
    bpy.context.collection.objects.link(root)
    for item in objects:
        if item.parent is None:
            item.parent = root
    armature.animation_data_create()
    armature.animation_data.action = None
    track = armature.animation_data.nla_tracks.new()
    track.name = f"{label}-loop"
    strip = track.strips.new(f"{label}-walk", 1, action)
    duration = float(action.frame_range[1] - action.frame_range[0])
    strip.action_frame_start = float(action.frame_range[0])
    strip.action_frame_end = float(action.frame_range[1])
    strip.repeat = 240.0 / duration
    strip.frame_end = 241.0
    return root, objects


def bounds(objects) -> tuple[Vector, Vector]:
    points = []
    for item in objects:
        if item.type == "MESH":
            points.extend(item.matrix_world @ Vector(corner) for corner in item.bound_box)
    return (
        Vector(tuple(min(point[i] for point in points) for i in range(3))),
        Vector(tuple(max(point[i] for point in points) for i in range(3))),
    )


def frame_camera(camera, direction: Vector, objects, aspect: float) -> dict:
    direction.normalize()
    right = direction.cross(Vector((0.0, 0.0, 1.0))).normalized()
    minimum, maximum = bounds(objects)
    center = (minimum + maximum) * 0.5
    corners = [Vector((x, y, z)) for x in (minimum.x, maximum.x) for y in (minimum.y, maximum.y) for z in (minimum.z, maximum.z)]
    vertical = Vector((0.0, 0.0, 1.0))
    horizontal_span = max(right.dot(point - center) for point in corners) - min(right.dot(point - center) for point in corners)
    vertical_span = max(vertical.dot(point - center) for point in corners) - min(vertical.dot(point - center) for point in corners)
    camera.location = center + direction * 35.0
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = max(vertical_span, horizontal_span / aspect) * 1.12
    return {"center": list(center), "horizontalSpan": horizontal_span, "verticalSpan": vertical_span, "orthoScale": camera.data.ortho_scale}


def main() -> int:
    args = arguments()
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    baseline_root, baseline_objects = import_character(args.baseline, "v8-2")
    candidate_root, candidate_objects = import_character(args.candidate, "v8-3")
    all_objects = baseline_objects + candidate_objects
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 480
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = 1
    scene.frame_end = args.frames
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = scene.world or bpy.data.worlds.new("review-world")
    scene.world.color = (0.035, 0.045, 0.055)
    camera_data = bpy.data.cameras.new("locked-review-camera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("locked-review-camera", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    key_data = bpy.data.lights.new("review-key", "AREA")
    key_data.energy, key_data.shape, key_data.size = 1600, "DISK", 8.0
    key = bpy.data.objects.new("review-key", key_data)
    bpy.context.collection.objects.link(key)
    key.location = Vector((5.0, -8.0, 10.0))
    fill_data = bpy.data.lights.new("review-fill", "AREA")
    fill_data.energy, fill_data.size = 700, 7.0
    fill = bpy.data.objects.new("review-fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = Vector((-6.0, 4.0, 7.0))
    report = {"schema": "eonwild.motion.v8_3_media.v1", "frames": args.frames, "fps": args.fps, "durationSeconds": args.frames / args.fps, "layout": "v8.2-left-v8.3-right", "views": {}}
    for name, direction in VIEWS.items():
        baseline_root.location = Vector((0.0, 0.0, 0.0))
        candidate_root.location = Vector((0.0, 0.0, 0.0))
        bpy.context.view_layer.update()
        camera_facts = frame_camera(camera, direction.copy(), all_objects, 480 / 540)
        patterns = {}
        for label, visible, hidden in (
            ("v8-2", baseline_objects, candidate_objects),
            ("v8-3", candidate_objects, baseline_objects),
        ):
            for item in visible:
                item.hide_render = False
            for item in hidden:
                item.hide_render = True
            target = args.output / f"{name}-{label}-frames"
            target.mkdir(parents=True, exist_ok=True)
            scene.render.filepath = str(target / "frame-")
            bpy.ops.render.render(animation=True)
            first = target / "frame-0001.png"
            if not first.is_file():
                raise RuntimeError(f"render sequence missing: {first}")
            patterns[label] = str(target / "frame-%04d.png")
        report["views"][name] = {"framePatterns": patterns, "camera": camera_facts}
    (args.output / "render-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
