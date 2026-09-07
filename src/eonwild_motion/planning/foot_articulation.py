"""Independent contact-pad recovery, separate from metatarsal push-off.

The metatarsal's late-stance extension must not become a downward rotation of
an unloaded flat pad at the instant of lift. Author a separate, C2 pad arc
from level support through recovery and back to level pre-contact. The limb
solver and final skin evaluation still own reach, grounding and slip checks.
"""
from __future__ import annotations
import math
from numbers import Real
from ..errors import ContractError
from .grounded_gait import smooth


def recovery_pitch(phase: float, amplitude_degrees: float, peak_fraction: float = .42) -> float:
    for value in (phase, amplitude_degrees, peak_fraction):
        if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value):
            raise ContractError('pad recovery requires finite numeric parameters')
    if not 0<=phase<=1 or not 0<=amplitude_degrees<=60 or not .1<=peak_fraction<=.9:
        raise ContractError('pad recovery exceeds its authored envelope')
    gain=(smooth(phase/peak_fraction) if phase<=peak_fraction
          else 1-smooth((phase-peak_fraction)/(1-peak_fraction)))
    return -amplitude_degrees*gain


def declare_pad_recovery(plan: dict) -> None:
    """Annotate an already private plan copy; never mutate reference assets."""
    parameters=plan.get('parameters',{})
    amplitude=parameters.get('foot_recovery_pitch_degrees',0.)
    peak=parameters.get('swing_recovery_peak_fraction',.42)
    for row in plan['samples']:
        for foot in row['feet'].values():
            scale=foot.get('articulation_scale',1.)
            if isinstance(scale,bool) or not isinstance(scale,Real) or not math.isfinite(scale) or not 0<=scale<=1:
                raise ContractError('pad recovery scale must be finite in [0,1]')
            foot['pad_pitch_degrees']=(0. if foot['contact'] else
                recovery_pitch(foot['swing_phase'],amplitude,peak)*scale)
