"""Render actual candidate channels with Blender Cycles CPU; optionally FBX.

blender -b --python tools/render_candidate.py -- --package out/run --output out/review
No graphics driver, factory/experiment imports, or external scene assets are
required. A preview or FBX transport never grants production/Unity approval.
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

SOURCE_FPS = 120


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_frame(scene, value):
    frame = math.floor(value)
    scene.frame_set(frame, subframe=value - frame)


def area_light(scene, name, position, target, power, size):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy, data.size = power, size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--view", choices=("side", "three-quarter"), default="three-quarter")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--fbx", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if not 12 <= args.fps <= 120 or not 320 <= args.width <= 3840 or not 1 <= args.samples <= 256:
        raise ValueError("invalid review resolution, samples or frame rate")
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
    scene.render.fps = SOURCE_FPS
    scene.render.fps_base = 1
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    if not meshes or not any(obj.type == "ARMATURE" for obj in scene.objects):
        raise ValueError("candidate import has no rigged mesh")
    actions = list(bpy.data.actions)
    if not actions:
        raise ValueError("candidate import has no animation actions")
    start = min(float(action.frame_range[0]) for action in actions)
    end = max(float(action.frame_range[1]) for action in actions)
    if abs((end - start) / SOURCE_FPS - duration) > 2e-5:
        raise ValueError(f"imported duration changed: {(end-start)/SOURCE_FPS} != {duration}")
    count = max(2, int(math.ceil(duration * args.fps)))
    scene.frame_start, scene.frame_end = math.floor(start), round(end)
    exports = {}
    if args.fbx:
        if abs(start - round(start)) > .001 or abs(end - round(end)) > .001:
            raise ValueError("FBX transport requires endpoints on the declared 120 Hz grid")
        target = output / "motion.fbx"
        bpy.ops.export_scene.fbx(filepath=str(target), object_types={"ARMATURE", "MESH"},
            add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
            axis_forward="-Z", axis_up="Y", global_scale=1.0, apply_unit_scale=True,
            path_mode="COPY", embed_textures=True)
        exports["motion.fbx"] = sha(target)
    points = []
    for k in range(9):
        set_frame(scene, start + (end - start) * k / 8)
        deps = bpy.context.evaluated_depsgraph_get()
        for obj in meshes:
            evaluated = obj.evaluated_get(deps)
            points.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) / 2
    span = max(high - low)
    if span <= 0:
        raise ValueError("degenerate candidate bounds")
    f = runtime["forward_axis"]
    # Blender's glTF importer maps Y-up to Z-up: (x,y,z)->(x,-z,y).
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
    material = bpy.data.materials.new("ReviewGroundMaterial")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (.18, .20, .22, 1)
    bsdf.inputs["Roughness"].default_value = .85
    ground.data.materials.append(material)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("ReviewWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.32, .36, .42, 1)
    background.inputs["Strength"].default_value = .45
    area_light(scene, "Key", center + lateral * span * .7 + Vector((0, 0, span)), center, span * span * 90, span * .8)
    area_light(scene, "Fill", center - lateral * span * .8 + forward * span * .4 + Vector((0, 0, span * .5)), center, span * span * 35, span)
    # Workbench/Mesa segfaulted on headless CI. CPU Cycles avoids that driver
    # path rather than silently skipping the missing frames or retrying errors.
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.seed = 0
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.use_persistent_data = True
    scene.render.resolution_x = args.width
    scene.render.resolution_y = int(args.width * 9 / 16) // 2 * 2
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    for index in range(count):
        set_frame(scene, start + index * SOURCE_FPS / args.fps)
        scene.render.filepath = str(frames / f"{index:05d}.png")
        bpy.ops.render.render(write_still=True)
    video = output / "preview.mp4"
    subprocess.run(["ffmpeg", "-y", "-framerate", str(args.fps), "-i", str(frames / "%05d.png"),
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames,width,height", "-of", "json", str(video)], text=True))["streams"][0]
    if int(probe["nb_read_frames"]) != count:
        raise ValueError("encoded preview has missing or extra frames")
    cover = output / "cover.png"
    cover.write_bytes((frames / f"{count // 3:05d}.png").read_bytes())
    receipt = {"schema": "eonwild.motion.review-render.v1", "source_sha256": sha(source),
        "manifest_sha256": sha(package / "manifest.json"), "renderer_sha256": sha(Path(__file__)),
        "blender": bpy.app.version_string, "engine": "CYCLES_CPU", "samples": args.samples,
        "fps": args.fps, "frames": count, "verified_encoded_frames": int(probe["nb_read_frames"]),
        "source_duration_s": duration, "encoded_duration_s": count / args.fps,
        "source_frame_start": start, "source_frame_end": end, "source_fps": SOURCE_FPS,
        "timing": "native-time sampling; FBX retains full endpoint; video omits duplicate loop endpoint",
        "view": args.view, "media": {"preview.mp4": sha(video), "cover.png": sha(cover)}, "exports": exports,
        "visual_approval": "PENDING", "unity_import_validation": "NOT_RUN",
        "presentation": "CPU studio study; bbox presentation floor is not contact validation"}
    (output / "render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
