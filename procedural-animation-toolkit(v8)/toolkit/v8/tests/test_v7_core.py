from __future__ import annotations

import unittest
import numpy as np

from eonproc_v4.clip import AnimationClip
from eonproc_v7.profile import BipedV7Profile
from eonproc_v7.locomotion import _turn_envelope
from eonproc_v7.transitions import pose_transition, phase_matched_loop_transition


class TestV7Core(unittest.TestCase):
    def test_turn_envelope_is_c2_like_at_ends(self):
        self.assertAlmostEqual(_turn_envelope(0.0, .18, .76), 0.0, places=12)
        self.assertAlmostEqual(_turn_envelope(1.0, .18, .76), 0.0, places=12)
        self.assertGreater(_turn_envelope(.30, .18, .76), .99)
        self.assertGreater(_turn_envelope(.70, .18, .76), .99)
        eps=1e-4
        self.assertLess(abs(_turn_envelope(eps,.18,.76)-_turn_envelope(0,.18,.76)),1e-8)
        self.assertLess(abs(_turn_envelope(1,.18,.76)-_turn_envelope(1-eps,.18,.76)),1e-8)

    def test_v7_profile_is_contact_conservative(self):
        p=BipedV7Profile()
        self.assertGreaterEqual(p.internal_sample_hz, 120)
        self.assertGreaterEqual(p.export_sample_hz, 60)
        self.assertLess(p.pelvis_support_shift_gain, .04)
        self.assertGreater(p.turn_head_lead_deg, p.turn_neck_lead_deg)
        self.assertGreater(p.turn_neck_lead_deg, p.turn_chest_lead_deg)
        self.assertGreater(p.turn_tail_counter_tip_deg, p.turn_tail_counter_root_deg)

    def _clip(self,name,with_pelvis=True):
        t=np.linspace(0,1,61)
        q=np.tile(np.array([0.,0.,0.,1.]),(len(t),1))
        trans={'root':np.column_stack([np.zeros(len(t)),np.zeros(len(t)),t])}
        if with_pelvis:
            trans['pelvis']=np.column_stack([.01*np.sin(2*np.pi*t),.01*np.cos(2*np.pi*t),np.zeros(len(t))])
        return AnimationClip(name=name,times=t,rotations={'bone':q},translations=trans,extras={'loop':True})

    def test_pose_transition_preserves_pelvis_endpoints(self):
        a=self._clip('a');b=self._clip('b')
        b.translations['pelvis']+=np.array([.02,.01,0.])
        tr=pose_transition('t',a,b,.7,60,.5,.25,'root')
        target_idx=round(.25*(len(b.times)-1))
        np.testing.assert_allclose(tr.translations['pelvis'][-1],b.translations['pelvis'][target_idx],atol=1e-12)
        self.assertTrue(tr.diagnostics['quality_gates']['pelvis_translation_preserved'])

    def test_transition_handles_track_present_on_one_side(self):
        a=self._clip('a',with_pelvis=False);b=self._clip('b',with_pelvis=True)
        tr=pose_transition('t',a,b,.5,60,0,0,'root')
        self.assertIn('pelvis',tr.translations)
        tr2=phase_matched_loop_transition('p',a,b,1.0,60,'root')
        self.assertIn('pelvis',tr2.translations)


if __name__=='__main__':
    unittest.main()
