#!/usr/bin/env python3
"""Exercise the V8.2 release's fail-closed contract and package boundaries."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PACKAGE = ROOT / "procedural-animation-toolkit(v8.2)"
GENERATOR = Path("scripts/release_generate.py")
VERIFIER = Path("scripts/verify_release.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blender(package: Path, script: Path, arguments: list[str]) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            "blender",
            "--background",
            "--python-exit-code",
            "1",
            "--python",
            str(package / script),
            "--",
            *arguments,
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )


def rebuild_with_mismatched_timeline(source: Path, target: Path, clip: str) -> None:
    raw = source.read_bytes()
    cursor = 12
    chunks = []
    document = None
    while cursor < len(raw):
        length, kind = struct.unpack_from("<II", raw, cursor)
        cursor += 8
        payload = raw[cursor:cursor + length]
        cursor += length
        if kind == 0x4E4F534A:
            document = json.loads(payload.decode("utf-8"))
        chunks.append((kind, payload))
    if document is None:
        raise RuntimeError("missing GLB JSON")

    animation = next(
        item for item in document["animations"] if item.get("name") == clip
    )
    rotation_channels = [
        channel
        for channel in animation["channels"]
        if channel["target"]["path"] == "rotation"
    ]
    sampler = animation["samplers"][rotation_channels[1]["sampler"]]
    original = document["accessors"][int(sampler["input"])]
    shifted = copy.deepcopy(original)
    shifted["byteOffset"] = int(shifted.get("byteOffset", 0)) + 4
    shifted["count"] = int(shifted["count"]) - 1
    document["accessors"].append(shifted)
    sampler["input"] = len(document["accessors"]) - 1

    rebuilt = []
    for kind, payload in chunks:
        if kind == 0x4E4F534A:
            payload = json.dumps(document, separators=(",", ":")).encode("utf-8")
            payload += b" " * ((-len(payload)) % 4)
        rebuilt.append(struct.pack("<II", len(payload), kind) + payload)
    body = b"".join(rebuilt)
    target.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)


def result(name: str, process: subprocess.CompletedProcess) -> dict:
    combined = (process.stdout + "\n" + process.stderr).strip().splitlines()
    diagnostic = next(
        (
            line.strip()
            for line in reversed(combined)
            if "RuntimeError:" in line or "ValueError:" in line
        ),
        combined[-1] if combined else "",
    )
    return {
        "case": name,
        "expected": "nonzero",
        "exitCode": process.returncode,
        "result": "PASS" if process.returncode != 0 else "FAIL",
        "diagnostic": diagnostic,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix="v8-2-p1-negative-") as directory:
        package = Path(directory) / "package"
        shutil.copytree(SOURCE_PACKAGE, package)
        original_config = json.loads((package / "config/release.json").read_text())

        mutations = [
            (
                "bad expected parent",
                lambda config: config["contract"]["expectedParents"].__setitem__(
                    "pelvis", "chest"
                ),
            ),
            (
                "STEP interpolation",
                lambda config: config["contract"]["accessorContract"].__setitem__(
                    "interpolation", "STEP"
                ),
            ),
            (
                "CUBICSPLINE interpolation",
                lambda config: config["contract"]["accessorContract"].__setitem__(
                    "interpolation", "CUBICSPLINE"
                ),
            ),
            (
                "commonTimeline false",
                lambda config: config["contract"]["accessorContract"].__setitem__(
                    "commonTimeline", False
                ),
            ),
            (
                "bad componentType",
                lambda config: config["contract"]["accessorContract"].__setitem__(
                    "componentType", 5123
                ),
            ),
            (
                "bad type",
                lambda config: config["contract"]["accessorContract"].__setitem__(
                    "type", "VEC3"
                ),
            ),
            (
                "bad byteStride",
                lambda config: config["contract"]["accessorContract"].__setitem__(
                    "byteStride", 12
                ),
            ),
            (
                "zero local-delta bounds",
                lambda config: (
                    config["contract"].__setitem__("maxChestLocalDeltaDegrees", 0),
                    config["contract"].__setitem__("maxNeckLocalDeltaDegrees", 0),
                ),
            ),
        ]
        for index, (name, mutate) in enumerate(mutations):
            config = copy.deepcopy(original_config)
            mutate(config)
            config_path = package / f"config/negative-{index}.json"
            config_path.write_text(json.dumps(config))
            process = blender(
                package,
                GENERATOR,
                ["--config", str(config_path), "--output", str(Path(directory) / "out.glb")],
            )
            rows.append(result(name, process))
            config_path.unlink()

        mismatched = package / "input/mismatched-timeline.glb"
        rebuild_with_mismatched_timeline(
            package / original_config["base"],
            mismatched,
            original_config["walkClips"][0],
        )
        config = copy.deepcopy(original_config)
        config["base"] = str(mismatched.relative_to(package))
        config["baseSha256"] = sha(mismatched)
        config_path = package / "config/negative-timeline.json"
        config_path.write_text(json.dumps(config))
        process = blender(
            package,
            GENERATOR,
            ["--config", str(config_path), "--output", str(Path(directory) / "out.glb")],
        )
        rows.append(result("mismatched common timeline", process))
        config_path.unlink()
        mismatched.unlink()

        cache = package / "scripts/__pycache__"
        cache.mkdir()
        small = cache / "probe.pyc"
        small.write_bytes(b"cache")
        small_output = Path(directory) / "verify-small.json"
        process = blender(
            package,
            VERIFIER,
            ["--output", str(small_output)],
        )
        row = result("small pycache", process)
        small_result = json.loads(small_output.read_text())
        row["diagnostic"] = {
            "forbiddenPaths": small_result["forbiddenPaths"],
            "oversizedFiles": small_result["oversizedFiles"],
        }
        rows.append(row)
        small.unlink()

        large = cache / "oversized.pyc"
        with large.open("wb") as handle:
            handle.truncate(100 * 1024 * 1024 + 1)
        large_output = Path(directory) / "verify-large.json"
        process = blender(
            package,
            VERIFIER,
            ["--output", str(large_output)],
        )
        row = result(">100MB pyc", process)
        large_result = json.loads(large_output.read_text())
        row["diagnostic"] = {
            "forbiddenPaths": large_result["forbiddenPaths"],
            "oversizedFiles": large_result["oversizedFiles"],
        }
        rows.append(row)

    document = {
        "schema": "eonwild.v8_2.p1_negative_tests.v1",
        "status": "PASS" if all(row["result"] == "PASS" for row in rows) else "FAIL",
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    print(json.dumps(document, indent=2))
    raise SystemExit(0 if document["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
