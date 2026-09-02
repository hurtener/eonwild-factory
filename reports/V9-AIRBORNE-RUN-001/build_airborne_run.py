#!/usr/bin/env python3
"""Task-local CLI for the reusable semantic airborne-gait vertical."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import solve_airborne_gait, evaluate_airborne_skin


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-clip", required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=ROOT / "profiles/v9/program.airborne-gait.run.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contact-profile", type=Path)
    args = parser.parse_args()
    binding = json.loads(args.binding.read_text())
    gait = load_airborne_gait(json.loads(args.profile.read_text()))
    authority, inplace, plan, receipt = solve_airborne_gait(Glb(args.source), source_clip=args.source_clip, semantic_roles=binding["roles"], gait=gait)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "airborne-run-root_motion.glb").write_bytes(authority)
    (args.output / "airborne-run-in_place.glb").write_bytes(inplace)
    for name, value in (("world-plan", plan), ("solve-receipt", receipt)):
        (args.output / f"{name}.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    if args.contact_profile:
        skin = evaluate_airborne_skin(Glb.from_bytes(authority), contact_profile=json.loads(args.contact_profile.read_text()), gait=gait, body_height_m=receipt["body_height_m"])
        (args.output / "final-skinned-ground-receipt.json").write_text(json.dumps(skin, indent=2, allow_nan=False) + "\n")
        print(json.dumps({k: v for k, v in skin.items() if k not in {"frames", "skin_adapter"}}, indent=2))
    print(json.dumps({k: v for k, v in receipt.items() if k not in {"emitted_proxy_samples", "semantic_binding", "body_response"}}, indent=2))


if __name__ == "__main__":
    main()
