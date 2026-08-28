#!/usr/bin/env python3
"""Regenerate the approved V8.2 GLB from the included iteration-b base."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np

PKG = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("glb_math", PKG / "scripts/glb_math.py")
g = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(g)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_locals(glb, tracks, i):
    return [tracks.get(n.get("name", f"node_{j}"), np.asarray([glb.rest_rotation[j]]))[i if n.get("name", f"node_{j}") in tracks else 0] for j,n in enumerate(glb.nodes)]
def power(q, f): return g.q_from_rotvec(g.q_to_rotvec(q) * f)
def contract_roles(c):
 r=c["roles"]; return r["pelvis"],r["chest"],[*r["neck"],r["head"]]
def validate(glb, tracks, c, clip):
 pelvis,chest,neck=contract_roles(c); roles=c["roles"]; names=[pelvis,chest,*neck]; expected=[roles["root"],c["spineParent"],chest,*neck[:-1]]
 if any(n not in glb.name_to_node or n not in tracks for n in names): raise RuntimeError("semantic role missing animation rotation")
 for n,parent in zip(names,expected):
  idx=glb.name_to_node[n]; actual=glb.nodes[glb.parents[idx]].get("name") if glb.parents[idx] is not None else None
  if actual!=parent: raise RuntimeError(f"hierarchy contract mismatch for {n}: {actual}")
 accessors=glb.rotation_accessors(clip); ac=c["accessorContract"]
 for n in names:
  if tracks[n].shape[1]!=4 or n not in accessors: raise RuntimeError("rotation layout is not VEC4")
  item=glb.json["accessors"][accessors[n]]; view=glb.json["bufferViews"][item["bufferView"]]
  if item["componentType"]!=ac["componentType"] or item["type"]!=ac["type"] or int(view.get("byteStride",16))!=ac["byteStride"]: raise RuntimeError("accessor contract mismatch")
 if len({len(v) for v in tracks.values()})!=1: raise RuntimeError("timeline contract mismatch")

def solve(glb, clip, cfg):
    _, tracks = glb.tracks(clip); c = cfg["contract"]; pelvis_name,chest,neck=contract_roles(c); validate(glb,tracks,c,clip); names=[chest,*neck]
    values={n:np.empty_like(tracks[n], dtype=np.float64) for n in names}; pelvis=glb.name_to_node[pelvis_name]; chest_i=glb.name_to_node[chest]; ref=None
    for i in range(len(next(iter(tracks.values())))):
        local=load_locals(glb, tracks, i); world=g.all_worlds(glb, local)
        if ref is None: ref=world[pelvis]
        pelvis_roll=g.q_to_rotvec(g.q_mul(world[pelvis], g.q_inv(ref)))[int(c["basis"]["rotationVectorAxis"])]
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
    limits={chest:float(c["maxChestLocalDeltaDegrees"]), **{n:float(c["maxNeckLocalDeltaDegrees"]) for n in neck}}
    for n,rows in values.items():
        base=tracks[n]; maximum=max(float(np.degrees(np.linalg.norm(g.q_to_rotvec(g.q_mul(g.q_inv(base[i]),rows[i]))))) for i in range(len(rows)))
        if maximum>limits[n]+1e-6: raise RuntimeError(f"local delta bound exceeded {n}: {maximum}")
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
