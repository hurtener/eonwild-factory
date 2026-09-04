#!/usr/bin/env python3
"""Analyze the supplied Tarbosaurus power-attack / feeding reference.

The source contains camera cuts, zoom and perspective changes.  This script
therefore reports two clearly separated layers:

* observed timing / silhouette evidence from frames;
* authored motion interpretation used by V8.

It never represents the clip as calibrated motion capture.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def video_meta(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,nb_frames:format=duration,size",
        "-of", "json", str(path),
    ], text=True)
    payload = json.loads(raw)
    stream = payload["streams"][0]
    num, den = (int(x) for x in stream["avg_frame_rate"].split("/"))
    return {
        "duration_seconds": float(payload["format"]["duration"]),
        "file_size_bytes": int(payload["format"]["size"]),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": num / den,
        "frame_count": int(stream.get("nb_frames") or round(float(payload["format"]["duration"]) * num / den)),
    }


def read_frame(cap: cv2.VideoCapture, time_s: float) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_MSEC, float(time_s) * 1000.0)
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"Could not read frame at {time_s:.3f}s")
    return frame


def silhouette_metrics(frame_bgr: np.ndarray) -> dict:
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # White studio background is low-saturation and high-value.  Retain the
    # animal while suppressing most of the soft ground shadow.
    mask = ((hsv[:, :, 1] > 26) | (gray < 205)).astype(np.uint8) * 255
    mask[:4] = 0
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    count, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return {"valid": False}
    # Prefer a large component above the bottom shadow band.
    candidates = []
    h, w = mask.shape
    for i in range(1, count):
        x, y, bw, bh, area = stats[i]
        cy = cents[i][1]
        score = area * (0.45 if cy > h * 0.86 else 1.0)
        candidates.append((score, i))
    _, idx = max(candidates)
    component = labels == idx
    ys, xs = np.nonzero(component)
    points = np.column_stack([xs, ys]).astype(np.float64)
    center = points.mean(axis=0)
    cov = np.cov(points - center, rowvar=False)
    vals, vecs = np.linalg.eigh(cov)
    axis = vecs[:, int(np.argmax(vals))]
    angle = math.degrees(math.atan2(axis[1], axis[0]))
    x, y, bw, bh, area = stats[idx]
    return {
        "valid": True,
        "bbox_xywh": [int(x), int(y), int(bw), int(bh)],
        "area_pixels": int(area),
        "centroid_xy": [float(center[0]), float(center[1])],
        "principal_axis_angle_deg_ambiguous_180": float(angle),
        "height_fraction": float(bh / h),
        "width_fraction": float(bw / w),
        "centroid_y_fraction": float(center[1] / h),
    }


def create_contact_sheet(video: Path, out: Path, times: list[float], cols: int = 4) -> None:
    cap = cv2.VideoCapture(str(video))
    thumbs = []
    for t in times:
        frame = read_frame(cap, t)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        thumbs.append((t, Image.fromarray(rgb).resize((368, 200), Image.Resampling.LANCZOS)))
    cap.release()
    rows = math.ceil(len(thumbs) / cols)
    canvas = Image.new("RGB", (cols * 368, rows * 226), (18, 22, 23))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, (t, image) in enumerate(thumbs):
        x = (i % cols) * 368
        y = (i // cols) * 226
        canvas.paste(image, (x, y))
        draw.rectangle((x, y + 200, x + 368, y + 226), fill=(18, 22, 23))
        draw.text((x + 8, y + 207), f"{t:05.2f}s", fill=(244, 226, 164), font=font)
    canvas.save(out, quality=92)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    video = Path(args.video)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    meta = video_meta(video)

    key_times = [
        0.00, 0.25, 0.50, 0.75,
        1.00, 1.25, 1.50, 1.90,
        2.30, 2.75, 3.20, 3.75,
        4.15, 5.00, 6.50, 7.50,
        8.00, 8.45, 8.90, 9.35,
        9.75, 10.20, 10.65, 11.10,
        11.45, 11.75, 11.95,
    ]
    create_contact_sheet(video, output / "attack-eat-v8-keyframes.jpg", key_times, cols=4)

    cap = cv2.VideoCapture(str(video))
    metric_times = np.arange(meta["frame_count"], dtype=np.float64) / meta["fps"]
    silhouettes = []
    for t in metric_times:
        frame = read_frame(cap, float(t))
        silhouettes.append({"time_seconds": float(t), **silhouette_metrics(frame)})
    cap.release()

    observed = [
        {"start": 0.00, "end": 0.45, "label": "attention and lowering", "evidence": "Side silhouette: skull and neck lower while the hindlimbs begin flexing; the tail remains extended as a stabilizer."},
        {"start": 0.45, "end": 0.95, "label": "deep coil and pivot", "evidence": "The animal compresses and rotates toward camera; cranial direction changes before the hips complete the reorientation."},
        {"start": 0.95, "end": 1.50, "label": "explosive release", "evidence": "The head opens toward the future path, the tail sweeps opposite, and one leg drives while the other advances for a catch."},
        {"start": 1.50, "end": 3.45, "label": "low charge with sequential catches", "evidence": "The torso stays relatively low while alternating legs fold and extend beneath the pelvis; the gape remains intentional rather than breathing-scale."},
        {"start": 3.45, "end": 4.05, "label": "deceleration / posture recovery", "evidence": "Stride commitment reduces and the silhouette begins to settle before the camera cut."},
        {"start": 4.05, "end": 7.95, "label": "frontal display / repeated vocal gape", "evidence": "Camera changes to frontal; two broad gape/closure beats are visible. This section is treated as display/roar evidence, not bite contact."},
        {"start": 8.00, "end": 9.30, "label": "feeding target acquisition and descent", "evidence": "The head approaches the substrate with a controlled neck descent; the mouth remains mostly closed until near the target."},
        {"start": 9.30, "end": 10.05, "label": "late gape and bite acquisition", "evidence": "The jaw opens near the food rather than during the whole descent, then closes around it."},
        {"start": 10.05, "end": 11.55, "label": "clamped hold and tear", "evidence": "The head remains low, then pulls while the jaw is visibly engaged; the movement reads as neck/body bracing rather than chewing alone."},
        {"start": 11.55, "end": 12.04, "label": "release, chew and reposition", "evidence": "The head eases off the pull and the jaw/neck settle toward another feeding decision."},
    ]
    authored = {
        "attack": {
            "source_window_seconds": [0.0, 4.05],
            "interpretation": "Condense the observed pivot-to-charge into a gameplay-readable committed two-step power bite rather than copying camera motion or a full running loop.",
            "phases": [
                "target acquisition and gaze lock",
                "pelvis back/down coil with signed knee/ankle flexion",
                "head/neck target lead and tail counter-preload",
                "hindlimb release",
                "first advancing catch step",
                "second drive/catch step",
                "late jaw gape",
                "snap closure at contact",
                "clamped lateral hold/tear",
                "recoil, deceleration and grounded recovery",
            ],
            "non_negotiables": [
                "pelvis/contact transform solved before leg IK",
                "no post-solve body translation",
                "jaw closed at contact and recovery",
                "two readable support changes",
                "head motion leads but does not drag the center of mass",
            ],
        },
        "feeding": {
            "source_window_seconds": [8.0, 12.04],
            "interpretation": "Build a side-readable whole-body feeding loop from the frontal/three-quarter evidence: late gape, clamped bite, braced pull, chew/swallow, reacquisition and uneven timing.",
            "phases": [
                "low feeding-ready posture",
                "small target search",
                "jaw/neck retraction",
                "late gape",
                "short target thrust",
                "snap and clamp",
                "pelvis/foot brace",
                "diagonal side pull",
                "chew and swallow",
                "pause and reacquire",
            ],
            "variation": "Three unequal events with alternating pull direction and strength; exact complete-loop closure only after the full pattern.",
        },
        "turning": {
            "interpretation": "Increase the V7 cranio-cervical lead: eyes/head predict the path, neck forms curvature, chest follows, pelvis commits later, distal tail counters and releases after heading acceptance.",
            "perceptual_target": "A large animal reorienting mass, not a straight walk rotated on a turntable.",
        },
    }
    report = {
        "schema": "eonwild.reference-analysis.attack-eat.v8",
        "source": str(video.resolve()),
        "metadata": meta,
        "method": {
            "frame_review": "24 FPS source reviewed through timestamped contact sheets and key frames",
            "silhouette_metrics": "largest non-white connected component; principal axis is 180-degree ambiguous",
            "limitations": [
                "camera cuts and changing view prevent calibrated world-space reconstruction",
                "camera zoom/perspective confound absolute displacement",
                "the clip is used as behavioral and timing evidence, not motion capture",
            ],
        },
        "observed_timeline": observed,
        "authored_v8_interpretation": authored,
        "silhouette_samples": silhouettes,
    }
    (output / "attack-eat-reference-analysis-v8.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "README.md").write_text(
        "# V8 reference analysis\n\n"
        "The source video is preserved unchanged. `observed_timeline` records visible evidence; "
        "`authored_v8_interpretation` records animation-design inference. Camera cuts, zoom, and "
        "perspective prevent treating the source as calibrated motion capture.\n",
        encoding="utf-8",
    )
    print(json.dumps({"contact_sheet": str(output / 'attack-eat-v8-keyframes.jpg'), "report": str(output / 'attack-eat-reference-analysis-v8.json')}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
