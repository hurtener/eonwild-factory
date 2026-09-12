"""Pelvis accommodation to planted leg planes for directional diagnostics."""
import numpy as np


def accommodate_support_planes(hips, ankles, normals, gains, up, forward, lateral, height):
    """Move the pelvis, not individual limb joints, toward loaded leg planes.

    Independent horizontal projections avoid an ill-conditioned double-support snap.
    This is a bounded geometric accommodation, not a mass/force simulation.
    """
    basis=np.column_stack((lateral,forward))
    a=np.asarray([normals[s]@basis for s in hips])
    error=np.asarray([normals[s]@(ankles[s]-hips[s]) for s in hips])
    w=np.asarray([gains[s] for s in hips])
    # Blend independent plane projections. Solving the two almost-parallel
    # equations together amplified tiny load changes into pelvis snaps.
    lengths=np.sum(a*a,axis=1)
    projections=a*(error/np.maximum(lengths,1e-8))[:,None]
    delta=np.sum(w[:,None]*projections,axis=0)/max(float(w.sum()),1.)
    length=np.linalg.norm(delta)
    if length>.12*height:delta*=.12*height/length
    return basis@delta
