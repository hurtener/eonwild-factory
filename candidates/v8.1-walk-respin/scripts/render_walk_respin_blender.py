#!/usr/bin/env python3
"""Render exactly one approval MP4 from the isolated V8.1 walk respin.

This candidate-owned wrapper reuses the accepted V8.1 renderer's scene and
film helpers read-only, deliberately bypassing its still/gallery paths.  It
does not write an image, alter the imported animation, or touch accepted V8.1
files.  The only editorial media it emits is the requested 10-second MP4.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy


ROOT = Path(__file__).resolve().parents[3]
ACCEPTED_RENDERER = ROOT / "showcase" / "v8.1" / "render_v8_1_blender.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--clip", required=True)
    parser.add_argument("--duration-seconds", type=float, default=10.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    return parser.parse_args(argv)


def accepted_renderer():
    if not ACCEPTED_RENDERER.is_file():
        raise RuntimeError(f"Missing accepted renderer: {ACCEPTED_RENDERER}")
    spec = importlib.util.spec_from_file_location("accepted_v8_1_renderer", ACCEPTED_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load accepted renderer helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_contact_readability_stage(ground: bpy.types.Object) -> dict[str, object]:
    """Presentation-only neutral floor treatment for toe-contact inspection."""
    if not ground.data.materials:
        raise RuntimeError("Walk review stage has no ground material")
    material = ground.data.materials[0]
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Walk review ground lacks a Principled BSDF")
    # A middle neutral value preserves a visible contact shadow without making
    # the floor compete with the animal silhouette.
    neutral_floor = (0.115, 0.135, 0.135, 1.0)
    bsdf.inputs["Base Color"].default_value = neutral_floor
    bsdf.inputs["Roughness"].default_value = 0.91
    for name, energy in (("SHOWCASE_KEY", 1325), ("SHOWCASE_FILL", 775), ("SHOWCASE_RIM", 925)):
        light = bpy.data.objects.get(name)
        if light is not None and hasattr(light.data, "energy"):
            light.data.energy = energy
    return {
        "groundBaseColor": list(neutral_floor),
        "groundRoughness": 0.91,
        "lighting": "neutral floor with raised existing key/fill/rim energies; no scene or animation changes",
    }


def main() -> None:
    cfg = parse_args()
    if cfg.duration_seconds != 10.0 or cfg.fps != 24:
        raise ValueError("Approval render is fixed at exactly 10.000 seconds and 24 fps")
    if cfg.output.exists() and any(cfg.output.iterdir()):
        raise RuntimeError(f"Refusing non-empty output directory: {cfg.output}")
    manifest = json.loads(cfg.manifest.read_text(encoding="utf-8"))
    clips = {clip["name"]: clip for clip in manifest.get("clips", [])}
    if cfg.clip not in clips:
        raise ValueError(f"Requested clip not in candidate manifest: {cfg.clip}")
    if not clips[cfg.clip].get("loop"):
        raise ValueError("Approval clip must be an explicitly looping walk")
    render = accepted_renderer()
    cfg.output.mkdir(parents=True)
    render.clean_scene()
    # glTF importer resolves sampler time using current scene FPS. Set this
    # before import to retain the baked 4.301075s clip duration at 24 fps.
    bpy.context.scene.render.fps = cfg.fps
    bpy.ops.import_scene.gltf(filepath=str(cfg.input), loglevel=0)
    imported = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "ARMATURE"}]
    armatures = [obj for obj in imported if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError(f"Expected one imported armature, received {len(armatures)}")
    armature = armatures[0]
    actions = render.action_map()
    if cfg.clip not in actions:
        raise RuntimeError(f"Candidate clip missing after glTF import: {cfg.clip}")
    bounds = render.sampled_deformed_bounds(bpy.context.scene, armature, actions, [clips[cfg.clip]])
    camera, ground = render.make_stage(bounds, "side")
    # The accepted renderer creates this only for attack/feeding readability;
    # hide it in a walk-only approval shot.
    proxy = bpy.data.objects.get("PROJECT_OWNED_TARGET_PROXY")
    if proxy is not None:
        proxy.hide_render = True
    render.world_setup()
    render.render_setup(cfg.width, cfg.height, cfg.fps)
    scene = bpy.context.scene
    contact_stage = apply_contact_readability_stage(ground)
    scene.camera = camera
    film = cfg.output / "walk-relaxed-v8-1-respin-side.mp4"
    render.render_film(
        scene, actions[cfg.clip], clips[cfg.clip], armature, film,
        cfg.fps, cfg.duration_seconds, cfg.duration_seconds,
    )
    report = {
        "renderer": "Blender candidate-owned walk-only wrapper",
        "blenderVersion": bpy.app.version_string,
        "acceptedRendererReadOnly": str(ACCEPTED_RENDERER),
        "inputGlb": str(cfg.input.resolve()),
        "inputGlbSha256": hashlib.sha256(cfg.input.read_bytes()).hexdigest(),
        "manifest": str(cfg.manifest.resolve()),
        "clip": cfg.clip,
        "durationSeconds": cfg.duration_seconds,
        "fps": cfg.fps,
        "frameCount": int(cfg.duration_seconds * cfg.fps),
        "resolution": [cfg.width, cfg.height],
        "view": "side",
        "targetProxyRendered": False,
        "contactReadabilityStage": contact_stage,
        "onlyEditorialMedia": str(film.resolve()),
        "boundsM": {"min": list(bounds[0]), "max": list(bounds[1])},
        "animationDataPolicy": "candidate GLB imported read-only; no action channels changed",
    }
    (cfg.output / "render-run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
