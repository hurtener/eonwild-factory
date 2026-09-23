"""Optional loaded-posture support and admitted physical tail links.

Effective tonic running impedance, not reconstructed muscle co-contraction.
All support acts internally; the free root receives no spring or motor.
"""
import numpy as np


def add_tail_chain(model,metadata,points,fractions,capacities,length,body,pin,trunk,recipe):
    import opensim as o
    policy=recipe['spatial'];settings=recipe['bracing']['tail']
    roles=sorted((k for k in points if k.startswith('tail.')),key=lambda k:int(k.split('.')[-1]))
    positions=np.array([points[r] for r in roles]);positions[:,2]=0
    # A physical link must have its own admitted skin joint. Resampling points
    # and choosing nearest roles silently drives the same bone several times.
    target_links = int(settings.get('target_links', len(roles)-1))
    if target_links != len(roles)-1:
        raise ValueError(f'Tail requests {target_links} links but source admits {len(roles)-1}; '
                         'subdivide and re-admit the source skin before building the model')
    extents=np.diff(positions,axis=0);lengths=np.linalg.norm(extents,axis=1)
    if len(lengths)<2 or np.any(lengths<1e-5):raise ValueError('Tail needs a nondegenerate admitted chain')
    edges=np.r_[0,np.cumsum(lengths)];s=(edges[:-1]+edges[1:])/(2*edges[-1])
    radii=np.interp(s,settings['radius_stations'],settings['radius_leg_lengths'])*length
    # Cylinder volume establishes a smooth taper; normalize to admitted total mass.
    volume=radii*radii*lengths;shares=volume/volume.sum()
    total=fractions['tail_proximal']+fractions['tail_distal']
    parent=trunk;parent_origin=np.zeros(3);segments=[]
    for i,(role,extent,ell,radius,share) in enumerate(zip(roles,extents,lengths,radii,shares)):
        name='tail_'+str(i);origin=positions[i]
        policy.setdefault('posture_reference',{})[name]=settings['base_loaded_pitch_rad'] if i==0 else 0.
        policy['posture_reference'][name+'_yaw']=0.
        # Two-component bending stiffness: bone/disc (steep taper) plus soft
        # tissue (muscle/ligament, shallow taper). This keeps proximal rigidity
        # while preventing the distal chain from becoming a free pendulum.
        radius_ratio=radius/radii[0]
        bone_exp=settings.get('bone_stiffness_taper_exponent',3.0)
        soft_exp=settings.get('soft_tissue_stiffness_taper_exponent',1.0)
        bone_frac=settings.get('bone_stiffness_fraction',0.5)
        shape=bone_frac*radius_ratio**bone_exp+(1.-bone_frac)*radius_ratio**soft_exp
        # Distance-dependent damping ratio: proximal slightly underdamped for
        # elastic energy storage, distal critically damped so it settles.
        zeta_prox=settings.get('damping_ratio_proximal',0.5)
        zeta_dist=settings.get('damping_ratio_distal',1.0)
        zeta_i=zeta_prox+(zeta_dist-zeta_prox)*float(s[i])
        for suffix,factor in [('',settings['pitch_EI_BW_L2']),('_yaw',settings['yaw_EI_BW_L2'])]:
            recipe.setdefault('passive_support',{})[name+suffix]=dict(
                stiffness_BW_leg_length=factor*length/ell*shape,
                damping_BW_leg_length_s=0.,rest_radians=0.,damping_ratio=zeta_i)
        policy['joint_axes'][name]={'yaw':{'bounds':[-.20,.20],'capacity_ratio':.8}}
        b=body(name,total*share,extent*.5,extent,radius)
        # Engineering radius-dependent torque-capacity envelope with a floor.
        # Its tunable exponent is not identified PCSA or measured muscle torque.
        cap_exp=settings.get('capacity_taper_exponent',1.5)
        cap_floor=settings.get('capacity_floor_ratio',0.667)
        cap_shape=radius_ratio**cap_exp
        pin(name,parent,origin-parent_origin,b,[-.14,.14],
            capacities['tail_proximal']*max(cap_floor,cap_shape*float(shares[i:].sum())))
        metadata['axial_bindings'].append(dict(body=name,role=role))
        frame=o.PhysicalOffsetFrame('tip_'+name,b,o.Transform(o.Vec3(*map(float,extent))))
        model.addComponent(frame)
        metadata['clearance_frames'].append(dict(path='/tip_'+name,minimum_height_m=(.22 if i==len(lengths)-1 else .08)*length))
        segments.append(dict(body=name,role=role,end_role=roles[i+1],length_m=float(ell),
                             arc_start_m=float(edges[i]),arc_end_m=float(edges[i+1]),radius_m=float(radius)))
        parent=b;parent_origin=origin
    metadata['tail_chain']=segments;metadata['tail_terminal_body']=segments[-1]['body']
    metadata['tail_subdivision']=dict(links=len(lengths),nodes=len(roles),mass_kg=metadata['mass_kg']*total,
        stiffness_law='Angular stiffness EI/segment_length; radius taper; shared physical chain, no render-only smoothing')


