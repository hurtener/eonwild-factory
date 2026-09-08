#!/usr/bin/env python3
"""Bounded tail bilateral geometry and front-camera projection audit.

This is a kinematic/material diagnostic.  Projected vertex exposure is a
point-sampled silhouette proxy, not a raster visibility or biological claim.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np

from eonwild_motion.factory.animal import scaled_contact_profile
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.skin_rig import SkinRig


ARC = Path("/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521")
ENGINE = ARC / "worktrees/eonwild-source-cubic-published-integration"
ENGINE_HEAD = "f9ca924bcc79943d2d2b7eeab28bef8763c18ec4"
ENGINE_TREE = "91f63ac2efb1bbc49e0ae85cadb13fcac97722b2"
PACKAGE = ARC / "out/source-cubic-adult-v10-f9ca924"
CUBIC_CAMERA = ARC / "out/source-cubic-adult-v10-f9ca924-native-review-001/front-body/camera.json"
SHALLOW_CAMERA = ARC / "out/continuation-adult-v10-load-acceptance-low-front-shallow-001/camera/front-low-shallow.json"
SHALLOW_FILM = ARC / "out/continuation-adult-v10-load-acceptance-low-front-shallow-001/v10/preview.mp4"
OUTPUT = Path(__file__).with_name("result.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments), cwd=ENGINE, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def verify_package(path: Path) -> dict:
    manifest = json.loads((path / "manifest.json").read_text())
    actual = {name: sha(path / name) for name in manifest["files"]}
    if actual != manifest["files"]:
        raise RuntimeError("immutable V10 package manifest mismatch")
    return manifest


def canonical_to_blender(points: np.ndarray) -> np.ndarray:
    return np.stack((points[..., 0], -points[..., 2], points[..., 1]), axis=-1)


def canonical_from_blender(vector: np.ndarray) -> np.ndarray:
    return np.asarray((vector[0], vector[2], -vector[1]), dtype=float)


def camera_basis(camera: dict) -> dict:
    center = np.asarray(camera["center_relative_root"], dtype=float)
    position = np.asarray(camera["position_relative_root"], dtype=float)
    view = position - center
    view /= np.linalg.norm(view)
    # ``view`` points from target toward camera. Blender camera local +X is
    # world-up cross view (the opposite ordering mirrors screen horizontal).
    right = np.cross((0.0, 0.0, 1.0), view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    up /= np.linalg.norm(up)
    canonical_view = canonical_from_blender(view)
    canonical_right = canonical_from_blender(right)
    return {
        "center": center,
        "position": position,
        "view": view,
        "right": right,
        "up": up,
        "canonical_view": canonical_view,
        "canonical_right": canonical_right,
    }


def axis_aligned_basis(camera: dict) -> dict:
    original = camera_basis(camera)
    view = original["canonical_view"]
    aligned = np.asarray((0.0, view[1], math.hypot(view[0], view[2])))
    aligned /= np.linalg.norm(aligned)
    blender_view = canonical_to_blender(aligned)
    right = np.cross((0.0, 0.0, 1.0), blender_view)
    right /= np.linalg.norm(right)
    up = np.cross(blender_view, right)
    up /= np.linalg.norm(up)
    distance = float(np.linalg.norm(original["position"] - original["center"]))
    return {
        "center": original["center"],
        "position": original["center"] + blender_view * distance,
        "view": blender_view,
        "right": right,
        "up": up,
        "canonical_view": aligned,
        "canonical_right": canonical_from_blender(right),
    }


class Package:
    def __init__(self, path: Path):
        self.path = path
        self.manifest = verify_package(path)
        self.recipe = json.loads((path / "recipe.json").read_text())
        self.runtime = json.loads((path / "runtime.json").read_text())
        self.biomechanics = json.loads((path / "biomechanics.json").read_text())
        self.glb = Glb.from_bytes((path / "root_motion.glb").read_bytes())
        contact_path = ENGINE / self.recipe["contact_profile"]["path"]
        if sha(contact_path) != self.recipe["contact_profile"]["sha256"]:
            raise RuntimeError("contact profile binding mismatch")
        contact = scaled_contact_profile(
            json.loads(contact_path.read_text()),
            self.biomechanics["geometry"]["uniform_scale"],
        )
        roles = self.runtime["rig_roles"]
        self.rig = SkinRig(
            self.glb, roles, self.runtime["forward_axis"],
            self.runtime["up_axis"], contact,
        )
        name = self.glb.document["animations"][0]["name"]
        self.tracks, self.timeline = read_animation_tracks(
            self.glb, name, require_common_timeline=True,
        )
        if any(track.interpolation != "CUBICSPLINE" for track in self.tracks.values()):
            raise RuntimeError("audit requires exact CUBICSPLINE V10")
        self.duration = float(self.timeline[-1])
        nodes = self.glb.name_to_node
        self.root = nodes[roles["root"]]
        self.tail = np.asarray([nodes[name] for name in roles["tail"]], dtype=int)
        for parent, child in zip(self.tail[:-1], self.tail[1:]):
            if self.glb.parents[child] != parent:
                raise RuntimeError("semantic tail is not a contiguous base-to-tip chain")
        self.tail_strength = np.sum(
            self.rig.weights * np.isin(self.rig.node_ids, self.tail), axis=1)
        self.tail_material = np.flatnonzero(self.tail_strength >= 0.5)
        self.other_material = np.flatnonzero(self.tail_strength < 0.5)
        if len(self.tail_material) != 10_557:
            raise RuntimeError("tail material membership changed")

    def worlds(self, time_s: float) -> np.ndarray:
        time_s = float(time_s) % self.duration
        translations = np.asarray(self.glb.rest_translation, dtype=float).copy()
        rotations = np.asarray(self.glb.rest_rotation, dtype=float).copy()
        scales = np.asarray(self.glb.rest_scale, dtype=float).copy()
        destinations = {"translation": translations, "rotation": rotations, "scale": scales}
        for (node, path), track in self.tracks.items():
            destinations[path][node] = track.sample(time_s)
        return self.rig.world(translations, rotations, scales)

    def root_relative_skin(self, worlds: np.ndarray) -> np.ndarray:
        return self.rig.skin(worlds) - worlds[self.root, :3, 3]

    def root_relative_tail_joints(self, worlds: np.ndarray) -> np.ndarray:
        return worlds[self.tail, :3, 3] - worlds[self.root, :3, 3]


def nearest_reflection_distances(points_ful: np.ndarray) -> np.ndarray:
    reflected = points_ful.copy()
    reflected[:, 2] *= -1.0
    result = np.full(len(points_ful), math.inf)
    for start in range(0, len(points_ful), 128):
        block = reflected[start : start + 128]
        squared = np.sum((block[:, None, :] - points_ful[None, :, :]) ** 2, axis=2)
        result[start : start + len(block)] = np.sqrt(np.min(squared, axis=1))
    return result


def exposure_proxy(xyz: np.ndarray, package: Package, camera: dict, basis: dict) -> dict:
    """Point-sampled projected tail extent beyond non-tail vertex envelopes."""
    blender = canonical_to_blender(xyz)
    horizontal = (blender - basis["center"]) @ basis["right"]
    vertical = (blender - basis["center"]) @ basis["up"]
    scale = float(camera["orthographic_scale"])
    px = 320.0 + horizontal / (scale * 640.0 / 360.0) * 640.0
    py = 180.0 - vertical / scale * 360.0
    body_x = px[package.other_material]
    body_y = py[package.other_material]
    tail_x = px[package.tail_material]
    tail_y = py[package.tail_material]
    left, right = [], []
    for x, y in zip(tail_x, tail_y):
        near = np.abs(body_y - y) <= 1.0
        if not np.any(near):
            continue
        lower, upper = float(body_x[near].min()), float(body_x[near].max())
        if x < lower - 0.5:
            left.append(lower - x)
        if x > upper + 0.5:
            right.append(x - upper)
    return {
        "classification": "point-sampled projected extent; not triangle raster visibility or depth proof",
        "screen_left_vertex_count": len(left),
        "screen_right_vertex_count": len(right),
        "maximum_screen_left_extent_pixels": max(left, default=0.0),
        "maximum_screen_right_extent_pixels": max(right, default=0.0),
        "tail_screen_x_range_pixels": [float(tail_x.min()), float(tail_x.max())],
    }


if git("rev-parse", "HEAD") != ENGINE_HEAD or git("rev-parse", "HEAD^{tree}") != ENGINE_TREE:
    raise RuntimeError("source reader checkout identity changed")
if git("status", "--porcelain"):
    raise RuntimeError("source reader checkout is dirty")

package = Package(PACKAGE)
forward, up, lateral = package.rig.forward, package.rig.up, package.rig.lateral
duration = package.duration
neutral_world = package.rig.neutral_world
neutral_root = neutral_world[package.root, :3, 3]
neutral_joints = neutral_world[package.tail, :3, 3] - neutral_root
neutral_skin = package.rig.skin(neutral_world, package.tail_material) - neutral_root
neutral_ful = np.stack(
    (neutral_skin @ forward, neutral_skin @ up, neutral_skin @ lateral), axis=1)
reflection_distances = nearest_reflection_distances(neutral_ful)
neutral_lateral = neutral_ful[:, 2]

sample_times = np.linspace(0.0, duration, 297, endpoint=False)
joint_lateral = []
material_lateral = []
for time_s in sample_times:
    worlds = package.worlds(time_s)
    joint_lateral.append(package.root_relative_tail_joints(worlds) @ lateral)
    material_lateral.append(
        package.root_relative_skin(worlds)[package.tail_material] @ lateral)
joint_lateral = np.asarray(joint_lateral)
material_lateral = np.asarray(material_lateral)
joint_center = joint_lateral.mean(axis=0)
material_center = material_lateral.mean(axis=0)

pair_times = np.linspace(0.0, duration / 2.0, 149, endpoint=False)
joint_residuals = []
material_residuals = []
for time_s in pair_times:
    first = package.worlds(time_s)
    second = package.worlds(time_s + duration / 2.0)
    first_joints = package.root_relative_tail_joints(first) @ lateral
    second_joints = package.root_relative_tail_joints(second) @ lateral
    first_material = package.root_relative_skin(first)[package.tail_material] @ lateral
    second_material = package.root_relative_skin(second)[package.tail_material] @ lateral
    joint_residuals.append((first_joints - joint_center) + (second_joints - joint_center))
    material_residuals.append(
        (first_material - material_center) + (second_material - material_center))
joint_residuals = np.asarray(joint_residuals)
material_residuals = np.asarray(material_residuals)

cameras = {}
for label, path in (("current_cubic_front", CUBIC_CAMERA), ("older_shallow_front", SHALLOW_CAMERA)):
    camera = json.loads(path.read_text())
    actual = camera_basis(camera)
    aligned = axis_aligned_basis(camera)
    yaw = math.degrees(math.atan2(
        float(actual["canonical_view"] @ lateral),
        float(actual["canonical_view"] @ forward),
    ))
    cameras[label] = {
        "path": str(path),
        "sha256": sha(path),
        "camera": camera,
        "declared_axis_yaw_degrees": yaw,
        "screen_right_canonical_f_u_l": [
            float(actual["canonical_right"] @ axis)
            for axis in (forward, up, lateral)
        ],
        "axis_aligned_position_relative_root": aligned["position"].tolist(),
        "axis_aligned_position_preserves_target_distance_elevation": True,
        "double_support_projection_witnesses": [],
    }
    for frame in (4, 41):
        time_s = frame / 30.0
        xyz = package.root_relative_skin(package.worlds(time_s))
        cameras[label]["double_support_projection_witnesses"].append({
            "frame": frame,
            "time_s": time_s,
            "inherited_yaw_camera": exposure_proxy(xyz, package, camera, actual),
            "corrected_axis_camera": exposure_proxy(xyz, package, camera, aligned),
        })

result = {
    "schema": "eonwild.motion.adult-v10-tail-bilateral-audit.v1",
    "classification": "read-only kinematic, skin-weight and camera-projection diagnostic",
    "source": {
        "engine_head": ENGINE_HEAD,
        "engine_tree": ENGINE_TREE,
        "root_motion_glb_sha256": sha(PACKAGE / "root_motion.glb"),
        "manifest_sha256": sha(PACKAGE / "manifest.json"),
        "plan_sha256": sha(PACKAGE / "plan.json"),
        "runtime_sha256": sha(PACKAGE / "runtime.json"),
        "duration_s": duration,
        "key_count": len(package.timeline),
        "shallow_linear_film_sha256": sha(SHALLOW_FILM),
    },
    "declared_frame": {
        "forward": forward.tolist(),
        "up": up.tolist(),
        "lateral": lateral.tolist(),
        "positive_lateral_semantic": "right according to admitted bilateral hip ordering",
    },
    "neutral_rig_and_skin": {
        "tail_roles": [package.glb.nodes[index]["name"] for index in package.tail],
        "tail_parent_indices": [package.glb.parents[index] for index in package.tail],
        "tail_joint_lateral_m": (neutral_joints @ lateral).tolist(),
        "tail_material_definition": "all normalized skin influences; aggregate semantic-tail weight >= 0.5",
        "tail_material_vertex_count": len(package.tail_material),
        "tail_material_negative_positive_lateral_counts": [
            int(np.sum(neutral_lateral < 0.0)), int(np.sum(neutral_lateral > 0.0))],
        "tail_material_lateral_quantiles_m": {
            str(q): float(np.quantile(neutral_lateral, q))
            for q in (0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0)
        },
        "reflected_nearest_vertex_distance_quantiles_m": {
            str(q): float(np.quantile(reflection_distances, q))
            for q in (0.0, 0.5, 0.9, 0.95, 0.99, 1.0)
        },
        "reflection_limit": "nearest-vertex distance is tessellation-sensitive; it does not pair topology or prove a symmetric volume",
    },
    "animated_bilateral": {
        "half_cycle_s": duration / 2.0,
        "exact_pair_count": len(pair_times),
        "tail_tip_lateral_min_max_m": [
            float(joint_lateral[:, -1].min()), float(joint_lateral[:, -1].max())],
        "tail_tip_lateral_peak_to_peak_m": float(np.ptp(joint_lateral[:, -1])),
        "tail_material_centroid_lateral_min_max_m": [
            float(material_lateral.mean(axis=1).min()),
            float(material_lateral.mean(axis=1).max()),
        ],
        "tail_material_centroid_lateral_peak_to_peak_m": float(
            np.ptp(material_lateral.mean(axis=1))),
        "joint_half_cycle_antisymmetry_residual_m": {
            "maximum": float(np.max(np.abs(joint_residuals))),
            "rms": float(np.sqrt(np.mean(joint_residuals ** 2))),
        },
        "corresponding_material_half_cycle_antisymmetry_residual_m": {
            "maximum": float(np.max(np.abs(material_residuals))),
            "p99": float(np.quantile(np.abs(material_residuals), 0.99)),
            "rms": float(np.sqrt(np.mean(material_residuals ** 2))),
        },
    },
    "cameras": cameras,
    "conclusion": {
        "one_sided_tail_joint_motion": "NOT_OBSERVED",
        "perfect_neutral_material_symmetry": "NOT_ESTABLISHED",
        "camera_alignment": (
            "Both reviewed front cameras retain a 2.231-degree azimuth from the old source axis; "
            "the admitted corrected model forward is exact +Z. Screen right maps almost exactly "
            "to negative declared lateral. The inherited yaw changes projected tail exposure and "
            "can make one half-cycle more legible through body occlusion."
        ),
        "action": (
            "Do not change the rig or tail law from this evidence. Compare the two double-support "
            "poses with one corrected-axis camera at the same target, distance, elevation and scale."
        ),
    },
    "limitations": [
        "The point-sampled exposure proxy does not rasterize triangles or prove pixel visibility.",
        "Neutral nearest-vertex reflection is sensitive to asymmetric tessellation and does not prove a symmetric volume.",
        "The older shallow movie uses the prior LINEAR package; it is presentation evidence only.",
        "This audit does not establish tail mass, inertia, force, COM, biological accuracy, production approval or Unity parity.",
    ],
}
OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
print(json.dumps({"output": str(OUTPUT), "sha256": sha(OUTPUT)}, indent=2))
