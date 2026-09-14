"""Animal-owned attention envelopes; angles are whole-head headings in degrees.

These are authored reconstruction limits, not measured biological hard stops.
Target selection and any requested body turn belong to the behavior/motor.
"""
import math
from copy import deepcopy

CONTRACT = 'eonwild.attention-envelope.v1'


def resolve_attention(profile):
    a = deepcopy(profile['attention'])
    e = a.get('envelope')
    if e is None:
        return None  # Preserved profiles reproduce the historical law.
    if e.get('contract') != CONTRACT:
        raise ValueError('Unsupported attention envelope')
    values = [e[k] for k in ('normalDegrees', 'scanDegrees', 'strongDegrees',
                            'maximumDegrees', 'hardDegrees')]
    if (not all(isinstance(x, (int, float)) and not isinstance(x, bool) and
                math.isfinite(x) for x in values) or
            not 0 < values[0] <= values[1] <= values[2] < values[3] <= values[4] < 90):
        raise ValueError('Invalid attention envelope ranges')
    weights = e['neckWeights']
    if (len(weights) != len(profile['neckRoles']) or not weights or
            any(not math.isfinite(w) or w <= 0 for w in weights) or
            not math.isclose(sum(weights), 1., abs_tol=1e-6)):
        raise ValueError('Attention neck weights must match ordered semantic roles and sum to one')
    if (not 0 < a['neckShare'] < 1 or not 0 < e['bodyFollowStartDegrees'] < e['maximumDegrees'] or
            a['yawLimit'] != e['maximumDegrees']):
        raise ValueError('Invalid attention distribution or runtime limit')
    if not e.get('classification') or not e.get('source'):
        raise ValueError('Attention envelope requires provenance')
    return a


def attention_intent(mode, attention):
    """Resolve a behavior's named glance without copying animal angles into it."""
    fields = {'none': None, 'normal': 'normalDegrees', 'scan': 'scanDegrees',
              'strong': 'strongDegrees', 'exceptional': 'hardDegrees'}
    if mode not in fields:
        raise ValueError('Unsupported attention intent')
    key = fields[mode]
    return {'requestedDegrees': attention['envelope'][key] if key else 0.,
            'exceptional': mode == 'exceptional'}


def bound_attention(requested_degrees, attention, exceptional=False):
    """Identity through strong range, then C1 saturation toward the selected cap.

    Body-follow output is an unfulfilled heading request, never root motion.
    Ordinary movement cannot enter the exceptional range by accident.
    """
    if not math.isfinite(requested_degrees):
        raise ValueError('Non-finite attention target')
    e = attention['envelope']
    cap = e['hardDegrees'] if exceptional else e['maximumDegrees']
    soft = e['strongDegrees']
    size = abs(requested_degrees)
    yaw = size if size <= soft else soft + (cap-soft)*math.tanh((size-soft)/(cap-soft))
    yaw = math.copysign(yaw, requested_degrees)
    return {'yawDegrees': yaw, 'unfulfilledYawDegrees': requested_degrees-yaw,
            'bodyFollowDegrees': math.copysign(max(0., size-e['bodyFollowStartDegrees']), requested_degrees)}


def attention_vectors(attention):
    return [dict(requestedDegrees=x, exceptional=exceptional,
                 **bound_attention(x, attention, exceptional))
            for exceptional in (False, True)
            for x in (-180., -85., -70., -60., -55., -45., -35., 0., 35., 45., 55., 60., 70., 85., 180.)]
