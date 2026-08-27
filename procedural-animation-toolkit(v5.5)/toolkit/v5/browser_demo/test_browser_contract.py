#!/usr/bin/env python3
"""Data-contract smoke test for the dependency-free V4 WebGL2 viewer."""
from __future__ import annotations
from pathlib import Path
import base64
import hashlib
import json
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parent
GLB = ROOT / "tarbosaurus_procedural_v4_animation_pack.glb"
MANIFEST = ROOT / "animation-manifest.v4.json"
HTML = ROOT / "index.html"
JS = ROOT / "v4-viewer.js"
SELF = ROOT.parents[2] / "validated_result" / "v4" / "showcase" / "OPEN_ME_tarbosaurus_v4_3d_browser.html"

def parse_glb(path: Path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF" and version == 2 and length == len(raw)
    cursor = 12
    chunks = {}
    while cursor < len(raw):
        size, kind = struct.unpack_from("<II", raw, cursor); cursor += 8
        chunks[kind] = raw[cursor:cursor+size]; cursor += size
    return json.loads(chunks[0x4E4F534A].decode("utf-8")), chunks[0x004E4942]

def main() -> int:
    subprocess.run(["node", "--check", str(JS)], check=True)
    manifest = json.loads(MANIFEST.read_text())
    names = {clip["name"] for clip in manifest["clips"]}
    gltf, binary = parse_glb(GLB)
    assert len(gltf.get("animations", [])) == 37
    assert {a.get("name") for a in gltf["animations"]} == names
    assert len(gltf["skins"][0]["joints"]) == 75
    attrs = gltf["meshes"][0]["primitives"][0]["attributes"]
    for index in range(3):
        assert f"JOINTS_{index}" in attrs and f"WEIGHTS_{index}" in attrs
    html = HTML.read_text()
    js = JS.read_text()
    ui_names = set(re.findall(r'data-clip="([^"]+)"', html))
    sequence_names = set(re.findall(r'"(PROC_[A-Z0-9_]+_V4(?:_INPLACE|_ROOTMOTION)?)"', js))
    missing_ui = sorted(ui_names - names)
    missing_sequence = sorted(sequence_names - names)
    assert not missing_ui, missing_ui
    assert not missing_sequence, missing_sequence
    assert "bone(aJoints0.x)*aWeights0.x" in js
    assert "bone(aJoints2.w)*aWeights2.w" in js
    assert "RGBA32F" in js and "texelFetch" in js
    assert "remaining=this.queue.slice()" in js
    assert SELF.exists() and SELF.stat().st_size > GLB.stat().st_size
    self_html = SELF.read_text(encoding="utf-8")
    assert "http://" not in self_html and "https://" not in self_html
    marker = "window.V4_EMBEDDED_GLB_BASE64="
    start = self_html.index(marker) + len(marker)
    assert self_html[start] == '"'
    end = self_html.index('";window.V4_EMBEDDED_MANIFEST=', start + 1)
    embedded = json.loads(self_html[start:end+1])
    decoded_hash = hashlib.sha256(base64.b64decode(embedded)).hexdigest()
    source_hash = hashlib.sha256(GLB.read_bytes()).hexdigest()
    assert decoded_hash == source_hash
    result = {
        "status": "PASS",
        "glb_bytes": GLB.stat().st_size,
        "binary_chunk_bytes": len(binary),
        "animation_count": len(names),
        "skin_joint_count": 75,
        "joint_weight_sets": 3,
        "gpu_skin_influences": 12,
        "ui_clip_buttons": len(ui_names),
        "sequence_clip_references": len(sequence_names),
        "self_contained_html_bytes": SELF.stat().st_size,
        "embedded_glb_sha256": source_hash,
        "external_urls_in_self_contained_html": False,
        "node_syntax_check": True,
        "note": "GPU presentation requires a WebGL2-capable end-user browser; visual tracks are independently rendered and validated offline.",
    }
    out = ROOT.parents[2] / "validated_result" / "v4" / "v4-browser-contract-validation.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
