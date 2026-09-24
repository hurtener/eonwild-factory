"""Shared physical-effort and carried-body objectives for all trajectory bases."""
import numpy as np


def shared_effort_residual(effort,command,policy):
    """Same capacity/effort costs for periodic and finite coordination."""
    return (policy['effort_weight']*effort,
            policy['capacity_weight']*np.maximum(np.abs(effort)-.95,0),
            policy['capacity_weight']*.5*np.maximum(np.abs(command)-.98,0))


def shared_cf_residual(problem,effort):
    """Existing soft CF-inspired coupling; not an anatomical muscle model."""
    p=problem.policy
    if not p.get('cf_coupling_weight',0.) or 'motor_tail_0_yaw' not in problem.motors:
        return np.zeros(effort.shape[:-1]+(0,))
    indices=[problem.motors.index(n) for n in ('motor_tail_0_yaw','motor_hip_l','motor_hip_r')]
    torque=effort[...,indices]*problem.capacities[indices]
    value=torque[...,0]-p.get('cf_moment_arm_ratio',.6)*(torque[...,2]-torque[...,1])
    return (p['cf_coupling_weight']*value/(problem.bw*problem.L))[...,None]



def shared_tail_carriage_residual(problem, mechanics):
    """One loaded-carriage objective for periodic and finite trajectories."""
    p=problem.policy;out=[]
    for j,frame in enumerate(problem.metadata['clearance_frames']):
        name=frame['path'].removeprefix('/tip_')
        reference=problem.metadata.get('bracing',{}).get('loaded_tail_end_heights_relative_root_m',{}).get(name)
        if reference is not None:
            relative=mechanics['clearance'][:,j]+frame['minimum_height_m']-mechanics['q'][:,problem.index['height']]
            allowance=p.get('tail_carriage_half_range_leg_lengths',.08)*problem.L
            out.append(p.get('tail_carriage_weight',0.)*np.maximum(abs(relative-reference)-allowance,0)/problem.L)
    return np.column_stack(out) if out else np.zeros((len(mechanics['q']),0))

