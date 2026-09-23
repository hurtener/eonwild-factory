"""Research-profile attention on reduced anatomy, before contact reconstruction.

Regional weights are preferences, not permission to exceed physical coordinates.
Smooth bounded allocation redistributes bend when a reduced region approaches its
limit. Actual horizontal skull heading is solved, rather than summing Euler yaw.
"""
import numpy as np
from scipy.optimize import brentq
from eonwild_motion.attention import resolve_attention, attention_intent, bound_attention


class ProfileAttention:
    def __init__(self, profile, metadata, mode='scan'):
        self.attention = resolve_attention(profile)
        if self.attention is None:
            raise ValueError('Moco profile attention requires a central envelope')
        self.target_degrees = attention_intent(mode, self.attention)['requestedDegrees']
        self.exceptional = mode == 'exceptional'
        roles = profile['neckRoles']
        bindings = [b for b in metadata['axial_bindings'] if b['role'] in roles]
        starts = [roles.index(b['role']) for b in bindings]
        if not starts or starts[0] != 0 or starts != sorted(set(starts)):
            raise ValueError('Reduced neck bindings must partition ordered profile roles')
        weights = self.attention['envelope']['neckWeights']
        regional = [sum(weights[a:b]) for a,b in zip(starts, starts[1:]+[len(roles)])]
        head = [b for b in metadata['axial_bindings'] if b['role'] == 'head']
        if len(head) != 1:
            raise ValueError('Exactly one admitted head is required')
        self.names = [b['body']+'_yaw' for b in bindings+head]
        share = self.attention['neckShare']
        self.weights = np.array([share*w for w in regional]+[1-share])
        bounds = np.array([metadata['coordinates'][n]['bounds_rad'] for n in self.names])
        if not np.isfinite(bounds).all() or np.any(bounds[:,0]>=0) or np.any(bounds[:,1]<=0):
            raise ValueError('Attention coordinates require finite bounds around zero')
        self.mid = bounds.mean(axis=1)
        self.half = (bounds[:,1]-bounds[:,0])/2
        self.zero = np.arctanh(-self.mid/self.half)
        self.description = dict(coordinates=self.names, preferred_weights=self.weights.tolist(),
            reduced_regions=[dict(body=b['body'],roles=roles[a:z]) for b,a,z in
                             zip(bindings,starts,starts[1:]+[len(roles)])],
            attention=self.attention, target_mode=mode,
            method='Central profile preferences aggregated by admitted semantic regions; smooth bounded allocation against actual projected skull heading. No capacity or range changes.')

    def coordinates(self, scale):
        return self.mid+self.half*np.tanh(self.zero+scale*self.weights/self.half)

    def solve(self, requested_degrees, heading_degrees):
        bounded = bound_attention(requested_degrees,self.attention,self.exceptional)
        target = bounded['yawDegrees']
        def error(scale):
            return heading_degrees(self.coordinates(scale))-target
        # Finite soft approach to the admitted limits, never an output clamp.
        lo,hi=-20.,20.
        a,b=error(lo),error(hi)
        if a<=0<=b:
            scale=brentq(error,lo,hi,xtol=1e-11)
        else:
            scale=lo if abs(a)<abs(b) else hi
        values=self.coordinates(scale)
        achieved=float(heading_degrees(values))
        return values,dict(requested_degrees=float(requested_degrees),
            bounded_degrees=float(target), achieved_degrees=achieved,
            unfulfilled_degrees=float(target-achieved), **{k:v for k,v in bounded.items() if k!='yawDegrees'})
