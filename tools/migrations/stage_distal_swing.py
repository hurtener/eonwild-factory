"""Exact single source edit staging, not a motion recipe or production import.

Do not publish this helper in the active PR: materialize its emitted immutable
module blob instead. No commit, ref, asset, floor or threshold writes.
"""
from pathlib import Path
import hashlib,json,subprocess
path=Path('src/eonwild_motion/solve/airborne_gait.py');raw=path.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='7d8a0c48ec38fd55c0e93baca76f5aaf22299819'
text=raw.decode()
before='free_pitch = _qrotvec(tuple(lateral * math.radians(solved_pitch * (1 - support_lock))))'
after='free_pitch = _qrotvec(tuple(lateral * math.radians(foot_plan["foot_pitch_degrees"] * (1 - support_lock))))'
assert text.count(before)==1
text=text.replace(before,after,1)
path.write_text(text)
subprocess.run(['git','diff','--check'],check=True)
result=subprocess.run(['gh','api','repos/hurtener/eonwild-factory/git/blobs','--method','POST','--input','-'],
 input=json.dumps({'content':text,'encoding':'utf-8'}),text=True,capture_output=True,check=True)
print('DISTAL_SWING_SOURCE '+json.dumps({'blob':json.loads(result.stdout)['sha'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}),flush=True)
