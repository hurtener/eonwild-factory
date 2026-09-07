"""Exact source staging only; materialize blob and remove before the PR update."""
from pathlib import Path
import hashlib,json,subprocess
path=Path('src/eonwild_motion/planning/gait_transition.py');raw=path.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='a5954cd8a67347149001ef2ec70a1a052df77405'
text=raw.decode();before='from .grounded_gait import GroundedGait, sample_grounded_gait, smooth'
assert text.count(before)==1;text=text.replace(before,before+', touchdown_reach')
before='self.reach = math.copysign(gait.touchdown_reach_body_heights * height, self.speed)'
assert text.count(before)==1;text=text.replace(before,'self.reach = (touchdown_reach(gait, height) if isinstance(gait, GroundedGait) else\n                      math.copysign(gait.touchdown_reach_body_heights * height, self.speed))')
path.write_text(text)
subprocess.run(['git','diff','--check'],check=True)
response=subprocess.run(['gh','api','repos/hurtener/eonwild-factory/git/blobs','--method','POST','--input','-'],
 input=json.dumps({'content':text,'encoding':'utf-8'}),text=True,capture_output=True,check=True)
print('CENTERED_TRANSITION_BLOB '+json.loads(response.stdout)['sha'],flush=True)
