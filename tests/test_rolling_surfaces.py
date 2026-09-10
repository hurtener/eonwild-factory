from dataclasses import replace
from eonwild_motion.solve.rolling_surfaces import RollingContactEvent, RollingContactPlan


def test_rolling_contact_keeps_material_anchor_until_declared_transfer():
    heel = RollingContactEvent(0., 2, (0., 0., 0.))
    toe = RollingContactEvent(0.4, 8, (0., 0., 0.2))
    plan = RollingContactPlan(1., .6, ((heel, toe), (heel, toe)),
                              ((0., 0., 0.),) * 2, ((0., 0., 0.),) * 2, '')
    plan = replace(plan, binding_sha256=plan.current_binding_sha256())
    assert plan.event('left', .3999) == heel
    assert plan.event('left', .4) == toe
    assert plan.event('left', .599) == toe
    changed = replace(plan, events=((heel, replace(toe, anchor_m=(0., 0., .3))), (heel, toe)))
    assert changed.current_binding_sha256() != plan.binding_sha256
