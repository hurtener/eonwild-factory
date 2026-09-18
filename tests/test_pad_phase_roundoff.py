import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.foot_articulation import recovery_pitch


def test_contact_timestamp_arithmetic_roundoff_is_not_a_new_swing():
    assert recovery_pitch(-2.22e-16,28)==0
    assert recovery_pitch(1+2.22e-16,28)==0


@pytest.mark.parametrize('phase',[-1e-10,1+1e-10])
def test_genuinely_out_of_interval_phase_still_rejects(phase):
    with pytest.raises(ContractError):recovery_pitch(phase,28)
