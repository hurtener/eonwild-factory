import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.solve.moco_attention import ProfileAttention


def attention():
    profile=json.loads((Path(__file__).resolve().parents[1]/'catalog/embodiment/tarbo.v1.json').read_text())
    meta={'axial_bindings':[{'body':'lower','role':'neck.0'},
                           {'body':'upper','role':'neck.2'},{'body':'skull','role':'head'}],
          'coordinates':{n+'_yaw':{'bounds_rad':[-.35,.35]} for n in ('lower','upper','skull')}}
    return ProfileAttention(profile,meta)


def test_semantic_regions_and_actual_heading_not_species_names():
    a=attention()
    np.testing.assert_allclose(a.weights,[.83*.16,.83*.84,.17])
    # Stand-in for projected 3D anatomy: yaw coordinates do not add directly.
    heading=lambda q:float(np.degrees(sum(q)*1.18))
    positive=[]
    for target in np.linspace(-45,45,101):
        q,r=a.solve(target,heading)
        assert max(abs(q))<.35 and abs(r['unfulfilled_degrees'])<1e-7
        np.testing.assert_allclose(q,-a.solve(-target,heading)[0],atol=1e-10)
        positive.append(q)
    assert np.max(np.abs(np.diff(positive,axis=0)))<.025


def test_unreachable_heading_is_reported_without_widening_limits():
    a=attention()
    q,r=a.solve(90,lambda q:float(np.degrees(sum(q))*.5))
    assert r['bounded_degrees']<60
    assert r['unfulfilled_degrees']>20
    assert max(abs(q))<=.35


def test_invalid_central_profile_rejected():
    a=attention()
    p={'attention':a.attention,'neckRoles':['neck.0']}
    with pytest.raises(ValueError,match='weights'):
        ProfileAttention(p,{})
