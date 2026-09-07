"""Reusable acceleration/arrest programs with immutable stance anchors.

This is kinematic choreography, not a force model. Root speed is integrated
analytically; foot placements are committed at touchdown, never dragged by a
speed blend. Low-speed airborne transitions retain double support before
joining the authored running regime. No historical take or script is loaded.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from numbers import Real

import numpy as np

from ..errors import ContractError
from .swing_transport import transport_progress
from .airborne_gait import AirborneGait, sample_airborne_gait, sampled_handoff_phase
from .grounded_gait import GroundedGait, sample_grounded_gait, smooth, touchdown_reach
from .parameters import gait_parameters


@dataclass(frozen=True)
class GaitTransition:
    kind: str
    ramp_cycles: int = 2
    anticipation_seconds: float = .3
    settle_seconds: float = .3
    sample_hz: int = 120
    boundary_sample_hz: int = 480
    idle_crouch_body_heights: float = .025
    minimum_swing_scale: float = .25
    support_placement: str = "instantaneous_speed"
    handoff_phase_fraction: float = 0.0
    handoff_sample_hz: int | None = None

    def __post_init__(self):
        if self.kind not in ('start', 'stop'):
            raise ContractError('transition kind must be start or stop')
        if type(self.ramp_cycles) is not int or not 1 <= self.ramp_cycles <= 4:
            raise ContractError('transition needs one to four full ramp cycles')
        if type(self.sample_hz) is not int or not 24 <= self.sample_hz <= 240:
            raise ContractError('invalid transition sample rate')
        if type(self.boundary_sample_hz) is not int or not self.sample_hz <= self.boundary_sample_hz <= 1920:
            raise ContractError('invalid transition boundary sample rate')
        for key in ('anticipation_seconds', 'settle_seconds', 'idle_crouch_body_heights', 'minimum_swing_scale', 'handoff_phase_fraction'):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
                raise ContractError(f'{key} must be finite numeric')
        if not 0 <= self.anticipation_seconds <= 2 or not 0 <= self.settle_seconds <= 2:
            raise ContractError('transition hold exceeds its envelope')
        if not 0 <= self.idle_crouch_body_heights <= .15 or not .1 <= self.minimum_swing_scale <= 1:
            raise ContractError('transition posture exceeds its envelope')
        if self.support_placement not in ('instantaneous_speed', 'integrated_support'):
            raise ContractError('unknown transition support placement')
        if not 0 <= self.handoff_phase_fraction <= .25:
            raise ContractError('handoff phase must be within the first quarter cycle')
        if (self.handoff_sample_hz is not None
            and (type(self.handoff_sample_hz) is not int
                 or not self.boundary_sample_hz <= self.handoff_sample_hz <= 1920)):
            raise ContractError('handoff sample rate must be within the boundary envelope')


def load_gait_transition(document):
    if not isinstance(document, dict) or document.get('schema') != 'eonwild.motion.gait-transition.v1' or set(document) - {'schema', 'parameters', 'classification', 'reference_basis'}:
        raise ContractError('unsupported gait transition profile')
    try:
        return GaitTransition(**document['parameters'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError(f'invalid gait transition profile: {exc}') from exc


def _smooth_derivative(u):
    return 30 * u**2 * (1 - u)**2 if 0 < u < 1 else 0.


def _smooth_integral(u):
    return 2.5 * u**4 - 3 * u**5 + u**6


def declared_handoff_phase(transition: GaitTransition, gait) -> float:
    """Return an authored phase on the bound gait's actual sampling clock.

    No candidate is inspected, no phase search is performed and no timing is
    inherited from a historical take. Integer rounding selects a clock tick,
    not a pose that happens to satisfy a failed validation metric.
    """
    if not isinstance(transition, GaitTransition) or not isinstance(gait, (GroundedGait, AirborneGait)):
        raise ContractError('handoff phase requires validated transition and gait profiles')
    owned = sampled_handoff_phase(gait)
    if owned is not None and transition.handoff_phase_fraction != gait.handoff_phase_fraction:
        raise ContractError('transition handoff phase differs from the bound gait interface')
    if owned is not None and transition.handoff_sample_hz != gait.handoff_sample_hz:
        raise ContractError('transition handoff sample rate differs from the bound gait interface')
    period = 2 * gait.step_period_s
    count = math.ceil(gait.cycles * period * gait.sample_hz)
    dt = gait.cycles * period / count
    return round(transition.handoff_phase_fraction * period / dt) * dt


class _Choreography:
    def __init__(self, transition, gait, height):
        if not isinstance(gait, (GroundedGait, AirborneGait)):
            raise ContractError('transition needs a supported locomotion profile')
        if isinstance(height, bool) or not isinstance(height, Real) or not math.isfinite(height) or height <= 0:
            raise ContractError('transition body height must be positive and finite')
        self.transition, self.gait, self.height = transition, gait, float(height)
        self.step = gait.step_period_s
        self.period = 2 * self.step
        self.join_phase = declared_handoff_phase(transition, gait)
        self.clock_offset = self.join_phase if transition.kind == 'stop' else 0.
        self.ramp = transition.ramp_cycles * self.period - self.clock_offset
        self.speed = gait.step_length_body_heights * height / self.step
        self.reach = (touchdown_reach(gait, height) if isinstance(gait, GroundedGait) else
                      math.copysign(gait.touchdown_reach_body_heights * height, self.speed))
        self.start = transition.kind == 'start'
        self.delay = transition.anticipation_seconds if self.start else 0.
        self.end = self.ramp + (self.period + self.join_phase if self.start else self.step + transition.settle_seconds)
        self.duration = self.delay + self.end
        if self.duration > 30:
            raise ContractError('transition duration exceeds 30 seconds')
        self.grounded = isinstance(gait, GroundedGait)
        self.stance = self.period * gait.duty_factor if self.grounded else self.step * (1 - gait.flight_fraction)
        self.sampler = sample_grounded_gait if self.grounded else sample_airborne_gait

    def envelope(self, time):
        u = min(1., max(0., time / self.ramp))
        weight = smooth(u)
        velocity = _smooth_derivative(u) / self.ramp
        return (weight, velocity) if self.start else (1 - weight, -velocity)

    def root(self, time):
        if time <= 0:
            return (0., 0., 0.) if self.start else (self.speed * time, self.speed, 0.)
        if time >= self.ramp:
            displacement = self.speed * self.ramp * .5
            return (displacement + self.speed * (time - self.ramp), self.speed, 0.) if self.start else (displacement, 0., 0.)
        u = time / self.ramp
        weight, derivative = self.envelope(time)
        distance = self.speed * self.ramp * (_smooth_integral(u) if self.start else u - _smooth_integral(u))
        return distance, self.speed * weight, self.speed * derivative

    def touchdown(self, time):
        # Both start feet are initially planted under the calibrated pelvis.
        if self.start and time <= 0:
            return 0.
        # The swing already in progress at stop entry owns its next
        # touchdown. Replanning that airborne target would jump the foot at t=0.
        if not self.start and time <= self.step - self.clock_offset + 1e-9:
            return self.speed * time + self.reach
        weight, _ = self.envelope(time)
        if self.transition.support_placement == 'integrated_support':
            # Commit reach using the distance the body WILL cover over this
            # support interval. An instantaneous speed scale leaves a planted
            # foot behind an accelerating pelvis. Neither anchors nor the
            # sustained gait's length/cadence are changed after touchdown.
            travel = self.root(self.liftoff(time))[0] - self.root(time)[0]
            weight = travel / (self.speed * self.stance)
        return self.root(time)[0] + self.reach * weight

    def liftoff(self, touchdown):
        if not self.start and touchdown >= self.ramp - 1e-8:
            return self.end + self.period  # final placement remains planted
        duration = self.stance
        if not self.grounded:
            # Extend support at low speed, rather than inventing a flight
            # phase before acceleration or after the final arrest.
            weight = min(self.envelope(touchdown)[0], self.envelope(touchdown + self.step)[0])
            if self.start and self.transition.support_placement == 'integrated_support':
                # Support must release in time for the upcoming speed, rather
                # than retain a low-speed stance duration while the body runs
                # away from it. The next contact is committed, not slid.
                weight = self.envelope(touchdown + self.step)[0]
            airborne = smooth((weight - .35) / .3)
            duration = self.step * (1.12 * (1 - airborne) + (1 - self.gait.flight_fraction) * airborne)
        return max(0., touchdown + duration) if self.start else touchdown + duration

    def canonical_foot(self, side, virtual):
        offset = 0. if side == 'left' else self.step
        row = self.sampler(self.gait, virtual + offset, self.height)
        foot = dict(row['feet'][side])
        # The base sampler includes a shared flight lift. Reconstruct
        # it from BOTH actual transition contacts below, not from an
        # independently warped foot's fictitious partner.
        if not self.grounded and row['flight']:
            phase = ((virtual + offset) / self.step) % 1
            u = (phase - (1 - self.gait.flight_fraction)) / self.gait.flight_fraction
            foot['height_m'] -= self.gait.flight_foot_lift_body_heights * self.height * math.sin(math.pi * u)**4
        return foot

    def foot(self, side, time):
        offset = 0. if side == 'left' else self.step
        if time < 0 and self.start:
            return {'contact': True, 'forward_m': 0., 'height_m': 0., 'toe_flex_degrees': 0.,
                'foot_pitch_degrees': 0., 'swing_phase': 0., 'touchdown_time_s': 0., 'articulation_scale': 0.}
        index = math.floor((time + self.clock_offset - offset + 1e-9) / self.period)
        touchdown = offset + index * self.period - self.clock_offset
        if not self.start:
            last = self.ramp + offset
            touchdown = min(touchdown, last)
        next_touchdown = touchdown + self.period
        lift = self.liftoff(touchdown)
        weight, _ = self.envelope(time)
        contact = time < lift - 1e-9
        if contact:
            fraction = min(1., max(0., (time - touchdown) / (lift - touchdown)))
            virtual = fraction * self.stance
            original = self.canonical_foot(side, virtual)
            forward, height, toe, pitch, swing = self.touchdown(touchdown), 0., original['toe_flex_degrees'] * weight, original['foot_pitch_degrees'] * weight, 0.
            amplitude = weight
        else:
            swing = min(1., max(0., (time - lift) / (next_touchdown - lift)))
            original = self.canonical_foot(side, self.stance + swing * (self.period - self.stance))
            at_lift, _ = self.envelope(lift)
            at_land, _ = self.envelope(next_touchdown)
            amplitude = max(self.transition.minimum_swing_scale, at_lift, at_land)
            pitch_scale = at_lift + (amplitude - at_lift) * smooth(swing / .35)
            progress = (transport_progress(swing, self.gait.swing_transport_ramp_fraction)
                        if not self.grounded and self.gait.swing_transport_ramp_fraction else smooth(swing))
            forward = self.touchdown(touchdown) + (self.touchdown(next_touchdown) - self.touchdown(touchdown)) * progress
            height = original['height_m'] * amplitude
            toe = original['toe_flex_degrees'] * pitch_scale
            pitch = original['foot_pitch_degrees'] * pitch_scale
        return {'contact': contact, 'forward_m': float(forward), 'height_m': float(height),
            'toe_flex_degrees': float(toe), 'foot_pitch_degrees': float(pitch), 'swing_phase': float(swing),
            'touchdown_time_s': float(self.delay + max(0., touchdown) if self.start else touchdown),
            'articulation_scale': float(amplitude), 'liftoff_time_s': float(lift), 'next_touchdown_time_s': float(next_touchdown)}

    def sample(self, time):
        active = time - self.delay
        weight, derivative = self.envelope(active)
        distance, velocity, acceleration = self.root(active)
        phase = (max(0., active) + self.clock_offset) % self.period
        if min(phase, self.period - phase) < 1e-8:
            phase = 0.
        carrier = self.sampler(self.gait, phase, self.height)
        standing = -self.transition.idle_crouch_body_heights * self.height
        offset = standing + weight * (carrier['pelvis_height_offset_m'] - standing)
        vertical_velocity = weight * carrier.get('pelvis_vertical_velocity_mps', 0.) + derivative * (carrier['pelvis_height_offset_m'] - standing)
        feet = {side: self.foot(side, active) for side in ('left', 'right')}
        support = sum(int(foot['contact']) for foot in feet.values())
        if not self.grounded and support == 0:
            begin = max(foot['liftoff_time_s'] for foot in feet.values())
            end = min(foot['next_touchdown_time_s'] for foot in feet.values())
            fraction = min(1., max(0., (active - begin) / (end - begin)))
            lift = self.gait.flight_foot_lift_body_heights * self.height * weight * math.sin(math.pi * fraction)**4
            for foot in feet.values():
                foot['height_m'] += lift
        return {'time_s': float(time), 'root_forward_m': float(distance), 'root_velocity_mps': float(velocity),
            'root_acceleration_mps2': float(acceleration), 'pelvis_height_offset_m': float(offset),
            'pelvis_vertical_velocity_mps': float(vertical_velocity), 'locomotion_time_s': float(phase),
            'performance_gain': float(weight), 'stage': 'ANTICIPATION' if active < 0 else ('ACCELERATE' if self.start else 'ARREST'),
            'support_count': support, 'flight': support == 0, 'feet': feet}


def build_transition_plan(transition: GaitTransition, gait, body_height_m):
    if not isinstance(transition, GaitTransition):
        raise ContractError('transition must be validated')
    c = _Choreography(transition, gait, body_height_m)
    count = int(math.ceil(c.duration * transition.sample_hz))
    times = set(np.linspace(0., c.duration, count + 1).tolist())
    boundaries = {0., c.duration, c.delay, c.delay + c.ramp}
    for index in range(-2, 2 * transition.ramp_cycles + 5):
        touchdown = index * c.step - c.clock_offset
        boundaries.update((c.delay + touchdown, c.delay + c.liftoff(touchdown)))
    for boundary in boundaries:
        if not 0 <= boundary <= c.duration:
            continue
        times.add(boundary)
        times.update(boundary + k / transition.boundary_sample_hz for k in range(-2, 3)
                     if 0 <= boundary + k / transition.boundary_sample_hz <= c.duration)
    if transition.handoff_sample_hz is not None:
        handoff = c.duration if c.start else 0.
        times.update(handoff + k / transition.handoff_sample_hz for k in range(-2, 3)
                     if 0 <= handoff + k / transition.handoff_sample_hz <= c.duration)
    ordered = []
    for time in sorted(times):
        if not ordered or time - ordered[-1] > 1e-7:
            ordered.append(time)
    rows = [c.sample(time) for time in ordered]
    entry_speed, exit_speed = (0., c.speed) if c.start else (c.speed, 0.)
    cues = [{'time_s': 0., 'name': 'ANTICIPATION_START' if c.start else 'ARREST_START'},
            {'time_s': c.duration, 'name': 'LOCOMOTION_READY' if c.start else 'RECOVERY_COMPLETE'}]
    for cue in cues:
        cue.update(kind='animation_cue', authoritative_world_fact=False)
    return {'schema': 'eonwild.motion.v9.contact-plan.v1', 'program': 'gait_transition',
        'locomotion_program': 'grounded_gait' if c.grounded else 'airborne_gait', 'loop': False,
        'body_height_m': float(body_height_m), 'duration_s': c.duration, 'same_foot_cycle_s': c.period,
        'parameters': gait_parameters(gait), 'transition_parameters': gait_parameters(transition), 'samples': rows, 'events': cues,
        'transition_contract': {'kind': transition.kind, 'entry_speed_mps': entry_speed, 'exit_speed_mps': exit_speed,
            'entry_pose': 'calibrated_ready' if c.start else ('locomotion_declared_phase' if c.join_phase else 'locomotion_phase_zero'),
            'exit_pose': ('locomotion_declared_phase' if c.join_phase else 'locomotion_phase_zero') if c.start else 'calibrated_ready',
            'steady_phase_s': c.join_phase, 'interface_schema': 'eonwild.motion.gait-interface.v2' if c.join_phase else 'eonwild.motion.gait-interface.v1',
            'root_distance_m': rows[-1]['root_forward_m'],
            'verification': 'Requires final emitted pose/velocity and skin-contact parity; planner intent is not proof.'},
        'classification': 'bounded contact-owned kinematic start/stop choreography; no force or biological claim'}
