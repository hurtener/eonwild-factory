#!/usr/bin/env python3
"""Render one fixed three-quarter, walk-only V8.1/V8.2 review film.

The script imports a GLB read-only and delegates scene construction to the
accepted V8.1 renderer.  A supplied bounds file locks the second render to
the first render's framing; it never alters animation data or the source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
ACCEPTED_RENDERER = ROOT / "showcase/v8.1/render_v8_1_blender.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--locked-bounds", type=Path)
    parser.add_argument("--duration-seconds", type=float, default=10.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)


def renderer():
    spec = importlib.util.spec_from_file_location("accepted_v8_1_renderer", ACCEPTED_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"missing accepted renderer: {ACCEPTED_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_for_review(render, ground: bpy.types.Object) -> dict[str, object]:
    material = ground.data.materials[0]
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("review floor has no Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.115, 0.135, 0.135, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.91
    for name, energy in (("SHOWCASE_KEY", 1325), ("SHOWCASE_FILL", 775), ("SHOWCASE_RIM", 925)):
        light = bpy.data.objects.get(name)
        if light is not None:
            light.data.energy = energy
    return {"view": "threeq", "ground": [0.115, 0.135, 0.135, 1.0], "roughness": 0.91, "lights": [1325, 775, 925]}


def main() -> int:
    cfg = parse_args()
    if cfg.duration_seconds != 10.0 or cfg.fps != 24:
        raise RuntimeError("review render is fixed to 10.000 seconds at 24 fps")
    if cfg.output.exists() and any(cfg.output.iterdir()):
        raise RuntimeError(f"refusing non-empty output: {cfg.output}")
    manifest = json.loads(cfg.manifest.read_text(encoding="utf-8"))
    clips = {item["name"]: item for item in manifest["clips"]}
    if cfg.clip not in clips or not clips[cfg.clip].get("loop"):
        raise RuntimeError("requested clip must be an explicit looping manifest clip")
    render = renderer()
    cfg.output.mkdir(parents=True)
    render.clean_scene()
    bpy.context.scene.render.fps = cfg.fps
    bpy.ops.import_scene.gltf(filepath=str(cfg.input), loglevel=0)
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError(f"expected one armature, got {len(armatures)}")
    armature = armatures[0]
    actions = render.action_map()
    if cfg.clip not in actions:
        raise RuntimeError(f"missing imported clip: {cfg.clip}")
    if cfg.locked_bounds:
        locked = json.loads(cfg.locked_bounds.read_text(encoding="utf-8"))
        locked = locked.get("bounds", locked)
        bounds = (Vector(locked["min"]), Vector(locked["max"]))
        bounds_policy = "locked-from-approved-threeq"
    else:
        bounds = render.sampled_deformed_bounds(bpy.context.scene, armature, actions, [clips[cfg.clip]])
        bounds_policy = "measured-approved-threeq-source"
    camera, ground = render.make_stage(bounds, "threeq")
    proxy = bpy.data.objects.get("PROJECT_OWNED_TARGET_PROXY")
    if proxy is not None:
        proxy.hide_render = True
    render.world_setup()
    render.render_setup(cfg.width, cfg.height, cfg.fps)
    stage = stage_for_review(render, ground)
    scene = bpy.context.scene
    scene.camera = camera
    film = cfg.output / "walk-relaxed-threeq.mp4"
    render.render_film(scene, actions[cfg.clip], clips[cfg.clip], armature, film, cfg.fps, cfg.duration_seconds, cfg.duration_seconds)
    report = {"schema": "eonwild.v8_2.threeq_review_render.v1", "status": "PASS", "blenderVersion": bpy.app.version_string, "inputGlb": str(cfg.input.resolve()), "inputSha256": hashlib.sha256(cfg.input.read_bytes()).hexdigest(), "manifest": str(cfg.manifest.resolve()), "clip": cfg.clip, "durationSeconds": 10.0, "fps": 24, "frameCount": 240, "resolution": [cfg.width, cfg.height], "bounds": {"min": list(bounds[0]), "max": list(bounds[1]), "policy": bounds_policy}, "stage": stage, "onlyEditorialMedia": str(film.resolve()), "animationDataPolicy": "import read-only; no action channels changed"}
    (cfg.output / "render-run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
