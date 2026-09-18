"""Pure clock and declared-travel helpers for connected review rendering."""
from __future__ import annotations

import bisect


def plan_distance(rows: list[dict], time_s: float) -> float:
    times = [float(row["time_s"]) for row in rows]
    if time_s < times[0] - 2e-6 or time_s > times[-1] + 2e-6:
        raise ValueError("connected source time is outside its declared motor trajectory")
    index = bisect.bisect_left(times, time_s)
    if index < len(times) and abs(times[index] - time_s) <= 2e-6:
        return float(rows[index]["root_forward_m"])
    if index == 0 or index == len(times):
        raise ValueError("connected motor trajectory cannot bracket source time")
    before, after = rows[index - 1], rows[index]
    alpha = (time_s - float(before["time_s"])) / (float(after["time_s"]) - float(before["time_s"]))
    return float(before["root_forward_m"]) + alpha * (
        float(after["root_forward_m"]) - float(before["root_forward_m"])
    )


def segment_at(segments: list[dict], timeline_s: float) -> dict:
    """Select half-open film intervals, assigning an exact join to its new segment."""
    starts = [float(row["timeline_start_s"]) for row in segments]
    index = bisect.bisect_right(starts, timeline_s + 1e-12) - 1
    if index < 0 or index >= len(segments) or timeline_s >= float(segments[index]["timeline_end_s"]) - 1e-12:
        if index + 1 < len(segments) and abs(timeline_s - float(segments[index + 1]["timeline_start_s"])) <= 2e-9:
            index += 1
        else:
            raise ValueError("connected film time is outside its schedule")
    return segments[index]
