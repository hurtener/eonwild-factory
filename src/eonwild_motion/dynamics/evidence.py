"""Deterministic visual evidence for the dynamics slice (stdlib only).

No matplotlib / Blender dependency: small SVG line charts rendered as
text, with fixed size, palette and number formatting, so bytes are stable
across runs and reviewers can open them in any browser. Each figure
builder returns ``(svg, facts)``; facts are the numeric claims the figure
visualizes and are embedded in the slice report.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

PALETTE = ("#1f6feb", "#d1242f", "#1a7f37", "#9a6700", "#6e40c9", "#0550ae")


def _nice_bounds(values: Sequence[float]) -> tuple[float, float]:
    low, high = min(values), max(values)
    if low == high:
        low, high = low - 1.0, high + 1.0
    pad = 0.08 * (high - low)
    return low - pad, high + pad


def svg_line_chart(
    title: str,
    series: Sequence[tuple[str, str, Sequence[float], Sequence[float]]],
    *,
    width: int = 640,
    height: int = 360,
    xlabel: str = "",
    ylabel: str = "",
) -> str:
    """One SVG line chart; deterministic formatting (3 decimals for data)."""
    margin_l, margin_r, margin_t, margin_b = 64, 16, 34, 44
    plot_w, plot_h = width - margin_l - margin_r, height - margin_t - margin_b
    all_x = [x for _, _, xs, _ in series for x in xs]
    all_y = [y for _, _, _, ys in series for y in ys]
    if not all_x or not all_y:
        raise ValueError("chart needs at least one point")
    x0, x1 = _nice_bounds([float(v) for v in all_x])
    y0, y1 = _nice_bounds([float(v) for v in all_y])

    def px(x: float) -> float:
        return margin_l + (x - x0) / (x1 - x0) * plot_w

    def py(y: float) -> float:
        return margin_t + (1.0 - (y - y0) / (y1 - y0)) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" font-family="sans-serif">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width // 2}" y="20" text-anchor="middle" font-size="14" font-weight="bold">{title}</text>',
    ]
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        yv = y0 + frac * (y1 - y0)
        parts.append(
            f'<line x1="{margin_l}" y1="{py(yv):.1f}" x2="{width - margin_r}" y2="{py(yv):.1f}" stroke="#e3e6ea"/>'
            f'<text x="{margin_l - 6}" y="{py(yv) + 4:.1f}" text-anchor="end" font-size="10" fill="#555">{yv:.2f}</text>'
        )
    for _, _, xs, ys in series:
        pts = " ".join(f"{px(float(x)):.1f},{py(float(y)):.1f}" for x, y in zip(xs, ys))
        parts.append(f'<polyline points="{pts}" fill="none" stroke-width="2"/>')
    # Color pass (keeps point formatting stable above).
    lines = []
    for i, (label, color, xs, ys) in enumerate(series):
        pts = " ".join(f"{px(float(x)):.1f},{py(float(y)):.1f}" for x, y in zip(xs, ys))
        lines.append(
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>'
            f'<text x="{width - margin_r}" y="{margin_t + 14 + 16 * i}" text-anchor="end" font-size="11" fill="{color}">{label}</text>'
        )
    parts.extend(lines)
    parts.append(f'<text x="{width // 2}" y="{height - 8}" text-anchor="middle" font-size="11" fill="#555">{xlabel}</text>')
    parts.append(f'<text x="12" y="{height // 2}" text-anchor="middle" font-size="11" fill="#555" transform="rotate(-90 12 {height // 2})">{ylabel}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def figure_ballistic_vs_kinematic() -> tuple[str, dict[str, Any]]:
    """Ballistic COM vs the legacy kinematic sine arc, same endpoints.

    Shows why the pelvis-sine was never a COM: equal endpoints, different
    physics — the sine implies phantom mid-flight forces, the ballistic
    arc implies none.
    """
    from .ballistic import BallisticRequest, plan_ballistic_com

    request = BallisticRequest(
        launch_com_m=(0.0, 2.0, 0.0),
        launch_velocity_mps=(3.7193, 3.0, 0.0),  # vx = 2.6 m / T analytic: hits the target
        landing_com_m=(2.6, 1.7, 0.0),
        total_mass_kg=1500.0,
        preload_velocity_mps=(4.0, 0.0, 0.0),
    )
    plan = plan_ballistic_com(request)
    times = [s["time_s"] for s in plan.samples]
    ballistic_y = [s["com_m"][1] for s in plan.samples]
    duration = plan.flight_time_s
    # Legacy kinematic arc pinned to the same endpoints for comparison.
    y0, y1 = ballistic_y[0], ballistic_y[-1]
    apex = max(ballistic_y)
    sine_y = [y0 + (y1 - y0) * (t / duration) + (apex - (y0 + y1) / 2) * math.sin(math.pi * t / duration) ** 2 for t in times]
    svg = svg_line_chart(
        "COM height: ballistic plan vs legacy kinematic sine (same endpoints)",
        [
            ("ballistic COM (gravity only)", PALETTE[0], times, ballistic_y),
            ("legacy sine arc (phantom forces)", PALETTE[1], times, sine_y),
        ],
        xlabel="flight time (s)",
        ylabel="COM height (m)",
    )
    from .ballistic import verify_ballistic_samples

    facts = {
        "flight_time_s": round(duration, 4),
        "verification": verify_ballistic_samples(plan.samples),
        "takeoff_impulse_ns": [round(v, 1) for v in (plan.takeoff_impulse_ns or [])],
        "landing_impulse_ns": [round(v, 1) for v in (plan.landing_impulse_ns or [])],
    }
    return svg, facts


def figure_contact_authority() -> tuple[str, dict[str, Any]]:
    """Skinned patch gap + persistent velocity across stance → flight."""
    from .contact_authority import AuthorityThresholds, PatchFrame, evaluate_contact_authority

    frames: list[PatchFrame] = []
    loaded: list[bool] = []
    for i in range(25):
        t = i / 120.0
        stance = i < 15
        gap = 0.0002 if stance else 0.02 + 0.05 * math.sin(math.pi * (i - 15) / 10)
        drift = 0.0004 * i if stance else 0.0
        sole = ((drift, gap, 0.10), (drift, gap, -0.10), (drift + 0.05, gap, 0.0))
        toe = ((drift + 0.12, gap, 0.05), (drift + 0.12, gap, -0.05))
        frames.append(PatchFrame(time_s=t, sole_m=sole, toe_m=toe))
        loaded.append(stance)
    report = evaluate_contact_authority(frames, loaded, thresholds=AuthorityThresholds())
    gaps = [min(min(p[1] for p in f.sole_m), min(p[1] for p in f.toe_m)) for f in frames]
    times = [f.time_s for f in frames]
    svg = svg_line_chart(
        "Contact authority: patch gap across stance (loaded) and flight",
        [("min patch gap (m)", PALETTE[2], times, gaps)],
        xlabel="time (s)",
        ylabel="gap (m)",
    )
    return svg, {"verdict": report["verdict"], "phases": report["phase_count"], "reasons": report["reasons"]}


def figure_budgets_and_growth() -> tuple[str, dict[str, Any]]:
    """Takeoff/landing margins vs launch speed + allometric trait scales."""
    from .capacity import CapacityProfile, assess_landing, assess_takeoff
    from .growth import allometric_scale

    capacity = CapacityProfile(profile_id="slice_fixture_v1")
    speeds = [2.0 + 0.5 * i for i in range(9)]
    force_margin, work_margin = [], []
    for speed in speeds:
        takeoff = assess_takeoff(
            total_mass_kg=1500.0,
            takeoff_impulse_ns=(1500.0 * speed, 1500.0 * 2.0, 0.0),
            stance_time_s=0.28,
            capacity=capacity,
        )
        landing = assess_landing(
            total_mass_kg=1500.0,
            impact_velocity_mps=(speed, -3.0, 0.0),
            capacity=capacity,
        )
        force_margin.append(takeoff["force_limit_n"] - takeoff["required_peak_force_n"])
        work_margin.append(landing["absorption_budget_j"] - landing["required_work_j"])
    svg = svg_line_chart(
        "Feasibility margins vs launch speed (fixture 1500 kg)",
        [
            ("takeoff force margin (N)", PALETTE[0], speeds, force_margin),
            ("landing work margin (J)", PALETTE[3], speeds, work_margin),
        ],
        xlabel="horizontal launch speed (m/s)",
        ylabel="margin (N / J)",
    )
    growth = {name: round(allometric_scale(t)["mass_ratio"], 3) for name, t in (("juvenile", 0.62), ("subadult", 0.82), ("adult", 1.0), ("heavy", 1.12))}
    return svg, {"capacity_status": capacity.status, "mass_ratios": growth}


def figure_bite_window() -> tuple[str, dict[str, Any]]:
    """Axial target tracking over a bite window plus the coupled tail."""
    import numpy as np

    from .whole_body import solve_bite_window

    parents = [None, 0, 1, 2]
    rest_t = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
    rest_r = [(0.0, 0.0, 0.0, 1.0)] * 4
    times = [i / 60.0 for i in range(19)]
    track = [{"root_position_m": (0.0, 0.0, 0.0)} for _ in times]
    targets = [(0.5 + 0.8 * (t / times[-1]), 2.5 - 0.7 * (t / times[-1]), 0.0) for t in times]
    window = solve_bite_window(
        parents=parents, rest_translations=rest_t, rest_rotations=rest_r,
        chain=[1, 2, 3], root_track=track,
        root_rotations=[np.eye(3)] * len(times), lateral_axis=(0.0, 0.0, 1.0),
        targets_m=targets, times_s=times,
        tail_params={"inertia_kg_m2": 750.0, "body_inertia_kg_m2": 7500.0},
    )
    residuals = [s["residual_m"] for s in window["samples"]]
    tail_angles = [math.degrees(s["angle_rad"]) for s in window["tail_track"]["samples"]]
    svg = svg_line_chart(
        "Bite window: head tracking residual and coupled tail answer",
        [
            ("tracking residual x100 (m)", PALETTE[1], times, [100 * r for r in residuals]),
            ("tail angle (deg)", PALETTE[0], times, tail_angles),
        ],
        xlabel="window time (s)",
        ylabel="residual x100 (m) / tail (deg)",
    )
    return svg, {
        "worst_residual_m": round(window["worst_residual_m"], 6),
        "all_reached": window["all_reached"],
        "tail_final_deg": round(tail_angles[-1], 3),
    }


__all__ = [
    "figure_ballistic_vs_kinematic",
    "figure_bite_window",
    "figure_budgets_and_growth",
    "figure_contact_authority",
    "svg_line_chart",
]
