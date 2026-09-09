"""Typed persistent-support behavior programs, independent of experiment scripts.

Channels describe an authored performance, not reconstructed forces. Lengths
are expressed against admitted hip height; semantic chains conserve signed
angular increments when their joint counts differ.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
import re

import numpy as np

from ..errors import ContractError


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ContractError(f'{label} must be finite numeric')
    return float(value)


@dataclass(frozen=True)
class Anchor:
    enter: float
    capture: float
    resisted_end: float
    release: float
    tolerance_m: float
    offset_body_heights: tuple = (0., 0., 0.)

    def validate(self, duration):
        for value in (self.enter, self.capture, self.resisted_end, self.release, self.tolerance_m, *self.offset_body_heights):
            _number(value, 'oral phase or offset')
        if not 0 <= self.enter < self.capture < self.resisted_end < self.release <= duration:
            raise ContractError('oral phases must be ordered')
        if not 0 < self.tolerance_m <= .002 or len(self.offset_body_heights) != 3 or np.linalg.norm(self.offset_body_heights) > .5:
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
    translation_scale_body_heights: tuple = (1., 1., 1.)
    support_reach_body_heights: tuple = (0., 0.)


def curve(time, keys):
    """Shape-preserving cubic Hermite; endpoints/extrema have zero velocity."""
    time = _number(time, 'channel time')
    try:
        for row in keys:
            if len(row) != 2:
                raise ContractError('channel needs time/value pairs')
            for value in row:
                _number(value, 'channel value')
        rows = np.asarray(keys, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ContractError('channel needs finite time/value pairs') from exc
    if rows.ndim != 2 or rows.shape[1] != 2 or len(rows) < 2:
        raise ContractError('channel needs finite time/value pairs')
    dt = np.diff(rows[:, 0])
    if np.any(dt <= 0):
        raise ContractError('channel times must increase strictly')
    slopes = np.diff(rows[:, 1]) / dt
    tangent = np.zeros(len(rows))
    for i in range(1, len(rows) - 1):
        if slopes[i - 1] * slopes[i] > 0:
            w1, w2 = 2 * dt[i] + dt[i - 1], dt[i] + 2 * dt[i - 1]
            tangent[i] = (w1 + w2) / (w1 / slopes[i - 1] + w2 / slopes[i])
    if time <= rows[0, 0]:
        return float(rows[0, 1])
    if time >= rows[-1, 0]:
        return float(rows[-1, 1])
    i = int(np.searchsorted(rows[:, 0], time, side='right') - 1)
    u = (time - rows[i, 0]) / dt[i]
    return float((2 * u**3 - 3 * u**2 + 1) * rows[i, 1]
        + (u**3 - 2 * u**2 + u) * dt[i] * tangent[i]
        + (-2 * u**3 + 3 * u**2) * rows[i + 1, 1]
        + (u**3 - u**2) * dt[i] * tangent[i + 1])


def resample_chain(values, count):
    """Conserve total signed rotation through normalized segment overlap."""
    if type(count) is not int or not 1 <= count <= 128:
        raise ContractError('invalid semantic chain size')
    try:
        values = np.asarray([_number(v, 'chain angle') for v in values], dtype=float)
    except TypeError as exc:
        raise ContractError('invalid semantic chain weights') from exc
    if values.ndim != 1 or not len(values):
        raise ContractError('invalid semantic chain weights')
    if count == len(values):
        return values.copy()
    # Midpoint interpolation does not preserve nonuniform or signed sums.
    left = np.maximum(np.arange(count)[:, None] / count, np.arange(len(values))[None, :] / len(values))
    right = np.minimum((np.arange(count)[:, None] + 1) / count, (np.arange(len(values))[None, :] + 1) / len(values))
    return np.maximum(0., right - left) @ (values * len(values))


def load_supported_action(document):
    allowed = {'schema', 'duration_seconds', 'sample_hz', 'reference_duration_seconds', 'loop', 'gape_degrees',
        'max_joint_rate_degrees_per_second', 'lane_width_body_heights', 'base_pitch_degrees', 'yaw_weights', 'channels',
        'support_limits', 'joint_pitch_limits_degrees', 'anchor', 'events', 'reference_basis', 'classification',
        'translation_scale_body_heights', 'support_reach_body_heights'}
    if not isinstance(document, dict) or document.get('schema') != 'eonwild.motion.supported-action.v1' or set(document) - allowed:
        raise ContractError('unsupported persistent-support profile')
    try:
        duration = _number(document['duration_seconds'], 'duration')
        reference = _number(document['reference_duration_seconds'], 'reference duration')
        hz, loop = document['sample_hz'], document['loop']
        gape = _number(document['gape_degrees'], 'gape')
        rate = _number(document['max_joint_rate_degrees_per_second'], 'joint rate')
        lane = _number(document['lane_width_body_heights'], 'stance width')
        if type(hz) is not int or not 24 <= hz <= 240 or type(loop) is not bool:
            raise ContractError('invalid supported timeline')
        if not 0 < duration <= 30 or not 0 < reference <= 30 or not 0 <= gape <= 60 or not 0 < rate <= 1200 or not .1 <= lane <= .6:
            raise ContractError('supported profile exceeds the family envelope')
        channel_bounds = {'body': (-1., 2.), 'drop': (-.15, .4), 'forward': (-.4, .4), 'lateral': (-.15, .15),
                          'yaw': (-45., 45.), 'jaw': (0., 1.), 'tail': (-2., 2.)}
        if not isinstance(document['channels'], dict) or set(document['channels']) != set(channel_bounds):
            raise ContractError('supported channels are incomplete')
        channels = {}
        for name, keys in document['channels'].items():
            curve(0., keys)
            if keys[0][0] != 0 or keys[-1][0] != reference:
                raise ContractError('channel must span the reference timeline')
            if loop and keys[0][1] != keys[-1][1]:
                raise ContractError('loop channel does not close')
            low, high = channel_bounds[name]
            if any(not low <= row[1] <= high for row in keys):
                raise ContractError(f'{name} channel exceeds its bounded envelope')
            channels[name] = tuple(tuple(float(v) for v in row) for row in keys)
        roles = {'pelvis', 'spine', 'chest', 'neck', 'head', 'tail'}
        if not isinstance(document['base_pitch_degrees'], dict) or set(document['base_pitch_degrees']) != roles:
            raise ContractError('supported pitch roles are incomplete')
        base = {}
        for role, values in document['base_pitch_degrees'].items():
            checked = resample_chain(values, len(values))
            if np.max(np.abs(checked)) > 180:
                raise ContractError('base pitch exceeds the angular envelope')
            base[role] = tuple(float(v) for v in checked)
        yaw = document['yaw_weights']
        if not isinstance(yaw, dict) or set(yaw) - roles:
            raise ContractError('unknown supported yaw role')
        yaw = {k: _number(v, 'yaw weight') for k, v in yaw.items()}
        if any(abs(v) > 2 for v in yaw.values()):
            raise ContractError('yaw weight exceeds the family envelope')
        limits = document['support_limits']
        if not isinstance(limits, dict) or set(limits) != {'knee_interior_degrees', 'ankle_interior_degrees', 'hip_sagittal_degrees'}:
            raise ContractError('support articulation limits are incomplete')
        limits = {k: tuple(_number(v, 'support limit') for v in row) for k, row in limits.items()}
        if any(len(row) != 2 or not -180 <= row[0] < row[1] <= 180 for row in limits.values()):
            raise ContractError('invalid support articulation interval')
        body_limits = document['joint_pitch_limits_degrees']
        if not isinstance(body_limits, dict) or set(body_limits) != roles - {'tail'}:
            raise ContractError('body articulation limits are incomplete')
        body_limits = {k: tuple(tuple(_number(v, 'body limit') for v in row) for row in rows) for k, rows in body_limits.items()}
        if any(not rows or len(rows) > 128 or any(len(row) != 2 or not -180 <= row[0] < row[1] <= 180 for row in rows) for rows in body_limits.values()):
            raise ContractError('invalid body articulation interval')
        scales = tuple(_number(v, 'translation scale') for v in document.get('translation_scale_body_heights', (1., 1., 1.)))
        reach = tuple(_number(v, 'support reach') for v in document.get('support_reach_body_heights', (0., 0.)))
        if len(scales) != 3 or any(not 0 < v <= 8 for v in scales) or len(reach) != 2 or any(abs(v) > .5 for v in reach):
            raise ContractError('invalid normalized support calibration')
        anchor = None
        if document.get('anchor') is not None:
            payload = dict(document['anchor'])
            if 'offset_body_heights' in payload:
                payload['offset_body_heights'] = tuple(payload['offset_body_heights'])
            anchor = Anchor(**payload)
            anchor.validate(reference)
        events, seen, previous = [], set(), -1.
        for event in document['events']:
            if not isinstance(event, dict) or set(event) != {'name', 'reference_time_seconds'}:
                raise ContractError('invalid animation cue')
            name = event['name']
            time = _number(event['reference_time_seconds'], 'event time')
            if not isinstance(name, str) or re.fullmatch(r'[A-Z][A-Z0-9_]{1,63}', name) is None or not 0 <= time <= reference or time < previous or (time, name) in seen:
                raise ContractError('invalid, duplicate, or unordered animation cue')
            events.append({'name': name, 'reference_time_seconds': time})
            previous = time
            seen.add((time, name))
        return SupportedAction(duration, hz, reference, loop, gape, rate, lane, base, yaw, channels,
            limits, body_limits, anchor, tuple(events), scales, reach)
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f'invalid persistent-support profile: {exc}') from exc
