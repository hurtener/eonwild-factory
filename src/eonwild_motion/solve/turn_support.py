"""Pelvis accommodation to planted leg planes for directional diagnostics."""
import numpy as np


def accommodate_support_planes(hips, ankles, normals, gains, up, forward, lateral, height):
    """Move the pelvis, not individual limb joints, toward loaded leg planes.

    The horizontal regularizer avoids an ill-conditioned double-support snap.
    This is a bounded geometric accommodation, not a mass/force simulation.
    """
    basis=np.column_stack((lateral,forward))
    a=np.asarray([normals[s]@basis for s in hips])
    error=np.asarray([normals[s]@(ankles[s]-hips[s]) for s in hips])
    w=np.asarray([gains[s] for s in hips])
    delta=np.linalg.solve(a.T@(w[:,None]*a)+.002*np.eye(2),a.T@(w*error))
    length=np.linalg.norm(delta)
    if length>.12*height:delta*=.12*height/length
    return basis@delta
