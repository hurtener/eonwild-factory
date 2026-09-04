from __future__ import annotations
import re,subprocess,unittest
from pathlib import Path

class TestBrowserV7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[1]
        cls.index=(cls.root/'browser_demo/index-v7.html').read_text()
        cls.js=(cls.root/'browser_demo/v7-viewer.js').read_text()
    def test_controls_and_turns(self):
        for token in ('PROC_TURN_LEFT_35_V7_ROOTMOTION','PROC_TURN_RIGHT_35_V7_ROOTMOTION','data-action="biteMirrored"','playPause','sequenceStatus'):
            self.assertIn(token,self.index+self.js)
    def test_root_motion_loop_accumulation(self):
        self.assertIn('rootCycleDelta',self.js)
        self.assertIn('Math.floor(Math.max(0,t)/clip.duration)',self.js)
    def test_exact_handoff_player_contract(self):
        self.assertIn('exact handoff',self.js)
        self.assertIn('commitQueuedClip',self.js)
        self.assertIn('aria-pressed',self.js)
    def test_javascript_syntax(self):
        subprocess.run(['node','--check',str(self.root/'browser_demo/v7-viewer.js')],check=True)

if __name__=='__main__':unittest.main()
