"""Check the defining turn constraint: loaded feet cannot spin or skate."""
import pytest
import numpy as np
from eonwild_motion.planning.directional_steps import DirectionalSteps

def planner():
    return DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,{'left':-.22,'right':.22},{'left':.1,'right':.1},[{'steps':n,'step_length_body_heights':d,'turn_degrees':a,'label':l} for n,d,a,l in [(6,.25,35,'gentle walking turn'),(4,.15,-40,'tight walking turn'),(6,0,75,'turn in place')]])

def test_support_is_stationary_and_heading_frozen():
    p=planner();previous=None
    for t in np.linspace(0,p.duration,4001):
        sample=p.sample(t)
        assert any(f['contact'] for f in sample['feet'].values())
        if previous:
            for s,f in sample['feet'].items():
                old=previous['feet'][s]
                if old['contact'] and f['contact']:
                    np.testing.assert_allclose(f['position'],old['position'],atol=1e-12)
                    assert abs(f['heading']-old['heading'])<1e-12
        previous=sample

def test_in_place_travels_around_support_and_alternates():
    p=planner();events=[e for e in p.events if e['label']=='turn in place']
    a,_=p.body(events[0]['start']);b,_=p.body(events[-1]['end'])
    assert np.linalg.norm(a-b)>.005
    assert np.linalg.norm(a-b)<p.height*.3
    assert all(x['side']!=y['side'] for x,y in zip(events,events[1:]))

def test_path_is_continuous_at_block_boundaries():
    p=planner()
    for e in p.events:
        for t in [e['start'],e['end']]:
            a,ya=p.body(t-1e-6);b,yb=p.body(t+1e-6)
            assert np.linalg.norm(a-b)<1e-5
            assert abs(ya-yb)<1e-5


def test_attention_leads_turns_and_settles():
    from eonwild_motion.solve.turn_attention import turn_look_yaw
    p=planner()
    before=p.blocks[0]['start']-.1
    assert p.body(before)[1]==0
    for block in p.blocks:
        t=block['start']+.2
        assert turn_look_yaw(p,t,1.6,32)*block['angle']>0
    assert abs(turn_look_yaw(p,p.duration,1.6,32))<1e-12
    assert max(abs(turn_look_yaw(p,t,1.6,32)) for t in np.linspace(0,p.duration,400))<np.radians(32)



def test_turn_body_does_not_pause_for_foot_commands():
    p=planner()
    b=next(b for b in p.blocks if b['stationary'])
    for t in np.linspace(b['start']+.1,b['end']-.1,60):
        assert p.body(t+.001)[1]>p.body(t-.001)[1]
    # The pelvis is already turning while the first foot is recovering.
    t=b['start']+.5*p.period
    assert p.body(t)[1]>b['heading']
    assert any(not f['contact'] for f in p.sample(t)['feet'].values())


def test_turn_heel_release_is_continuous_and_recovery_is_low():
    p=planner();b=next(b for b in p.blocks if b['stationary'])
    e=next(e for e in p.events if e['block'] is b);side=e['side']
    t=e['start']+.10*e['duration']
    a=p.sample(t-1e-6)['feet'][side];z=p.sample(t+1e-6)['feet'][side]
    assert abs(a['roll_degrees']-z['roll_degrees'])<1e-6
    max_height=max(p.sample(t)['feet'][side]['position'][1] for t in np.linspace(e['start'],e['end'],100))
    assert max_height-p.foot_heights[side]<=.037*p.height+1e-12


def test_turn_unloads_before_release_and_varies_inner_outer_steps():
    p=planner();b=next(b for b in p.blocks if b['stationary'])
    events=[e for e in p.events if e['block'] is b]
    assert not events[0]['inner'] and events[1]['inner']
    assert events[0]['duration'] > events[1]['duration']
    for e in events:
        t=e['start']+.10*e['duration']
        assert p.weight(t)*p.lanes[e['side']] < 0
        assert not p.sample(t+1e-6)['feet'][e['side']]['contact']
    # Changing recovery geometry must not create position jumps at release/landing.
    for e in events:
        for u in (.10,.90):
            t=e['start']+u*e['duration']
            a=p.sample(t-1e-6)['feet'][e['side']]['position']
            z=p.sample(t+1e-6)['feet'][e['side']]['position']
            assert np.linalg.norm(a-z)<1e-5


def test_turn_opens_with_outside_foot_in_both_directions():
    for angle in (100,-100):
        lanes={'left':-.36,'right':.36}
        p=DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,lanes,
            {'left':.1,'right':.1},[{'steps':4,'step_length_body_heights':0,
            'turn_degrees':angle,'label':'turn'}],turn_stance={'outside_opening_body_heights':.045})
        first=p.events[0]
        assert first['side']==('left' if angle>0 else 'right')
        assert not first['inner']
        h=first['targetHeading'];axis=p.lateral*np.cos(h)-p.forward*np.sin(h)
        assert abs((first['target']-p.origin)@axis) > abs(lanes[first['side']])+.08
        for e in p.events[-2:]:
            h=e['targetHeading'];axis=p.lateral*np.cos(h)-p.forward*np.sin(h)
            center,_=p.body(min(e['block']['end'],e['end']+.35*p.period))
            assert abs(abs((e['target']-p.origin-center)@axis)-.36)<1e-10


