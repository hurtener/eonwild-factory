#!/usr/bin/env python3
"""Regenerate the approved V8.2 GLB from the included iteration-b base."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

PKG = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("glb_math", PKG / "scripts/glb_math.py")
g = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(g)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_locals(glb, tracks, i):
    return [tracks.get(n.get("name", f"node_{j}"), np.asarray([glb.rest_rotation[j]]))[i if n.get("name", f"node_{j}") in tracks else 0] for j,n in enumerate(glb.nodes)]
def power(q, f): return g.q_from_rotvec(g.q_to_rotvec(q) * f)

def solve(glb, clip, cfg):
    _, tracks = glb.tracks(clip); c = cfg["contract"]; chest=c["chest"]; neck=c["neckHead"]; names=[chest,*neck]
    values={n:np.empty_like(tracks[n], dtype=np.float64) for n in names}; pelvis=glb.name_to_node[c["pelvis"]]; chest_i=glb.name_to_node[chest]; ref=None
    for i in range(len(next(iter(tracks.values())))):
        local=load_locals(glb, tracks, i); world=g.all_worlds(glb, local)
        if ref is None: ref=world[pelvis]
        pelvis_roll=g.q_to_rotvec(g.q_mul(world[pelvis], g.q_inv(ref)))[2]
        relative=g.q_mul(world[chest_i], g.q_inv(world[pelvis]))
        chest_world=g.q_mul(g.q_from_rotvec(g.q_to_rotvec(relative)+np.asarray([0.,0.,-float(c["chestRollGain"])*pelvis_roll])), world[pelvis])
        delta=g.q_mul(chest_world, g.q_inv(world[chest_i])); target=list(world); parent=glb.parents[chest_i]
        values[chest][i]=chest_world if parent is None else g.q_mul(g.q_inv(target[int(parent)]), chest_world); target[chest_i]=chest_world
        for name, residual in zip(neck, c["neckResidualFractions"]):
            idx=glb.name_to_node[name]; desired=g.q_mul(power(delta,float(residual)), world[idx]); parent=glb.parents[idx]
            values[name][i]=desired if parent is None else g.q_mul(g.q_inv(target[int(parent)]), desired); target[idx]=desired
    for rows in values.values():
        for i in range(1,len(rows)):
            if np.dot(rows[i-1],rows[i])<0: rows[i]*=-1
        rows[-1]=rows[0]
    return values

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",default=PKG/"config/release.json",type=Path); p.add_argument("--output",type=Path); a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else None)
    cfg=json.loads(a.config.read_text()); base=PKG/cfg["base"]; out=a.output or (PKG/cfg["output"])
    if sha(base)!=cfg["baseSha256"]: raise RuntimeError("included base SHA mismatch")
    glb=g.Glb(base); raw=bytearray(glb.raw)
    for clip in cfg["walkClips"]:
        result=solve(glb,clip,cfg); accessors=glb.rotation_accessors(clip)
        for name, rows in result.items():
            offset,count=glb.accessor_offset(accessors[name]); raw[glb.bin_start+offset:glb.bin_start+offset+count*16]=rows.astype("<f4").tobytes()
    out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(raw)
    actual=sha(out)
    if actual!=cfg["outputSha256"]: raise RuntimeError(f"reproduction SHA mismatch: {actual}")
    print(json.dumps({"status":"PASS","output":str(out),"sha256":actual},indent=2))
if __name__=="__main__": main()
