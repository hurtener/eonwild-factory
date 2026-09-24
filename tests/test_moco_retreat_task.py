import numpy as np
from eonwild_motion.solve.moco_retreat_task import RetreatPlan,horizontal_balance


def plan():
 spec=dict(steps=4,step_scale_of_normal=.32,clearance_leg_lengths=.045,first_swing_s=3.,step_interval_s=1.8,
           swing_seconds=1.,release_seconds=.32,prepare_s=2.,settle_seconds=1.,duration_s=16.,
           release_pitch_rad=.1,recovery_pitch_rad=.04,recovery_digit_rad=-.12,adoption_seconds=.8)
 feet={s:dict(origin=[0.,.2,z],rotation=np.eye(3),digit=0.) for s,z in [('l',-.5),('r',.5)]}
 geometry={'sites':[{'center_local_m':[-.1,-.1,0.],'radius_m':.1}]}
 return RetreatPlan(spec,feet,geometry,1.37,2.5)


def test_loaded_rear_witness_is_fixed_and_retreat_closes_by_placement():
 p=plan()
 for side in ['l','r']:
  pos,rot,digit=p.foot(0.,side);np.testing.assert_allclose(pos,p.initial[side]['origin'])
  np.testing.assert_allclose(rot,np.eye(3));assert digit==0
 for e in p.events:
  witness=[]
  for t in np.linspace(e['lift']-.32,e['lift'],21):
   pos,R,_=p.foot(t,e['side']);witness.append(pos+R@p.pivot)
  np.testing.assert_allclose(witness,np.tile(witness[0],(len(witness),1)),atol=1e-12)
  for t in np.linspace(e['lift'],e['land'],21):assert p.weights(t)[0 if e['side']=='l' else 1]==0
 for side in ['l','r']:
  pos,rot,digit=p.foot(16,side)
  np.testing.assert_allclose(pos,np.array(p.initial[side]['origin'])+p.final_translation)
  np.testing.assert_allclose(rot,np.eye(3));assert digit==0


def test_swing_has_no_endpoint_velocity_corner_or_retraction():
 p=plan();h=1e-4
 for e in p.events:
  values=np.array([p.foot(t,e['side'])[0] for t in np.linspace(e['lift'],e['land'],201)])
  # Rear pivot can rotate the MTP slightly; its planned rear witness moves only backward.
  witness=np.array([p.foot(t,e['side'])[0]+p.foot(t,e['side'])[1]@p.pivot for t in np.linspace(e['lift'],e['land'],201)])
  assert np.max(np.diff(witness[:,0]))<=1e-12
  assert np.max(values[:,1])>.25
  for t in [e['lift'],e['land']]:
   velocity=(p.foot(t+h,e['side'])[0]-p.foot(t-h,e['side'])[0])/(2*h)
   assert np.linalg.norm(velocity)<1e-5


def test_horizontal_balance_obeys_reduced_equation_and_endpoint_state():
 t=np.linspace(0,6,601);z=np.c_[.2*np.sin(t),.1*np.cos(t)];h=2.
 c=horizontal_balance(t,z,h,[.03,.02],[-.3,.01])
 np.testing.assert_allclose(c[0],[.03,.02],atol=1e-12)
 np.testing.assert_allclose(c[-1],[-.3,.01],atol=1e-12)
 acceleration=np.diff(c,n=2,axis=0)/(.01**2)
 np.testing.assert_allclose(c[1:-1]-h/9.80665*acceleration,z[1:-1],atol=1e-11)


def test_distal_release_lifts_rear_keeps_front_material_anchor_and_digit_orientation():
 p=plan();spec=dict(p.specification,release_contact='distal')
 geometry={'toe_midpoint_m':[.2,-.1,0.], 'sites':[
     {'center_local_m':[-.1,-.1,0.],'radius_m':.1},
     {'center_local_m':[.3,0.,0.],'radius_m':.1,'distal':True}]}
 p=RetreatPlan(spec,p.initial,geometry,1.37,2.5)
 from scipy.spatial.transform import Rotation
 for e in p.events:
  anchors=[];rear=[]
  for t in np.linspace(e['lift']-spec['release_seconds'],e['lift'],21):
   position,R,digit=p.foot(t,e['side']);D=Rotation.from_rotvec([0,0,digit]).as_matrix()
   anchors.append(position+R@(p.midpoint+D@p.distal_center))
   rear.append((position+R@np.array([-.1,-.2,0.]))[1])
   np.testing.assert_allclose(R@D,np.eye(3),atol=1e-12)
  np.testing.assert_allclose(anchors,np.tile(anchors[0],(len(anchors),1)),atol=1e-12)
  assert rear[-1]>rear[0]+.02
