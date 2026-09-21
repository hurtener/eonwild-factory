"""Geometry-calibrated contact and transparent task-space priors for Moco.

These are engineering/animal-transfer priors, not measured dinosaur motion.
No previous animation is read and no knee-angle trajectory is prescribed.
"""
import math
from pathlib import Path
import numpy as np


def foot_geometry(admission, recipe):
    policy = recipe['calibrated_task']
    surfaces = admission.get('foot_surface')
    if not surfaces:
        raise ValueError('Calibrated Moco requires fresh admitted sole geometry')
    points = admission['points']
    length = sum(np.mean([[np.linalg.norm(np.array(points[f'{s}Leg.{i+1}'])-points[f'{s}Leg.{i}']) for i in range(3)] for s in ('left','right')], axis=0))
    vertices = np.concatenate([v['vertices_m'] for v in surfaces.values()])
    mid = np.mean([v['toe_midpoint_m'] for v in surfaces.values()], axis=0); mid[2] = 0
    sites = []
    radius = policy['pad_radius_leg_lengths'] * length
    xs = np.linspace(float(np.quantile(vertices[:,0], .03)), float(np.quantile(vertices[:,0], .97)), 5)
    for i, x in enumerate(xs):
        subset = vertices[abs(vertices[:,0]-x) < .12*length]
        bottom = float(subset[:,1].min()) - policy['pad_envelope_margin_m']
        position = np.array([x, bottom+radius, 0.])
        distal = x > mid[0]
        sites.append(dict(name=f'pad{i}', distal=bool(distal),
                          center_local_m=(position-mid if distal else position).tolist(), radius_m=float(radius)))
    return dict(toe_midpoint_m=mid.tolist(), sites=sites,
                sole_depth_m=float(-vertices[:,1].min()),
                classification='Spheres fit to admitted sole samples; radius/compliance are engineering priors')


