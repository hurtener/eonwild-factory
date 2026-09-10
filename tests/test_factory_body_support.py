from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from eonwild_motion.dynamics.body_support_coordinator import BodySupportSolution
from eonwild_motion.factory.body_support import (
    BODY_SUPPORT_POLICY,
    body_support_payloads,
    coordinate_body_support,
)
from eonwild_motion.factory.io import digest, json_bytes
from eonwild_motion.errors import ContractError


class _Adapter:
    frozen_anchor_sha256 = "a" * 64
    body_control_cycle_s = 1.25
    body_height_m = 2.0

    def __init__(self, query, law):
        self.query = query
        self.law = law

    def binding_receipt(self, coefficients):
        return {"final_law_binding_sha256": "b" * 64}

    def law_for_coefficients(self, coefficients):
        return ("accepted-law", tuple(coefficients))


def _plan():
    return {
        "samples": [
            {"time_s": index / 5, "root_forward_m": index / 10}
            for index in range(6)
        ]
    }


def test_factory_orchestrates_bound_proxy_bridge_and_accepted_law(monkeypatch):
    import eonwild_motion.factory.body_support as module

    captured = {}

    def prepare(source, rig, animal, **kwargs):
        captured["proxy"] = (source, rig, animal, kwargs)
        return {"mass_model": {"total_mass_kg": 10.0}}, {"status": "PASS"}

    def bridge(**kwargs):
        captured["bridge"] = kwargs
        return "trial-evaluator"

    solution = BodySupportSolution(
        "AVAILABLE", (0.0,) * 12, 0.0, 0.0, 0.0, 0, 1
    )
    monkeypatch.setattr(module, "prepare_surface_mass_proxy", prepare)
    monkeypatch.setattr(module, "SourceFinalGeometryAdapter", _Adapter)
    monkeypatch.setattr(module, "build_surface_mass_trial_evaluator", bridge)
    monkeypatch.setattr(
        module,
        "solve_body_support_trajectory",
        lambda evaluator, **kwargs: solution,
    )
    result = coordinate_body_support(
        source_bytes=b"source",
        rig_bytes=b"rig",
        animal_bytes=b"animal",
        query=SimpleNamespace(),
        law=SimpleNamespace(),
        plan=_plan(),
        forward_axis=(0.0, 0.0, 1.0),
        up_axis=(0.0, 1.0, 0.0),
    )
    assert captured["proxy"][3] == {
        "source_sha256": digest(b"source"),
        "rig_sha256": digest(b"rig"),
        "animal_sha256": digest(b"animal"),
        "coordinate_system": module.COORDINATES,
    }
    assert captured["bridge"]["body_control_cycle_s"] == 1.25
    assert captured["bridge"]["sample_count"] == 5
    np.testing.assert_allclose(
        captured["bridge"]["cycle_travel_m"], (0.0, 0.0, 0.5)
    )
    assert result.law == ("accepted-law", (0.0,) * 12)
    assert result.receipt["policy_id"] == BODY_SUPPORT_POLICY
    assert result.receipt["source_sampled_dynamics"] == "AVAILABLE"
    assert result.receipt["serialized_dynamics_parity"] == "NOT_RUN"
    assert result.receipt["trial_sampling"] == {
        "duration_s": 1.0,
        "body_control_cycle_s": 1.25,
        "interval_count": 5,
        "cycle_travel_m": [0.0, 0.0, 0.5],
        "sample_semantics": module.SAMPLE_SEMANTICS,
    }
    assert result.receipt["surface_mass_profile_sha256"] == digest(
        json_bytes(result.surface_mass_profile)
    )
    payloads = body_support_payloads(result)
    assert set(payloads) == {
        "surface-mass-profile.json",
        "surface-mass-audit.json",
        "body-support-coordination.json",
    }
    assert json.loads(payloads["body-support-coordination.json"])[
        "accepted_binding"
    ]["final_law_binding_sha256"] == "b" * 64


def test_factory_preserves_unavailable_solution_without_an_accepted_law(monkeypatch):
    import eonwild_motion.factory.body_support as module

    unavailable = BodySupportSolution(
        "UNAVAILABLE", (0.0,) * 12, float("inf"), float("inf"),
        float("inf"), 0, 1, "no feasible contact wrench"
    )
    monkeypatch.setattr(
        module,
        "prepare_surface_mass_proxy",
        lambda *args, **kwargs: (
            {"mass_model": {"total_mass_kg": 10.0}}, {"status": "PASS"}
        ),
    )
    monkeypatch.setattr(module, "SourceFinalGeometryAdapter", _Adapter)
    monkeypatch.setattr(
        module, "build_surface_mass_trial_evaluator", lambda **kwargs: object()
    )
    monkeypatch.setattr(
        module, "solve_body_support_trajectory", lambda *args, **kwargs: unavailable
    )
    result = coordinate_body_support(
        source_bytes=b"source", rig_bytes=b"rig", animal_bytes=b"animal",
        query=SimpleNamespace(), law=SimpleNamespace(), plan=_plan(),
        forward_axis=(0.0, 0.0, 1.0),
        up_axis=(0.0, 1.0, 0.0),
    )
    assert result.law is None
    assert result.receipt["status"] == "UNAVAILABLE"
    assert result.receipt["solution"]["reason"] == "no feasible contact wrench"
    assert result.receipt["solution"]["objective"] is None
    assert "accepted_binding" not in result.receipt
    json_bytes(result.receipt)


