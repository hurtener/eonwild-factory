#!/usr/bin/env python3
"""Render the validated Tarbosaurus V5.5 GLB as a local showcase.

The GLB is imported read-only.  This script never writes to the source tree or
modifies animation data; each clip is selected from the actions produced by
Blender's glTF importer and rendered into a fresh output directory.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PRIORITY_TAGS = {"walk", "turn", "start", "stop", "idle", "alert", "eat", "attack", "roar"}
FILM_NAMES = (
    "PROC_IDLE_BREATH_V5_5",
    "PROC_WALK_RELAXED_V5_5_INPLACE",
    "PROC_TURN_LEFT_35_V5_5_INPLACE",
    "PROC_START_WALK_V5_5_INPLACE",
    "PROC_EAT_LOOP_V5_5",
    "PROC_BITE_ATTACK_V5_5",
    "PROC_ROAR_V5_5",
)


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=360)
    p.add_argument("--fps", type=int, default=20)
    p.add_argument("--film-max-seconds", type=float, default=3.2)
    p.add_argument("--still-only", action="store_true")
    p.add_argument("--film-name", help="Render only this action as a film and skip stills")
    p.add_argument("--inspect-only", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    return p.parse_args(argv)


def clean_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.75, metallic: float = 0.0) -> bpy.types.Material:
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return m


def make_stage(bounds: tuple[Vector, Vector]) -> tuple[bpy.types.Camera, bpy.types.Object]:
    lo, hi = bounds
    center = (lo + hi) * 0.5
    size = hi - lo
    horizontal = max(size.x, size.y)
    radius = max(horizontal, size.z) * 0.5

    ground_mat = material("Showcase ground", (0.018, 0.030, 0.027, 1.0), 0.96)
    # glTF import in this fixture is Z-up: X/Y are the floor plane and Z is
    # height.  Keep this basis explicit so the ground can never become a wall.
    bpy.ops.mesh.primitive_plane_add(size=max(100.0, radius * 20.0), location=(center.x, center.y, lo.z - 0.035))
    ground = bpy.context.object
    ground.name = "SHOWCASE_GROUND"
    ground.data.materials.append(ground_mat)

    # A softly curved cyclorama keeps the silhouette readable without adding
    # any external texture or copyrighted visual input.
    bpy.ops.mesh.primitive_plane_add(size=max(100.0, radius * 20.0), location=(lo.x - radius * 4.0, center.y, center.z), rotation=(0.0, math.pi / 2.0, 0.0))
    backdrop = bpy.context.object
    backdrop.name = "SHOWCASE_BACKDROP"
    backdrop.data.materials.append(material("Showcase backdrop", (0.012, 0.027, 0.027, 1.0), 1.0))

    # Shoot across X so the animal's dominant Y length reads as a stable side
    # profile.  Keep the distance driven by vertical stature: using the full
    # root-motion envelope here would make the subject postage-stamp small.
    camera_distance = max(size.y * 1.65, size.z * 3.0, 10.0)
    bpy.ops.object.camera_add(location=(center.x + camera_distance, center.y, center.z + size.z * 0.48))
    camera = bpy.context.object
    camera.name = "SHOWCASE_CAMERA"
    camera.data.lens = 58
    camera.data.sensor_width = 36
    camera.data.dof.use_dof = False
    bpy.context.scene.camera = camera

    def point_at(obj: bpy.types.Object, target: Vector) -> None:
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()

    point_at(camera, center + Vector((0.0, 0.0, size.z * 0.08)))
    bpy.ops.object.light_add(type="AREA", location=(center.x + horizontal * 1.8, center.y - size.y * 0.8, center.z + size.z * 2.4))
    key = bpy.context.object
    key.name = "SHOWCASE_KEY"
    key.data.energy = 1100
    key.data.shape = "DISK"
    key.data.size = radius * 2.5
    point_at(key, center)
    bpy.ops.object.light_add(type="AREA", location=(center.x - horizontal * 1.3, center.y + size.y * 0.9, center.z + size.z * 0.9))
    fill = bpy.context.object
    fill.name = "SHOWCASE_FILL"
    fill.data.energy = 650
    fill.data.size = radius * 3.0
    point_at(fill, center)
    bpy.ops.object.light_add(type="AREA", location=(center.x + horizontal * 0.3, center.y, center.z + size.z * 0.25))
    rim = bpy.context.object
    rim.name = "SHOWCASE_RIM"
    rim.data.energy = 850
    rim.data.size = radius * 1.8
    point_at(rim, center + Vector((0.0, radius * 0.2, 0.0)))
    return camera, ground


def world_setup() -> None:
    world = bpy.data.worlds.new("V5.5 Showcase World") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.004, 0.009, 0.010, 1.0)
        bg.inputs["Strength"].default_value = 0.22


def render_setup(width: int, height: int, fps: int) -> None:
    scene = bpy.context.scene
    # The host's Blender 5.2 build exposes the Eevee enum as BLENDER_EEVEE;
    # keep the fallback for distributions that retain the newer spelling.
    engines = {item.identifier for item in scene.bl_rna.properties["render"].fixed_type.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.fps = fps
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = ""
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.video_bitrate = 7000
    scene.view_settings.look = "AgX - Medium High Contrast"


def imported_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    corners: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not corners:
        return Vector((-1, 0, -1)), Vector((1, 2, 1))
    lo = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
    hi = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
    return lo, hi


def sampled_deformed_bounds(
    scene: bpy.types.Scene,
    armature: bpy.types.Object,
    actions: dict[str, bpy.types.Action],
    priority: list[dict],
) -> tuple[Vector, Vector]:
    """Find a single locked camera envelope across every priority clip.

    The dependency graph evaluates the imported skin at sparse phase samples;
    this captures both deformation and root motion without changing any source
    keyframes.  The resulting envelope is intentionally shared by every shot.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points: list[Vector] = []
    for clip in priority:
        action = actions[clip["name"]]
        start, end = set_action(armature, action)
        for phase in (0.0, 0.25, 0.5, 0.75, 1.0):
            scene.frame_set(start + int(round((end - start) * phase)))
            depsgraph.update()
            for obj in scene.objects:
                if obj.type != "MESH" or obj.name.startswith("SHOWCASE_"):
                    continue
                evaluated = obj.evaluated_get(depsgraph)
                mesh = evaluated.to_mesh()
                try:
                    points.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
                finally:
                    evaluated.to_mesh_clear()
    if not points:
        return imported_bounds([o for o in scene.objects if o.type in {"MESH", "ARMATURE"}])
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def action_map() -> dict[str, bpy.types.Action]:
    return {a.name: a for a in bpy.data.actions}


