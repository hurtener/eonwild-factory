"""Ground-relative attack with actual skin-surface witnesses and rigid-foot IK.

Task-local engineering motion; semantic bindings, never species-name branches.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import grounded_committed_bite as B
from src.eonwild_motion.layers.leg_contact_resolve_v3 import _rotation_from_matrix


def phase(t, a):
    k = a["timing"]
    if t < k["anticipation_end"]:
        body = 0.12 * B.smooth(t / k["anticipation_end"])
    elif t < k["reach_end"]:
        body = 0.12 + 0.88 * B.smooth(
            (t - k["anticipation_end"]) / (k["reach_end"] - k["anticipation_end"])
        )
    elif t < k["hold_end"]:
        body = 1.0
    else:
        body = 1 - B.smooth((t - k["hold_end"]) / (k["recovery_end"] - k["hold_end"]))
    if t < k["anticipation_end"]:
        jaw = 0.0
    elif t < k["gape_peak"]:
        jaw = B.smooth(
            (t - k["anticipation_end"]) / (k["gape_peak"] - k["anticipation_end"])
        )
    elif t < k["reach_end"]:
        jaw = 1 - 0.65 * B.smooth(
            (t - k["gape_peak"]) / (k["reach_end"] - k["gape_peak"])
        )
    elif t < k["close_end"]:
        jaw = 0.35 - (0.35 - a["closed_hold_fraction"]) * B.smooth(
            (t - k["reach_end"]) / (k["close_end"] - k["reach_end"])
        )
    else:
        jaw = a["closed_hold_fraction"] * body
    return body, jaw


def matrix(q):
    x, y, z, w = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def axis_q(axis, angle):
    return np.asarray(B.S.qaxis(axis, float(angle)))


def least_squares(fun, initial, lo, hi, iterations=45, project=None):
    project = project or (lambda value: np.clip(value, lo, hi))
    x = project(np.asarray(initial, dtype=float))
    damping = 1e-4
    for _ in range(iterations):
        r = fun(x)
        if np.linalg.norm(r) < 1e-5:
            break
        eps = 1e-4
        jac = np.column_stack(
            [(fun(x + np.eye(len(x))[i] * eps) - r) / eps for i in range(len(x))]
        )
        step = np.linalg.solve(jac.T @ jac + np.eye(len(x)) * damping, -jac.T @ r)
        step = np.clip(step, -0.18, 0.18)
        trial = project(x + step)
        if np.linalg.norm(fun(trial)) < np.linalg.norm(r):
            x = trial
            damping = max(1e-7, damping * 0.5)
        else:
            damping = min(1e3, damping * 4)
    return x


def articulation_layout(rig, profile):
    """Resolve neutral-relative engineering limits by semantic chain position."""
    path = B.REPOSITORY / profile["body_articulation"]["path"]
    raw = path.read_bytes()
    config = json.loads(raw)
    groups = ("pelvis", "spine", "chest", "neck", "head")
    joints = []
    for role in groups:
        limits = config["joint_pitch_limits_degrees"][role]
        if len(limits) != len(rig.roles[role]):
            raise ValueError(f"articulation semantic joint count mismatch: {role}")
        for index, (node, bounds) in enumerate(zip(rig.roles[role], limits)):
            if not bounds[0] <= 0 <= bounds[1] or bounds[0] == bounds[1]:
                raise ValueError(f"invalid articulation bounds: {role}:{index}")
            joints.append((role, index, node, bounds))
    nodes = [item[2] for item in joints]
    if len(set(nodes)) != len(nodes):
        raise ValueError("overlapping body articulation semantic roles")
    curve = [
        i
        for i, row in enumerate(joints)
        if row[0] in config["cervical_curve"]["semantics"]
    ]
    for before, after in zip(curve, curve[1:]):
        if rig.parents[nodes[after]] != nodes[before]:
            raise ValueError("cervical semantic curve must follow the parent hierarchy")
    return config, joints, curve, B.sha(raw)


def measure_articulation(rig, profile, emitted):
    """Check actual serialized rotations, not the solver's intended angles."""
    config, joints, curve, profile_hash = articulation_layout(rig, profile)
    tracks, times = B._clip_state(emitted, "grounded_committed_bite")
    t0, r0, s0 = rig.pose(0)
    w0 = rig.world(t0, r0, s0)
    lateral = np.cross(np.array([0.0, 1.0, 0.0]), rig.forward)
    axes = [np.linalg.solve(w0[node, :3, :3], lateral) for _, _, node, _ in joints]
    axes = [axis / np.linalg.norm(axis) for axis in axes]
    head = rig.roles["head"][0]
    local_forward = np.linalg.solve(w0[head, :3, :3], rig.forward)
    maximum_curve = 0.0
    minimum_curve_pitch = 0.0
    minimum_action_curve_pitch = 0.0
    extrema = [[float("inf"), -float("inf")] for _ in joints]
    hold_pitch = []
    rows = []
    for index, time in enumerate(times):
        t, r, s = map(np.asarray, B._pose(emitted, tracks, index))
        _, source_r, _ = rig.pose(index)
        amount, _ = phase(float(time), profile["attack"])
        values = []
        action_values = []
        for j, (_, _, node, bounds) in enumerate(joints):
            inverse = np.r_[-r0[node, :3], r0[node, 3]]
            delta = np.asarray(B.S.qmul(inverse, r[node]))
            if delta[3] < 0:
                delta = -delta
            angle = float(np.degrees(2 * np.arctan2(delta[:3] @ axes[j], delta[3])))
            if not bounds[0] - 1e-4 <= angle <= bounds[1] + 1e-4:
                raise ValueError(
                    f"emitted articulation bound violated at {time}: {j}={angle}, bounds={bounds}"
                )
            extrema[j][0] = min(extrema[j][0], angle)
            extrema[j][1] = max(extrema[j][1], angle)
            values.append(angle)
            neutral = r0[node] if np.dot(source_r[node], r0[node]) >= 0 else -r0[node]
            baseline = (1 - amount) * source_r[node] + amount * neutral
            baseline /= np.linalg.norm(baseline)
            action_delta = np.asarray(
                B.S.qmul(np.r_[-baseline[:3], baseline[3]], r[node])
            )
            if action_delta[3] < 0:
                action_delta = -action_delta
            action_values.append(
                float(
                    np.degrees(
                        2 * np.arctan2(action_delta[:3] @ axes[j], action_delta[3])
                    )
                )
            )
        values = np.asarray(values)
        action_values = np.asarray(action_values)
        change = float(np.max(np.abs(np.diff(values[curve]))))
        maximum_curve = max(maximum_curve, change)
        minimum_curve_pitch = min(minimum_curve_pitch, float(values[curve].min()))
        if (
            change
            > config["cervical_curve"]["max_adjacent_pitch_change_degrees"] + 1e-4
        ):
            raise ValueError(f"emitted cervical curvature kink at {time}: {change}")
        minimum_action_curve_pitch = min(
            minimum_action_curve_pitch, float(action_values[curve].min())
        )
        if (
            action_values[curve].min()
            < -config["cervical_curve"]["max_reverse_pitch_degrees"] - 1e-4
        ):
            raise ValueError(
                f"emitted reverse cervical kink at {time}: action={action_values[curve]}"
            )
        w = rig.world(t, r, s)
        forward = w[head, :3, :3] @ local_forward
        pitch = float(np.degrees(np.arctan2(-forward[1], forward @ rig.forward)))
        if (
            profile["attack"]["timing"]["reach_end"]
            <= time
            <= profile["attack"]["timing"]["hold_end"]
        ):
            low, high = config["hold_head_nose_down_degrees"]
            if not low <= pitch <= high or values[-1] <= 0:
                raise ValueError(
                    f"emitted head must pivot nose-down during reach/hold at {time}: world={pitch}, local={values[-1]}"
                )
            hold_pitch.append(pitch)
        rows.append(
            {
                "time_seconds": float(time),
                "head_nose_down_degrees": pitch,
                "joint_pitch_degrees": values.tolist(),
                "action_joint_pitch_degrees": action_values.tolist(),
            }
        )
    return {
        "status": "PASS_EMITTED_ENGINEERING_LIMITS_NOT_BIOLOGICAL_VALIDATION",
        "sample_count": len(times),
        "profile_sha256": profile_hash,
        "joint_pitch_extrema_degrees": extrema,
        "maximum_adjacent_cervical_pitch_change_degrees": maximum_curve,
        "minimum_cervical_pitch_degrees": minimum_curve_pitch,
        "minimum_action_cervical_pitch_degrees": minimum_action_curve_pitch,
        "reverse_gate_basis": "action delta from source-idle-suppressed baseline; total emitted neutral-relative pitch independently obeys hard joint bounds",
        "hold_head_nose_down_range_degrees": [min(hold_pitch), max(hold_pitch)],
        "samples": rows,
    }


