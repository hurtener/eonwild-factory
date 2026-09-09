"""Reopen compiled motion-set packages and verify declared serialized handoffs.

This tool never compiles or repairs a package.  It consumes immutable package
directories produced by ``factory compile-set``, repeats package verification,
and runs the same native-time handoff verifier used by transition releases.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.compiler import verify_package
from eonwild_motion.factory.handoff import verify_handoff
from eonwild_motion.factory.io import digest, json_bytes, write_json


_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def _name(value: str) -> str:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise ContractError(f"motion package name is invalid: {value!r}")
    return value


def _handoff(value: str) -> tuple[str, str]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ContractError("handoffs must use TRANSITION:STEADY package names")
    return _name(parts[0]), _name(parts[1])


def _git_identity(root: Path) -> dict[str, str]:
    def git(value: str) -> str:
        return subprocess.check_output(
            ["git", "rev-parse", value], cwd=root, text=True
        ).strip()

    return {"head": git("HEAD"), "tree": git("HEAD^{tree}")}


def verify_compiled_motion_set(
    *,
    root: Path,
    packages: Path,
    motions: list[str],
    handoffs: list[tuple[str, str]],
    output: Path,
) -> dict:
    root = root.resolve()
    packages = packages.resolve()
    output = output.resolve()
    motions = [_name(value) for value in motions]
    handoffs = [(_name(transition), _name(steady)) for transition, steady in handoffs]
    if len(set(motions)) != len(motions):
        raise ContractError("motion package names must be unique")
    if len(set(handoffs)) != len(handoffs):
        raise ContractError("handoff pairs must be unique")
    labels = [f"{transition}-to-{steady}" for transition, steady in handoffs]
    if len(set(labels)) != len(labels):
        raise ContractError("handoff pairs produce ambiguous evidence names")
    selected = set(motions)
    if any(
        transition not in selected or steady not in selected
        for transition, steady in handoffs
    ):
        raise ContractError("every handoff package must be present in --motions")
    if not packages.is_dir():
        raise ContractError("compiled package root is missing")
    if output.exists():
        raise ContractError(
            "choose a new output directory; existing evidence is immutable"
        )
    if output == packages or output.is_relative_to(packages):
        raise ContractError("handoff evidence must be outside compiled packages")
    package_paths = {name: packages / name for name in motions}
    if any(not path.is_dir() for path in package_paths.values()):
        raise ContractError("one or more selected package directories are missing")

    output.mkdir(parents=True)
    started = time.perf_counter()
    result = {
        "schema": "eonwild.motion.compiled-motion-set-verification.v1",
        "source": _git_identity(root),
        "motions": motions,
        "packages": {},
        "handoffs": {},
        "visual_review": "PENDING",
        "unity_validation": "NOT_RUN",
        "production_approved": False,
        "status": "BLOCKED",
    }

    def save() -> None:
        result["elapsed_seconds"] = time.perf_counter() - started
        write_json(output / "results.json", result)

    for name, path in package_paths.items():
        try:
            result["packages"][name] = verify_package(path)
        except Exception as exc:
            result["packages"][name] = {
                "integrity": "ERROR",
                "technical_status": "ERROR",
                "error": str(exc),
            }
            (output / f"{name}.package.error.log").write_text(traceback.format_exc())
        save()
        print(
            "MOTION_SET_PACKAGE", name, json.dumps(result["packages"][name]), flush=True
        )

    for (transition, steady), label in zip(handoffs, labels, strict=True):
        try:
            receipt = verify_handoff(
                package_paths[transition], package_paths[steady], root=root
            )
        except Exception as exc:
            receipt = {
                "schema": "eonwild.motion.handoff-validation.v1",
                "status": "ERROR",
                "error": str(exc),
                "visual_review": "PENDING",
                "unity_validation": "NOT_RUN",
                "production_approved": False,
            }
            (output / f"{label}.error.log").write_text(traceback.format_exc())
        receipt_bytes = json_bytes(receipt)
        (output / f"{label}.handoff.json").write_bytes(receipt_bytes)
        result["handoffs"][label] = {
            "status": receipt.get("status", "ERROR"),
            "receipt_sha256": digest(receipt_bytes),
        }
        save()
        print(
            "MOTION_SET_HANDOFF",
            label,
            json.dumps(result["handoffs"][label]),
            flush=True,
        )

    if (
        result["packages"]
        and all(
            item.get("integrity") == "PASS" and item.get("technical_status") == "PASS"
            for item in result["packages"].values()
        )
        and result["handoffs"]
        and all(item.get("status") == "PASS" for item in result["handoffs"].values())
    ):
        result["status"] = "PASS"
    save()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--motions", nargs="+", required=True)
    parser.add_argument("--handoff", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_compiled_motion_set(
            root=args.root,
            packages=args.packages,
            motions=args.motions,
            handoffs=[_handoff(value) for value in args.handoff],
            output=args.output,
        )
    except (ContractError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
