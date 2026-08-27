"""Rig-aware living-neutral jaw calibration for V5."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap, AnatomicalBasis, Pose

@dataclass(frozen=True)
class JawCalibrationResult:
    close_degrees: float
    minimum_gap_m: float
    median_gap_m: float
    maximum_gap_m: float
    target_minimum_gap_m: float
    candidate_count: int
    witness_bin_count: int
    jaw_vertex_count: int
    upper_vertex_count: int
    jaw_chain: tuple[str, ...]
    upper_chain: tuple[str, ...]
    def to_dict(self): return asdict(self)

class JawClosureModel:
    def __init__(self, asset: GlbAsset, semantics: SemanticMap, basis: AnatomicalBasis, hip_height: float):
        self.asset=asset; self.semantics=semantics; self.basis=basis; self.hip_height=float(hip_height)
        self.primitive=asset.primitive()
        if self.primitive.joints is None or self.primitive.weights is None: raise ValueError("skinned primitive required")
        self.jaw_chain=tuple(asset.single_child_chain(semantics.bone("jaw"),16))
        self.upper_chain=tuple(semantics.bone(t) for t in ("skull","snout","snout_tip") if t in semantics.tags)
        skin_nodes,_=asset.skin_data(); n2s={asset.nodes[n].get("name"):i for i,n in enumerate(skin_nodes)}
        jaw_skin=[n2s[n] for n in self.jaw_chain]; upper_skin=[n2s[n] for n in self.upper_chain]
        jw=np.zeros(len(self.primitive.positions)); uw=np.zeros(len(self.primitive.positions))
        for k in range(self.primitive.joints.shape[1]):
            jw += self.primitive.weights[:,k]*np.isin(self.primitive.joints[:,k],jaw_skin)
            uw += self.primitive.weights[:,k]*np.isin(self.primitive.joints[:,k],upper_skin)
        self.jaw_mask=jw>.55; self.upper_mask=uw>.50
        self.bins=self._select_bins()
        if len(self.bins)<3: raise ValueError(f"only {len(self.bins)} jaw witness bins")
        union=sorted({int(x) for pair in self.bins for arr in pair for x in arr})
        self.indices=np.asarray(union,dtype=np.int64); lookup={v:i for i,v in enumerate(union)}
        self.local_bins=[(np.asarray([lookup[int(x)] for x in j]),np.asarray([lookup[int(x)] for x in u])) for j,u in self.bins]
    def _select_bins(self):
        p=self.primitive.positions; f=p@self.basis.forward; up=p@self.basis.up; lat=p@self.basis.lateral
        jf=f[self.jaw_mask]; uf=f[self.upper_mask]
        lo=max(float(np.quantile(jf,.12)),float(np.quantile(uf,.12))); hi=min(float(np.quantile(jf,.98)),float(np.quantile(uf,.98)))
        lo+=(hi-lo)*.05; center=float(np.median(lat[self.jaw_mask])); half=max(self.hip_height*.16,.18)
        out=[]
        edges=np.linspace(lo,hi,7)
        for a,b in zip(edges[:-1],edges[1:]):
            j=np.where(self.jaw_mask&(f>=a)&(f<b)&(np.abs(lat-center)<half))[0]
            u=np.where(self.upper_mask&(f>=a)&(f<b)&(np.abs(lat-center)<half))[0]
            if len(j)<8 or len(u)<8: continue
            j=j[up[j]>=np.quantile(up[j],.96)]; u=u[up[u]<=np.quantile(up[u],.04)]
            if len(j) and len(u): out.append((j,u))
        return out
    def gaps(self,close_degrees:float):
        pose=Pose(self.asset); pose.rotate_world_rest_axis(self.semantics.bone("jaw"),self.basis.lateral,-math.radians(close_degrees))
        i=self.indices; pts=self.asset.skin_points(self.primitive.positions[i],self.primitive.joints[i],self.primitive.weights[i],pose.world_matrices); h=pts@self.basis.up
        return np.asarray([float(np.quantile(h[u],.25)-np.quantile(h[j],.75)) for j,u in self.local_bins])
    def calibrate(self,minimum=42.0,maximum=52.0,step=.25,target_minimum_gap_m=None):
        target=float(target_minimum_gap_m if target_minimum_gap_m is not None else self.hip_height*.0015)
        candidates=np.arange(minimum,maximum+step*.5,step); scored=[]
        for close in candidates:
            gaps=self.gaps(float(close)); mn=float(gaps.min()); score=abs(mn-target)+max(0.,-mn)*1000.
            scored.append((score,float(close),gaps))
        _,close,gaps=min(scored,key=lambda x:x[0])
        return JawCalibrationResult(close,float(gaps.min()),float(np.median(gaps)),float(gaps.max()),target,len(candidates),len(self.local_bins),int(self.jaw_mask.sum()),int(self.upper_mask.sum()),self.jaw_chain,self.upper_chain)
