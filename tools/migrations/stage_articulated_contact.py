"""One-shot source edit staging for the unavailable local execution container.

NOT a motion program and never a factory import. Edits only the exact recorded
source blob; uploads immutable text blobs for an explicit, separate reviewed
commit. Does not move branch refs, commit, approve motion or mutate reference
assets. Remove from the final active PR tree after materializing the source.
"""
from pathlib import Path
import hashlib
import json
import subprocess

path=Path('src/eonwild_motion/solve/airborne_gait.py')
raw=path.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='68627342518f36007165554a9b6d1054f30870ef'
text=raw.decode()

def edit(before,after):
    global text
    assert text.count(before)==1, before[:100]
    text=text.replace(before,after,1)

edit('''            foot_plan = row["feet"][side]
            for toe_chain in toes[side]:''','''            foot_plan = row["feet"][side]
            material_partition = "performance" in plan
            swing_phase = foot_plan["swing_phase"]
            support_lock = (1.0 if foot_plan["contact"] else
                            1 - _smooth(min(swing_phase, 1 - swing_phase) / .18))
            for toe_chain in toes[side]:''')
edit('''                    flex = foot_plan["toe_flex_degrees"] * (0.45 if index == 0 else 0.275)
                    rot[n]''','''                    flex = foot_plan["toe_flex_degrees"] * (0.45 if index == 0 else 0.275)
                    if material_partition:
                        flex *= 1 - support_lock
                    rot[n]''')
edit('''                candidate_foot = nominal_foot + initial_tip_offset - np.asarray(_qrotate(candidate_q, tuple(flexed_tip_offset)))
                rotated_roots''','''                candidate_foot = (nominal_foot.copy() if material_partition else
                                  nominal_foot + initial_tip_offset - np.asarray(_qrotate(candidate_q, tuple(flexed_tip_offset))))
                rotated_roots''')
edit('''                for _ in range((48 if "performance" in plan else 18) if lock > 1e-12 else 0):''','''                for _ in range(18 if not material_partition and lock > 1e-12 else 0):''')
edit('''            for _ in range(7):
                best = min''','''            # Resolve the actual articulation more accurately, rather than
            # filtering serialized rotations after contact validation. The
            # old reproduction path retains its exact seven refinements.
            for _ in range(14 if material_partition else 7):
                best = min''')
edit('''            rot[ankle] = _world_rotation(source, w, ankle, desired_ankle_q)
            w = _world_matrices(source, tr, rot, base_s)
            # During contact''','''            rot[ankle] = _world_rotation(source, w, ankle, desired_ankle_q)
            w = _world_matrices(source, tr, rot, base_s)
            if material_partition:
                # The ankle/metatarsal is NOT the contact pad. Articulate it
                # around the stationary foot root while the MTP joint keeps
                # the load-bearing pad and digits in their calibrated frame.
                # Release that frame C2 during swing, allowing authored fold
                # and digit flex. No per-bone translation/scale is introduced.
                free_pitch = _qrotvec(tuple(lateral * math.radians(solved_pitch * (1 - support_lock))))
                foot_world = _qmul(free_pitch, _rotation_from_matrix(base_w[foot]))
                rot[foot] = _world_rotation(source, w, foot, foot_world)
                w = _world_matrices(source, tr, rot, base_s)
            # During contact''')
edit('''            for tc in toes[side]:
                if len(tc) != 3:''','''            for tc in toes[side]:
                if material_partition:
                    # Calibrated FK, not a nearly straight two-link toe IK:
                    # at full support the fixed foot frame plus zero local
                    # flex makes EVERY toe landmark stationary. During swing
                    # the existing bounded flex is explicit choreography.
                    # Final material-point and skeleton checks remain required.
                    continue
                if len(tc) != 3:''')
path.write_text(text)
subprocess.run(['git','diff','--check'],check=True)
content=path.read_bytes()
print('STAGED_ARTICULATED_SOURCE_SHA256',hashlib.sha256(content).hexdigest(),flush=True)
response=subprocess.run(['gh','api','repos/hurtener/eonwild-factory/git/blobs','--method','POST','--input','-'],
    input=json.dumps({'content':text,'encoding':'utf-8'}),text=True,capture_output=True,check=True)
print('STAGED_ARTICULATED_GIT_BLOB',json.loads(response.stdout)['sha'],flush=True)
