"""One-time branch migration; removed by the installing job, never imported."""
from pathlib import Path
import json
import hashlib


def change(path, old, new):
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f'non-unique patch context: {path}: {old[:100]}')
    p.write_text(text.replace(old, new))


solver = 'src/eonwild_motion/solve/airborne_gait.py'
change(solver, '        facts = {}\n        for side, chain in legs.items():', '        from .performance import apply_performance\n        apply_performance(source, tr, rot, base_s, base_w, roles, plan, row, up, forward)\n        facts = {}\n        for side, chain in legs.items():')
change(solver, '            foot_height = float(np.asarray(_world_position(base_w[foot])) @ up - ground)', '            if "performance" in plan:\n                side_lane = math.copysign(.5 * plan["performance"]["lane_width_body_heights"] * body_height, side_lane)\n            foot_height = float(np.asarray(_world_position(base_w[foot])) @ up - ground)')
change(solver, '            nominal_foot = desired_foot.copy()', '            correction = np.asarray(foot_plan.get("target_offset_m", [0., 0., 0.]), dtype=float)\n            if correction.shape != (3,) or not np.isfinite(correction).all() or np.linalg.norm(correction) > .06 * body_height:\n                raise ContractError("invalid bounded skin target correction")\n            desired_foot += correction\n            nominal_foot = desired_foot.copy()')
change(solver, '            delta = _orientation_from_bend(kp - hp, anatomical_normals[side], desired_knee - hp, desired_normal)', '            source_normal = (_unit(np.cross(kp - hp, ap - kp)) if "performance" in plan else anatomical_normals[side])\n            delta = _orientation_from_bend(kp - hp, source_normal, desired_knee - hp, desired_normal)')
compiler = 'src/eonwild_motion/factory/compiler.py'
change(compiler, 'from .source import geometry_height', 'from .source import geometry_height\nfrom ..solve.performance import load_performance, decorate_plan\nfrom ..solve.skin_targets import solve_with_skin_targets, evaluate_skin')
change(compiler, '{"contact_profile", "description", "supersedes"}', '{"contact_profile", "performance_profile", "description", "supersedes"}')
change(compiler, '    return recipe, paths', '    if "performance_profile" in recipe:\n        paths["performance_profile"] = locked_file(root, recipe["performance_profile"])\n    return recipe, paths')
change(compiler, 'sample_hz=grounded.sample_hz, swing_hip_lift_degrees=0)', 'sample_hz=grounded.sample_hz, swing_hip_lift_degrees=grounded.swing_hip_lift_degrees)')
change(compiler, '    validate_plan(plan, recipe["program"])', '    if "performance_profile" in snapshots:\n        plan = decorate_plan(plan, load_performance(json.loads(snapshots["performance_profile"])))\n    validate_plan(plan, recipe["program"])')
change(compiler, '    root_raw, inplace_raw, _, receipt = solve_airborne_gait(source, source_clip=None,\n        semantic_roles=roles, gait=gait, up_axis=tuple(up), forward_axis=tuple(forward),\n        plan_override=plan, legacy_overlay=False)', '    if plan.get("performance", {}).get("skin_refinement", False):\n        if "contact_profile" not in snapshots:\n            raise ContractError("skin refinement requires a locked contact profile")\n        root_raw, inplace_raw, plan, receipt = solve_with_skin_targets(source, semantic_roles=roles,\n            gait=gait, up_axis=up, forward_axis=forward, plan=plan,\n            contact_profile=json.loads(snapshots["contact_profile"]))\n    else:\n        root_raw, inplace_raw, _, receipt = solve_airborne_gait(source, source_clip=None,\n            semantic_roles=roles, gait=gait, up_axis=tuple(up), forward_axis=tuple(forward),\n            plan_override=plan, legacy_overlay=False)')
change(compiler, '    technical = (all(row["status"] == "PASS" for row in evaluated.values()) and', '    if "performance_profile" in snapshots and "contact_profile" in snapshots:\n        surface = evaluate_skin(outputs["root_motion"], json.loads(snapshots["contact_profile"]), plan)\n    refinement_ok = receipt.get("skin_target_refinement", {}).get("converged", True)\n    technical = (refinement_ok and all(row["status"] == "PASS" for row in evaluated.values()) and')
change(compiler, '        "unity_import_status": "NOT_VERIFIED"}', '        "unity_import_status": "NOT_VERIFIED",\n        "ground_plane": (json.loads(snapshots["contact_profile"])["geometry"]["ground"] if "contact_profile" in snapshots else None)}')
# Match V9 recovery polarity rather than holding a plantarflexed paddle.
change('src/eonwild_motion/planning/grounded_gait.py', 'pitch = gait.push_off_pitch_degrees * (1 - smooth(swing / .35)) + gait.foot_recovery_pitch_degrees * recovery', 'pitch = gait.push_off_pitch_degrees * (1 - smooth(swing / .35)) - gait.foot_recovery_pitch_degrees * recovery')
renderer = 'tools/render_candidate.py'
change(renderer, 'choices=("side", "three-quarter")', 'choices=("side", "three-quarter", "front", "rear")')
change(renderer, '    camera_data = bpy.data.cameras.new("ReviewCamera")', '    if args.view in ("front", "rear"):\n        offset = forward * (1 if args.view == "front" else -1)\n    camera_data = bpy.data.cameras.new("ReviewCamera")')
change(renderer, '    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(center.x, center.y, low.z - .005))', '    plane = runtime.get("ground_plane")\n    if plane is None:\n        raise ValueError("review requires the explicit package ground plane")\n    if plane["up_axis"] != "Y":\n        raise ValueError("this Blender review scene currently supports Y-up sources only")\n    ground_level = float(plane["level_m"])\n    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(center.x, center.y, ground_level))')
change(renderer, '"presentation": "CPU studio study; bbox presentation floor is not contact validation"', '"ground_level_m": ground_level, "presentation": "fixed declared contact floor; no bbox floor fitting; review is not approval"')
# New recipes leave all old input bytes and approved takes untouched.
def write(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    return {'path': path, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
base = json.loads(Path('recipes/heavy-biped/run.v2.json').read_text())
perf = {'schema': 'eonwild.motion.performance.v1', 'classification': 'art-directed coordination; no force or biological claim',
    'parameters': {'lane_width_body_heights': .24, 'pelvis_sway_body_heights': .006, 'pelvis_yaw_degrees': 2., 'pelvis_roll_degrees': .6,
                   'tail_yaw_degrees': 12., 'tail_lag_fraction': .12, 'gaze_elevation_degrees': 3., 'center_tail': True, 'skin_refinement': True}}
for name, length, step, duty, reach, clear, recover in [('walk.v2',.6,.9,.62,.25,.14,28),('fast-walk.v1',.6,.7,.57,.25,.16,30),('reverse-walk.v3',-.38,1.,.68,.20,.12,22)]:
    program = {'schema':'eonwild.motion.v9.grounded-gait.v1','parameters':{'step_period_s':step,'step_length_body_heights':length,
        'duty_factor':duty,'touchdown_reach_body_heights':reach,'swing_clearance_body_heights':clear,'pelvis_crouch_body_heights':.035,
        'pelvis_excursion_body_heights':.016,'cycles':1,'sample_hz':120,'toe_flex_degrees':24.,'foot_recovery_pitch_degrees':recover,
        'push_off_pitch_degrees':20. if length>0 else 10.,'push_off_start_fraction':.6,'swing_hip_lift_degrees':30. if length>0 else 12.,'rounded_swing_peak_fraction':.42}}
    recipe = dict(base);recipe.update(id='heavy-biped.'+name,version=int(name.rsplit('v',1)[1]),program='grounded_gait',description='V9 articulated grounded gait with explicit narrow lanes; candidate requires visual review')
    recipe['program_profile']=write('catalog/programs/heavy-biped.'+name+'.json',program)
    recipe['performance_profile']=write('catalog/performance/heavy-biped.'+name+'.json',perf)
    write('recipes/heavy-biped/'+name+'.json',recipe)
for gaitname in ['run','sprint']:
    program=json.loads(Path('catalog/programs/heavy-biped.'+gaitname+'.v2.json').read_text())
    program['parameters']['articulation_preferred_margin_degrees']=8.
    # Keep the accepted V9 stride, support and launch landmarks. Only add a
    # preferred smooth articulation region; do not slow playback to hide rates.
    perf2=json.loads(json.dumps(perf));perf2['parameters']['gaze_elevation_degrees']=5. if gaitname=='sprint' else 3.
    recipe=dict(base);recipe.update(id='heavy-biped.'+gaitname+'.v3',version=3,description='V9 stride retained; material contact, lateral tail and independent gaze')
    recipe['program_profile']=write('catalog/programs/heavy-biped.'+gaitname+'.v3.json',program)
    recipe['performance_profile']=write('catalog/performance/heavy-biped.'+gaitname+'.v3.json',perf2)
    write('recipes/heavy-biped/'+gaitname+'.v3.json',recipe)
