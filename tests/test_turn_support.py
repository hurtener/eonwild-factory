"""Loaded leg plane errors must be accommodated at the pelvis."""
import numpy as np
from eonwild_motion.solve.turn_support import accommodate_support_planes


def test_loaded_plane_moves_pelvis_without_vertical_lift():
    hip={'left':np.array([.1,2.,0.])}
    ankle={'left':np.array([0.,0.,0.])}
    normal={'left':np.array([1.,0.,0.])}
    correction=accommodate_support_planes(hip,ankle,normal,{'left':1.},
        np.array([0.,1.,0.]),np.array([0.,0.,1.]),np.array([1.,0.,0.]),2.)
    assert abs((hip['left']+correction-ankle['left'])@normal['left'])<.0003
    assert correction[1]==0


def test_unloaded_leg_does_not_drive_pelvis():
    hip={'left':np.array([.1,2.,0.])}
    correction=accommodate_support_planes(hip,{'left':np.zeros(3)},
        {'left':np.array([1.,0.,0.])},{'left':0.},np.array([0.,1.,0.]),
        np.array([0.,0.,1.]),np.array([1.,0.,0.]),2.)
    np.testing.assert_array_equal(correction,np.zeros(3))
