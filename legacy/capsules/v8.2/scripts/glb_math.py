#!/usr/bin/env python3
"""Minimal quaternion and GLB helpers used by the V8.2 release scripts."""
from __future__ import annotations

import json
from pathlib import Path
import struct

import numpy as np


def q_normal(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    return q / np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-15)


def q_inv(q: np.ndarray) -> np.ndarray:
    q = q_normal(q)
    return np.concatenate([-q[..., :3], q[..., 3:4]], axis=-1)


def q_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    av, aw = a[..., :3], a[..., 3:4]
    bv, bw = b[..., :3], b[..., 3:4]
    vector = aw * bv + bw * av + np.cross(av, bv)
    scalar = aw * bw - np.sum(av * bv, axis=-1, keepdims=True)
    return q_normal(np.concatenate([vector, scalar], axis=-1))


def q_from_rotvec(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float64)
    angle = np.linalg.norm(vector, axis=-1, keepdims=True)
    half = angle * 0.5
    scale = np.empty_like(angle)
    np.divide(np.sin(half), angle, out=scale, where=angle > 1e-12)
    scale[angle <= 1e-12] = 0.5 - angle[angle <= 1e-12] ** 2 / 48.0
    return q_normal(np.concatenate([vector * scale, np.cos(half)], axis=-1))


def q_to_rotvec(q: np.ndarray) -> np.ndarray:
    q = q_normal(q)
    q = q if q[..., 3] >= 0.0 else -q
    vector = q[:3]
    scalar = float(np.clip(q[3], -1.0, 1.0))
    length = np.linalg.norm(vector)
    angle = 2.0 * np.arctan2(length, scalar)
    return vector * (angle / max(length, 1e-15))


class Glb:
    """Read the JSON and binary chunks needed for deterministic in-place edits."""

    _WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

    def __init__(self, path: Path):
        self.path = path
        self.raw = path.read_bytes()
        magic, version, total = struct.unpack_from("<4sII", self.raw, 0)
        if magic != b"glTF" or version != 2 or total != len(self.raw):
            raise ValueError("invalid GLB")
        cursor = 12
        self.bin_start = None
        self.binary = None
        self.json = None
        while cursor < len(self.raw):
            length, kind = struct.unpack_from("<II", self.raw, cursor)
            cursor += 8
            chunk = self.raw[cursor:cursor + length]
            if kind == 0x4E4F534A:
                self.json = json.loads(chunk.decode("utf-8"))
            elif kind == 0x004E4942:
                self.bin_start, self.binary = cursor, chunk
            cursor += length
        if self.json is None or self.bin_start is None or self.binary is None:
            raise ValueError("GLB missing JSON or BIN chunk")
        self.nodes = self.json["nodes"]
        self.name_to_node = {
            node.get("name", f"node_{index}"): index
            for index, node in enumerate(self.nodes)
        }
        self.parents: list[int | None] = [None] * len(self.nodes)
        for parent, node in enumerate(self.nodes):
            for child in node.get("children", []):
                self.parents[int(child)] = parent
        self.rest_rotation = [
            np.asarray(node.get("rotation", [0.0, 0.0, 0.0, 1.0]), dtype=np.float64)
            for node in self.nodes
        ]

    def accessor_layout(self, index: int) -> tuple[dict, dict, int]:
        item = self.json["accessors"][index]
        view = self.json["bufferViews"][item["bufferView"]]
        width = self._WIDTHS.get(item["type"])
        if width is None:
            raise ValueError(f"unsupported accessor type: {index}")
        return item, view, width

    def accessor(self, index: int) -> np.ndarray:
        item, view, width = self.accessor_layout(index)
        if item["componentType"] != 5126:
            raise ValueError(f"unsupported accessor component: {index}")
        offset = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
        return np.frombuffer(
            self.binary,
            dtype="<f4",
            count=int(item["count"]) * width,
            offset=offset,
        ).reshape((-1, width)).astype(np.float64)

    def animation(self, name: str) -> dict:
        for animation in self.json.get("animations", []):
            if animation.get("name") == name:
                return animation
        raise KeyError(name)

    def rotation_channels(self, name: str) -> list[tuple[str, dict]]:
        animation = self.animation(name)
        output = []
        for channel in animation["channels"]:
            if channel["target"]["path"] != "rotation":
                continue
            node = self.nodes[channel["target"]["node"]].get("name")
            output.append((node, animation["samplers"][channel["sampler"]]))
        return output

    def rotation_accessors(self, name: str) -> dict[str, int]:
        return {
            node: int(sampler["output"])
            for node, sampler in self.rotation_channels(name)
        }

    def accessor_offset(self, index: int) -> tuple[int, int]:
        item, view, _ = self.accessor_layout(index)
        if (
            item["componentType"] != 5126
            or item["type"] != "VEC4"
            or int(view.get("byteStride", 16)) != 16
        ):
            raise ValueError(f"unexpected rotation accessor: {index}")
        offset = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
        return offset, int(item["count"])


def all_worlds(glb: Glb, local_rotations: list[np.ndarray]) -> list[np.ndarray]:
    worlds: list[np.ndarray | None] = [None] * len(local_rotations)

    def resolve(index: int) -> np.ndarray:
        if worlds[index] is None:
            parent = glb.parents[index]
            worlds[index] = (
                local_rotations[index]
                if parent is None
                else q_mul(resolve(int(parent)), local_rotations[index])
            )
        return worlds[index]  # type: ignore[return-value]

    return [resolve(index) for index in range(len(local_rotations))]
