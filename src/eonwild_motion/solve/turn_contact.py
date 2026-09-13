"""Material-patch tangential correction for a behavior-owned planted interval.

The frozen centroid is a reduced contact constraint. Per-vertex deformation
must still be measured; a stationary centroid alone is not a locked full patch.
"""
import numpy as np


def tangent(vector,up):
    v=np.asarray(vector);u=np.asarray(up)
    return v-u*np.dot(v,u)


def material_patch_correction(patch,reference,up):
    return tangent(np.mean(reference,axis=0)-np.mean(patch,axis=0),up)


def material_patch_drift(patch,reference,up):
    difference=np.asarray(patch)-np.asarray(reference);u=np.asarray(up)
    horizontal=difference-np.outer(difference@u,u)
    return {'centroid_m':float(np.linalg.norm(horizontal.mean(axis=0))),
            'maximum_vertex_m':float(np.linalg.norm(horizontal,axis=1).max())}
