"""Current-rig running choreography over the shared airborne gait family.

Speeds and stride are authored animal inputs, not mass-derived biology.
The cyclic gait owns loading, push-off and recovery; consumers own entry state.
"""
import math
from .airborne_gait import AirborneGait, sample_airborne_gait
from .grounded_gait import smooth


def resolve_running(profile, recipe):
    values = profile['locomotion']['run']
    for key, unit in [('preferredSpeed', 'm/s'), ('stepLength', 'm'), ('sameFootStride', 'm')]:
        item = values[key]
        if (item['unit'] != unit or isinstance(item['value'], bool)
                or not math.isfinite(item['value']) or item['value'] <= 0
                or not item.get('source', {}).get('citation')):
            raise ValueError('Invalid running input: ' + key)
    speed, step, stride = (values[k]['value'] for k in ('preferredSpeed', 'stepLength', 'sameFootStride'))
    if not math.isclose(stride, 2 * step):
        raise ValueError('A running stride must contain two alternating steps')
    height = profile['authoring']['bodyHeightM']
    reach_fraction = recipe.get('touchdown_reach_step_fraction', .5)
    if (isinstance(reach_fraction, bool) or not isinstance(reach_fraction, (int, float))
            or not math.isfinite(reach_fraction)
            or not 0 < reach_fraction < 1):
        raise ValueError('Running touchdown reach must be a fraction of one step')
    return AirborneGait(**recipe['parameters'], step_period_s=step / speed,
                       step_length_body_heights=step / height,
                       touchdown_reach_body_heights=reach_fraction * step / height)


def running_sample(gait, time_s, height):
    row = sample_airborne_gait(gait, time_s, height)
    for foot in row['feet'].values():
        u = foot['swing_phase']
        # The distal pad continues heel release while the metatarsal folds.
        # Its shape is never flattened simply because the animal is airborne.
        foot['distal_endpoint_role'] = 'shape_preference'
        if not foot['contact']:
            foot['stance_roll_swing_pitch_degrees'] = gait.push_off_pitch_degrees * (1 - smooth(u / .42))
            foot['pad_pitch_degrees'] = 10 * math.sin(math.pi * u) ** 2
            # Running coordinates recovery through the hip objective and
            # foot trajectory. An additional world-metatarsal target held
            # the ankle at its flexion limit while the knee kept moving.
    return row
