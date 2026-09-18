"""Contact-owned swing transport with finite acceleration and fixed endpoints.

A minimum-jerk *position* curve spends much of a short, fast swing barely
moving, then races through its centre. The root keeps moving meanwhile. A
bounded ramp in *velocity* starts transport earlier and catches it later,
without changing either touchdown, step length, contact time or root speed.
This is authored kinematic coordination, not muscle or force simulation.
"""
from __future__ import annotations

import math
from numbers import Real

from ..errors import ContractError


def validate_transport_ramp(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ContractError('swing transport ramp must be finite numeric')
    if value != 0 and not .06 <= value <= .45:
        raise ContractError('swing transport ramp must be zero (legacy) or in [.06, .45]')


def _integrated_ramp(u: float) -> float:
    # Integral of quintic smoothstep, from zero to u. I(1) = 1/2.
    return u**4 * (2.5 + u * (-3.0 + u))


def transport_progress(phase: float, ramp_fraction: float) -> float:
    """Monotone unit transport, with zero velocity/acceleration at contact.

    Nonzero ramps integrate smoothstep velocity into an exact unit distance.
    The plateau velocity is 1/(1-ramp_fraction), not an extra distance gain.
    At both ramp/plateau joins position and its first three derivatives agree.
    The zero sentinel retains the historical quintic-position evaluation.
    """
    validate_transport_ramp(ramp_fraction)
    if isinstance(phase, bool) or not isinstance(phase, Real) or not math.isfinite(phase):
        raise ContractError('swing transport phase must be finite numeric')
    if not -1e-12 <= phase <= 1 + 1e-12:
        raise ContractError('swing transport phase must lie in [0, 1]')
    u = min(1.0, max(0.0, float(phase)))
    if not ramp_fraction:
        return u * u * u * (10 + u * (-15 + 6 * u))
    a = float(ramp_fraction)
    if u < a:
        return a * _integrated_ramp(u / a) / (1 - a)
    if u > 1 - a:
        return 1 - a * _integrated_ramp((1 - u) / a) / (1 - a)
    return (u - a * .5) / (1 - a)
