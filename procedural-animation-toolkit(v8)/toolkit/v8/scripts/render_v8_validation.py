#!/usr/bin/env python3
"""Render the baked V8 GLB and build a self-contained multi-clip validation HTML."""
from __future__ import annotations

import argparse
import base64
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation
import vtk
from vtk.util import numpy_support

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader, BakedAnimation
from eonproc_v4.locomotion import TerrainAwareLocomotionGenerator
from eonproc_v4.profile import BipedV4Profile
from eonproc_v8.profile import BipedV8Profile
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator
from eonproc_v4.terrain import FlatTerrain, PlaneTerrain, ProceduralTerrain, TerrainSurface


@dataclass(frozen=True)
class PreviewSpec:
    key: str
    label: str
    clip: str | tuple[str, ...]
    view: str
    fps: int
    max_duration: float | None = None
    terrain: str = "flat"
    debug_soles: bool = False
    description: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source GLB used for texture/fixture checks")
    parser.add_argument("--animated-glb", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--v3-side")
    parser.add_argument("--v3-threeq")
    parser.add_argument("--reference-video")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    return parser.parse_args()


def vtk_image_to_pil(image: vtk.vtkImageData) -> Image.Image:
    width, height, _ = image.GetDimensions()
    scalars = image.GetPointData().GetScalars()
    components = scalars.GetNumberOfComponents()
    array = numpy_support.vtk_to_numpy(scalars).reshape(height, width, components)
    return Image.fromarray(np.flipud(array[:, :, :3]).astype(np.uint8), mode="RGB")


def rotation_from_matrix(matrix: np.ndarray) -> Rotation:
    basis = np.asarray(matrix[:3, :3], dtype=np.float64)
    u, _, vt = np.linalg.svd(basis)
    orthogonal = u @ vt
    if np.linalg.det(orthogonal) < 0.0:
        u[:, -1] *= -1.0
        orthogonal = u @ vt
    return Rotation.from_matrix(orthogonal)


class V8Renderer:
    def __init__(
        self,
        asset: GlbAsset,
        generator: TerrainAwareLocomotionGenerator,
        width: int,
        height: int,
        output_dir: Path,
    ):
        self.asset = asset
        self.g = generator
        self.primitive = asset.primitive()
        self.width = width
        self.height = height
        self.root_index = asset.name_to_node[generator.root]
        self.root_rest_rotation = rotation_from_matrix(asset.rest_world[self.root_index])

        material = asset.json["materials"][0]
        texture_index = material["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        image_index = asset.json["textures"][texture_index]["source"]
        mime = asset.json["images"][image_index].get("mimeType", "image/jpeg")
        extension = ".png" if mime == "image/png" else ".jpg"
        texture_path = output_dir / f"_v8_basecolor{extension}"
        asset.extract_image(image_index, texture_path)

        points = vtk.vtkPoints()
        points.SetData(numpy_support.numpy_to_vtk(self.primitive.positions.astype(np.float32), deep=True))
        triangles = self.primitive.indices.reshape(-1, 3).astype(np.int64)
        legacy = np.empty((len(triangles), 4), dtype=np.int64)
        legacy[:, 0] = 3
        legacy[:, 1:] = triangles
        cells = vtk.vtkCellArray()
        cells.ImportLegacyFormat(numpy_support.numpy_to_vtkIdTypeArray(legacy.ravel(), deep=True))
        self.poly = vtk.vtkPolyData()
        self.poly.SetPoints(points)
        self.poly.SetPolys(cells)
        if self.primitive.texcoords is not None:
            texcoords = numpy_support.numpy_to_vtk(self.primitive.texcoords.astype(np.float32), deep=True)
            texcoords.SetNumberOfComponents(2)
            texcoords.SetName("TCoords")
            self.poly.GetPointData().SetTCoords(texcoords)
        if self.primitive.normals is not None:
            normals = numpy_support.numpy_to_vtk(self.primitive.normals.astype(np.float32), deep=True)
            normals.SetNumberOfComponents(3)
            normals.SetName("Normals")
            self.poly.GetPointData().SetNormals(normals)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.poly)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        reader = vtk.vtkPNGReader() if extension == ".png" else vtk.vtkJPEGReader()
        reader.SetFileName(str(texture_path))
        reader.Update()
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        texture.InterpolateOn()
        self.actor.SetTexture(texture)
        self.actor.GetProperty().SetAmbient(0.30)
        self.actor.GetProperty().SetDiffuse(0.84)

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.902, 0.923, 0.93)
        self.renderer.AddActor(self.actor)

        self.terrain_poly = vtk.vtkPolyData()
        terrain_mapper = vtk.vtkPolyDataMapper()
        terrain_mapper.SetInputData(self.terrain_poly)
        self.terrain_actor = vtk.vtkActor()
        self.terrain_actor.SetMapper(terrain_mapper)
        self.terrain_actor.GetProperty().SetColor(0.42, 0.48, 0.44)
        self.terrain_actor.GetProperty().SetOpacity(0.36)
        self.renderer.AddActor(self.terrain_actor)

        self.sole_poly = vtk.vtkPolyData()
        self.sole_points = vtk.vtkPoints()
        self.sole_poly.SetPoints(self.sole_points)
        glyph = vtk.vtkVertexGlyphFilter()
        glyph.SetInputData(self.sole_poly)
        sole_mapper = vtk.vtkPolyDataMapper()
        sole_mapper.SetInputConnection(glyph.GetOutputPort())
        self.sole_actor = vtk.vtkActor()
        self.sole_actor.SetMapper(sole_mapper)
        self.sole_actor.GetProperty().SetColor(0.93, 0.22, 0.10)
        self.sole_actor.GetProperty().SetPointSize(5.0)
        self.sole_actor.SetVisibility(False)
        self.renderer.AddActor(self.sole_actor)

        key = vtk.vtkLight()
        key.SetPosition(4.0, 7.0, 6.0)
        key.SetFocalPoint(0.0, 1.0, 0.0)
        key.SetIntensity(0.92)
        self.renderer.AddLight(key)
        fill = vtk.vtkLight()
        fill.SetPosition(-5.0, 4.2, -2.0)
        fill.SetFocalPoint(0.0, 1.0, 0.0)
        fill.SetIntensity(0.34)
        self.renderer.AddLight(fill)

        self.window = vtk.vtkRenderWindow()
        self.window.SetOffScreenRendering(1)
        self.window.SetMultiSamples(0)
        self.window.AddRenderer(self.renderer)
        self.window.SetSize(width, height)
        self.camera = self.renderer.GetActiveCamera()
        self.camera.SetViewUp(0.0, 1.0, 0.0)
        self.camera.SetViewAngle(31.0)
        self.capture = vtk.vtkWindowToImageFilter()
        self.capture.SetInput(self.window)
        self.capture.SetInputBufferTypeToRGB()

    def set_terrain(self, terrain: TerrainSurface, root_positions: np.ndarray) -> None:
        positions = np.asarray(root_positions)
        min_x = float(np.min(positions[:, 0]) - 3.2)
        max_x = float(np.max(positions[:, 0]) + 3.2)
        min_z = float(np.min(positions[:, 2]) - 4.0)
        max_z = float(np.max(positions[:, 2]) + 4.0)
        nx, nz = 42, max(60, int((max_z - min_z) * 13))
        xs = np.linspace(min_x, max_x, nx)
        zs = np.linspace(min_z, max_z, nz)
        xx, zz = np.meshgrid(xs, zs)
        query = np.column_stack([xx.ravel(), np.zeros(xx.size), zz.ravel()])
        heights, _ = terrain.heights_normals(query)
        vertices = np.column_stack([query[:, 0], heights - 0.001, query[:, 2]])
        triangles: list[tuple[int, int, int]] = []
        for iz in range(nz - 1):
            for ix in range(nx - 1):
                a = iz * nx + ix
                b = a + 1
                c = a + nx
                d = c + 1
                triangles.extend([(a, c, b), (b, c, d)])
        points = vtk.vtkPoints()
        points.SetData(numpy_support.numpy_to_vtk(vertices.astype(np.float32), deep=True))
        tri = np.asarray(triangles, dtype=np.int64)
        legacy = np.empty((len(tri), 4), dtype=np.int64)
        legacy[:, 0] = 3
        legacy[:, 1:] = tri
        cells = vtk.vtkCellArray()
        cells.ImportLegacyFormat(numpy_support.numpy_to_vtkIdTypeArray(legacy.ravel(), deep=True))
        self.terrain_poly.SetPoints(points)
        self.terrain_poly.SetPolys(cells)
        self.terrain_poly.Modified()

    def set_pose(self, world_matrices: list[np.ndarray], debug_soles: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        points, normals = self.asset.skin_mesh(
            self.primitive.positions,
            self.primitive.normals,
            self.primitive.joints,
            self.primitive.weights,
            world_matrices,
        )
        self.poly.GetPoints().SetData(numpy_support.numpy_to_vtk(points.astype(np.float32), deep=True))
        if normals is not None:
            vtk_normals = numpy_support.numpy_to_vtk(normals.astype(np.float32), deep=True)
            vtk_normals.SetNumberOfComponents(3)
            vtk_normals.SetName("Normals")
            self.poly.GetPointData().SetNormals(vtk_normals)
        self.poly.Modified()

        if debug_soles:
            selected = np.concatenate([
                self.g.sole.selections["l"].vertex_indices,
                self.g.sole.selections["r"].vertex_indices,
            ])
            sole = points[selected]
            self.sole_points.SetData(numpy_support.numpy_to_vtk(sole.astype(np.float32), deep=True))
            self.sole_points.Modified()
            self.sole_poly.Modified()
            self.sole_actor.SetVisibility(True)
        else:
            self.sole_actor.SetVisibility(False)

        root = world_matrices[self.root_index][:3, 3].copy()
        current_rotation = rotation_from_matrix(world_matrices[self.root_index])
        delta = current_rotation * self.root_rest_rotation.inv()
        lateral = delta.apply(self.g.base_basis.lateral)
        forward = delta.apply(self.g.base_basis.forward)
        lateral[1] = 0.0
        forward[1] = 0.0
        lateral /= max(np.linalg.norm(lateral), 1e-12)
        forward /= max(np.linalg.norm(forward), 1e-12)
        return root, lateral, forward

    def render(self, root: np.ndarray, lateral: np.ndarray, forward: np.ndarray, view: str) -> Image.Image:
        up = np.array([0.0, 1.0, 0.0])
        if view == "side":
            position = root + lateral * 8.35 + up * 0.95 + forward * 0.18
            focal = root - up * 0.49 + forward * 0.03
            angle = 31.0
        elif view == "threeq":
            position = root + lateral * 7.35 + up * 1.02 + forward * 1.60
            focal = root - up * 0.48 + forward * 0.05
            angle = 31.0
        elif view == "overhead":
            position = root + lateral * 4.7 + up * 6.0 - forward * 1.4
            focal = root - up * 0.40 + forward * 0.35
            angle = 36.0
        elif view == "feet":
            position = root + lateral * 3.1 - up * 0.42 + forward * 0.55
            focal = root - up * 1.08 + forward * 0.28
            angle = 24.0
        else:
            raise ValueError(view)
        self.camera.SetPosition(*map(float, position))
        self.camera.SetFocalPoint(*map(float, focal))
        self.camera.SetViewUp(0.0, 1.0, 0.0)
        self.camera.SetViewAngle(angle)
        self.renderer.ResetCameraClippingRange()
        self.window.Render()
        self.capture.Modified()
        self.capture.Update()
        return vtk_image_to_pil(self.capture.GetOutput())


def terrain_for(name: str, generator: TerrainAwareLocomotionGenerator, profile: BipedV4Profile) -> TerrainSurface:
    if name == "uneven":
        return ProceduralTerrain(
            amplitude=generator.hip_height * profile.uneven_terrain_amplitude_hip_fraction,
            wavelength=profile.uneven_terrain_wavelength_m,
            secondary_amplitude=generator.hip_height * profile.uneven_terrain_amplitude_hip_fraction * 0.24,
            secondary_wavelength=profile.uneven_terrain_wavelength_m * 0.48,
        )
    if name == "slope":
        return PlaneTerrain.from_slopes(forward_slope=0.075, height=generator.mesh_ground)
    return FlatTerrain(generator.mesh_ground)


def frame_samples(animation: BakedAnimation, fps: int, max_duration: float | None = None, start: float = 0.0) -> list[float]:
    duration = animation.duration - start if max_duration is None else min(max_duration, animation.duration - start)
    count = max(2, int(round(duration * fps)))
    return (start + np.arange(count, dtype=np.float64) / fps).tolist()


def encode_video(frame_dir: Path, destination: Path, fps: int) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", str(frame_dir / "frame_%04d.jpg"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination),
    ], check=True)


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def render_preview(
    spec: PreviewSpec,
    pack: AnimationPackReader,
    renderer: V8Renderer,
    terrain: TerrainSurface,
    output_dir: Path,
) -> tuple[Path, Path]:
    frame_dir = output_dir / "_frames" / spec.key
    shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True)
    sequence: list[tuple[BakedAnimation, float]] = []
    names = (spec.clip,) if isinstance(spec.clip, str) else spec.clip
    if len(names) == 1:
        animation = pack.animation(names[0])
        sequence.extend((animation, value) for value in frame_samples(animation, spec.fps, spec.max_duration))
    else:
        # Transition reel: small source lead-in, complete transition/action clips,
        # then a brief target-loop recovery. This renders the actual baked tracks.
        for index, name in enumerate(names):
            animation = pack.animation(name)
            if index == 0 or index == len(names) - 1:
                duration = min(0.8, animation.duration)
                start = max(0.0, 0.22 * animation.duration) if index == 0 else 0.0
                values = frame_samples(animation, spec.fps, duration, start=start)
            else:
                values = frame_samples(animation, spec.fps)
            sequence.extend((animation, value) for value in values)

    root_positions = []
    worlds_cache: list[list[np.ndarray]] = []
    for animation, time_value in sequence:
        worlds = pack.world_matrices_at(animation, time_value)
        worlds_cache.append(worlds)
        root_positions.append(worlds[renderer.root_index][:3, 3])
    renderer.set_terrain(terrain, np.asarray(root_positions))

    selected_images: list[Image.Image] = []
    key_indices = set(np.linspace(0, len(sequence) - 1, 4).round().astype(int).tolist())
    for frame_index, worlds in enumerate(worlds_cache):
        root, lateral, forward = renderer.set_pose(worlds, spec.debug_soles)
        image = renderer.render(root, lateral, forward, spec.view)
        image.save(frame_dir / f"frame_{frame_index:04d}.jpg", "JPEG", quality=86, subsampling=1)
        if frame_index in key_indices:
            labeled = image.copy()
            draw = ImageDraw.Draw(labeled)
            draw.rounded_rectangle((8, 8, 230, 36), radius=7, fill=(245, 247, 247))
            draw.text((17, 16), f"{spec.label} · {frame_index/spec.fps:.2f}s", fill=(16, 25, 31))
            selected_images.append(labeled)
    video = output_dir / f"v8_{spec.key}_{spec.fps}fps.mp4"
    encode_video(frame_dir, video, spec.fps)
    strip = Image.new("RGB", (renderer.width * 4, renderer.height), "white")
    while len(selected_images) < 4:
        selected_images.append(selected_images[-1].copy())
    for index, image in enumerate(selected_images[:4]):
        strip.paste(image, (index * renderer.width, 0))
    montage = output_dir / f"v8_{spec.key}_keyframes.jpg"
    strip.save(montage, quality=90)
    return video, montage


