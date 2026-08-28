#!/usr/bin/env python3
"""Fail-closed snapshot verifier for the lean V8.2 release."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys
sys.dont_write_bytecode = True
from pathlib import Path
PKG=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("glb_math",PKG/"scripts/glb_math.py"); g=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(g)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--config",default=PKG/"config/release.json",type=Path); p.add_argument("--candidate",type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else None); c=json.loads(a.config.read_text()); manifest=json.loads((PKG/"RELEASE_MANIFEST.json").read_text()); inventory=manifest.get("inventory",{}); actual={str(x.relative_to(PKG)) for x in PKG.rglob("*") if x.is_file() and x.name!="RELEASE_MANIFEST.json" and "__pycache__" not in x.parts}; inv_ok=set(inventory)==actual and bool(manifest.get("selfHashConvention")); hashes=all((PKG/k).is_file() and sha(PKG/k)==v["sha256"] and (PKG/k).stat().st_size<=100*1024*1024 for k,v in inventory.items()); media_ok=True
 for k,v in inventory.items():
  if "media" in v:
   q=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height,nb_frames","-of","json",str(PKG/k)])); s=q["streams"][0]; m=v["media"]; media_ok &= int(s["width"])==m["width"] and int(s["height"])==m["height"] and int(s["nb_frames"])==m["frames"] and abs(float(q["format"]["duration"])-m["duration"])<1e-6
 base=PKG/c["base"]; candidate=a.candidate or (PKG/c["output"]); b=g.Glb(base); x=g.Glb(candidate); allowed=set(c["contract"]["allowedOutputRotationNodes"]); changed=[]; exact=inv_ok and hashes and media_ok
 if sha(base)!=c["baseSha256"] or sha(candidate)!=c["outputSha256"]: exact=False
 if b.json!=x.json: exact=False
 for clip in c["walkClips"]:
  br=b.rotation_accessors(clip); xr=x.rotation_accessors(clip)
  if set(br)!=set(xr): exact=False
  for name,ai in br.items():
   bo,bc=b.accessor_offset(ai); xo,xc=x.accessor_offset(xr[name]); same=bc==xc and b.binary[bo:bo+bc*16]==x.binary[xo:xo+xc*16]
   if not same: changed.append(f"{clip}/{name}"); exact &= name in allowed
 result={"schema":"eonwild.v8_2.release_verify.v2","status":"PASS" if exact and changed else "FAIL","baseSha256":sha(base),"candidateSha256":sha(candidate),"changedRotationAccessors":changed,"allowedNodes":sorted(allowed),"checks":{"manifestInventoryExact":inv_ok,"inventoryHashesAndSizes":hashes,"mediaFacts":media_ok,"baseHash":sha(base)==c["baseSha256"],"candidateHash":sha(candidate)==c["outputSha256"],"jsonByteEquivalent":b.json==x.json,"onlyAllowedWalkRotationAccessors":exact,"nonemptyApprovedChangeSet":bool(changed)}}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2)); raise SystemExit(0 if result["status"]=="PASS" else 1)
if __name__=="__main__": main()
