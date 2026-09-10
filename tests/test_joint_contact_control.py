import numpy as np

from test_constant_skin_targets import _inputs

from eonwild_motion.solve.joint_contact_control import (
    JointContactTrial,
    quintic_boundary_transport,
    solve_fixed_authored_pitch,
)


def test_minimax_fit_does_not_weight_duplicate_seam_vertices():
    targets = np.asarray([[0.,0.,0.],[0.,0.,0.],[1.,0.,0.]])
    def evaluate(x):
        # Counterrotation changes the separation; forward/up shift recenters.
        separation = 0.00038 - 0.00001*x[1]
        errors = np.asarray([
            [-0.5*separation-x[2], -x[3], 0.],
            [-0.5*separation-x[2], -x[3], 0.],
            [0.5*separation-x[2], -x[3], 0.],
        ])
        return JointContactTrial(errors, targets, 0.0001, 0., 0., 0., x[0])
    solved = solve_fixed_authored_pitch(evaluate, authored_pitch_degrees=28.)
    assert max(np.linalg.norm(row) for row in solved.trial.material_errors_m) < 0.0002
    assert abs(solved.coordinates[2]) < 1e-10


def test_quintic_transport_preserves_endpoint_pose_velocity_and_acceleration():
    p0=np.asarray([1.,2.]); v0=np.asarray([.3,-.2]); a0=np.asarray([.1,.4])
    p1=np.asarray([-1.,4.]); v1=np.asarray([-.1,.5]); a1=np.asarray([.2,-.3])
    f=lambda u: quintic_boundary_transport(u,p0,v0,a0,p1,v1,a1)
    h=1e-5
    assert np.allclose(f(0),p0) and np.allclose(f(1),p1)
    assert np.allclose((f(h)-f(0))/h, v0, atol=2e-4)
    assert np.allclose((f(1)-f(1-h))/h, v1, atol=2e-4)
    assert np.allclose((f(2*h)-2*f(h)+f(0))/h**2, a0, atol=2e-3)
    assert np.allclose((f(1)-2*f(1-h)+f(1-2*h))/h**2, a1, atol=2e-3)


def test_source_query_applies_joint_contact_controls_inside_pose_solve():
    query = _inputs()["query"]
    baseline = query.evaluate(0.2)
    controls = {
        side: {
            "authored_pitch_degrees": baseline.row["feet"][side][
                "foot_pitch_degrees"
            ],
            "foot_counterrotation_degrees": 0.0,
            "target_offset_m": [0.0, 0.0, 0.0],
        }
        for side in ("left", "right")
    }
    reproduced = query.evaluate_with_joint_contact_controls(0.2, controls)
    assert np.allclose(reproduced.worlds, baseline.worlds, atol=1e-12, rtol=0)
    controls["left"]["foot_counterrotation_degrees"] = 1.0
    rotated = query.evaluate_with_joint_contact_controls(0.2, controls)
    assert not np.allclose(rotated.worlds, baseline.worlds, atol=1e-10, rtol=0)
