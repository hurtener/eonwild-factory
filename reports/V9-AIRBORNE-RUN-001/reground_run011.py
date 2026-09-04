#!/usr/bin/env python3
"""Regrounding driver: iterate per-side stance offsets to true ground contact.

Run from the repository root (one solve + one 120 Hz skin evaluation per
round, several minutes each):

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-AIRBORNE-RUN-001/reground_run011.py \\
        --rounds 3 --output build/V9-AIRBORNE-RUN-001/iteration-011-regrounded

Each round: solve with current offsets -> skin-evaluate with the strict
1 mm contact authority -> measure per-side median/min loaded sole gap ->
adjust offsets toward a 0.5 mm target clearance. Stops early when both
feet sit inside [-0.5 mm, +2.0 mm] with no penetration, no skate and no
unknown-contact failures. Pelvis/root motion is never touched: only
distal leg targets move (bounded to 5 cm by the gait contract).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from eonwild_motion.dynamics.contact_authority import AuthorityThresholds
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import (
    evaluate_airborne_skin_with_authority,
    solve_airborne_gait,
)

SOURCE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb"
)
SOURCE_CLIP = "PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"
BINDING = ROOT / "profiles/v9/rig.airborne-jaw-breathing.json"
BASE_PROFILE = (
    ROOT / "build/V9-AIRBORNE-RUN-001/iteration-010-breathing/candidate/engineering-profile.json"
)
CONTACT_PROFILE = (
    ROOT / "build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority"
    / "sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json"
)

TARGET_CLEARANCE_M = 0.0005
MIN_OK_M = -0.0005
MAX_OK_M = 0.0020
STRICT = AuthorityThresholds()  # 1 mm ground tolerance, 0.35 m/s skate


def measure(authority: dict, side: str) -> dict:
    foot = authority["per_foot"][side]
    gaps: list[float] = []
    for phase in foot.get("phases", []):
        if phase.get("minimum_gap_m") is not None and phase.get("verdict") != "FAIL":
            gaps.append(float(phase["minimum_gap_m"]))
    return {"verdict": foot["verdict"], "min_gap_m": min(gaps) if gaps else None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start-left", type=float, default=0.007)
    parser.add_argument("--start-right", type=float, default=0.013)
    parser.add_argument("--push-off-pitch", type=float, default=None)
    parser.add_argument("--recovery-pitch", type=float, default=None)
    parser.add_argument("--damping", type=float, default=0.7)
    args = parser.parse_args()

    binding = json.loads(BINDING.read_text())["roles"]
    base = json.loads(BASE_PROFILE.read_text())
    contact_profile = json.loads(CONTACT_PROFILE.read_text())
    source = Glb.from_bytes(SOURCE.read_bytes())

    offsets = {"left": args.start_left, "right": args.start_right}
    log: list[dict] = []
    last: dict = {}
    for round_index in range(args.rounds):
        overrides = {
            "stance_ground_offset_left_m": offsets["left"],
            "stance_ground_offset_right_m": offsets["right"],
        }
        if args.push_off_pitch is not None:
            overrides["push_off_pitch_degrees"] = args.push_off_pitch
        if args.recovery_pitch is not None:
            overrides["foot_recovery_pitch_degrees"] = args.recovery_pitch
        gait = replace(load_airborne_gait(base), **overrides)
        print(f"[round {round_index}] offsets L={offsets['left']:.4f} R={offsets['right']:.4f}", flush=True)
        authority_glb, inplace, plan, receipt = solve_airborne_gait(
            source, source_clip=SOURCE_CLIP, semantic_roles=binding, gait=gait
        )
        skin = evaluate_airborne_skin_with_authority(
            Glb.from_bytes(authority_glb),
            contact_profile=contact_profile,
            gait=gait,
            body_height_m=receipt["body_height_m"],
            authority_thresholds=STRICT,
        )
        verdict = skin["contact_authority_v1"]
        entry: dict = {"round": round_index, "offsets": dict(offsets), "sides": {}}
        done = True
        for side in ("left", "right"):
            gaps = []
            for frame in skin["frames"]:
                row = frame["feet"][side]
                if row["planned_contact"]:
                    gaps.append(min(row["sole_minimum_gap_m"], row["toe_minimum_gap_m"]))
            median_gap = statistics.median(gaps)
            min_gap = min(gaps)
            entry["sides"][side] = {
                "median_gap_m": median_gap,
                "min_gap_m": min_gap,
                "authority": verdict["per_foot"][side]["verdict"],
            }
            print(
                f"  {side}: median_gap={median_gap * 1000:.2f}mm "
                f"min_gap={min_gap * 1000:.2f}mm authority={verdict['per_foot'][side]['verdict']}",
                flush=True,
            )
            if not (MIN_OK_M <= min_gap <= MAX_OK_M):
                done = False
            # Proportional correction toward target clearance, damped.
            # Never chase below the penetration floor: back off instead.
            if min_gap < MIN_OK_M:
                correction = -(abs(min_gap) - 0.0002)
            else:
                correction = args.damping * (median_gap - TARGET_CLEARANCE_M)
            offsets[side] = min(0.05, max(0.0, offsets[side] + correction))
        entry["verdict"] = verdict["verdict"]
        entry["reasons"] = {
            side: verdict["per_foot"][side].get("reasons", [])
            for side in ("left", "right")
        }
        log.append(entry)
        # Persist every round (skin evals are expensive; never lose one).
        round_dir = args.output / f"round-{round_index}"
        round_dir.mkdir(parents=True, exist_ok=True)
        (round_dir / "airborne-run-root_motion.glb").write_bytes(authority_glb)
        (round_dir / "airborne-run-in_place.glb").write_bytes(inplace)
        for name, value in (
            ("world-plan", plan),
            ("solve-receipt", receipt),
            ("final-skinned-ground-receipt", {k: v for k, v in skin.items()}),
        ):
            (round_dir / f"{name}.json").write_text(
                json.dumps(value, indent=2, allow_nan=False) + "\n"
            )
        last = {"authority_glb": authority_glb, "inplace": inplace,
                "plan": plan, "receipt": receipt, "skin": skin}
        if done and verdict["verdict"] == "PASS":
            print(f"[round {round_index}] GROUNDED: both feet inside tolerance", flush=True)
            break
    else:
        print("rounds exhausted without full PASS; see reground-log.json", flush=True)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "airborne-run-root_motion.glb").write_bytes(last["authority_glb"])
    (args.output / "airborne-run-in_place.glb").write_bytes(last["inplace"])
    for name, value in (
        ("world-plan", last["plan"]),
        ("solve-receipt", last["receipt"]),
        ("final-skinned-ground-receipt", {k: v for k, v in last["skin"].items()}),
        ("reground-log", log),
    ):
        (args.output / f"{name}.json").write_text(
            json.dumps(value, indent=2, allow_nan=False) + "\n"
        )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
