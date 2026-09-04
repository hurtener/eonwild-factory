"""Reference-video silhouette analysis for species/profile fitting.

The tool intentionally reports measured image-space quantities separately from
biomechanical inferences. It does not claim markerless motion capture from a
single uncalibrated side view.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import math

import cv2
import numpy as np


@dataclass
class FrameMeasurement:
    index: int
    time_seconds: float
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]
    ground_y: float
    torso_axis_degrees: float
    foreground_area: int


def _largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if count <= 1:
        return np.zeros_like(mask, dtype=np.uint8)
    index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == index).astype(np.uint8)


def _measure(mask: np.ndarray, index: int, fps: float) -> FrameMeasurement | None:
    ys, xs = np.nonzero(mask)
    if len(xs) < 200:
        return None
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    width = max(1, x1 - x0 + 1)
    # Torso is measured from the central 30% of the silhouette to reduce head/tail bias.
    mids_x: list[float] = []
    mids_y: list[float] = []
    for x in range(int(x0 + 0.37 * width), int(x0 + 0.67 * width)):
        column = np.flatnonzero(mask[:, x])
        if len(column) < 6:
            continue
        span = float(column[-1] - column[0])
        if span < 0.08 * (y1 - y0 + 1):
            continue
        mids_x.append(float(x))
        mids_y.append(0.5 * float(column[0] + column[-1]))
    angle = 0.0
    if len(mids_x) >= 8:
        slope, _ = np.polyfit(np.asarray(mids_x), np.asarray(mids_y), 1)
        angle = math.degrees(math.atan(float(slope)))
    return FrameMeasurement(
        index=index,
        time_seconds=index / fps,
        bbox=(x0, y0, x1, y1),
        centroid=(float(xs.mean()), float(ys.mean())),
        ground_y=float(np.quantile(ys, 0.995)),
        torso_axis_degrees=angle,
        foreground_area=int(len(xs)),
    )


def analyze_reference(path: str | Path, steady_start_seconds: float = 1.25) -> dict[str, Any]:
    source = Path(path)
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise OSError(f"Could not open reference video {source}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 24.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frames: list[np.ndarray] = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    if not frames:
        raise ValueError("Reference video contained no frames")

    # Estimate the pale studio background from border pixels over multiple frames.
    border_samples = []
    for frame in frames[:: max(1, len(frames) // 24)]:
        border_samples.extend([
            frame[:16].reshape(-1, 3), frame[-16:].reshape(-1, 3),
            frame[:, :16].reshape(-1, 3), frame[:, -16:].reshape(-1, 3),
        ])
    background = np.median(np.concatenate(border_samples, axis=0), axis=0)

    masks: list[np.ndarray] = []
    measurements: list[FrameMeasurement] = []
    kernel = np.ones((3, 3), np.uint8)
    for index, frame in enumerate(frames):
        delta = np.linalg.norm(frame.astype(np.float32) - background.astype(np.float32), axis=2)
        mask = (delta > 24.0).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        mask = _largest_component(mask)
        masks.append(mask)
        measured = _measure(mask, index, fps)
        if measured is not None:
            measurements.append(measured)

    steady_start = int(round(steady_start_seconds * fps))
    normalized: list[np.ndarray] = []
    for mask, measured in zip(masks, [_measure(mask, i, fps) for i, mask in enumerate(masks)]):
        if measured is None:
            normalized.append(np.zeros((96, 192), dtype=np.float32))
            continue
        x0, y0, x1, y1 = measured.bbox
        crop = mask[max(0, y0 - 4): min(height, y1 + 5), max(0, x0 - 4): min(width, x1 + 5)]
        canvas = np.zeros((96, 192), dtype=np.uint8)
        if crop.size:
            scale = min(184 / max(crop.shape[1], 1), 88 / max(crop.shape[0], 1))
            resized = cv2.resize(crop, (max(1, int(crop.shape[1] * scale)), max(1, int(crop.shape[0] * scale))), interpolation=cv2.INTER_NEAREST)
            oy = (96 - resized.shape[0]) // 2
            ox = (192 - resized.shape[1]) // 2
            canvas[oy:oy + resized.shape[0], ox:ox + resized.shape[1]] = resized
        normalized.append(canvas.astype(np.float32))

    # Translation-normalized silhouette autocorrelation over plausible gait lags.
    lag_min = max(12, int(1.2 * fps))
    lag_max = min(int(3.0 * fps), len(normalized) - steady_start - 1)
    lag_scores: dict[int, float] = {}
    for lag in range(lag_min, lag_max + 1):
        values = []
        for index in range(steady_start, len(normalized) - lag):
            a = normalized[index]
            b = normalized[index + lag]
            union = np.logical_or(a > 0.5, b > 0.5).sum()
            if union == 0:
                continue
            intersection = np.logical_and(a > 0.5, b > 0.5).sum()
            values.append(1.0 - intersection / union)
        if values:
            lag_scores[lag] = float(np.median(values))
    best_lag = min(lag_scores, key=lag_scores.get) if lag_scores else int(round(2.0 * fps))

    steady_measurements = [m for m in measurements if m.index >= steady_start]
    torso = np.asarray([m.torso_axis_degrees for m in steady_measurements], dtype=np.float64)
    ground = np.asarray([m.ground_y for m in steady_measurements], dtype=np.float64)
    bbox_heights = np.asarray([m.bbox[3] - m.bbox[1] + 1 for m in steady_measurements], dtype=np.float64)
    centroid_x = np.asarray([m.centroid[0] for m in steady_measurements], dtype=np.float64)
    time = np.asarray([m.time_seconds for m in steady_measurements], dtype=np.float64)
    image_speed = float(np.polyfit(time, centroid_x, 1)[0]) if len(time) >= 2 else 0.0

    return {
        "source": str(source),
        "measurement_scope": "single uncalibrated side-view silhouette analysis",
        "video": {
            "fps": fps,
            "frame_count_reported": frame_count,
            "frame_count_decoded": len(frames),
            "duration_seconds": len(frames) / fps,
            "width": width,
            "height": height,
            "estimated_background_bgr": background.astype(float).tolist(),
        },
        "steady_interval": {
            "start_seconds": steady_start_seconds,
            "end_seconds": len(frames) / fps,
        },
        "reference_fit": {
            "best_cycle_lag_frames": int(best_lag),
            "best_cycle_seconds": float(best_lag / fps),
            "lag_score": float(lag_scores.get(best_lag, 0.0)),
            "median_torso_axis_degrees_image": float(np.median(torso)) if len(torso) else 0.0,
            "p10_torso_axis_degrees_image": float(np.percentile(torso, 10)) if len(torso) else 0.0,
            "p90_torso_axis_degrees_image": float(np.percentile(torso, 90)) if len(torso) else 0.0,
            "median_ground_y_pixels": float(np.median(ground)) if len(ground) else 0.0,
            "median_silhouette_height_pixels": float(np.median(bbox_heights)) if len(bbox_heights) else 0.0,
            "centroid_translation_pixels_per_second": image_speed,
            "recommended_cycle_hz": float(fps / best_lag),
            "recommended_stance_fraction": 0.72,
            "recommended_posture": "relaxed forward balance; near-horizontal torso; skull carried close to horizon",
        },
        "frames": [asdict(value) for value in measurements],
        "limits": [
            "No calibrated camera or world scale.",
            "No anatomical markers or force measurements.",
            "Silhouette periodicity estimates cadence but not exact joint trajectories.",
            "Reference values remain profile constraints, not motion-capture ground truth.",
        ],
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze_reference(args.video)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "cycleSeconds": result["reference_fit"]["best_cycle_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
