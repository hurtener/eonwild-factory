import numpy as np
from eonwild_motion.solve.moco_distal_release import released_forefoot


def test_unloaded_sag_restores_contact_and_scales_with_torque_over_inertia():
    t=np.linspace(0,2,201);load=np.ones(len(t));load[(t>.5)&(t<1.3)]=0
    policy=dict(unloaded_threshold_BW=.02,frequency_hz=2.,damping_ratio=.65,release_seconds=.06,prepare_seconds=.14)
    a,windows=released_forefoot(t,load,np.full(len(t),-10.),np.full(len(t),.3),policy)
    b,_=released_forefoot(t,load,np.full(len(t),-20.),np.full(len(t),.6),policy)
    assert np.min(a)<-.05 and len(windows)==1
    np.testing.assert_allclose(a,b,atol=1e-12)
    assert np.all(a[load>.02]==0) and a[windows[0]['contact_ready_s']==t]==0


def test_loaded_or_too_short_flight_never_releases():
    t=np.linspace(0,1,101);load=np.ones(len(t));load[40:50]=0
    policy=dict(unloaded_threshold_BW=.02,frequency_hz=2.,damping_ratio=.65,release_seconds=.06,prepare_seconds=.14)
    a,windows=released_forefoot(t,load,np.full(len(t),-10.),np.ones(len(t)),policy)
    assert not windows and not np.any(a)
