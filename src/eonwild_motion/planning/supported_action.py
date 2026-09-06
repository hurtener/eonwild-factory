"""Persistent-support performance channels, extracted from V9 Feeding003.

Waypoints carry velocity; grip and release are separate phases. No locomotion
schedule, prior animation file, or historical experiment module is used here.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import math
import numpy as np
from ..errors import ContractError


@dataclass(frozen=True)
class Anchor:
    enter: float
    capture: float
    resisted_end: float
    release: float
    tolerance_m: float = .002
    offset_body_heights: tuple = (0., 0., 0.)

    def validate(self, duration):
        values = [self.enter, self.capture, self.resisted_end, self.release, self.tolerance_m, *self.offset_body_heights]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ContractError('oral phases require finite numbers')
        if not 0 <= self.enter < self.capture < self.resisted_end < self.release <= duration:
            raise ContractError('oral phases must be ordered')
        if not 0 < self.tolerance_m <= .002 or len(self.offset_body_heights) != 3:
            raise ContractError('invalid oral tolerance or target offset')


@dataclass(frozen=True)
class SupportedAction:
    duration_seconds: float
    sample_hz: int
    reference_duration_seconds: float
    loop: bool
    gape_degrees: float
    max_joint_rate_degrees_per_second: float
    lane_width_body_heights: float
    base_pitch_degrees: dict
    yaw_weights: dict
    channels: dict
    support_limits: dict
    joint_pitch_limits_degrees: dict
    anchor: Anchor | None
    events: tuple


def curve(time, keys):
    """Shape-preserving cubic Hermite; endpoints/extrema have zero velocity."""
    rows = np.asarray(keys, dtype=float)
    if rows.ndim != 2 or rows.shape[1] != 2 or len(rows) < 2 or not np.isfinite(rows).all():
        raise ContractError('channel needs finite time/value pairs')
    x, y = rows[:, 0], rows[:, 1]
    h = np.diff(x)
    if (h <= 0).any():
        raise ContractError('channel times must strictly increase')
    sec = np.diff(y) / h
    tangent = np.zeros(len(x))
    for i in range(1, len(x) - 1):
        if sec[i-1] * sec[i] > 0:
            w1, w2 = 2*h[i] + h[i-1], h[i] + 2*h[i-1]
            tangent[i] = (w1+w2) / (w1/sec[i-1] + w2/sec[i])
    if time <= x[0]: return float(y[0])
    if time >= x[-1]: return float(y[-1])
    i = int(np.searchsorted(x, time, side='right') - 1)
    u = (time - x[i]) / h[i]
    return float((2*u**3-3*u**2+1)*y[i] + (u**3-2*u**2+u)*h[i]*tangent[i]
                 + (-2*u**3+3*u**2)*y[i+1] + (u**3-u**2)*h[i]*tangent[i+1])


def resample_chain(values, count):
    """Preserve total authored rotation when a semantic chain changes size."""
    values = np.asarray(values, dtype=float)
    if count < 1 or values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ContractError('invalid semantic chain weights')
    if count == len(values): return values.copy()
    values = np.interp((np.arange(count)+.5)/count, (np.arange(len(values))+.5)/len(values), values) * len(values)/count
    return values


def load_supported_action(document):
    allowed = {'schema','duration_seconds','sample_hz','reference_duration_seconds','loop','gape_degrees',
        'max_joint_rate_degrees_per_second','lane_width_body_heights','base_pitch_degrees','yaw_weights','channels',
        'support_limits','joint_pitch_limits_degrees','anchor','events','reference_basis','classification'}
    if not isinstance(document, dict) or document.get('schema') != 'eonwild.motion.supported-action.v1' or set(document) - allowed:
        raise ContractError('unsupported persistent-support profile')
    try:
        data = deepcopy(document)
        duration = data['duration_seconds']; reference = data.get('reference_duration_seconds', 6.)
        hz = data.get('sample_hz', 60); loop = data.get('loop', False)
        if type(loop) is not bool or type(hz) is not int or not 24 <= hz <= 240:
            raise ContractError('invalid timing or loop flag')
        for value in (duration, reference, data['gape_degrees'], data['max_joint_rate_degrees_per_second'], data['lane_width_body_heights']):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ContractError('invalid supported scalar')
        if not 0 < duration <= 30 or not 0 < reference <= 30 or not 0 <= data['gape_degrees'] <= 60 or not 0 < data['max_joint_rate_degrees_per_second'] <= 1200:
            raise ContractError('supported recipe exceeds duration/gape/rate envelope')
        if not .1 <= data['lane_width_body_heights'] <= .6:
            raise ContractError('unsupported stance width')
        if set(data['channels']) != {'body','drop','forward','lateral','yaw','jaw','tail'}:
            raise ContractError('supported channels are incomplete')
        channels = {}
        for name, keys in data['channels'].items():
            curve(0, keys)
            if keys[0][0] != 0 or keys[-1][0] != reference:
                raise ContractError('channel must span the reference timeline')
            if loop and keys[0][1] != keys[-1][1]: raise ContractError('loop channel does not close')
            if name == 'jaw' and any(not 0 <= row[1] <= 1 for row in keys): raise ContractError('jaw fraction outside [0,1]')
            channels[name] = tuple(tuple(row) for row in keys)
        roles = {'pelvis','spine','chest','neck','head','tail'}
        if set(data['base_pitch_degrees']) != roles or set(data['yaw_weights']) - roles:
            raise ContractError('unsupported semantic body roles')
        for values in data['base_pitch_degrees'].values(): resample_chain(values, len(values))
        anchor = Anchor(**data['anchor']) if data.get('anchor') else None
        if anchor: anchor.validate(reference)
        limits = data['support_limits']
        if set(limits) != {'knee_interior_degrees','ankle_interior_degrees','hip_sagittal_degrees'}:
            raise ContractError('missing support limits')
        for bounds in limits.values():
            if len(bounds) != 2 or not all(math.isfinite(v) for v in bounds) or bounds[0] >= bounds[1]:
                raise ContractError('invalid support envelope')
        body_limits = data['joint_pitch_limits_degrees']
        if set(body_limits) != roles - {'tail'}: raise ContractError('missing body limits')
        for rows in body_limits.values():
            if not rows or any(len(b) != 2 or not all(math.isfinite(v) for v in b) or b[0] >= b[1] for b in rows):
                raise ContractError('invalid body envelope')
        events = tuple(data.get('events', []))
        for event in events:
            if set(event) != {'name','reference_time_seconds'} or not isinstance(event['name'],str) or not event['name'] or not 0 <= event['reference_time_seconds'] <= reference:
                raise ContractError('invalid action cue')
        return SupportedAction(duration,hz,reference,loop,data['gape_degrees'],data['max_joint_rate_degrees_per_second'],data['lane_width_body_heights'],
            data['base_pitch_degrees'],data['yaw_weights'],channels,limits,body_limits,anchor,events)
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        raise ContractError(f'malformed supported profile: {exc}') from exc
