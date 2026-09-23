"""Geometry-calibrated contact and transparent task-space priors for Moco.

These are engineering/animal-transfer priors, not measured dinosaur motion.
No previous animation is read and no knee-angle trajectory is prescribed.
"""
import math
import copy
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
    if recipe.get('spatial'):
        # Symmetric transverse pads support roll without twisting the knee.
        # Width comes from the admitted sole; both feet use the averaged envelope.
        width=float(np.quantile(np.abs(vertices[:,2]),.70))
        for index in (1,3):
            original=sites[index]
            original['stiffness_share']=.5
            original['center_local_m'][2]=-width*.65
            other=dict(original, name=original['name']+'_outer',center_local_m=list(original['center_local_m']))
            other['center_local_m'][2]=width*.65
            sites.append(other)
        # Preserve the front-most reference station for the peel task.
        sites.sort(key=lambda v:v['center_local_m'][0]+(mid[0] if v['distal'] else 0))
    per_side = {}
    if policy.get('surface_edge_pads'):
        # Geometry-owned lateral sole coverage. Preserve total nominal stiffness;
        # this redistributes contact samples, not muscle/force capacity.
        for suffix, side in [('l', 'left'), ('r', 'right')]:
            surface = np.asarray(surfaces[side]['vertices_m'])
            fitted = copy.deepcopy(sites)
            for i, x in enumerate(xs):
                band = surface[abs(surface[:, 0] - x) < .12 * length]
                for edge, fraction in [('inner', .12), ('outer', .88)]:
                    z = np.quantile(band[:, 2], fraction)
                    edge_band = band[band[:, 2] <= z] if fraction < .5 else band[band[:, 2] >= z]
                    point = edge_band[np.argmin(edge_band[:, 1])].copy()
                    point[1] += radius - policy['pad_envelope_margin_m']
                    distal = bool(point[0] > mid[0])
                    fitted.append(dict(name=f'edge{i}_{edge}', distal=distal,
                        center_local_m=(point-mid if distal else point).tolist(),
                        radius_m=float(radius), stiffness_share=.5))
            total = sum(v.get('stiffness_share', 1.) for v in fitted)
            original = sum(v.get('stiffness_share', 1.) for v in sites)
            for v in fitted:
                v['stiffness_share'] = v.get('stiffness_share', 1.) * original / total
            per_side[suffix] = fitted
    return dict(toe_midpoint_m=mid.tolist(), sites=sites, sites_by_side=per_side,
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
        z*=recipe.get('spatial',{}).get('foot_track_hip_width_ratio',1.)
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
    if recipe.get('spatial'):
        values={'pitch':values['pitch'],'height':values['height'],
                **recipe['spatial']['posture_reference']}
    paths=[]
    for key in values:
        joint='root' if key in ('pitch','height','yaw','roll','lateral') else metadata['coordinates'][key].get('joint',key)
        paths.append(f'/jointset/{joint}/{key}/value');names.append(paths[-1])
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
    if recipe.get('spatial'):
        reference=o.TimeSeriesTable();labels=o.StdVectorString()
        for key in ('pitch','yaw','roll','forward','height','lateral',*metadata['coordinates']):
            joint=metadata['coordinates'].get(key,{}).get('joint','root')
            labels.append(f'/jointset/{joint}/{key}/value')
        reference.setColumnLabels(labels);reference.addTableMetaDataString('inDegrees','no')
        for t in times:
            row=o.RowVector(labels.size(),0);row[0]=recipe.get('attention',{}).get('nose_pitch_radians',.10)
            reference.appendRow(float(t),row)
        path=Path(metadata['reference_directory'])/'head-direction-reference.sto'
        o.STOFileAdapter.write(reference,str(path))
        gaze=o.MocoOrientationTrackingGoal('stable_forward_attention',recipe.get('attention',{}).get('orientation_tracking_weight',recipe['spatial']['gaze_weight']))
        frames=o.StdVectorString();frames.append('/bodyset/head')
        gaze.setFramePaths(frames);gaze.setStatesReference(o.TableProcessor(str(path)));problem.addGoal(gaze)
        attention=recipe.get('attention',{})
        if metadata.get('attention_reference_offset_m') is not None:
            if not metadata.get('attention_frame'):raise ValueError('Focused running needs admitted nose geometry')
            reference=o.TimeSeriesTableVec3();labels=o.StdVectorString();labels.append(metadata['attention_frame'])
            reference.setColumnLabels(labels)
            for t in times:
                target=np.array(metadata['attention_reference_offset_m'])+[admission['preferred_speed_mps']*t,0,0]
                row=o.RowVectorVec3(1);row[0]=o.Vec3(*target);reference.appendRow(float(t),row)
            path=Path(metadata['reference_directory'])/'nose-position-reference.sto'
            o.STOFileAdapterVec3.write(reference,str(path))
            position=o.MocoTranslationTrackingGoal('focused_nose_position',attention['position_tracking_weight'])
            position.setFramePaths(labels);position.setTranslationReferenceFile(str(path));problem.addGoal(position)
    for region in recipe.get('coordination',{}).get('vertical_regions',[]):
        name=region['body'];target=metadata['vertical_region_reference_m'][name]
        goal=o.MocoOutputTrackingGoal('supported_vertical_'+name,float(region.get('moco_tracking_weight',region['weight'])))
        goal.setOutputPath('/bodyset/'+name+'|position');goal.setOutputIndex(1)
        goal.setTrackingFunction(o.Constant(target));goal.setExponent(2);problem.addGoal(goal)
    if task.get('support_force_weight'):
        add_support_task(problem, admission, metadata, recipe, times)


def admit_attention_reference(model, metadata, warm_start, speed, vertical_regions=()):
    """A constant task-space aim from the warm physical trajectory, not a joint schedule."""
    import opensim as o
    if not metadata.get('attention_frame'):raise ValueError('Focused running needs admitted nose geometry')
    trajectory=o.MocoTrajectory(str(warm_start));names=list(trajectory.getStateNames())
    matrix=trajectory.getStatesTrajectoryMat();state_names=model.getStateVariableNames()
    valid={state_names.get(i) for i in range(state_names.getSize())}
    state=model.initSystem();nose=o.PhysicalOffsetFrame.safeDownCast(model.getComponent(metadata['attention_frame']))
    offsets=[]
    regions={p['body']:model.getBodySet().get(p['body']) for p in vertical_regions}
    heights={n:[] for n in regions}
    for i,t in enumerate(trajectory.getTimeMat()):
        for j,name in enumerate(names):
            if name in valid and name.endswith('/value'):model.setStateVariableValue(state,name,float(matrix[i,j]))
        model.realizePosition(state)
        offsets.append(nose.getPositionInGround(state).to_numpy()-[speed*t,0,0])
        for n,b in regions.items():heights[n].append(b.getPositionInGround(state).get(1))
    target=np.mean(offsets,axis=0);target[2]=0.
    metadata['vertical_region_reference_m']={n:float(np.mean(v)) for n,v in heights.items()}
    metadata['attention_reference_offset_m']=target.tolist()
    metadata['attention_reference_provenance']='Mean skull-fixed nose position relative to constant travel in the saved physical warm start; lateral aim centered by symmetry. Soft task, not prescribed neck angles.'


def add_continuation_tracking(problem, trajectory_path, metadata, weight, full_body=False):
    """Temporary numerical continuation around a prior physical solution.

    The default regularizes existing sagittal leg states. Optional full-body
    continuation retains a coordinated spatial initializer while all states
    remain optimization variables. This is not an unguided predictive solve.
    """
    import opensim as o
    source=o.MocoTrajectory(str(trajectory_path));names=list(source.getStateNames())
    keep=[n for n in names if n.startswith('/jointset/') and (full_body or (
        n.split('/')[-2].startswith(('hip_','knee_','ankle_','mtp_','digit_')) and not n.split('/')[-2].endswith(('_yaw','_roll'))))]
    table=o.TimeSeriesTable();labels=o.StdVectorString()
    for name in keep:labels.append(name)
    table.setColumnLabels(labels);table.addTableMetaDataString('inDegrees','no')
    matrix=source.getStatesTrajectoryMat()
    for i,t in enumerate(source.getTimeMat()):
        row=o.RowVector(len(keep))
        for j,name in enumerate(keep):row[j]=float(matrix[i,names.index(name)])
        table.appendRow(float(t),row)
    path=Path(metadata['reference_directory'])/'continuation-reference.sto'
    o.STOFileAdapter.write(table,str(path))
    goal=o.MocoStateTrackingGoal('coordinated_physics_continuation' if full_body else 'sagittal_physics_continuation',float(weight))
    goal.setReference(o.TableProcessor(str(path)))
    for name in keep:goal.setWeightForState(name,.02 if name.endswith('/speed') else 1.)
    problem.addGoal(goal)


def add_foot_continuation(problem,model,trajectory_path,metadata,weight):
    """Retain warm-start foot placement while coordinates remain free to balance."""
    import opensim as o
    source=o.MocoTrajectory(str(trajectory_path));names=list(source.getStateNames())
    values=source.getStatesTrajectoryMat();state=model.initSystem()
    paths=['/bodyset/toe_l','/bodyset/toe_r']
    bodies=[model.getBodySet().get(path.rsplit('/',1)[-1]) for path in paths]
    table=o.TimeSeriesTableVec3();labels=o.StdVectorString()
    for path in paths:labels.append(path)
    table.setColumnLabels(labels)
    for i,t in enumerate(source.getTimeMat()):
        for j,name in enumerate(names):
            if name.endswith('/value'):model.setStateVariableValue(state,name,float(values[i,j]))
        model.realizePosition(state);row=o.RowVectorVec3(len(paths))
        for j,body in enumerate(bodies):row[j]=body.getPositionInGround(state)
        table.appendRow(float(t),row)
    path=Path(metadata['reference_directory'])/'continuation-foot-reference.sto'
    o.STOFileAdapterVec3.write(table,str(path))
    goal=o.MocoTranslationTrackingGoal('coordinated_foot_placement',float(weight))
    goal.setFramePaths(labels);goal.setTranslationReferenceFile(str(path));problem.addGoal(goal)


def add_support_task(problem, admission, metadata, recipe, times):
    """Soft, impulse-normalized single-lobe loading prior; not measured GRF.

    ExternalLoads are reference data for a goal ONLY, never model forces.
    Horizontal/lateral forces remain outcomes of contact and whole-body balance.
    """
    import opensim as o
    policy=recipe['calibrated_task']; duty=policy['duty_factor']
    period=2*admission['step_length_m']/admission['preferred_speed_mps']
    bw=metadata['mass_kg']*9.80665
    table=o.TimeSeriesTable(); labels=o.StdVectorString()
    for side in ('l','r'):
        for axis in 'xyz': labels.append('support_'+side+'_'+axis)
    table.setColumnLabels(labels)
    for t in times:
        row=o.RowVector(6,0)
        for i,offset in enumerate((0,.5)):
            phase=(t/period+offset)%1
            row[i*3+1]=bw/duty*np.sin(np.pi*phase/duty)**2 if phase<duty else 0
        table.appendRow(float(t),row)
    directory=Path(metadata['reference_directory'])
    data_path=directory/'support-force-prior.sto'
    o.STOFileAdapter.write(table,str(data_path))
    loads=o.ExternalLoads(); loads.setDataFileName(str(data_path))
    # Moco divides squared force error by BW once. Divide once more here
    # so the configured weight multiplies dimensionless squared BW error.
    goal=o.MocoContactTrackingGoal('continuous_weight_receiving',policy['support_force_weight']/bw)
    for side in ('l','r'):
        force=o.ExternalForce();force.setName('support_'+side)
        force.set_applied_to_body('toe_'+side)
        force.set_force_expressed_in_body('ground')
        force.set_force_identifier('support_'+side+'_')
        loads.cloneAndAppend(force)
        paths=o.StdVectorString()
        for contact in metadata['contacts']:
            if contact['force'].endswith('_'+side):paths.append('/forceset/'+contact['force'])
        group=o.MocoContactTrackingGoalGroup(paths,'support_'+side)
        group.append_alternative_frame_paths('/bodyset/digit_'+side)
        goal.addContactGroup(group)
    loads_path=directory/'support-force-prior.xml';loads.printToXML(str(loads_path))
    goal.setExternalLoadsFile(str(loads_path))
    goal.setProjection('vector');goal.setProjectionVector(o.Vec3(0,1,0))
    problem.addGoal(goal)


def seed(admission, metadata, recipe, times):
    L1,L2,L3=metadata['segment_lengths_m']; p=recipe['calibrated_task']; height=p['hip_height_leg_lengths']*(L1+L2+L3)+metadata['foot_geometry']['sole_depth_m']
    pitch=p['trunk_pitch_radians']; q={name:[] for name in ['pitch','forward','height',*(['yaw','roll','lateral'] if recipe.get('spatial') else []),*metadata['coordinates']]}
    for t in times:
        _,feet=task_sample(admission,metadata,recipe,float(t)); row=dict(pitch=pitch,forward=t*admission['preferred_speed_mps'],height=height,
            chest=0.,neck=p['neck_rest_radians'],tail_proximal=p['tail_proximal_rest_radians'],tail_distal=p['tail_distal_rest_radians'])
        if recipe.get('spatial'):
            row={**dict.fromkeys(q,0.),**row,**recipe['spatial']['posture_reference']}
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
