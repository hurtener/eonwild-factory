"""Regression witnesses for the C50 duplicated/disconnected tail failure."""
import unittest
from copy import deepcopy
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from eonwild_motion.glb.container import Glb
from eonwild_motion.factory.chain_subdivision import subdivide_chain
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.moco_binding import validate_axial_bindings

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/sha256/2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f.glb'

class TailBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=Glb(SOURCE)
        cls.raw,cls.receipt=subdivide_chain(cls.original,['Bone_'+str(i).zfill(3) for i in range(24,15,-1)],12)
        cls.source=Glb.from_bytes(cls.raw)
        cls.roles={'tail.'+str(i):cls.source.name_to_node[n] for i,n in enumerate(cls.receipt['chain'])}
        cls.metadata={'axial_bindings':[dict(body='tail_'+str(i),role='tail.'+str(i)) for i in range(12)],
            'tail_chain':[dict(body='tail_'+str(i),role='tail.'+str(i),end_role='tail.'+str(i+1)) for i in range(12)]}

    def test_connected_weighted_links_and_old_bind_preservation(self):
        validate_axial_bindings(self.metadata,self.roles,self.source.parents)
        self.assertEqual(self.receipt['links'],12)
        self.assertEqual(self.receipt['nodes'],13)
        self.assertLess(self.receipt['bind_skin_error_m'],3e-6)
        self.assertLess(self.receipt['existing_joint_world_error'],3e-6)
        # No incidental rounding changes in original inverse binds or jaw skin.
        old_ib=np.array(self.original.accessor_values(self.original.document['skins'][0]['inverseBindMatrices']))
        new_ib=np.array(self.source.accessor_values(self.source.document['skins'][0]['inverseBindMatrices']))
        np.testing.assert_array_equal(old_ib,new_ib[:len(old_ib)])
        attrs=self.source.document['meshes'][0]['primitives'][0]['attributes']
        old_ids=np.concatenate([self.original.accessor_values(attrs['JOINTS_'+str(i)]) for i in range(3)],axis=1)
        new_ids=np.concatenate([self.source.accessor_values(attrs['JOINTS_'+str(i)]) for i in range(3)],axis=1).astype(int)
        old_weights=np.concatenate([self.original.accessor_values(attrs['WEIGHTS_'+str(i)]) for i in range(3)],axis=1)
        new_weights=np.concatenate([self.source.accessor_values(attrs['WEIGHTS_'+str(i)]) for i in range(3)],axis=1)
        np.testing.assert_allclose(new_weights.sum(axis=1),old_weights.sum(axis=1),atol=2e-7)
        nodes=self.source.document['skins'][0]['joints']
        worlds=np.array(_world_matrices(self.source,self.source.rest_translation,self.source.rest_rotation,self.source.rest_scale))
        positions=np.array(self.source.accessor_values(attrs['POSITION']))
        positions=np.c_[positions,np.ones(len(positions))]
        inverse=new_ib.reshape(-1,4,4).transpose(0,2,1)
        def skin(w):return np.einsum('nv,nvij,nj->ni',new_weights,(w[nodes]@inverse)[new_ids],positions)[:,:3]
        before=skin(worlds)
        for name in self.receipt['inserted']:
            node=self.source.name_to_node[name];slot=nodes.index(node)
            self.assertGreater(new_weights[new_ids==slot].sum(),0)
            rotations=list(self.source.rest_rotation)
            rotations[node]=(Rotation.from_quat(rotations[node])*Rotation.from_rotvec([0,.12,0])).as_quat()
            after=skin(np.array(_world_matrices(self.source,self.source.rest_translation,rotations,self.source.rest_scale)))
            self.assertGreater(np.max(np.linalg.norm(after-before,axis=1)),.001)
        original_tail={self.original.document['skins'][0]['joints'].index(self.original.name_to_node['Bone_'+str(i).zfill(3)]) for i in range(24,15,-1)}
        unaffected=(np.where(np.isin(old_ids,list(original_tail)),old_weights,0).sum(axis=1)==0)
        np.testing.assert_array_equal(new_ids[unaffected],old_ids[unaffected])
        np.testing.assert_array_equal(new_weights[unaffected],old_weights[unaffected])

    def test_rejects_duplicate_drive_disconnection_and_wrong_count(self):
        m=deepcopy(self.metadata);m['axial_bindings'][1]['role']='tail.0'
        with self.assertRaisesRegex(ValueError,'unique'):validate_axial_bindings(m,self.roles,self.source.parents)
        parents=list(self.source.parents);parents[self.roles['tail.3']]=None
        with self.assertRaisesRegex(ValueError,'connected'):validate_axial_bindings(self.metadata,self.roles,parents)
        m=deepcopy(self.metadata);m['tail_chain'].pop()
        with self.assertRaisesRegex(ValueError,'count'):validate_axial_bindings(m,self.roles,self.source.parents)

if __name__=='__main__':unittest.main()
