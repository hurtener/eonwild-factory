"""Render the ACTUAL candidate in Blender, with an optional FBX transport.

blender -b --python tools/render_candidate.py -- --package out/run --output out/review
Requires Blender's glTF importer and ffmpeg on PATH. No factory modules or old
experiment scripts are imported. Export is not a claim of Unity parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy
from mathutils import Vector


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--view", choices=("side", "three-quarter"), default="three-quarter")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--fbx", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.fps < 12 or args.width < 320:
        raise ValueError("invalid review resolution or frame rate")
    package, output = args.package.resolve(), args.output.resolve()
    source = package / "in_place.glb"
    manifest = json.loads((package / "manifest.json").read_text())
    if sha(source) != manifest["files"]["in_place.glb"]:
        raise ValueError("candidate hash does not match its manifest")
    runtime = json.loads((package / "runtime.json").read_text())
    if sha(package / "runtime.json") != manifest["files"]["runtime.json"]:
        raise ValueError("runtime metadata hash mismatch")
    duration = float(runtime["duration_s"])
    if not 0 < duration <= 60:
        raise ValueError("review duration outside supported envelope")
    output.mkdir(parents=True, exist_ok=False)
    frames = output / "frames"
    frames.mkdir()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = args.fps
    scene.render.fps_base = 1
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    if not meshes or not any(obj.type == "ARMATURE" for obj in scene.objects):
        raise ValueError("candidate import has no rigged mesh")
    count = max(2, int(math.ceil(duration * args.fps)))
    scene.frame_start, scene.frame_end = 1, count
    # Export before adding the stage. Preserve actual action timing; verify in
    # Unity separately before using the transport in gameplay.
    exports = {}
    if args.fbx:
        target = output / "motion.fbx"
        bpy.ops.export_scene.fbx(filepath=str(target), object_types={"ARMATURE", "MESH"},
            add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
            axis_forward="-Z", axis_up="Y", global_scale=1.0, apply_unit_scale=True)
        exports["motion.fbx"] = sha(target)
    points = []
    for k in range(9):
        value = 1 + (count - 1) * k / 8
        scene.frame_set(int(value), subframe=value % 1)
        deps = bpy.context.evaluated_depsgraph_get()
        for obj in meshes:
            evaluated = obj.evaluated_get(deps)
            points.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) / 2
    span = max(high - low)
    # Blender's glTF import converts Y-up to Z-up: (x,y,z)->(x,-z,y).
    f = runtime["forward_axis"]
    forward = Vector((f[0], -f[2], f[1])).normalized()
    lateral = Vector((0, 0, 1)).cross(forward).normalized()
    offset = lateral + (forward * .65 if args.view == "three-quarter" else Vector((0, 0, 0)))
    camera_data = bpy.data.cameras.new("ReviewCamera")
    camera = bpy.data.objects.new("ReviewCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = center + offset.normalized() * span * 1.65 + Vector((0, 0, span * .25))
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = span * 1.28
    camera_data.clip_end = max(1000., span * 10)
    scene.camera = camera
    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(center.x, center.y, low.z - .005))
    ground = bpy.context.object
    ground.name = "ReviewGround"
    ground.color = (.22, .24, .25, 1)
    # Workbench intentionally emphasizes silhouette/deformation, not a claim
    # of finished game lighting. Existing texture images remain available.
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "TEXTURE"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.background_type = "WORLD"
    scene.world.color = (.12, .13, .15)
    scene.render.resolution_x = args.width
    scene.render.resolution_y = int(args.width * 9 / 16) // 2 * 2
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.frame_set(1)
    for index in range(count):
        # No retiming: every image is sampled at index/fps seconds.
        scene.frame_set(index + 1)
        scene.render.filepath = str(frames / f"{index:05d}.png")
        bpy.ops.render.render(write_still=True)
    video = output / "preview.mp4"
    subprocess.run(["ffmpeg", "-y", "-framerate", str(args.fps), "-i", str(frames / "%05d.png"),
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
    cover = output / "cover.png"
    cover.write_bytes((frames / f"{count // 3:05d}.png").read_bytes())
    receipt = {"schema": "eonwild.motion.review-render.v1", "source_sha256": sha(source),
        "manifest_sha256": sha(package / "manifest.json"), "renderer_sha256": sha(Path(__file__)),
        "blender": bpy.app.version_string, "fps": args.fps, "frames": count,
        "source_duration_s": duration, "encoded_duration_s": count / args.fps,
        "timing": "native speed; final duplicate loop endpoint omitted", "view": args.view,
        "media": {"preview.mp4": sha(video), "cover.png": sha(cover)}, "exports": exports,
        "visual_approval": "PENDING", "unity_import_validation": "NOT_RUN",
        "presentation": "Workbench study, not final game shading"}
    (output / "render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__": main()
