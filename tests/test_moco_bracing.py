"""Focused witnesses for internal support, tail subdivision and physical stops."""
import json
import unittest
from pathlib import Path
import numpy as np
from test_moco_prototype import admission,o
from eonwild_motion.solve.moco_prototype import make_model

@unittest.skipUnless(o is not None,'Optional OpenSim environment required')
class SupportedBody(unittest.TestCase):
    def model(self,mass_scale=1.,recipe_name='moco-supported-stride.v1.json'):
        a=admission(mass=1000*mass_scale)
        a['points'].update({'spine.2':[.5,-.1,0],'nose':[3.4,0.,0.]})
        for i in range(1,5):a['points'][f'neck.{i}']=[1.2+.3*i,.05*i,0]
        vertices=[[x,-.16,z] for x in np.linspace(-.1,.6,30) for z in (-.2,0,.2)]
        a['foot_surface']={s:dict(vertices_m=vertices,toe_midpoint_m=[.25,-.1,0]) for s in ('left','right')}
        recipe=json.loads((Path(__file__).parents[1]/'catalog/behaviors'/recipe_name).read_text())
        recipe['contact']['stiffness_N_m2']*=mass_scale
        return make_model(a,recipe)

    def test_material_clearance_follows_articulated_toe_without_external_support(self):
        model,r=self.model(recipe_name='moco-contact-support.v1.json')
        state=model.initSystem()
        model.getCoordinateSet().get('height').setValue(state,10)
        model.getCoordinateSet().get('ankle_l').setValue(state,.6)
        model.getCoordinateSet().get('digit_l').setValue(state,.4)
        model.realizeAcceleration(state)
        points=r['material_foot_witnesses']['points']
        self.assertTrue(any(p['body']=='digit_l' for p in points))
        self.assertTrue(any(p['body']=='toe_l' for p in points))
        for point in points:
            frame=o.PhysicalFrame.safeDownCast(model.getComponent(point['path']))
            parent=model.getBodySet().get(point['body'])
            expected=parent.findStationLocationInGround(state,o.Vec3(*point['local_m']))
            np.testing.assert_allclose(frame.getPositionInGround(state).to_numpy(),expected.to_numpy(),atol=1e-12)
        self.assertEqual(model.getNumControls(),len(r['actuators']))
        self.assertFalse(r['root_reserves'])
        np.testing.assert_allclose(model.calcMassCenterAcceleration(state).to_numpy(),[0,-9.80665,0],atol=1e-6)

    def test_arbitrary_admitted_tail_count_and_internal_support(self):
        model,r=self.model();state=model.initSystem()
        self.assertEqual(len(r['tail_chain']),4) # fixture has five admitted nodes
        self.assertEqual(r['tail_terminal_body'],'tail_3')
        total=sum(r['segments'][b['body']]['mass_kg'] for b in r['tail_chain'])
        self.assertAlmostEqual(total,r['tail_subdivision']['mass_kg'])
        self.assertAlmostEqual(model.getTotalMass(state),1000)
        model.getCoordinateSet().get('height').setValue(state,10)
        model.setStateVariableValue(state,'/forceset/motor_tail_0_yaw/activation',.2)
        model.realizeAcceleration(state)
        np.testing.assert_allclose(model.calcMassCenterAcceleration(state).to_numpy(),[0,-9.80665,0],atol=1e-6)
        self.assertFalse(r['root_reserves'])

    def test_calibrated_loaded_support_has_the_declared_torque(self):
        model,r=self.model();state=model.initSystem()
        model.getCoordinateSet().get('height').setValue(state,10)
        for name,entry in r['bracing']['coordinates'].items():
            model.getCoordinateSet().get(name).setValue(state,entry['loaded_angle_rad'])
        model.realizeVelocity(state)
        for name,entry in r['bracing']['coordinates'].items():
            spring=model.getForceSet().get('passive_'+name)
            actual=spring.getRecordValues(state).get(0)
            self.assertAlmostEqual(actual,entry['holding_demand_Nm']*entry['supported_fraction'],places=6)

    def test_rotational_limit_damping_dissipates_in_correct_units(self):
        model,r=self.model();state=model.initSystem()
        coordinate=model.getCoordinateSet().get('knee_l')
        force=model.getForceSet().get('limit_knee_l')
        coordinate.setValue(state,coordinate.getRangeMax()+.15)
        coordinate.setSpeedValue(state,0);model.realizeVelocity(state)
        elastic=force.getRecordValues(state).get(0)
        coordinate.setSpeedValue(state,1);model.realizeVelocity(state)
        moving=force.getRecordValues(state).get(0)
        expected=-r['actuators']['motor_knee_l']['capacity_Nm']*.01
        self.assertLess(elastic,0)
        self.assertAlmostEqual(moving-elastic,expected,places=6)

    def test_support_and_stops_preserve_mass_unit_acceleration(self):
        observed=[]
        for scale in (1.,.001):
            model,r=self.model(scale);state=model.initSystem()
            for n,q in dict(height=10,pitch=.04,knee_l=-.1,chest=.05,tail_0=.08).items():
                model.getCoordinateSet().get(n).setValue(state,q)
            model.getCoordinateSet().get('knee_l').setSpeedValue(state,1)
            model.realizeAcceleration(state);observed.append(state.getUDot().to_numpy().copy())
        np.testing.assert_allclose(*observed,rtol=1e-7,atol=1e-6)
