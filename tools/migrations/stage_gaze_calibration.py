"""Temporary exact source staging; not a generator, no commits/ref writes.

Materialize the returned immutable blobs into their real module paths and
remove this staging utility before updating the active PR.
"""
from pathlib import Path
import hashlib,json,subprocess

changes={
 'src/eonwild_motion/factory/compiler.py':[
  ('from ..solve.supported_action import solve_supported_action',
   'from ..solve.supported_action import solve_supported_action\nfrom ..solve.gaze import calibrate_rostral_direction'),
  ('        plan = decorate_plan(plan, load_performance(json.loads(snapshots["performance_profile"])))',
   '        plan = decorate_plan(plan, load_performance(json.loads(snapshots["performance_profile"])))\n        if "contact_profile" not in snapshots:\n            raise ContractError("forward attention requires locked geometry calibration")\n        plan["gaze_calibration"] = calibrate_rostral_direction(source, roles=roles,\n            contact_profile=json.loads(snapshots["contact_profile"]), forward_axis=forward, up_axis=up)')],
 'src/eonwild_motion/solve/performance.py':[
  ('    neutral_forward = _qrotate(_qinv(_rotation_from_matrix(base_worlds[head])), tuple(forward))',
   '    calibration = plan.get("gaze_calibration")\n    if calibration is None:\n        # Preserve the low-level/synthetic compatibility path. The active\n        # factory supplies a geometry-derived rostral axis explicitly.\n        neutral_forward = _qrotate(_qinv(_rotation_from_matrix(base_worlds[head])), tuple(forward))\n    else:\n        from .gaze import load_rostral_axis\n        neutral_forward = load_rostral_axis(calibration, roles["head"])')]
}
expected={'src/eonwild_motion/factory/compiler.py':'1cca9e81eb365c8a172add2f48af09859ff26ccc',
          'src/eonwild_motion/solve/performance.py':'03538049e58157297d2b18bc2288cb4088ab57ec'}
for name,edits in changes.items():
    path=Path(name);raw=path.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected[name]
    text=raw.decode()
    for before,after in edits:
        assert text.count(before)==1,before
        text=text.replace(before,after,1)
    path.write_text(text)
    result=subprocess.run(['gh','api','repos/hurtener/eonwild-factory/git/blobs','--method','POST','--input','-'],
        input=json.dumps({'content':text,'encoding':'utf-8'}),text=True,capture_output=True,check=True)
    print('GAZE_MODULE_BLOB '+json.dumps({'path':name,'git_blob':json.loads(result.stdout)['sha'],
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}),flush=True)
subprocess.run(['git','diff','--check'],check=True)
