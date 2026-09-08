"""Bounded fast-walk recovery candidate identity and fixed-leg-clock checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.planning.grounded_gait import load_grounded_gait


ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / 'recipes/heavy-biped/tarbosaurus-pin-552-1-adult-fast-walk-recovery.v3.json'


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def test_v3_fast_walk_recovery_selects_only_the_rate_limited_world_carrier():
    recipe, paths = load_recipe(V3, ROOT)
    assert recipe['version'] == 3
    assert recipe['supersedes'] == 'heavy-biped.tarbosaurus-pin-552-1-adult-fast-walk-recovery.v2'
    for binding in recipe.values():
        if isinstance(binding, dict) and {'path', 'sha256'} <= set(binding):
            assert hashlib.sha256((ROOT / binding['path']).read_bytes()).hexdigest() == binding['sha256']

    after = load_grounded_gait(read(paths['program_profile']))
    assert (after.step_period_s, after.step_length_body_heights, after.duty_factor,
            after.cycles, after.sample_hz) == (.8, .6, .62, 1, 120)
    assert (after.touchdown_reach_body_heights, after.swing_clearance_body_heights,
            after.pelvis_crouch_body_heights, after.pelvis_excursion_body_heights) == (.25, .22, 0, .016)
    assert (after.metatarsal_recovery_world_degrees_from_down,
            after.metatarsal_recovery_release_fraction,
            after.toe_recovery_peak_fraction,
            after.rounded_swing_peak_fraction) == (-20, .9, .42, .42)
    assert (after.pad_recovery_pitch_degrees, after.toe_flex_degrees,
            after.push_off_pitch_degrees, after.push_off_start_fraction,
            after.swing_hip_lift_degrees, after.centered_stance) == (35, 25, 28, .6, 30, True)
    assert after.metatarsal_recovery_carrier == 'rate_limited_c2'
