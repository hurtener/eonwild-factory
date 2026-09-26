"""Finite placement/attention intents over the shared retreat contact interface.

Authored support choreography only: mass, constraints and forces belong to the
shared OpenSim model and FiniteCoordination, not to this task planner.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from .moco_retreat_task import RetreatPlan
from .moco_tasks import smooth


class PlacementPlan(RetreatPlan):
    def __init__(self, specification, initial_feet, geometry, normal_step, leg_length):
        super().__init__(dict(specification, steps=4), initial_feet, geometry, normal_step, leg_length)
        self.specification = specification
        self.mode = specification.get('placement_mode',specification['family'])
        self.heading_angle = np.deg2rad(specification.get('heading_degrees', 0.))
        self.center = np.mean([v['origin'] for v in initial_feet.values()], axis=0)
        self.events = []
        interval = specification['step_interval_s']
        first = specification['first_swing_s']
        swing = specification['swing_seconds']
        if self.mode == 'pivot':
            # Outside leg opens the new stance, inside leg follows. Repeat,
            # keeping a wider footprint than forward walking. Never swivel a
            # loaded foot: heading changes only during its unloaded swing.
            outside = 'r' if self.heading_angle > 0 else 'l'
            inside = 'l' if outside == 'r' else 'r'
            placements = [(side, j / 3) for j in range(1, 4) for side in (outside, inside)]
            for i, (side, fraction) in enumerate(placements):
                yaw = self.heading_angle * fraction
                R = Rotation.from_rotvec([0., yaw, 0.]).as_matrix()
                relative = np.array(initial_feet[side]['origin']) - self.center
                relative[2] *= specification['stance_width_scale']
                final = self.center + R @ relative
                self.events.append(dict(side=side, lift=first+i*interval,
                    land=first+i*interval+swing, translation=final-np.array(initial_feet[side]['origin']), yaw=yaw))
            self.final_translation = np.zeros(3)
        elif self.mode == 'lateral':
            signed = leg_length * specification['lateral_distance_leg_lengths']
            outside = max(initial_feet, key=lambda s: np.sign(signed)*initial_feet[s]['origin'][2])
            inside = 'l' if outside == 'r' else 'r'
            for i, side in enumerate((outside, inside, outside, inside)):
                translation = np.array([0., 0., signed*(1 if i<2 else 2)])
                self.events.append(dict(side=side,lift=first+i*interval,
                    land=first+i*interval+swing,translation=translation,yaw=0.))
            self.final_translation = np.array([0., 0., 2*signed])
        elif self.mode == 'retreat':
            for i,(side,multiple) in enumerate([('r',1),('l',2),('r',3),('l',3)]):
                self.events.append(dict(side=side,lift=first+i*interval,
                    land=first+i*interval+swing,translation=np.array([-multiple*self.step,0.,0.]),yaw=0.))
            self.final_translation = np.array([-3*self.step,0.,0.])
        elif self.mode == 'alert':
            self.final_translation = np.zeros(3)
        else:
            raise ValueError('Unknown finite placement family: '+self.mode)
        self.end = (self.events[-1]['land']+specification['settle_seconds'] if self.events
                    else specification['attention_keys'][-1][0])
        if self.end+specification['adoption_seconds'] >= specification['duration_s']:
            raise ValueError('Placement task must retain settling and final rest')
        self.keys=[(0.,.5),(specification['prepare_s'],.5)]
        for e in self.events:
            weight=1. if e['side']=='r' else 0.
            self.keys.extend([(e['lift'],weight),(e['land'],weight)])
        self.keys.extend([(self.end,.5),(specification['duration_s'],.5)])

    def heading(self, time):
        if self.mode != 'pivot': return 0.
        a=self.events[0]['lift']-.1
        b=self.events[-1]['land']
        return self.heading_angle*float(smooth((time-a)/(b-a)))

    def attention_degrees(self, time):
        keys=self.specification.get('attention_keys')
        if keys:
            for (a,va),(b,vb) in zip(keys[:-1],keys[1:]):
                if time<=b:return va+(vb-va)*float(smooth((time-a)/(b-a)))
            return keys[-1][1]
        if self.mode=='pivot':
            lead=self.specification['attention_lookahead_s']
            return float(np.degrees(self.heading(time+lead)-self.heading(time)))
        return 0.

    def foot(self, t, side):
        initial=self.initial[side];translation=np.zeros(3);yaw=0.;pitch=0.;lift=0.;curl=0.
        s=self.specification
        for e in self.events:
            if e['side']!=side:continue
            if t>=e['land']:
                translation=e['translation'];yaw=e['yaw'];continue
            prepare=e['lift']-s['release_seconds']
            if t<prepare:break
            if t<e['lift']:
                pitch=s['release_pitch_rad']*float(smooth((t-prepare)/s['release_seconds']))
            else:
                u=(t-e['lift'])/(e['land']-e['lift']);blend=float(smooth(u));bump=64*u**3*(1-u)**3
                translation=(1-blend)*translation+blend*e['translation']
                yaw=(1-blend)*yaw+blend*e['yaw']
                lift=self.clearance*bump
                pitch=s['release_pitch_rad']*(1-blend)+s['recovery_pitch_rad']*bump
                curl=s['recovery_digit_rad']*bump
            break
        if self.front_release:pitch=-pitch;curl-=pitch
        R0=np.asarray(initial['rotation'])
        base=Rotation.from_rotvec([0.,yaw,0.]).as_matrix()@R0
        R=base@Rotation.from_rotvec([0.,0.,pitch]).as_matrix()
        if self.front_release:
            D0=Rotation.from_rotvec([0.,0.,initial['digit']]).as_matrix()
            D=Rotation.from_rotvec([0.,0.,initial['digit']+curl]).as_matrix()
            correction=base@(self.midpoint+D0@self.distal_center)-R@(self.midpoint+D@self.distal_center)
        else:correction=base@self.pivot-R@self.pivot
        return np.asarray(initial['origin'])+translation+correction+[0.,lift,0.],R,initial['digit']+curl
