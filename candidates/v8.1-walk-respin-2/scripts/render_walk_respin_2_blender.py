#!/usr/bin/env python3
"""Walk-only approval renderer for respin 2; emits one MP4 and metadata."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "candidates" / "v8.1-walk-respin" / "scripts" / "render_walk_respin_blender.py"


def lighter_contact_stage(ground: bpy.types.Object) -> dict[str, object]:
    if not ground.data.materials:
        raise RuntimeError("Walk review stage has no ground material")
    material = ground.data.materials[0]
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Walk review ground lacks a Principled BSDF")
    neutral_floor = (0.32, 0.34, 0.34, 1.0)
    bsdf.inputs["Base Color"].default_value = neutral_floor
    bsdf.inputs["Roughness"].default_value = 0.92
    return {
        "groundBaseColor": list(neutral_floor),
        "groundRoughness": 0.92,
        "lighting": "lighter neutral floor retained solely to expose metatarsal rise and toe-only contact shadow",
    }


def main() -> None:
    spec = importlib.util.spec_from_file_location("respin_1_walk_renderer", PARENT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Missing read-only parent renderer: {PARENT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply_contact_readability_stage = lighter_contact_stage
    module.main()


if __name__ == "__main__":
    main()
