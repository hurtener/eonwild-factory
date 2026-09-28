import numpy as np
from eonwild_motion.solve.moco_ground_support import recovery_reference


def test_roll_and_fold_precede_rise_without_widening_joint_limits():
    names=['pitch','yaw','roll','height','hip_l','knee_l','ankle_l']
    ix={n:i for i,n in enumerate(names)}
    rest=np.array([0.,0.,1.4,.55,.1,-1.2,.5])
    standing=np.array([0.,0.,0.,2.,.3,-.6,.8])
    bounds={'hip_l':(-.8,1.45),'knee_l':(-2.,-.16),'ankle_l':(.15,2.25)}
    policy=dict(fold_keys=[[0,0],[1,1],[6,1]],roll_keys=[[0,0],[1,0],[3,1],[6,1]],
                rise_keys=[[0,0],[3,0],[6,1]],crouch_radians={'hip_l':.65,'knee_l':-1.9,'ankle_l':1.0})
    np.testing.assert_allclose(recovery_reference(rest,standing,0,policy,ix,bounds),rest)
    crouch=recovery_reference(rest,standing,3,policy,ix,bounds)
    assert crouch[ix['height']]==rest[ix['height']]
    assert crouch[ix['roll']]==0
    assert crouch[ix['knee_l']] < rest[ix['knee_l']]
    np.testing.assert_allclose(recovery_reference(rest,standing,6,policy,ix,bounds),standing)
    for t in np.linspace(0,6,121):
        q=recovery_reference(rest,standing,t,policy,ix,bounds)
        for n,(lo,hi) in bounds.items():
            assert lo <= q[ix[n]] <= hi


def test_planted_stance_is_reached_by_the_rise_and_is_a_noop_otherwise():
    from eonwild_motion.solve.moco_ground_support import recovery_reference
    names=['pitch','yaw','roll','height','forward','lateral','knee_l']
    ix={n:i for i,n in enumerate(names)}
    rest=np.array([0.,0.,1.4,.55,10.,.5,-1.2]);standing=rest.copy();standing[[2,3,6]]=[0.,2.,-.6]
    policy=dict(fold_keys=[[0,0],[1,1]],roll_keys=[[0,0],[2,1]],rise_keys=[[0,0],[3,0],[6,1]])
    bounds={'knee_l':(-2.,-.16)}
    # Unshifted stance: forward/lateral never move (C61 behaviour preserved).
    for t in np.linspace(0,6,25):
        q=recovery_reference(rest,standing,t,policy,ix,bounds);assert q[ix['forward']]==10. and q[ix['lateral']]==.5
    moved=standing.copy();moved[ix['forward']]+=.4
    assert recovery_reference(rest,moved,3,policy,ix,bounds)[ix['forward']]==10.
    np.testing.assert_allclose(recovery_reference(rest,moved,6,policy,ix,bounds)[ix['forward']],10.4)


def test_balance_weight_ramps_smoothly_and_defaults_to_the_legacy_weight():
    from eonwild_motion.solve.moco_ground_support import balance_weight
    assert balance_weight(.5,{})==3.
    policy={'balance':{'weight':45.,'ramp_rise_fraction':.3}}
    values=[balance_weight(r,policy) for r in np.linspace(0,1,101)]
    assert values[0]==3. and values[-1]==45.
    assert all(b>=a for a,b in zip(values,values[1:]))
    assert max(np.diff(values)) < 5.


def test_skin_feedback_maps_regions_to_witness_groups_and_never_undercuts(tmp_path):
    import json,subprocess,sys
    times=[k/24 for k in range(49)]
    def row(t):
        pen=-.10 if abs(t-1.)<.05 else .05
        return dict(time_s=t,body_skin_floor_min_m=dict(thigh_l=.2,shin_l=pen,forelimb_r=pen/2,trunk=.3))
    (tmp_path/'r.json').write_text(json.dumps(dict(measurements=[row(t) for t in times])))
    subprocess.run([sys.executable,'tools/skin_clearance_feedback.py','--retarget',str(tmp_path/'r.json'),'--output',str(tmp_path/'f.json')],check=True,capture_output=True)
    out=json.loads((tmp_path/'f.json').read_text())['extra_clearance_m']
    assert set(out)=={'thigh_l','chest'}          # shin lifts thigh, forelimb lifts chest
    peak=out['thigh_l']['values_m'][24]
    assert abs(peak-.11)<1e-9                      # measured 10 cm + 1 cm margin, never less
    assert out['thigh_l']['values_m'][20]>0        # anticipated before the contact frame
    assert 'trunk' not in out                      # no penetration, no clearance
