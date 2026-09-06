"""One-use source migration for this interrupted session; remove before PR.

This is not imported by the engine or any behavior program. Every replacement
requires an exact inspected source fragment. Approved source assets are not
modified, and no engineering threshold is changed.
"""
from pathlib import Path
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def replace(path, old, new):
    target = ROOT / path
    text = target.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f'{path}: expected one exact source fragment: {old[:100]!r}')
    target.write_text(text.replace(old, new))


engine = 'src/eonwild_motion/solve/airborne_gait.py'
replace(engine, '    rows = plan["samples"]\n    times = [row["time_s"] for row in rows]', '''    rows = plan["samples"]
    if plan.get("program") == "gait_transition":
        # Sample the same steady response, not a fresh lag initialized at zero
        # or a fictitious cyclic start/stop carrier. All pose layers share the
        # behavior-owned phase; the quintic gain has zero endpoint derivatives.
        steady = driven_body_response(gait, build_airborne_plan(gait, plan["body_height_m"]), roles)
        reference_times = np.asarray([r["time_s"] for r in steady["samples"]])
        names = set().union(*(r["sagittal_node_degrees"] for r in steady["samples"]))
        from .performance import phase_and_gain
        result = []
        for row in rows:
            phase, gain = phase_and_gain(row)
            angles = {name: gain * float(np.interp(phase, reference_times,
                [r["sagittal_node_degrees"].get(name, 0.) for r in steady["samples"]])) for name in names}
            result.append({"time_s": row["time_s"], "support_count": row["support_count"],
                "normalized_vertical_motion_drive": gain * float(np.interp(phase, reference_times,
                    [r["normalized_vertical_motion_drive"] for r in steady["samples"]])),
                "sagittal_node_degrees": angles})
        return {"classification": "phase-preserving bounded kinematic transition response; no cyclic claim for a one-shot",
            "reference_cyclic_state_seam_degrees": steady["maximum_cyclic_state_seam_degrees"], "samples": result}
    times = [row["time_s"] for row in rows]''')
replace(engine, '    frames_t, frames_r, emitted = [], [], []', '''    # Digit bend planes belong to neutral anatomy. Projecting the *moving*
    # toe elbow becomes ill-conditioned at extension and can choose the other
    # branch on the last loop sample despite identical endpoint targets.
    toe_normals = {}
    if "performance" in plan:
        for side, chains in toes.items():
            for a, b, c in chains:
                pa, pb, pc = (np.asarray(_world_position(base_w[n])) for n in (a, b, c))
                normal = np.cross(pb - pa, pc - pb)
                toe_normals[a] = _unit(normal if np.linalg.norm(normal) > 1e-8 else lateral)
    frames_t, frames_r, emitted = [], [], []''')
replace(engine, '        tr, rot = base_t[:], base_r[:]\n        root_delta', '''        tr, rot = base_t[:], base_r[:]
        from .performance import phase_and_gain
        motion_time, performance_gain = phase_and_gain(row)
        root_delta''')
replace(engine, 'math.radians(total / len(names))', 'math.radians(performance_gain * total / len(names))')
replace(engine, 'math.radians(jaw_breathing_angle(gait, row["time_s"]))', 'math.radians(performance_gain * jaw_breathing_angle(gait, motion_time))')
replace(engine, '                hip_target = gait.swing_hip_lift_degrees * recovery', '                hip_target = gait.swing_hip_lift_degrees * recovery * foot_plan.get("articulation_scale", 1.)')
replace(engine, '''                bend = pb - pa - direction * float((pb - pa) @ direction)
                if np.linalg.norm(bend) < 1e-8:
                    bend = up - direction * float(up @ direction)''', '''                if "performance" in plan:
                    foot_delta = _qmul(_rotation_from_matrix(w[foot]), _qinv(_rotation_from_matrix(base_w[foot])))
                    normal = np.asarray(_qrotate(foot_delta, tuple(toe_normals[a])))
                    bend = np.cross(direction, normal)
                else:
                    # Immutable legacy path for accepted baseline builds.
                    bend = pb - pa - direction * float((pb - pa) @ direction)
                    if np.linalg.norm(bend) < 1e-8:
                        bend = up - direction * float(up @ direction)''')

