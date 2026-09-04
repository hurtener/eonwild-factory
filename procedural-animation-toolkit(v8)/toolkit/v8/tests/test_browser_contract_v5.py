import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
class BrowserContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.js=(ROOT/'toolkit/v5/browser_demo/v5-viewer.js').read_text();cls.html=(ROOT/'toolkit/v5/browser_demo/index.html').read_text();cls.manifest=json.loads((ROOT/'validated_result/v5/animation-manifest.v5.json').read_text());cls.names={c['name'] for c in cls.manifest['clips']}
 def test_ui_state_is_visible_and_accessible(self):
  for token in ('aria-pressed','is-active','syncPlaybackUI','playerState','sequenceStatus','cancelSequence','timeline'):self.assertIn(token,self.js+self.html)
 def test_exact_handoff_and_root_continuity(self):
  for token in ('commitQueuedClip','exactHandoff','rootOffset','computeRootOffset','pending','sourcePhase','Q.slerp'):self.assertIn(token,self.js)
  self.assertNotIn('this.nextTime',self.js)
 def test_all_html_clip_references_exist(self):
  refs=set(re.findall(r'data-clip="([^"]+)"',self.html));self.assertTrue(refs);self.assertEqual([],sorted(refs-self.names))
 def test_all_manifest_action_queues_exist(self):
  for queue in self.manifest['actionSequences'].values():self.assertEqual([],sorted(set(queue)-self.names))
 def test_single_file_browser_is_embedded(self):
  s=(ROOT/'validated_result/v5/OPEN_ME_tarbosaurus_v5_3d_browser.html').read_text(errors='ignore');self.assertIn('__EONWILD_V5_GLB_BASE64',s);self.assertNotIn('src="v5-viewer.js"',s);self.assertNotIn('https://',s)
if __name__=='__main__':unittest.main()