def test_walking_curve_carries_velocity_across_steps_and_prepares_heel_on_support():
    walking={'travel_ramp_fraction':.2,'heel_prepare_step_fraction':.35,
             'heel_roll_degrees':8.,'clearance_body_heights':.035,
             'recovery_outward_body_heights':.012}
    p=DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,
        {'left':-.24,'right':.24},{'left':0.,'right':0.},
        [{'steps':6,'step_length_body_heights':.25,'turn_degrees':35,'label':'curve'}],
        step_seconds=1.,walking=walking)
    block=p.blocks[0];speeds=[]
    for t in np.linspace(block['start']+1.3,block['end']-1.3,80):
        speeds.append(np.linalg.norm(p.body(t+.0001)[0]-p.body(t-.0001)[0])/.0002)
    assert max(speeds)-min(speeds)<1e-6
    e=p.events[2];side=e['side'];d=e['duration'];t=e['start']-.15*d
    before=p.sample(t)['feet'][side];later=p.sample(t+.02*d)['feet'][side]
    assert before['contact'] and later['contact']
    assert 0<before['roll_degrees']<later['roll_degrees']<8
    np.testing.assert_array_equal(before['position'],later['position'])
    for phase in (0.,.10,.90):
        t=e['start']+phase*d
        a=p.sample(t-1e-6)['feet'][side];b=p.sample(t+1e-6)['feet'][side]
        middle=p.sample(t)['feet'][side]['roll_degrees']
        left_rate=(middle-a['roll_degrees'])/1e-6
        right_rate=(b['roll_degrees']-middle)/1e-6
        assert abs(left_rate-right_rate)<.005
        assert np.linalg.norm(a['position']-b['position'])<1e-5


def test_walking_unload_keeps_heel_moving_through_release():
    walking={'travel_ramp_fraction':.2,'heel_prepare_step_fraction':.35,
             'heel_roll_degrees':22.,'clearance_body_heights':.14,
             'recovery_outward_body_heights':.012,'rounded_swing_peak_fraction':.42,
             'heel_peak_swing_fraction':.10,'heel_release_swing_fraction':.40}
    p=DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,
        {'left':-.24,'right':.24},{'left':0.,'right':0.},
        [{'steps':6,'step_length_body_heights':.25,'turn_degrees':35,'label':'curve'}],
        step_seconds=1.,walking=walking)
    e=p.events[2];side=e['side'];lift=e['start']+.1*e['duration'];eps=1e-5
    before=p.sample(lift-eps)['feet'][side];after=p.sample(lift+eps)['feet'][side]
    assert before['contact'] and not after['contact']
    assert (after['roll_degrees']-before['roll_degrees'])/(2*eps)>10
    np.testing.assert_allclose(before['position'],after['position'],atol=1e-8)
    # At the later heel maximum the free foot already moves upward, so the
    # entire leg cannot stop at the old common release boundary.
    peak=lift+.8*e['duration']*.10
    a=p.sample(peak-eps)['feet'][side];b=p.sample(peak+eps)['feet'][side]
    assert (b['position'][1]-a['position'][1])/(2*eps)>.1
    for t in (lift,peak,lift+.8*.40):
        a=p.sample(t-eps)['feet'][side];m=p.sample(t)['feet'][side];b=p.sample(t+eps)['feet'][side]
        assert abs((m['roll_degrees']-a['roll_degrees'])/eps-(b['roll_degrees']-m['roll_degrees'])/eps)<.02
    # All planted targets remain fixed; overlapping heel motion is articulation.
    previous=None
    for t in np.linspace(0,p.duration,1001):
        row=p.sample(t)
        assert any(f['contact'] for f in row['feet'].values())
        if previous:
            for side,f in row['feet'].items():
                old=previous['feet'][side]
                if old['contact'] and f['contact']:
                    np.testing.assert_allclose(f['position'],old['position'],atol=1e-12)
                    assert f['heading']==old['heading']
        previous=row


def test_compact_recovery_keeps_support_load_clock_aligned():
    from eonwild_motion.solve.turn_support import contact_loads
    from eonwild_motion.planning.walking_response import recovery_window
    walking={'travel_ramp_fraction':.2,'heel_prepare_step_fraction':.35,'heel_roll_degrees':22.,'clearance_body_heights':.14,'recovery_outward_body_heights':.012,'rounded_swing_peak_fraction':.42,'heel_peak_swing_fraction':.1,'heel_release_swing_fraction':.4,'recovery_seconds':.82,'heel_prepare_seconds':.43}
    p=DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,{'left':-.24,'right':.24},{'left':0.,'right':0.},[{'steps':4,'step_length_body_heights':.25,'turn_degrees':35,'label':'curve'}],step_seconds=2.,walking=walking)
    for e in p.events:
        a,b=recovery_window(e,walking)
        assert (b-a)*e['duration']==pytest.approx(.82)
        lift=e['start']+a*e['duration']
        before=p.sample(lift-1e-6)['feet'][e['side']];after=p.sample(lift+1e-6)['feet'][e['side']]
        assert before['contact'] and not after['contact']
        assert after['roll_degrees']>before['roll_degrees']
    for t in np.linspace(0,p.duration,500):
        row=p.sample(t);loads=contact_loads(p,t)
        for side,f in row['feet'].items():
            if not f['contact']: assert loads[side]==pytest.approx(0.)
