"""Independent diagnostic; not source derivative authority or emitted acceptance."""
from pathlib import Path
import importlib.util, sys, json, hashlib
import numpy as np
base=Path(__file__).resolve().parent
path=base/'root-source-quadratic-inputs-83aa5e5.py'
spec=importlib.util.spec_from_file_location('root_interface_inputs',path)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
programs={k:m.build(k) for k in ('steady','start','stop')}
phase=m.declared_handoff_phase(programs['start'].transition,programs['steady'].grounded)
joints=sorted({int(i) for skin in programs['steady'].source.document['skins'] for i in skin['joints']})
names=m.node_names(programs['steady'].source)
assert len(joints)>=70
for side in ('left','right'):
    print(side,'material rows',len(m.evaluate(programs['steady'],phase).material_points[side]),flush=True)
rows=[]
for label,left,tleft,right,tright in [('start',programs['start'],float(programs['start'].plan['duration_s']),programs['steady'],phase),('stop',programs['steady'],phase,programs['stop'],0.)]:
    left0=m.evaluate(left,tleft);right0=m.evaluate(right,tright)
    for h in (1e-3,3e-4,1e-4,3e-5):
        a=m.evaluate(left,tleft-h);aa=m.evaluate(left,tleft-2*h)
        b=m.evaluate(right,tright+h);bb=m.evaluate(right,tright+2*h)
        def estimate(y0,y1,y2,back):
            return ((3*y0-4*y1+y2) if back else (-3*y0+4*y1-y2))/(2*h)
        lv=estimate(left0.worlds[joints,:3,3],a.worlds[joints,:3,3],aa.worlds[joints,:3,3],True)
        rv=estimate(right0.worlds[joints,:3,3],b.worlds[joints,:3,3],bb.worlds[joints,:3,3],False)
        joint=m.max_rows(lv-rv,[names[i] for i in joints])
        errors={}
        for side in ('left','right'):
            vl=estimate(left0.material_points[side],a.material_points[side],aa.material_points[side],True)
            vr=estimate(right0.material_points[side],b.material_points[side],bb.material_points[side],False)
            errors[side]=vl-vr
        material=m.max_material(errors)
        row={'join':label,'h_s':h,'joint_velocity_difference_mps':joint,'ordered_foot_material_velocity_difference_mps':material}
        rows.append(row); print(label,h,joint['maximum'],material['maximum'],flush=True)
result={'classification':'independent second-order one-sided source finite-difference diagnostic; no emitted/C1/derivative-authority verdict','source_head':'83aa5e5391848493c902af0c6bd4ecab6228afe6','input_builder_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for program in programs.values() for p in program.input_paths.values()},'recipes':{k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in m.RECIPES.items()},'declared_phase_s':phase,'skin_joint_count':len(joints),'skin_joint_ids':joints,'joint_labels':[names[i] for i in joints],'rows':rows}
(base/'root-source-quadratic-probe.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
