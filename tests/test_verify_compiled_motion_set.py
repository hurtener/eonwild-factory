"""Focused tests for serialized shared motion-set handoff verification."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_compiled_motion_set", ROOT / "tools/verify_compiled_motion_set.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _packages(tmp_path: Path) -> Path:
    packages = tmp_path / "packages"
    for name in ("walk", "fast-walk", "walk-start", "walk-stop"):
        (packages / name).mkdir(parents=True)
    return packages


def _args(packages: Path, output: Path) -> list[str]:
    return [
        "--root",
        str(ROOT),
        "--packages",
        str(packages),
        "--motions",
        "walk",
        "fast-walk",
        "walk-start",
        "walk-stop",
        "--handoff",
        "walk-start:walk",
        "--handoff",
        "walk-stop:walk",
        "--output",
        str(output),
    ]


def test_reopens_every_package_and_runs_both_actual_handoffs(tmp_path, monkeypatch):
    packages = _packages(tmp_path)
    output = tmp_path / "evidence"
    package_calls = []
    handoff_calls = []

    def verify_package(path):
        package_calls.append(path)
        return {
            "integrity": "PASS",
            "technical_status": "PASS",
            "visual_review": "PENDING",
            "unity_parity": "NOT_RUN",
            "production_approved": False,
        }

    def verify_handoff(transition, steady, *, root):
        handoff_calls.append((transition, steady, root))
        return {
            "schema": "eonwild.motion.handoff-validation.v1",
            "status": "PASS",
            "modes": {
                "root_motion": {"status": "PASS"},
                "in_place": {"status": "PASS"},
            },
            "visual_review": "PENDING",
            "unity_validation": "NOT_RUN",
            "production_approved": False,
        }

    monkeypatch.setattr(MODULE, "verify_package", verify_package)
    monkeypatch.setattr(MODULE, "verify_handoff", verify_handoff)
    monkeypatch.setattr(
        MODULE, "_git_identity", lambda root: {"head": "a" * 40, "tree": "b" * 40}
    )

    assert MODULE.main(_args(packages, output)) == 0
    assert package_calls == [
        packages / name for name in ("walk", "fast-walk", "walk-start", "walk-stop")
    ]
    assert [(a.name, b.name) for a, b, _ in handoff_calls] == [
        ("walk-start", "walk"),
        ("walk-stop", "walk"),
    ]
    result = json.loads((output / "results.json").read_text())
    assert result["status"] == "PASS"
    assert set(result["handoffs"]) == {"walk-start-to-walk", "walk-stop-to-walk"}
    for label, summary in result["handoffs"].items():
        receipt = output / f"{label}.handoff.json"
        assert MODULE.digest(receipt.read_bytes()) == summary["receipt_sha256"]


def test_blocked_package_or_handoff_keeps_combined_result_blocked(
    tmp_path, monkeypatch
):
    packages = _packages(tmp_path)
    output = tmp_path / "evidence"

    def verify_package(path):
        return {
            "integrity": "PASS",
            "technical_status": "BLOCKED" if path.name == "fast-walk" else "PASS",
        }

    def verify_handoff(transition, steady, *, root):
        return {"status": "BLOCKED" if transition.name == "walk-stop" else "PASS"}

    monkeypatch.setattr(MODULE, "verify_package", verify_package)
    monkeypatch.setattr(MODULE, "verify_handoff", verify_handoff)
    monkeypatch.setattr(
        MODULE, "_git_identity", lambda root: {"head": "a" * 40, "tree": "b" * 40}
    )

    assert MODULE.main(_args(packages, output)) == 2
    result = json.loads((output / "results.json").read_text())
    assert result["status"] == "BLOCKED"
    assert result["packages"]["fast-walk"]["technical_status"] == "BLOCKED"
    assert result["handoffs"]["walk-stop-to-walk"]["status"] == "BLOCKED"


def test_errors_are_retained_and_existing_evidence_is_immutable(tmp_path, monkeypatch):
    packages = _packages(tmp_path)
    output = tmp_path / "evidence"

    def verify_package(path):
        if path.name == "walk-start":
            raise ValueError("corrupt package")
        return {"integrity": "PASS", "technical_status": "PASS"}

    monkeypatch.setattr(MODULE, "verify_package", verify_package)
    monkeypatch.setattr(
        MODULE, "verify_handoff", lambda *args, **kwargs: {"status": "PASS"}
    )
    monkeypatch.setattr(
        MODULE, "_git_identity", lambda root: {"head": "a" * 40, "tree": "b" * 40}
    )

    assert MODULE.main(_args(packages, output)) == 2
    assert "corrupt package" in (output / "walk-start.package.error.log").read_text()
    preserved = (output / "results.json").read_bytes()
    assert MODULE.main(_args(packages, output)) == 1
    assert (output / "results.json").read_bytes() == preserved


def test_rejects_unselected_or_escaping_handoff_names_before_output(tmp_path):
    packages = _packages(tmp_path)
    output = tmp_path / "evidence"
    args = _args(packages, output)
    args[args.index("walk-stop:walk")] = "../walk-stop:walk"
    assert MODULE.main(args) == 1
    assert not output.exists()


def test_rejects_handoff_pairs_with_colliding_evidence_names(tmp_path):
    packages = tmp_path / "packages"
    motions = ("a-to-b", "c", "a", "b-to-c")
    for name in motions:
        (packages / name).mkdir(parents=True)
    output = tmp_path / "evidence"
    assert (
        MODULE.main(
            [
                "--root",
                str(ROOT),
                "--packages",
                str(packages),
                "--motions",
                *motions,
                "--handoff",
                "a-to-b:c",
                "--handoff",
                "a:b-to-c",
                "--output",
                str(output),
            ]
        )
        == 1
    )
    assert not output.exists()


def test_hosted_workflow_compiles_current_set_and_checks_serialized_joins():
    workflow = (ROOT / ".github/workflows/shared-motion-set.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "timeout-minutes: 180" in workflow
    current_set = "catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v2.json"
    assert workflow.count(current_set) == 2
    assert "tarbosaurus-pin-552-1-adult-grounded.v1.json" not in workflow
    assert "--motions walk fast-walk walk-start walk-stop" in workflow
    assert "--interpolation CUBICSPLINE" in workflow
    assert "tools/verify_compiled_motion_set.py" in workflow
    assert workflow.count("--handoff walk-start:walk") == 1
    assert workflow.count("--handoff walk-stop:walk") == 1
    assert "shared-locomotion-set-packages-and-handoffs" in workflow
    assert "path: out/shared-locomotion-set-ci" in workflow
    assert "set +e" in workflow
    assert "status=${PIPESTATUS[0]}" in workflow
    assert "compile-set.exit-code.txt" in workflow
