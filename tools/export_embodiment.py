"""Export a validated, immutable animal profile and Python reference vectors."""
import argparse,json,hashlib,math
from pathlib import Path
from eonwild_motion.embodiment import validate,SecondaryState
from eonwild_motion.glb.container import Glb
p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--motion',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
d=json.loads(a.profile.read_text());g=Glb(a.motion);validate(d,[n.get('name','') for n in g.nodes])
if hashlib.sha256(a.motion.read_bytes()).hexdigest()!=d['source']['motionSha256']:raise ValueError('Profile motion hash mismatch')
a.output.mkdir(parents=True,exist_ok=True);raw=a.profile.read_bytes();(a.output/(d['id']+'.profile.json')).write_bytes(raw)
s=SecondaryState(d);frames=[]
for i in range(1500):
 dt=[1/60,1/24,1/120,0][i%4];speed=0 if i<60 or i>1100 else .9*(1+.2*math.sin(i*.02));signal=math.sin(i*.051)
 frames.append({'delta':dt,'speed':speed,'strideSignal':signal,'angles':s.step(dt,speed,signal)})
(a.output/(d['id']+'.secondary-vectors.json')).write_text(json.dumps({'profileSha256':hashlib.sha256(raw).hexdigest(),'frames':frames},separators=(',',':')))
print(d['id'],'exported validated profile and',len(frames),'cross-runtime reference frames')
from eonwild_motion.attention import resolve_attention,attention_vectors
attention=resolve_attention(d)
if attention:
 (a.output/(d['id']+'.attention-vectors.json')).write_text(json.dumps({'profileSha256':hashlib.sha256(raw).hexdigest(),'attention':attention,'frames':attention_vectors(attention)},indent=2)+'\n')

if 'locomotion' in d:
 from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities,resolve_walk
 c=resolve_capabilities(d)
 (a.output/(d['id']+'.capabilities.json')).write_text(json.dumps({'profileSha256':hashlib.sha256(raw).hexdigest(),'resolved':c,'walking':resolve_walk(c)},indent=2)+'\n')
