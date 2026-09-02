"""Full-body landscape side preview, with no evidence overlays hiding feet."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.eonwild_motion.blender.render_walk_review import import_character, frame_camera, add_review_ground, _mesh_objects


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--clip", default="V9_AIRBORNE_RUN_IN_PLACE")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ground", type=float, required=True)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--joint-region", action="store_true")
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--probe-frame", type=float, action="append")
    parser.add_argument("--camera-side", type=int, choices=(-1, 1), default=1)
    parser.add_argument("--view", choices=("side", "front", "rear"), default="side")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 24
    _, objects, timeline = import_character(args.candidate, args.clip, args.frames, 24)
    # Imported action frames start at zero, but the presentation NLA strip
    # starts at scene frame one. Record both authorities, not an inferred offset.
    armature = max((obj for obj in objects if obj.type == "ARMATURE"), key=lambda obj: len(obj.data.bones))
    strip = armature.animation_data.nla_tracks["v9-walk-review-loop"].strips[0]
    def source_time(frame):
        return (strip.action_frame_start + (frame - strip.frame_start) / strip.scale) / scene.render.fps
    timeline["nla_scene_start"] = float(strip.frame_start)
    timeline["nla_scene_end"] = float(strip.frame_end)
    timeline["source_time_formula"] = "(action_frame_start + (scene_frame - nla_scene_start) / presentation_scale) / fps"
    timeline["rendered_samples"] = [{"scene_frame": float(frame), "source_time_s": source_time(frame)} for frame in (args.probe_frame or range(1, args.frames + 1))]
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 620
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("run-preview-world")
    scene.world.color = (.065, .075, .075)
    scene.frame_start, scene.frame_end = 1, args.frames
    bounds = []
    joint_bounds = []
    roles = json.loads(args.binding.read_text())["roles"] if args.binding else None
    for frame in range(1, args.frames + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for obj in _mesh_objects(objects):
            bounds.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
        if args.joint_region:
            if roles is None:
                raise RuntimeError("joint-region preview requires semantic binding")
            for armature in [obj for obj in objects if obj.type == "ARMATURE"]:
                names = [roles["pelvis"]] + [n for side in ("left", "right") for n in roles["legs"][side]["contactChain"]]
                joint_bounds.extend(armature.matrix_world @ armature.pose.bones[n].head for n in names)
    scene.frame_set(1)
    add_review_ground(objects, canonical_ground_y=args.ground)
    camera_data = bpy.data.cameras.new("full-body-fixed-side")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("full-body-fixed-side", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    direction = Vector((args.camera_side, 0, .035)) if args.view == "side" else Vector((0, -1 if args.view == "front" else 1, .035))
    camera_facts = frame_camera(camera, direction, objects, 1100 / 620, extra_points=bounds)
    camera_facts["view"] = args.view
    # Blender's landscape orthographic scale spans image width. The shared
    # portrait review helper uses a vertical fit, so explicitly correct here.
    camera.data.ortho_scale = max(camera_facts["horizontalSpan"], camera_facts["verticalSpan"] * 1100 / 620) * 1.18
    camera_facts["orthoScale"] = camera.data.ortho_scale
    if args.joint_region:
        minimum = Vector(tuple(min(p[a] for p in joint_bounds) for a in range(3)))
        maximum = Vector(tuple(max(p[a] for p in joint_bounds) for a in range(3)))
        center = (minimum + maximum) * .5
        center.z += .12
        camera.location = center + Vector((35 * args.camera_side, 0, 1.225))
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = max(maximum.y - minimum.y, (maximum.z - minimum.z + .45) * 1100 / 620) * 1.25
        camera_facts.update(center=list(center), orthoScale=camera.data.ortho_scale, camera_side=args.camera_side, region="diagnostic hip-knee-ankle crop; not full-body acceptance")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "render-receipt.json").write_text(json.dumps({"status": "ENGINEERING_MEDIAN_SEED_NOT_VISUALLY_ACCEPTED", "timeline": timeline, "camera": camera_facts, "ground": args.ground, "frames": args.frames, "fps": 24}, indent=2))
    scene.render.filepath = str(args.output / "frame-")
    if args.probe_frame:
        for frame in args.probe_frame:
            scene.frame_set(int(frame), subframe=frame - int(frame))
            label = f"{int(frame):04d}" if frame.is_integer() else f"{frame:06.2f}"
            scene.render.filepath = str(args.output / f"frame-{label}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
