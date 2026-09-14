"""Backward travel, support continuity and release on the shared planner."""
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities, plan_directional
from eonwild_motion.planning.reverse_walking import reverse_articulation, reverse_attention
from eonwild_motion.solve.turn_support import contact_loads

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("animal", ["allo", "tarbo"])
@pytest.mark.parametrize("yaw", [0., .71])
def test_backward_support_and_stopping(animal,yaw):
    profile=json.loads((ROOT/f"catalog/embodiment/{animal}.v1.json").read_text())
    recipe=json.loads((ROOT/"catalog/behaviors/reverse-walking-review.v1.json").read_text())
    c=resolve_capabilities(profile);h=profile["authoring"]["bodyHeightM"]
    forward=np.array([np.sin(yaw),0,np.cos(yaw)])
    lateral=np.array([np.cos(yaw),0,-np.sin(yaw)])
    p,receipt=plan_directional(c,[0,h,0],forward,lateral,[0,1,0],h,
        {"alpha":-h*.14,"beta":h*.14},{"alpha":0.,"beta":0.},recipe)
    start,heading=p.body(0);end,final_heading=p.body(p.duration)
    assert (end-start)@forward == pytest.approx(-4*.32*c["stepLengthM"])
    assert final_heading==heading==0
    assert np.linalg.norm(p.body(p.duration)[0]-p.body(p.duration-.01)[0])<1e-10
    assert receipt["blocks"][0]["resolved_step_length_m"]<0
    previous=None
    for t in np.linspace(0,p.duration,501):
        row=p.sample(t);loads=contact_loads(p,t)
        assert sum(loads.values())==pytest.approx(1.)
        for side,f in row["feet"].items():
            if not f["contact"]:
                assert loads[side]==pytest.approx(0.)
            elif previous and previous["feet"][side]["contact"]:
                np.testing.assert_allclose(f["position"],previous["feet"][side]["position"],atol=1e-12)
        previous=row
    assert all(f["contact"] for f in previous["feet"].values())
    assert reverse_attention(p,0,recipe["reverse"])==0.
    assert reverse_attention(p,.4,recipe["reverse"])>0.
    assert abs(reverse_attention(p,p.duration,recipe["reverse"]))<1e-12


def test_reverse_recovery_relaxes_before_touchdown_without_forward_launch():
    recipe=json.loads((ROOT/"catalog/behaviors/reverse-walking-review.v1.json").read_text())
    policy=recipe["reverse"]
    for u in [0.,.94,1.]:
        f=reverse_articulation(u,False,0.,policy)
        assert abs(f["toe_flex_degrees"])<1e-10
        assert abs(f["foot_pitch_degrees"])<1e-10
    f=reverse_articulation(.44,False,0.,policy)
    assert f["toe_flex_degrees"]==pytest.approx(14.)
    assert f["foot_pitch_degrees"]==-8.
    assert recipe["walking"]["heel_roll_degrees"]==4.


def test_backward_rejects_ambiguous_direction_and_forward_articulation():
    profile=json.loads((ROOT/"catalog/embodiment/allo.v1.json").read_text())
    recipe=json.loads((ROOT/"catalog/behaviors/reverse-walking-review.v1.json").read_text())
    c=resolve_capabilities(profile)
    def plan(r):
        return plan_directional(c,[0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,
            {"alpha":-.28,"beta":.28},{"alpha":0.,"beta":0.},r)
    recipe["blocks"][0].pop("step_scale_of_normal")
    recipe["blocks"][0]["step_length_body_heights"]=.2
    with pytest.raises(ValueError,match="profile-relative"):
        plan(recipe)
    recipe["walking"]["articulation_source"]="admitted_grounded_walk"
    with pytest.raises(ValueError,match="own grounded articulation"):
        plan(recipe)