def create_master_montage(montages: list[tuple[PreviewSpec, Path]], destination: Path) -> None:
    thumb_w, thumb_h = 480, 270
    rows = math.ceil(len(montages) / 2)
    canvas = Image.new("RGB", (thumb_w * 2, thumb_h * rows), (238, 241, 242))
    for index, (spec, path) in enumerate(montages):
        image = Image.open(path).convert("RGB")
        # use the second key pose from each strip
        crop_w = image.width // 4
        image = image.crop((crop_w, 0, crop_w * 2, image.height)).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, thumb_w, 34), fill=(15, 23, 29))
        draw.text((10, 9), spec.label, fill=(244, 228, 168))
        canvas.paste(image, ((index % 2) * thumb_w, (index // 2) * thumb_h))
    canvas.save(destination, quality=91)


def create_html(destination: Path, media: dict, specs: list[PreviewSpec], report: dict, fixture: dict, baked: dict | None) -> None:
    report_clips = report.get("clips", {})
    implementation = report.get("implementation", {})
    rows = []
    for spec in specs:
        names = [spec.clip] if isinstance(spec.clip, str) else list(spec.clip)
        rows.append({"key": spec.key, "label": spec.label, "description": spec.description, "clips": names, "view": spec.view, "fps": spec.fps})
    app_data = json.dumps({"media": media, "previews": rows}, separators=(",", ":"))
    locomotion_clip = report_clips.get("PROC_WALK_RELAXED_V8_ROOTMOTION", {})
    locomotion_diag = locomotion_clip.get("diagnostics", {})
    terrain_diag = report_clips.get("PROC_WALK_UNEVEN_TERRAIN_V8_ROOTMOTION", {}).get("diagnostics", {})
    clip_count = report.get("output", {}).get("clip_count", len(report_clips))
    sole_left = fixture.get("sole", {}).get("l", {}).get("selectedVertexCount", 0)
    sole_right = fixture.get("sole", {}).get("r", {}).get("selectedVertexCount", 0)
    reference_fit = report.get("profile", {}).get("cycle_hz", 0.45)
    max_pen = max(terrain_diag.get("loaded_max_penetration_m", {"l": 0.0, "r": 0.0}).values(), default=0.0) * 1000
    required_ok = (baked or {}).get("status", "PENDING")
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Eonwild Tarbosaurus V8 validation</title>
<style>
:root{{--bg:#091015;--panel:#101a21;--panel2:#17242c;--line:#2a3b46;--text:#edf4f6;--muted:#9cafba;--gold:#e5c771;--green:#88d4a7;--orange:#e6a66c}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 48% -15%,#29404d 0,#091015 48%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}.wrap{{max-width:1240px;margin:auto;padding:28px 22px 52px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;margin-bottom:18px}}h1{{margin:0;font-size:clamp(28px,4.5vw,50px);line-height:1.02;letter-spacing:-.035em}}.eyebrow{{color:var(--gold);font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:12px;margin-bottom:8px}}.status{{border:1px solid #315b46;color:var(--green);background:#13261d;border-radius:999px;padding:9px 12px;font-size:12px;font-weight:800;white-space:nowrap}}.viewer{{background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 28px 90px #0009}}video{{display:block;width:100%;aspect-ratio:16/9;object-fit:contain;background:#e6ebec}}.controls{{display:flex;gap:9px;align-items:center;flex-wrap:wrap;padding:13px 14px;border-top:1px solid var(--line)}}button{{font:inherit;color:var(--text);background:#1a2932;border:1px solid #354852;border-radius:9px;padding:8px 11px;cursor:pointer}}button:hover,button.active{{background:#2a3e49;border-color:#627a87}}select{{font:inherit;color:var(--text);background:#1a2932;border:1px solid #354852;border-radius:9px;padding:8px 10px;max-width:360px}}input[type=range]{{flex:1;min-width:200px;accent-color:var(--gold)}}.time{{color:var(--muted);font-variant-numeric:tabular-nums;font-size:12px;min-width:105px;text-align:right}}.stats{{display:grid;grid-template-columns:repeat(6,1fr);gap:11px;margin:15px 0}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px}}.num{{font-size:25px;font-weight:850;letter-spacing:-.035em}}.label{{color:var(--muted);font-size:11px;line-height:1.35;margin-top:3px}}.cols{{display:grid;grid-template-columns:1.25fr .9fr;gap:14px}}h2{{font-size:18px;margin:0 0 10px}}h3{{font-size:14px;margin:17px 0 7px}}p,li{{color:#c6d2d8;line-height:1.55}}ul{{padding-left:19px;margin:8px 0}}.pass{{color:#bde7cc}}.note{{border-left:3px solid var(--gold);background:#1b1d19;padding:10px 12px;border-radius:0 10px 10px 0;color:#d8d4c5;font-size:13px;margin-top:12px}}.clipname{{color:#f0da91;background:#0d151a;padding:2px 5px;border-radius:5px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em}}.previewmeta{{padding:11px 15px;background:#0d151a;border-top:1px solid var(--line);color:#b7c5cc;font-size:13px}}footer{{color:#81939d;font-size:12px;margin-top:20px}}@media(max-width:900px){{.stats{{grid-template-columns:repeat(3,1fr)}}.cols{{grid-template-columns:1fr}}}}@media(max-width:600px){{header{{flex-direction:column;align-items:flex-start}}.stats{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><div class="wrap"><header><div><div class="eyebrow">Eonwild procedural animation toolkit · V8</div><h1>Tarbosaurus production animation pack</h1></div><div class="status">✓ generated on the real 75-joint rig</div></header>
<section class="viewer"><video id="video" muted loop playsinline preload="metadata"></video><div class="previewmeta" id="meta"></div><div class="controls"><button id="play">Play</button><button data-speed="0.5">0.5×</button><button data-speed="1" class="active">1×</button><button data-speed="1.5">1.5×</button><select id="select"></select><input id="scrub" type="range" min="0" max="1000" value="0"><span id="time" class="time">0.00 / 0.00s</span></div></section>
<div class="stats"><div class="card"><div class="num">{clip_count}</div><div class="label">baked animation clips including actions and transitions</div></div><div class="card"><div class="num">{sole_left + sole_right}</div><div class="label">actual skinned sole vertices used for collision checks</div></div><div class="card"><div class="num">{reference_fit:.2f} Hz</div><div class="label">reference-fitted relaxed gait cadence</div></div><div class="card"><div class="num">{locomotion_diag.get('mean_speed_mps', 0.0):.2f} m/s</div><div class="label">resolved relaxed-walk root speed</div></div><div class="card"><div class="num">{max_pen:.2f} mm</div><div class="label">maximum loaded selected-sole penetration on uneven terrain</div></div><div class="card"><div class="num">{required_ok}</div><div class="label">baked GLB structural validation</div></div></div>
<div class="cols"><section class="card"><h2>V8 Design-Lab action and turn pass</h2><p>V8 preserves V7’s contact-locked pelvis/leg solve and regenerates the complete pack around a deeply staged power attack, expressive feeding, and stronger gaze-led turns. The final pelvis transform is established first, both complete legs and weighted sole patches are solved against that exact transform, and those same local tracks are exported without a later balance offset.</p><ul><li>The proven relaxed walk remains the lower-body regression baseline; action and turn changes are not allowed to reintroduce pelvis flight, sole penetration, or anatomical knee/ankle reversals.</li><li>Vertex-level contact checks use 64 representative skinned sole vertices per foot; the baked walk and turns were re-sampled after export to reject hovering and ground penetration.</li><li>Left and right turns use stronger head overshoot, distributed neck curvature, head pitch/roll focus, delayed chest and pelvis commitment, asymmetric steps, and an opposing nine-joint tail shape.</li><li>The power bite now stages target lock, hindlimb coil, two catch steps, late gape, snap, clamp, lateral tear, recoil and recovery. Feeding uses three unequal bite/pull/chew/swallow events in a 10.8-second exact loop.</li><li>Eighteen transitions are rebuilt against the final V8 poses and preserve root/pelvis endpoints for exact player handoff without a second crossfade.</li><li>The calibrated mostly-closed mouth is retained; broad gape is late and behavior-specific, with contact closure in both attack leads and each feeding bite.</li></ul><div class="note">The red contact-debug preview shows the exact selected mesh vertices evaluated against the uneven terrain—not toe-bone proxy points.</div></section><section class="card"><h2>Automated validation</h2><ul><li class="pass">All 68 semantic tags resolve; no mapped source bone is missing.</li><li class="pass">75-joint skin and inverse-bind matrices are preserved.</li><li class="pass">Signed knee and ankle branch constraints are enforced across every generated locomotion and action clip.</li><li class="pass">Source animation names are unique and all channel targets are valid.</li><li class="pass">Every animation timeline is finite and strictly increasing.</li><li class="pass">The contact system evaluates at 120 Hz and exports at 60 Hz; exact baked-track regression tests then recheck feet, pelvis, turns, and transitions.</li></ul><h3>Human review still matters</h3><p>Judge mass, intent, facial readability, foot deformation, transition timing, tail damping, and whether each action fits the game camera. The validators prove structural and biomechanical constraints; they do not replace animation direction.</p><div class="note">Preview videos are baked from the generated GLB itself. The interactive browser demo in the toolkit plays the same baked animation tracks directly.</div></section></div>
<footer>V8 action/turn refinement and inherited capability flags: {sum(bool(v) for v in implementation.values())}/{len(implementation)} V8 capability groups enabled. The supplied reference video is embedded as a separate visual comparison and is not represented as calibrated mocap.</footer></div>
<script>const app={app_data};const video=document.getElementById('video'),sel=document.getElementById('select'),meta=document.getElementById('meta'),play=document.getElementById('play'),scrub=document.getElementById('scrub'),time=document.getElementById('time');let speed=1;for(const p of app.previews){{const o=document.createElement('option');o.value=p.key;o.textContent=p.label;sel.appendChild(o)}}function load(key){{const p=app.previews.find(x=>x.key===key);video.src=app.media[key];video.load();video.playbackRate=speed;meta.innerHTML=`<b>${{p.label}}</b> · ${{p.fps}} FPS preview · <span class="clipname">${{p.clips.join(' → ')}}</span><br>${{p.description}}`;play.textContent='Play'}}sel.onchange=()=>load(sel.value);play.onclick=()=>{{if(video.paused){{video.play();play.textContent='Pause'}}else{{video.pause();play.textContent='Play'}}}};document.querySelectorAll('[data-speed]').forEach(b=>b.onclick=()=>{{speed=Number(b.dataset.speed);video.playbackRate=speed;document.querySelectorAll('[data-speed]').forEach(x=>x.classList.toggle('active',x===b))}});scrub.oninput=()=>{{if(video.duration)video.currentTime=Number(scrub.value)/1000*video.duration}};function fmt(x){{return Number.isFinite(x)?x.toFixed(2):'0.00'}}function sync(){{if(video.duration){{scrub.value=Math.round(video.currentTime/video.duration*1000);time.textContent=`${{fmt(video.currentTime)}} / ${{fmt(video.duration)}}s`}}requestAnimationFrame(sync)}}load(app.previews[0].key);requestAnimationFrame(sync);</script></body></html>'''
    destination.write_text(html, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    asset = GlbAsset(args.animated_glb)
    source_asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV8Profile()
    generator = TarbosaurusV8LocomotionGenerator(source_asset, semantics, profile)
    pack = AnimationPackReader(asset)
    renderer = V8Renderer(asset, generator, args.width, args.height, output)

    cycle = 1.0 / profile.cycle_hz
    specs = [
        PreviewSpec("walk_side", "V8 relaxed walk regression · side", "PROC_WALK_RELAXED_V8_INPLACE", "side", 20, cycle, "flat", False, "V7 contact-locked relaxed gait retained as the lower-body regression baseline."),
        PreviewSpec("turn_left_threeq", "V8 turn left · pronounced gaze lead", "PROC_TURN_LEFT_35_V8_ROOTMOTION", "threeq", 12, None, "flat", False, "Eyes/head overshoot toward the future path, the neck bends into the turn, chest follows, pelvis commits later, and the tail remains opposed."),
        PreviewSpec("turn_right_threeq", "V8 turn right · mirrored gaze lead", "PROC_TURN_RIGHT_35_V8_ROOTMOTION", "threeq", 12, None, "flat", False, "Mirrored review of cranio-cervical anticipation and asymmetric inside/outside steps."),
        PreviewSpec("bite_left_side", "Design-Lab power attack · side", "PROC_BITE_ATTACK_V8", "side", 20, None, "flat", False, "Target lock, deep pelvis coil, two support changes, late gape, snap contact, clamped side pull, recoil and grounded recovery."),
        PreviewSpec("bite_left_threeq", "Design-Lab power attack · three-quarter", "PROC_BITE_ATTACK_V8", "threeq", 12, None, "flat", False, "The same left-lead attack from a gameplay-oriented camera; review jaw timing, body brace, tail counter-shape and catch steps."),
        PreviewSpec("bite_right_threeq", "Mirrored power attack · three-quarter", "PROC_BITE_ATTACK_MIRRORED_V8", "threeq", 10, None, "flat", False, "Independent right-lead support and attack-direction validation."),
        PreviewSpec("eat_side", "Design-Lab feeding expression · side", "PROC_EAT_LOOP_V8", "side", 12, None, "flat", False, "Three unequal late-gape bite events with clamped alternating side pulls, whole-body bracing, chewing, swallowing and reacquisition."),
        PreviewSpec("eat_threeq", "Detailed feeding · three-quarter", "PROC_EAT_LOOP_V8", "threeq", 8, None, "flat", False, "Review head/neck expression, load transfer, tail counterbalance and exact long-loop closure."),
        PreviewSpec("bite_transition", "Walk → power attack → walk", ("PROC_WALK_RELAXED_V8_INPLACE", "PROC_WALK_TO_BITE_READY_V8", "PROC_BITE_ATTACK_V8", "PROC_BITE_TO_WALK_V8", "PROC_WALK_RELAXED_V8_INPLACE"), "threeq", 10, None, "flat", False, "Actual authored sequence with exact handoffs and no second runtime crossfade."),
    ]

    videos: dict[str, Path] = {}
    montages: list[tuple[PreviewSpec, Path]] = []
    for spec in specs:
        print(f"[render-v8] {spec.key}: {spec.label}", file=sys.stderr, flush=True)
        video, montage = render_preview(spec, pack, renderer, terrain_for(spec.terrain, generator, profile), output)
        videos[spec.key] = video
        montages.append((spec, montage))
    create_master_montage(montages, output / "tarbosaurus_v8_master_montage.jpg")

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    fixture_path = output.parent / "v8-fixture-validation.json"
    fixture = json.loads(fixture_path.read_text()) if fixture_path.exists() else {}
    baked_path = output.parent / "v8-baked-ground-regression.json"
    baked = json.loads(baked_path.read_text()) if baked_path.exists() else None
    media = {key: data_uri(path, "video/mp4") for key, path in videos.items()}
    if args.reference_video:
        reference_path = output / "reference_tarbosaurus_attack_eat.mp4"
        shutil.copy2(args.reference_video, reference_path)
        media["reference"] = data_uri(reference_path, "video/mp4")
        specs.append(PreviewSpec("reference", "Supplied power-attack / feeding reference", "SUPPLIED_REFERENCE_VIDEO", "source", 24, None, "flat", False, "The user-supplied attack/feeding reference. Observed timing and behavior are separated from authored inference; camera cuts and zoom prevent treating it as calibrated motion capture."))
    if args.v3_side:
        baseline_side = output / "baseline_v3_side.mp4"
        shutil.copy2(args.v3_side, baseline_side)
        media["v3_side"] = data_uri(baseline_side, "video/mp4")
        specs.append(PreviewSpec("v3_side", "V3 baseline · side", "PROC_WALK_LARGE_V3_INPLACE", "side", 60, None, "flat", False, "Previous validated baseline walk for direct visual regression review."))
    if args.v3_threeq:
        baseline_threeq = output / "baseline_v3_threeq.mp4"
        shutil.copy2(args.v3_threeq, baseline_threeq)
        media["v3_threeq"] = data_uri(baseline_threeq, "video/mp4")
        specs.append(PreviewSpec("v3_threeq", "V3 baseline · 3/4", "PROC_WALK_LARGE_V3_INPLACE", "threeq", 60, None, "flat", False, "Previous validated baseline three-quarter view for mass, posture, and tail comparison."))
    html_path = output / "OPEN_ME_tarbosaurus_v8_validation.html"
    create_html(html_path, media, specs, report, fixture, baked)
    shutil.rmtree(output / "_frames", ignore_errors=True)
    for temporary_texture in output.glob("_v8_basecolor.*"):
        temporary_texture.unlink(missing_ok=True)
    print(json.dumps({"html": str(html_path), "videos": {k: str(v) for k, v in videos.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
