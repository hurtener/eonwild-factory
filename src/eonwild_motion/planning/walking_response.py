"""Authored purposeful walking response, independent of body travel speed."""


def recovery_window(event, walking):
    """Spend extra time supporting weight, preserving a walking swing duration."""
    duration = event['duration']
    recovery = walking.get('recovery_seconds') if not event['block']['stationary'] else None
    span = min(.8, recovery / duration) if recovery else .8
    lift = .1 + (.8-span)*.25
    return lift, lift+span


def moving_articulation(weight, minimum, preparation=1.):
    """A committed moving foot retains articulation as body speed changes."""
    return preparation * (minimum + (1 - minimum) * weight)