def rot(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*x*(10+x*(-15+6*x))


def task_sample(admission, metadata, recipe, t):
    p=recipe['calibrated_task']; step=admission['step_length_m']; speed=admission['preferred_speed_mps']
    T=2*step/speed; duty=p['duty_factor']; L=sum(metadata['segment_lengths_m'])
    reference={}; poses={}; phase=t/T
    # Bounded task guidance: same speed/stride, soft foot recovery and approach.
    # Root and all joint motion remain free variables of the dynamics solve.
    for suffix, offset in [('l',0),('r',.5)]:
        continuous=phase+offset; cycle=math.floor(continuous); ph=continuous-cycle
        z=admission['points'][('left' if suffix=='l' else 'right')+'Leg.0'][2]
        anchor=(cycle-offset)*speed*T + speed*T*duty*.5 + p['catch_bias_leg_lengths']*L
        swing=max(0.,(ph-duty)/(1-duty))
        if ph < duty:
            u=ph/duty
            ramp=float(np.clip((u-.40)/.60,0,1))
            peel=(6*ramp**3-8*ramp**4+3*ramp**5) if p.get('continuous_release') else smooth(ramp)
            angle=-p['toe_off_pitch_radians']*float(peel)
            # Roll through the distal pad while the MTP and proximal toes rise.
            toe_angle=angle*(1-float(smooth((u-.35)/.5)))
            pivot=np.array(metadata['foot_geometry']['toe_midpoint_m'])
            front=np.array(metadata['foot_geometry']['sites'][-1]['center_local_m'])
            front[1]-=metadata['foot_geometry']['sites'][-1]['radius_m']
            distal_origin=np.array([anchor,0,z])-rot(toe_angle)@front
            mtp=distal_origin-rot(angle)@pivot
        else:
            # A quintic position joins stationary support; the broad arc clears
            # the real sole. The optimizer is allowed to change its details.
            x0=anchor; x1=anchor+speed*T
            angle=-p['toe_off_pitch_radians']*(1-float(smooth(swing)))
            if p.get('continuous_release'):
                # Continue the heel's angular velocity through release. The
                # quintic tangent basis has zero displacement/velocity at catch.
                release_rate=-p['toe_off_pitch_radians']/(.60*duty*T)
                tangent=swing-6*swing**3+8*swing**4-3*swing**5
                angle+=release_rate*(1-duty)*T*tangent
            toe_angle=-p['toe_off_pitch_radians']*float(smooth(swing/.22))*(1-float(smooth((swing-.45)/.55)))
            pivot=np.array(metadata['foot_geometry']['toe_midpoint_m'])
            front=np.array(metadata['foot_geometry']['sites'][-1]['center_local_m'])
            front[1]-=metadata['foot_geometry']['sites'][-1]['radius_m']
            lift=p['recovery_clearance_leg_lengths']*L*np.sin(np.pi*swing)**2
            distal_origin=np.array([x0+(x1-x0)*smooth(swing),lift,z])-rot(toe_angle)@front
            mtp=distal_origin-rot(angle)@pivot
        reference['/bodyset/toe_'+suffix]=mtp
        reference['/bodyset/digit_'+suffix]=distal_origin
        reference['/tip_digit_'+suffix]=distal_origin+rot(toe_angle)@np.array(metadata['segments']['digit_'+suffix]['extent_local_m'])
        poses[suffix]=(mtp,angle,toe_angle-angle)
    return reference, poses


def add_tracking(problem, admission, metadata, recipe):
    import opensim as o
    task=recipe['calibrated_task']; duration=admission['step_length_m']/admission['preferred_speed_mps']
    times=np.linspace(0,duration,121)
    paths=list(task_sample(admission,metadata,recipe,0)[0])
    table=o.TimeSeriesTableVec3(); labels=o.StdVectorString()
    for path in paths: labels.append(path)
    table.setColumnLabels(labels)
    for t in times:
        values,_=task_sample(admission,metadata,recipe,t); row=o.RowVectorVec3(len(paths))
        for i,path in enumerate(paths):row[i]=o.Vec3(*values[path])
        table.appendRow(float(t),row)
    goal=o.MocoTranslationTrackingGoal('foot_clearance_and_support_task',task['foot_tracking_weight'])
    if 'reference_directory' in metadata:
        path=Path(metadata['reference_directory'])/'foot-task-reference.sto'
        o.STOFileAdapterVec3.write(table,str(path));goal.setTranslationReferenceFile(str(path))
    else: goal.setTranslationReference(table)
    goal.setFramePaths(labels); problem.addGoal(goal)
    # Broad supported posture, explicitly authored. This is a soft regularizer;
    # it does not prescribe the running knee, ankle or body response waveform.
    states=o.TimeSeriesTable(); names=o.StdVectorString()
    values={'pitch':task['trunk_pitch_radians'],'height':task['hip_height_leg_lengths']*sum(metadata['segment_lengths_m'])+metadata['foot_geometry']['sole_depth_m'],
            'chest':0.,'neck':task['neck_rest_radians'],'tail_proximal':task['tail_proximal_rest_radians'],
            'tail_distal':task['tail_distal_rest_radians']}
    paths=[]
    for key in values:
        paths.append(f'/jointset/{"root" if key in ("pitch","height") else key}/{key}/value');names.append(paths[-1])
    states.setColumnLabels(names)
    states.addTableMetaDataString('inDegrees','no')
    for t in times:
        row=o.RowVector(len(values))
        for i,v in enumerate(values.values()):row[i]=v
        states.appendRow(float(t),row)
    posture=o.MocoStateTrackingGoal('supported_axial_posture',task['posture_tracking_weight'])
    if 'reference_directory' in metadata:
        path=Path(metadata['reference_directory'])/'posture-task-reference.sto'
        o.STOFileAdapter.write(states,str(path));posture.setReference(o.TableProcessor(str(path)))
    else: posture.setReference(o.TableProcessor(states))
    posture.setAllowUnusedReferences(True)
    problem.addGoal(posture)


def seed(admission, metadata, recipe, times):
    L1,L2,L3=metadata['segment_lengths_m']; p=recipe['calibrated_task']; height=p['hip_height_leg_lengths']*(L1+L2+L3)+metadata['foot_geometry']['sole_depth_m']
    pitch=p['trunk_pitch_radians']; q={name:[] for name in ['pitch','forward','height',*metadata['coordinates']]}
    for t in times:
        _,feet=task_sample(admission,metadata,recipe,float(t)); row=dict(pitch=pitch,forward=t*admission['preferred_speed_mps'],height=height,
            chest=0.,neck=p['neck_rest_radians'],tail_proximal=p['tail_proximal_rest_radians'],tail_distal=p['tail_distal_rest_radians'])
        for side,(foot,angle,digit) in feet.items():
            # Three-link seed only; its knee trajectory is not an objective.
            swing=((t/(2*admission['step_length_m']/admission['preferred_speed_mps'])+(0 if side=='l' else .5))%1)
            theta=.2+.95*np.sin(np.pi*np.clip((swing-p['duty_factor'])/(1-p['duty_factor']),0,1))**2
            dx=foot[0]-row['forward']-L3*np.sin(theta);dy=foot[1]-height+L3*np.cos(theta)
            d=np.hypot(dx,dy); knee=-np.arccos(np.clip((d*d-L1*L1-L2*L2)/(2*L1*L2),-.98,.97))
            hip=np.arctan2(dx,-dy)+np.arccos(np.clip((L1*L1+d*d-L2*L2)/(2*L1*d),-.99,.99))
            row.update({f'hip_{side}':hip-pitch,f'knee_{side}':knee,f'ankle_{side}':theta-hip-knee,
                        f'mtp_{side}':angle-theta,f'digit_{side}':digit})
        for name in q:q[name].append(row[name])
    return {k:np.array(v) for k,v in q.items()}
