"""Source-owned walk sequence; cadence changes preserve planted placements."""
from copy import deepcopy
import math
from .gait_transition import GaitTransition, _Choreography, _smooth_integral
from .grounded_gait import sample_grounded_gait, smooth
from .foot_articulation import declare_pad_recovery_sample


class WalkSequence:
    def __init__(self, gait, height, parameters, faster_rate=1.35):
        if not math.isfinite(faster_rate) or not 1 < faster_rate <= 1.5:
            raise ValueError('faster walking cadence must be in (1, 1.5]')
        self.gait, self.height, self.parameters = gait, height, deepcopy(parameters)
        self.period = 2 * gait.step_period_s
        self.rate = faster_rate
        self.start = _Choreography(GaitTransition('start', ramp_cycles=1,
            anticipation_seconds=.8, idle_crouch_body_heights=.025,
            support_placement='integrated_support'), gait, height)
        self.stop = _Choreography(GaitTransition('stop', ramp_cycles=1,
            settle_seconds=.8, idle_crouch_body_heights=.025,
            support_placement='integrated_support'), gait, height)
        self.ramp_duration = self.period / ((1 + self.rate) / 2)
        lengths = [self.start.duration, self.period, self.ramp_duration,
                   self.period / self.rate, self.ramp_duration, self.stop.duration]
        self.bounds = [0.]
        for length in lengths: self.bounds.append(self.bounds[-1] + length)
        self.duration = self.bounds[-1]
        self.speed = self.start.speed
        self.start_distance = self.start.sample(self.start.duration)['root_forward_m']
        self.stages = ['idle/start walking', 'normal walk', 'speed up',
                       'faster walk', 'slow down', 'stop/idle']

    def sample(self, time):
        if not 0 <= time <= self.duration + 1e-8: raise ValueError('sequence time outside domain')
        stage = min(5, next((i for i in range(6) if time < self.bounds[i+1]), 5))
        local = time - self.bounds[stage]
        if stage == 0:
            row = self.start.sample(local)
        elif stage == 5:
            row = self.stop.sample(local)
            displacement = self.start_distance + 4*self.period*self.speed
            row['root_forward_m'] += displacement
            for foot in row['feet'].values(): foot['forward_m'] += displacement
        else:
            if stage in (1, 3):
                rate = 1. if stage == 1 else self.rate
                clock = (stage-1)*self.period + local*rate
            else:
                initial, final = (1., self.rate) if stage == 2 else (self.rate, 1.)
                u = min(1., max(0., local / self.ramp_duration))
                rate = initial + (final-initial)*smooth(u)
                clock = (stage-1)*self.period + self.ramp_duration*(initial*u+(final-initial)*_smooth_integral(u))
            row = sample_grounded_gait(self.gait, clock, self.height)
            row['locomotion_time_s'] = clock % self.period
            row['performance_gain'] = 1.
            row['root_velocity_mps'] = self.speed*rate
            row['root_forward_m'] += self.start_distance
            for foot in row['feet'].values(): foot['forward_m'] += self.start_distance
        row['time_s'] = float(time)
        row['sequence_stage'] = self.stages[stage]
        declare_pad_recovery_sample(self.parameters, row)
        return row
