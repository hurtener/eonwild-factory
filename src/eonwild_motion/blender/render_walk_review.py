#!/usr/bin/env python3
"""Render a fixed-camera, candidate-only V9 walk review in Blender.

The GLB stores the canonical right-handed Y-up frame.  Blender imports that
frame into its Z-up scene, so the renderer keeps the conversion explicit when
placing the floor and optional machine overlay.  It imports one generated GLB
read-only, adds only a neutral floor/camera/annotation scene, and emits
numbered PNG sequences.  Encoding the final contact-sheet film is left to
ffmpeg so Blender's build does not need an FFMPEG image-format enum.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

from eonwild_motion.blender.native_playback import reject_stock_cubic_playback


# These directions are expressed in Blender's Z-up scene after the glTF
# importer conversion.  "side" is a lateral view, "front" follows the
# canonical forward direction, and top is a true plan view.
VIEWS = {
    "side": Vector((1.0, 0.0, 0.10)),
    "front": Vector((0.0, -1.0, 0.10)),
    "rear-three-quarter": Vector((-1.0, 1.0, 0.13)),
    "top": Vector((0.0, 0.0, 1.0)),
}

_CANONICAL_TO_BLENDER = ("x", "-z", "y")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overlay-json", type=Path)
    parser.add_argument(
        "--ground-level-canonical-y",
        type=float,
        required=True,
        help="Measured contact-floor Y in canonical glTF metres; maps to Blender Z.",
    )
    parser.add_argument("--frames", type=int, default=240)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument(
        "--presentation-profile",
        type=Path,
        help="V2/V3/V4 fixed-front profile whose presentation request is hash-bound here.",
    )
    parser.add_argument(
        "--probe-frame",
        type=int,
        action="append",
        help="Render only these frame numbers for a diagnostic probe (repeatable).",
    )
    parser.add_argument("--view", choices=tuple(VIEWS), action="append")
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    return parser.parse_args(arguments)


def _canonical_hash(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _presentation_request(args: argparse.Namespace) -> dict:
    if args.presentation_profile is None:
        return {
            "contract": "legacy_explicit_cli",
            "fps": args.fps,
            "frame_count": args.frames,
            "duration_s": args.frames / args.fps,
            "evidence_authority": False,
        }
    profile = json.loads(args.presentation_profile.read_text(encoding="utf-8"))
    identities = {
        (
            "eonwild.motion.v9.fixed-front-render-profile.v2",
            "fixed-front-render-v2",
            2,
        ),
        (
            "eonwild.motion.v9.fixed-front-render-profile.v3",
            "fixed-front-render-v3",
            3,
        ),
        (
            "eonwild.motion.v9.fixed-front-render-profile.v4",
            "fixed-front-render-v4",
            4,
        ),
    }
    identity = (
        (profile.get("schema"), profile.get("id"), profile.get("version"))
        if isinstance(profile, dict)
        else None
    )
    if identity not in identities:
        raise RuntimeError("presentation profile must be fixed-front-render-v2, v3, or v4")
    presentation = profile.get("presentation")
    expected = {
        "fps": 24,
        "frame_start": 1,
        "frame_count": 240,
        "duration_s": 10.0,
        "loop_mode": "deterministic_repeat_modulo_action_duration",
        "action_source": "exact_named_candidate_clip",
        "evidence_authority": False,
    }
    if presentation != expected:
        raise RuntimeError(
            "fixed-front presentation request is ambiguous or unsupported"
        )
    if args.frames != expected["frame_count"] or args.fps != expected["fps"]:
        raise RuntimeError(
            "CLI frames/fps cannot override the fixed-front presentation request"
        )
    return {
        "contract": f"fixed-front-render-v{profile['version']}-presentation-only",
        "profile_sha256": hashlib.sha256(
            args.presentation_profile.read_bytes()
        ).hexdigest(),
        **({"profile_version": 4} if profile["version"] == 4 else {}),
        **expected,
    }


def _select_exact_action(actions, clip_name: str):
    matches = [item for item in actions if item.name == clip_name]
    if not matches:
        raise RuntimeError(f"candidate action not found by exact name: {clip_name}")
    if len(matches) != 1:
        raise RuntimeError(f"candidate action is ambiguous by exact name: {clip_name}")
    return matches[0]


def import_character(path: Path, clip_name: str, frame_count: int, fps: int):
    reject_stock_cubic_playback(path, consumer="legacy walk review renderer")
    before_objects = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = list(set(bpy.data.objects) - before_objects)
    actions = list(set(bpy.data.actions) - before_actions)
    armatures = [item for item in objects if item.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("candidate GLB did not import an armature")
    armature = max(armatures, key=lambda item: len(item.data.bones))
    action = _select_exact_action(actions, clip_name)
    root = bpy.data.objects.new("v9-walk-review-root", None)
    bpy.context.collection.objects.link(root)
    for item in objects:
        if item.parent is None:
            item.parent = root
        if item.type == "MESH" and not any(
            modifier.type == "ARMATURE" for modifier in item.modifiers
        ):
            # glTF packages may carry an unskinned scale/reference mesh (for
            # example an Icosphere) alongside the character.  It is not part
            # of the candidate body and must not determine camera bounds,
            # floor placement, or the rendered evidence.
            item.hide_render = True
    armature.animation_data_create()
    armature.animation_data.action = None
    track = armature.animation_data.nla_tracks.new()
    track.name = "v9-walk-review-loop"
    strip = track.strips.new("v9-walk-review-walk", 1, action)
    duration = float(action.frame_range[1] - action.frame_range[0])
    if duration <= 0.0:
        raise RuntimeError("candidate action has no positive duration")
    strip.action_frame_start = float(action.frame_range[0])
    strip.action_frame_end = float(action.frame_range[1])
    # Play exactly one complete imported action over the requested presentation
    # frame range.  ``repeat < 1`` truncates an action in Blender NLA; temporal
    # fitting belongs on strip scale instead.
    strip.repeat = 1.0
    strip.scale = float(frame_count) / duration
    strip.frame_end = float(frame_count + 1)
    action_timeline = {
        "action_name": action.name,
        "frame_start": float(action.frame_range[0]),
        "frame_end": float(action.frame_range[1]),
        "duration_s": duration / float(fps),
        "presentation_scale": float(frame_count) / duration,
        "presentation_cycle_coverage": 1.0,
        "nla_repeat": 1.0,
    }
    action_timeline["timeline_sha256"] = _canonical_hash(action_timeline)
    return root, objects, action_timeline


def _mesh_objects(objects):
    meshes = [item for item in objects if item.type == "MESH"]
    if not meshes:
        raise RuntimeError("candidate contains no renderable mesh")
    skinned = [
        item
        for item in meshes
        if any(modifier.type == "ARMATURE" for modifier in item.modifiers)
    ]
    return skinned or meshes


def bounds(objects, *, extra_points=()) -> tuple[Vector, Vector]:
    points = list(extra_points)
    for item in _mesh_objects(objects):
        points.extend(item.matrix_world @ Vector(corner) for corner in item.bound_box)
    if not points:
        raise RuntimeError("candidate contains no renderable mesh")
    return (
        Vector(tuple(min(point[index] for point in points) for index in range(3))),
        Vector(tuple(max(point[index] for point in points) for index in range(3))),
    )


def _camera_basis(direction: Vector) -> tuple[Vector, Vector, Vector]:
    """Return view direction, camera-right, and camera-up in world space."""

    view = direction.normalized()
    up_reference = (
        Vector((0.0, 1.0, 0.0)) if abs(view.z) > 0.95 else Vector((0.0, 0.0, 1.0))
    )
    right = view.cross(up_reference)
    if right.length <= 1.0e-9:
        raise RuntimeError("camera direction is parallel to its up reference")
    right.normalize()
    up = right.cross(view).normalized()
    return view, right, up


def frame_camera(
    camera,
    direction: Vector,
    objects,
    aspect: float,
    *,
    extra_points=(),
) -> dict:
    view, right, up = _camera_basis(direction)
    minimum, maximum = bounds(objects, extra_points=extra_points)
    center = (minimum + maximum) * 0.5
    corners = [
        Vector((x, y, z))
        for x in (minimum.x, maximum.x)
        for y in (minimum.y, maximum.y)
        for z in (minimum.z, maximum.z)
    ]
    horizontal_span = max(right.dot(point - center) for point in corners) - min(
        right.dot(point - center) for point in corners
    )
    vertical_span = max(up.dot(point - center) for point in corners) - min(
        up.dot(point - center) for point in corners
    )
    if horizontal_span <= 0.0 or vertical_span <= 0.0:
        raise RuntimeError("camera bounds have no projected area")
    camera.location = center + view * 35.0
    camera.rotation_euler = (
        (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.ortho_scale = max(vertical_span, horizontal_span / aspect) * 1.18
    return {
        "center": list(center),
        "horizontalSpan": horizontal_span,
        "verticalSpan": vertical_span,
        "orthoScale": camera.data.ortho_scale,
        "direction": list(view),
        "right": list(right),
        "up": list(up),
    }


def add_review_ground(objects, *, canonical_ground_y: float):
    minimum, maximum = bounds(objects)
    horizontal_span = max(maximum.x - minimum.x, maximum.y - minimum.y)
    size = max(100.0, horizontal_span * 100.0)
    center = (minimum + maximum) * 0.5
    if not math.isfinite(canonical_ground_y):
        raise RuntimeError("canonical contact-floor Y must be finite")
    # The importer mapping is [x,y,z] -> [x,-z,y], so canonical Y is exactly
    # Blender Z.  Do not infer the floor from the full-mesh minimum: tails,
    # claws, or a non-contact mesh vertex can be below the measured sole/toe
    # contact level and leave the animal visibly suspended.
    ground_z = float(canonical_ground_y)
    bpy.ops.mesh.primitive_plane_add(
        size=size,
        location=(center.x, center.y, ground_z),
    )
    ground = bpy.context.object
    ground.name = "v9-neutral-review-ground"
    material = bpy.data.materials.new("v9-neutral-review-ground-material")
    # Match the world background so the finite diagnostic plane has no visible
    # horizon/edge in side/front/rear views.  Workbench still casts the body
    # shadow onto this floor, while crop assertions prove its finite boundary
    # is outside every camera frame.
    # Workbench's studio light brightens the horizontal plane relative to the
    # world background.  Use a calibrated low albedo so the two surfaces meet
    # without a visible horizon while retaining cast shadows.
    material.diffuse_color = (0.07, 0.08, 0.075, 1.0)
    material.roughness = 0.94
    material.metallic = 0.0
    ground.data.materials.append(material)
    return ground, ground_z, size


def ground_gap_facts(
    objects, ground_z: float, frame_numbers: tuple[int, ...]
) -> list[dict]:
    """Measure the mesh-to-contact-floor gap at the rendered probe frames."""

    facts = []
    for frame_number in frame_numbers:
        bpy.context.scene.frame_set(frame_number)
        bpy.context.view_layer.update()
        minimum, _ = bounds(objects)
        facts.append(
            {
                "frame": frame_number,
                "minimumMeshBlenderZ": float(minimum.z),
                "groundBlenderZ": float(ground_z),
                "minimumMeshGroundGapM": float(minimum.z - ground_z),
            }
        )
    return facts


def _finite_vec3(value, *, label: str) -> Vector:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise RuntimeError(f"overlay {label} must contain three numbers")
    result = [float(item) for item in value]
    if not all(math.isfinite(item) for item in result):
        raise RuntimeError(f"overlay {label} must be finite")
    return Vector(result)


def canonical_to_blender(value, *, label: str) -> Vector:
    canonical = _finite_vec3(value, label=label)
    return Vector((canonical.x, -canonical.z, canonical.y))


def _material(name: str, color: tuple[float, float, float, float]):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def _line_object(name: str, points: tuple[Vector, ...], material, bevel: float = 0.012):
    if len(points) < 2:
        raise RuntimeError("overlay line requires at least two points")
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 0
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, value in zip(spline.points, points):
        point.co = (*value, 1.0)
    object_value = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(object_value)
    curve.materials.append(material)
    return object_value


def _label_object(text: str, location: Vector, material):
    data = bpy.data.curves.new(f"v9-overlay-label-{text}", type="FONT")
    data.body = text
    data.align_x = "CENTER"
    data.size = 0.12
    data.extrude = 0.002
    object_value = bpy.data.objects.new(f"v9-overlay-label-{text}", data)
    bpy.context.collection.objects.link(object_value)
    object_value.location = location
    data.materials.append(material)
    return object_value


def load_overlay(path: Path | None) -> dict:
    if path is None:
        return {"frames": []}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"cannot read overlay JSON: {path}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("frames"), list):
        raise RuntimeError("overlay JSON must contain a frames array")
    return document


def add_top_overlay(overlay: dict, frame_count: int, ground_z: float):
    """Add animated current/target/achieved markers and a deterministic axis key."""

    records = overlay.get("frames", [])
    if not records:
        return [], []
    materials = {
        "current": _material("v9-overlay-current", (0.20, 0.82, 0.32, 1.0)),
        "target": _material("v9-overlay-target", (0.98, 0.64, 0.12, 1.0)),
        "achieved": _material("v9-overlay-achieved", (0.20, 0.52, 0.98, 1.0)),
        "axis": _material("v9-overlay-axis", (0.96, 0.96, 0.96, 1.0)),
    }
    overlay_objects = []
    all_points = []
    states = ("current_m", "target_m", "achieved_m")
    for side in ("left", "right"):
        for state in states:
            marker = None
            for render_frame in range(1, frame_count + 1):
                record = records[
                    min(
                        len(records) - 1,
                        round(
                            (render_frame - 1)
                            * (len(records) - 1)
                            / max(1, frame_count - 1)
                        ),
                    )
                ]
                sides = record.get("sides", {}) if isinstance(record, dict) else {}
                side_record = sides.get(side, {}) if isinstance(sides, dict) else {}
                value = (
                    side_record.get(state) if isinstance(side_record, dict) else None
                )
                if value is None:
                    continue
                point = canonical_to_blender(value, label=f"{side}.{state}")
                point.z = ground_z + 0.04
                all_points.append(point.copy())
                if marker is None:
                    bpy.ops.mesh.primitive_uv_sphere_add(
                        segments=8,
                        ring_count=4,
                        radius=0.065,
                        location=point,
                    )
                    marker = bpy.context.object
                    marker.name = f"v9-overlay-{side}-{state}"
                    marker.data.materials.append(materials[state.removesuffix("_m")])
                    overlay_objects.append(marker)
                marker.location = point
                marker.keyframe_insert(data_path="location", frame=render_frame)
            if marker is None:
                raise RuntimeError(f"overlay has no finite {side}.{state} samples")

    first = records[0]
    center = canonical_to_blender(first.get("hip_center_m"), label="hip_center_m")
    center.z = ground_z + 0.02
    travel = canonical_to_blender(first.get("travel_tangent"), label="travel_tangent")
    lateral = canonical_to_blender(first.get("lateral_axis"), label="lateral_axis")
    # The mapping is linear but changes the sign of the Blender Y component;
    # remove any vertical component before drawing the plan-view key.
    travel.z = 0.0
    lateral.z = 0.0
    if travel.length <= 1.0e-9 or lateral.length <= 1.0e-9:
        raise RuntimeError("overlay axes must be nonzero ground vectors")
    travel.normalize()
    lateral.normalize()
    axis_extent = 1.0
    overlay_objects.append(
        _line_object(
            "v9-overlay-travel-axis",
            (center - travel * axis_extent, center + travel * axis_extent),
            materials["axis"],
            bevel=0.018,
        )
    )
    overlay_objects.append(
        _line_object(
            "v9-overlay-lateral-axis",
            (center - lateral * axis_extent, center + lateral * axis_extent),
            materials["axis"],
            bevel=0.010,
        )
    )
    for label, offset in (("T", travel * 1.12), ("L", lateral * 1.12)):
        point = center + offset
        point.z = ground_z + 0.05
        overlay_objects.append(_label_object(label, point, materials["axis"]))
    return overlay_objects, all_points


def assert_crop_boundary(
    camera, ground, *, view_name: str, aspect: float, margin_factor: float = 1.25
) -> dict:
    """Prove the finite review floor cannot put an edge in the image."""

    inverse = camera.matrix_world.inverted()
    projected = [
        inverse @ (ground.matrix_world @ Vector(corner)) for corner in ground.bound_box
    ]
    horizontal = max(point.x for point in projected) - min(
        point.x for point in projected
    )
    vertical = max(point.y for point in projected) - min(point.y for point in projected)
    frame_width = float(camera.data.ortho_scale * aspect)
    frame_height = float(camera.data.ortho_scale)
    is_top = view_name == "top"
    required_horizontal = frame_width * margin_factor
    required_vertical = frame_height * margin_factor
    passed = horizontal >= required_horizontal and (
        not is_top or vertical >= required_vertical
    )
    if not passed:
        raise RuntimeError(
            f"{view_name}: finite floor edge can enter frame "
            f"(projected={horizontal:.3f}x{vertical:.3f}, frame={frame_width:.3f}x{frame_height:.3f})"
        )
    return {
        "status": "PASS",
        "view": view_name,
        "projectedGroundSpan": [horizontal, vertical],
        "frameSpan": [frame_width, frame_height],
        "marginFactor": margin_factor,
        "checks": {
            "horizontal": horizontal >= required_horizontal,
            "vertical": (not is_top) or vertical >= required_vertical,
        },
    }


def main() -> int:
    args = arguments()
    if args.frames < 2 or args.fps < 1:
        raise RuntimeError("frames and fps must be positive")
    probe_frames = tuple(sorted(set(args.probe_frame or ())))
    if any(frame < 1 or frame > args.frames for frame in probe_frames):
        raise RuntimeError("probe frames must fall within the rendered frame range")
    args.output.mkdir(parents=True, exist_ok=True)
    presentation = _presentation_request(args)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    character_root, objects, action_timeline = import_character(
        args.candidate, args.clip, args.frames, args.fps
    )
    loop_binding = {
        "candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "clip": args.clip,
        "action_timeline": action_timeline,
        "presentation": presentation,
    }
    loop_binding["presentation_loop_sha256"] = _canonical_hash(loop_binding)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.render.resolution_x = 480
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = 1
    scene.frame_end = args.frames
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = scene.world or bpy.data.worlds.new("v9-review-world")
    scene.world.color = (0.07, 0.08, 0.075)
    camera_data = bpy.data.cameras.new("v9-locked-review-camera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("v9-locked-review-camera", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    scene.frame_set(1)
    bpy.context.view_layer.update()
    ground, ground_z, ground_size = add_review_ground(
        objects,
        canonical_ground_y=args.ground_level_canonical_y,
    )
    overlay = load_overlay(args.overlay_json)
    overlay_objects, overlay_points = add_top_overlay(overlay, args.frames, ground_z)
    selected_views = args.view or list(VIEWS)
    view_directions = dict(VIEWS)
    if presentation.get("profile_version") == 4:
        # Blender +Y is canonical -Z after [x,y,z] -> [x,-z,y].
        view_directions["front"] = Vector((0.0, 1.0, 0.10))
    measured_frames = probe_frames or (1, max(1, args.frames // 2), args.frames)
    ground_gap = ground_gap_facts(objects, ground_z, measured_frames)
    report = {
        "schema": "eonwild.motion.v9.walk-review-media.v2",
        "clip": args.clip,
        "frames": args.frames,
        "fps": args.fps,
        "durationSeconds": args.frames / args.fps,
        "presentationOnly": True,
        "evidenceAuthority": False,
        "presentationLoop": loop_binding,
        "renderMode": "probe" if probe_frames else "animation",
        "renderedFrameNumbers": list(probe_frames)
        if probe_frames
        else {"start": 1, "end": args.frames},
        "layout": "candidate-only-four-view-sequences",
        "coordinateMapping": {
            "canonical": "right-handed Y-up glTF metres",
            "blenderScene": "right-handed Z-up",
            "canonicalToBlender": "[x,y,z] -> [x,-z,y]",
        },
        "ground": {
            "type": "matte-neutral-plane",
            "canonicalGroundY": args.ground_level_canonical_y,
            "z": ground_z,
            "size": ground_size,
            "includedInCameraBounds": False,
            "cropBoundaryAssertion": "required per view",
            "placementSource": "explicit measured canonical contact floor mapped by [x,y,z] -> [x,-z,y]",
            "meshGroundGapMeasurements": ground_gap,
        },
        "overlay": {
            "input": str(args.overlay_json) if args.overlay_json else None,
            "status": "PASS" if overlay_points else "NOT_PROVIDED",
            "states": ["current", "target", "achieved"] if overlay_points else [],
            "topViewOnly": True,
        },
        "views": {},
    }
    for name in selected_views:
        bpy.context.view_layer.update()
        extra = overlay_points if name == "top" else ()
        camera_facts = frame_camera(
            camera,
            view_directions[name].copy(),
            objects,
            480 / 540,
            extra_points=extra,
        )
        crop_facts = assert_crop_boundary(
            camera, ground, view_name=name, aspect=480 / 540
        )
        target = args.output / f"{name}-candidate-frames"
        target.mkdir(parents=True, exist_ok=True)
        if probe_frames:
            for frame_number in probe_frames:
                scene.frame_set(frame_number)
                scene.render.filepath = str(target / f"frame-{frame_number:04d}.png")
                bpy.ops.render.render(write_still=True)
            first = target / f"frame-{probe_frames[0]:04d}.png"
        else:
            scene.render.filepath = str(target / "frame-")
            bpy.ops.render.render(animation=True)
            first = target / "frame-0001.png"
        if not first.is_file():
            raise RuntimeError(f"render sequence missing: {first}")
        report["views"][name] = {
            "framePattern": str(target / "frame-%04d.png"),
            "camera": camera_facts,
            "cropBoundaryAssertion": crop_facts,
        }
    (args.output / "render-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
