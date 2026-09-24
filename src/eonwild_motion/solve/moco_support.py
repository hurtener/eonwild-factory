"""Optional soft support/recovery tasks, not anatomical limits or external forces."""
import numpy as np


def recovery_residual(angle, speed, acceleration, load_bw, period, policy):
    """Continuous unloading selects relaxation without a phase threshold/snap.

    The angle/rate envelopes are declared artistic/engineering preferences.
    Contact and inverse dynamics still determine the required internal effort.
    """
    gate=1/(1+(np.maximum(load_bw,0)/policy['unloaded_load_BW'])**4)
    return np.concatenate([
        policy['angle_weight']*gate*np.maximum(angle-policy['comfortable_max_angle_rad'],0),
        policy['rate_weight']*gate*np.maximum(np.abs(speed)-policy['comfortable_max_rate_rad_s'],0),
        policy['acceleration_weight']*gate*acceleration*(period/(2*np.pi))**2,
    ])


def ankle_support_residual(angle, speed, acceleration, load_bw, period, length, policy):
    """Identical load/recovery comfort objectives for every trajectory basis.

    Returns sample-major rows so finite optimization retains local time sparsity.
    Existing period scaling of recovery and gravity scaling of loaded movement
    are retained; these soft preferences are not anatomical or force limits.
    """
    columns=[]
    if policy.get('ankle_recovery'):
        columns.append(recovery_residual(angle,speed,acceleration,load_bw,
                       period,policy['ankle_recovery']).reshape(3,-1).T)
    loaded=policy.get('ankle_loaded')
    if loaded:
        positive_load=np.maximum(load_bw,0)
        gate=np.sqrt(positive_load/(positive_load+.08))
        omega=np.sqrt(9.80665/length)
        columns.extend([(loaded['rate_weight']*gate*speed/omega)[:,None],
                        (loaded['acceleration_weight']*gate*acceleration/omega**2)[:,None]])
    return np.concatenate(columns,axis=1) if columns else np.zeros((len(angle),0))


def lane_residual(foot_lateral, load_bw, half_width, allowance, length, weight):
    """Soft world-track envelope. Never pull a planted foot toward a moving hip."""
    gate=np.sqrt(np.maximum(load_bw,0)/(np.maximum(load_bw,0)+.1))
    outward=foot_lateral*np.array([-1.,1.])
    return (weight*gate*np.maximum(np.abs(outward-half_width)-allowance,0)/length).ravel()