class Rig:
    def __init__(self, raw, profile):
        self.d, self.binary = B.S.parse_glb(raw)
        self.glb = B.Glb.from_bytes(raw)
        self.tracks, _ = B._clip_state(self.glb, profile["source"]["clip"])
        self.parents = [None] * len(self.d["nodes"])
        for parent, node in enumerate(self.d["nodes"]):
            for child in node.get("children", []):
                self.parents[child] = parent
        self.order = []

        def visit(i):
            if i in self.order:
                return
            if self.parents[i] is not None:
                visit(self.parents[i])
            self.order.append(i)

        for i in range(len(self.parents)):
            visit(i)
        names = {n.get("name"): i for i, n in enumerate(self.d["nodes"])}
        sr = json.loads((B.REPOSITORY / profile["semantic_rig"]["path"]).read_text())[
            "roles"
        ]
        self.roles = {
            key: [
                names[n] for n in ([sr[key]] if isinstance(sr[key], str) else sr[key])
            ]
            for key in ("pelvis", "spine", "chest", "neck", "head", "tail", "root")
        }
        self.legs = {
            side: [names[n] for n in sr["legs"][side]["contactChain"]]
            for side in ("left", "right")
        }
        self.roles["jaw_lower"] = B.binding_roles(
            json.loads((B.REPOSITORY / profile["semantic_binding"]["path"]).read_text())
        )["jaw_lower"]
        mesh_nodes = [
            node for node in self.d["nodes"] if "mesh" in node and "skin" in node
        ]
        if len(mesh_nodes) != 1:
            raise ValueError(
                "attack surface witness requires exactly one skinned mesh node"
            )
        mesh_node = mesh_nodes[0]
        skin = self.d["skins"][mesh_node["skin"]]
        self.joints = skin["joints"]
        primitives = self.d["meshes"][mesh_node["mesh"]]["primitives"]
        if len(primitives) != 1:
            raise ValueError(
                "attack surface witness currently requires exactly one skinned primitive"
            )
        attrs = primitives[0]["attributes"]

        def read(index):
            acc = self.d["accessors"][index]
            view = self.d["bufferViews"][acc["bufferView"]]
            dtype = np.dtype(
                {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[
                    acc["componentType"]
                ]
            )
            width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[
                acc["type"]
            ]
            return np.ndarray(
                (acc["count"], width),
                dtype=dtype,
                buffer=self.binary,
                offset=view.get("byteOffset", 0) + acc.get("byteOffset", 0),
                strides=(
                    view.get("byteStride", width * dtype.itemsize),
                    dtype.itemsize,
                ),
            ).astype(float)

        self.ib = read(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.positions = np.c_[
            read(attrs["POSITION"]), np.ones(len(read(attrs["POSITION"])))
        ]
        sets = sorted(
            int(key.split("_")[1]) for key in attrs if key.startswith("JOINTS_")
        )
        if not sets or any("WEIGHTS_" + str(i) not in attrs for i in sets):
            raise ValueError("unpaired skin influence attributes")
        self.ids = np.concatenate(
            [read(attrs["JOINTS_" + str(i)]) for i in sets], axis=1
        ).astype(int)
        self.weights = np.concatenate(
            [read(attrs["WEIGHTS_" + str(i)]) for i in sets], axis=1
        )
        self.weights /= self.weights.sum(axis=1)[:, None]
        self.node_ids = np.array(self.joints)[self.ids]
        t, r, s = self.pose(0)
        w = self.world(t, r, s)
        points = self.skin(w)
        jaw = self.roles["jaw_lower"][0]
        jaw_nodes = {jaw}
        for i in self.order:
            if self.parents[i] in jaw_nodes:
                jaw_nodes.add(i)
        lower_weight = (self.weights * np.isin(self.node_ids, list(jaw_nodes))).sum(
            axis=1
        )
        self.lower_jaw_indices = np.where(lower_weight > 0.5)[0]
        head_nodes = {self.roles["head"][0]}
        for i in self.order:
            if self.parents[i] in head_nodes:
                head_nodes.add(i)
        head_weight = (self.weights * np.isin(self.node_ids, list(head_nodes))).sum(
            axis=1
        )
        pelvis = w[self.roles["pelvis"][0], :3, 3]
        head = w[self.roles["head"][0], :3, 3]
        self.forward = np.array([*(head - pelvis)])
        self.forward[1] = 0
        self.forward /= np.linalg.norm(self.forward)
        f = points @ self.forward
        lower = np.where(lower_weight > 0.7)[0]
        lower = lower[f[lower] > np.quantile(f[lower], 0.90)]
        upper = np.where(
            (head_weight > 0.7)
            & (lower_weight < 0.1)
            & (f > np.quantile(f[lower], 0.1))
        )[0]
        # Select facing oral surfaces at the rostral tip, not bone origins.
        lower = lower[points[lower, 1] > np.quantile(points[lower, 1], 0.7)]
        upper = upper[points[upper, 1] < np.quantile(points[upper, 1], 0.3)]
        if len(lower) < 3 or len(upper) < 3:
            raise ValueError("mouth surface masks are empty")
        self.masks = {"lower": lower, "upper": upper}
        self.terms = {
            name: self.compress(indices) for name, indices in self.masks.items()
        }
        self.ground = float(points[:, 1].min())
        self.sole_indices = np.where(
            points[:, 1] < self.ground + 0.04 * profile["body_metrics"]["body_height_m"]
        )[0]
        self.initial_surfaces = {k: self.centroid(w, k) for k in self.masks}

    def pose(self, i):
        t, r, s = B._pose(self.glb, self.tracks, i)
        return np.array(t), np.array(r), np.array(s)

    def world(self, t, r, s):
        w = np.zeros((len(t), 4, 4))
        for i in self.order:
            local = np.eye(4)
            local[:3, :3] = matrix(r[i]) * s[i]
            local[:3, 3] = t[i]
            w[i] = local if self.parents[i] is None else w[self.parents[i]] @ local
        return w

    def skin(self, w, indices=None):
        transforms = w[self.joints] @ self.ib
        indices = slice(None) if indices is None else indices
        return np.einsum(
            "nv,nvij,nj->ni",
            self.weights[indices],
            transforms[self.ids[indices]],
            self.positions[indices],
        )[:, :3]

    def compress(self, indices):
        out = np.zeros((len(self.joints), 4))
        for slot in range(self.ids.shape[1]):
            ids = self.ids[indices, slot]
            local = np.einsum("nij,nj->ni", self.ib[ids], self.positions[indices])
            np.add.at(
                out, ids, local * self.weights[indices, slot, None] / len(indices)
            )
        return out

    def centroid(self, w, name):
        return np.einsum("nij,nj->i", w[self.joints], self.terms[name])[:3]


def build_attack(profile_path: Path, output: Path, receipt_path: Path):
    profile = json.loads(profile_path.read_text())
    a = dict(profile["attack"])
    metrics = profile["body_metrics"]
    for field, normalized, metric in (
        ("prop_radius_m", "prop_radius_width_fraction", "body_width_m"),
        (
            "target_forward_from_pelvis_m",
            "target_forward_length_fraction",
            "body_length_m",
        ),
        ("target_lateral_m", "target_lateral_width_fraction", "body_width_m"),
        ("pelvis_drop_m", "pelvis_drop_height_fraction", "body_height_m"),
        ("pelvis_forward_m", "pelvis_forward_length_fraction", "body_length_m"),
        (
            "foot_transform_tolerance_m",
            "foot_transform_tolerance_width_fraction",
            "body_width_m",
        ),
        (
            "mouth_reach_tolerance_m",
            "mouth_reach_tolerance_length_fraction",
            "body_length_m",
        ),
    ):
        a[field] = float(a[normalized]) * float(metrics[metric])
    raw = (B.REPOSITORY / profile["source"]["path"]).read_bytes()
    for key in ("source", "semantic_rig", "semantic_binding"):
        if (
            B.sha((B.REPOSITORY / profile[key]["path"]).read_bytes())
            != profile[key]["sha256"]
        ):
            raise ValueError(key + " hash mismatch")
    rig = Rig(raw, profile)
    d, bi = rig.d, rig.binary
    anim = B.S.animation_by_name(d, profile["source"]["clip"])
    channels = B.channel_accessors(d, anim)
    t0, r0, s0 = rig.pose(0)
    w0 = rig.world(t0, r0, s0)
    pelvis = rig.roles["pelvis"][0]
    jaw = rig.roles["jaw_lower"][0]
    head = rig.roles["head"][0]
    lateral = np.cross(np.array([0.0, 1.0, 0.0]), rig.forward)
    # Ground is evaluated from the original skinned mesh, not a mouth offset.
    ground = rig.ground
    radius = a["prop_radius_m"]
    target = (
        w0[pelvis, :3, 3]
        + rig.forward * a["target_forward_from_pelvis_m"]
        + lateral * a["target_lateral_m"]
    )
    target[1] = ground + radius
    upper_target = target + np.array([0.0, radius * 0.65, 0.0])
    parent = rig.parents[pelvis]
    groups = ("pelvis", "spine", "chest", "neck", "head")
    articulation, joint_layout, curve, articulation_hash = articulation_layout(
        rig, profile
    )
    joint_count = len(joint_layout)
    pitch = profile["axes_local_xyz"]["pitch"]
    pitch_axes = {
        node: np.linalg.solve(w0[node, :3, :3], lateral)
        for key in (*groups, "tail")
        for node in rig.roles[key]
    }
    pitch_axes = {
        node: axis / np.linalg.norm(axis) for node, axis in pitch_axes.items()
    }

    def upper_pose(x, t, r, amount=1):
        tt = t.copy()
        rr = r.copy()
        pelvis_delta = np.linalg.solve(
            w0[parent, :3, :3],
            rig.forward * x[-1] * metrics["body_length_m"]
            + np.array([0.0, -x[-2] * metrics["body_height_m"], 0.0]),
        )
        tt[pelvis] += pelvis_delta * amount
        for (_, _, node, _), value in zip(joint_layout, x[:joint_count]):
            rr[node] = B.S.qmul(rr[node], axis_q(pitch_axes[node], value * amount))
        if "tail_response" in articulation:
            gains = articulation["tail_response"]["pelvis_pitch_gain"]
            if len(gains) != len(rig.roles["tail"]):
                raise ValueError("tail response semantic count mismatch")
            for node, gain in zip(rig.roles["tail"], gains):
                rr[node] = B.S.qmul(
                    rr[node], axis_q(pitch_axes[node], x[0] * gain * amount)
                )
        return tt, rr

    local_forward = np.linalg.solve(w0[head, :3, :3], rig.forward)
    local_up = np.linalg.solve(w0[head, :3, :3], np.array([0.0, 1.0, 0.0]))

    desired_pitch = np.radians(articulation["preferred_hold_head_nose_down_degrees"])
    desired_forward = rig.forward * np.cos(desired_pitch) - np.array(
        [0, 1, 0]
    ) * np.sin(desired_pitch)
    desired_up = np.array([0, 1, 0]) * np.cos(desired_pitch) + rig.forward * np.sin(
        desired_pitch
    )
    preferred = np.r_[
        np.radians([2] * joint_count),
        a["pelvis_drop_height_fraction"],
        a["pelvis_forward_length_fraction"],
    ]
    preferred[curve] = np.radians(np.linspace(2, 10, len(curve)))
    prior_weights = np.full(len(preferred), 0.006)
    if "preferred_joint_pitch_degrees" in articulation:
        for i, (role, chain_index, _, _) in enumerate(joint_layout):
            preferred[i] = np.radians(
                articulation["preferred_joint_pitch_degrees"][role][chain_index]
            )
            prior_weights[i] = articulation["posture_prior_weights"][role]
        prior_weights[-2:] = articulation["posture_prior_weights"]["translation"]

    def residual(x):
        t, r = upper_pose(x, t0, r0)
        w = rig.world(t, r, s0)
        hf = w[head, :3, :3] @ local_forward
        hu = w[head, :3, :3] @ local_up
        return np.r_[
            (rig.centroid(w, "upper") - upper_target) / metrics["body_height_m"],
            (hf / np.linalg.norm(hf) - desired_forward) * 0.25,
            (hu / np.linalg.norm(hu) - desired_up) * 0.25,
            np.diff(x[curve]) * 0.012,
            (x - preferred) * prior_weights,
        ]

    translation_limits = articulation["reach_translation_limits"]
    bounds = [row[3] for row in joint_layout]
    lo = np.r_[
        np.radians([row[0] for row in bounds]),
        translation_limits["pelvis_drop_height_fraction"][0],
        translation_limits["pelvis_forward_length_fraction"][0],
    ]
    hi = np.r_[
        np.radians([row[1] for row in bounds]),
        translation_limits["pelvis_drop_height_fraction"][1],
        translation_limits["pelvis_forward_length_fraction"][1],
    ]
    # A downward bite does not spend the body's upward extension authority.
    # Tiny reverse bending is tolerated; a large head counterrotation is not.
    reverse = np.radians(articulation["cervical_curve"]["max_reverse_pitch_degrees"])
    lo[curve] = np.maximum(lo[curve], -reverse)
    lo[-3] = max(lo[-3], 0.0)
    curve_limit = np.radians(
        articulation["cervical_curve"]["max_adjacent_pitch_change_degrees"]
    )
    curve_groups = [(curve, curve_limit)]
    if "trunk_curve" in articulation:
        trunk = [
            i
            for i, row in enumerate(joint_layout)
            if row[0] in ("pelvis", "spine", "chest")
        ]
        curve_groups.append(
            (
                trunk,
                np.radians(
                    articulation["trunk_curve"]["max_adjacent_pitch_change_degrees"]
                ),
            )
        )

    def project(value):
        value = np.clip(value, lo, hi)
        # Intersect the adjacent-angle slabs and box. The final gate below
        # rejects nonconvergence, so this cannot silently soften the limits.
        for _ in range(40):
            for curve_nodes, limit in curve_groups:
                for left, right in zip(curve_nodes, curve_nodes[1:]):
                    difference = value[right] - value[left]
                    excess = abs(difference) - limit
                    if excess > 0:
                        shift = np.sign(difference) * excess / 2
                        value[left] += shift
                        value[right] -= shift
            value = np.clip(value, lo, hi)
        return value

    seeds = [preferred, np.r_[np.radians([0] * joint_count), 0.38, 0.15]]
    trials = [least_squares(residual, seed, lo, hi, 180, project) for seed in seeds]
    angles = min(trials, key=lambda x: np.linalg.norm(residual(x)))
    tt, rr = upper_pose(angles, t0, r0)
    ww = rig.world(tt, rr, s0)
    reach = float(np.linalg.norm(rig.centroid(ww, "upper") - upper_target))
    solved_forward = ww[head, :3, :3] @ local_forward
    solved_pitch = np.degrees(
        np.arctan2(-solved_forward[1], solved_forward @ rig.forward)
    )
    pitch_min, pitch_max = articulation["hold_head_nose_down_degrees"]
    if (
        not pitch_min <= solved_pitch <= pitch_max
        or np.max(np.abs(np.diff(angles[curve]))) > curve_limit + 1e-7
    ):
        raise ValueError(
            f"infeasible articulated head/neck posture: pitch={solved_pitch}; angles={np.degrees(angles[:joint_count])}"
        )
    if reach > a["mouth_reach_tolerance_m"]:
        raise ValueError(
            f"infeasible articulated upper-mouth reach {reach}; target={upper_target}; reached={rig.centroid(ww, 'upper')}; angles={np.degrees(angles[:joint_count])}; ground={ground}"
        )
    # Pick opening polarity from measured surface separation.
    jaw_trials = []
    for sign in (-1, 1):
        rr = r0.copy()
        rr[jaw] = B.S.qmul(rr[jaw], axis_q(pitch, np.radians(a["gape_degrees"]) * sign))
        ww = rig.world(t0, rr, s0)
        jaw_trials.append(
            (float(rig.centroid(ww, "upper")[1] - rig.centroid(ww, "lower")[1]), sign)
        )
    jaw_sign = max(jaw_trials)[1]
    n = int(profile["source"]["sample_count"])
    duration = a["duration_seconds"]
    times = np.linspace(0, duration, n)
    rows = {key: [] for key in channels}
    leg_previous = {side: np.zeros(9) for side in rig.legs}
    foot_error = 0.0
    surface = []
    pelvis_rows = []
    sole_drift = 0.0
    minimum_sole_y = float("inf")
    minimum_jaw_y = float("inf")
    constrained_jaw_samples = 0
    # Suppress idle motion only in the active upper-body pose. The stance
    # goals and complete toe hierarchy retain their original source motion.
    support_nodes = set()
    for chain in rig.legs.values():
        support_nodes.update(chain)
    for node in rig.order:
        if rig.parents[node] in support_nodes:
            support_nodes.add(node)
    idle_suppression_nodes = [node for node in rig.order if node not in support_nodes]
    hold_samples = []
    support_samples = []
    for sample, time in enumerate(times):
        ts, rs, ss = rig.pose(sample)
        source_w = rig.world(ts, rs, ss)
        amount, gape = phase(float(time), a)
        ts[pelvis] = (1 - amount) * ts[pelvis] + amount * t0[pelvis]
        for node in idle_suppression_nodes:
            neutral = r0[node] if np.dot(rs[node], r0[node]) >= 0 else -r0[node]
            blended = (1 - amount) * rs[node] + amount * neutral
            rs[node] = blended / np.linalg.norm(blended)
        ts, rs = upper_pose(angles, ts, rs, amount)
        jaw_base = rs[jaw].copy()

        def jaw_floor(fraction):
            rs[jaw] = B.S.qmul(
                jaw_base,
                axis_q(pitch, np.radians(a["gape_degrees"]) * fraction * jaw_sign),
            )
            return float(
                rig.skin(rig.world(ts, rs, ss), rig.lower_jaw_indices)[:, 1].min()
            )

        jaw_floor_limit = (
            ground
            + float(a["jaw_ground_clearance_height_fraction"])
            * metrics["body_height_m"]
        )
        if jaw_floor(gape) < jaw_floor_limit:
            if jaw_floor(0) < jaw_floor_limit:
                raise ValueError(
                    "closed jaw cannot clear ground at requested body pose"
                )
            low, high = 0.0, gape
            for _ in range(12):
                middle = (low + high) / 2
                if jaw_floor(middle) >= jaw_floor_limit:
                    low = middle
                else:
                    high = middle
            gape = low
            constrained_jaw_samples += 1
            jaw_floor(gape)
        # Each 3-link leg uses local rotations only. The distal foot world
        # orientation is then reconstructed exactly, preserving every toe.
        for side, chain in rig.legs.items():
            if "support_articulation" in profile:
                import support_solver

                rs, support = support_solver.solve(
                    rig,
                    ts,
                    rs,
                    ss,
                    source_w,
                    w0,
                    side,
                    amount,
                    profile["support_articulation"],
                )
                foot_error = max(foot_error, support["foot_transform_error"])
                support_samples.append(
                    {"time_seconds": float(time), "side": side, **support}
                )
                continue
            base = rs.copy()
            foot = chain[-1]
            goal = source_w[foot]
            chain_parent_world = rig.world(ts, base, ss)[rig.parents[chain[0]]]

            def leg_pose(x):
                trial = base.copy()
                for j, node in enumerate(chain[:-1]):
                    rv = x[j * 3 : j * 3 + 3]
                    length = np.linalg.norm(rv)
                    if length > 1e-12:
                        trial[node] = B.S.qmul(base[node], axis_q(rv / length, length))
                return trial

            def leg_residual(x):
                trial = leg_pose(x)
                foot_world = chain_parent_world.copy()
                for node in chain:
                    local = np.eye(4)
                    local[:3, :3] = matrix(trial[node]) * ss[node]
                    local[:3, 3] = ts[node]
                    foot_world = foot_world @ local
                return np.r_[(foot_world[:3, 3] - goal[:3, 3]) * 3, x * 0.00005]

            solution = least_squares(
                leg_residual, leg_previous[side], np.full(9, -1.6), np.full(9, 1.6), 18
            )
            leg_previous[side] = solution
            rs = leg_pose(solution)
            w = rig.world(ts, rs, ss)
            local = np.linalg.solve(w[rig.parents[foot]], goal)
            rs[foot] = _rotation_from_matrix(
                tuple(tuple(float(v) for v in row) for row in local)
            )
            w = rig.world(ts, rs, ss)
            foot_error = max(foot_error, float(np.max(np.abs(w[foot] - goal))))
        w = rig.world(ts, rs, ss)
        if a["timing"]["close_end"] <= time <= a["timing"]["hold_end"]:
            upper = rig.centroid(w, "upper")
            lower = rig.centroid(w, "lower")
            row = {
                "time_seconds": float(time),
                "upper_target_error_m": float(np.linalg.norm(upper - upper_target)),
            }
            for name, centroid in (("upper", upper), ("lower", lower)):
                points = rig.skin(w, rig.masks[name])
                row[name + "_oral_centroid_signed_distance_m"] = float(
                    np.linalg.norm(centroid - target) - radius
                )
                row[name + "_oral_nearest_signed_distance_m"] = float(
                    np.linalg.norm(points - target, axis=1).min() - radius
                )
            if row["upper_target_error_m"] > a["mouth_reach_tolerance_m"] or any(
                value > 1e-6 for key, value in row.items() if "signed_distance" in key
            ):
                raise ValueError(f"emitted hold oral engagement failed: {row}")
            hold_samples.append(row)
        if sample % 6 == 0 or sample == n - 1:
            upper = rig.centroid(w, "upper")
            lower = rig.centroid(w, "lower")
            sole = rig.skin(w, rig.sole_indices)
            source_sole = rig.skin(source_w, rig.sole_indices)
            sole_drift = max(
                sole_drift, float(np.linalg.norm(sole - source_sole, axis=1).max())
            )
            minimum_sole_y = min(minimum_sole_y, float(sole[:, 1].min()))
            jaw_min = float(rig.skin(w, rig.lower_jaw_indices)[:, 1].min())
            minimum_jaw_y = min(minimum_jaw_y, jaw_min)
            surface.append(
                {
                    "time": float(time),
                    "upper": upper.tolist(),
                    "lower": lower.tolist(),
                    "aperture_m": float(np.linalg.norm(upper - lower)),
                    "aperture_vertical_m": float(upper[1] - lower[1]),
                    "upper_target_distance_m": float(
                        np.linalg.norm(upper - upper_target)
                    ),
                    "head_forward_dot": float(
                        (w[head, :3, :3] @ local_forward) @ rig.forward
                    ),
                    "head_up_dot": float((w[head, :3, :3] @ local_up)[1]),
                    "lower_jaw_minimum_y_m": jaw_min,
                }
            )
        for key in rows:
            node, path = key
            rows[key].append(
                tuple({"translation": ts, "rotation": rs, "scale": ss}[path][node])
            )
        pelvis_rows.append(w[pelvis, :3, 3].tolist())
    if foot_error > a["foot_transform_tolerance_m"]:
        raise ValueError(f"foot transform drift {foot_error}")
    for key, values in rows.items():
        ia, oa = channels[key]
        original = B.S.read_accessor(d, bi, oa)
        values[0] = original[0]
        values[-1] = original[-1]
        B.S.write_accessor(d, bi, oa, values)
    for ia in {v[0] for v in channels.values()}:
        B.S.write_accessor(d, bi, ia, [(float(t),) for t in times])
        d["accessors"][ia]["min"] = [0.0]
        d["accessors"][ia]["max"] = [duration]
    anim["name"] = "grounded_committed_bite"
    encoded = B.S.encode_glb(d, bi)
    emitted_articulation = measure_articulation(rig, profile, B.Glb.from_bytes(encoded))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    receipt = {
        "status": "EXPERIMENTAL_ATTACK_PREVIEW_NOT_USER_ACCEPTED",
        "candidate": str(output),
        "candidate_sha256": B.sha(encoded),
        "duration_seconds": duration,
        "target": {
            "world_position_m": target.tolist(),
            "preview_prop_radius_m": radius,
            "ground_y_m": ground,
            "ground_derivation": "minimum frame-zero fully skinned source surface Y",
        },
        "body_angles_degrees": {
            role: float(
                sum(
                    np.degrees(angles[i])
                    for i, row in enumerate(joint_layout)
                    if row[0] == role
                )
            )
            for role in groups
        },
        "body_articulation": {
            "profile_path": profile["body_articulation"]["path"],
            "profile_sha256": articulation_hash,
            "pitch_convention": articulation["pitch_convention"],
            "joint_angles": [
                {
                    "semantic": role,
                    "chain_index": index,
                    "node": node,
                    "pitch_degrees": float(np.degrees(angles[i])),
                    "limits_degrees": bounds,
                }
                for i, (role, index, node, bounds) in enumerate(joint_layout)
            ],
            "maximum_adjacent_cervical_pitch_change_degrees": float(
                np.degrees(np.max(np.abs(np.diff(angles[curve]))))
            ),
            "hold_head_nose_down_degrees": float(solved_pitch),
            "pelvis_drop_height_fraction": float(angles[-2]),
            "pelvis_forward_length_fraction": float(angles[-1]),
            "claims": articulation["claims"],
            "emitted_verification": {
                key: value
                for key, value in emitted_articulation.items()
                if key != "samples"
            },
        },
        "mouth_geometry": {
            "mask_rule": "rostral jaw-influenced upper-facing and head-influenced lower-facing surface percentiles; every available normalized skin influence",
            "influences_per_vertex": rig.ids.shape[1],
            "vertex_counts": {k: len(v) for k, v in rig.masks.items()},
            "initial": {k: v.tolist() for k, v in rig.initial_surfaces.items()},
            "peak_gape_degrees": a["gape_degrees"],
            "jaw_open_sign": jaw_sign,
            "solve_upper_target_distance_m": reach,
            "minimum_lower_jaw_y_m": minimum_jaw_y,
            "ground_constrained_closing_samples": constrained_jaw_samples,
            "samples": surface,
        },
        "contact": {
            "max_foot_world_matrix_delta": foot_error,
            "bone_translations_unchanged_except_pelvis": True,
            "bone_scales_unchanged": True,
            "leg_rotations_changed_for_crouch": True,
            "skinned_sole_max_vertex_delta_from_source_m": sole_drift,
            "skinned_sole_minimum_y_m": minimum_sole_y,
            "skinned_sole_measurement": "all influences for frame-zero ground-band vertices at every sixth sample; not whole-surface collision proof",
        },
        "support_articulation": {
            "method": profile.get("support_articulation", {}).get(
                "method", "historical_free_9dof_foot_position_dls"
            ),
            "samples": support_samples,
        },
        "hold_contact": {
            "source_idle_suppression": "smooth active-pose blend; source stance and toes retained",
            "sample_count": len(hold_samples),
            "maximum_upper_target_error_m": max(
                row["upper_target_error_m"] for row in hold_samples
            ),
            "declared_upper_target_tolerance_m": a["mouth_reach_tolerance_m"],
            "maximum_upper_oral_centroid_signed_distance_m": max(
                row["upper_oral_centroid_signed_distance_m"] for row in hold_samples
            ),
            "maximum_lower_oral_centroid_signed_distance_m": max(
                row["lower_oral_centroid_signed_distance_m"] for row in hold_samples
            ),
            "maximum_upper_oral_nearest_signed_distance_m": max(
                row["upper_oral_nearest_signed_distance_m"] for row in hold_samples
            ),
            "maximum_lower_oral_nearest_signed_distance_m": max(
                row["lower_oral_nearest_signed_distance_m"] for row in hold_samples
            ),
            "samples": hold_samples,
            "status": "PASS_ORAL_ENGAGEMENT_NOT_COLLISION_PHYSICS",
        },
        "timing": a["timing"],
        "visual_acceptance": "NOT_CLAIMED",
        "claims": profile["claims"],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
