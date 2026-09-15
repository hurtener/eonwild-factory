"""Authored purposeful walking response, independent of body travel speed."""


def recovery_window(event, walking):
    """Spend extra time supporting weight, preserving a walking swing duration."""
    if 'recovery_window' in event:
        import math
        lift, touch = event['recovery_window']
        if not all(math.isfinite(v) for v in (lift, touch)) or not 0 <= lift < touch <= 1:
            raise ValueError('Explicit recovery window requires 0 <= lift < touch <= 1')
        return lift, touch
    duration = event['duration']
    recovery = walking.get('recovery_seconds') if not event['block']['stationary'] else None
    span = min(.8, recovery / duration) if recovery else .8
    lift = .1 + (.8-span)*.25
    return lift, lift+span


def support_transfer_times(event, walking, transfer_fraction):
    """One release clock for foot contact and planned support.

    Unexpected events can forbid anticipation before their physical trigger.
    The default is the existing anticipatory walking/turning transfer.
    """
    d = event['duration']
    a, b = recovery_window(event, walking)
    lift, touch = event['start']+a*d, event['start']+b*d
    start = max(lift-transfer_fraction*d,
                event.get('load_release_not_before_s', -float('inf')))
    if start >= lift:
        raise ValueError('Support release must begin before foot lift')
    return start, lift, touch, touch+transfer_fraction*d


def moving_articulation(weight, minimum, preparation=1.):
    """A committed moving foot retains articulation as body speed changes."""
    return preparation * (minimum + (1 - minimum) * weight)
