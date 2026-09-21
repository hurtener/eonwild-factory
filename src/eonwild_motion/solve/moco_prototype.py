"""Optional offline planar/spatial mechanics experiment, independent of runtime imports.

OpenSim is deliberately imported only by entry points. Internal joint actuators
have finite activation dynamics. The free root has NO actuators or reserves;
gravity and compliant toe contacts supply its external forces. Proportions and
total mass come from semantic admission. Remaining priors are explicitly authored.
"""
from __future__ import annotations

import hashlib
import json
import math
import contextlib
from copy import deepcopy
from pathlib import Path

import numpy as np


def dimensions(admission):
    p = {k: np.asarray(v, dtype=float) for k, v in admission["points"].items()}
    lengths = np.mean([
        [np.linalg.norm(p[f"{side}Leg.{i+1}"] - p[f"{side}Leg.{i}"]) for i in range(3)]
        for side in ("left", "right")], axis=0)
    toes = [v[0] - p["leftLeg.3"][0] for k, v in p.items()
            if k.startswith("legs.left.toeChains.") and k.endswith(".2")]
    return p, lengths, float(max(toes))


def make_model(admission, recipe):
    import opensim as o

    points, lengths, toe_length = dimensions(admission)
    body_mass = admission["animal"]["measurements"]["body_mass"]
    if body_mass.get("unit") != "kg":
        raise ValueError("Moco admission body mass must explicitly use kg")
    mass = float(body_mass["value"])
    if not math.isfinite(mass) or mass <= 0 or not np.isfinite(lengths).all() or np.any(lengths <= 0) or toe_length <= 0:
        raise ValueError("Moco requires positive finite mass and segment lengths")
    total_length = float(sum(lengths))
    spatial = recipe.get("spatial")
    calibrated = recipe.get('calibrated_task')
    if calibrated:
        from .moco_tasks import foot_geometry
        foot = foot_geometry(admission, recipe)
    fractions = recipe["mass_fractions"]
    fraction_sum = sum(v * (2 if k.endswith("_each") else 1) for k, v in fractions.items())
    if abs(fraction_sum - 1) > 1e-9:
        raise ValueError("Segment mass fractions must sum to one")
    model = o.Model()
    model.setName("semantic_spatial_stride_prototype" if spatial else "semantic_planar_stride_prototype")
    model.setGravity(o.Vec3(0, -9.80665, 0))
    metadata = {"mass_kg": mass, "segment_lengths_m": lengths.tolist(),
                "toe_length_m": toe_length, "segments": {}, "coordinates": {},
                "actuators": {}, "contacts": [], "clearance_frames": [], "root_reserves": []}

    def vec(v):
        return o.Vec3(*map(float, v))

    def body(name, fraction, center, extent, radius):
        m = mass * fraction
        # Uniform cylinder about its principal axis; general axis in XY.
        d = np.asarray(extent, dtype=float)
        L = float(np.linalg.norm(d))
        axis = d / max(L, 1e-9)
        axial = .5 * m * radius ** 2
        transverse = m * (3 * radius ** 2 + L ** 2) / 12
        tensor = transverse * np.eye(3) + (axial - transverse) * np.outer(axis, axis)
        inertia = o.Inertia(float(tensor[0, 0]), float(tensor[1, 1]), float(tensor[2, 2]),
                            float(tensor[0, 1]), float(tensor[0, 2]), float(tensor[1, 2]))
        b = o.Body(name, m, vec(center), inertia)
        model.addBody(b)
        metadata["segments"][name] = {"mass_kg": m, "com_local_m": list(map(float, center)),
            "inertia_kg_m2": tensor.tolist(), "extent_local_m": list(map(float, extent)),
            "radius_m": radius}
        return b

    trunk = body("trunk", fractions["trunk"], [(.22 if calibrated else .42)*points['neck.0'][0], -.021*total_length, 0],
                 [2*points['neck.0'][0], 0, 0], .265*total_length)
    if spatial:
        from .moco_spatial import spatial_joint
        root=spatial_joint('root',model.getGround(),[0,0,0],trunk,
            [('pitch',(0,0,1)),('yaw',(0,1,0)),('roll',(1,0,0))],
            ('forward','height','lateral'))
        metadata['spatial']=spatial
    else:
        root = o.PlanarJoint("root", model.getGround(), o.Vec3(0), o.Vec3(0),
                             trunk, o.Vec3(0), o.Vec3(0))
        for i, name in enumerate(("pitch", "forward", "height")):
            root.upd_coordinates(i).setName(name)
    model.addJoint(root)
    coordinates = {}

    def pin(name, parent, location, child, bounds, capacity):
        extra=spatial.get('joint_axes',{}).get(name,{}) if spatial else {}
        axes=[(name,(0,0,1))]
        for suffix,axis in [('yaw',(0,1,0)),('roll',(1,0,0))]:
            if suffix in extra:axes.append((name+'_'+suffix,axis))
        if extra:
            j=spatial_joint(name,parent,location,child,axes)
        else:
            j=o.PinJoint(name,parent,vec(location),o.Vec3(0),child,o.Vec3(0),o.Vec3(0))
            j.updCoordinate().setName(name)
        model.addJoint(j)
        for index,(coordinate,axis) in enumerate(axes):
            c=j.upd_coordinates(index);c.setName(coordinate)
            b=bounds if index==0 else extra[coordinate.rsplit('_',1)[-1]]['bounds']
            cap=capacity if index==0 else capacity*extra[coordinate.rsplit('_',1)[-1]]['capacity_ratio']
            c.setRangeMin(b[0]);c.setRangeMax(b[1]);coordinates[coordinate]=c
            act=o.ActivationCoordinateActuator();act.setName('motor_'+coordinate);act.setCoordinate(c)
            force=cap*mass*9.80665*total_length;act.setOptimalForce(force)
            act.setMinControl(-1);act.setMaxControl(1)
            act.set_activation_time_constant(recipe['activation_time_constant_s']);act.set_default_activation(0)
            model.addForce(act)
            metadata['coordinates'][coordinate]={'bounds_rad':list(b),'joint':name,'axis':axis}
            metadata['actuators']['motor_'+coordinate]={'capacity_Nm':force,'activation_time_constant_s':recipe['activation_time_constant_s']}
            passive=recipe.get('passive_support',{}).get(coordinate)
            if not passive and recipe.get('joint_viscosity_capacity_seconds') and name.startswith(('hip_','knee_','ankle_','mtp_','digit_')):
                passive={'stiffness_BW_leg_length':0.,'damping_BW_leg_length_s':cap*recipe['joint_viscosity_capacity_seconds'],'rest_radians':0.}
            if passive:
                spring=o.SpringGeneralizedForce(coordinate);spring.setName('passive_'+coordinate)
                spring.set_stiffness(passive['stiffness_BW_leg_length']*mass*9.80665*total_length)
                spring.set_viscosity(passive['damping_BW_leg_length_s']*mass*9.80665*total_length)
                spring.set_rest_length(passive['rest_radians']);model.addForce(spring)
                metadata.setdefault('passive_support',{})[coordinate]=passive
        return j

    capacities = recipe["capacity_body_weight_leg_length"]
    for suffix, semantic in (("l", "left"), ("r", "right")):
        thigh = body("thigh_" + suffix, fractions["thigh_each"], [0, -lengths[0]*.45, 0],
                     [0, -lengths[0], 0], .083*total_length)
        shin = body("shin_" + suffix, fractions["shin_each"], [0, -lengths[1]*.43, 0],
                    [0, -lengths[1], 0], .046*total_length)
        meta = body("metatarsus_" + suffix, fractions["metatarsus_each"], [0, -lengths[2]*.5, 0],
                    [0, -lengths[2], 0], .031*total_length)
        extent = np.array(foot['toe_midpoint_m']) if calibrated else np.array([toe_length,0,0])
        toe = body("toe_" + suffix, fractions["toe_each"], extent*.48,
                   extent, .021*total_length)
        pin("hip_"+suffix, trunk, [0, 0, points[semantic+"Leg.0"][2]], thigh,
            [-.80, 1.45], capacities["hip"])
        pin("knee_"+suffix, thigh, [0, -lengths[0], 0], shin,
            [-2.0, -.16], capacities["knee"])
        pin("ankle_"+suffix, shin, [0, -lengths[1], 0], meta,
            [.15, 2.25], capacities["ankle"])
        pin("mtp_"+suffix, meta, [0, -lengths[2], 0], toe,
            [-1.25, 1.25], capacities["mtp"])
        if calibrated:
            distal_extent = np.array([toe_length, -.10, 0])-extent
            digit = body('digit_'+suffix, fractions['digit_each'], distal_extent*.45,
                         distal_extent, .016*total_length)
            pin('digit_'+suffix,toe,extent,digit,[-.35,.95],capacities['digit'])
            tip = o.PhysicalOffsetFrame('tip_digit_'+suffix,digit,o.Transform(vec(distal_extent)))
            model.addComponent(tip)
        # Contact spheres alone leave gaps in the foot's physical envelope.
        # Keep the MTP center and distal toe bone above the floor as well; this
        # prevents an optimizer from burying the articulation while perching on
        # a sphere with the toes pointing almost vertically upwards.
        end = o.PhysicalOffsetFrame("tip_toe_"+suffix, toe,
                                    o.Transform(vec(extent)))
        model.addComponent(end)
        metadata["clearance_frames"].extend([
            {"path":"/bodyset/toe_"+suffix, "minimum_height_m":.5*total_length*recipe["contact"]["radius_leg_length"]},
            {"path":"/tip_toe_"+suffix, "minimum_height_m":.002*total_length}])

    if spatial:
        from .moco_spatial import add_axial
        add_axial(model,metadata,points,fractions,capacities,total_length,body,pin,trunk,recipe)
    else:
        neck_origin = points["neck.0"].copy(); neck_origin[2] = 0
        neck_extent = points["head"] - neck_origin; neck_extent[2] = 0
        neck = body("neck", fractions["neck"], neck_extent*.60, neck_extent, .124*total_length)
        neck_parent = trunk
        if calibrated:
            chest_origin = points['spine.2'].copy(); chest_origin[2]=0
            chest_extent = neck_origin-chest_origin
            chest = body('chest', fractions['chest'], chest_extent*.55, chest_extent, .21*total_length)
            pin('chest',trunk,chest_origin,chest,[-.20,.20],capacities['chest'])
            metadata['chest_semantic_role']='spine.2'
            neck_parent=chest; neck_origin=chest_extent
        pin("neck", neck_parent, neck_origin, neck, [-.35, .35] if calibrated else [-.25,.25], capacities["neck"])
        tail_keys = sorted((k for k in points if k.startswith("tail.")), key=lambda s: int(s.split(".")[-1]))
        base = points[tail_keys[0]].copy(); base[2] = 0
        split = points[tail_keys[len(tail_keys)//2]].copy(); split[2] = 0
        tip = points[tail_keys[-1]].copy(); tip[2] = 0
        prox_extent, distal_extent = split-base, tip-split
        prox = body("tail_proximal", fractions["tail_proximal"], prox_extent*.36, prox_extent, .112*total_length)
        distal = body("tail_distal", fractions["tail_distal"], distal_extent*.36, distal_extent, .046*total_length)
        pin("tail_proximal", trunk, base, prox, [-.20, .20], capacities["tail_proximal"])
        pin("tail_distal", prox, prox_extent, distal, [-.32, .32], capacities["tail_distal"])

        for b, end, clearance in ((prox, prox_extent, .083*total_length), (distal, distal_extent, (.25 if calibrated else .05)*total_length)):
            frame = o.PhysicalOffsetFrame("tip_"+b.getName(), b, o.Transform(vec(end)))
            model.addComponent(frame)
            metadata["clearance_frames"].append({"path": "/tip_"+b.getName(), "minimum_height_m": clearance})

    ground = o.ContactHalfSpace(o.Vec3(0), o.Vec3(0, 0, -math.pi/2), model.getGround())
    ground.setName("floor")
    model.addContactGeometry(ground)
    contact = recipe["contact"]
    radius = total_length * contact["radius_leg_length"]
    for suffix in ("l", "r"):
        toe = model.updBodySet().get("toe_" + suffix)
        sites = foot['sites'] if calibrated else [dict(name=name,center_local_m=[toe_length*fraction,0,0],radius_m=radius,distal=False) for name,fraction in [('rear',.16),('front',.84)]]
        for site in sites:
            name,center,radius=site['name'],list(site['center_local_m']),site['radius_m']
            contact_body=model.updBodySet().get(('digit_' if site['distal'] else 'toe_')+suffix)
            sphere = o.ContactSphere(radius, vec(center), contact_body)
            sphere.setName("sphere_" + name + "_" + suffix)
            model.addContactGeometry(sphere)
            force = o.SmoothSphereHalfSpaceForce()
            force.setName("contact_" + name + "_" + suffix)
            force.connectSocket_sphere(sphere); force.connectSocket_half_space(ground)
            for key in ("static_friction", "dynamic_friction", "viscous_friction"):
                getattr(force, "set_" + key)(contact[key])
            force.set_stiffness(contact["stiffness_N_m2"]*site.get('stiffness_share',1.))
            force.set_dissipation(contact["dissipation_s_m"])
            force.set_transition_velocity(contact["transition_velocity_mps"])
            force.set_constant_contact_force(1e-5)
            model.addForce(force)
            metadata["contacts"].append({"force": force.getName(), "body": contact_body.getName(),
                                         "center_local_m": center, "radius_m": radius})
    if calibrated: metadata['foot_geometry']=foot
    model.finalizeConnections()
    if spatial:
        from .moco_spatial import calibrate_axial_capacity
        calibrate_axial_capacity(model,metadata,recipe)
    state = model.initSystem()
    metadata["model_mass_kg"] = model.getTotalMass(state)
    return model, metadata


def seed_coordinates(admission, recipe, times):
    """Analytic task-space initialization only; no authored clip is imported."""
    _, lengths, _ = dimensions(admission)
    L1, L2, L3 = lengths
    L = sum(lengths)
    speed = admission["preferred_speed_mps"]
    step = admission["step_length_m"]
    half_period = step / speed
    phase = times / (2*half_period)
    radius = recipe["contact"]["radius_leg_length"] * L
    height = .78*L + .018*np.cos(4*np.pi*phase)
    q = {"pitch": np.zeros_like(times), "forward": times*speed, "height": height}
    for suffix, offset in (("l", 0), ("r", .5)):
        ph = (phase+offset) % 1
        swing = np.clip((ph-.5)*2, 0, 1)
        # Hermite endpoint velocities match stance belt speed. Full-stride period
        # and contact schedule are only an optimizer seed, not enforced goals.
        h = 10*swing**3 - 15*swing**4 + 6*swing**5
        bend = swing - 10*swing**3 + 15*swing**4 - 6*swing**5
        fx = np.where(ph < .5, step*.5 - 2*step*ph, -step*.5 + step*h - step*bend)
        fy = radius-.009 + .23*np.sin(np.pi*swing)**2
        theta = .45 + .30*np.sin(np.pi*swing)**2
        dx = fx - L3*np.sin(theta)
        dy = fy-height + L3*np.cos(theta)
        d = np.hypot(dx, dy)
        k = -np.arccos(np.clip((d*d-L1*L1-L2*L2)/(2*L1*L2), -.99, .98))
        hip = np.arctan2(dx, -dy) + np.arccos(np.clip((L1*L1+d*d-L2*L2)/(2*L1*d), -.99, .99))
        q["hip_"+suffix] = hip
        q["knee_"+suffix] = k
        q["ankle_"+suffix] = theta-hip-k
        q["mtp_"+suffix] = -theta
    for name in ("neck", "tail_proximal", "tail_distal"):
        q[name] = np.zeros_like(times)
    return q


def make_study(model, metadata, admission, recipe, mesh=25, warm_start=None):
    import opensim as o

    study = o.MocoStudy()
    study.setName("spatial_stride_prototype" if recipe.get('spatial') else "planar_stride_prototype")
    problem = study.updProblem()
    problem.setModelAsCopy(model)
    speed, step = admission["preferred_speed_mps"], admission["step_length_m"]
    if not all(math.isfinite(x) and x > 0 for x in (speed, step)):
        raise ValueError("Moco task needs positive finite speed and step length")
    duration = step/speed
    problem.setTimeBounds(0, duration)
    L = sum(metadata["segment_lengths_m"])
    problem.setStateInfoPattern(".*/speed", [-18, 18])
    problem.setStateInfoPattern(".*/activation", [-1, 1])
    problem.setStateInfo("/jointset/root/pitch/value", [-.16, .16])
    problem.setStateInfo("/jointset/root/forward/value", [0, step*1.3], 0, step)
    floor_offset=metadata.get('foot_geometry',{}).get('sole_depth_m',0.)
    problem.setStateInfo("/jointset/root/height/value", [.60*L+floor_offset, (.96 if floor_offset else .91)*L+floor_offset])
    problem.setStateInfo("/jointset/root/forward/speed", [.3*speed, 1.7*speed])
    problem.setStateInfo("/jointset/root/height/speed", [-3.5, 3.5])
    for name, data in metadata["coordinates"].items():
        problem.setStateInfo(f"/jointset/{data.get('joint',name)}/{name}/value", data["bounds_rad"])

    if recipe.get('spatial'):
        bounds=recipe['spatial']['root_bounds']
        for name in ('yaw','roll','lateral'):
            problem.setStateInfo(f'/jointset/root/{name}/value',bounds[name])
            problem.setStateInfo(f'/jointset/root/{name}/speed',[-3,3])
    periodic = o.MocoPeriodicityGoal("half_stride_symmetry")
    problem.addGoal(periodic)
    def opposite(name):
        if recipe.get('spatial'):
            import re
            return re.sub(r'_(l|r)(?=_|/|$)',lambda m:'_r' if m.group(1)=='l' else '_l',name)
        if "_l/" in name or name.endswith("_l"):
            return name.replace("_l/", "_r/") if "_l/" in name else name[:-2]+"_r"
        if "_r/" in name or name.endswith("_r"):
            return name.replace("_r/", "_l/") if "_r/" in name else name[:-2]+"_l"
        return name
    names = model.getStateVariableNames()
    for i in range(names.getSize()):
        name = names.get(i)
        if name != "/jointset/root/forward/value":
            from .moco_spatial import reflected_coordinate
            coordinate=name.split('/')[-2].removeprefix('motor_')
            method=periodic.addNegatedStatePair if recipe.get('spatial') and reflected_coordinate(coordinate) else periodic.addStatePair
            method(o.MocoPeriodicityGoalPair(name, opposite(name)))
    for name in metadata["actuators"]:
        path = "/forceset/"+name
        from .moco_spatial import reflected_coordinate
        method=periodic.addNegatedControlPair if recipe.get('spatial') and reflected_coordinate(name.removeprefix('motor_')) else periodic.addControlPair
        method(o.MocoPeriodicityGoalPair(path, opposite(path)))
    effort = o.MocoControlGoal("bounded_joint_effort", recipe["optimization"]["effort_weight"])
    problem.addGoal(effort)
    for frame in metadata["clearance_frames"]:
        clearance = o.MocoOutputConstraint()
        clearance.setName(frame["path"].strip("/").replace("/","_")+"_clearance")
        clearance.setOutputPath(frame["path"]+"|position")
        clearance.setOutputIndex(1)
        bounds = o.StdVectorMocoBounds(); bounds.append(o.MocoBounds(frame["minimum_height_m"], 10))
        clearance.updConstraintInfo().setBounds(bounds)
        problem.addPathConstraint(clearance)
    bw = metadata["mass_kg"]*9.80665
    for contact in metadata["contacts"]:
        goal = o.MocoOutputGoal(contact["force"]+"_force_cost", recipe["optimization"].get("contact_force_weight",1.0)/(bw*bw))
        goal.setOutputPath("/forceset/"+contact["force"]+"|sphere_force")
        # SpatialVec stores moment first, force second. Select vertical force
        # explicitly; its six-component norm would mix N and Nm.
        goal.setOutputIndex(4)
        goal.setExponent(2)
        problem.addGoal(goal)
    if recipe.get('calibrated_task'):
        from .moco_tasks import add_tracking
        if recipe.get('attention'):
            if not warm_start:raise ValueError('Focused attention requires a physical warm start')
            from .moco_tasks import admit_attention_reference
            admit_attention_reference(model,metadata,warm_start,speed)
        add_tracking(problem,admission,metadata,recipe)
        continuation_weight=recipe['optimization'].get('continuation_tracking_weight',0.)
        if continuation_weight:
            if not warm_start:raise ValueError('Continuation requires a saved physical solution')
            from .moco_tasks import add_continuation_tracking
            add_continuation_tracking(problem,warm_start,metadata,continuation_weight,
                                      recipe['optimization'].get('full_body_continuation',False))
            foot_weight=recipe['optimization'].get('continuation_foot_weight',0.)
            if foot_weight:
                from .moco_tasks import add_foot_continuation
                add_foot_continuation(problem,model,warm_start,metadata,foot_weight)
        acceleration_weight=recipe['optimization'].get('distal_acceleration_weight',0.)
        if acceleration_weight:
            for side in ('l','r'):
                for part in ('shin','metatarsus','toe','digit'):
                    goal=o.MocoOutputGoal('smooth_'+part+'_'+side,acceleration_weight)
                    goal.setOutputPath('/bodyset/'+part+'_'+side+'|angular_acceleration')
                    goal.setExponent(2);problem.addGoal(goal)
    solver = study.initCasADiSolver()
    solver.set_num_mesh_intervals(mesh)
    dynamics_mode = recipe["optimization"].get("dynamics_mode", "explicit")
    solver.set_multibody_dynamics_mode(dynamics_mode)
    if dynamics_mode == "implicit":
        solver.set_minimize_implicit_multibody_accelerations(True)
        solver.set_implicit_multibody_accelerations_weight(recipe["optimization"]["acceleration_weight"])
        solver.set_implicit_multibody_acceleration_bounds(o.MocoBounds(-300, 300))
    solver.set_optim_max_iterations(recipe["optimization"]["max_iterations"])
    solver.set_optim_constraint_tolerance(recipe["optimization"]["constraint_tolerance"])
    solver.set_optim_convergence_tolerance(recipe["optimization"]["convergence_tolerance"])
    solver.set_scale_variables_using_bounds(True)
    solver.set_optim_sparsity_detection(recipe['optimization'].get('sparsity_detection','none'))
    solver.set_optim_finite_difference_scheme(recipe['optimization'].get('finite_difference_scheme','central'))
    solver.set_interpolate_control_mesh_interior_points(recipe['optimization'].get('linear_controls', False))
    solver.set_enforce_path_constraint_mesh_interior_points(True)
    solver.set_parallel(4)
    solver.set_optim_ipopt_print_level(5)
    if recipe.get('calibrated_task'):solver.set_output_interval(25)
    if warm_start:
        if spatial := recipe.get('spatial'):
            from .moco_spatial import transfer_guess
            guess=transfer_guess(solver,warm_start,model,metadata)
            if 'reference_directory' in metadata:guess.write(str(Path(metadata['reference_directory'])/'initial-guess.sto'))
            solver.setGuess(guess)
        else:
            solver.setGuessFile(str(warm_start))
    else:
        guess = solver.createGuess()
        times = np.linspace(0, duration, 2*mesh+1)
        guess.setNumTimes(len(times))
        def ov(arr):
            v = o.Vector(len(arr), 0)
            for i, x in enumerate(arr): v[i] = float(x)
            return v
        guess.setTime(ov(times))
        if recipe.get('calibrated_task'):
            from .moco_tasks import seed
            seed_fn=lambda times:seed(admission,metadata,recipe,times)
        else: seed_fn=lambda times:seed_coordinates(admission,recipe,times)
        coords = seed_fn(times)
        # Differentiate across the periodic boundary, not a clipped one-sided
        # recovery endpoint, to give the optimizer a continuous initial guess.
        eps = 1e-5
        before = seed_fn(times-eps)
        after = seed_fn(times+eps)
        for name in guess.getStateNames():
            if name.endswith("/activation"):
                values = np.zeros_like(times)
            else:
                coord, kind = name.split("/")[-2:]
                values = coords[coord] if kind == "value" else (after[coord]-before[coord])/(2*eps)
            guess.setState(name, ov(values))
        for name in guess.getControlNames():
            guess.setControl(name, ov(np.zeros_like(times)))
        for name in guess.getDerivativeNames():
            guess.setDerivative(name, ov(np.zeros_like(times)))
        solver.setGuess(guess)
    return study


def run(admission_path, recipe_path, output, mesh=25, warm_start=None, build_only=False):
    import opensim as o

    output = Path(output).resolve()
    if (output/"solution.sto").exists():
        raise FileExistsError("Use a new candidate directory; solved artifacts are retained")
    output.mkdir(parents=True, exist_ok=True)
    o.Logger.removeFileSink()
    o.Logger.addFileSink(str(output/"opensim.log"))
    admission = json.loads(Path(admission_path).read_text())
    recipe = json.loads(Path(recipe_path).read_text())
    model, metadata = make_model(admission, recipe)
    metadata.update({"schema": "eonwild.motion.moco-model-receipt.v1", "opensim": o.GetVersion(),
        "classification": recipe["classification"], "admission": admission, "recipe": recipe,
        "mesh_intervals": mesh, "status": "BUILT_NOT_SOLVED", "user_review": "PENDING"})
    if recipe.get('calibrated_task'):metadata['reference_directory']=str(output)
    model.printToXML(str(output/"model.osim"))
    metadata["model_sha256"] = hashlib.sha256((output/"model.osim").read_bytes()).hexdigest()
    (output/"model-receipt.json").write_text(json.dumps(metadata, indent=2)+"\n")
    mass_unit=recipe['optimization'].get('mass_unit_kg',1.)
    if not math.isfinite(mass_unit) or mass_unit<=0:raise ValueError('Positive optimization mass unit required')
    if mass_unit!=1:
        # Unit conditioning only: m, s and mass_unit kg. Every mass, inertia,
        # motor, spring and contact stiffness changes by the same factor.
        # Simbody's Hertz force is linear in its stiffness property. Keeping
        # geometric/velocity smoothing unchanged preserves accelerations.
        scaled_admission=deepcopy(admission);scaled_recipe=deepcopy(recipe)
        scaled_admission['animal']['measurements']['body_mass']['value']/=mass_unit
        scaled_recipe['contact']['stiffness_N_m2']/=mass_unit
        solve_model,solve_metadata=make_model(scaled_admission,scaled_recipe)
        solve_metadata.update(admission=admission,recipe=recipe,reference_directory=str(output),optimization_mass_unit_kg=mass_unit)
        solve_model.printToXML(str(output/'optimization-model.osim'))
        metadata['optimization_mass_unit_kg']=mass_unit
        metadata['optimization_model_sha256']=hashlib.sha256((output/'optimization-model.osim').read_bytes()).hexdigest()
        (output/'model-receipt.json').write_text(json.dumps(metadata,indent=2)+'\n')
    else:solve_model,solve_metadata=model,metadata
    study = make_study(solve_model, solve_metadata, admission, recipe, mesh, warm_start)
    for name in ('attention_reference_offset_m','attention_reference_provenance'):
        if name in solve_metadata:metadata[name]=solve_metadata[name]
    (output/'model-receipt.json').write_text(json.dumps(metadata,indent=2)+'\n')
    study.printToXML(str(output/"study.omoco"))
    if build_only:
        return
    with contextlib.chdir(output):
        solution = study.solve()
    success = bool(solution.success())
    if solution.isSealed(): solution.unseal()
    report = {"success": success, "status": solution.getStatus(),
              "iterations": solution.getNumIterations(), "objective": solution.getObjective(),
              "mesh_intervals": mesh, "model_sha256": metadata["model_sha256"],
              "claim": "Discretized optimizer result; physical replay and mesh refinement are separate checks"}
    solution.write(str(output/"solution.sto"))
    (output/"solve-receipt.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report), flush=True)
    return report
