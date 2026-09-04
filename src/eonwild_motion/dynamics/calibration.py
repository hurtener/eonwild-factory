"""Open-source calibration anchors for capacity and gait regimes.

Every number here carries retrieval provenance (URL + date + exact
claim). Strength of evidence is labeled per value: open-encyclopedia
priors are *not* peer-reviewed calibration — they bound obvious
nonsense and name the papers that must replace them (see
``PEER_REVIEW_BACKLOG``). Nothing in this module changes planner
verdicts; it adds independent plausibility checks that fail loudly on
absurd speeds and regimes.
"""

from __future__ import annotations

import math
from typing import Any

from ..errors import ContractError
from .centroidal import _finite

RETRIEVED = "2026-09-04"

SOURCES: dict[str, dict[str, str]] = {
    "froude_formula": {
        "url": "https://en.wikipedia.org/wiki/Froude_number",
        "retrieved": RETRIEVED,
        "claim": "Fr = v^2 / (g*l); legged locomotion analyzed as inverted "
        "pendulum; dynamically similar gaits at equal Fr (Alexander).",
        "strength": "open-encyclopedia summary of textbook biomechanics",
    },
    "gait_transition_fr": {
        "url": "https://en.wikipedia.org/wiki/Froude_number",
        "retrieved": RETRIEVED,
        "claim": "Walk-to-run transition around Fr ~ 0.5; amble to symmetric "
        "running gait around Fr ~ 1.0 (Alexander 1984).",
        "strength": "open-encyclopedia summary; needs Alexander 1976/1984 primary",
    },
    "ostrich_top_speed": {
        "url": "https://en.wikipedia.org/wiki/Ostrich",
        "retrieved": RETRIEVED,
        "claim": "Ostrich top speed 70 km/h — fastest living land bird; "
        "upper plausibility anchor for large-biped sprint claims.",
        "strength": "open-encyclopedia; needs primary speed-trial sourcing",
    },
}

PEER_REVIEW_BACKLOG: tuple[str, ...] = (
    "Rubenson et al. 2004 — ostrich running GRF multiples (force prior).",
    "Hutchinson & Garcia 2002 — T. rex top-speed modeling bounds.",
    "Sellers & Manning 2007 — multi-ton biped speed estimates.",
    "Gatesy & Biewener 1991 — bipedal locomotion mechanics baseline.",
    "Alexander 1976/1984 — Froude dynamic-similarity primaries.",
)


def froude_number(speed_mps: float, leg_length_m: float, *, gravity_mps2: float = 9.81) -> float:
    """Fr = v²/(g·l); hip height is the accepted leg-length proxy here."""
    speed = _finite(speed_mps, label="speed_mps")
    length = _finite(leg_length_m, label="leg_length_m")
    gravity = _finite(gravity_mps2, label="gravity_mps2")
    if speed < 0.0 or length <= 0.0 or gravity <= 0.0:
        raise ContractError("froude inputs are out of range")
    return speed * speed / (gravity * length)


def froude_frequency_hz(froude: float, leg_length_m: float, *, gravity_mps2: float = 9.81) -> float:
    """Characteristic frequency scale sqrt(Fr·g/l) — NOT a cadence prediction.

    It equals stride frequency only under stride-length ≈ leg-length, which
    cursorial bipeds violate by over-striding (our run: 2.66·l). Compare
    against measured cadence as a scaling check, never as a target.
    """
    fr = _finite(froude, label="froude")
    length = _finite(leg_length_m, label="leg_length_m")
    if fr < 0.0 or length <= 0.0:
        raise ContractError("froude frequency inputs are out of range")
    return math.sqrt(fr * gravity_mps2 / length)


def classify_gait(froude: float) -> dict[str, Any]:
    """Regime bins from the sourced Alexander transition points."""
    fr = _finite(froude, label="froude")
    if fr < 0.0:
        raise ContractError("froude number must be non-negative")
    if fr < 0.5:
        regime = "walk"
    elif fr < 1.0:
        regime = "walk_run_transition"
    elif fr <= 10.0:
        regime = "run"
    else:
        regime = "extreme_sprint"
    return {
        "froude": fr,
        "regime": regime,
        "source": "gait_transition_fr",
        "flight_expected": fr >= 0.5,
    }


def plausibility_report(
    *,
    speed_mps: float,
    hip_height_m: float,
    duty_factor: float,
    has_flight: bool,
    label: str = "gait",
) -> dict[str, Any]:
    """Independent speed/regime/flight consistency check (fail-loud).

    Uses hip height as the leg-length proxy (documented assumption).
    Flags: aerial gait below Fr 0.5 (no ballistic flight down there);
    duty factor above 0.5 while claiming flight (a foot is always down);
    speeds past the ostrich anchor without an extreme-sprint regime.
    """
    speed = _finite(speed_mps, label="speed_mps")
    hip = _finite(hip_height_m, label="hip_height_m")
    duty = _finite(duty_factor, label="duty_factor")
    if speed < 0.0 or hip <= 0.0 or not 0.0 < duty < 1.0:
        raise ContractError("plausibility inputs are out of range")
    fr = froude_number(speed, hip)
    regime = classify_gait(fr)["regime"]
    flags: list[str] = []
    if has_flight and fr < 0.5:
        flags.append(f"flight claimed at Fr {fr:.2f} < 0.5 (below run transition)")
    if has_flight and duty > 0.5:
        flags.append(f"duty {duty:.3f} > 0.5 contradicts flight (a foot is always down)")
    if speed > 70.0 / 3.6 and regime != "extreme_sprint":
        flags.append("speed past the ostrich 70 km/h anchor outside extreme-sprint regime")
    return {
        "label": label,
        "speed_mps": speed,
        "speed_kmh": speed * 3.6,
        "hip_height_m": hip,
        "froude": fr,
        "regime": regime,
        "duty_factor": duty,
        "has_flight": bool(has_flight),
        "froude_frequency_hz": froude_frequency_hz(fr, hip),
        "flags": flags,
        "verdict": "PASS" if not flags else "FAIL",
        "sources": ["froude_formula", "gait_transition_fr", "ostrich_top_speed"],
    }


__all__ = [
    "PEER_REVIEW_BACKLOG",
    "RETRIEVED",
    "SOURCES",
    "classify_gait",
    "froude_frequency_hz",
    "froude_number",
    "plausibility_report",
]
