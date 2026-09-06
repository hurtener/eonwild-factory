#!/usr/bin/env python3
"""Fail-closed snapshot verifier for the lean V8.2 release."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

PKG = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("glb_math", PKG / "scripts/glb_math.py")
g = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(g)

MAX_FILE_BYTES = 100 * 1024 * 1024
REJECTED_COMPONENTS = {
    "__pycache__",
    ".cache",
    ".pytest_cache",
    "cache",
    "caches",
    "tmp",
    "temp",
    "temporary",
    "rejected",
    "rejects",
}
REJECTED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".temp", ".bak", ".rej"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejected_path(relative):
    parts = [part.lower() for part in relative.parts]
    return (
        any(part in REJECTED_COMPONENTS for part in parts)
        or relative.suffix.lower() in REJECTED_SUFFIXES
        or any(
            part.startswith(("rejected-", "rejected_", "temp-", "temp_"))
            for part in parts
        )
    )


def media_facts_match(path, expected):
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=width,height,nb_frames",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    stream = probe["streams"][0]
    return (
        int(stream["width"]) == expected["width"]
        and int(stream["height"]) == expected["height"]
        and int(stream["nb_frames"]) == expected["frames"]
        and abs(float(probe["format"]["duration"]) - expected["duration"]) < 1e-6
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default=PKG / "config/release.json", type=Path
    )
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    )

    config = json.loads(args.config.read_text())
    manifest = json.loads((PKG / "RELEASE_MANIFEST.json").read_text())
    inventory = manifest.get("inventory", {})
    actual_paths = [
        path
        for path in PKG.rglob("*")
        if path.is_file() and path.name != "RELEASE_MANIFEST.json"
    ]
    actual = {str(path.relative_to(PKG)) for path in actual_paths}
    manifest_inventory_exact = (
        set(inventory) == actual and bool(manifest.get("selfHashConvention"))
    )
    forbidden = sorted(
        str(path.relative_to(PKG))
        for path in actual_paths
        if rejected_path(path.relative_to(PKG))
    )
    oversized = sorted(
        {
            str(path.relative_to(PKG))
            for path in actual_paths
            if path.stat().st_size > MAX_FILE_BYTES
        }
    )
    hashes_and_sizes = all(
        (PKG / relative).is_file()
        and sha(PKG / relative) == facts["sha256"]
        and (PKG / relative).stat().st_size <= MAX_FILE_BYTES
        for relative, facts in inventory.items()
    )
    media_ok = all(
        "media" not in facts
        or media_facts_match(PKG / relative, facts["media"])
        for relative, facts in inventory.items()
    )

    base = PKG / config["base"]
    candidate = args.candidate or (PKG / config["output"])
    base_glb = g.Glb(base)
    candidate_glb = g.Glb(candidate)
    allowed = set(config["contract"]["allowedOutputRotationNodes"])
    changed = []
    accessor_scope_ok = True
    json_equal = base_glb.json == candidate_glb.json
    for clip in config["walkClips"]:
        base_accessors = base_glb.rotation_accessors(clip)
        candidate_accessors = candidate_glb.rotation_accessors(clip)
        if set(base_accessors) != set(candidate_accessors):
            accessor_scope_ok = False
            continue
        for name, base_accessor in base_accessors.items():
            candidate_accessor = candidate_accessors[name]
            base_offset, base_count = base_glb.accessor_offset(base_accessor)
            candidate_offset, candidate_count = candidate_glb.accessor_offset(
                candidate_accessor
            )
            same = (
                base_count == candidate_count
                and base_glb.binary[
                    base_offset:base_offset + base_count * 16
                ]
                == candidate_glb.binary[
                    candidate_offset:candidate_offset + candidate_count * 16
                ]
            )
            if not same:
                changed.append(f"{clip}/{name}")
                accessor_scope_ok = accessor_scope_ok and name in allowed

    checks = {
        "manifestInventoryExact": manifest_inventory_exact,
        "inventoryHashesAndSizes": hashes_and_sizes,
        "noForbiddenPaths": not forbidden,
        "noOversizedFiles": not oversized,
        "mediaFacts": media_ok,
        "baseHash": sha(base) == config["baseSha256"],
        "candidateHash": sha(candidate) == config["outputSha256"],
        "jsonByteEquivalent": json_equal,
        "onlyAllowedWalkRotationAccessors": accessor_scope_ok,
        "nonemptyApprovedChangeSet": bool(changed),
    }
    result = {
        "schema": "eonwild.v8_2.release_verify.v3",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "baseSha256": sha(base),
        "candidateSha256": sha(candidate),
        "changedRotationAccessors": changed,
        "allowedNodes": sorted(allowed),
        "forbiddenPaths": forbidden,
        "oversizedFiles": oversized,
        "checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
