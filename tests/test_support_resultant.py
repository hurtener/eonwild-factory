from __future__ import annotations

import pytest

from eonwild_motion.dynamics.centroidal import CentroidalSample
from eonwild_motion.dynamics.support_resultant import sampled_support_resultants
from eonwild_motion.errors import ContractError


def sample(time, *, mass=10.0, com=(0.2, 1.0, 0.3), velocity=(0, 0, 0), angular=(0, 0, 0), mode="absolute"):
    return CentroidalSample(
        time_s=time,
        total_mass_kg=mass,
        com_m=com,
        com_velocity_mps=velocity,
        linear_momentum_kg_mps=tuple(mass * value for value in velocity),
        angular_momentum_kg_m2ps=angular,
        mass_mode=mode,
    )


def test_stationary_resultant_passes_through_com_projection():
    rows = [sample(t) for t in (0.0, 0.5, 1.0)]
    result = sampled_support_resultants(rows, ground_height_m=0, up_axis=(0, 1, 0), forward_axis=(0, 0, 1))
    assert result[1].point_m == pytest.approx((0.2, 0.0, 0.3))
    assert result[1].force_n == pytest.approx((0.0, 98.0665, 0.0))


def test_known_horizontal_acceleration_moves_resultant_opposite_acceleration():
    # v_x=t gives exactly 1 m/s^2 at the middle sample.  Independent planar
    # moment balance requires p_x=c_x-h*a_x/g when Hdot=0.
    rows = [sample(t, velocity=(t, 0, 0)) for t in (0.0, 1.0, 2.0)]
    result = sampled_support_resultants(rows, ground_height_m=0, up_axis=(0, 1, 0), forward_axis=(0, 0, 1))
    assert result[1].point_m[0] == pytest.approx(0.2 - 1.0 / 9.80665)
    assert result[1].point_m[2] == pytest.approx(0.3)


def test_known_pitch_momentum_rate_moves_forward_resultant():
    # With vertical force only, tau_x = -r_z*F_y.  L_x=2t therefore requires
    # r_z=-2/(m*g), independently of the implementation's vector layout.
    rows = [sample(t, angular=(2 * t, 0, 0)) for t in (0.0, 1.0, 2.0)]
    result = sampled_support_resultants(rows, ground_height_m=0, up_axis=(0, 1, 0), forward_axis=(0, 0, 1))
    assert result[1].point_m[2] == pytest.approx(0.3 - 2.0 / (10.0 * 9.80665))


def test_declared_frame_rotation_preserves_planar_solution():
    # Rotate the conventional frame so +Z is up and +X is forward.  A +Y
    # lateral acceleration must move the ground point toward -Y.
    rows = [sample(t, com=(0.3, 0.2, 1.0), velocity=(0, t, 0)) for t in (0.0, 1.0, 2.0)]
    result = sampled_support_resultants(rows, ground_height_m=0, up_axis=(0, 0, 1), forward_axis=(1, 0, 0))
    assert result[1].point_m == pytest.approx((0.3, 0.2 - 1.0 / 9.80665, 0.0))


def test_fail_closed_on_normalized_or_non_supporting_samples():
    with pytest.raises(ContractError, match="absolute mass"):
        sampled_support_resultants([sample(t, mode="normalized") for t in (0, 1, 2)], ground_height_m=0, up_axis=(0, 1, 0), forward_axis=(0, 0, 1))
    falling = [sample(t, velocity=(0, -9.80665 * t, 0)) for t in (0, 1, 2)]
    with pytest.raises(ContractError, match="positive normal force"):
        sampled_support_resultants(falling, ground_height_m=0, up_axis=(0, 1, 0), forward_axis=(0, 0, 1))
    with pytest.raises(ContractError, match="up axis"):
        sampled_support_resultants([sample(t) for t in (0, 1, 2)], ground_height_m=0, up_axis=(0, 0, 0), forward_axis=(0, 0, 1))
