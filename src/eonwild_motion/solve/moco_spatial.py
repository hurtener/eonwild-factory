"""Reduced spatial anatomy and reflection for the optional offline Moco path.

All axes use admitted forward/up/lateral coordinates. Joint ranges, distribution
and passive mechanics are explicit engineering priors, not fossil measurements.
"""
import numpy as np


def spatial_joint(name, parent, location, child, axes, translations=()):
    import opensim as o
    transform=o.SpatialTransform()
    # A valid orthogonal basis is required even for unused transform axes.
    for i,axis in enumerate(((0,0,1),(0,1,0),(1,0,0),(1,0,0),(0,1,0),(0,0,1))):
        transform.updTransformAxis(i).setAxis(o.Vec3(*axis))
        transform.updTransformAxis(i).set_function(o.Constant(0))
    for i,(coordinate,axis) in enumerate(axes):
        a=transform.updTransformAxis(i);a.setAxis(o.Vec3(*axis))
        names=o.ArrayStr();names.append(coordinate);a.setCoordinateNames(names)
        a.set_function(o.LinearFunction(1,0))
    for i,coordinate in enumerate(translations):
        a=transform.updTransformAxis(3+i);names=o.ArrayStr();names.append(coordinate)
        a.setCoordinateNames(names);a.set_function(o.LinearFunction(1,0))
    return o.CustomJoint(name,parent,o.Vec3(*map(float,location)),o.Vec3(0),child,o.Vec3(0),o.Vec3(0),transform)


def reflected_coordinate(name):
    return name in ('yaw','roll','lateral') or '_yaw' in name or '_roll' in name


def calibrate_axial_capacity(model, metadata, recipe):
    """Engineering reserve from gravity demand, not reconstructed muscle strength."""
    import opensim as o
    fraction=recipe['spatial'].get('static_axial_capacity_fraction')
    if fraction is None:return
    if not 0<fraction<1:raise ValueError('Static capacity fraction must be between zero and one')
    state=model.initSystem();indices={}
    for coordinate in model.getCoordinateSet():
        state.updU().setToZero();coordinate.setSpeedValue(state,1)
        indices[coordinate.getName()]=int(np.argmax(np.abs(state.getU().to_numpy())))
    state.updU().setToZero();model.updCoordinateSet().get('height').setValue(state,10)
    for name,value in recipe['spatial']['posture_reference'].items():model.updCoordinateSet().get(name).setValue(state,value)
    model.realizeVelocity(state)
    torque=o.InverseDynamicsSolver(model).solve(state,o.Vector(state.getNU(),0)).to_numpy()
    for motor,data in metadata['actuators'].items():
        coordinate=motor.removeprefix('motor_')
        if coordinate.startswith(('hip_','knee_','ankle_','mtp_','digit_')):continue
        required=float(abs(torque[indices[coordinate]]));prior=data['capacity_Nm']
        capacity=max(prior,required/fraction)
        act=o.ActivationCoordinateActuator.safeDownCast(model.updForceSet().get(motor));act.setOptimalForce(capacity)
        data.update(capacity_Nm=capacity,prior_capacity_Nm=prior,static_gravity_minus_passive_demand_Nm=required)
    metadata['axial_capacity_calibration']=dict(static_fraction=fraction,
        classification='Engineering torque reserve from supported reference-pose inverse dynamics, after passive support. No muscle reconstruction or external forces added to simulation.')
    model.finalizeConnections()


