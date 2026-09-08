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
    if u > .5:
        v=1-u
        return 1-v**3*(10+v*(-15+6*v))
    return u**3*(10+u*(-15+6*u))


def recovery_pitch(
    phase: float,
    amplitude_degrees: float,
    peak_fraction: float = .42,
    release_fraction: float = 1.0,
) -> float:
    for value in (phase, amplitude_degrees, peak_fraction, release_fraction):
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ContractError('pad recovery requires finite numeric parameters')
    # Phase subtraction at an exact contact timestamp can produce -1 ulp.
    # Admit roundoff only, not a physically different contact interval.
    if (not -1e-12 <= phase <= 1+1e-12 or not 0 <= amplitude_degrees <= 60
            or not .1 <= peak_fraction < release_fraction <= 1):
        raise ContractError(
            f'pad recovery exceeds its authored envelope: phase={phase}, amplitude={amplitude_degrees}, '
            f'peak={peak_fraction}, release={release_fraction}')
    phase = min(1., max(0., float(phase)))
    gain = (_smooth(phase/peak_fraction) if phase <= peak_fraction else
            _smooth((release_fraction-phase)/(release_fraction-peak_fraction))
            if phase < release_fraction else 0.)
    return -amplitude_degrees*gain


def _smooth_integral(u: float) -> float:
    """Integral of the quintic C2 smoothstep on its unit interval."""
    return u ** 4 * (2.5 + u * (-3 + u))


def rate_limited_recovery_gain(
    phase: float,
    peak_fraction: float,
    release_fraction: float,
) -> float:
    """A C2 recovery crown whose branch speed is capped by a linear middle.

    The historical crown uses a quintic over each entire branch, whose peak
    phase slope is 1.875 / branch-length.  This opt-in carrier ramps its
    velocity with the same quintic for a quarter of each branch, transports at
    a constant middle speed, then ramps back to zero.  With normalized branch
    coordinate x, r=.25, S the quintic smoothstep, and
    Q(z)=integral(S(z)), its value is 4rQ(x/r)/3 for x<=r,
    4(x-r/2)/3 for r<x<1-r, and its symmetric complement thereafter.  Thus
    B(0), B(r), B(1-r), B(1) = 0, 1/6, 5/6, 1;
    B' = 0, 4/3, 4/3, 0; and B'' = 0 at all four joins.  The rising crown is
    B(phase/peak); the returning crown is B((release-phase)/(release-peak)).
    Its maximum phase slope is 1 / (.75 * branch-length), while value,
    velocity, and acceleration remain continuous at lift, peak, release, and
    the two internal joins.
    """
    for value in (phase, peak_fraction, release_fraction):
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ContractError('rate-limited recovery requires finite numeric parameters')
    if not -1e-12 <= phase <= 1 + 1e-12 or not .1 <= peak_fraction < release_fraction <= 1:
        raise ContractError(
            f'rate-limited recovery exceeds its authored envelope: phase={phase}, '
            f'peak={peak_fraction}, release={release_fraction}')
    phase = min(1., max(0., float(phase)))

    def branch(progress: float) -> float:
        # Fixed rather than profile-tunable: it is a declared bounded timing
        # policy, not a second release-fraction sweep.
        ramp = .25
        speed = 1 / (1 - ramp)
        if progress <= ramp:
            return speed * ramp * _smooth_integral(progress / ramp)
        if progress < 1 - ramp:
            return speed * (.5 * ramp + progress - ramp)
        tail = (1 - progress) / ramp
        return 1 - speed * ramp * _smooth_integral(tail)

    if phase <= peak_fraction:
        return branch(phase / peak_fraction)
    if phase < release_fraction:
        return branch((release_fraction - phase) / (release_fraction - peak_fraction))
    return 0.


def signed_recovery_pitch(phase: float, pitch_degrees: float, peak_fraction: float = .42) -> float:
    """Evaluate a profile-authored signed pad pitch over the same C2 crown."""
    if isinstance(pitch_degrees, bool) or not isinstance(pitch_degrees, Real) or not math.isfinite(pitch_degrees):
        raise ContractError('signed pad recovery requires a finite numeric pitch')
    if not -60 <= pitch_degrees <= 60:
        raise ContractError('signed pad recovery exceeds its articulation envelope')
    return math.copysign(-recovery_pitch(phase, abs(pitch_degrees), peak_fraction), pitch_degrees)


def declare_pad_recovery(plan: dict) -> None:
    """Annotate an already-private plan copy, never historical input assets."""
    parameters=plan.get('parameters',{})
    amplitude=parameters.get('foot_recovery_pitch_degrees',0.)
    signed_pitch=parameters.get('pad_recovery_pitch_degrees')
    peak=parameters.get('swing_recovery_peak_fraction',.42)
    if signed_pitch is not None:
        # Validate the declared policy even for a degenerate all-contact plan.
        signed_recovery_pitch(0.,signed_pitch,peak if peak else .5)
    # Existing zero sentinel denotes an unshifted mid-swing recovery.
    if peak == 0 and not isinstance(peak, bool):
        peak = .5
    for row in plan['samples']:
        for foot in row['feet'].values():
            scale=foot.get('articulation_scale',1.)
            if isinstance(scale,bool) or not isinstance(scale,Real) or not math.isfinite(scale) or not 0<=scale<=1:
                raise ContractError('pad recovery scale must be finite in [0,1]')
            foot['pad_pitch_degrees']=(0. if foot['contact'] else scale * (
                recovery_pitch(foot['swing_phase'],amplitude,peak) if signed_pitch is None
                else signed_recovery_pitch(foot['swing_phase'],signed_pitch,peak)))
