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


def lane_residual(foot_lateral, load_bw, half_width, allowance, length, weight):
    """Soft world-track envelope. Never pull a planted foot toward a moving hip."""
    gate=np.sqrt(np.maximum(load_bw,0)/(np.maximum(load_bw,0)+.1))
    outward=foot_lateral*np.array([-1.,1.])
    return (weight*gate*np.maximum(np.abs(outward-half_width)-allowance,0)/length).ravel()
