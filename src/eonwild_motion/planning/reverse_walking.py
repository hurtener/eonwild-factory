"""Authored grounded backward release, recovery and attention controls.

Placement and support timing use the shared step planner. This behavior owns
its reduced release and toe/metatarsal envelope; no forward clip is reversed.
"""
import math
from .grounded_gait import smooth
from .foot_articulation import recovery_pitch


def reverse_articulation(phase, contact, roll, policy):
    crown = -recovery_pitch(phase, 1., .44, .94) if not contact else 0.
    return {
        'toe_flex_degrees': policy['toe_curl_degrees'] * crown,
        'foot_pitch_degrees': roll + policy['metatarsal_pitch_degrees'] * crown,
        'articulation_scale': .35,
        'walking_knee_preference_degrees': policy['knee_extension_preference_degrees'],
    }


def reverse_attention(sequence, time, policy):
    """Look before retreat, keep awareness during steps, then settle forward."""
    end=sequence.blocks[-1]['end']
    gain=smooth(time/.8)*(1-smooth((time-(end-.5))/.95))
    return math.radians(policy['look_degrees'])*policy['look_side']*gain