def initialize_lateral_balance(model, metadata, guess):
    """Periodic inverted-pendulum balance and position IK, for initialization only."""
    import opensim as o
    from scipy.integrate import solve_ivp
    from scipy.optimize import least_squares
    names=list(guess.getStateNames());matrix=np.array(guess.getStatesTrajectoryMat());times=guess.getTimeMat()
    state=model.initSystem();coordinates=model.updCoordinateSet();L=sum(metadata['segment_lengths_m'])
    ratio=metadata['spatial'].get('foot_track_hip_width_ratio',1.)
    pad_half_width=max(abs(c['center_local_m'][2]) for c in metadata['contacts'])
    forces=[];cop=[];heights=[];targets=[]
    def set_row(row):
        for j,n in enumerate(names):model.setStateVariableValue(state,n,float(row[j]))
        for side in ('l','r'):coordinates.get('hip_'+side+'_roll').setValue(state,0)
        model.realizeVelocity(state)
    for row in matrix:
        set_row(row);force=[]
        for side in ('l','r'):
            force.append(sum(model.getForceSet().get(c['force']).getRecordValues(state).get(1) for c in metadata['contacts'] if c['force'].endswith('_'+side)))
        z=[metadata['admission']['points'][s+'Leg.0'][2]*ratio for s in ('left','right')]
        forces.append(sum(force));cop.append(float(np.dot(force,z)/max(sum(force),1e-6)))
        heights.append(model.calcMassCenterPosition(state).get(1))
        targets.append({side:model.getBodySet().get('toe_'+side).getPositionInGround(state).to_numpy().copy() for side in ('l','r')})
    coeff=np.array(forces)/metadata['mass_kg']/np.array(heights)
    def integrate(initial,forced):
        return solve_ivp(lambda t,x:[x[1],np.interp(t,times,coeff)*(x[0]-(np.interp(t,times,cop) if forced else 0))],
            (times[0],times[-1]),initial,t_eval=times,rtol=1e-8,atol=1e-10).y
    offset=integrate([0,0],True);fundamental=np.column_stack([integrate(x,False)[:,-1] for x in ([1,0],[0,1])])
    initial=np.linalg.solve(fundamental+np.eye(2),-offset[:,-1]);lateral=integrate(initial,True)
    for i,row in enumerate(matrix):
        set_row(row);coordinates.get('lateral').setValue(state,float(lateral[0,i]))
        for side in ('l','r'):
            hip,knee,roll=[coordinates.get(n+'_'+side) for n in ('hip','knee')]+[coordinates.get('hip_'+side+'_roll')]
            old=np.array([hip.getValue(state),knee.getValue(state),0.]);target=targets[i][side].copy();target[2]*=ratio
            toe=model.getBodySet().get('toe_'+side)
            def residual(x):
                hip.setValue(state,float(x[0]));knee.setValue(state,float(x[1]));roll.setValue(state,float(x[2]));model.realizePosition(state)
                # The tilted transverse pads need a small raised foot origin.
                raised=target.copy();raised[1]+=.5*pad_half_width*abs(np.sin(x[2]))
                return np.r_[toe.getPositionInGround(state).to_numpy()-raised,.005*(x[:2]-old[:2])]
            bounds=([-.8,-2.,-.3],[1.45,-.16,.3])
            result=least_squares(residual,np.clip(old,*bounds),bounds=bounds,max_nfev=35,ftol=1e-9,xtol=1e-9,gtol=1e-9)
            for c,value in zip((hip,knee,roll),result.x):matrix[i,names.index(c.getAbsolutePathString()+'/value')]=value
            mtp=coordinates.get('mtp_'+side);col=names.index(mtp.getAbsolutePathString()+'/value')
            matrix[i,col]+=old[0]+old[1]-result.x[0]-result.x[1]
        matrix[i,names.index('/jointset/root/lateral/value')]=lateral[0,i]
    for j,name in enumerate(names):
        if name.endswith('/speed'):
            value=names.index(name.removesuffix('/speed')+'/value');matrix[:,j]=np.gradient(matrix[:,value],times)
    for j,name in enumerate(names):
        v=o.Vector(len(times),0)
        for i in range(len(times)):v[i]=float(matrix[i,j])
        guess.setState(name,v)
    return dict(root_lateral_range_m=[float(lateral[0].min()),float(lateral[0].max())],
        classification='Periodic lateral force/moment balance and position IK warm start only; no trajectory tracking or root assistance')


