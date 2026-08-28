from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import zlib

from ..errors import ValidationFailure


SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def _paeth(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    diagonal_distance = abs(estimate - upper_left)
    if left_distance <= above_distance and left_distance <= diagonal_distance:
        return left
    return above if above_distance <= diagonal_distance else upper_left


def _decode(path: Path) -> tuple[bytes, bytes, int, int]:
    raw = path.read_bytes()
    if not raw.startswith(SIGNATURE):
        raise ValidationFailure(f"not a PNG: {path}")
    cursor = len(SIGNATURE)
    ihdr = None
    compressed = bytearray()
    while cursor < len(raw):
        if cursor + 12 > len(raw):
            raise ValidationFailure("truncated PNG chunk")
        length = struct.unpack_from(">I", raw, cursor)[0]
        kind = raw[cursor + 4:cursor + 8]
        payload = raw[cursor + 8:cursor + 8 + length]
        if len(payload) != length:
            raise ValidationFailure("truncated PNG payload")
        expected_crc = struct.unpack_from(">I", raw, cursor + 8 + length)[0]
        actual_crc = zlib.crc32(kind)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValidationFailure("PNG CRC mismatch")
        cursor += 12 + length
        if kind == b"IHDR":
            ihdr = payload
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if ihdr is None or len(ihdr) != 13:
        raise ValidationFailure("PNG has no valid IHDR")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", ihdr
    )
    channels = {2: 3, 6: 4}.get(color)
    if depth != 8 or channels is None or compression or filtering or interlace:
        raise ValidationFailure("canonical PNG supports non-interlaced 8-bit RGB/RGBA")
    scanlines = zlib.decompress(bytes(compressed))
    stride = width * channels
    if len(scanlines) != height * (stride + 1):
        raise ValidationFailure("PNG scanline length mismatch")
    pixels = bytearray(height * stride)
    source = 0
    for row in range(height):
        filter_type = scanlines[source]
        source += 1
        prior_offset = (row - 1) * stride
        row_offset = row * stride
        for column in range(stride):
            value = scanlines[source]
            source += 1
            left = pixels[row_offset + column - channels] if column >= channels else 0
            above = pixels[prior_offset + column] if row else 0
            upper_left = (
                pixels[prior_offset + column - channels]
                if row and column >= channels
                else 0
            )
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = value + left
            elif filter_type == 2:
                decoded = value + above
            elif filter_type == 3:
                decoded = value + ((left + above) // 2)
            elif filter_type == 4:
                decoded = value + _paeth(left, above, upper_left)
            else:
                raise ValidationFailure(f"unsupported PNG filter: {filter_type}")
            pixels[row_offset + column] = decoded & 0xFF
    return ihdr, bytes(pixels), width, height


def canonicalize_png(path: Path) -> dict[str, object]:
    ihdr, pixels, width, height = _decode(path)
    channels = 4 if ihdr[9] == 6 else 3
    stride = width * channels
    scanlines = b"".join(
        b"\x00" + pixels[row * stride:(row + 1) * stride]
        for row in range(height)
    )
    canonical = b"".join(
        (
            SIGNATURE,
            _chunk(b"IHDR", ihdr),
            _chunk(b"IDAT", zlib.compress(scanlines, level=9)),
            _chunk(b"IEND", b""),
        )
    )
    path.write_bytes(canonical)
    return {
        "fileSha256": hashlib.sha256(canonical).hexdigest(),
        "pixelContentSha256": hashlib.sha256(pixels).hexdigest(),
        "width": width,
        "height": height,
        "channels": channels,
        "canonicalization": "decoded-scanlines-filter0-zlib9@1",
    }
