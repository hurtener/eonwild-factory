"""Optional actual OpenSim physics witnesses; run with the Moco interpreter."""
import json
from pathlib import Path
import unittest
import numpy as np
try:
    import opensim as o
except ImportError:
    o = None
from eonwild_motion.solve.moco_prototype import make_model, seed_coordinates
from eonwild_motion.solve.moco_tasks import task_sample


def admission(scale=1, mass=1000):
    points = {'neck.0':[1.2,0,0], 'head':[2.7,.25,0]}
    for side,z in [('left',-.4),('right',.4)]:
        for i,p in enumerate([[0,0,z],[.2,-.8,z],[-.3,-1.7,z],[-.2,-2.2,z]]):
            points[f'{side}Leg.{i}']=p
    points['legs.left.toeChains.0.2']=[.3,-2.2,-.4]
    for i,p in enumerate([[-.4,.1,0],[-1.5,.12,0],[-2.8,.05,0],[-4,-.1,0],[-5,-.3,0]]):points[f'tail.{i}']=p
    return {'points':{k:(np.asarray(v)*scale).tolist() for k,v in points.items()},
            'animal':{'measurements':{'body_mass':{'value':mass,'unit':'kg'}}},
            'preferred_speed_mps':3.4,'step_length_m':2.02}


@unittest.skipUnless(o is not None, 'Optional OpenSim environment required')
class ModelPhysics(unittest.TestCase):
    def setUp(self):
        self.recipe=json.loads((Path(__file__).parents[1]/'catalog/behaviors/moco-stride-prototype.v1.json').read_text())

    def test_mass_and_internal_only_actuation(self):
        model,receipt=make_model(admission(),self.recipe);state=model.initSystem()
        self.assertAlmostEqual(model.getTotalMass(state),1000)
        self.assertEqual(receipt['root_reserves'],[])
        self.assertEqual(model.getNumControls(),11)
        for name in receipt['actuators']:
            actuator=o.ActivationCoordinateActuator.safeDownCast(model.getForceSet().get(name))
            self.assertNotIn(actuator.getCoordinate().getName(),['pitch','height','forward'])

    def test_inertia_and_geometry_scale_from_admission(self):
        _,a=make_model(admission(),self.recipe);_,b=make_model(admission(2,8000),self.recipe)
        for name in a['segments']:
            np.testing.assert_allclose(b['segments'][name]['inertia_kg_m2'],32*np.array(a['segments'][name]['inertia_kg_m2']),atol=1e-10)
            np.testing.assert_allclose(b['segments'][name]['com_local_m'],2*np.array(a['segments'][name]['com_local_m']),atol=1e-12)

    def test_unactuated_airborne_body_falls_under_gravity(self):
        model,_=make_model(admission(),self.recipe);state=model.initSystem()
        model.getCoordinateSet().get('height').setValue(state,10)
        model.realizeAcceleration(state);acc=model.calcMassCenterAcceleration(state)
        np.testing.assert_allclose([acc.get(i) for i in range(3)],[0,-9.80665,0],atol=1e-7)

    def test_floor_contact_pushes_up_and_not_sideways(self):
        model,r=make_model(admission(),self.recipe);state=model.initSystem()
        length=sum(r['segment_lengths_m']);radius=r['contacts'][0]['radius_m']
        model.getCoordinateSet().get('height').setValue(state,length+radius-.009)
        model.realizeVelocity(state)
        for c in r['contacts']:
            values=model.getForceSet().get(c['force']).getRecordValues(state)
            self.assertGreater(values.get(1),100)
            self.assertLess(abs(values.get(0))+abs(values.get(2)),1e-7)

    def test_seed_contact_anchor_does_not_slide_with_root(self):
        a=admission();model,r=make_model(a,self.recipe);state=model.initSystem()
        times=np.linspace(.05,.45,9)*a['step_length_m']/a['preferred_speed_mps']
        q=seed_coordinates(a,self.recipe,times);positions=[]
        for i,t in enumerate(times):
            for name,values in q.items():model.getCoordinateSet().get(name).setValue(state,float(values[i]))
            model.realizePosition(state);p=model.getBodySet().get('toe_l').getPositionInGround(state)
            positions.append([p.get(j) for j in range(3)])
        np.testing.assert_allclose(positions,np.broadcast_to(positions[0],(len(times),3)),atol=1e-10)

    def test_calibrated_model_has_internal_toes_chest_and_conserves_mass(self):
        a=admission();a['points']['spine.2']=[.5,-.1,0]
        vertices=[[x,-.16,0] for x in np.linspace(-.1,.6,60)]
        a['foot_surface']={s:dict(vertices_m=vertices,toe_midpoint_m=[.25,-.1,0]) for s in ('left','right')}
        recipe=json.loads((Path(__file__).parents[1]/'catalog/behaviors/moco-stride-prototype.v2.json').read_text())
        model,receipt=make_model(a,recipe);state=model.initSystem()
        self.assertAlmostEqual(model.getTotalMass(state),1000)
        self.assertEqual(model.getNumControls(),14)
        self.assertEqual(len(receipt['contacts']),10)
        self.assertEqual(receipt['root_reserves'],[])
        for name in ('chest','digit_l','digit_r'):self.assertIn(name,receipt['coordinates'])
        model.getCoordinateSet().get('height').setValue(state,10)
        model.realizeAcceleration(state)
        gravity=model.calcMassCenterAcceleration(state)
        np.testing.assert_allclose([gravity.get(i) for i in range(3)],[0,-9.80665,0],atol=1e-6)
        T=2*a['step_length_m']/a['preferred_speed_mps']
        for t in (0.,recipe['calibrated_task']['duty_factor']*T,.5*T,T):
            before,_=task_sample(a,receipt,recipe,t-1e-7)
            after,_=task_sample(a,receipt,recipe,t+1e-7)
            for name in before:self.assertLess(np.linalg.norm(after[name]-before[name]),1e-5)
        # Heel release must carry velocity into swing, rather than easing to a
        # micro-stop and immediately restarting the recovery.
        release=recipe['calibrated_task']['duty_factor']*T
        eps=1e-6
        before,_=task_sample(a,receipt,recipe,release-eps)
        at,_=task_sample(a,receipt,recipe,release)
        after,_=task_sample(a,receipt,recipe,release+eps)
        v0=(at['/bodyset/toe_l']-before['/bodyset/toe_l'])/eps
        v1=(after['/bodyset/toe_l']-at['/bodyset/toe_l'])/eps
        np.testing.assert_allclose(v0,v1,atol=1e-3)
        self.assertGreater(np.linalg.norm(v0),.1)

    def test_calibrated_model_rejects_missing_sole_admission(self):
        recipe=json.loads((Path(__file__).parents[1]/'catalog/behaviors/moco-stride-prototype.v2.json').read_text())
        with self.assertRaisesRegex(ValueError,'sole geometry'):make_model(admission(),recipe)


if __name__ == '__main__':unittest.main()