def calibrate_bracing(model,metadata,recipe):
    import opensim as o
    policy=recipe['bracing'];L=sum(metadata['segment_lengths_m']);bw=metadata['mass_kg']*9.80665
    state=model.initSystem();coordinates=model.updCoordinateSet();indices={}
    for c in coordinates:
        state.updU().setToZero();c.setSpeedValue(state,1)
        indices[c.getName()]=int(np.argmax(np.abs(state.getU().to_numpy())))
    state.updU().setToZero();coordinates.get('height').setValue(state,10.)
    coordinates.get('pitch').setValue(state,policy['loaded_root_pitch_rad'])
    loaded=dict(policy['loaded_coordinates_rad'])
    for part in metadata.get('tail_chain',[]):
        loaded[part['body']]=policy['tail']['base_loaded_pitch_rad'] if part['body']=='tail_0' else 0.
        loaded[part['body']+'_yaw']=0.
    for n,v in loaded.items():coordinates.get(n).setValue(state,float(v))
    model.realizeVelocity(state)
    # Remove existing spring biases only for the calibrated coordinates to
    # measure the holding torque. Contact is absent at this calibration height.
    selected={n for n in loaded if n in metadata.get('passive_support',{})}
    for n in selected:
        spring=o.SpringGeneralizedForce.safeDownCast(model.updForceSet().get('passive_'+n))
        spring.set_stiffness(0.);spring.set_viscosity(0.)
    model.finalizeConnections();state=model.initSystem()
    coordinates.get('height').setValue(state,10.);coordinates.get('pitch').setValue(state,policy['loaded_root_pitch_rad'])
    for n,v in loaded.items():coordinates.get(n).setValue(state,float(v))
    model.realizeVelocity(state)
    demand=o.InverseDynamicsSolver(model).solve(state,o.Vector(state.getNU(),0)).to_numpy()
    mass=o.Matrix();model.getMatterSubsystem().calcM(state,mass);mass=mass.to_numpy()
    loaded_tail={}
    for part in metadata.get('tail_chain',[]):
        frame=o.PhysicalFrame.safeDownCast(model.getComponent('/tip_'+part['body']))
        loaded_tail[part['body']]=float(frame.getPositionInGround(state).get(1)-10.)
    results={}
    for n in sorted(selected):
        original=metadata['passive_support'][n]
        inertia=float(mass[indices[n],indices[n]])
        region=policy['tail'] if n.startswith('tail_') else policy['regions'][n]
        if n.startswith('tail_'):
            stiffness=original['stiffness_BW_leg_length']*bw*L
            zeta=original.get('damping_ratio',region['damping_ratio'])
        else:
            stiffness=inertia*(2*np.pi*region['frequency_hz'])**2
            zeta=region['damping_ratio']
        damping=2*zeta*np.sqrt(stiffness*inertia)
        support_fraction=region.get('gravity_support_fraction',0.) if not n.endswith(('_yaw','_roll')) else 0.
        preload=float(demand[indices[n]])*support_fraction
        rest=loaded[n]+preload/stiffness
        spring=o.SpringGeneralizedForce.safeDownCast(model.updForceSet().get('passive_'+n))
        spring.set_stiffness(stiffness);spring.set_viscosity(damping);spring.set_rest_length(rest)
        results[n]=dict(loaded_angle_rad=loaded[n],holding_demand_Nm=float(demand[indices[n]]),
            supported_fraction=support_fraction,stiffness_Nm_per_rad=stiffness,damping_Nms_per_rad=damping,
            reflected_inertia_kg_m2=inertia,rest_angle_rad=rest)
    metadata['bracing']=dict(classification=policy['classification'],coordinates=results,
        loaded_tail_end_heights_relative_root_m=loaded_tail,
        root_support='None; all bracing forces are internal joint torques',
        calibration='Static loaded pose without contact; damping from locked-neighbour reflected inertia approximation',
        physiology='Constant effective running engagement, not a muscle or phase-dependent co-contraction model')
    model.finalizeConnections()


