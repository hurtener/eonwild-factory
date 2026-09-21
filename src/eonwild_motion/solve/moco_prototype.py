"""Optional offline planar mechanics experiment, independent of runtime imports.

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
    fractions = recipe["mass_fractions"]
    fraction_sum = sum(v * (2 if k.endswith("_each") else 1) for k, v in fractions.items())
    if abs(fraction_sum - 1) > 1e-9:
        raise ValueError("Segment mass fractions must sum to one")
    model = o.Model()
    model.setName("semantic_planar_stride_prototype")
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

    trunk = body("trunk", fractions["trunk"], [.42*points['neck.0'][0], -.021*total_length, 0],
                 [2*points['neck.0'][0], 0, 0], .265*total_length)
    root = o.PlanarJoint("root", model.getGround(), o.Vec3(0), o.Vec3(0),
                         trunk, o.Vec3(0), o.Vec3(0))
    root_names = ("pitch", "forward", "height")
    for i, name in enumerate(root_names):
        root.upd_coordinates(i).setName(name)
    model.addJoint(root)
    coordinates = {}

    def pin(name, parent, location, child, bounds, capacity):
        j = o.PinJoint(name, parent, vec(location), o.Vec3(0), child, o.Vec3(0), o.Vec3(0))
        c = j.updCoordinate()
        c.setName(name)
        c.setRangeMin(bounds[0]); c.setRangeMax(bounds[1])
        model.addJoint(j)
        coordinates[name] = c
        act = o.ActivationCoordinateActuator()
        act.setName("motor_" + name)
        act.setCoordinate(c)
        force = capacity * mass * 9.80665 * total_length
        act.setOptimalForce(force)
        act.setMinControl(-1); act.setMaxControl(1)
        act.set_activation_time_constant(recipe["activation_time_constant_s"])
        act.set_default_activation(0)
        model.addForce(act)
        metadata["coordinates"][name] = {"bounds_rad": list(bounds)}
        metadata["actuators"]["motor_" + name] = {"capacity_Nm": force,
                "activation_time_constant_s": recipe["activation_time_constant_s"]}
        return j

    capacities = recipe["capacity_body_weight_leg_length"]
    for suffix, semantic in (("l", "left"), ("r", "right")):
        thigh = body("thigh_" + suffix, fractions["thigh_each"], [0, -lengths[0]*.45, 0],
                     [0, -lengths[0], 0], .083*total_length)
        shin = body("shin_" + suffix, fractions["shin_each"], [0, -lengths[1]*.43, 0],
                    [0, -lengths[1], 0], .046*total_length)
        meta = body("metatarsus_" + suffix, fractions["metatarsus_each"], [0, -lengths[2]*.5, 0],
                    [0, -lengths[2], 0], .031*total_length)
        toe = body("toe_" + suffix, fractions["toe_each"], [toe_length*.48, 0, 0],
                   [toe_length, 0, 0], .021*total_length)
        pin("hip_"+suffix, trunk, [0, 0, points[semantic+"Leg.0"][2]], thigh,
            [-.80, 1.45], capacities["hip"])
        pin("knee_"+suffix, thigh, [0, -lengths[0], 0], shin,
            [-2.0, -.16], capacities["knee"])
        pin("ankle_"+suffix, shin, [0, -lengths[1], 0], meta,
            [.15, 2.25], capacities["ankle"])
        pin("mtp_"+suffix, meta, [0, -lengths[2], 0], toe,
            [-1.25, 1.25], capacities["mtp"])
        # Contact spheres alone leave gaps in the foot's physical envelope.
        # Keep the MTP center and distal toe bone above the floor as well; this
        # prevents an optimizer from burying the articulation while perching on
        # a sphere with the toes pointing almost vertically upwards.
        end = o.PhysicalOffsetFrame("tip_toe_"+suffix, toe,
                                    o.Transform(o.Vec3(toe_length, 0, 0)))
        model.addComponent(end)
        metadata["clearance_frames"].extend([
            {"path":"/bodyset/toe_"+suffix, "minimum_height_m":.5*total_length*recipe["contact"]["radius_leg_length"]},
            {"path":"/tip_toe_"+suffix, "minimum_height_m":.002*total_length}])

    neck_origin = points["neck.0"].copy(); neck_origin[2] = 0
    neck_extent = points["head"] - neck_origin; neck_extent[2] = 0
    neck = body("neck", fractions["neck"], neck_extent*.60, neck_extent, .124*total_length)
    pin("neck", trunk, neck_origin, neck, [-.25, .25], capacities["neck"])
    tail_keys = sorted((k for k in points if k.startswith("tail.")), key=lambda s: int(s.split(".")[-1]))
    base = points[tail_keys[0]].copy(); base[2] = 0
    split = points[tail_keys[len(tail_keys)//2]].copy(); split[2] = 0
    tip = points[tail_keys[-1]].copy(); tip[2] = 0
    prox_extent, distal_extent = split-base, tip-split
    prox = body("tail_proximal", fractions["tail_proximal"], prox_extent*.36, prox_extent, .112*total_length)
    distal = body("tail_distal", fractions["tail_distal"], distal_extent*.36, distal_extent, .046*total_length)
    pin("tail_proximal", trunk, base, prox, [-.20, .20], capacities["tail_proximal"])
    pin("tail_distal", prox, prox_extent, distal, [-.32, .32], capacities["tail_distal"])

    for b, end, clearance in ((prox, prox_extent, .083*total_length), (distal, distal_extent, .05*total_length)):
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
        for name, fraction in (("rear", .16), ("front", .84)):
            center = [toe_length * fraction, 0, 0]
            sphere = o.ContactSphere(radius, vec(center), toe)
            sphere.setName("sphere_" + name + "_" + suffix)
            model.addContactGeometry(sphere)
            force = o.SmoothSphereHalfSpaceForce()
            force.setName("contact_" + name + "_" + suffix)
            force.connectSocket_sphere(sphere); force.connectSocket_half_space(ground)
            for key in ("static_friction", "dynamic_friction", "viscous_friction"):
                getattr(force, "set_" + key)(contact[key])
            force.set_stiffness(contact["stiffness_N_m2"])
            force.set_dissipation(contact["dissipation_s_m"])
            force.set_transition_velocity(contact["transition_velocity_mps"])
            force.set_constant_contact_force(1e-5)
            model.addForce(force)
            metadata["contacts"].append({"force": force.getName(), "body": "toe_"+suffix,
                                         "center_local_m": center, "radius_m": radius})
    model.finalizeConnections()
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
    study.setName("planar_stride_prototype")
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
    problem.setStateInfo("/jointset/root/height/value", [.60*L, .91*L])
    problem.setStateInfo("/jointset/root/forward/speed", [.3*speed, 1.7*speed])
    problem.setStateInfo("/jointset/root/height/speed", [-3.5, 3.5])
    for name, data in metadata["coordinates"].items():
        problem.setStateInfo(f"/jointset/{name}/{name}/value", data["bounds_rad"])

    periodic = o.MocoPeriodicityGoal("half_stride_symmetry")
    problem.addGoal(periodic)
    def opposite(name):
        if "_l/" in name or name.endswith("_l"):
            return name.replace("_l/", "_r/") if "_l/" in name else name[:-2]+"_r"
        if "_r/" in name or name.endswith("_r"):
            return name.replace("_r/", "_l/") if "_r/" in name else name[:-2]+"_l"
        return name
    names = model.getStateVariableNames()
    for i in range(names.getSize()):
        name = names.get(i)
        if name != "/jointset/root/forward/value":
            periodic.addStatePair(o.MocoPeriodicityGoalPair(name, opposite(name)))
    for name in metadata["actuators"]:
        path = "/forceset/"+name
        periodic.addControlPair(o.MocoPeriodicityGoalPair(path, opposite(path)))
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
    solver.set_enforce_path_constraint_mesh_interior_points(True)
    solver.set_parallel(4)
    solver.set_optim_ipopt_print_level(5)
    if warm_start:
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
        coords = seed_coordinates(admission, recipe, times)
        # Differentiate across the periodic boundary, not a clipped one-sided
        # recovery endpoint, to give the optimizer a continuous initial guess.
        eps = 1e-5
        before = seed_coordinates(admission, recipe, times-eps)
        after = seed_coordinates(admission, recipe, times+eps)
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
    model.printToXML(str(output/"model.osim"))
    metadata["model_sha256"] = hashlib.sha256((output/"model.osim").read_bytes()).hexdigest()
    (output/"model-receipt.json").write_text(json.dumps(metadata, indent=2)+"\n")
    study = make_study(model, metadata, admission, recipe, mesh, warm_start)
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
