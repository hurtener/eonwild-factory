"""Minimal GLB 2.0 I/O used by the Eonwild procedural animation skill v2.

The implementation intentionally avoids Blender for inspection, testing, and baking. It
preserves the original JSON, binary payload, skin joint order, inverse-bind matrices,
materials, and textures, then appends animation accessors/channels.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import copy
import hashlib
import json
import math
import struct

import numpy as np
from scipy.spatial.transform import Rotation

_COMPONENT_DTYPES: dict[int, np.dtype] = {
    5120: np.dtype("<i1"),
    5121: np.dtype("<u1"),
    5122: np.dtype("<i2"),
    5123: np.dtype("<u2"),
    5125: np.dtype("<u4"),
    5126: np.dtype("<f4"),
}
_TYPE_WIDTH = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _quat_matrix_xyzw(q: Iterable[float]) -> np.ndarray:
    return Rotation.from_quat(np.asarray(q, dtype=np.float64)).as_matrix()


def matrix_from_trs(
    translation: np.ndarray,
    rotation: Rotation,
    scale: np.ndarray,
) -> np.ndarray:
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = rotation.as_matrix() @ np.diag(scale)
    matrix[:3, 3] = translation
    return matrix


@dataclass(frozen=True)
class PrimitiveData:
    positions: np.ndarray
    normals: np.ndarray | None
    texcoords: np.ndarray | None
    indices: np.ndarray
    joints: np.ndarray | None
    weights: np.ndarray | None
    primitive_index: int
    mesh_index: int


class GlbAsset:
    """Parsed GLB with convenience access to nodes, skeleton, and skinned mesh data."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        raw = self.path.read_bytes()
        if len(raw) < 20:
            raise ValueError(f"{self.path} is too small to be a GLB")
        magic, version, total_length = struct.unpack_from("<4sII", raw, 0)
        if magic != b"glTF" or version != 2 or total_length != len(raw):
            raise ValueError("Invalid GLB 2.0 header or declared length")

        cursor = 12
        chunks: list[tuple[int, bytes]] = []
        while cursor < len(raw):
            chunk_length, chunk_type = struct.unpack_from("<II", raw, cursor)
            cursor += 8
            chunks.append((chunk_type, raw[cursor : cursor + chunk_length]))
            cursor += chunk_length
        json_chunks = [data for kind, data in chunks if kind == 0x4E4F534A]
        bin_chunks = [data for kind, data in chunks if kind == 0x004E4942]
        if len(json_chunks) != 1 or len(bin_chunks) != 1:
            raise ValueError("Expected exactly one JSON and one BIN chunk")

        self.json: dict[str, Any] = json.loads(json_chunks[0].decode("utf-8"))
        self.binary = bytes(bin_chunks[0])
        self.nodes: list[dict[str, Any]] = self.json.get("nodes", [])
        self.name_to_node: dict[str, int] = {
            node.get("name", f"node_{index}"): index
            for index, node in enumerate(self.nodes)
        }
        self.parents: list[int | None] = [None] * len(self.nodes)
        for parent_index, node in enumerate(self.nodes):
            for child_index in node.get("children", []):
                if self.parents[child_index] is not None:
                    raise ValueError(f"Node {child_index} has multiple parents")
                self.parents[child_index] = parent_index

        self.rest_translation: list[np.ndarray] = []
        self.rest_rotation: list[Rotation] = []
        self.rest_scale: list[np.ndarray] = []
        self.rest_local: list[np.ndarray] = []
        for node in self.nodes:
            if "matrix" in node:
                matrix = np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4).T
                translation = matrix[:3, 3].copy()
                basis = matrix[:3, :3]
                scale = np.linalg.norm(basis, axis=0)
                if np.any(scale <= 1e-10):
                    raise ValueError("Node matrix contains degenerate scale")
                rotation = Rotation.from_matrix(basis @ np.diag(1.0 / scale))
            else:
                translation = np.asarray(node.get("translation", [0.0, 0.0, 0.0]), dtype=np.float64)
                rotation = Rotation.from_quat(node.get("rotation", [0.0, 0.0, 0.0, 1.0]))
                scale = np.asarray(node.get("scale", [1.0, 1.0, 1.0]), dtype=np.float64)
                matrix = matrix_from_trs(translation, rotation, scale)
            self.rest_translation.append(translation)
            self.rest_rotation.append(rotation)
            self.rest_scale.append(scale)
            self.rest_local.append(matrix)

        self.rest_world = self.world_matrices(self.rest_local)
        self.rest_world_rotation = self.world_rotations(self.rest_rotation)

    def accessor(self, accessor_index: int) -> np.ndarray:
        accessor = self.json["accessors"][accessor_index]
        if "bufferView" not in accessor:
            raise NotImplementedError("Sparse or implicit accessors are not supported")
        view = self.json["bufferViews"][accessor["bufferView"]]
        component_type = accessor["componentType"]
        dtype = _COMPONENT_DTYPES[component_type]
        width = _TYPE_WIDTH[accessor["type"]]
        count = accessor["count"]
        byte_offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", dtype.itemsize * width)
        if stride == dtype.itemsize * width:
            values = np.frombuffer(
                self.binary,
                dtype=dtype,
                count=count * width,
                offset=byte_offset,
            ).reshape(count, width)
        else:
            values = np.ndarray(
                shape=(count, width),
                dtype=dtype,
                buffer=self.binary,
                offset=byte_offset,
                strides=(stride, dtype.itemsize),
            )
        values = np.array(values)
        if accessor["type"].startswith("MAT"):
            side = int(math.sqrt(width))
            # glTF matrices are stored column-major.
            values = values.reshape(count, side, side).transpose(0, 2, 1)
        if accessor.get("normalized"):
            if np.issubdtype(dtype, np.signedinteger):
                max_value = np.iinfo(dtype).max
                values = np.maximum(values.astype(np.float64) / max_value, -1.0)
            elif np.issubdtype(dtype, np.unsignedinteger):
                values = values.astype(np.float64) / np.iinfo(dtype).max
        return values

    def buffer_view_bytes(self, buffer_view_index: int) -> bytes:
        view = self.json["bufferViews"][buffer_view_index]
        start = view.get("byteOffset", 0)
        return self.binary[start : start + view["byteLength"]]

    def world_matrices(self, local_matrices: list[np.ndarray]) -> list[np.ndarray]:
        world: list[np.ndarray | None] = [None] * len(local_matrices)

        def resolve(index: int) -> np.ndarray:
            cached = world[index]
            if cached is not None:
                return cached
            parent = self.parents[index]
            current = local_matrices[index]
            result = current if parent is None else resolve(parent) @ current
            world[index] = result
            return result

        return [resolve(index) for index in range(len(local_matrices))]

    def world_rotations(self, local_rotations: list[Rotation]) -> list[Rotation]:
        world: list[Rotation | None] = [None] * len(local_rotations)

        def resolve(index: int) -> Rotation:
            cached = world[index]
            if cached is not None:
                return cached
            parent = self.parents[index]
            result = local_rotations[index] if parent is None else resolve(parent) * local_rotations[index]
            world[index] = result
            return result

        return [resolve(index) for index in range(len(local_rotations))]

    def primitive(self, mesh_index: int = 0, primitive_index: int = 0) -> PrimitiveData:
        primitive = self.json["meshes"][mesh_index]["primitives"][primitive_index]
        attributes = primitive["attributes"]
        positions = self.accessor(attributes["POSITION"]).astype(np.float64)
        normals = (
            self.accessor(attributes["NORMAL"]).astype(np.float64)
            if "NORMAL" in attributes
            else None
        )
        texcoords = (
            self.accessor(attributes["TEXCOORD_0"]).astype(np.float64)
            if "TEXCOORD_0" in attributes
            else None
        )
        if "indices" in primitive:
            indices = self.accessor(primitive["indices"]).reshape(-1).astype(np.int64)
        else:
            indices = np.arange(len(positions), dtype=np.int64)

        joint_sets: list[np.ndarray] = []
        weight_sets: list[np.ndarray] = []
        set_index = 0
        while f"JOINTS_{set_index}" in attributes and f"WEIGHTS_{set_index}" in attributes:
            joint_sets.append(self.accessor(attributes[f"JOINTS_{set_index}"]).astype(np.int64))
            weight_sets.append(self.accessor(attributes[f"WEIGHTS_{set_index}"]).astype(np.float64))
            set_index += 1
        joints = np.concatenate(joint_sets, axis=1) if joint_sets else None
        weights = np.concatenate(weight_sets, axis=1) if weight_sets else None
        if weights is not None:
            sums = weights.sum(axis=1, keepdims=True)
            weights = np.divide(weights, sums, out=np.zeros_like(weights), where=sums > 1e-12)
        return PrimitiveData(
            positions=positions,
            normals=normals,
            texcoords=texcoords,
            indices=indices,
            joints=joints,
            weights=weights,
            primitive_index=primitive_index,
            mesh_index=mesh_index,
        )

    def skin_index_for_mesh_node(self, mesh_index: int = 0) -> int:
        candidates = [node for node in self.nodes if node.get("mesh") == mesh_index and "skin" in node]
        if len(candidates) != 1:
            raise ValueError(f"Expected one skinned node for mesh {mesh_index}, found {len(candidates)}")
        return int(candidates[0]["skin"])

    def skin_data(self, skin_index: int = 0) -> tuple[list[int], np.ndarray]:
        skin = self.json["skins"][skin_index]
        joints = list(map(int, skin["joints"]))
        inverse_bind = self.accessor(skin["inverseBindMatrices"]).astype(np.float64)
        return joints, inverse_bind

    def skin_points(
        self,
        positions: np.ndarray,
        joints: np.ndarray,
        weights: np.ndarray,
        world_matrices: list[np.ndarray],
        skin_index: int = 0,
    ) -> np.ndarray:
        points, _ = self.skin_mesh(positions, None, joints, weights, world_matrices, skin_index)
        return points

    def skin_mesh(
        self,
        positions: np.ndarray,
        normals: np.ndarray | None,
        joints: np.ndarray,
        weights: np.ndarray,
        world_matrices: list[np.ndarray],
        skin_index: int = 0,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        """Linear-blend-skin points and optional normals in one influence pass."""
        skin_nodes, inverse_bind = self.skin_data(skin_index)
        skin_matrices = np.stack(
            [world_matrices[node_index] @ inverse_bind[joint_index] for joint_index, node_index in enumerate(skin_nodes)]
        )
        homogeneous = np.concatenate([positions, np.ones((len(positions), 1), dtype=np.float64)], axis=1)
        output = np.zeros((len(positions), 4), dtype=np.float64)
        normal_output = None if normals is None else np.zeros((len(normals), 3), dtype=np.float64)
        for influence_index in range(joints.shape[1]):
            influence_weights = weights[:, influence_index]
            mask = influence_weights > 1e-10
            if not np.any(mask):
                continue
            matrices = skin_matrices[joints[mask, influence_index]]
            transformed = np.einsum("nij,nj->ni", matrices, homogeneous[mask])
            output[mask] += transformed * influence_weights[mask, None]
            if normal_output is not None:
                transformed_normals = np.einsum("nij,nj->ni", matrices[:, :3, :3], normals[mask])
                normal_output[mask] += transformed_normals * influence_weights[mask, None]
        if normal_output is not None:
            lengths = np.linalg.norm(normal_output, axis=1, keepdims=True)
            normal_output = np.divide(
                normal_output, lengths, out=np.zeros_like(normal_output), where=lengths > 1e-12
            )
        return output[:, :3], normal_output

    def extract_image(self, image_index: int, destination: str | Path) -> Path:
        image = self.json["images"][image_index]
        if "bufferView" not in image:
            raise NotImplementedError("Only bufferView-backed images are supported")
        path = Path(destination)
        path.write_bytes(self.buffer_view_bytes(image["bufferView"]))
        return path

    def descendants(self, node_name: str) -> list[str]:
        start = self.name_to_node[node_name]
        result: list[str] = []
        stack = list(reversed(self.nodes[start].get("children", [])))
        while stack:
            current = stack.pop()
            result.append(self.nodes[current].get("name", f"node_{current}"))
            stack.extend(reversed(self.nodes[current].get("children", [])))
        return result

    def single_child_chain(self, start_name: str, max_nodes: int = 32) -> list[str]:
        chain = [start_name]
        current = self.name_to_node[start_name]
        while len(chain) < max_nodes:
            children = self.nodes[current].get("children", [])
            if len(children) != 1:
                break
            current = children[0]
            chain.append(self.nodes[current].get("name", f"node_{current}"))
        return chain

    def write_animations(
        self,
        destination: str | Path,
        animations: list[dict[str, Any]],
        replace_existing: bool = True,
    ) -> Path:
        """Append animation arrays and write a new GLB.

        Each animation dictionary must contain:
          name: str
          times: float32 array [samples]
          rotations: mapping node-name -> float32 quaternions [samples,4] xyzw
          translations: optional mapping node-name -> float32 vectors [samples,3]
          extras: optional JSON object
        """
        gltf = copy.deepcopy(self.json)
        binary = bytearray(self.binary)

        def align4() -> None:
            while len(binary) % 4:
                binary.append(0)

        def append_buffer_view(blob: bytes) -> int:
            align4()
            offset = len(binary)
            binary.extend(blob)
            index = len(gltf.setdefault("bufferViews", []))
            gltf["bufferViews"].append(
                {"buffer": 0, "byteOffset": offset, "byteLength": len(blob)}
            )
            return index

        def add_accessor(array: np.ndarray, kind: str, include_minmax: bool = False) -> int:
            values = np.asarray(array, dtype=np.float32)
            if values.ndim == 1:
                values = values[:, None]
            view = append_buffer_view(values.tobytes(order="C"))
            accessor: dict[str, Any] = {
                "bufferView": view,
                "componentType": 5126,
                "count": int(values.shape[0]),
                "type": kind,
            }
            if include_minmax:
                accessor["min"] = values.min(axis=0).astype(float).tolist()
                accessor["max"] = values.max(axis=0).astype(float).tolist()
            index = len(gltf.setdefault("accessors", []))
            gltf["accessors"].append(accessor)
            return index

        encoded: list[dict[str, Any]] = []
        for specification in animations:
            times = np.asarray(specification["times"], dtype=np.float32).reshape(-1)
            if len(times) < 2 or np.any(np.diff(times) <= 0):
                raise ValueError(f"Animation {specification['name']} has invalid time samples")
            time_accessor = add_accessor(times, "SCALAR", include_minmax=True)
            samplers: list[dict[str, Any]] = []
            channels: list[dict[str, Any]] = []

            for path_name, width, kind in (("rotations", 4, "VEC4"), ("translations", 3, "VEC3")):
                for node_name, values in specification.get(path_name, {}).items():
                    if node_name not in self.name_to_node:
                        raise KeyError(f"Animation references unknown node {node_name}")
                    array = np.asarray(values, dtype=np.float32)
                    if array.shape != (len(times), width):
                        raise ValueError(
                            f"{specification['name']}:{node_name}:{path_name} expected {(len(times), width)}, got {array.shape}"
                        )
                    output_accessor = add_accessor(array, kind)
                    sampler_index = len(samplers)
                    samplers.append(
                        {
                            "input": time_accessor,
                            "output": output_accessor,
                            "interpolation": specification.get("interpolation", "LINEAR"),
                        }
                    )
                    channels.append(
                        {
                            "sampler": sampler_index,
                            "target": {
                                "node": self.name_to_node[node_name],
                                "path": "rotation" if path_name == "rotations" else "translation",
                            },
                        }
                    )
            encoded.append(
                {
                    "name": specification["name"],
                    "samplers": samplers,
                    "channels": channels,
                    "extras": specification.get("extras", {}),
                }
            )

        if replace_existing:
            gltf["animations"] = encoded
        else:
            gltf.setdefault("animations", []).extend(encoded)
        align4()
        gltf["buffers"][0]["byteLength"] = len(binary)
        json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        while len(json_bytes) % 4:
            json_bytes += b" "
        total_length = 12 + 8 + len(json_bytes) + 8 + len(binary)
        output = Path(destination)
        with output.open("wb") as fh:
            fh.write(struct.pack("<4sII", b"glTF", 2, total_length))
            fh.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
            fh.write(json_bytes)
            fh.write(struct.pack("<II", len(binary), 0x004E4942))
            fh.write(binary)
        return output


def quaternion_continuity(values: np.ndarray) -> np.ndarray:
    """Flip quaternion signs so adjacent samples stay on one hemisphere."""
    result = np.asarray(values, dtype=np.float64).copy()
    for index in range(1, len(result)):
        if float(np.dot(result[index - 1], result[index])) < 0.0:
            result[index] *= -1.0
    return result
