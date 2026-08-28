from __future__ import annotations

import json
from pathlib import Path
import struct
from typing import Any

from ..errors import ValidationFailure


_COMPONENTS = {
    5120: ("b", 1),
    5121: ("B", 1),
    5122: ("h", 2),
    5123: ("H", 2),
    5125: ("I", 4),
    5126: ("f", 4),
}
_WIDTHS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


class Glb:
    def __init__(self, path: Path | None = None, *, raw: bytes | None = None):
        if (path is None) == (raw is None):
            raise ValueError("provide exactly one of path or raw")
        self.path = path
        self.raw = path.read_bytes() if path is not None else bytes(raw)
        if len(self.raw) < 20:
            raise ValidationFailure("GLB is truncated")
        magic, version, total = struct.unpack_from("<4sII", self.raw, 0)
        if magic != b"glTF" or version != 2 or total != len(self.raw):
            raise ValidationFailure("invalid GLB header")
        cursor = 12
        document = None
        self.bin_start = None
        self.binary = None
        while cursor < len(self.raw):
            length, kind = struct.unpack_from("<II", self.raw, cursor)
            cursor += 8
            chunk = self.raw[cursor:cursor + length]
            if len(chunk) != length:
                raise ValidationFailure("GLB chunk exceeds file")
            if kind == 0x4E4F534A:
                document = json.loads(chunk.decode("utf-8"))
            elif kind == 0x004E4942:
                self.bin_start, self.binary = cursor, chunk
            cursor += length
        if document is None or self.binary is None or self.bin_start is None:
            raise ValidationFailure("GLB requires JSON and BIN chunks")
        self.document: dict[str, Any] = document
        self.nodes = self.document["nodes"]
        self.name_to_node = {
            node.get("name", f"node_{index}"): index
            for index, node in enumerate(self.nodes)
        }
        self.parents: list[int | None] = [None] * len(self.nodes)
        for parent, node in enumerate(self.nodes):
            for child in node.get("children", []):
                child = int(child)
                if self.parents[child] is not None:
                    raise ValidationFailure("node has multiple parents")
                self.parents[child] = parent
        self.rest_rotation = [
            tuple(float(value) for value in node.get("rotation", [0, 0, 0, 1]))
            for node in self.nodes
        ]
        self.rest_translation = [
            tuple(float(value) for value in node.get("translation", [0, 0, 0]))
            for node in self.nodes
        ]
        self.rest_scale = [
            tuple(float(value) for value in node.get("scale", [1, 1, 1]))
            for node in self.nodes
        ]

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Glb":
        return cls(raw=raw)

    def accessor_layout(self, index: int) -> tuple[dict, dict, int, int, str]:
        item = self.document["accessors"][index]
        if "bufferView" not in item:
            raise ValidationFailure(f"sparse-only accessor is unsupported: {index}")
        view = self.document["bufferViews"][item["bufferView"]]
        component = _COMPONENTS.get(item["componentType"])
        width = _WIDTHS.get(item["type"])
        if component is None or width is None:
            raise ValidationFailure(f"unsupported accessor layout: {index}")
        code, component_size = component
        return item, view, width, component_size, code

    def accessor_values(self, index: int) -> list[tuple[float | int, ...]]:
        item, view, width, component_size, code = self.accessor_layout(index)
        item_size = width * component_size
        stride = int(view.get("byteStride", item_size))
        if stride < item_size:
            raise ValidationFailure(f"accessor stride is too small: {index}")
        start = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
        values = []
        for row in range(int(item["count"])):
            offset = start + row * stride
            end = offset + item_size
            if end > len(self.binary):
                raise ValidationFailure(f"accessor exceeds BIN chunk: {index}")
            values.append(struct.unpack_from("<" + code * width, self.binary, offset))
        return values

    def accessor_region(self, index: int) -> tuple[int, int, int]:
        item, view, width, component_size, _ = self.accessor_layout(index)
        item_size = width * component_size
        stride = int(view.get("byteStride", item_size))
        offset = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
        return offset, int(item["count"]), stride

    def accessor_bytes(self, index: int) -> bytes:
        item, view, width, component_size, _ = self.accessor_layout(index)
        item_size = width * component_size
        offset, count, stride = self.accessor_region(index)
        return b"".join(
            self.binary[offset + row * stride:offset + row * stride + item_size]
            for row in range(count)
        )

    def animation(self, name: str) -> dict[str, Any]:
        for animation in self.document.get("animations", []):
            if animation.get("name") == name:
                return animation
        raise ValidationFailure(f"animation not found: {name}")

    def rotation_channels(self, name: str) -> list[tuple[str, dict[str, Any]]]:
        return self.animation_channels(name, "rotation")

    def animation_channels(
        self, name: str, property_name: str | None = None
    ) -> list[tuple[str, str, dict[str, Any]] | tuple[str, dict[str, Any]]]:
        animation = self.animation(name)
        output = []
        for channel in animation["channels"]:
            path = channel["target"]["path"]
            if property_name is not None and path != property_name:
                continue
            node_name = self.nodes[channel["target"]["node"]].get("name")
            if not isinstance(node_name, str):
                raise ValidationFailure("animation target node has no name")
            sampler = animation["samplers"][channel["sampler"]]
            output.append(
                (node_name, sampler)
                if property_name is not None
                else (node_name, path, sampler)
            )
        return output

    def rotation_accessors(self, name: str) -> dict[str, int]:
        return {
            node: int(sampler["output"])
            for node, sampler in self.rotation_channels(name)
        }

    def animation_accessors(self, name: str, property_name: str) -> dict[str, int]:
        return {
            node: int(sampler["output"])
            for node, sampler in self.animation_channels(name, property_name)
        }

    def node_parent_name(self, name: str) -> str | None:
        if name not in self.name_to_node:
            raise ValidationFailure(f"node not found: {name}")
        parent = self.parents[self.name_to_node[name]]
        return None if parent is None else self.nodes[parent].get("name")
