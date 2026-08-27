#!/usr/bin/env python3
"""Render a self-contained v1/v2 validation HTML from a fully rigged GLB.

Requires numpy, scipy, PyYAML, VTK, Pillow, and ffmpeg. The produced HTML has no
network dependency: four H.264 previews are embedded as data URIs.
"""
from __future__ import annotations

import argparse
import base64
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
import vtk
from vtk.util import numpy_support

SCRIPT_DIR = Path(__file__).resolve().parent
V2_ROOT = SCRIPT_DIR
V1_ROOT = SCRIPT_DIR.parent.parent / "v1" / "scripts"
sys.path.insert(0, str(V2_ROOT))
sys.path.insert(0, str(V1_ROOT))

from eonproc_v2.gltf_io import GlbAsset
from eonproc_v2.rig import SemanticMap
from eonproc_v2.profile import BipedV2Profile
from eonproc_v2.generator import ContactAwareBipedGenerator
from eonproc_v1.generator import LegacyBipedGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--html-name", default="tarbosaurus-procedural-v2-validation.html")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    return parser.parse_args()


def vtk_image_to_pil(image: vtk.vtkImageData) -> Image.Image:
    width, height, _ = image.GetDimensions()
    scalars = image.GetPointData().GetScalars()
    components = scalars.GetNumberOfComponents()
    array = numpy_support.vtk_to_numpy(scalars).reshape(height, width, components)
    array = np.flipud(array[:, :, :3])
    return Image.fromarray(array.astype(np.uint8), mode="RGB")


class Renderer:
    def __init__(self, asset: GlbAsset, width: int, height: int, output_dir: Path):
        self.asset = asset
        self.primitive = asset.primitive()
        self.width = width
        self.height = height
        self.output_dir = output_dir

        material = asset.json["materials"][0]
        texture_index = material["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        image_index = asset.json["textures"][texture_index]["source"]
        mime = asset.json["images"][image_index].get("mimeType", "image/jpeg")
        extension = ".png" if mime == "image/png" else ".jpg"
        texture_path = output_dir / f"_preview_basecolor{extension}"
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
        if extension == ".png":
            reader = vtk.vtkPNGReader()
        else:
            reader = vtk.vtkJPEGReader()
        reader.SetFileName(str(texture_path))
        reader.Update()
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        texture.InterpolateOn()
        self.actor.SetTexture(texture)
        self.actor.GetProperty().SetAmbient(0.25)
        self.actor.GetProperty().SetDiffuse(0.82)

        self.renderer = vtk.vtkRenderer()
        self.renderer.AddActor(self.actor)
        self.renderer.SetBackground(0.91, 0.925, 0.93)

        plane = vtk.vtkPlaneSource()
        plane.SetOrigin(-3.2, -0.004, -6.0)
        plane.SetPoint1(3.2, -0.004, -6.0)
        plane.SetPoint2(-3.2, -0.004, 12.0)
        plane_mapper = vtk.vtkPolyDataMapper()
        plane_mapper.SetInputConnection(plane.GetOutputPort())
        plane_actor = vtk.vtkActor()
        plane_actor.SetMapper(plane_mapper)
        plane_actor.GetProperty().SetColor(0.57, 0.60, 0.59)
        plane_actor.GetProperty().SetOpacity(0.26)
        self.renderer.AddActor(plane_actor)

        grid_points = vtk.vtkPoints()
        grid_lines = vtk.vtkCellArray()

        def add_line(start: tuple[float, float, float], end: tuple[float, float, float]) -> None:
            first = grid_points.InsertNextPoint(*start)
            second = grid_points.InsertNextPoint(*end)
            grid_lines.InsertNextCell(2)
            grid_lines.InsertCellPoint(first)
            grid_lines.InsertCellPoint(second)

        for x in np.arange(-3.0, 3.01, 0.5):
            add_line((float(x), 0.0, -6.0), (float(x), 0.0, 12.0))
        for z in np.arange(-6.0, 12.01, 0.5):
            add_line((-3.0, 0.0, float(z)), (3.0, 0.0, float(z)))
        grid_poly = vtk.vtkPolyData()
        grid_poly.SetPoints(grid_points)
        grid_poly.SetLines(grid_lines)
        grid_mapper = vtk.vtkPolyDataMapper()
        grid_mapper.SetInputData(grid_poly)
        grid_actor = vtk.vtkActor()
        grid_actor.SetMapper(grid_mapper)
        grid_actor.GetProperty().SetColor(0.33, 0.37, 0.37)
        grid_actor.GetProperty().SetOpacity(0.27)
        grid_actor.GetProperty().SetLineWidth(1.0)
        self.renderer.AddActor(grid_actor)

        key = vtk.vtkLight()
        key.SetPosition(4.0, 7.0, 6.0)
        key.SetFocalPoint(0.0, 1.0, 0.0)
        key.SetIntensity(0.86)
        self.renderer.AddLight(key)
        fill = vtk.vtkLight()
        fill.SetPosition(-4.0, 4.0, -2.0)
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

    def set_mesh(self, world_matrices: list[np.ndarray]) -> None:
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

    def render(self, root_progress: float, view: str) -> Image.Image:
        if view == "side":
            self.camera.SetPosition(8.25, 2.25, root_progress + 0.18)
            self.camera.SetFocalPoint(0.0, 0.83, root_progress + 0.02)
        elif view == "threeq":
            self.camera.SetPosition(7.35, 2.34, root_progress + 1.62)
            self.camera.SetFocalPoint(0.0, 0.83, root_progress + 0.05)
        else:
            raise ValueError(view)
        self.renderer.ResetCameraClippingRange()
        self.window.Render()
        self.capture.Modified()
        self.capture.Update()
        return vtk_image_to_pil(self.capture.GetOutput())


def encode_video(frame_dir: Path, destination: Path, fps: int) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frame_dir / "frame_%04d.jpg"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(destination),
        ],
        check=True,
    )


