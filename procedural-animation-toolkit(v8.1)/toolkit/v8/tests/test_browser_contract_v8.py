from __future__ import annotations
import subprocess,unittest
from pathlib import Path

class TestBrowserV8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[1]
        cls.index=(cls.root/'browser_demo/index-v8.html').read_text()
        cls.js=(cls.root/'browser_demo/v8-viewer.js').read_text()
    def test_controls_and_v8_clips(self):
        combined=self.index+self.js
        for token in ('PROC_TURN_LEFT_35_V8_ROOTMOTION','PROC_TURN_RIGHT_35_V8_ROOTMOTION','PROC_BITE_ATTACK_V8','PROC_BITE_ATTACK_MIRRORED_V8','PROC_EAT_LOOP_V8','data-action="biteMirrored"','playPause','sequenceStatus'):
            self.assertIn(token,combined)
    def test_root_motion_loop_accumulation(self):
        self.assertIn('rootCycleDelta',self.js)
        self.assertIn('Math.floor(Math.max(0,t)/clip.duration)',self.js)
    def test_exact_handoff_and_button_state(self):
        self.assertIn('exact handoff',self.js)
        self.assertIn('commitQueuedClip',self.js)
        self.assertIn('aria-pressed',self.js)
        self.assertIn('is-active',self.js)
    def test_v8_embed_contract(self):
        self.assertIn('__EONWILD_V8_GLB_BASE64',self.js)
        self.assertIn('__EONWILD_V8_MANIFEST',self.js)
    def test_javascript_syntax(self):
        subprocess.run(['node','--check',str(self.root/'browser_demo/v8-viewer.js')],check=True)

if __name__=='__main__':unittest.main()
