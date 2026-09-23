"""Finite, head-led path intent for the shared contact-planned walking task.

Authored steering intent, not a converged optimal-control trajectory. The same
anatomy, limits and contact mechanics are evaluated after limb placement.
"""
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import CubicSpline
from scipy.spatial.transform import Rotation
from .moco_tasks import smooth


class TurnPlan:
    def __init__(self, specification, duration, velocity):
        self.specification = specification
        knots = np.asarray(specification['yaw_rate_keys'], dtype=float)
        if (knots.ndim != 2 or knots.shape[1] != 2 or not np.isfinite(knots).all()
                or np.any(np.diff(knots[:, 0]) <= 0) or knots[0, 0] != 0
                or knots[-1, 0] != duration):
            raise ValueError('Yaw-rate keys must span the finite sequence in increasing time')
        self.duration = duration
        times = np.linspace(0, duration, int(duration * 1000) + 1)
        rates = np.zeros_like(times)
        for (begin, a), (end, b) in zip(knots[:-1], knots[1:]):
            mask = (times >= begin) & (times <= end)
            rates[mask] = a + (b-a)*smooth((times[mask]-begin)/(end-begin))
        heading = cumulative_trapezoid(rates, times, initial=0.)
        self.heading = CubicSpline(times, heading)
        speeds = np.asarray(velocity(times))
        forward = cumulative_trapezoid(speeds*np.cos(heading), times, initial=0.)
        lateral = cumulative_trapezoid(-speeds*np.sin(heading), times, initial=0.)
        self.position = CubicSpline(times, np.stack((forward, np.zeros_like(times), lateral), axis=-1))
        self.velocity = velocity

    def frame(self, time):
        time = np.clip(time, 0, self.duration)
        yaw = self.heading(time)
        return self.position(time), Rotation.from_rotvec([0., float(yaw), 0.]).as_matrix()

    def attention(self, time):
        lead = self.specification['attention_lookahead_s']
        return float(self.heading(min(time+lead, self.duration))-self.heading(time))

    def body_offsets(self, time, tail_count):
        """Continuous attention lead, lateral banking and delayed tail heading."""
        lead = self.attention(time)
        values = {name: share*lead for name, share in self.specification['attention_shares'].items()}
        # Gravity/centripetal resultant supplies a small lean intent. It does
        # not certify that the authored contact forces produce this motion.
        values['roll'] = -float(np.arctan(self.velocity(np.array(time))*self.heading(time, 1)/9.80665))
        delay = self.specification['tail_follow_delay_s']
        previous = float(self.heading(time))
        for i in range(tail_count):
            delayed = float(self.heading(max(0., time-delay*(i+1)/tail_count)))
            values[f'tail_{i}_yaw'] = delayed-previous
            previous = delayed
        return values
