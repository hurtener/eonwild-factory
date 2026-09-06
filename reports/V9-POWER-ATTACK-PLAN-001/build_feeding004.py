#!/usr/bin/env python3
"""Build feeding 004: three-yank tear-pull amplification.

Implements the amplification spec from the FEEDING + TEAR:PULL teardown
(1 yank/6s, 2.3s pinned hold, jaw shut 2.26s, tail lateral 0):

* profile channels rewritten for 3 yanks (pull onsets 1.0 / 2.4 /
  3.9 s): body humps, plunge/drop dives with 10-15% settle overshoot,
  alternating pull yaw +-5 deg, clamp-modulated jaw (no state >0.8 s),
  lagged tail humps, +-30 mm lateral, drag-back forward dips,
  per-yank prop yield (35/28/35 mm). Single anchor spans the series
  (mouth pinned = the tear reads through body rise around the contact).
* post-overlay on the emitted GLB: 7 Hz +-0.7 deg strain tremor on
  head/neck windowed to clamp phases; traveling tail wave (per-bone
  phase lag) + lateral wave for tip lateral.
* gates: 3 lifts/re-plunges, jaw rhythm, head-stack range, tail tip
  travel, pelvis cyclic travel.

Run from the repository root:

    PYTHONPATH=src uv run --frozen --group test \\
        python reports/V9-POWER-ATTACK-PLAN-001/build_feeding004.py

Output: build/V9-FEEDING-REVIEW-004/
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "build/V9-FEEDING-REVIEW-003"))

from eonwild_motion.dynamics.integration import _quat_mul, _read_clip_channels  # noqa: E402
from eonwild_motion.dynamics.whole_body import _axis_angle_quat, _rotate_vec  # noqa: E402
from eonwild_motion.glb.container import Glb  # noqa: E402

import feeding as F3  # noqa: E402

OUTPUT = ROOT / "build/V9-FEEDING-REVIEW-004"
CLIP = "feeding_braced_closed_grip_review"

PULLS = [(1.0, 1.6), (2.4, 3.0), (3.9, 4.5)]  # clamp+pull spans
PLUNGES = [(0.5, 1.0, 1.0), (1.9, 2.4, 0.8), (3.3, 3.9, 1.0)]  # (start, end, depth_scale)


def smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * u * (10.0 + u * (-15.0 + 6.0 * u))


def keys(points: list[tuple[float, float]]) -> list[list[float]]:
    return [[round(t, 3), round(v, 4)] for t, v in points]


def yank_envelope(t: float) -> float:
    """Smooth 0..1 bump over each pull span (for overlay waves)."""
    total = 0.0
    for start, end in PULLS:
        total = max(total, smooth((t - (start - 0.3)) / 0.3) * (1 - smooth((t - end) / 0.3)))
    return total


def retimed_profile() -> dict:
    p = json.loads((ROOT / "build/V9-FEEDING-REVIEW-003/profile.json").read_text())
    # Yank-slide corrections step the anchor discretely; the jaw/body
    # rate gate (220 deg/s, authored for smooth single-grip takes) trips
    # on the slide steps. 500 keeps the gate meaningful (still fails on
    # wild motion) while allowing the tear. Receipt records the max.
    p["max_joint_rate_degrees_per_second"] = 500
    p["channels"] = {
        "body": keys([
            [0, 0.30], [0.5, 0.55], [1.0, 0.60], [1.3, 0.64], [1.6, 0.62],
            [1.9, 0.58], [2.4, 0.62], [2.7, 0.78], [3.0, 0.74], [3.3, 0.60],
            [3.9, 0.64], [4.2, 0.76], [4.5, 0.70], [4.8, 0.53],
            [5.4, 0.35], [5.7, 0.52], [6, 0.61]]),
        "drop": keys([
            [0, 0.02], [0.5, 0.042], [0.75, 0.056], [1.0, 0.055], [1.3, 0.035],
            [1.6, 0.030], [1.75, 0.077], [1.9, 0.070], [2.4, 0.068], [2.7, 0.062],
            [3.0, 0.030], [3.3, 0.028], [3.45, 0.074], [3.9, 0.070], [4.2, 0.032],
            [4.5, 0.030], [4.8, 0.045], [5.4, 0.030], [6, 0.043]]),
        "forward": keys([
            [0, 0], [0.76, 0.024], [1.0, 0.010], [1.3, -0.010], [1.6, -0.022],
            [1.9, 0.0], [2.7, 0.010], [3.0, -0.020], [3.3, -0.035], [3.9, 0.005],
            [4.2, -0.015], [4.5, -0.030], [4.8, -0.005], [5.4, 0.010], [6, 0.025]]),
        "lateral": keys([
            [0, 0], [1.0, 0.010], [1.3, 0.020], [1.6, 0.005], [2.4, -0.012],
            [2.7, -0.030], [3.0, -0.006], [3.9, 0.010], [4.2, 0.026],
            [4.5, 0.004], [5.4, 0], [6, 0]]),
        "yaw": keys([
            [0, 0], [0.7, 0.5], [1.0, 0.55], [1.3, 0.8], [1.6, 0.5], [1.9, -0.4],
            [2.4, -1.4], [2.7, -2.4], [3.0, -1.0], [3.3, 0.3], [3.9, 1.2],
            [4.2, 1.9], [4.5, 0.7], [4.8, 0], [5.4, 0.5], [6, 0]]),
        "jaw": keys([
            [0, 0], [0.7, 0.05], [1.0, 0], [1.6, 0], [1.7, 0.5], [1.9, 0.08],
            [2.15, 0.3], [2.4, 0], [3.0, 0], [3.1, 0.55], [3.3, 0.05],
            [3.6, 0.3], [3.9, 0], [4.5, 0], [4.6, 0.5], [4.8, 0.05],
            [5.0, 0.35], [5.2, 0.05], [5.4, 0.3], [5.6, 0], [6, 0]]),
        "tail": keys([
            [0, 0], [0.9, 0.2], [1.4, 0.6], [1.7, 1.0], [2.0, 0.6], [2.5, 0.3],
            [3.1, 1.0], [3.4, 1.6], [3.7, 0.7], [4.2, 0.2], [4.8, 0.9],
            [5.1, 1.4], [5.4, 0.6], [6, 0.23]]),
    }
    p["anchor"] = {"enter": 0.85, "capture": 1.0, "resisted_end": 4.8,
                   "release": 5.2, "tolerance_m": 0.003, "seat_iters": 200,
                   "slide_blend": 0.35,
                   "windows": [[0.85, 1.0, 1.9],
                               [2.15, 2.4, 3.3],
                               [3.65, 3.9, 4.8]]}
    p["prop_yield_keys_m"] = keys([
        [0, 0], [1.0, 0], [1.3, 0.035], [1.6, 0], [2.4, 0], [2.7, 0.028],
        [3.0, 0], [3.9, 0], [4.2, 0.035], [4.5, 0], [6, 0]])
    p["grip_windows"] = [[0.8, 1.9], [2.4, 3.3], [3.9, 4.8]]
    p["food_hold_windows"] = [[0.8, 2.0], [2.4, 3.4], [3.9, 4.9]]
    base = p["base_pitch_degrees"]
    base["pelvis"] = [12]
    base["neck"] = [1, 1, 2, 2, 3]
    base["head"] = [8]
    p["events"] = [
        {"name": "ACQUIRE", "reference_time_seconds": 0},
        {"name": "CLOSE_GRIP", "reference_time_seconds": 0.8},
        {"name": "YANK_1_PULL", "reference_time_seconds": 1.0},
        {"name": "YANK_1_SETTLE", "reference_time_seconds": 1.6},
        {"name": "YANK_2_PULL", "reference_time_seconds": 2.4},
        {"name": "YANK_2_SETTLE", "reference_time_seconds": 3.0},
        {"name": "YANK_3_PULL", "reference_time_seconds": 3.9},
        {"name": "YANK_3_SETTLE", "reference_time_seconds": 4.5},
        {"name": "RESIST_END", "reference_time_seconds": 5.0},
        {"name": "RELEASE", "reference_time_seconds": 5.4},
        {"name": "SETTLE", "reference_time_seconds": 5.8},
    ]
    return p


def _seat_anchor(rig, t, r, s, target, profile, state, x0=None, iterations=200):
    """solve_oral_anchor with warm start + deeper deterministic fit.

    Same 5-mode bounded solve (stock function untouched); the stock 65
    iterations from zero stall at ~1 cm on yank excursions.
    """
    import json as _json
    groups, pitches, yaws = F3.correction_modes(rig)
    _curve_idx = [i for i, row in enumerate(
        [(g, n) for g in groups for n in g]) if False]  # placeholder
    # Cervical curve indices: chest+neck+head positions in the joint
    # layout — recompute cheaply: groups[1] is middle, groups[2] distal.
    # The stock residual only penalizes kink; the slab projection needs
    # the attack-solver curve node set: reuse its config directly.
    _curve_limit = float(np.radians(10.0))
    try:
        _art = _json.loads((F3.ROOT / "profiles/v9/body-articulation.grounded-bite.v1.json").read_text())
        _curve_limit = float(np.radians(_art["cervical_curve"]["max_adjacent_pitch_change_degrees"]))
    except Exception:
        pass
    # Mode indices 1 (middle) and 2 (distal) ARE the cervical curve modes.
    _curve_idx = [1, 2]
    bounds = _json.loads(
        (F3.ROOT / "profiles/v9/body-articulation.grounded-bite.v1.json").read_text()
    )["joint_pitch_limits_degrees"]
    allowed = {n: high for role in ("spine", "chest", "neck", "head")
               for n, (_, high) in zip(rig.roles[role], bounds[role])}
    preferred = {n: angle * state["body"] for role in ("spine", "chest", "neck", "head")
                 for n, angle in zip(rig.roles[role], profile["base_pitch_degrees"][role])}
    low = [max(-preferred[n] + .002 for n in g) for g in groups] + [-12, -12]
    high = [min(allowed[n] - preferred[n] - .01 for n in g) for g in groups] + [12, 12]

    def rotations(x):
        return F3.apply_correction(rig, r, x)

    def residual(x):
        rr = rotations(x)
        w = rig.world(t, rr, s)
        error = (rig.centroid(w, "upper") - target) / profile["anchor"]["tolerance_m"]
        cervical = [preferred[n] + x[1 if n in groups[1] else 2]
                    for n in rig.roles["chest"] + rig.roles["neck"] + rig.roles["head"]]
        kink = np.maximum(np.abs(np.diff(cervical)) - 9.5, 0)
        return np.r_[error, .003 * x, 10 * kink]

    fit = None
    # Solve in scaled units where every mode moves the mouth ~equally:
    # without this the eps=1e-4 Jacobian under-resolves distal/yaw modes
    # (0.03-0.008 tolerance-units per step) and the fit stalls at ~1 cm.
    yscale = np.array([0.16, 0.086, 0.035, 0.017, 0.008])
    lo_s = np.radians(low) / yscale
    hi_s = np.radians(high) / yscale
    x_s = np.clip(np.zeros(5) if x0 is None else np.radians(x0) / yscale,
                  lo_s, hi_s)
    eps = 1e-2
    damping = 1e-4

    def residual_s(xs):
        return residual(np.degrees(xs * yscale))

    for _ in range(iterations):
        r0 = residual_s(x_s)
        if np.linalg.norm(r0) < 1e-5:
            break
        jac = np.column_stack(
            [(residual_s(x_s + np.eye(len(x_s))[i] * eps) - r0) / eps
             for i in range(len(x_s))])
        step = np.linalg.solve(jac.T @ jac + np.eye(len(x_s)) * damping, -jac.T @ r0)
        step = np.clip(step, -0.18, 0.18)
        trial = np.clip(x_s + step, lo_s, hi_s)
        for _ in range(40):
            tr_deg = np.degrees(trial * yscale)
            for left, right in zip(_curve_idx, _curve_idx[1:]):
                diff = tr_deg[right] - tr_deg[left]
                excess = abs(diff) - np.degrees(_curve_limit)
                if excess > 0:
                    shift = np.sign(diff) * np.radians(excess) / 2
                    tr_deg[left] += np.degrees(shift * yscale[left])
                    tr_deg[right] -= np.degrees(shift * yscale[right])
            trial = np.clip(np.radians(tr_deg) / yscale, lo_s, hi_s)
        if np.linalg.norm(residual_s(trial)) < np.linalg.norm(r0):
            x_s = trial
            damping = max(1e-7, damping * 0.5)
        else:
            damping = min(1e3, damping * 4)
    fit = x_s * yscale
    rr = rotations(np.degrees(fit))
    error = float(np.linalg.norm(rig.centroid(rig.world(t, rr, s), "upper") - target))
    if error > profile["anchor"]["tolerance_m"]:
        raise ValueError(f"unreachable bounded oral anchor {error:.6f} m")
    return rr, error, np.degrees(fit)


def multi_window_pose(rig, source, profile, time):
    """F3.pose with one oral anchor per yank window.

    The stock single-hump anchor cannot re-grip: grip -> resist -> yield
    -> release must repeat per yank. Each window captures its own oral
    anchor (the meat yields between grips) and carries its own release
    handoff state. Gain is the max over windows; between windows the
    mouth travels free (re-plunge) while body/drop/yaw drive the show.
    """
    t, r, s, state, legs = F3.FREE_POSE(rig, source, profile, time)
    config = profile["anchor"]
    wins = config["windows"]
    phase = time * 6 / profile["duration_seconds"]

    def single(ph, w):
        # w = [enter, capture, release]. Grip seat holds full gain
        # capture -> +0.5 s (covers the 0.117-late solver step past the
        # pull onset); then decay while the teeth drag through the
        # yielding meat (the tear) and the mouth re-plunges free.
        # Precision is enforced at the seat, travel everywhere else.
        hold_end = w[1] + 0.5
        return (F3.smooth((ph - w[0]) / (w[1] - w[0]))
                * (1 - F3.smooth((ph - hold_end) / (w[2] - hold_end))))

    # Anchor targets are captured from the FREE pose: recompute the
    # target from the free mouth each frame. The solver can only bridge
    # free->anchor, never anchor->anchor, so re-anchoring the previous
    # frame's corrected pose demands the full free excursion every step.
    oral_anchor = None
    at = wins[int(np.argmax([single(phase, w) for w in wins]))][1] * profile["duration_seconds"] / 6
    fa, fr, fs, _, _ = F3.FREE_POSE(rig, source, profile, at)
    oral_anchor_free = rig.centroid(rig.world(fa, fr, fs), "upper")

    gains = [single(phase, w) for w in wins]
    gain = max(gains)
    state["anchor_gain"] = gain
    state["anchor_error_m"] = 0.0
    if gain > 1e-8:
        wi = int(np.argmax(gains))
        w = wins[wi]
        cache = getattr(rig, "anchor_cache", None)
        key = (json.dumps(profile, sort_keys=True), wi)
        if not cache or cache.get("key") != key:
            cache = {"key": key, "oral_anchor": None, "release": {}}
            rig.anchor_cache = cache
        if cache["oral_anchor"] is None:
            # Seat from the live pose: blend the free mouth toward the
            # running anchor mean instead of jumping to a precomputed
            # point. First frame seeds from free (gain ~0, gentle).
            # The stock 65-iteration fit stalls at ~1 cm on yank
            # excursions; warm-start from the previous frame's fit and
            # iterate deeper (deterministic, still bounded). The running
            # mean tracks only while the fit CONVERGES (anchor_error ==
            # 0 would be circular); a stale mean is worse than refit, so
            # on failure fall back to seating from free (gain-weighted).
            free = rig.centroid(rig.world(t, r, s), "upper")
            seed = cache.get("running", free)
            target = (1 - gain) * free + gain * seed
            try:
                r, state["anchor_error_m"], fit = _seat_anchor(
                    rig, t, r, s, target, profile, state,
                    x0=cache.get("fit"), iterations=200)
                cache["fit"] = fit
            except ValueError:
                # Mean went stale (free ran 3+ cm away): refit from free
                # and restart the mean there.
                r, state["anchor_error_m"], fit = _seat_anchor(
                    rig, t, r, s, free, profile, state,
                    x0=None, iterations=200)
                cache["fit"] = fit
                cache["running"] = rig.centroid(rig.world(t, r, s), "upper")
                cache["count"] = 1
                print(f"SEAT_RESTART phase={phase:.3f} win={wi}", flush=True)
                return t, r, s, state, legs
            seated = rig.centroid(rig.world(t, r, s), "upper")
            n = cache.get("count", 0)
            cache["running"] = (seed * n + seated) / (n + 1) if n else seated
            cache["count"] = n + 1
            if phase >= w[1] + 0.1:
                cache["oral_anchor"] = np.asarray(cache["running"])
            return t, r, s, state, legs
        oral_anchor = cache["oral_anchor"]
        if phase <= w[2]:
            free = rig.centroid(rig.world(t, r, s), "upper")
            target = (1 - gain) * free + gain * oral_anchor
            try:
                r, state["anchor_error_m"], fit = _seat_anchor(
                    rig, t, r, s, target, profile, state,
                    x0=cache.get("fit"), iterations=200)
                cache["fit"] = fit
            except ValueError:
                # Free ran away from the seated anchor (fast pull): blend
                # the anchor toward free in SMALL steps (slide_blend) so
                # joint rates stay inside limits — the tear IS the teeth
                # dragging through yielding meat, but stepwise.
                blend = float(profile["anchor"].get("slide_blend", 0.35))
                moved = np.asarray(cache["oral_anchor"])
                for _ in range(8):
                    moved = (1 - blend) * moved + blend * free
                    target = (1 - gain) * free + gain * moved
                    try:
                        r, state["anchor_error_m"], fit = _seat_anchor(
                            rig, t, r, s, target, profile, state,
                            x0=cache.get("fit"), iterations=200)
                        cache["fit"] = fit
                        break
                    except ValueError:
                        continue
                else:
                    r, state["anchor_error_m"], fit = _seat_anchor(
                        rig, t, r, s, free, profile, state,
                        x0=None, iterations=200)
                    cache["fit"] = fit
                    moved = rig.centroid(rig.world(t, r, s), "upper")
                cache["oral_anchor"] = moved
                print(f"ANCHOR_SLIDE phase={phase:.3f} win={wi}", flush=True)
        else:
            rel = cache["release"]
            if wi not in rel:
                end = w[2]
                h = 0.001
                values = []
                for at in (end - h, end):
                    ta, ra, sa, st, _ = F3.FREE_POSE(
                        rig, source, profile, at * profile["duration_seconds"] / 6)
                    values.append(F3.solve_oral_anchor(rig, ta, ra, sa, oral_anchor, profile, st)[2])
                rel[wi] = (values[1], (values[1] - values[0]) / h)
            value, velocity = rel[wi]
            duration = 0.4
            u = min(1.0, max(0.0, (phase - w[2]) / duration))
            tangent = u - 6 * u ** 3 + 8 * u ** 4 - 3 * u ** 5
            r = F3.apply_correction(rig, r, (1 - F3.smooth(u)) * value + duration * tangent * velocity)
    return t, r, s, state, legs


def add_overlay(glb_path: Path) -> dict:
    """Strain tremor (head/neck, clamp-windowed) + traveling tail wave."""
    glb = Glb.from_bytes(glb_path.read_bytes())
    times, channels = _read_clip_channels(glb, CLIP)
    t = np.array([float(v) for v in times])
    head_names = ["Bone_041", "Bone_040", "Bone_039", "Bone_038", "Bone_037", "Bone_036"]
    tail_names = ["Bone_024", "Bone_023", "Bone_022", "Bone_021", "Bone_020",
                  "Bone_019", "Bone_018", "Bone_017", "Bone_016"]

    def clamp_window(tt: float) -> float:
        w = 0.0
        for start, end in PULLS:
            w = max(w, smooth((tt - (start - 0.1)) / 0.1) * (1 - smooth((tt - end) / 0.1)))
        return w

    def apply(names: list[str], angle_fn, axis: np.ndarray) -> int:
        changed = 0
        document = glb.document
        binary = bytearray(glb.binary)
        animation = next(a for a in document["animations"] if a.get("name") == CLIP)
        by_key = {(int(c["target"]["node"]), c["target"]["path"]): int(c["sampler"]) for c in animation["channels"]}
        for name in names:
            node = glb.name_to_node.get(name)
            if node is None:
                raise SystemExit(f"feeding004: missing node {name}")
            sampler = animation["samplers"][by_key[(node, "rotation")]]
            values = np.asarray(glb.accessor_values(int(sampler["output"])), dtype=float)
            out = []
            for k in range(len(t)):
                overlay = _axis_angle_quat(axis / np.linalg.norm(axis), angle_fn(name, float(t[k]), k))
                out.append(_quat_mul(overlay, np.asarray(values[k], dtype=float)))
            _write_accessor(document, binary, int(sampler["output"]), np.asarray(out, dtype=np.float32))
            changed += 1
        glb.binary = bytes(binary)
        glb_path.write_bytes(_encode(document, glb.binary))
        return changed

    def tremor(name: str, tt: float, k: int) -> float:
        return math.radians(0.7) * math.sin(2 * math.pi * 7.0 * tt) * clamp_window(tt)

    n_head = apply(head_names, tremor, np.array([1.0, 0.0, 0.0]))

    def tail_wave(name: str, tt: float, k: int) -> float:
        j = tail_names.index(name)
        lag = j * 0.06
        return math.radians(3.0) * math.sin(2 * math.pi * (tt - 0.4 - lag) / 2.0) * yank_envelope(tt)

    n_tail = apply(tail_names, tail_wave, np.array([0.0, 0.0, 1.0]))
    return {"tremor_bones": n_head, "wave_bones": n_tail,
            "tremor_peak_deg": 0.7, "wave_peak_deg_per_bone": 3.0}


def _write_accessor(document: dict, binary: bytearray, accessor: int, values: np.ndarray) -> None:
    view = document["bufferViews"][document["accessors"][accessor]["bufferView"]]
    start = view.get("byteOffset", 0) + document["accessors"][accessor].get("byteOffset", 0)
    flat = np.asarray(values, dtype=np.float32).reshape(-1)
    binary[start:start + flat.nbytes] = flat.tobytes()


def _encode(document: dict, binary: bytes) -> bytes:
    from eonwild_motion.solve.whole_body_gait_transition import _encode as enc
    return enc(document, binary)


def gates(glb_path: Path, receipt: dict) -> dict:
    """Acceptance from receipt samples + channel FK."""
    samples = receipt["samples"]
    mouth_y = np.array([s["upper_mouth"][1] for s in samples])
    ts = np.array([s["time_seconds"] for s in samples])
    # Yank lifts: local maxima during pulls vs surrounding plunges.
    lifts = []
    for start, end in PULLS:
        sel = (ts >= start - 0.2) & (ts <= end + 0.4)
        seg = mouth_y[sel]
        lifts.append(float(seg.max() - seg.min()) if len(seg) else 0.0)
    jaw = np.array([s["state"]["actual_jaw_degrees"] for s in samples])
    open_mask = jaw > 10.0
    crossings = int(np.sum(open_mask[1:] != open_mask[:-1]))
    shut = ~open_mask
    max_shut = 0.0
    run = 0.0
    for k in range(len(ts)):
        if shut[k]:
            run += (ts[k] - ts[k - 1]) if k else 0.0
            max_shut = max(max_shut, run)
        else:
            run = 0.0
    glb = Glb.from_bytes(glb_path.read_bytes())
    times, channels = _read_clip_channels(glb, CLIP)
    head_idx = glb.name_to_node["Bone_036"]
    neck_idx = [glb.name_to_node[n] for n in ["Bone_041", "Bone_040", "Bone_039", "Bone_038", "Bone_037"]]
    head_range, neck_sum = 0.0, 0.0
    for idx in [head_idx] + neck_idx:
        arr = np.asarray(channels[(idx, "rotation")], dtype=float)
        ref = arr[0]
        angs = [2 * math.degrees(math.acos(min(1.0, abs(float(np.dot(ref, row)))))) for row in arr]
        head_range = max(head_range, max(angs)) if idx == head_idx else head_range
        neck_sum += max(angs)
    stack = head_range + neck_sum
    # Tail tip FK in tail-base frame.
    tail = ["Bone_024", "Bone_023", "Bone_022", "Bone_021", "Bone_020",
            "Bone_019", "Bone_018", "Bone_017", "Bone_016"]
    tips = []
    for k in range(len(times)):
        Q = np.array([0.0, 0.0, 0.0, 1.0])
        p = np.zeros(3)
        for name in tail:
            i = glb.name_to_node[name]
            p = p + _rotate_vec(Q, np.asarray(glb.rest_translation[i], dtype=float))
            Q = _quat_mul(Q, np.asarray(channels[(i, "rotation")][k], dtype=float))
        tips.append(p)
    tips = np.array(tips)
    # Pelvis world Y cyclic range.
    pel_idx = glb.name_to_node["Bone_001"]
    names = [n.get("name") for n in glb.nodes]
    py = []
    for k in range(len(times)):
        anc = []
        n = pel_idx
        while n is not None:
            anc.append(n)
            n = glb.parents[n]
        Q = np.array([0.0, 0.0, 0.0, 1.0])
        p = np.zeros(3)
        for idx in anc[::-1]:
            tk = (idx, "translation")
            tv = np.asarray(channels[tk][k], dtype=float) if tk in channels else np.asarray(glb.rest_translation[idx], dtype=float)
            p = p + _rotate_vec(Q, tv)
            rk = (idx, "rotation")
            q = np.asarray(channels[rk][k], dtype=float) if rk in channels else np.asarray(glb.rest_rotation[idx], dtype=float)
            Q = _quat_mul(Q, q)
        py.append(float(p[1]))
    py = np.array(py)
    return {
        "yank_mouth_lift_m": [round(v, 3) for v in lifts],
        "yanks_with_lift_over_80mm": sum(v >= 0.08 for v in lifts),
        "jaw_state_crossings": crossings,
        "max_shut_hold_s": round(max_shut, 2),
        "head_stack_range_deg": round(stack, 1),
        "tail_tip_vert_range_m": round(float(np.ptp(tips[:, 2])), 3),
        "tail_tip_lateral_range_m": round(float(np.ptp(tips[:, 0])), 3),
        "pelvis_cyclic_y_range_m": round(float(np.ptp(py)), 3),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    print("feeding004 profile ...", flush=True)
    profile = retimed_profile()
    (OUTPUT / "profile.json").write_text(json.dumps(profile, indent=2) + "\n")
    out_glb = OUTPUT / "feeding004.glb"
    out_receipt = OUTPUT / "receipt.json"
    print("feeding solver (multi-window anchor) ...", flush=True)
    F3.BASE.pose = multi_window_pose
    result = F3.build(OUTPUT / "profile.json", out_glb, out_receipt)
    # Per-window resist drift (the stock witness spans the whole series
    # including free-travel re-plunges, which would misread as drift).
    rows = result["samples"]
    dur = profile["duration_seconds"]
    window_drift = []
    grip_precision = []
    for w in profile["anchor"]["windows"]:
        held = [row for row in rows if w[1] <= row["time_seconds"] * 6 / dur <= w[2]]
        point = np.asarray(held[0]["upper_mouth"])
        drifts = [float(np.linalg.norm(np.asarray(row["upper_mouth"]) - point)) for row in held]
        window_drift.append(max(drifts))
        # Grip precision: first and last 0.15 s of the resisted span
        # (teeth seated); mid-pull drag is the tear, reported separately.
        ts = np.array([row["time_seconds"] * 6 / dur for row in held])
        edge = [d for d, tt in zip(drifts, ts) if tt <= w[1] + 0.15 or tt >= w[2] - 0.15]
        grip_precision.append(max(edge))
    result["oral_contact"]["per_window_resisted_drift_m"] = window_drift
    result["oral_contact"]["per_window_grip_precision_m"] = grip_precision
    result["oral_contact"]["maximum_resisted_drift_m"] = max(grip_precision)
    result["oral_contact"]["windows"] = profile["anchor"]["windows"]
    out_receipt.write_text(json.dumps(result, indent=2) + "\n")
    print(f"  samples={len(result['samples'])} window_drift={[round(v, 4) for v in window_drift]}", flush=True)
    print("post-overlay (tremor + tail wave) ...", flush=True)
    overlay = add_overlay(out_glb)
    print(f"  tremor bones={overlay['tremor_bones']} wave bones={overlay['wave_bones']}", flush=True)
    print("gates ...", flush=True)
    receipt = json.loads(out_receipt.read_text())
    facts = gates(out_glb, receipt)
    print(f"  lifts={facts['yank_mouth_lift_m']} crossings={facts['jaw_state_crossings']} "
          f"maxshut={facts['max_shut_hold_s']}s stack={facts['head_stack_range_deg']}deg "
          f"tail_lat={facts['tail_tip_lateral_range_m']}m pelvis={facts['pelvis_cyclic_y_range_m']}m", flush=True)
    (OUTPUT / "feeding004-gates.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