def safe_slug(name: str) -> str:
    return name.lower().replace("proc_", "").replace("_v5_5", "").replace("_", "-")


def set_action(armature: bpy.types.Object, action: bpy.types.Action) -> tuple[int, int]:
    if not armature.animation_data:
        armature.animation_data_create()
    for track in armature.animation_data.nla_tracks:
        track.mute = True
        track.is_solo = False
    armature.animation_data.action = action
    start = math.floor(action.frame_range[0])
    end = math.ceil(action.frame_range[1])
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    bpy.context.scene.frame_set(start)
    return start, end


def render_still(scene: bpy.types.Scene, camera: bpy.types.Camera, action: bpy.types.Action, armature: bpy.types.Object, path: Path) -> None:
    start, end = set_action(armature, action)
    scene.frame_set(start + max(0, int((end - start) * 0.46)))
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_film(
    scene: bpy.types.Scene,
    action: bpy.types.Action,
    clip_info: dict,
    armature: bpy.types.Object,
    path: Path,
    fps: int,
    max_seconds: float,
) -> None:
    start, end = set_action(armature, action)
    # Looping clips are rendered for their complete manifest duration.  A
    # frame cap is retained for one-shot films so the showcase remains
    # pragmatic without truncating an authored loop at an arbitrary phase.
    if clip_info.get("loop"):
        frame_count = max(2, round(float(clip_info["durationSeconds"]) * fps))
    else:
        frame_count = min(end - start + 1, max(2, math.ceil(max_seconds * fps)))
    # This Blender build has no FFMPEG image-format enum, so render a numbered
    # PNG sequence and encode it with the host ffmpeg executable.
    frame_dir = path.parent / f".{path.stem}.frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(frame_dir / "frame_")
    scene.render.fps = fps
    scene.frame_start = start
    scene.frame_end = start + frame_count - 1
    bpy.ops.render.render(animation=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode showcase MP4 films")
    subprocess.run([
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(fps), "-start_number", str(start),
        "-i", str(frame_dir / "frame_%04d.png"), "-frames:v", str(frame_count),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path),
    ], check=True)
    shutil.rmtree(frame_dir)