skin = 'src/eonwild_motion/solve/skin_targets.py'
replace(skin, 'def evaluate_skin(glb, profile, plan):\n    frames, metadata = skin_frames(glb, profile)', '''def evaluate_skin(glb, profile, plan, *, world_offsets=None):
    frames, metadata = skin_frames(glb, profile)
    if world_offsets is not None:
        # Evaluate the actual in-place skin with the motor's planned travel.
        # Offsets alter the evaluation coordinate frame, never the GLB, floor,
        # witness identities, support flags, or engineering tolerances.
        offsets = np.asarray(world_offsets, dtype=float)
        if offsets.shape != (len(frames), 3) or not np.isfinite(offsets).all():
            raise ContractError("in-place world reconstruction requires one finite offset per sample")
        frames = deepcopy(frames)
        for frame, offset in zip(frames, offsets):
            frame["root_m"] = (np.asarray(frame["root_m"]) + offset).tolist()
            for foot in frame["feet"].values():
                for region in ("sole_points", "toe_points"):
                    for point in foot[region]:
                        point["point_m"] = (np.asarray(point["point_m"]) + offset).tolist()''')
replace(skin, 'def _cyclic_fill(times, values, loaded):', 'def _cyclic_fill(times, values, loaded, *, loop=True):')
replace(skin, '''        a, b = (before[-1] if len(before) else indices[-1]), (after[0] if len(after) else indices[0])''', '''        if not loop and (not len(before) or not len(after)):
            # A one-shot must not borrow contact corrections from its other
            # endpoint: entry/exit contact belongs to its adjacent behavior.
            result[i] = values[after[0] if len(after) else before[-1]]
            continue
        a, b = (before[-1] if len(before) else indices[-1]), (after[0] if len(after) else indices[0])''')
replace(skin, '            correction = _cyclic_fill(times, correction, loaded)', '            correction = _cyclic_fill(times, correction, loaded, loop=current.get("loop", True))')

compiler = 'src/eonwild_motion/factory/compiler.py'
replace(compiler, '''    receipt["final_skinned_contact_gate"] = surface["verdict"]
    receipt["final_skinned_contact_scope"] = "reopened serialized root-motion authority at the locked floor; full skin influences"''', '''    in_place_surface = {"verdict": "NOT_MEASURED", "reason": "no bound skinned contact profile"}
    if "contact_profile" in snapshots:
        try:
            origin_travel = plan["samples"][0]["root_forward_m"]
            offsets = [forward * (row["root_forward_m"] - origin_travel) for row in plan["samples"]]
            in_place_surface = evaluate_skin(outputs["in_place"], json.loads(snapshots["contact_profile"]), plan,
                world_offsets=offsets)
        except (ContractError, ValueError, KeyError, StopIteration) as exc:
            in_place_surface = {"verdict": "FAIL", "reason": f"in-place skinned reconstruction failed: {exc}"}
    receipt["final_skinned_contact_gate"] = "PASS" if surface["verdict"] == in_place_surface["verdict"] == "PASS" else "FAIL"
    receipt["final_skinned_contact_scope"] = "both reopened serialized exports; in-place plus planned motor travel; locked floor and full skin influences"''')
replace(compiler, 'and surface["verdict"] == "PASS")', 'and surface["verdict"] == "PASS" and in_place_surface["verdict"] == "PASS")')
replace(compiler, '"solver_feasibility": feasibility, "skinned_contact": surface,', '"solver_feasibility": feasibility, "skinned_contact": surface, "in_place_skinned_contact": in_place_surface,')

subprocess.run(['python', '-m', 'compileall', '-q', 'src/eonwild_motion'], cwd=ROOT, check=True)
print('SOURCE_REPAIRS_COMPILE; no acceptance claim; engineering thresholds unchanged')
