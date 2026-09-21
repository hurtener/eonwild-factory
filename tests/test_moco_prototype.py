"""Optional actual OpenSim physics witnesses; run with the Moco interpreter."""
import json
from pathlib import Path
import unittest
import re
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

    def spatial_model(self,mass_scale=1.):
        a=admission();a['points']['spine.2']=[.5,-.1,0]
        a['points']['nose']=[3.4,0.,0.]
        for i in range(1,5):a['points'][f'neck.{i}']=[1.2+.3*i,.05*i,0]
        vertices=[[x,-.16,z] for x in np.linspace(-.1,.6,30) for z in (-.2,0,.2)]
        a['foot_surface']={s:dict(vertices_m=vertices,toe_midpoint_m=[.25,-.1,0]) for s in ('left','right')}
        recipe=json.loads((Path(__file__).parents[1]/'catalog/behaviors/moco-spatial-stride.v1.json').read_text())
        a['animal']['measurements']['body_mass']['value']*=mass_scale
        recipe['contact']['stiffness_N_m2']*=mass_scale
        return make_model(a,recipe)

    def test_admitted_attention_witness_moves_with_skull(self):
        model,receipt=self.spatial_model();state=model.initSystem()
        self.assertEqual(receipt['attention_frame'],'/nose')
        nose=o.PhysicalOffsetFrame.safeDownCast(model.getComponent('/nose'))
        head=model.getBodySet().get('head')
        positions=[]
        for pitch in (-.12,.14):
            model.getCoordinateSet().get('neck').setValue(state,pitch)
            model.getCoordinateSet().get('head_yaw').setValue(state,.08)
            model.realizePosition(state)
            actual=nose.getPositionInGround(state).to_numpy()
            expected=head.findStationLocationInGround(state,o.Vec3(*receipt['nose_local_m'])).to_numpy()
            np.testing.assert_allclose(actual,expected,atol=1e-12)
            positions.append(actual)
        self.assertGreater(np.linalg.norm(positions[1]-positions[0]),.1)

    def test_periodic_basis_keeps_roll_axes_and_mean_hip_adduction(self):
        from eonwild_motion.solve.moco_coordination import Coordination,basis_parameters
        model,_=self.spatial_model()
        names=[c.getName() for c in model.getCoordinateSet()]
        parameters=basis_parameters(names,3)
        self.assertIn(('hip_l_roll',0,'constant'),parameters)
        self.assertIn(('hip_l_yaw',0,'constant'),parameters)
        self.assertIn(('chest_roll',1,'sin'),parameters)
        self.assertFalse(any(n=='hip_r_roll' for n,_,_ in parameters))
        p=Coordination.__new__(Coordination);p.names=names;p.index={n:i for i,n in enumerate(names)}
        p.period=1.;p.parameters=parameters;p._cache={}
        times=np.array([.13,.63]);arrays=p._arrays(times)
        # Every left roll contribution must equal the negated right roll at
        # the opposite half-stride, including the static adduction component.
        for values in arrays:
            np.testing.assert_allclose(values[0,p.index['hip_l_roll']],-values[1,p.index['hip_r_roll']],atol=1e-10)
        constant=parameters.index(('hip_l_roll',0,'constant'))
        self.assertEqual(arrays[0][0,p.index['hip_r_roll'],constant],-1.)

    def test_same_topology_warm_start_retains_nonzero_implicit_accelerations(self):
        import tempfile
        from eonwild_motion.solve.moco_spatial import transfer_guess
        model,_=self.spatial_model()
        study=o.MocoStudy();problem=study.updProblem();problem.setModelAsCopy(model)
        problem.setTimeBounds(0,1)
        problem.setStateInfoPattern('.*/value',[-20,20]);problem.setStateInfoPattern('.*/speed',[-20,20])
        problem.setStateInfoPattern('.*/activation',[-1,1])
        solver=study.initCasADiSolver();solver.set_multibody_dynamics_mode('implicit');solver.set_num_mesh_intervals(30)
        source=solver.createGuess();times=source.getTimeMat()
        def vector(values):
            result=o.Vector(len(values),0)
            for i,value in enumerate(values):result[i]=float(value)
            return result
        source.setState('/jointset/neck/neck/value',vector(.1*np.sin(2*np.pi*times)))
        source.setState('/jointset/neck/neck/speed',vector(.2*np.pi*np.cos(2*np.pi*times)))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'guess.sto';source.write(str(path))
            restored=transfer_guess(solver,path)
        names=list(restored.getDerivativeNames());col=names.index('/jointset/neck/neck/accel')
        acceleration=np.asarray(restored.getDerivativesTrajectoryMat())[:,col]
        np.testing.assert_allclose(acceleration[2:-2],-.4*np.pi**2*np.sin(2*np.pi*times[2:-2]),atol=.02)

    def test_optimizer_mass_units_preserve_contact_acceleration(self):
        outputs=[]
        for scale in (1.,.001):
            model,_=self.spatial_model(scale);state=model.initSystem()
            for n,q in dict(height=2.2,pitch=.04,hip_l=.4,knee_l=-1.,ankle_l=.6,hip_r=.7,knee_r=-1.4,ankle_r=.9,hip_l_roll=.03).items():
                model.getCoordinateSet().get(n).setValue(state,q)
            model.setStateVariableValue(state,'/forceset/motor_tail_0_yaw/activation',.03)
            model.realizeAcceleration(state);outputs.append(state.getUDot().to_numpy().copy())
        np.testing.assert_allclose(outputs[0],outputs[1],rtol=1e-8,atol=1e-7)

    def test_axial_reserve_is_internal_and_leaves_static_headroom(self):
        model,receipt=self.spatial_model()
        for data in receipt['actuators'].values():
            if 'static_gravity_minus_passive_demand_Nm' in data:
                self.assertLessEqual(data['static_gravity_minus_passive_demand_Nm']/data['capacity_Nm'],.40000001)
        self.assertEqual(model.getNumControls(),31)
        self.assertEqual(receipt['root_reserves'],[])

    def test_spatial_tail_motor_reacts_through_body_without_external_support(self):
        model,r=self.spatial_model();state=model.initSystem()
        model.getCoordinateSet().get('height').setValue(state,10)
        model.setStateVariableValue(state,'/forceset/motor_tail_0_yaw/activation',.05)
        model.realizeAcceleration(state)
        acc=model.calcMassCenterAcceleration(state)
        np.testing.assert_allclose([acc.get(i) for i in range(3)],[0,-9.80665,0],atol=1e-7)
        self.assertGreater(abs(model.getCoordinateSet().get('yaw').getAccelerationValue(state)),1e-5)
        self.assertAlmostEqual(model.getTotalMass(state),1000)
        self.assertEqual(model.getJointSet().get('root').numCoordinates(),6)
        self.assertEqual(r['root_reserves'],[])

    def test_spatial_half_stride_reflection_preserves_geometry(self):
        from eonwild_motion.solve.moco_spatial import reflected_coordinate
        model,_=self.spatial_model()
        values=dict(height=2.1,pitch=.08,yaw=.1,roll=-.05,lateral=.12,
                    hip_l=.3,knee_l=-1.,ankle_l=.8,hip_r=.8,knee_r=-1.4,ankle_r=1.1,
                    hip_l_yaw=.08,hip_r_roll=-.08,tail_0_yaw=.12,neck_upper_yaw=-.05)
        def positions(q):
            state=model.initSystem()
            for name,value in q.items():model.getCoordinateSet().get(name).setValue(state,value)
            model.realizePosition(state)
            return {b.getName():np.array([b.getPositionInGround(state).get(i) for i in range(3)]) for b in model.getBodySet()}
        def swap(name):return re.sub(r'_(l|r)(?=_|$)',lambda m:'_r' if m.group(1)=='l' else '_l',name)
        before=positions(values)
        after=positions({swap(n):(-v if reflected_coordinate(n) else v) for n,v in values.items()})
        for name,position in before.items():np.testing.assert_allclose(after[swap(name)],position*[1,1,-1],atol=1e-9)


if __name__ == '__main__':unittest.main()
