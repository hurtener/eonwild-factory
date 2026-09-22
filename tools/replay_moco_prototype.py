#!/usr/bin/env python3
"""Replay saved Moco states through their exact OpenSim model; export mechanics.

This is state replay, not a forward-integration validation or a Unity retarget.
Dense values are interpolated by Moco. Original node and dense measurements are
kept separately so off-mesh errors cannot be hidden by a video resampling.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import opensim as o

p=argparse.ArgumentParser();p.add_argument("directory",type=Path);a=p.parse_args()
root=a.directory
receipt=json.loads((root/"model-receipt.json").read_text())
solve=json.loads((root/"solve-receipt.json").read_text())
model=o.Model(str(root/"model.osim")); state=model.initSystem()

def xyz(v):return [float(v.get(i)) for i in range(3)]

def replay(dense):
    trajectory=o.MocoTrajectory(str(root/"solution.sto"))
    if dense:trajectory.resampleWithNumTimes(241)
    times=np.array(trajectory.getTimeMat())
    states=np.array(trajectory.getStatesTrajectoryMat())
    controls=np.array(trajectory.getControlsTrajectoryMat())
    names=list(trajectory.getStateNames()); control_names=list(trajectory.getControlNames())
    motors=list(receipt["actuators"])
    rows=[]
    for index,t in enumerate(times):
        state.setTime(float(t))
        for j,name in enumerate(names):model.setStateVariableValue(state,name,float(states[index,j]))
        model.realizeVelocity(state)
        u=o.Vector(model.getNumControls(),0)
        for j,name in enumerate(control_names):u[motors.index(name.rsplit("/",1)[-1])]=float(controls[index,j])
        model.setControls(state,u);model.realizeAcceleration(state)
        row={"time_s":float(t),"bodies":{},"contacts":[],"coordinates":{},
             "com_m":xyz(model.calcMassCenterPosition(state)),
             "com_velocity_mps":xyz(model.calcMassCenterVelocity(state)),
             "com_acceleration_mps2":xyz(model.calcMassCenterAcceleration(state))}
        for name,segment in receipt["segments"].items():
            b=model.getBodySet().get(name)
            row["bodies"][name]={"origin":xyz(b.getPositionInGround(state)),
                "rotation":[[float(b.getTransformInGround(state).R().get(i,j)) for j in range(3)] for i in range(3)],
                "end":xyz(b.findStationLocationInGround(state,o.Vec3(*segment["extent_local_m"]))),
                "com":xyz(b.findStationLocationInGround(state,b.getMassCenter()))}
        for c in receipt["contacts"]:
            b=model.getBodySet().get(c["body"])
            local=o.Vec3(*c["center_local_m"])
            center=b.findStationLocationInGround(state,local)
            velocity=np.array(xyz(b.findStationVelocityInGround(state,local)))
            omega=np.array(xyz(b.getAngularVelocityInGround(state)))
            surface_velocity=velocity+np.cross(omega,[0,-c["radius_m"],0])
            values=model.getForceSet().get(c["force"]).getRecordValues(state)
            row["contacts"].append({"name":c["force"],"center":xyz(center),
                "surface_velocity_mps":surface_velocity.tolist(),
                "penetration_m":c["radius_m"]-center.get(1),
                "force_N":[float(values.get(i)) for i in range(3)]})
        for i in range(model.getCoordinateSet().getSize()):
            c=model.getCoordinateSet().get(i)
            row["coordinates"][c.getName()]={"value":c.getValue(state),"speed":c.getSpeedValue(state)}
        row["activations"]={name:float(states[index,names.index('/forceset/'+name+'/activation')]) for name in motors}
        row['clearance_heights_m']={f['path']:float(o.PhysicalFrame.safeDownCast(
            model.getComponent(f['path'])).getPositionInGround(state).get(1))
            for f in receipt.get('clearance_frames',[])}
        rows.append(row)
    return rows

nodes=replay(False);dense=replay(True)
reflection=np.diag([1,1,-1])
step=receipt['admission']['step_length_m']
join_positions=[];join_rotations=[];join_speeds=[]
for name,body in nodes[-1]['bodies'].items():
    other=name[:-2]+('_r' if name.endswith('_l') else '_l') if name.endswith(('_l','_r')) else name
    first=nodes[0]['bodies'][other]
    for point in ('origin','end'):
        expected=reflection@np.array(first[point])+[step,0,0]
        join_positions.append(float(np.linalg.norm(np.array(body[point])-expected)))
    expected=reflection@np.array(first['rotation'])@reflection
    relative=expected.T@np.array(body['rotation'])
    join_rotations.append(float(np.arccos(np.clip((np.trace(relative)-1)/2,-1,1))))
from eonwild_motion.solve.moco_spatial import reflected_coordinate
import re
for name,c in nodes[-1]['coordinates'].items():
    other=re.sub(r'_(l|r)(?=_|$)',lambda m:'_r' if m.group(1)=='l' else '_l',name)
    sign=-1 if reflected_coordinate(name) else 1
    join_speeds.append(abs(c['speed']-sign*nodes[0]['coordinates'][other]['speed']))
half_join=dict(maximum_body_point_error_m=max(join_positions),
    maximum_body_rotation_error_rad=max(join_rotations),maximum_coordinate_speed_error=max(join_speeds),
    scope='Actual final solve node versus reflected opposite initial node plus step translation; not constructed full-loop closure')
mass=receipt["mass_kg"];bw=mass*9.80665
times=np.array([r['time_s'] for r in dense]);dt=times[1]-times[0]
force=np.array([[c['force_N'] for c in r['contacts']] for r in dense]).sum(axis=1)
cv=np.array([r['com_velocity_mps'] for r in dense]);ca=np.gradient(cv,times,axis=0)
kinematic_balance=mass*(ca+np.array([0,9.80665,0]))-force
slips=[float(np.linalg.norm(np.array(c['surface_velocity_mps'])[[0,2]])) for r in dense for c in r['contacts'] if c['force_N'][1]>.05*bw]
clearance={}
for frame in receipt.get('clearance_frames',[]):
    path=frame['path']
    values=[r['clearance_heights_m'][path]-frame['minimum_height_m'] for r in dense]
    clearance[path]={'minimum_height_m':frame['minimum_height_m'],'minimum_margin_m':min(values)}
report={"schema":"eonwild.motion.moco-replay.v1","optimizer":solve,
    "sample_scope":"Moco spline-interpolated states replayed through exact OpenSim model; not forward integration",
    "mass_kg":mass,"root_reserves":receipt['root_reserves'],
    "duration_s":float(times[-1]),"samples":len(dense),
    "vertical_force_BW_range":[float(force[:,1].min()/bw),float(force[:,1].max()/bw)],
    "mean_vertical_force_BW":float(np.trapezoid(force[:,1],times)/(times[-1]*bw)),
    "airborne_fraction_under_0_05_BW":float(np.mean(force[:,1]<.05*bw)),
    "max_penetration_m":max(c['penetration_m'] for r in dense for c in r['contacts']),
    "max_loaded_surface_speed_mps":max(slips,default=0),
    "p95_loaded_surface_speed_mps":float(np.percentile(slips,95)) if slips else 0,
    "bone_clearance":clearance,
    "half_stride_join":half_join,
    "rms_dense_force_balance_BW":float(np.sqrt(np.mean(kinematic_balance[2:-2,:2]**2))/bw),
    "max_dense_force_balance_BW":float(np.max(np.linalg.norm(kinematic_balance[2:-2,:2],axis=1))/bw),
    "rms_dense_3d_force_balance_BW":float(np.sqrt(np.mean(kinematic_balance[2:-2]**2))/bw),
    "max_dense_3d_force_balance_BW":float(np.max(np.linalg.norm(kinematic_balance[2:-2],axis=1))/bw),
    "max_activation":max(abs(x) for r in dense for x in r['activations'].values()),
    "knee_opening_deg":{side:[float(min(180+np.degrees(r['coordinates']['knee_'+side]['value']) for r in dense)),float(max(180+np.degrees(r['coordinates']['knee_'+side]['value']) for r in dense))] for side in ['l','r']},
    "limits":"Coarse discretization, estimated inertias/contact/strength; no muscles, bone stress or biological validation. "+('Reduced spatial dynamics; independent forward replay remains separate.' if receipt.get('spatial') else 'Planar dynamics; no lateral balance.')}
(root/'replay.json').write_text(json.dumps({'metadata':receipt,'report':report,'nodes':nodes,'frames':dense},separators=(',',':'))+'\n')
(root/'replay-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
