#!/usr/bin/env python3
"""Regenerate the approved V8.2 GLB from the included iteration-b base."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import numpy as np

PKG = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("glb_math", PKG / "scripts/glb_math.py")
g = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(g)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_locals(glb, tracks, sample):
    output = []
    for index, node in enumerate(glb.nodes):
        name = node.get("name", f"node_{index}")
        output.append(
            tracks[name][sample] if name in tracks else glb.rest_rotation[index]
        )
    return output


def power(q, fraction):
    return g.q_from_rotvec(g.q_to_rotvec(q) * fraction)


def contract_roles(contract):
    roles = contract["roles"]
    return roles["pelvis"], roles["chest"], [*roles["neck"], roles["head"]]


def resolve_parent_selector(contract, selector):
    roles = contract["roles"]
    if selector == "spine_parent":
        return contract["spineParent"]
    if selector.startswith("neck:"):
        try:
            return roles["neck"][int(selector.split(":", 1)[1])]
        except (ValueError, IndexError) as exc:
            raise RuntimeError(f"invalid expected-parent selector: {selector}") from exc
    if selector in roles and isinstance(roles[selector], str):
        return roles[selector]
    raise RuntimeError(f"invalid expected-parent selector: {selector}")


def expected_parent_pairs(contract):
    roles = contract["roles"]
    expected = contract["expectedParents"]
    neck_roles = roles["neck"]
    neck_parents = expected["neck"]
    if len(neck_roles) != len(neck_parents):
        raise RuntimeError("expectedParents.neck length mismatch")
    pairs = [
        (roles["pelvis"], resolve_parent_selector(contract, expected["pelvis"])),
        (roles["chest"], resolve_parent_selector(contract, expected["chest"])),
    ]
    pairs.extend(
        (name, resolve_parent_selector(contract, selector))
        for name, selector in zip(neck_roles, neck_parents)
    )
    pairs.append(
        (roles["head"], resolve_parent_selector(contract, expected["head"]))
    )
    return pairs


def validate(glb, contract, clip):
    pelvis, chest, neck = contract_roles(contract)
    names = [pelvis, chest, *neck]
    channels = glb.rotation_channels(clip)
    by_name = {name: sampler for name, sampler in channels}

    if any(name not in glb.name_to_node or name not in by_name for name in names):
        raise RuntimeError("semantic role missing animation rotation")

    for name, expected_parent in expected_parent_pairs(contract):
        index = glb.name_to_node[name]
        parent_index = glb.parents[index]
        actual_parent = (
            glb.nodes[parent_index].get("name") if parent_index is not None else None
        )
        if actual_parent != expected_parent:
            raise RuntimeError(
                f"hierarchy contract mismatch for {name}: "
                f"expected {expected_parent}, got {actual_parent}"
            )

    accessor_contract = contract["accessorContract"]
    required_fields = {
        "componentType",
        "type",
        "byteStride",
        "commonTimeline",
        "interpolation",
    }
    missing = required_fields - set(accessor_contract)
    if missing:
        raise RuntimeError(f"missing accessor contract fields: {sorted(missing)}")
    if accessor_contract["commonTimeline"] is not True:
        raise RuntimeError("accessor contract requires commonTimeline=true")

    common_times = None
    rotations = {}
    for name, sampler in channels:
        interpolation = sampler.get("interpolation", "LINEAR")
        if interpolation != accessor_contract["interpolation"]:
            raise RuntimeError(
                f"interpolation contract mismatch for {name}: {interpolation}"
            )
        output_index = int(sampler["output"])
        item, view, _ = glb.accessor_layout(output_index)
        stride = int(view.get("byteStride", 16))
        if (
            item["componentType"] != accessor_contract["componentType"]
            or item["type"] != accessor_contract["type"]
            or stride != accessor_contract["byteStride"]
        ):
            raise RuntimeError(f"accessor contract mismatch for {name}")
        input_times = glb.accessor(int(sampler["input"])).reshape(-1)
        if common_times is None:
            common_times = input_times
        elif not np.array_equal(common_times, input_times):
            raise RuntimeError(f"common timeline contract mismatch for {clip}")
        rotations[name] = glb.accessor(output_index)

    if common_times is None:
        raise RuntimeError(f"no rotation tracks: {clip}")
    if any(rows.shape[0] != common_times.shape[0] for rows in rotations.values()):
        raise RuntimeError(f"rotation count/timeline mismatch for {clip}")
    return common_times, rotations


def solve(glb, clip, config):
    contract = config["contract"]
    _, tracks = validate(glb, contract, clip)
    pelvis_name, chest, neck = contract_roles(contract)
    names = [chest, *neck]
    values = {
        name: np.empty_like(tracks[name], dtype=np.float64) for name in names
    }
    pelvis = glb.name_to_node[pelvis_name]
    chest_index = glb.name_to_node[chest]
    reference = None
    for sample in range(len(next(iter(tracks.values())))):
        local = load_locals(glb, tracks, sample)
        world = g.all_worlds(glb, local)
        if reference is None:
            reference = world[pelvis]
        pelvis_roll = g.q_to_rotvec(
            g.q_mul(world[pelvis], g.q_inv(reference))
        )[int(contract["basis"]["rotationVectorAxis"])]
        relative = g.q_mul(world[chest_index], g.q_inv(world[pelvis]))
        chest_world = g.q_mul(
            g.q_from_rotvec(
                g.q_to_rotvec(relative)
                + np.asarray(
                    [0.0, 0.0, -float(contract["chestRollGain"]) * pelvis_roll]
                )
            ),
            world[pelvis],
        )
        delta = g.q_mul(chest_world, g.q_inv(world[chest_index]))
        target = list(world)
        parent = glb.parents[chest_index]
        values[chest][sample] = (
            chest_world
            if parent is None
            else g.q_mul(g.q_inv(target[int(parent)]), chest_world)
        )
        target[chest_index] = chest_world
        for name, residual in zip(neck, contract["neckResidualFractions"]):
            index = glb.name_to_node[name]
            desired = g.q_mul(power(delta, float(residual)), world[index])
            parent = glb.parents[index]
            values[name][sample] = (
                desired
                if parent is None
                else g.q_mul(g.q_inv(target[int(parent)]), desired)
            )
            target[index] = desired

    for rows in values.values():
        for sample in range(1, len(rows)):
            if np.dot(rows[sample - 1], rows[sample]) < 0:
                rows[sample] *= -1
        rows[-1] = rows[0]

    limits = {
        chest: float(contract["maxChestLocalDeltaDegrees"]),
        **{
            name: float(contract["maxNeckLocalDeltaDegrees"])
            for name in neck
        },
    }
    for name, rows in values.items():
        base = tracks[name]
        maximum = max(
            float(
                np.degrees(
                    np.linalg.norm(
                        g.q_to_rotvec(g.q_mul(g.q_inv(base[sample]), rows[sample]))
                    )
                )
            )
            for sample in range(len(rows))
        )
        if maximum > limits[name] + 1e-6:
            raise RuntimeError(f"local delta bound exceeded {name}: {maximum}")
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default=PKG / "config/release.json", type=Path
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    )
    config = json.loads(args.config.read_text())
    base = PKG / config["base"]
    output = args.output or (PKG / config["output"])
    if sha(base) != config["baseSha256"]:
        raise RuntimeError("included base SHA mismatch")
    glb = g.Glb(base)
    raw = bytearray(glb.raw)
    for clip in config["walkClips"]:
        result = solve(glb, clip, config)
        accessors = glb.rotation_accessors(clip)
        for name, rows in result.items():
            offset, count = glb.accessor_offset(accessors[name])
            raw[
                glb.bin_start + offset:glb.bin_start + offset + count * 16
            ] = rows.astype("<f4").tobytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    actual = sha(output)
    if actual != config["outputSha256"]:
        raise RuntimeError(f"reproduction SHA mismatch: {actual}")
    print(
        json.dumps(
            {"status": "PASS", "output": str(output), "sha256": actual},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