def transfer_guess(solver, path, model=None, metadata=None):
    """Warm-start a changed topology; this is initialization, never tracking."""
    import opensim as o
    old=o.MocoTrajectory(str(path));guess=solver.createGuess()
    old.resample(guess.getTime())
    old_states=list(old.getStateNames());old_controls=list(old.getControlNames())
    states=np.asarray(old.getStatesTrajectoryMat());controls=np.asarray(old.getControlsTrajectoryMat())
    zero=np.zeros(len(np.asarray(guess.getTimeMat())))
    def v(values):
        out=o.Vector(len(values),0)
        for i,x in enumerate(values):out[i]=float(x)
        return out
    for name in guess.getStateNames():
        if name in old_states:values=states[:,old_states.index(name)]
        else:
            values=zero
            if name.startswith('/jointset/'):
                coordinate,kind=name.split('/')[-2:]
                mapping={'tail_0':('tail_proximal',.6),'tail_1':('tail_proximal',.4),
                         'tail_2':('tail_distal',.6),'tail_3':('tail_distal',.4),
                         'neck_upper':('neck',.45)}
                if coordinate in mapping:
                    source,scale=mapping[coordinate];source=f'/jointset/{source}/{source}/{kind}'
                    if source in old_states:values=scale*states[:,old_states.index(source)]
        if name.startswith('/jointset/neck/neck/') and '/jointset/neck_upper/neck_upper/value' not in old_states:values=values*.55
        guess.setState(name,v(values))
    for name in guess.getControlNames():
        guess.setControl(name,v(np.clip(controls[:,old_controls.index(name)],-1,1) if name in old_controls else zero))
    for name in guess.getDerivativeNames():
        # Same-topology continuation also needs accelerations. A zero implicit
        # acceleration guess contradicts a moving gait even when q/u are good.
        speed=name.removesuffix('/accel')+'/speed'
        values=np.gradient(states[:,old_states.index(speed)],old.getTimeMat(),edge_order=2) if speed in old_states else zero
        guess.setDerivative(name,v(np.clip(values,-300,300)))
    changed_topology=any(name not in old_states for name in guess.getStateNames())
    if model is not None and changed_topology:
        # A new topology cannot inherit old muscle/motor effort unchanged.
        # Initialize internal torques with inverse dynamics of the guess only;
        # root residuals remain unactuated, and no angle tracking is introduced.
        from scipy.optimize import lsq_linear
        if metadata['spatial'].get('balanced_initialization'):
            metadata['balanced_initialization']=initialize_lateral_balance(model,metadata,guess)
        state=model.initSystem();names=list(guess.getStateNames())
        matrix=np.asarray(guess.getStatesTrajectoryMat());times=np.asarray(guess.getTimeMat())
        admission=metadata.get('admission')
        if admission and not metadata['spatial'].get('balanced_initialization'):
            # Initialize the narrower running track through hip adduction.
            # This is a guess only, not a prescribed hip waveform or root force.
            length=sum(metadata['segment_lengths_m'])
            ratio=metadata['spatial'].get('foot_track_hip_width_ratio',1.)
            for side,semantic in [('l','left'),('r','right')]:
                path=f'/jointset/hip_{side}/hip_{side}_roll/value'
                values=zero+admission['points'][semantic+'Leg.0'][2]*(1-ratio)/length
                guess.setState(path,v(values))
            matrix=np.asarray(guess.getStatesTrajectoryMat())
        coordinates=list(model.getCoordinateSet());u_indices={}
        for coordinate in coordinates:
            state.updU().setToZero();coordinate.setSpeedValue(state,1.)
            u_indices[coordinate.getName()]=int(np.argmax(np.abs(state.getU().to_numpy())))
        speed_columns={c.getName():names.index(c.getAbsolutePathString()+'/speed') for c in coordinates}
        accelerations={n:np.gradient(matrix[:,i],times) for n,i in speed_columns.items()}
        inverse=o.InverseDynamicsSolver(model)
        activations={n:[] for n in metadata['actuators']}
        realized_accelerations=[]
        motor_names=list(activations)
        input_matrix=np.zeros((state.getNU(),len(motor_names)))
        for j,motor in enumerate(motor_names):
            input_matrix[u_indices[motor.removeprefix('motor_')],j]=metadata['actuators'][motor]['capacity_Nm']
        for row,t in enumerate(times):
            state.setTime(float(t))
            for i,name in enumerate(names):model.setStateVariableValue(state,name,0. if name.endswith('/activation') else float(matrix[row,i]))
            model.realizeVelocity(state);model.setControls(state,o.Vector(model.getNumControls(),0))
            udot=o.Vector(state.getNU(),0)
            for n,values in accelerations.items():udot[u_indices[n]]=float(values[row])
            # Bounded least squares minimizes acceleration error with the six
            # root coordinates genuinely unactuated. Clipping inverse torques
            # independently can leave enormous accelerations in small toes.
            bias=inverse.solve(state,o.Vector(state.getNU(),0)).to_numpy()
            mass=o.Matrix();model.getMatterSubsystem().calcM(state,mass)
            mass=mass.to_numpy()
            response=np.linalg.solve(mass,input_matrix)
            target=udot.to_numpy()+np.linalg.solve(mass,bias)
            result=lsq_linear(response,target,bounds=(-.95,.95),method='bvls',tol=1e-9)
            for j,motor in enumerate(motor_names):activations[motor].append(float(result.x[j]))
            realized_accelerations.append(response@result.x-np.linalg.solve(mass,bias))
        for motor,values in activations.items():
            values=np.asarray(values);guess.setState('/forceset/'+motor+'/activation',v(values))
            controls=np.clip(values+metadata['actuators'][motor]['activation_time_constant_s']*np.gradient(values,times),-.99,.99)
            guess.setControl('/forceset/'+motor,v(controls))
        realized_accelerations=np.asarray(realized_accelerations)
        for name in guess.getDerivativeNames():
            if name.endswith('/accel'):
                guess.setDerivative(name,v(np.clip(realized_accelerations[:,u_indices[name.split('/')[-2]]],-300,300)))
    return guess