def as_data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def create_html(
    destination: Path,
    clips: dict[str, dict[str, str]],
    report: dict,
    width: int,
    height: int,
) -> None:
    clip_json = json.dumps(clips, separators=(",", ":"))
    diagnostics = report["diagnostics"]
    contact_cm = max(diagnostics["max_contact_target_error_m"].values()) * 100.0
    toe_cm = max(diagnostics["max_loaded_toe_ground_error_m"].values()) * 100.0
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eonwild Tarbosaurus procedural animation — v2 validation</title>
<style>
:root{{--bg:#0b1116;--panel:#121b22;--panel2:#18242d;--text:#eef4f7;--muted:#9fb0bc;--line:#2b3b47;--accent:#e7c86d;--good:#8bd3a5;--v1:#d89b83}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 50% -20%,#263843 0,#0b1116 50%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:1220px;margin:auto;padding:28px 22px 50px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;margin-bottom:18px}}h1{{font-size:clamp(28px,4vw,48px);line-height:1.03;margin:0;letter-spacing:-.035em}}.eyebrow{{color:var(--accent);font-size:12px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px}}.status{{border:1px solid #365546;background:#15271f;color:var(--good);padding:8px 12px;border-radius:999px;font-size:12px;font-weight:800;white-space:nowrap}}
.viewer{{background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 24px 80px #0009}}.stage{{position:relative;background:#e8ecee;aspect-ratio:{width}/{height};display:grid;place-items:center}}video{{width:100%;height:100%;object-fit:contain;background:#e8ecee;display:block}}.compare{{display:none;width:100%;height:100%;grid-template-columns:1fr 1fr;gap:1px;background:#34444f}}.compare .pane{{position:relative;overflow:hidden;background:#e8ecee}}.badge{{position:absolute;top:12px;left:12px;background:#101820dc;color:white;padding:6px 9px;border-radius:8px;font-size:11px;font-weight:800;letter-spacing:.08em}}.badge.v1{{color:#ffd5c5}}.badge.v2{{color:#c5f4d5}}
.toolbar{{display:flex;flex-wrap:wrap;align-items:center;gap:9px;padding:13px 15px;border-top:1px solid var(--line)}}button,a.btn{{font:inherit;color:var(--text);background:#1b2831;border:1px solid #344650;padding:8px 11px;border-radius:9px;text-decoration:none;cursor:pointer}}button:hover,a.btn:hover,button.active{{background:#2a3b46;border-color:#536b79}}button.active{{color:var(--accent)}}input[type=range]{{flex:1;min-width:190px;accent-color:var(--accent)}}.time{{font-variant-numeric:tabular-nums;color:var(--muted);font-size:12px;min-width:102px;text-align:right}}.spacer{{width:8px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:11px;margin:16px 0}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}}.num{{font-size:25px;font-weight:850;letter-spacing:-.035em}}.label{{color:var(--muted);font-size:11px;line-height:1.35;margin-top:3px}}.cols{{display:grid;grid-template-columns:1.35fr 1fr;gap:14px}}h2{{font-size:18px;margin:0 0 9px}}h3{{font-size:14px;margin:14px 0 5px}}p,li{{color:#c5d1d7;line-height:1.56}}ul{{margin:7px 0 0;padding-left:18px}}code{{color:#f1dc99;background:#0e171d;padding:2px 5px;border-radius:5px}}.note{{border-left:3px solid var(--accent);padding:9px 12px;background:#191d19;border-radius:0 10px 10px 0;color:#d9d5c6;font-size:13px;margin-top:12px}}.v1note{{border-left-color:var(--v1)}}footer{{color:#7f919d;font-size:12px;margin-top:18px}}
@media(max-width:900px){{.grid{{grid-template-columns:repeat(3,1fr)}}.cols{{grid-template-columns:1fr}}}}@media(max-width:620px){{header{{align-items:flex-start;flex-direction:column}}.grid{{grid-template-columns:repeat(2,1fr)}}.compare{{grid-template-columns:1fr}}.compare .pane:first-child{{display:none}}}}
</style></head><body><div class="wrap">
<header><div><div class="eyebrow">Eonwild procedural animation skill v2</div><h1>Tarbosaurus contact-aware walk validation</h1></div><div class="status">✓ v2 baked and structurally validated</div></header>
<section class="viewer"><div class="stage"><video id="single" muted loop playsinline preload="auto"></video><div id="compare" class="compare"><div class="pane"><video id="left" muted loop playsinline preload="auto"></video><span class="badge v1">V1 · phase FK</span></div><div class="pane"><video id="right" muted loop playsinline preload="auto"></video><span class="badge v2">V2 · contact + balance</span></div></div></div>
<div class="toolbar"><button id="play">Play</button><button data-speed="0.5">0.5×</button><button data-speed="1" class="active">1×</button><button data-speed="1.5">1.5×</button><span class="spacer"></span><button data-mode="v2" class="active">V2</button><button data-mode="v1">V1</button><button data-mode="compare">Compare</button><span class="spacer"></span><button data-view="threeq" class="active">3/4</button><button data-view="side">Side</button><input id="scrub" type="range" min="0" max="1000" value="0"><span id="time" class="time">0.00 / 0.00s</span></div></section>
<div class="grid"><div class="card"><div class="num">75</div><div class="label">source skin joints preserved</div></div><div class="card"><div class="num">55</div><div class="label">bones actively driven in v2 walk</div></div><div class="card"><div class="num">120→60</div><div class="label">internal solve Hz → exported Hz</div></div><div class="card"><div class="num">{contact_cm:.2f} cm</div><div class="label">maximum loaded horizontal contact error</div></div><div class="card"><div class="num">{toe_cm:.2f} cm</div><div class="label">worst loaded toe-height proxy error</div></div><div class="card"><div class="num">9</div><div class="label">reactive tail segments</div></div></div>
<div class="cols"><section class="card"><h2>What changed in v2</h2><p>The walk is no longer a set of independent sine rotations. Each foot receives a contact position, C2-continuous swing path, load value, foot orientation, and toe phase. The full thigh–shin–ankle–foot chain is solved toward that target, while the pelvis shifts over the supporting leg before the opposite foot unloads.</p><p>The torso counter-rotates against pelvis yaw and roll; neck and head compensation retain some residual mass instead of becoming perfectly stabilized. The nine tail joints are driven by a periodically settled spring–damper response to support error, pelvis yaw, and pelvis velocity.</p><div class="note">The bind pose was mouth-open for modeling. V2 adds a neutral-pose layer that closes the five-joint mandible chain for locomotion, then applies only a small asynchronous breathing gape.</div><h3>Playback modes</h3><p><b>V2</b> shows the new two-cycle superloop. <b>V1</b> reconstructs the first phase-FK result. <b>Compare</b> keeps both videos synchronized. The moving-ground preview uses root motion so stance contacts can be judged against the grid.</p></section><section class="card"><h2>What still remains before “final”</h2><ul><li>Species-specific reference tuning should adjust stride length, stance timing, and pelvis compression from selected Tarbosaurus footage.</li><li>The current ground is flat; the same contact planner should be connected to terrain raycasts and surface normals at runtime.</li><li>Toe-ground validation currently uses semantic toe-tip joints as a proxy. A production validator should measure weighted sole vertices.</li><li>Turning, acceleration, stopping, attack transitions, and alert locomotion should reuse this kernel with different targets—not separate robotic cycles.</li></ul><div class="note v1note">V1 remains intentionally preserved. It is valuable as the low-complexity fallback and as a regression baseline, but v2 is the quality path.</div></section></div>
<footer>Generated from <code>tarbosaurus(1).glb</code> and <code>bone-map.edited-2.yml</code>. Embedded media is local to this HTML; no CDN or network access is required.</footer></div>
<script>
const clips={clip_json};let mode='v2',view='threeq',speed=1,playing=false;const single=document.getElementById('single'),compare=document.getElementById('compare'),left=document.getElementById('left'),right=document.getElementById('right'),scrub=document.getElementById('scrub'),time=document.getElementById('time'),play=document.getElementById('play');
function activeVideos(){{return mode==='compare'?[left,right]:[single]}}function master(){{return mode==='compare'?right:single}}function fmt(v){{return Number.isFinite(v)?v.toFixed(2):'0.00'}}
function setSources(preserve=true){{const t=preserve&&master().duration?master().currentTime:0;single.style.display=mode==='compare'?'none':'block';compare.style.display=mode==='compare'?'grid':'none';if(mode==='compare'){{left.src=clips.v1[view];right.src=clips.v2[view];left.load();right.load()}}else{{single.src=clips[mode][view];single.load()}}activeVideos().forEach(v=>{{v.playbackRate=speed;v.addEventListener('loadedmetadata',()=>{{v.currentTime=Math.min(t,v.duration||0);if(playing)v.play()}},{{once:true}})}})}}
function togglePlay(){{playing=!playing;activeVideos().forEach(v=>playing?v.play():v.pause());play.textContent=playing?'Pause':'Play'}}play.onclick=togglePlay;
document.querySelectorAll('[data-speed]').forEach(b=>b.onclick=()=>{{speed=Number(b.dataset.speed);document.querySelectorAll('[data-speed]').forEach(x=>x.classList.toggle('active',x===b));activeVideos().forEach(v=>v.playbackRate=speed)}});
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));setSources()}});document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{{view=b.dataset.view;document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b));setSources()}});
scrub.oninput=()=>{{const m=master();if(m.duration){{const t=Number(scrub.value)/1000*m.duration;activeVideos().forEach(v=>v.currentTime=t)}}}};
function sync(){{const m=master();if(mode==='compare'&&left.duration&&Math.abs(left.currentTime-right.currentTime)>.045)left.currentTime=right.currentTime;if(m.duration){{scrub.value=Math.round(m.currentTime/m.duration*1000);time.textContent=`${{fmt(m.currentTime)}} / ${{fmt(m.duration)}}s`}}requestAnimationFrame(sync)}}setSources(false);requestAnimationFrame(sync);
</script></body></html>'''
    destination.write_text(html, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_root = output_dir / "_render_frames"
    shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True)

    asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV2Profile()
    v2 = ContactAwareBipedGenerator(asset, semantics, profile)
    motion = v2.generate(keep_world_matrices=True)
    legacy = LegacyBipedGenerator(asset, semantics)
    renderer = Renderer(asset, args.width, args.height, output_dir)

    factor = profile.internal_sample_hz // profile.export_sample_hz
    export_indices = list(range(0, len(motion.times_internal), factor))
    if export_indices[-1] != len(motion.times_internal) - 1:
        export_indices.append(len(motion.times_internal) - 1)

    video_paths: dict[str, dict[str, Path]] = {"v1": {}, "v2": {}}
    for version in ("v1", "v2"):
        frame_dirs = {view: temp_root / f"{version}_{view}" for view in ("threeq", "side")}
        for directory in frame_dirs.values():
            directory.mkdir(parents=True)
        for frame_number, internal_index in enumerate(export_indices):
            global_phase = float(motion.times_internal[internal_index] / v2.cycle_duration)
            root_progress = v2.stride * global_phase
            if version == "v2":
                worlds = motion.world_matrices_internal[internal_index]
            else:
                pose = legacy.pose_at_phase(global_phase % 1.0)
                pose.add_world_translation_rest(legacy.root, legacy.basis.forward * root_progress)
                worlds = pose.world_matrices
            renderer.set_mesh(worlds)
            for view in ("threeq", "side"):
                image = renderer.render(root_progress, view)
                image.save(
                    frame_dirs[view] / f"frame_{frame_number:04d}.jpg",
                    format="JPEG", quality=88, optimize=False, subsampling=1,
                )
        for view in ("threeq", "side"):
            video = output_dir / f"tarbosaurus_{version}_{view}_60fps.mp4"
            encode_video(frame_dirs[view], video, profile.export_sample_hz)
            video_paths[version][view] = video

    clips = {
        version: {view: as_data_uri(path, "video/mp4") for view, path in views.items()}
        for version, views in video_paths.items()
    }
    report_path = output_dir / "procedural-v2-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        report = {"diagnostics": motion.diagnostics}
    html_path = output_dir / args.html_name
    create_html(html_path, clips, report, args.width, args.height)
    shutil.rmtree(temp_root, ignore_errors=True)
    print(json.dumps({"html": str(html_path), "videos": {k: {v: str(p) for v, p in x.items()} for k, x in video_paths.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
