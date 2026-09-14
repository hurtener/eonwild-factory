"""Shared anticipatory neck/head coordination for authored directional paths."""
import math
import numpy as np
from .airborne_gait import _qrotvec, _qrotate, _qinv, _qmul
from ..layers.leg_contact_resolve_v3 import _rotation_from_matrix


def turn_look_yaw(sequence, time_s, lead_seconds, maximum_degrees, anticipation_gain=1.):
    """Look toward the upcoming heading, then settle as the body catches up."""
    current = sequence.body(time_s)[1]
    # Anticipate the current turn without looking into the following reversal
    # prematurely. The anticipation onset itself eases in continuously.
    from ..planning.grounded_gait import smooth
    block = next((b for b in reversed(sequence.blocks) if time_s >= b['start']-.8), sequence.blocks[0])
    onset = smooth((time_s-(block['start']-.8))/.8)
    future = sequence.body(min(block['end'],time_s + lead_seconds))[1]
    difference = math.atan2(math.sin(future-current), math.cos(future-current))
    limit = math.radians(maximum_degrees)
    # Soft saturation preserves smooth velocity when attention reaches its range.
    return onset * limit * math.tanh(anticipation_gain * difference / limit) if limit > 0 else 0.0


def apply_turn_attention(context, rotations, yaw_radians, neck_share):
    """Distribute world-up yaw along semantic neck joints and the head.

    Apply before the final leg/contact evaluation. There is no species branch
    and no runtime-camera dependency. Rotations supplied here are source-local.
    """
    neck = list(context.roles.get('neck', []))
    head = context.roles.get('head')
    if not neck or not head:
        raise ValueError('turn attention requires semantic neck and head bindings')
    if not 0 <= neck_share <= 1:
        raise ValueError('invalid turn attention neck share')
    for name, share in [(n, neck_share/len(neck)) for n in neck] + [(head, 1-neck_share)]:
        node = context.source.name_to_node[name]
        axis = np.asarray(_qrotate(_qinv(_rotation_from_matrix(context.base_w[node])), context.up))
        rotations[node] = _qmul(rotations[node], _qrotvec(axis*yaw_radians*share))
