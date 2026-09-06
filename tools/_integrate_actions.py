"""One-use source integration; removed by the installing branch job."""
from pathlib import Path
import json, hashlib


def change(path, old, new):
    p=Path(path);text=p.read_text()
    if text.count(old)!=1:raise RuntimeError(f'patch context mismatch {path}: {old[:100]}')
    p.write_text(text.replace(old,new))

c='src/eonwild_motion/factory/compiler.py'
change(c,'PROGRAMS = ("airborne_gait", "grounded_gait")','PROGRAMS = ("airborne_gait", "grounded_gait", "supported_action")')
change(c,'from ..solve.skin_targets import solve_with_skin_targets, evaluate_skin','from ..solve.skin_targets import solve_with_skin_targets, evaluate_skin\nfrom ..planning.supported_action import load_supported_action\nfrom ..solve.supported_action import solve_supported_action')
change(c,'    height = geometry_height(source, roles, up)','    height = geometry_height(source, roles, up)\n    supported = recipe["program"] == "supported_action"')
change(c,'    else:\n        grounded = load_grounded_gait(profile)','    elif not supported:\n        grounded = load_grounded_gait(profile)')
change(c,'    if "performance_profile" in snapshots:\n        plan = decorate_plan','    if supported:\n        if "contact_profile" not in snapshots or "performance_profile" in snapshots:\n            raise ContractError("supported actions require contact data and their own performance channels")\n        action = load_supported_action(profile)\n        gait = AirborneGait(max_joint_angular_velocity_degrees_per_s=action.max_joint_rate_degrees_per_second)\n        root_raw, inplace_raw, plan, receipt = solve_supported_action(source, semantic_roles=roles, action=action,\n            contact_profile=json.loads(snapshots["contact_profile"]), up_axis=up, forward_axis=forward, body_height_m=height)\n    if "performance_profile" in snapshots:\n        plan = decorate_plan')
change(c,'    if plan.get("performance", {}).get("skin_refinement", False):','    if supported:\n        pass  # Already solved by the persistent-support program above.\n    elif plan.get("performance", {}).get("skin_refinement", False):')
change(c,'    if "performance_profile" in snapshots and "contact_profile" in snapshots:','    if ("performance_profile" in snapshots or supported) and "contact_profile" in snapshots:')
change(c,'    refinement_ok = receipt.get("skin_target_refinement", {}).get("converged", True)','    refinement_ok = receipt.get("skin_target_refinement", {}).get("converged", True) and receipt.get("oral_contact", {"status":"PASS"})["status"] == "PASS"')
change(c,'"outputs": evaluated, "rotation_rates": rates, "solver_feasibility": feasibility, "skinned_contact": surface,','"outputs": evaluated, "rotation_rates": rates, "solver_feasibility": feasibility, "skinned_contact": surface,\n        "oral_contact": receipt.get("oral_contact"),')
change(c,'animation.setdefault("extras", {}).update(program=recipe["program"], loop=True,','animation.setdefault("extras", {}).update(program=recipe["program"], loop=plan.get("loop", True),')
change(c,'"duration_s": plan["samples"][-1]["time_s"], "loop": True,','"duration_s": plan["samples"][-1]["time_s"], "loop": plan.get("loop", True),')
change(c,'"events": event_track(plan), "plan_sha256": digest(json_bytes(plan)),','"events": sorted(event_track(plan) + plan.get("events", []), key=lambda e: e["time_s"]), "plan_sha256": digest(json_bytes(plan)),')
change(c,'"skeleton_contact_stationary": max_tip_drift <= 0.001}','"skeleton_contact_stationary": max_tip_drift <= 0.001}\n    if not plan.get("loop", True):\n        del checks["rotation_loop_closed"]')
# Material targets intentionally move skeleton proxies by bounded offsets.
# Evaluate their target-relative error with the original tolerance; the skin
# authority still evaluates all real floor points without this compensation.
change(c,'            previous_tips[side] = tips','            previous_tips[side] = tips') if False else None
change(c,'            if previous_row is not None and row["feet"][side]["contact"] and previous_row["feet"][side]["contact"]:\n                max_tip_drift = max(max_tip_drift, float(np.linalg.norm(tips - previous_tips[side], axis=1).max()))',
'''            if previous_row is not None and row["feet"][side]["contact"] and previous_row["feet"][side]["contact"]:
                planned_delta = np.asarray(row["feet"][side].get("target_offset_m", [0.,0.,0.])) - np.asarray(previous_row["feet"][side].get("target_offset_m", [0.,0.,0.]))
                max_tip_drift = max(max_tip_drift, float(np.linalg.norm(tips - previous_tips[side] - planned_delta, axis=1).max()))''')
change(c,'"classification": "reopened skeleton proxy; not skinned-contact or physical validation"','"classification": "reopened skeleton target-relative proxy; explicit pre-solve skin offsets accounted for, final material contact independently checked"')
s='src/eonwild_motion/solve/skin_targets.py'
change(s,'origin = patch[witness] - forward * current["samples"][first]["feet"][side]["forward_m"]','origin = patch - forward * current["samples"][first]["feet"][side]["forward_m"]')
change(s,'                    error = target - patch[witness]','                    active = patch[:, index_up] <= patch[:, index_up].min() + .001\n                    # Fit the currently loaded material points to immutable\n                    # touchdown witnesses, not just one arbitrarily low point.\n                    errors = target[active] - patch[active]\n                    error = .5 * (errors.max(axis=0) + errors.min(axis=0))')
change(s,'"witnesses": {side: {"patch_index": int(value[0]), "anchor_origin_m": value[1].tolist()} for side, value in anchors.items()},','"witnesses": {side: {"initial_lowest_patch_index": int(value[0]), "material_anchor_origins_m": value[1].tolist()} for side, value in anchors.items()},')
q='src/eonwild_motion/factory/quality.py'
change(q,'    peak = 0.0','    peak = 0.0\n    witness = None\n    channel_count = 0')
change(q,'            peak = max(peak, float(np.max(angles / np.diff(times))))','''            speed = angles / np.diff(times)
            index = int(np.argmax(speed)); channel_count += 1
            if float(speed[index]) > peak:
                peak = float(speed[index])
                node = int(channel["target"]["node"])
                witness = {"node": node, "bone": glb.nodes[node].get("name"), "times_s": times[index:index+2].tolist(),
                           "quaternions_xyzw": quaternions[index:index+2].tolist()}
    if not channel_count:
        raise ContractError("rotation witness requires at least one actual rotation channel")''')
