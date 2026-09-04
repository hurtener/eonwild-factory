"""Render deterministic visual evidence for the V9 dynamics slice.

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-DYNAMICS-SLICE-001/render_slice_evidence.py

Writes SVG figures plus a ``summary.json`` with the numeric facts each
figure visualizes. Deterministic: fixed palette/geometry/formatting, no
timestamps, no randomness. Re-running must reproduce byte-identical SVGs
(the summary carries the code hash for audit).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from eonwild_motion.contracts.v9_models import BodyInstanceProfile
from eonwild_motion.dynamics.ballistic import BallisticRequest, plan_ballistic_com
from eonwild_motion.dynamics.capacity import CapacityProfile
from eonwild_motion.dynamics.evidence import (
    figure_ballistic_vs_kinematic,
    figure_budgets_and_growth,
    figure_contact_authority,
)
from eonwild_motion.planning.power_attack import PowerAttackRequest, plan_power_attack

OUTPUT = Path(__file__).resolve().parent


def _body() -> BodyInstanceProfile:
    segments = [
        {"id": "pelvis", "parent_id": None, "role": "pelvis", "mass_fraction": 0.5,
         "com_body_m": [0.0, 1.0, 0.0], "inertia_diagonal_normalized": [0.004, 0.006, 0.004]},
        {"id": "trunk", "parent_id": "pelvis", "role": "trunk", "mass_fraction": 0.5,
         "com_body_m": [0.0, 1.6, 0.0], "inertia_diagonal_normalized": [0.006, 0.009, 0.006]},
    ]
    return BodyInstanceProfile.from_document(
        {
            "profile_id": "slice_fixture",
            "family": "heavy_predatory_biped",
            "taxon": "synthetic fixture",
            "coordinate_system": {"units": "m", "time_units": "s", "mass_units": "kg",
                                  "handedness": "right", "up_axis": "Y", "forward_axis": "-Z"},
            "dimensions": {"body_length_m": 7.0, "hip_height_m": 2.15, "body_width_m": 0.95},
            "segment_com_frame": "body",
            "mass": {"mode": "absolute", "total_mass_kg": 1500.0, "mass_fraction_sum": 1.0,
                     "absolute_dynamics_enabled": True, "absolute_policy": "fixture_absolute_allowed"},
            "provenance": {"source": "slice_evidence", "status": "fixture", "kind": "synthetic_fixture",
                           "scientific_claims": False},
            "segments": segments,
        }
    )


def main() -> None:
    figures = {}
    facts: dict = {}
    for name, builder in (
        ("01-ballistic-vs-kinematic", figure_ballistic_vs_kinematic),
        ("02-contact-authority", figure_contact_authority),
        ("03-budgets-and-growth", figure_budgets_and_growth),
    ):
        svg, figure_facts = builder()
        (OUTPUT / f"{name}.svg").write_text(svg + "\n", encoding="utf-8")
        figures[name] = f"{name}.svg"
        facts[name] = figure_facts

    # Power-attack slice receipts: one feasible, one forced to fallback.
    capacity = CapacityProfile(profile_id="slice_fixture_v1")
    feasible = plan_power_attack(
        PowerAttackRequest(body=_body(), capacity=capacity,
                           launch_com_m=(0.0, 2.0, 0.0), launch_velocity_mps=(4.5, 2.5, 0.0),
                           preload_velocity_mps=(4.5, 0.0, 0.0), landing_com_m=(2.4, 1.7, 0.0))
    )
    brutal = plan_power_attack(
        PowerAttackRequest(body=_body(), capacity=capacity,
                           launch_com_m=(0.0, 2.0, 0.0), launch_velocity_mps=(14.0, 9.0, 0.0),
                           landing_com_m=(9.0, 1.7, 0.0))
    )
    facts["power_attack"] = {
        "feasible_variant": feasible["variant"],
        "feasible_physics_evaluated": feasible["physics_evaluated"],
        "feasible_plan_sha256": feasible["plan_sha256"],
        "brutal_variant": brutal["variant"],
        "brutal_limiting_factor": brutal["limiting_factor"],
        "brutal_plan_sha256": brutal["plan_sha256"],
    }
    try:
        head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=OUTPUT.parents[1], text=True).strip()
    except Exception:
        head = "unknown"
    summary = {"engine_head": head, "figures": figures, "facts": facts}
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    for path in sorted(OUTPUT.glob("*.svg")) + [OUTPUT / "summary.json"]:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        print(f"{path.name}  sha256:{digest}")


if __name__ == "__main__":
    main()
