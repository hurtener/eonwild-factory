from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector

from eonwild_motion.blender.native_playback import reject_stock_cubic_playback
from eonwild_motion.media.png import canonicalize_png


def _world_bounds() -> tuple[Vector, Vector]:
    points = []
    for item in bpy.context.scene.objects:
        if item.type != "MESH":
            continue
        points.extend(item.matrix_world @ Vector(corner) for corner in item.bound_box)
    if not points:
        raise RuntimeError("render import produced no mesh bounds")
    minimum = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return minimum, maximum


def execute_render_request(request_path: Path) -> dict[str, Any]:
    request = json.loads(request_path.read_text())
    for item in list(bpy.data.objects):
        bpy.data.objects.remove(item, do_unlink=True)
    reject_stock_cubic_playback(
        Path(request["artifactPath"]), consumer="canonical single-frame renderer"
    )
    bpy.ops.import_scene.gltf(filepath=request["artifactPath"])
    clip_name = request["clipName"]
    action = bpy.data.actions.get(clip_name)
    if action is not None:
        for item in bpy.context.scene.objects:
            if item.type == "ARMATURE":
                if item.animation_data is None:
                    item.animation_data_create()
                item.animation_data.action = action
    render_set = request["renderSet"]
    scene = bpy.context.scene
    scene.frame_set(int(render_set["frame"]))
    # The historical EEVEE enum was removed in newer Blender and requires
    # a usable graphics context. The active reproduction verifier must also
    # run headlessly: real CPU rendering, never a placeholder or skipped gate.
    # This changes only review PNGs, not immutable approved GLB bytes.
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.seed = 0
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 1
    scene.render.resolution_x = int(render_set["width"])
    scene.render.resolution_y = int(render_set["height"])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = tuple(render_set["background"][:3])
    minimum, maximum = _world_bounds()
    center = (minimum + maximum) * 0.5
    extent = maximum - minimum
    direction = Vector(render_set["viewDirection"]).normalized()
    camera_data = bpy.data.cameras.new("review-camera")
    camera = bpy.data.objects.new("review-camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + direction * max(extent) * 2.5
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    aspect = scene.render.resolution_x / scene.render.resolution_y
    camera_data.ortho_scale = max(extent.z, extent.x / max(aspect, 1e-6), extent.y)
    camera_data.ortho_scale *= float(render_set["margin"])
    scene.camera = camera
    light_data = bpy.data.lights.new("review-key", type="AREA")
    light_data.energy = 1800
    light_data.shape = "DISK"
    light_data.size = max(extent) * 1.5
    light = bpy.data.objects.new("review-key", light_data)
    bpy.context.collection.objects.link(light)
    light.location = center + Vector((max(extent), -max(extent), max(extent)))
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    output = Path(request["outputPath"])
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    media = canonicalize_png(output)
    result = {
        "schema": "eonwild.motion.render-report.v1",
        "status": "PASS",
        "runId": request["runId"],
        "profile": request["profile"],
        "source": request["source"],
        "artifact": {
            "path": request["artifactPath"],
            "sha256": request["artifactSha256"],
        },
        "renderSet": request["renderSetBinding"],
        "media": {"path": str(output), **media},
        "frame": int(render_set["frame"]),
        "clipSemanticId": request["clipSemanticId"],
        "camera": {
            "type": "ORTHO",
            "viewDirection": render_set["viewDirection"],
            "margin": render_set["margin"],
            "fullBodyBoundsDerived": True,
        },
        "blenderVersion": bpy.app.version_string,
    }
    report_path = Path(request["stageReportPath"])
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
