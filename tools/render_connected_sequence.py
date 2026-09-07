"""Render an immutable start -> steady cycles -> stop schedule in Blender.

Each segment evaluates its source GLB directly at source seconds selected by
the fixed-rate review clock.  The renderer does not create animation strips,
blend, retime, fit endpoints or copy boundary poses.  Root-motion segments
receive only their declared constant parent offset.  In-place segments receive
the same offset plus the declared motor trajectory at the evaluated source time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from connected_schedule import validate_connected_schedule
from connected_timeline import plan_distance, segment_at
from preview_clock import source_frame as mapped_source_frame, transport_clock
from render_candidate import area_light, camera_spec, projected_camera_frame, set_frame
from review_timing import native_sample_times


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_snapshot(package: Path, mode: str) -> dict:
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    files = manifest.get("files")
    if not isinstance(files, dict) or mode + ".glb" not in files:
        raise ValueError(f"connected source has no declared {mode}.glb: {package}")
    actual = {}
    for name, expected in sorted(files.items()):
        path = package / name
        if not path.is_file():
            raise ValueError(f"connected source file is missing: {path}")
        actual[name] = sha(path)
        if actual[name] != expected:
            raise ValueError(f"connected source file hash mismatch: {path}")
    return {
        "package": str(package),
        "manifest_sha256": sha(manifest_path),
        "package_id": manifest.get("id"),
        "technical_status": manifest.get("technical_status", "NOT_EVALUATED"),
        "manifest_files": actual,
        "source_glb": mode + ".glb",
        "source_glb_sha256": actual[mode + ".glb"],
    }


def semantic_root(objects: list, runtime: dict):
    name = runtime.get("rig_roles", {}).get("root")
    matches = [(obj, obj.pose.bones[name]) for obj in objects
               if obj.type == "ARMATURE" and name in obj.pose.bones]
    if len(matches) == 1:
        obj, bone = matches[0]
        return lambda: (obj.matrix_world @ bone.matrix).translation.copy()
    matches = [obj for obj in objects if obj.name.split(".")[0] == name and obj.type != "MESH"]
    if len(matches) == 1:
        return lambda: matches[0].matrix_world.translation.copy()
    raise ValueError(f"cannot uniquely resolve connected semantic root {name!r}")


def mesh_geometry_digest(obj) -> str:
    """Hash imported shape, topology, UVs and skin weights independent of names."""
    digest = hashlib.sha256()
    mesh = obj.data
    digest.update(struct.pack("<III", len(mesh.vertices), len(mesh.loops), len(mesh.polygons)))
    for vertex in mesh.vertices:
        digest.update(struct.pack("<3d", *vertex.co))
        groups = sorted((group.group, float(group.weight)) for group in vertex.groups)
        digest.update(struct.pack("<I", len(groups)))
        for group, weight in groups:
            digest.update(struct.pack("<Id", group, weight))
    for loop in mesh.loops:
        digest.update(struct.pack("<I", loop.vertex_index))
    for layer in mesh.uv_layers:
        for item in layer.data:
            digest.update(struct.pack("<2d", *item.uv))
    return digest.hexdigest()


def import_source(package: Path, mode: str, runtime: dict, plan: dict, index: int) -> dict:
    before_objects = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(package / (mode + ".glb")))
    objects = [obj for obj in bpy.data.objects if obj not in before_objects]
    actions = [action for action in bpy.data.actions if action not in before_actions]
    if not objects or not actions:
        raise ValueError(f"connected source import has no objects or actions: {package}")
    meshes = [obj for obj in objects if obj.type == "MESH"]
    if not meshes or not any(obj.type == "ARMATURE" for obj in objects):
        raise ValueError(f"connected source import has no rigged mesh: {package}")
    action_fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    start = min(float(action.frame_range[0]) for action in actions)
    end = max(float(action.frame_range[1]) for action in actions)
    clock = transport_clock(start, end, runtime["duration_s"], action_fps)
    parent = bpy.data.objects.new(f"ConnectedSourceParent{index:02d}", None)
    bpy.context.scene.collection.objects.link(parent)
    for obj in [obj for obj in objects if obj.parent is None]:
        matrix = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = matrix
    objects.append(parent)
    for obj in objects:
        obj.hide_render = True
    signature = sorted(mesh_geometry_digest(obj) for obj in meshes)
    root_position = semantic_root(objects, runtime)
    set_frame(bpy.context.scene, start)
    bpy.context.view_layer.update()
    return {
        "package": package,
        "runtime": runtime,
        "plan": plan,
        "objects": objects,
        "meshes": meshes,
        "parent": parent,
        "root_position": root_position,
        "clock": clock,
        "action_fps": action_fps,
        "geometry_signature": signature,
        "source_zero_root": root_position(),
    }


def source_frame(source: dict, time_s: float) -> float:
    clock = source["clock"]
    if abs(time_s) <= 2e-9:
        return clock.source_start_frame
    if abs(time_s - float(source["runtime"]["duration_s"])) <= 2e-6:
        return clock.source_end_frame
    return mapped_source_frame(clock.source_start_frame, time_s, source["action_fps"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--view", choices=("side", "three-quarter"), required=True)
    parser.add_argument("--mode", choices=("root_motion", "in_place"), required=True)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--samples", type=int, default=8)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if not 12 <= args.fps <= 120 or not 320 <= args.width <= 3840 or not 1 <= args.samples <= 256:
        raise ValueError("invalid connected review resolution, samples or frame rate")
    schedule_path = args.schedule.resolve()
    output = args.output.resolve()
    def reject_constant(value: str):
        raise ValueError(f"non-finite JSON constant in connected schedule: {value}")
    schedule = json.loads(schedule_path.read_text(), parse_constant=reject_constant)
    validate_connected_schedule(schedule)
    segments = schedule["segments"]
    output.mkdir(parents=True, exist_ok=False)
    frames = output / "frames"
    frames.mkdir()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1
    packages: dict[str, dict] = {}
    snapshots = []
    for index, row in enumerate(segments):
        key = row["package"]
        if key in packages:
            continue
        package = Path(key).resolve()
        snapshot = package_snapshot(package, args.mode)
        if snapshot["manifest_sha256"] != row["manifest_sha256"]:
            raise ValueError(f"connected schedule manifest identity changed: {package}")
        runtime = json.loads((package / "runtime.json").read_text())
        plan = json.loads((package / "plan.json").read_text())
        source = import_source(package, args.mode, runtime, plan, index)
        source["snapshot"] = snapshot
        packages[key] = source
        snapshots.append(snapshot)
    signatures = {tuple(source["geometry_signature"]) for source in packages.values()}
    if len(signatures) != 1:
        raise ValueError("connected source packages differ in imported geometry, topology, UVs or skin weights")
    action_fps = {source["action_fps"] for source in packages.values()}
    if len(action_fps) != 1:
        raise ValueError("connected source packages imported with different clocks")

    first_source = packages[segments[0]["package"]]
    runtime = first_source["runtime"]
    plane = runtime.get("ground_plane")
    if plane is None or plane.get("up_axis") != "Y" or not math.isfinite(float(plane.get("level_m"))):
        raise ValueError("connected review requires an explicitly declared finite Y-up floor")
    ground_level = float(plane["level_m"])
    f = runtime["forward_axis"]
    forward = Vector((f[0], -f[2], f[1])).normalized()
    lateral = Vector((0, 0, 1)).cross(forward).normalized()

    active_source = None
    def activate(row: dict, time_s: float) -> tuple[dict, Vector, float]:
        nonlocal active_source
        source = packages[row["package"]]
        if source is not active_source:
            for candidate in packages.values():
                hidden = candidate is not source
                for obj in candidate["objects"]:
                    obj.hide_render = hidden
            active_source = source
        distance = plan_distance(source["plan"]["samples"], time_s)
        offset = float(row["root_motion_parent_offset_m"])
        source["parent"].location = forward * (offset if args.mode == "root_motion" else offset + distance)
        set_frame(scene, source_frame(source, time_s))
        bpy.context.view_layer.update()
        return source, source["root_position"](), offset + distance

    sample_times = native_sample_times(float(schedule["duration_s"]), args.fps)
    evaluation_rows = []
    for timeline_s in sample_times:
        row = segment_at(segments, timeline_s)
        source_time = float(row["source_start_s"]) + timeline_s - float(row["timeline_start_s"])
        evaluation_rows.append((timeline_s, row, source_time))
    # Exact endpoints are additional diagnostic samples and do not extend the film.
    bounding_rows = list(evaluation_rows)
    for before, after in zip(segments, segments[1:]):
        bounding_rows.extend([
            (float(before["timeline_end_s"]), before, float(before["source_end_s"])),
            (float(after["timeline_start_s"]), after, float(after["source_start_s"])),
        ])
    bounding_rows.append((float(schedule["duration_s"]), segments[-1], float(segments[-1]["source_end_s"])))

    _, initial_root, initial_declared = activate(segments[0], float(segments[0]["source_start_s"]))
    points = []
    max_root_error = 0.0
    for _, row, source_time in bounding_rows:
        source, root, declared = activate(row, source_time)
        actual = (root - initial_root).dot(forward) + initial_declared
        max_root_error = max(max_root_error, abs(actual - declared))
        shift = root - initial_root
        deps = bpy.context.evaluated_depsgraph_get()
        for obj in source["meshes"]:
            evaluated = obj.evaluated_get(deps)
            points.extend(evaluated.matrix_world @ Vector(corner) - shift for corner in evaluated.bound_box)
    if max_root_error > 0.002:
        raise ValueError(f"connected world root differs from declared travel by {max_root_error} m")
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center, span = (low + high) / 2, max(high - low)
    if span <= 0:
        raise ValueError("degenerate connected candidate bounds")
    offset = lateral + (forward * .65 if args.view == "three-quarter" else Vector((0, 0, 0)))
    viewing_direction = (offset.normalized() * 1.65 + Vector((0, 0, .25))).normalized()
    center, scale = projected_camera_frame(points, viewing_direction=viewing_direction,
        fallback_center=center, fallback_span=span, aspect=16 / 9)
    position = center + viewing_direction * max(span, scale) * 1.65
    spec = camera_spec(None, view=args.view, focus="body", center=center,
        position=position, root=initial_root, scale=scale)
    (output / "camera.json").write_text(json.dumps(spec, indent=2) + "\n")
    camera_base = initial_root + Vector(spec["position_relative_root"])
    camera_center = initial_root + Vector(spec["center_relative_root"])
    camera_data = bpy.data.cameras.new("ConnectedReviewCamera")
    camera = bpy.data.objects.new("ConnectedReviewCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = camera_base
    camera.rotation_euler = (camera_center - camera_base).to_track_quat("-Z", "Y").to_euler()
    camera_data.type, camera_data.ortho_scale = "ORTHO", spec["orthographic_scale"]
    camera_data.clip_end = max(1000., span * 10)
    scene.camera = camera

    floor_size = max(span * 12, abs(float(schedule["declared_root_travel_m"])) * 2 + span * 4, 100)
    bpy.ops.mesh.primitive_plane_add(size=floor_size, location=(initial_root.x, initial_root.y, ground_level))
    ground = bpy.context.object
    ground.name = "ConnectedReviewGround"
    material = bpy.data.materials.new("ConnectedReviewGroundMaterial")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = .85
    geometry = nodes.new("ShaderNodeNewGeometry")
    checker = nodes.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 2.
    checker.inputs["Color1"].default_value = (.18, .20, .22, 1)
    checker.inputs["Color2"].default_value = (.23, .25, .27, 1)
    links.new(geometry.outputs["Position"], checker.inputs["Vector"])
    links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
    ground.data.materials.append(material)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("ConnectedReviewWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.32, .36, .42, 1)
    background.inputs["Strength"].default_value = .45
    light_span = max(span, abs(float(schedule["declared_root_travel_m"])) + span)
    area_light(scene, "Key", center + lateral * light_span * .35 + Vector((0, 0, span)),
               center, light_span * span * 90, light_span)
    area_light(scene, "Fill", center - lateral * light_span * .35 + forward * light_span * .2 + Vector((0, 0, span * .5)),
               center, light_span * span * 35, light_span)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples, scene.cycles.seed = args.samples, 0
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces, scene.cycles.diffuse_bounces, scene.cycles.glossy_bounces = 3, 2, 2
    scene.render.use_persistent_data = True
    scene.render.threads_mode, scene.render.threads = "FIXED", 2
    scene.render.resolution_x = args.width
    scene.render.resolution_y = int(args.width * 9 / 16) // 2 * 2
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    timeline = []
    for index, (timeline_s, row, source_time) in enumerate(evaluation_rows):
        source, root, declared = activate(row, source_time)
        camera.location = camera_base + root - initial_root
        scene.render.filepath = str(frames / f"{index:05d}.png")
        bpy.ops.render.render(write_still=True)
        timeline.append({
            "index": index,
            "timeline_s": timeline_s,
            "segment": row["label"],
            "source_package": row["package"],
            "source_time_s": source_time,
            "source_frame": source_frame(source, source_time),
            "declared_world_root_m": declared,
            "actual_world_root_m": (root - initial_root).dot(forward) + initial_declared,
            "parent_offset_m": float(row["root_motion_parent_offset_m"]),
        })
    (output / "timeline.json").write_text(json.dumps(timeline, indent=2, allow_nan=False) + "\n")

    joins_folder = output / "joins"
    joins_folder.mkdir()
    joins = []
    for index, (before, after) in enumerate(zip(segments, segments[1:]), start=1):
        record = {"index": index, "timeline_s": float(before["timeline_end_s"]), "before": {}, "after": {}}
        for side, row, source_time in (
            ("before", before, float(before["source_end_s"])),
            ("after", after, float(after["source_start_s"])),
        ):
            source, root, declared = activate(row, source_time)
            camera.location = camera_base + root - initial_root
            target = joins_folder / f"{index:02d}-{side}.png"
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
            record[side] = {
                "segment": row["label"], "source_package": row["package"],
                "source_time_s": source_time, "source_frame": source_frame(source, source_time),
                "declared_world_root_m": declared,
                "actual_world_root_m": (root - initial_root).dot(forward) + initial_declared,
                "image": str(target.relative_to(output)), "sha256": sha(target),
            }
        joins.append(record)
    (output / "joins.json").write_text(json.dumps(joins, indent=2, allow_nan=False) + "\n")

    terminal_row = segments[-1]
    terminal_time = float(terminal_row["source_end_s"])
    source, root, declared = activate(terminal_row, terminal_time)
    camera.location = camera_base + root - initial_root
    terminal_path = output / "terminal.png"
    scene.render.filepath = str(terminal_path)
    bpy.ops.render.render(write_still=True)
    terminal = {
        "timeline_s": float(schedule["duration_s"]), "segment": terminal_row["label"],
        "source_package": terminal_row["package"], "source_time_s": terminal_time,
        "source_frame": source_frame(source, terminal_time), "declared_world_root_m": declared,
        "actual_world_root_m": (root - initial_root).dot(forward) + initial_declared,
        "image": terminal_path.name, "sha256": sha(terminal_path),
    }

    video = output / "preview.mp4"
    subprocess.run(["ffmpeg", "-y", "-framerate", str(args.fps), "-i", str(frames / "%05d.png"),
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], check=True)
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames,width,height,r_frame_rate,duration", "-of", "json", str(video)], text=True))["streams"][0]
    if int(probe["nb_read_frames"]) != len(timeline):
        raise ValueError("encoded connected preview has missing or extra frames")
    numerator, denominator = map(int, probe["r_frame_rate"].split("/"))
    if numerator != args.fps * denominator:
        raise ValueError("encoded connected preview changed review frame rate")
    cover = output / "cover.png"
    cover.write_bytes((frames / f"{len(timeline) // 3:05d}.png").read_bytes())
    after = [package_snapshot(Path(row["package"]), args.mode) for row in snapshots]
    if after != snapshots:
        raise ValueError("connected source package changed during rendering")
    receipt = {
        "schema": "eonwild.motion.connected-review-render.v1",
        "schedule_sha256": sha(schedule_path),
        "renderer_sha256": sha(Path(__file__)),
        "timing_sampler_sha256": sha(Path(__file__).with_name("review_timing.py")),
        "source_packages_before": snapshots,
        "source_packages_after": after,
        "input_immutability": "PASS",
        "blender": bpy.app.version_string,
        "engine": "CYCLES_CPU", "samples": args.samples, "denoising": False,
        "fps": args.fps, "review_fps": args.fps, "frames": len(timeline),
        "verified_encoded_frames": int(probe["nb_read_frames"]),
        "source_clocks": [{"package": str(source["package"]), **source["clock"].receipt()}
                          for source in packages.values()],
        "declared_duration_s": float(schedule["duration_s"]), "encoded_duration_s": len(timeline) / args.fps,
        "timing": "fixed-rate review frames evaluate immutable source seconds on [0,duration); exact joins and one-shot terminal rendered separately",
        "segment_policy": "direct immutable source intervals; no NLA, repeat strip, retime, blend, fitted or copied boundary",
        "root_policy": "constant cumulative declared offset for root motion; declared motor trajectory reconstruction for in-place",
        "maximum_declared_root_error_m": max_root_error,
        "mode": args.mode, "view": args.view, "focus": "body", "camera": spec,
        "segments": [{key: row[key] for key in ("label", "package", "source_start_s", "source_end_s",
            "timeline_start_s", "timeline_end_s", "root_motion_parent_offset_m", "world_root_start_m", "world_root_end_m")}
            for row in segments],
        "join_samples": joins, "terminal_pose": terminal,
        "media": {name: sha(output / name) for name in ("preview.mp4", "cover.png", "camera.json", "timeline.json", "joins.json", "terminal.png")},
        "visual_approval": "PENDING", "unity_import_validation": "NOT_RUN",
        "ground_level_m": ground_level,
        "presentation": "fixed declared floor and 0.5 m world checker; camera tracks world root; no floor fitting or animal scaling",
    }
    (output / "render-receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps(receipt, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
