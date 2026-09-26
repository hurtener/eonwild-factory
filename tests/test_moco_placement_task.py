import numpy as np
from eonwild_motion.solve.moco_placement_task import PlacementPlan


def make(family):
    spec=dict(family=family,steps=4,step_scale_of_normal=.32,clearance_leg_lengths=.045,
        first_swing_s=2.1,step_interval_s=1.05,swing_seconds=.7,release_seconds=.2,
        prepare_s=1.2,settle_seconds=.5,duration_s=12.,release_pitch_rad=.1,
        recovery_pitch_rad=.04,recovery_digit_rad=-.12,adoption_seconds=.5,
        release_contact='distal',heading_degrees=60.,stance_width_scale=1.1,
        lateral_distance_leg_lengths=.15,attention_lookahead_s=1.5,
        attention_keys=[[0,0],[2,0],[4,35],[7,-35],[9,0]])
    feet={s:dict(origin=[0.,.2,z],rotation=np.eye(3),digit=0.) for s,z in [('l',-.5),('r',.5)]}
    geo=dict(toe_midpoint_m=[.2,-.1,0.],sites=[dict(center_local_m=[-.1,-.1,0.],radius_m=.1),dict(center_local_m=[.3,0.,0.],radius_m=.1,distal=True)])
    return PlacementPlan(spec,feet,geo,1.3,2.5)


def test_pivot_reorients_only_unloaded_feet_and_finishes_wider():
    p=make('pivot')
    assert p.events[0]['side']=='r'
    for e in p.events:
        rotations=[p.foot(t,e['side'])[1] for t in np.linspace(e['lift']-.2,e['lift'],9)]
        # Peel is sagittal, so world heading of the toe forward axis stays fixed.
        headings=[np.arctan2(-r[2,0],r[0,0]) for r in rotations]
        assert np.ptp(headings)<1e-12
        assert p.weights((e['lift']+e['land'])/2)[0 if e['side']=='l' else 1]==0
    final=[p.foot(12,s)[0] for s in ['l','r']]
    np.testing.assert_allclose(np.linalg.norm(final[0]-final[1]),1.1,atol=1e-10)
    assert abs(p.heading(12)-np.pi/3)<1e-12


def test_lateral_outside_opens_before_inside_closes_no_crossing():
    p=make('lateral');assert p.events[0]['side']=='r'
    for t in np.linspace(0,12,1001):assert p.foot(t,'r')[0][2]>p.foot(t,'l')[0][2]
    for side in ['l','r']:
        np.testing.assert_allclose(p.foot(12,side)[0],np.array(p.initial[side]['origin'])+[0,0,.75])


def test_alert_keeps_both_feet_and_has_no_spurious_contact_event():
    p=make('alert');assert not p.events
    for t in np.linspace(0,12,101):
        np.testing.assert_allclose(p.weights(t),[.5,.5])
        for side in ['l','r']:np.testing.assert_allclose(p.foot(t,side)[0],p.initial[side]['origin'])
    assert p.attention_degrees(4)==35 and p.attention_degrees(7)==-35
