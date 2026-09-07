"""Exact temporary staging; materialize module blobs and remove from PR tree."""
from pathlib import Path
import hashlib,json,subprocess
edits={
 'src/eonwild_motion/solve/performance.py':('c42cb82a3f9b76703587ad86c0adc73e760839f7',
   '    result["loop"] = plan.get("loop", True)\n    return result',
   '    result["loop"] = plan.get("loop", True)\n    from ..planning.foot_articulation import declare_pad_recovery\n    declare_pad_recovery(result)\n    return result'),
 'src/eonwild_motion/solve/airborne_gait.py':('53e3751acaf444f375d6af5791c624964034ad9b',
   'free_pitch = _qrotvec(tuple(lateral * math.radians(foot_plan["foot_pitch_degrees"] * (1 - support_lock))))',
   'free_pitch = _qrotvec(tuple(lateral * math.radians(foot_plan.get("pad_pitch_degrees", 0.) * (1 - support_lock))))')
}
for name,(expected,before,after) in edits.items():
    path=Path(name);raw=path.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected
    text=raw.decode();assert text.count(before)==1;text=text.replace(before,after,1);path.write_text(text)
    response=subprocess.run(['gh','api','repos/hurtener/eonwild-factory/git/blobs','--method','POST','--input','-'],
       input=json.dumps({'content':text,'encoding':'utf-8'}),text=True,capture_output=True,check=True)
    print('PAD_RECOVERY_MODULE '+json.dumps({'path':name,'blob':json.loads(response.stdout)['sha']}),flush=True)
subprocess.run(['git','diff','--check'],check=True)
