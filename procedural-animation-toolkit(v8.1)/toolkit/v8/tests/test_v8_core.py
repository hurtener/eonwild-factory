from __future__ import annotations
import unittest
import numpy as np
from eonproc_v4.clip import AnimationClip
from eonproc_v8.profile import BipedV8Profile
from eonproc_v8.actions import _jaw_event, _ramp, _plateau
from eonproc_v8.locomotion import _turn_envelope
from eonproc_v8.transitions import pose_transition

class TestV8Core(unittest.TestCase):
    def test_profile_action_and_turn_hierarchy(self):
        p=BipedV8Profile()
        self.assertGreater(p.turn_head_lead_deg,p.turn_neck_lead_deg)
        self.assertGreater(p.turn_neck_lead_deg,p.turn_chest_lead_deg)
        self.assertGreater(p.turn_tail_counter_tip_deg,p.turn_tail_counter_root_deg)
        self.assertGreater(p.bite_contact_fraction,p.bite_first_catch_fraction)
        self.assertGreater(p.bite_hold_end_fraction,p.bite_contact_fraction)
        self.assertGreater(p.bite_recovery_fraction,p.bite_hold_end_fraction)
        self.assertEqual(len(p.eating_bite_times),p.eating_bite_count)
        self.assertEqual(len(set(p.eating_bite_strengths)),p.eating_bite_count)

    def test_late_gape_is_closed_at_contact(self):
        p=BipedV8Profile();c=p.eating_bite_times[0]
        before,_=_jaw_event(c-.05,c,1.0,p.eating_jaw_open_deg)
        at,_=_jaw_event(c,c,1.0,p.eating_jaw_open_deg)
        pull,env=_jaw_event(c+.08,c,1.0,p.eating_jaw_open_deg)
        self.assertGreater(before,0.1)
        self.assertLess(abs(at),np.radians(1.0))
        self.assertGreater(env['pull'],0.5)
        self.assertLess(abs(pull),np.radians(1.0))

    def test_minimum_jerk_helpers_close(self):
        self.assertEqual(_ramp(0.1,.2,.4),0.0)
        self.assertEqual(_ramp(.5,.2,.4),1.0)
        self.assertEqual(_plateau(0,.1,.2,.7,.8),0.0)
        self.assertGreater(_plateau(.45,.1,.2,.7,.8),.99)
        self.assertEqual(_plateau(1,.1,.2,.7,.8),0.0)

    def test_turn_envelope_exact_ends(self):
        p=BipedV8Profile()
        self.assertAlmostEqual(_turn_envelope(0,p.turn_lead_rise_fraction,p.turn_lead_fall_start_fraction),0.0,places=12)
        self.assertAlmostEqual(_turn_envelope(1,p.turn_lead_rise_fraction,p.turn_lead_fall_start_fraction),0.0,places=12)

    def test_transition_keeps_root_and_pelvis_endpoints(self):
        t=np.linspace(0,1,61);q=np.tile([0.,0.,0.,1.],(61,1))
        a=AnimationClip('a',t,{'bone':q},{'root':np.column_stack([t*0,t*0,t]),'pelvis':np.column_stack([t*.01,t*.02,t*0])},{'loop':True})
        b=AnimationClip('b',t,{'bone':q},{'root':np.column_stack([t*0,t*0,t+.4]),'pelvis':np.column_stack([t*.03,t*.01,t*0])},{'loop':True})
        tr=pose_transition('t',a,b,.8,60,.5,.25,'root')
        ti=round(.25*(len(t)-1))
        np.testing.assert_allclose(tr.translations['root'][-1],b.translations['root'][ti],atol=1e-12)
        np.testing.assert_allclose(tr.translations['pelvis'][-1],b.translations['pelvis'][ti],atol=1e-12)

if __name__=='__main__':unittest.main()
