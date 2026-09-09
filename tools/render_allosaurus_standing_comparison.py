#!/usr/bin/env python3
"""Render a scale-correct, same-camera Allosaurus standing comparison in Blender."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
import numpy as np


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from eonwild_motion.factory.animal import apply_uniform_geometry_scale, load_animal_instance
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _rotation_from_matrix, _world_matrices


EXPECTED_CURRENT_SHA256 = "f1ac3ddebc2b8471af1a55439d0631ed0d350a750e59edaa661a9cd76ced4684"
CHAINS = {
    "left": ("Bone_023", "Bone_022", "Bone_021", "Bone_020", "Bone_019", "Bone_018"),
    "right": ("Bone_029", "Bone_028", "Bone_027", "Bone_026", "Bone_025", "Bone_024"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--animal", type=Path, required=True)
    parser.add_argument("--contact", type=Path, required=True)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument("--standing-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    return parser.parse_args(values)


def canonical_to_blender(points: np.ndarray) -> np.ndarray:
    return np.stack((points[..., 0], -points[..., 2], points[..., 1]), axis=-1)


def state(source: Glb) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    worlds = np.asarray(
        _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale),
        dtype=np.float64,
    )
    mesh_nodes = [index for index, node in enumerate(source.nodes) if "mesh" in node and "skin" in node]
    if len(mesh_nodes) != 1:
        raise RuntimeError("standing render requires exactly one skinned mesh")
    node = source.nodes[mesh_nodes[0]]
    primitive = source.document["meshes"][node["mesh"]]["primitives"][0]
    skin = source.document["skins"][node["skin"]]
    positions = np.asarray(source.accessor_values(primitive["attributes"]["POSITION"]), dtype=np.float64)
    ids = np.concatenate([
        np.asarray(source.accessor_values(primitive["attributes"][name]), dtype=np.int64)
        for name in ("JOINTS_0", "JOINTS_1")
    ], axis=1)
    weights = np.concatenate([
        np.asarray(source.accessor_values(primitive["attributes"][name]), dtype=np.float64)
        for name in ("WEIGHTS_0", "WEIGHTS_1")
    ], axis=1)
    weights /= weights.sum(axis=1, keepdims=True)
    joint_nodes = np.asarray(skin["joints"], dtype=np.int64)
    inverse = np.asarray(source.accessor_values(skin["inverseBindMatrices"]), dtype=np.float64)
    inverse = inverse.reshape(-1, 4, 4).transpose(0, 2, 1)
    transforms = worlds[joint_nodes] @ inverse
    skin_points = np.einsum(
        "nv,nvij,nj->ni",
        weights,
        transforms[ids],
        np.column_stack((positions, np.ones(len(positions)))),
    )[:, :3]
    triangles = np.asarray(source.accessor_values(primitive["indices"]), dtype=np.int64).reshape(-1, 3)
    return worlds, skin_points, triangles


def make_material(name: str, color: tuple[float, float, float, float]):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def add_segment(a: Vector, b: Vector, radius: float, material, name: str) -> None:
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)


def add_marker(point: Vector, radius: float, material, name: str) -> None:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10, radius=radius, location=point)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)


def project_in_front(point: Vector, position: Vector, target: Vector, distance: float = 0.8) -> Vector:
    view = (target - position).normalized()
    depth = view.dot(point - position)
    return point + view * (distance - depth)


def render(
    *,
    label: str,
    skin: np.ndarray,
    triangles: np.ndarray,
    worlds: np.ndarray,
    source: Glb,
    floor_m: float,
    camera_position: Vector,
    camera_target: Vector,
    ortho_scale: float,
    resolution: tuple[int, int],
    output: Path,
) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.world = bpy.data.worlds.new("StandingComparisonWorld")
    scene.world.color = (0.055, 0.055, 0.065)

    mesh = bpy.data.meshes.new("ExactStandingSkin")
    mesh.from_pydata(canonical_to_blender(skin).tolist(), [], triangles.tolist())
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    animal = bpy.data.objects.new("AllosaurusStandingSkin", mesh)
    scene.collection.objects.link(animal)
    animal.data.materials.append(make_material("Clay", (0.31, 0.42, 0.32, 1.0)))

    bpy.ops.mesh.primitive_plane_add(size=18.0, location=(0.0, 0.0, floor_m))
    bpy.context.object.data.materials.append(make_material("Floor", (0.12, 0.13, 0.15, 1.0)))

    camera_data = bpy.data.cameras.new("FixedSideCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ortho_scale
    camera = bpy.data.objects.new("FixedSideCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = camera_position
    camera.rotation_euler = (camera_target - camera_position).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    materials = {
        "left": make_material("LeftChain", (0.03, 0.64, 1.0, 1.0)),
        "right": make_material("RightChain", (1.0, 0.07, 0.50, 1.0)),
    }
    radius = 0.018 if resolution[0] > resolution[1] else 0.012
    for side, names in CHAINS.items():
        points = canonical_to_blender(
            np.asarray([worlds[source.name_to_node[name], :3, 3] for name in names])
        )
        projected = [project_in_front(Vector(point), camera_position, camera_target) for point in points]
        for index in range(len(projected) - 1):
            add_segment(projected[index], projected[index + 1], radius, materials[side], f"{label}-{side}-{index}")
        for index, point in enumerate(projected):
            add_marker(point, radius * 1.9, materials[side], f"{label}-{side}-joint-{index}")

    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


def main() -> int:
    options = args()
    output = options.output.resolve()
    if output.exists():
        raise RuntimeError("standing comparison output must be new")
    output.mkdir(parents=True)
    current_path, candidate_path = options.current.resolve(), options.candidate.resolve()
    if sha(current_path) != EXPECTED_CURRENT_SHA256:
        raise RuntimeError("current standing comparison source differs")
    receipt_text = options.standing_receipt.read_text()
    if sha(candidate_path) not in receipt_text or EXPECTED_CURRENT_SHA256 not in receipt_text:
        raise RuntimeError("standing receipt does not bind comparison sources")
    animal_document = json.loads(options.animal.read_text())
    current, candidate = Glb(current_path), Glb(candidate_path)
    animal = load_animal_instance(animal_document, source_sha256=EXPECTED_CURRENT_SHA256)
    scale = float(animal["uniform_scale"])
    apply_uniform_geometry_scale(current, scale)
    apply_uniform_geometry_scale(candidate, scale)
    current_worlds, current_skin, triangles = state(current)
    candidate_worlds, candidate_skin, candidate_triangles = state(candidate)
    if not np.array_equal(triangles, candidate_triangles):
        raise RuntimeError("standing comparison topology differs")
    contact = json.loads(options.contact.read_text())
    floor_m = float(contact["geometry"]["ground"]["level_m"]) * scale
    floors = (float(np.min(current_skin[:, 1])), float(np.min(candidate_skin[:, 1])))
    if abs(floors[1] - floor_m) > 2.0e-6:
        raise RuntimeError("standing candidate skin does not match the scaled material floor")

    camera_spec = json.loads(options.camera.read_text())
    current_root = canonical_to_blender(
        current_worlds[current.name_to_node["Bone_000"], :3, 3][None, :]
    )[0]
    camera_position = Vector(current_root + np.asarray(camera_spec["position_relative_root"]))
    camera_target = Vector(current_root + np.asarray(camera_spec["center_relative_root"]))
    view = (camera_position - camera_target).normalized()
    leg_names = tuple(name for chain in CHAINS.values() for name in chain[:4])
    leg_points = canonical_to_blender(np.asarray([
        current_worlds[current.name_to_node[name], :3, 3] for name in leg_names
    ]))
    leg_target = Vector(np.mean(leg_points, axis=0))
    leg_position = leg_target + view * 17.0

    images = []
    for label, source, worlds, skin in (
        ("before", current, current_worlds, current_skin),
        ("candidate", candidate, candidate_worlds, candidate_skin),
    ):
        full = output / f"{label}-full.png"
        render(
            label=label, skin=skin, triangles=triangles, worlds=worlds, source=source,
            floor_m=floor_m, camera_position=camera_position, camera_target=camera_target,
            ortho_scale=float(camera_spec["orthographic_scale"]), resolution=(960, 540), output=full,
        )
        close = output / f"{label}-legs.png"
        render(
            label=label, skin=skin, triangles=triangles, worlds=worlds, source=source,
            floor_m=floor_m, camera_position=leg_position, camera_target=leg_target,
            ortho_scale=3.25, resolution=(720, 720), output=close,
        )
        images.extend((full, close))

    def metrics(source: Glb, worlds: np.ndarray) -> dict:
        output_metrics = {}
        for side, names in CHAINS.items():
            points = np.asarray([worlds[source.name_to_node[name], :3, 3] for name in names[:4]])
            upper, lower = points[0] - points[1], points[2] - points[1]
            knee = float(np.degrees(np.arccos(np.clip(np.dot(upper, lower) / np.linalg.norm(upper) / np.linalg.norm(lower), -1, 1))))
            output_metrics[side] = {
                "hip_world_m": points[0].tolist(),
                "knee_world_m": points[1].tolist(),
                "ankle_world_m": points[2].tolist(),
                "mtp_world_m": points[3].tolist(),
                "knee_degrees": knee,
            }
        return output_metrics

    before_metrics, candidate_metrics = metrics(current, current_worlds), metrics(candidate, candidate_worlds)
    deltas = {
        side: {
            "hip_world_delta_m": (
                np.asarray(candidate_metrics[side]["hip_world_m"]) - np.asarray(before_metrics[side]["hip_world_m"])
            ).tolist(),
            "knee_world_delta_m": (
                np.asarray(candidate_metrics[side]["knee_world_m"]) - np.asarray(before_metrics[side]["knee_world_m"])
            ).tolist(),
            "knee_angle_delta_degrees": candidate_metrics[side]["knee_degrees"] - before_metrics[side]["knee_degrees"],
        }
        for side in CHAINS
    }
    receipt = {
        "schema": "eonwild.allosaurus.standing-comparison.v1",
        "status": "DIAGNOSTIC_VISUAL_REVIEW_PENDING",
        "inputs": {
            "current": {"path": str(current_path), "sha256": sha(current_path)},
            "candidate": {"path": str(candidate_path), "sha256": sha(candidate_path)},
            "animal": {"path": str(options.animal.resolve()), "sha256": sha(options.animal)},
            "contact": {"path": str(options.contact.resolve()), "sha256": sha(options.contact)},
            "rig": {"path": str(options.rig.resolve()), "sha256": sha(options.rig)},
            "camera": {"path": str(options.camera.resolve()), "sha256": sha(options.camera)},
            "standing_receipt": {"path": str(options.standing_receipt.resolve()), "sha256": sha(options.standing_receipt)},
        },
        "uniform_scale": scale,
        "material_floor_m": floor_m,
        "reconstructed_skin_floor_m": {"before": floors[0], "candidate": floors[1]},
        "floor_residual_m": {"before": floors[0] - floor_m, "candidate": floors[1] - floor_m},
        "metrics": {"before": before_metrics, "candidate": candidate_metrics, "delta": deltas},
        "render": {
            "method": "direct normalized 8-influence LBS from each source static TRS; Blender Workbench; no armature modifier",
            "same_camera_and_floor": True,
            "images": {path.name: sha(path) for path in images},
        },
        "claims": {
            "standing_pose": "authored engineering candidate",
            "anatomical_validation": False,
            "motion_validation": "NOT_RUN",
            "unity_validation": "NOT_RUN",
        },
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
