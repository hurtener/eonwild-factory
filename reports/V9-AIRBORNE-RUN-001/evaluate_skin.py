"""Reopen an emitted iteration and evaluate its fixed source-ground binding."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import evaluate_airborne_skin

parser = argparse.ArgumentParser()
parser.add_argument("--iteration", type=Path, required=True)
parser.add_argument("--contact-profile", type=Path, required=True)
parser.add_argument("--profile", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
receipt = json.loads((args.iteration / "solve-receipt.json").read_text())
gait = load_airborne_gait(json.loads((args.profile or args.iteration / "engineering-profile.json").read_text()))
skin = evaluate_airborne_skin(Glb(args.iteration / "airborne-run-root_motion.glb"), contact_profile=json.loads(args.contact_profile.read_text()), gait=gait, body_height_m=receipt["body_height_m"])
(args.output or args.iteration / "final-skinned-ground-receipt.json").write_text(json.dumps(skin, indent=2) + "\n")
print(json.dumps({k: v for k, v in skin.items() if k not in {"frames", "skin_adapter", "distal_patch_vertex_indices"}}, indent=2))