change(q,'"maximum_degrees_per_s": peak, "limit_degrees_per_s": maximum_degrees_per_s,','"maximum_degrees_per_s": peak, "limit_degrees_per_s": maximum_degrees_per_s, "peak_witness": witness,')
# More iterations on the opt-in material-constrained toe reach intersection.
change('src/eonwild_motion/solve/airborne_gait.py','for _ in range(18 if lock > 1e-12 else 0):','for _ in range((48 if "performance" in plan else 18) if lock > 1e-12 else 0):')
# Recover the reviewed V9 supported performance DATA, not its code/import graph.
old=json.loads(Path('build/V9-FEEDING-REVIEW-003/profile.json').read_text())
bounds=json.loads(Path('profiles/v9/body-articulation.grounded-bite.v1.json').read_text())['joint_pitch_limits_degrees']
base=json.loads(Path('recipes/heavy-biped/run.v2.json').read_text())
profile={'schema':'eonwild.motion.supported-action.v1','duration_seconds':6.,'reference_duration_seconds':6.,'sample_hz':60,'loop':False,
    'gape_degrees':58.,'max_joint_rate_degrees_per_second':220.,'lane_width_body_heights':.3,
    'base_pitch_degrees':old['base_pitch_degrees'],'yaw_weights':old['yaw_weights'],'channels':old['channels'],
    'support_limits':old['support_limits'],'joint_pitch_limits_degrees':bounds,'anchor':old['anchor'],
    'events':[{'name':e['name']+'_CUE','reference_time_seconds':e['reference_time_seconds']} for e in old['events']],
    'reference_basis':'V9 Feeding003 authored channels; user reference video informs performance review, not forces or biology',
    'classification':'persistent support and skinned oral-centroid constraints; runtime owns actual world interaction'}

def write(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    return {'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def emit(name,p):
    recipe=dict(base);recipe.update(id='heavy-biped.'+name,version=int(name.rsplit('v',1)[1]),program='supported_action',description=p['classification'])
    recipe['program_profile']=write('catalog/programs/heavy-biped.'+name+'.json',p)
    write('recipes/heavy-biped/'+name+'.json',recipe)
emit('feeding.v1',profile)
for name,duration,body,drop,fore,yaw,jaw,tail,loop in [
    ('idle.v1',6.,[[0,.02],[3,.08],[6,.02]],[[0,0],[3,.006],[6,0]],[[0,0],[6,0]],[[0,0],[6,0]],[[0,0],[6,0]],[[0,0],[3,.2],[6,0]],True),
    ('alert.v1',3.,[[0,0],[1.2,-.18],[2.,-.15],[6,0]],[[0,0],[6,0]],[[0,0],[6,0]],[[0,0],[1.2,15],[3.,15],[4.6,-10],[6,0]],[[0,0],[6,0]],[[0,0],[2,.25],[6,0]],False),
    ('bite-miss.v1',3.2,[[0,.05],[1.3,.32],[2.1,.73],[2.45,.88],[3.3,.40],[4.8,.20],[6,.05]],[[0,0],[1.4,.02],[2.4,.08],[3.2,.025],[6,0]],[[0,0],[1.3,-.02],[2.25,.025],[2.6,.035],[3.6,-.012],[6,0]],[[0,0],[2.4,-2],[3.2,4],[6,0]],[[0,0],[1.4,.08],[1.95,.7],[2.35,.65],[2.55,.02],[3.5,.08],[4.5,0],[6,0]],[[0,0],[2.6,1.2],[3.6,-.25],[6,0]],False),
    ('call.v1',4.,[[0,0],[1.2,-.15],[2.2,-.22],[3.8,-.15],[6,0]],[[0,0],[2,.01],[6,0]],[[0,0],[6,0]],[[0,0],[2,3],[4,-2],[6,0]],[[0,0],[1.2,.1],[2.,.52],[3.,.58],[4.2,.12],[5,0],[6,0]],[[0,0],[2.,.3],[4.,-.1],[6,0]],False)]:
    p=json.loads(json.dumps(profile));p.update(duration_seconds=duration,loop=loop,anchor=None,max_joint_rate_degrees_per_second=360.)
    p['channels']={'body':body,'drop':drop,'forward':fore,'lateral':[[0,0],[6,0]],'yaw':yaw,'jaw':jaw,'tail':tail}
    p['events']=[{'name':'ANTICIPATION_START','reference_time_seconds':0},{'name':'RECOVERY_START','reference_time_seconds':3.},{'name':'ACTION_COMPLETE','reference_time_seconds':6.}]
    p['classification']='authored supported '+name.split('.')[0]+' performance using the shared V9 body/contact program; not a gameplay contact fact'
    emit(name,p)
