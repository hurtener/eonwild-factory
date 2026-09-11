"""Portable animal profile and deterministic secondary-motion reference law.

This is a consumer layer over immutable motion, not a new locomotion compiler.
Angular axes are local right-handed glTF axes; Unity reflects axial Y/Z.
"""
from __future__ import annotations
from copy import deepcopy
import math
from typing import Mapping

SCHEMA = 'eonwild.animal-embodiment.v1'


def joints(profile):
    s = profile['secondary']
    return s['arms'] + ([s['jaw']] if s['hasJaw'] else [])


def validate(profile, node_names=None):
    if profile.get('schema') != SCHEMA or profile.get('version') != 1:
        raise ValueError('Unsupported embodiment profile')
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Non-finite profile value')
        if isinstance(value, dict):
            for child in value.values(): finite(child)
        elif isinstance(value, list):
            for child in value: finite(child)
    finite(profile)
    bindings = profile['bindings']
    roles = {b['role']: b['bone'] for b in bindings}
    if len(roles) != len(bindings) or any(not r or not b for r,b in roles.items()):
        raise ValueError('Duplicate or empty semantic role')
    required = {'root','pelvis','chest','head','leftFoot','rightFoot'} | set(profile['neckRoles'])
    if not required <= roles.keys(): raise ValueError('Missing required gait or attention role')
    if node_names is not None:
        for bone in roles.values():
            if node_names.count(bone) != 1: raise ValueError('Missing or ambiguous bone: '+bone)
    q = profile['sequence']
    if not 0 <= q['walkStart'] < q['walkEnd'] <= q['stopStart'] < q['duration']:
        raise ValueError('Invalid sequence intervals')
    s = profile['secondary']
    if s['contract'] != 'eonwild.secondary.v1' or min(s['breathPeriod'],s['fullWalkSpeed'],s['walkBlendRate']) <= 0:
        raise ValueError('Invalid secondary-motion law')
    seen=set()
    for joint in joints(profile):
        role=joint['role']; axis=joint['axis']
        if role not in roles or roles[role] in seen: raise ValueError('Missing or multiply driven joint')
        seen.add(roles[role])
        if len(axis)!=3 or not math.isclose(sum(x*x for x in axis),1,abs_tol=1e-6):
            raise ValueError('Joint axis must be an explicit local unit angular axis')
        if joint in s['arms'] and (joint['responseSeconds'] <= 0 or abs(joint['walkSign']) != 1):
            raise ValueError('Invalid joint response')
    return profile


class SecondaryState:
    def __init__(self, profile):
        validate(profile)
        self.settings=deepcopy(profile['secondary'])
        self.joints=deepcopy(joints(profile))
        self.elapsed=0.;self.walking=0.;self.response=[0.]*len(self.joints)

    def step(self, delta, speed, stride_signal):
        if not all(math.isfinite(x) for x in (delta,speed,stride_signal)) or delta < 0 or speed < 0:
            raise ValueError('Invalid secondary-motion input')
        s=self.settings;self.elapsed+=delta
        self.walking+=(min(1.,speed/s['fullWalkSpeed'])-self.walking)*(1-math.exp(-delta*s['walkBlendRate']))
        breath=.5-.5*math.cos(self.elapsed*math.tau/s['breathPeriod']+s['phase'])
        result=[]
        for i,j in enumerate(self.joints):
            angle=j['restDegrees']+j['breathDegrees']*breath
            if i<len(s['arms']):
                target=max(-1.,min(1.,stride_signal))*j['walkSign']
                self.response[i]+=(target-self.response[i])*(1-math.exp(-delta/max(.03,j['responseSeconds'])))
                angle+=j['walkDegrees']*self.walking*self.response[i]
            result.append(angle)
        return result
