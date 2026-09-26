"""Offline environmental load audit of a specified articulated trajectory.

Hydrostatic buoyancy and quadratic drag use admitted segment proxies and
explicit engineering coefficients. Forces are baked into the OpenSim model
for exact replay of THIS trajectory. This is not a fluid simulation, online
controller, or an independently predicted swimming gait.
"""
import numpy as np


def submerged_fraction(center_y,radius,water_height):
    # Spherical-cap fraction, continuous in value and first derivative.
    h=np.clip((water_height-center_y+radius)/radius,0,2)
    return h*h*(3-h)/4


def water_load(segment,position,velocity,policy):
    radius=segment['radius_m'];fraction=submerged_fraction(position[1],radius,policy['height_m'])
    volume=segment['mass_kg']/policy['body_density_kg_m3']
    buoyancy=np.array([0.,policy['water_density_kg_m3']*9.80665*volume*fraction,0.])
    v=np.asarray(velocity);area=np.pi*radius**2
    drag=-.5*policy['water_density_kg_m3']*policy['drag_coefficient']*area*fraction*np.linalg.norm(v)*v
    return buoyancy+drag


def install_water_replay(problem,times,trajectory,policy):
    import opensim as o
    loads={name:[] for name in problem.metadata['segments']}
    for t,q,u in zip(times,trajectory(times),trajectory(times,1)):
        problem.set_state(t,q,u)
        for name,segment in problem.metadata['segments'].items():
            body=problem.model.getBodySet().get(name);point=o.Vec3(*segment['com_local_m'])
            pos=body.findStationLocationInGround(problem.state,point).to_numpy()
            vel=body.findStationVelocityInGround(problem.state,point).to_numpy()
            loads[name].append(water_load(segment,pos,vel,policy))
    entries=[]
    for name,rows in loads.items():
        values=np.array(rows);body=problem.model.updBodySet().get(name)
        force=o.PrescribedForce();force.setName('water_'+name);force.connectSocket_frame(body)
        force.setForceIsInGlobalFrame(True);force.setPointIsInGlobalFrame(False)
        funcs=[]
        for axis in range(3):
            f=o.PiecewiseLinearFunction()
            for t,value in zip(times,values[:,axis]):f.addPoint(float(t),float(value))
            funcs.append(f)
        force.setForceFunctions(*funcs)
        force.setPointFunctions(*[o.Constant(float(x)) for x in problem.metadata['segments'][name]['com_local_m']])
        problem.model.addForce(force)
        entries.append(dict(force='water_'+name,body=name,peak_force_N=np.max(np.abs(values),axis=0).tolist()))
    problem.model.finalizeConnections();problem.state=problem.model.initSystem()
    problem.inverse=o.InverseDynamicsSolver(problem.model)
    problem.metadata['environment_loads']=dict(policy=policy,forces=entries,
        classification='Trajectory-baked hydrostatic/drag engineering audit; no fluid feedback or swimming convergence')
    return {name:np.array(rows).tolist() for name,rows in loads.items()}
