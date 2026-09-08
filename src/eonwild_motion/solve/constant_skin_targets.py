"""Diagnostic, source-owned constant skin-target values.

This is deliberately non-emitting.  It applies one immutable correction per
semantic foot at every source time and reports pointwise geometry only; it does
not claim branch stability, derivatives, C1 motion, or final contact authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
import math
import numpy as np
from ..errors import ContractError
from .airborne_gait import solve_airborne_plan_sample, _world_matrices
from .skin_rig import SkinRig
from .source_motion_query import SourceMotionQuery, SourceMotionUnavailable
from .support_anchors import CanonicalSupportAnchorProvider

_TARGET_GAP_M=.0001
_TOLERANCE_M=.0002

@dataclass(frozen=True)
class ConstantSkinTargetValue:
    status: str
    time_s: float
    row: Mapping[str, Any]
    corrections_m: Mapping[str, np.ndarray]
    observations: Mapping[str, Any]
    branch_witness: Mapping[str, Any]

class CanonicalConstantSkinTargetLaw:
    """Per-side canonical-touchdown constants bound to a SourceMotionQuery."""
    def __init__(self, query: SourceMotionQuery, provider: CanonicalSupportAnchorProvider, skin: SkinRig, constants: Mapping[str,np.ndarray]):
        self._query, self._provider, self._skin = query, provider, skin
        checked={}
        for side in ('left','right'):
            value=np.array(constants[side],dtype=float,copy=True)
            if value.shape != (3,) or not np.isfinite(value).all():
                raise ContractError('constant skin target requires finite per-side vectors')
            value.setflags(write=False); checked[side]=value
        self._constants=MappingProxyType(checked)

    @classmethod
    def build(cls, query: SourceMotionQuery, provider: CanonicalSupportAnchorProvider, *, source, semantic_roles, solver_gait, locomotion_gait, transition, plan, contact_profile, up_axis, forward_axis, articulation_profile=None, iterations:int=7):
        if type(iterations) is not int or iterations < 1: raise ContractError('constant skin target iterations must be positive integer')
        if query.refined: raise ContractError('constant skin target requires an unrefined source query')
        provider.validate_for_consumption(source,semantic_roles=semantic_roles,solver_gait=solver_gait,locomotion_gait=locomotion_gait,transition=transition,plan=plan,contact_profile=contact_profile,up_axis=up_axis,forward_axis=forward_axis,articulation_profile=articulation_profile)
        skin=SkinRig(source,semantic_roles,query.context.forward,query.context.up,contact_profile)
        constants={side:np.zeros(3) for side in ('left','right')}
        for _ in range(iterations):
            updates={}
            for side in ('left','right'):
                value=cls._observe(query,provider,skin,side,provider.anchor_for(side).touchdown_phase_s,constants)
                if not value['loaded']: raise ContractError('canonical touchdown must be loaded')
                updates[side]=.85*value['required_correction_m']
            for side in constants: constants[side]+=updates[side]
            if max(np.linalg.norm(v) for v in constants.values()) > .06*query.context.body_height: raise ContractError('constant skin target exceeded body-normalized correction envelope')
            if max(np.linalg.norm(v) for v in updates.values()) <= _TOLERANCE_M: break
        law=cls(query,provider,skin,constants)
        for side in ('left','right'):
            seen=law._observe_at(provider.anchor_for(side).touchdown_phase_s)
            if seen.observations[side]['residual_m'] > _TOLERANCE_M: raise ContractError('constant skin target did not converge at canonical touchdown')
        return law

    @staticmethod
    def _patch(skin, worlds, side):
        return np.vstack([skin.skin(worlds,skin.foot_regions[side][region]) for region in ('sole','toe')])
    @classmethod
    def _observe(cls,query,provider,skin,side,time,constants):
        result=query.evaluate(time)
        if isinstance(result,SourceMotionUnavailable): raise ContractError('constant skin target source value is unavailable')
        row={k:v for k,v in result.row.items()}; row['feet']={s:dict(f) for s,f in result.row['feet'].items()}
        for s,v in constants.items(): row['feet'][s]['target_offset_m']=v.tolist()
        pose=solve_airborne_plan_sample(query.context,row,body_response_sample=query._body_sample(query._exact_index(time),row))
        worlds=_world_matrices(query._source,pose.translations,pose.rotations,query.context.base_s)
        patch=cls._patch(skin,worlds,side); anchor=provider.anchor_for(side)
        target=anchor.material_origin_m+query.context.forward*row['feet'][side]['forward_m']
        active=patch[:,np.argmax(np.abs(query.context.up))] <= patch[:,np.argmax(np.abs(query.context.up))].min()+.001
        error=.5*((target[active]-patch[active]).max(0)+(target[active]-patch[active]).min(0))
        up=query.context.up; gap=float(patch[:,np.argmax(np.abs(up))].min()-skin.ground); error-=up*float(error@up); error+=up*(_TARGET_GAP_M-gap)
        return {'loaded':bool(row['feet'][side]['contact']),'required_correction_m':error,'gap_m':gap,'patch':patch,'pose':pose,'row':row}
    def _observe_at(self,time):
        data={side:self._observe(self._query,self._provider,self._skin,side,time,self._constants) for side in ('left','right')}
        obs={side:{'loaded':x['loaded'],'residual_m':float(np.linalg.norm(x['required_correction_m'])),'minimum_gap_m':x['gap_m'],'clearance_ok':x['gap_m']>=0} for side,x in data.items()}
        row=data['left']['row']
        return ConstantSkinTargetValue('AVAILABLE',float(time),MappingProxyType(row),MappingProxyType(self._constants),MappingProxyType(obs),MappingProxyType({'status':'BRANCH_OR_CONVERGENCE_UNAVAILABLE_FROM_EXISTING_ROW_SOLVER'}))
    def value(self,time_s):
        if isinstance(time_s,bool) or not isinstance(time_s,(int,float)) or not math.isfinite(time_s): raise ContractError('constant skin target time must be finite numeric')
        return self._observe_at(float(time_s))