def supported_initialization(problem,baseline,q,times):
    """Flatten rejected axial seed motion while retaining each world foot pose.

    Numerical initialization only. Subsequent optimization frees every
    coordinate and recomputes contact, loads and required torque.
    """
    from scipy.optimize import least_squares
    from scipy.spatial.transform import Rotation
    p=problem;settings=p.policy['initialization_body'];source=q.copy()
    for name,setting in settings.items():
        i=p.index[name]
        center=setting['center_leg_length']*p.L if 'center_leg_length' in setting else setting['center']
        q[:,i]=center+setting['amplitude_scale']*(q[:,i]-q[:,i].mean())
    for part in p.metadata.get('tail_chain',[]):
        i=p.index[part['body']]
        center=p.recipe['bracing']['tail']['base_loaded_pitch_rad'] if part['body']=='tail_0' else 0.
        q[:,i]=center+.15*(source[:,i]-source[:,i].mean())
    # The full stride has bilateral reflection; source row rotations are in
    # admitted world coordinates, not the artist's local bone axes.
    rows=baseline['frames'][:-1];half=len(rows);F=np.diag([1,1,-1])
    for j,t in enumerate(times):
        row=rows[j%half];mirror=j>=half;offset=[p.admission['step_length_m'] if mirror else 0.,0,0]
        for side in ('l','r'):
            other=('r' if side=='l' else 'l') if mirror else side
            previous=row['bodies']['toe_'+other]
            target=np.array(previous['origin']);orientation=np.array(previous['rotation'])
            if mirror:target=F@target;orientation=F@orientation@F
            target+=offset
            names=['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side]
            idx=[p.index[n] for n in names];body=p.model.getBodySet().get('toe_'+side)
            bounds=np.array([p.metadata['coordinates'][n]['bounds_rad'] for n in names]).T
            def residual(x):
                q[j,idx]=x
                pose=q[j].copy();pose[p.index['forward']]+=p.speed*t
                p.set_state(t,pose,np.zeros(len(p.names)))
                R=body.getTransformInGround(p.state).R()
                actual=np.array([[R.get(a,b) for b in range(3)] for a in range(3)])
                rotation=Rotation.from_matrix(orientation.T@actual).as_rotvec()
                return np.r_[body.getPositionInGround(p.state).to_numpy()-target,.3*rotation]
            x=least_squares(residual,np.clip(q[j,idx],*bounds),bounds=bounds,max_nfev=25,ftol=1e-8,xtol=1e-8,gtol=1e-8)
            q[j,idx]=x.x
    return q
