#!/usr/bin/env python3
"""Prepare one source-bound provisional surface-mass proxy and audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eonwild_motion.dynamics.surface_mass import COORDINATES, prepare_surface_mass_proxy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--rig", type=Path, required=True)
    parser.add_argument("--animal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [path.read_bytes() for path in (args.source, args.rig, args.animal)]
    hashes = [hashlib.sha256(raw).hexdigest() for raw in rows]
    profile, audit = prepare_surface_mass_proxy(
        *rows,
        source_sha256=hashes[0],
        rig_sha256=hashes[1],
        animal_sha256=hashes[2],
        coordinate_system=COORDINATES,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in (("profile.json", profile), ("audit.json", audit)):
        (args.output / name).write_text(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