def main() -> None:
    cfg = args()
    cfg.output.mkdir(parents=True, exist_ok=True)
    still_dir = cfg.output / "stills"
    film_dir = cfg.output / "films"
    still_dir.mkdir(exist_ok=True)
    film_dir.mkdir(exist_ok=True)
    clean_scene()
    # glTF's animation sampler is interpreted against the scene FPS at import;
    # set it before import so 60 Hz baked keys retain their manifest durations
    # when this 24 fps editorial render is requested.
    bpy.context.scene.render.fps = cfg.fps
    bpy.ops.import_scene.gltf(filepath=str(cfg.input), loglevel=0)
    imported = [o for o in bpy.context.scene.objects if o.type in {"MESH", "ARMATURE"}]
    for obj in bpy.context.scene.objects:
        if "icosphere" in obj.name.lower():
            obj.hide_render = True
    armatures = [o for o in imported if o.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("glTF import produced no armature")
    armature = armatures[0]
    actions = action_map()
    manifest = json.loads(cfg.manifest.read_text())
    priority = [c for c in manifest["clips"] if not c.get("transition") and set(c.get("tags", [])) & PRIORITY_TAGS]
    clip_by_name = {clip["name"]: clip for clip in priority}
    missing = [c["name"] for c in priority if c["name"] not in actions]
    if missing:
        raise RuntimeError(f"manifest actions missing after glTF import: {missing}")
    bounds = sampled_deformed_bounds(bpy.context.scene, armature, actions, priority)
    camera, _ground = make_stage(bounds)
    world_setup()
    render_setup(cfg.width, cfg.height, cfg.fps)
    scene = bpy.context.scene
    scene.camera = camera
    if cfg.inspect_only:
        objects = []
        for obj in bpy.context.scene.objects:
            if obj.type in {"MESH", "ARMATURE"}:
                objects.append({"name": obj.name, "type": obj.type, "location": list(obj.location), "dimensions": list(obj.dimensions), "matrix_world": [list(row) for row in obj.matrix_world]})
        bones = []
        for bone in armature.data.bones:
            if bone.name.lower() in {"root", "pelvis", "head", "tail", "tailbase", "neck", "bone_000", "bone_001", "bone_002"} or any(token in bone.name.lower() for token in ("head", "jaw", "tail")):
                bones.append({"name": bone.name, "head": list(bone.head_local), "tail": list(bone.tail_local), "parent": bone.parent.name if bone.parent else None})
        print(json.dumps({"actions": sorted(actions), "bounds": [list(bounds[0]), list(bounds[1])], "priority": [c["name"] for c in priority], "objects": objects, "bones": bones}, indent=2))
        return

    if not cfg.film_name:
        for clip in priority:
            name = clip["name"]
            render_still(scene, camera, actions[name], armature, still_dir / f"{safe_slug(name)}.png")
    film_names = [cfg.film_name] if cfg.film_name else list(FILM_NAMES)
    if not cfg.still_only:
        for name in film_names:
            if name in actions:
                render_film(scene, actions[name], clip_by_name[name], armature, film_dir / f"{safe_slug(name)}.mp4", cfg.fps, cfg.film_max_seconds)

    report = {
        "renderer": "Blender",
        "blender_version": bpy.app.version_string,
        "source_glb": str(cfg.input),
        "manifest": str(cfg.manifest),
        "resolution": [cfg.width, cfg.height],
        "fps": cfg.fps,
        "priority_clip_count": len(priority),
        "priority_clips": [c["name"] for c in priority],
        "film_clips": [name for name in film_names if name in actions] if not cfg.still_only else [],
        "film_duration_policy_seconds_non_loop": cfg.film_max_seconds,
        "loop_duration_policy": "manifest durationSeconds rendered at the requested FPS",
        "imported_actions": len(actions),
        "bounds_m": {"min": list(bounds[0]), "max": list(bounds[1])},
        "animation_data_policy": "source GLB imported read-only; action selection only; no animation channels edited",
    }
    (cfg.output / "render-run.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
