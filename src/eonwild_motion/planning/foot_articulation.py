"""Contact-pad recovery independent of the metatarsal's push-off extension.

A planted pad begins and ends swing level. The metatarsal may continue its
late-stance extension while the pad recovers through its own C2 arc. All
anatomical, rate, final skin and cyclic checks remain mandatory and unchanged.
"""
from __future__ import annotations
import math
from numbers import Real
from ..errors import ContractError


def _smooth(u: float) -> float:
    # Complementary evaluation avoids subtractive cancellation at u≈1.
    if u > .5:
        v=1-u
        return 1-v**3*(10+v*(-15+6*v))
    return u**3*(10+u*(-15+6*u))


def recovery_pitch(phase: float, amplitude_degrees: float, peak_fraction: float = .42) -> float:
    for value in (phase, amplitude_degrees, peak_fraction):
        if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value):
            raise ContractError('pad recovery requires finite numeric parameters')
    if not 0<=phase<=1 or not 0<=amplitude_degrees<=60 or not .1<=peak_fraction<=.9:
        raise ContractError('pad recovery exceeds its authored envelope')
    # Evaluate recovery toward zero from its small argument, preserving the
    # exact zero boundary instead of subtracting two almost-equal floats.
    gain=(_smooth(phase/peak_fraction) if phase<=peak_fraction
          else _smooth((1-phase)/(1-peak_fraction)))
    return -amplitude_degrees*gain


def declare_pad_recovery(plan: dict) -> None:
    """Annotate an already-private plan copy, never historical input assets."""
    parameters=plan.get('parameters',{})
    amplitude=parameters.get('foot_recovery_pitch_degrees',0.)
    peak=parameters.get('swing_recovery_peak_fraction',.42)
    # AirborneGait's existing zero sentinel denotes an unshifted mid-swing
    # recovery. It is not a request to place the crown outside (0,1).
    if peak == 0 and not isinstance(peak,bool):
        peak=.5
    for row in plan['samples']:
        for foot in row['feet'].values():
            scale=foot.get('articulation_scale',1.)
            if isinstance(scale,bool) or not isinstance(scale,Real) or not math.isfinite(scale) or not 0<=scale<=1:
                raise ContractError('pad recovery scale must be finite in [0,1]')
            foot['pad_pitch_degrees']=(0. if foot['contact'] else
                recovery_pitch(foot['swing_phase'],amplitude,peak)*scale)
