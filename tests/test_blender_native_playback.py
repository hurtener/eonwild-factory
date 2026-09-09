from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

import pytest

from eonwild_motion.blender.native_playback import (
    ExactCubicPlayback,
    reject_stock_cubic_playback,
    requires_exact_cubic_playback,
)
from eonwild_motion.errors import ContractError


def _glb(path: Path, interpolation: str) -> bytes:
    times = struct.pack("<2f", 0.0, 1.0)
    if interpolation == "LINEAR":
        rows = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    else:
        rows = (
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        )
    values = b"".join(struct.pack("<3f", *row) for row in rows)
    binary = times + values
    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(times)},
            {"buffer": 0, "byteOffset": len(times), "byteLength": len(values)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 2, "type": "SCALAR"},
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": len(rows),
                "type": "VEC3",
            },
        ],
        "nodes": [{"name": "animated"}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "animations": [
            {
                "name": "clip",
                "samplers": [
                    {"input": 0, "output": 1, "interpolation": interpolation}
                ],
                "channels": [
                    {"sampler": 0, "target": {"node": 0, "path": "translation"}}
                ],
            }
        ],
    }
    encoded = json.dumps(document, separators=(",", ":")).encode()
    encoded += b" " * ((4 - len(encoded) % 4) % 4)
    binary += b"\0" * ((4 - len(binary) % 4) % 4)
    raw = (
        struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(encoded) + 8 + len(binary))
        + struct.pack("<II", len(encoded), 0x4E4F534A)
        + encoded
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )
    path.write_bytes(raw)
    return raw


def test_cubic_detection_and_stock_rejection_are_read_only(tmp_path: Path) -> None:
    path = tmp_path / "cubic.glb"
    original = _glb(path, "CUBICSPLINE")
    assert requires_exact_cubic_playback(path) is True
    with pytest.raises(ContractError, match="approximate CUBICSPLINE import"):
        reject_stock_cubic_playback(path, consumer="test renderer")
    assert path.read_bytes() == original


def test_linear_detection_preserves_the_existing_stock_path(tmp_path: Path) -> None:
    path = tmp_path / "linear.glb"
    original = _glb(path, "LINEAR")
    assert requires_exact_cubic_playback(path) is False
    reject_stock_cubic_playback(path, consumer="test renderer")
    assert path.read_bytes() == original


def test_approved_multiclip_linear_capsule_preserves_stock_path() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "legacy/capsules/v8.2/asset/tarbosaurus_v8_2_approved.glb"
    )
    original_sha = "a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_sha
    assert requires_exact_cubic_playback(path) is False
    reject_stock_cubic_playback(path, consumer="legacy review renderer")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_sha


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), -0.1, 1.1])
def test_exact_playback_rejects_malformed_or_out_of_range_time(value: float) -> None:
    playback = ExactCubicPlayback(
        source=Path("unused.glb"),
        glb=None,  # type: ignore[arg-type]
        tracks={},
        timeline=(0.0, 1.0),
        importer=None,
        vnode_type=None,
    )
    with pytest.raises(ContractError, match="native playback time"):
        playback.apply(value)
