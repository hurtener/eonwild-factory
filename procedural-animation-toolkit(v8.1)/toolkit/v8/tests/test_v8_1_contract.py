from __future__ import annotations
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from eonproc_v8.profile import BipedV8Profile

class TestV81Contract(unittest.TestCase):
    def test_neutral_chain_and_idle_contract(self):
        p=BipedV8Profile()
        self.assertEqual((p.body_lean_deg,p.pelvis_neutral_pitch_deg,p.neck_relaxed_pitch_deg,p.head_horizon_pitch_deg),(-1.0,-1.10,-.60,.35))
        self.assertEqual(p.foot_pivot_gap_fraction,.90)

    def test_power_timing_is_biomechanically_ordered(self):
        p=BipedV8Profile()
        phases=(p.power_coil_start_fraction,p.power_coil_end_fraction,p.power_takeoff_fraction,p.power_apex_fraction,p.power_bite_contact_fraction,p.power_land_fraction,p.power_catch_fraction,p.power_arrest_end_fraction)
        self.assertEqual(tuple(sorted(phases)),phases)
        self.assertTrue(.17 <= (p.power_land_fraction-p.power_takeoff_fraction)*p.power_duration_seconds <= .21)
        self.assertTrue(.65 <= p.power_launch_load <= .75)
        self.assertTrue(.05 <= p.power_root_rise_hip_fraction <= .09)
        self.assertTrue(.30 <= p.power_forward_hip_fraction <= .45)

if __name__=='__main__': unittest.main()