def add_axial(model, metadata, points, fractions, capacities, length, body, pin, trunk, recipe):
    import opensim as o
    policy=recipe['spatial']
    def p(role):
        v=points[role].copy();v[2]=0;return v
    chest_origin=p('spine.2');neck_origin=p('neck.0')
    chest_extent=neck_origin-chest_origin
    chest=body('chest',fractions['chest'],chest_extent*.55,chest_extent,.21*length)
    pin('chest',trunk,chest_origin,chest,[-.20,.20],capacities['chest'])
    metadata['axial_bindings']=[dict(body='chest',role='spine.2')]
    # Two neck regions and a separate head retain original admitted pivots.
    neck_roles=sorted((k for k in points if k.startswith('neck.')),key=lambda k:int(k.split('.')[-1]))
    split=neck_roles[len(neck_roles)//2]
    nodes=[('neck','neck.0',split,.32,.10),('neck_upper',split,'head',.28,.09),
           ('head','head',None,.40,.15)]
    parent=chest;parent_origin=chest_origin
    for name,role,end,share,radius in nodes:
        origin=p(role);extent=(p(end)-origin) if end else np.array([.30*length,0,0])
        b=body(name,fractions['neck']*share,extent*.5,extent,radius*length)
        pin(name,parent,origin-parent_origin,b,[-.32,.32],capacities['neck']*(.8 if name=='neck' else .55))
        metadata['axial_bindings'].append(dict(body=name,role=role))
        if name=='head' and 'nose' in points:
            nose_local=p('nose')-origin
            nose=o.PhysicalOffsetFrame('nose',b,o.Transform(o.Vec3(*map(float,nose_local))))
            model.addComponent(nose)
            metadata['attention_frame']='/nose'
            metadata['nose_local_m']=nose_local.tolist()
        parent=b;parent_origin=origin
    tail_roles=sorted((k for k in points if k.startswith('tail.')),key=lambda k:int(k.split('.')[-1]))
    indices=np.linspace(0,len(tail_roles)-1,5).astype(int)
    total=fractions['tail_proximal']+fractions['tail_distal']
    parent=trunk;parent_origin=np.zeros(3)
    for i in range(4):
        role,end=tail_roles[indices[i]],tail_roles[indices[i+1]]
        origin=p(role);extent=p(end)-origin;name='tail_'+str(i)
        share=policy['tail_mass_shares'][i];radius=policy['tail_radius_leg_lengths'][i]*length
        b=body(name,total*share,extent*.40,extent,radius)
        pin(name,parent,origin-parent_origin,b,[-.26,.26],capacities['tail_proximal']*policy['tail_capacity_shares'][i])
        metadata['axial_bindings'].append(dict(body=name,role=role))
        frame=o.PhysicalOffsetFrame('tip_'+name,b,o.Transform(o.Vec3(*map(float,extent))))
        model.addComponent(frame)
        metadata['clearance_frames'].append(dict(path='/tip_'+name,minimum_height_m=(.22 if i==3 else .08)*length))
        parent=b;parent_origin=origin
