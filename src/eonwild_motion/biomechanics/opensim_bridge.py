"""OpenSim body-transform replay onto an unchanged artistic skin hierarchy.

A rig-shaped replay proxy proves transport, NOT anatomical/dynamic validation.
Every moving joint is a ball joint (a free root); dummy masses and zero gravity
are explicitly confined to kinematics. A future physically calibrated .osim and
solved trajectory can use the body-transform boundary without changing Unity.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation
from ..errors import ContractError
from .kinematic_seed import Seed


def _osim():
    try:
        import opensim
    except ImportError as exc:
        raise ContractError('OpenSim 4.6 is required for this bridge; no authored fallback is substituted') from exc
    return opensim


def _vec(o, values):
    return o.Vec3(*(float(v) for v in values))


def make_replay_proxy(seed: Seed):
    o=_osim(); model=o.Model();model.setName('kinematic_replay_proxy_NOT_DYNAMIC_ANATOMY')
    model.set_gravity(o.Vec3(0))
    joint_nodes=set(seed.source.document['skins'][0]['joints'])
    roots=[n for n in joint_nodes if seed.source.parents[n] not in joint_nodes]
    if roots != [seed.root]:
        raise ContractError('bridge requires exactly the mapped skin root')
    bodies={};joints={}; coordinates=[]
    for node in seed.skin.order:
        if node not in joint_nodes: continue
        parent=seed.source.parents[node]
        # Dummy inertial values make the kinematic structure loadable. They
        # MUST NOT be used to claim forces, running capacity or biological mass.
        body=o.Body(f'frame_{node}',1.,o.Vec3(0),o.Inertia(1.))
        model.addBody(body);bodies[node]=body
        if node==seed.root:
            joint=o.FreeJoint(f'joint_{node}',model.getGround(),_vec(o,seed.rest[node,:3,3]),o.Vec3(0),body,o.Vec3(0),o.Vec3(0))
            labels=('rx','ry','rz','tx','ty','tz')
        else:
            if parent not in bodies:
                raise ContractError('skin hierarchy contains an unsupported unbound intermediate node')
            offset=seed.rest[node,:3,3]-seed.rest[parent,:3,3]
            joint=o.BallJoint(f'joint_{node}',bodies[parent],_vec(o,offset),o.Vec3(0),body,o.Vec3(0),o.Vec3(0))
            labels=('rx','ry','rz')
        for i,label in enumerate(labels):
            coordinate=joint.upd_coordinates(i)
            coordinate.setName(f'q_{node}_{label}')
            coordinates.append((node,label,coordinate))
        model.addJoint(joint);joints[node]=joint
    model.finalizeConnections();model.initSystem()
    return model,bodies,joints,coordinates


def write_seed_states(seed, model, coordinates, times, translations, rotations, scales, path):
    rows=[]
    for i,time in enumerate(times):
        world=seed.skin.world(translations[i],rotations[i],scales[i])
        delta={n:Rotation.from_matrix(world[n,:3,:3]).as_matrix()@seed.rest_R[n].T for n in {n for n,_,_ in coordinates}}
        values={}
        for node in delta:
            parent=seed.source.parents[node]
            local=delta[node] if node==seed.root else delta[parent].T@delta[node]
            euler=Rotation.from_matrix(local).as_euler('XYZ')
            values.update({(node,axis):float(v) for axis,v in zip(('rx','ry','rz'),euler)})
            if node==seed.root:
                values.update({(node,axis):float(v) for axis,v in zip(('tx','ty','tz'),world[node,:3,3]-seed.rest[node,:3,3])})
        rows.append([float(time)]+[values[(n,k)] for n,k,c in coordinates])
    labels=['time']+[str(c.getAbsolutePathString())+'/value' for n,k,c in coordinates]
    with Path(path).open('w') as f:
        f.write('authored_kinematic_seed_NOT_PREDICTED\nversion=1\nnRows='+str(len(rows))+'\nnColumns='+str(len(labels))+'\ninDegrees=no\nendheader\n')
        f.write('\t'.join(labels)+'\n')
        for row in rows: f.write('\t'.join(format(x,'.17g') for x in row)+'\n')
    return labels[1:]


def replay(seed: Seed, output: Path, times, translations, rotations, scales):
    """Serialize, reopen and evaluate the OpenSim model and coordinate table."""
    o=_osim(); model,bodies,joints,coordinates=make_replay_proxy(seed)
    output.mkdir(parents=True,exist_ok=True)
    model_path=output/'kinematic-proxy.osim';states_path=output/'authored-walk-seed.sto'
    model.printToXML(str(model_path))
    labels=write_seed_states(seed,model,coordinates,times,translations,rotations,scales,states_path)
    # Reopen actual files rather than returning the input trajectories.
    model=o.Model(str(model_path));state=model.initSystem();table=o.TimeSeriesTable(str(states_path))
    found=list(table.getColumnLabels())
    if found!=labels or table.getNumRows()!=len(times):
        raise ContractError('OpenSim trajectory columns/rows differ after serialization')
    opened_coords={str(c.getAbsolutePathString())+'/value':c for c in [model.getCoordinateSet().get(i) for i in range(model.getCoordinateSet().getSize())]}
    if set(opened_coords)!=set(labels):
        raise ContractError('missing or unexpected OpenSim coordinate; refusing partial motion import')
    if str(table.getTableMetaDataString('inDegrees')).lower()!='no':
        raise ContractError('replay fixture requires explicit radians')
    body_nodes=list(bodies)
    reopened_bodies={n:model.getBodySet().get(f'frame_{n}') for n in body_nodes}
    result_t=[];result_q=[];max_source_position=0.;max_source_angle=0.;max_target_position=0.
    source_frames=[]
    for i,time in enumerate(times):
        if abs(float(table.getIndependentColumn()[i])-float(time))>1e-10:
            raise ContractError('OpenSim timeline changed')
        state.setTime(float(time));row=table.getRowAtIndex(i)
        for j,label in enumerate(labels):
            value=float(row.getElt(0,j))
            if not np.isfinite(value):raise ContractError('non-finite state value')
            opened_coords[label].setValue(state,value,False)
        model.realizePosition(state)
        t=np.asarray(seed.source.rest_translation,float).copy();q=np.asarray(seed.source.rest_rotation,float).copy()
        source_world=seed.skin.world(translations[i],rotations[i],scales[i])
        frame_row={}
        for node in seed.skin.order:
            if node not in reopened_bodies:continue
            transform=reopened_bodies[node].getTransformInGround(state)
            R=transform.R();p=transform.p()
            delta_R=np.array([[R.get(r,c) for c in range(3)] for r in range(3)])
            position=np.array([p.get(k) for k in range(3)])
            desired_R=delta_R@seed.rest_R[node]
            target_world=seed.skin.world(t,q,scales[i]);parent=seed.source.parents[node]
            parent_R=np.eye(3) if parent is None else Rotation.from_matrix(target_world[parent,:3,:3]).as_matrix()
            q[node]=Rotation.from_matrix(parent_R.T@desired_R).as_quat()
            if node==seed.root:
                parent_M=np.eye(4) if parent is None else target_world[parent]
                t[node]=(np.linalg.inv(parent_M)@np.r_[position,1])[:3]
            max_source_position=max(max_source_position,float(np.linalg.norm(position-source_world[node,:3,3])))
            source_R=Rotation.from_matrix(source_world[node,:3,:3]).as_matrix()
            max_source_angle=max(max_source_angle,float(Rotation.from_matrix(desired_R@source_R.T).magnitude()))
            frame_row[str(node)]={'position_m':position.tolist(),'delta_rotation_xyzw':Rotation.from_matrix(delta_R).as_quat().tolist()}
        target_world=seed.skin.world(t,q,scales[i])
        for node in body_nodes:
            max_target_position=max(max_target_position,float(np.linalg.norm(target_world[node,:3,3]-np.array(frame_row[str(node)]['position_m']))))
        result_t.append(t);result_q.append(q);source_frames.append(frame_row)
    result_t=np.asarray(result_t);result_q=np.asarray(result_q)
    for i in range(1,len(result_q)):
        mask=np.sum(result_q[i]*result_q[i-1],axis=1)<0;result_q[i,mask]*=-1
    threshold=5e-5
    if max_source_position>threshold or max_target_position>threshold or max_source_angle>1e-5:
        raise ContractError(f'OpenSim bridge parity failed: source={max_source_position},target={max_target_position},angle={max_source_angle}')
    frames={'schema':'eonwild.biomechanics.body-frames.v1','times_s':np.asarray(times).tolist(),'coordinate':seed.profile['coordinate'],'samples':source_frames}
    (output/'opensim-body-frames.json').write_text(json.dumps(frames,separators=(',',':'))+'\n')
    receipt={'status':'PASS_KINEMATIC_BRIDGE_ONLY','opensim_version':o.GetVersionAndDate(),'method':'reopened .osim + .sto -> getTransformInGround -> reference-frame calibrated local quaternions',
             'source_sha256':hashlib.sha256(seed.source.raw).hexdigest(),'model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'states_sha256':hashlib.sha256(states_path.read_bytes()).hexdigest(),
             'samples':len(times),'moving_bodies':len(body_nodes),'coordinates':len(labels),
             'max_source_frame_position_error_m':max_source_position,'max_target_frame_position_error_m':max_target_position,'max_orientation_error_rad':max_source_angle,
             'position_tolerance_m':threshold,'all_coordinates_accounted_for':True,'source_trajectory_classification':'AUTHORED_CONTACT_AWARE_SEED',
             'dinosaur_prediction':'NOT_RUN','mass_inertia_actuation':'UNVALIDATED_DUMMY_KINEMATIC_VALUES_DO_NOT_USE_FOR_DYNAMICS','unity_parity':'NOT_RUN','production_approval':'NOT_GRANTED'}
    (output/'opensim-replay.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return result_t,result_q,receipt


def moco_environment_smoke(output):
    """Independent minimum-effort slider. Never counted as an animal solve."""
    o=_osim();m=o.Model();m.setName('environment_smoke_not_animal');m.set_gravity(o.Vec3(0))
    b=o.Body('body',2.,o.Vec3(0),o.Inertia(1));m.addBody(b)
    j=o.SliderJoint('slider',m.getGround(),b);c=j.updCoordinate();c.setName('position');m.addJoint(j)
    a=o.CoordinateActuator();a.setCoordinate(c);a.setName('force');a.setOptimalForce(1);m.addForce(a);m.finalizeConnections()
    study=o.MocoStudy();p=study.updProblem();p.setModel(m)
    p.setTimeBounds([0],[1]);p.setStateInfo('/jointset/slider/position/value',[-2,2],[0],[1]);p.setStateInfo('/jointset/slider/position/speed',[-10,10],[0],[0]);p.setControlInfo('/forceset/force',[-100,100]);p.addGoal(o.MocoControlGoal())
    solver=study.initCasADiSolver();solver.set_num_mesh_intervals(12);solver.set_optim_max_iterations(100);solver.set_optim_convergence_tolerance(1e-6);solver.set_optim_constraint_tolerance(1e-6)
    solution=study.solve()
    if not solution.success():raise ContractError('Moco environment smoke did not converge')
    solution.write(str(Path(output)/'moco-environment-smoke.sto'))
    r={'status':'PASS','solver_status':solution.getStatus(),'test':'one-second minimum-effort 2kg slider','dinosaur_prediction':'NOT_RUN','opensim':o.GetVersionAndDate()}
    (Path(output)/'moco-environment-smoke.json').write_text(json.dumps(r,indent=2)+'\n');return r