def test_factory_rejects_noncanonical_dynamics_frame_before_proxy_work(monkeypatch):
    import eonwild_motion.factory.body_support as module

    monkeypatch.setattr(
        module,
        "prepare_surface_mass_proxy",
        lambda *args, **kwargs: pytest.fail("invalid frame reached proxy preparation"),
    )
    with pytest.raises(ContractError, match=r"canonical \+Y up and \+Z forward"):
        coordinate_body_support(
            source_bytes=b"source", rig_bytes=b"rig", animal_bytes=b"animal",
            query=SimpleNamespace(), law=SimpleNamespace(), plan=_plan(),
            forward_axis=(1.0, 0.0, 0.0), up_axis=(0.0, 1.0, 0.0),
        )


def test_compiler_routes_only_explicit_policy_and_fails_closed(monkeypatch, tmp_path):
    import eonwild_motion.factory.compiler as compiler

    calls = []
    available = SimpleNamespace(
        law="accepted-law",
        solution=SimpleNamespace(status="AVAILABLE", reason=None),
    )

    def coordinate(**kwargs):
        calls.append(kwargs)
        return available

    monkeypatch.setattr(compiler, "coordinate_body_support", coordinate)
    common = {
        "snapshots": {"source": b"source", "rig": b"rig", "animal": b"animal"},
        "query": "query",
        "law": "neutral-law",
        "plan": _plan(),
        "forward_axis": (0.0, 0.0, 1.0),
        "up_axis": (0.0, 1.0, 0.0),
    }
    assert (
        compiler._coordinate_selected_body_support(
            resolution=SimpleNamespace(solve_policy={}), **common
        )
        is None
    )
    assert calls == []

    selected = SimpleNamespace(
        solve_policy={"body_support_coordinator": BODY_SUPPORT_POLICY}
    )
    assert compiler._coordinate_selected_body_support(
        resolution=selected, **common
    ) is available
    assert calls == [
        {
            "source_bytes": b"source",
            "rig_bytes": b"rig",
            "animal_bytes": b"animal",
            "query": "query",
            "law": "neutral-law",
            "plan": common["plan"],
            "forward_axis": common["forward_axis"],
            "up_axis": common["up_axis"],
        }
    ]

    unavailable = SimpleNamespace(
        law=None,
        solution=SimpleNamespace(status="UNAVAILABLE", reason="wrench infeasible"),
    )
    monkeypatch.setattr(compiler, "coordinate_body_support", lambda **kwargs: unavailable)
    diagnostics = []
    monkeypatch.setattr(
        compiler,
        "_write_body_support_unavailable_checkpoint",
        lambda path, **kwargs: diagnostics.append((path, kwargs)),
    )
    unavailable_path = tmp_path / "unavailable"
    with pytest.raises(ContractError, match="wrench infeasible"):
        compiler._coordinate_selected_body_support(
            resolution=selected,
            unavailable_checkpoint=unavailable_path,
            recipe_bytes=b"recipe",
            engine_identity={"compiler.py": "c" * 64},
            **common,
        )
    assert diagnostics[0][0] == unavailable_path
    assert diagnostics[0][1]["compilation"] is unavailable


def test_unavailable_checkpoint_preserves_bound_diagnostics(tmp_path):
    import eonwild_motion.factory.compiler as compiler

    checkpoint = tmp_path / "checkpoint"
    compilation = SimpleNamespace(
        surface_mass_profile={"profile": "bound"},
        surface_mass_audit={"audit": "PASS"},
        receipt={"status": "UNAVAILABLE", "solution": {"objective": None}},
        solution=SimpleNamespace(reason="wrench infeasible"),
    )
    compiler._write_body_support_unavailable_checkpoint(
        checkpoint,
        compilation=compilation,
        recipe_bytes=b"recipe",
        snapshots={"source": b"source", "rig": b"rig", "animal": b"animal"},
        engine_identity={"compiler.py": "c" * 64},
    )
    manifest = json.loads((checkpoint / "manifest.json").read_text())
    assert manifest["status"] == "UNAVAILABLE"
    assert manifest["technical_status"] == "BLOCKED"
    assert manifest["reason"] == "wrench infeasible"
    assert set(manifest["files"]) == {
        "surface-mass-profile.json",
        "surface-mass-audit.json",
        "body-support-coordination.json",
    }
    assert json.loads(
        (checkpoint / "body-support-coordination.json").read_text()
    )["solution"]["objective"] is None


def test_coarse_proposal_cannot_approve_failing_source_resolution(monkeypatch):
    import eonwild_motion.factory.body_support as module
    monkeypatch.setattr(module, "prepare_surface_mass_proxy", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(module, "SourceFinalGeometryAdapter", _Adapter)
    counts = []
    def bridge(**kwargs):
        counts.append(kwargs['sample_count'])
        return lambda coefficients: object()
    monkeypatch.setattr(module, "build_surface_mass_trial_evaluator", bridge)
    monkeypatch.setattr(module, "solve_body_support_trajectory", lambda *a, **k:
        BodySupportSolution('AVAILABLE', (.001,) + (0.,) * 11, 0., 0., 0., 1, 14))
    monkeypatch.setattr(module, "_trial_residuals", lambda *a, **k: (np.array([.01]), .01, .02))
    plan = {'samples': [{'time_s': i/120, 'root_forward_m': i/240} for i in range(121)]}
    result = coordinate_body_support(source_bytes=b's', rig_bytes=b'r', animal_bytes=b'a',
        query=object(), law=object(), plan=plan, forward_axis=(0.,0.,1.), up_axis=(0.,1.,0.))
    assert counts == [12, 120]
    assert result.solution.status == 'UNAVAILABLE'
    assert result.law is None
    assert result.receipt['proposal_sampling']['solution']['status'] == 'AVAILABLE'
    assert result.solution.maximum_normalized_moment_residual == .02
