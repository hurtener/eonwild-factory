import sys,unittest
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap,AnatomicalBasis
from eonproc_v5.jaw import JawClosureModel
from eonproc_v5.polish import smooth_quaternions
class V5QualityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  full=ROOT.parents[1];cls.asset=GlbAsset(full/'inputs/tarbosaurus_source.glb');cls.sem=SemanticMap.load(full/'inputs/tarbosaurus_bone_map.edited.yml');cls.basis=AnatomicalBasis.gltf_y_up(cls.asset,cls.sem)
 def test_jaw_calibrates_to_safe_closed_pose(self):
  ground=self.asset.primitive().positions[:,1].min();hip=self.asset.rest_world[self.asset.name_to_node[self.sem.bone('pelvis')]][1,3]-ground;r=JawClosureModel(self.asset,self.sem,self.basis,hip).calibrate(target_minimum_gap_m=hip*.0015);self.assertAlmostEqual(r.close_degrees,50.,places=3);self.assertGreater(r.minimum_gap_m,0);self.assertLess(r.minimum_gap_m,.003)
 def test_loop_polish_closes_exactly(self):
  t=np.linspace(0,2*np.pi,121);q=Rotation.from_rotvec(np.c_[np.zeros_like(t),.1*np.sin(t)+.008*np.sin(17*t),np.zeros_like(t)]).as_quat();q[-1]=q[0];out,_=smooth_quaternions(q,True,7,3);self.assertTrue(np.array_equal(out[-1],out[0]))
if __name__=='__main__':unittest.main()
