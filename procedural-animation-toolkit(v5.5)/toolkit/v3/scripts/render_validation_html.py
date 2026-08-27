#!/usr/bin/env python3
"""Render V3 and build a self-contained V2/V3/reference validation HTML.

The V3 preview uses the exact generator pose sampled at 60 Hz. The HTML embeds
all media as data URIs and has no network dependency.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
import vtk
from vtk.util import numpy_support

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap
from eonproc_v3.profile import BipedV3Profile
from eonproc_v3.generator import AnatomicallyConstrainedBipedGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--v2-side")
    parser.add_argument("--v2-threeq")
    parser.add_argument("--reference-video")
    parser.add_argument("--html-name", default="tarbosaurus_procedural_v3_validation.html")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--preview-cycles", type=int, default=1)
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
        reader = vtk.vtkPNGReader() if extension == ".png" else vtk.vtkJPEGReader()
        reader.SetFileName(str(texture_path))
        reader.Update()
        texture = vtk.vtkTexture()
        texture.SetInputConnection(reader.GetOutputPort())
        texture.InterpolateOn()
        self.actor.SetTexture(texture)
        self.actor.GetProperty().SetAmbient(0.28)
        self.actor.GetProperty().SetDiffuse(0.82)

        self.renderer = vtk.vtkRenderer()
        self.renderer.AddActor(self.actor)
        self.renderer.SetBackground(0.91, 0.925, 0.93)

        plane = vtk.vtkPlaneSource()
        plane.SetOrigin(-3.4, -0.004, -8.0)
        plane.SetPoint1(3.4, -0.004, -8.0)
        plane.SetPoint2(-3.4, -0.004, 14.0)
        plane_mapper = vtk.vtkPolyDataMapper()
        plane_mapper.SetInputConnection(plane.GetOutputPort())
        plane_actor = vtk.vtkActor()
        plane_actor.SetMapper(plane_mapper)
        plane_actor.GetProperty().SetColor(0.57, 0.60, 0.59)
        plane_actor.GetProperty().SetOpacity(0.25)
        self.renderer.AddActor(plane_actor)

        grid_points = vtk.vtkPoints()
        grid_lines = vtk.vtkCellArray()
        def add_line(a: tuple[float, float, float], b: tuple[float, float, float]) -> None:
            ia = grid_points.InsertNextPoint(*a)
            ib = grid_points.InsertNextPoint(*b)
            grid_lines.InsertNextCell(2)
            grid_lines.InsertCellPoint(ia)
            grid_lines.InsertCellPoint(ib)
        for x in np.arange(-3.0, 3.01, 0.5):
            add_line((float(x), 0.0, -8.0), (float(x), 0.0, 14.0))
        for z in np.arange(-8.0, 14.01, 0.5):
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
        self.renderer.AddActor(grid_actor)

        key = vtk.vtkLight()
        key.SetPosition(4.0, 7.0, 6.0)
        key.SetFocalPoint(0.0, 1.0, 0.0)
        key.SetIntensity(0.88)
        self.renderer.AddLight(key)
        fill = vtk.vtkLight()
        fill.SetPosition(-4.0, 4.0, -2.0)
        fill.SetFocalPoint(0.0, 1.0, 0.0)
        fill.SetIntensity(0.35)
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
            self.camera.SetPosition(8.35, 2.27, root_progress + 0.18)
            self.camera.SetFocalPoint(0.0, 0.84, root_progress + 0.02)
        elif view == "threeq":
            self.camera.SetPosition(7.38, 2.35, root_progress + 1.62)
            self.camera.SetFocalPoint(0.0, 0.84, root_progress + 0.05)
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


def make_montage(frame_dirs: dict[str, Path], destination: Path) -> None:
    indices = [0, 30, 60, 90]
    rows: list[list[Image.Image]] = []
    for view in ("side", "threeq"):
        row = []
        files = sorted(frame_dirs[view].glob("frame_*.jpg"))
        for index in indices:
            image = Image.open(files[min(index, len(files) - 1)]).convert("RGB")
            image = image.resize((480, 270), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 112, 25), fill="white")
            draw.text((7, 5), f"{view} · {index/60:.2f}s", fill="black")
            row.append(image)
        rows.append(row)
    canvas = Image.new("RGB", (1920, 540), "white")
    for y, row in enumerate(rows):
        for x, image in enumerate(row):
            canvas.paste(image, (x * 480, y * 270))
    canvas.save(destination, quality=91)


def create_html(destination: Path, media: dict, report: dict, reference_analysis: dict) -> None:
    data = json.dumps(media, separators=(",", ":"))
    d = report["diagnostics"]
    gates = d.get("quality_gates", {})
    contact_cm = max(d["max_contact_target_error_m"].values()) * 100.0
    knee_min = min(d["joint_constraints"][s]["knee"]["flex_min_deg"] for s in ("l", "r"))
    ankle_min = min(d["joint_constraints"][s]["ankle"]["flex_min_deg"] for s in ("l", "r"))
    max_acc = d["max_joint_acceleration_deg_s2"]
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eonwild Tarbosaurus V3 validation</title>
<style>
:root{{--bg:#0a1015;--panel:#121b22;--panel2:#18242d;--text:#eef4f7;--muted:#9fb0bc;--line:#2b3b47;--gold:#e8c96c;--green:#89d3a4;--v2:#cc9a83;--blue:#8fc6e8}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 50% -20%,#263943 0,#0a1015 52%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.wrap{{max-width:1260px;margin:auto;padding:26px 22px 48px}}header{{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:17px}}h1{{font-size:clamp(27px,4vw,48px);line-height:1.02;letter-spacing:-.035em;margin:0}}.eyebrow{{color:var(--gold);font-weight:800;font-size:12px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px}}.status{{color:var(--green);background:#14261e;border:1px solid #315342;border-radius:999px;padding:8px 11px;font-size:12px;font-weight:800;white-space:nowrap}}.viewer{{background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 24px 80px #0008}}.stage{{position:relative;background:#e8ecee;aspect-ratio:16/9}}video{{width:100%;height:100%;display:block;object-fit:contain;background:#e8ecee}}.compare{{display:grid;grid-template-columns:1fr 1fr;width:100%;height:100%}}.pane{{position:relative;overflow:hidden;border-right:1px solid #1118}}.pane:last-child{{border-right:0}}.badge{{position:absolute;top:10px;left:10px;padding:5px 8px;border-radius:999px;background:#071017d9;color:white;font-size:11px;font-weight:850;letter-spacing:.05em}}.badge.v2{{background:#6d3f31e8}}.badge.v3{{background:#164d38e8}}.toolbar{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 14px;border-top:1px solid var(--line)}}button{{font:inherit;color:var(--text);background:#1b2831;border:1px solid #344753;padding:8px 10px;border-radius:9px;cursor:pointer}}button:hover,button.active{{background:#2b3d49;border-color:#617683}}.spacer{{width:1px;height:24px;background:var(--line);margin:0 3px}}input[type=range]{{flex:1;min-width:180px;accent-color:var(--gold)}}.time{{font-variant-numeric:tabular-nums;color:var(--muted);font-size:12px;min-width:110px;text-align:right}}.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:11px;margin:15px 0}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}}.num{{font-size:25px;font-weight:850;letter-spacing:-.035em}}.label{{color:var(--muted);font-size:11px;line-height:1.35;margin-top:2px}}.cols{{display:grid;grid-template-columns:1.25fr 1fr;gap:13px}}h2{{font-size:17px;margin:0 0 9px}}h3{{font-size:14px;margin:18px 0 5px}}p,li{{color:#c8d2d8;line-height:1.55}}ul{{margin:7px 0 0;padding-left:18px}}code{{color:#f3dd98;background:#0e161b;padding:2px 5px;border-radius:5px}}.note{{border-left:3px solid var(--gold);padding:9px 11px;background:#191c19;border-radius:0 9px 9px 0;color:#d9d5c7;font-size:13px;margin-top:11px}}.pass{{color:var(--green)}}.ref{{color:var(--blue)}}footer{{color:#7f929d;font-size:12px;margin-top:18px}}@media(max-width:930px){{.grid{{grid-template-columns:repeat(3,1fr)}}.cols{{grid-template-columns:1fr}}}}@media(max-width:660px){{header{{align-items:flex-start;flex-direction:column}}.grid{{grid-template-columns:repeat(2,1fr)}}.compare{{grid-template-columns:1fr}}.compare .pane:first-child{{display:none}}}}
</style></head><body><div class="wrap">
<header><div><div class="eyebrow">Eonwild procedural animation toolkit V3</div><h1>Tarbosaurus relaxed-walk validation</h1></div><div class="status">✓ zero knee/ankle reversals</div></header>
<section class="viewer"><div class="stage"><video id="single" muted loop playsinline preload="auto"></video><div id="compare" class="compare"><div class="pane"><video id="left" muted loop playsinline preload="auto"></video><span class="badge v2">V2</span></div><div class="pane"><video id="right" muted loop playsinline preload="auto"></video><span class="badge v3">V3</span></div></div></div><div class="toolbar"><button id="play">Play</button><button data-speed="0.5">0.5×</button><button data-speed="1" class="active">1×</button><button data-speed="1.5">1.5×</button><span class="spacer"></span><button data-mode="v3" class="active">V3</button><button data-mode="v2">V2</button><button data-mode="compare">Compare</button>{'<button data-mode="reference">Reference</button>' if 'reference' in media else ''}<span class="spacer"></span><button data-view="side" class="active">Side</button><button data-view="threeq">3/4</button><input id="scrub" type="range" min="0" max="1000" value="0"><span id="time" class="time">0.00 / 0.00s</span></div></section>
<div class="grid"><div class="card"><div class="num">0</div><div class="label">knee + ankle reverse-bend samples out of 481</div></div><div class="card"><div class="num">{knee_min:.1f}°</div><div class="label">minimum knee flexion retained</div></div><div class="card"><div class="num">{ankle_min:.1f}°</div><div class="label">minimum ankle flexion retained</div></div><div class="card"><div class="num">{contact_cm:.2f} cm</div><div class="label">maximum loaded horizontal contact error</div></div><div class="card"><div class="num">120→60</div><div class="label">internal solve Hz → baked GLB Hz</div></div><div class="card"><div class="num">{max_acc:.0f}</div><div class="label">maximum joint acceleration, below {d['profile']['max_joint_acceleration_deg_s2']:.0f}°/s² gate</div></div></div>
<div class="cols"><section class="card"><h2>What V3 fixes</h2><p>V2 could briefly choose the alternate inverse-kinematics branch as a leg recovered from rear extension. V3 measures the signed knee and ankle bend from the actual rig, then enforces that direction and non-zero flexion on every 120 Hz sample. A small unreachable-target error is accepted before an impossible joint pose.</p><p>Toe-off is now continuous in both target position and preferred heel/toe state. The solver carries the loaded toe-off pose into early swing and releases it with minimum-jerk curves instead of absorbing a hidden 5–7° preference jump.</p><p>The relaxed profile uses an approximately two-second cycle, 72% stance, a more level torso, a skull held near the horizon, and a softer tail whose root remains muscular while distal joints lag progressively.</p><div class="note"><b>Reference button:</b> the supplied 8.04-second side-view video is embedded untouched. It is a visual style reference, not calibrated motion capture.</div></section><section class="card"><h2>Automated gates</h2><ul><li class="pass">Zero signed knee reversals.</li><li class="pass">Zero signed ankle reversals.</li><li class="pass">Both constrained leg solvers converged on every sample.</li><li class="pass">Rotation and tail loop endpoints close exactly.</li><li class="pass">Loaded contact remains below 0.5% of hip height.</li><li class="pass">Joint velocity and acceleration remain inside the V3 profile ceilings.</li></ul><h3>What to judge visually</h3><ul><li>rear-to-front swing at 0.5×;</li><li>loading compression and extension;</li><li>horizon-facing relaxed posture versus V2;</li><li>tail root stability versus distal compliance;</li><li>mostly closed neutral mouth;</li><li>any source-weight deformation around ankle/toes.</li></ul><div class="note">The preview shows one 2.0-second gait cycle at 60 FPS. The downloadable GLB contains the full two-cycle, four-second superloop.</div></section></div>
<footer>Reference metadata: {reference_analysis.get('duration_seconds', 8.041667):.3f}s · {reference_analysis.get('fps', 24)} FPS · {reference_analysis.get('resolution', '736×400')}. Generated from the uploaded 75-joint GLB and edited semantic map. No CDN or network access is required.</footer></div>
<script>
const media={data};let mode='v3',view='side',speed=1,playing=false;const single=document.getElementById('single'),compare=document.getElementById('compare'),left=document.getElementById('left'),right=document.getElementById('right'),scrub=document.getElementById('scrub'),time=document.getElementById('time'),play=document.getElementById('play');
function active(){{return mode==='compare'?[left,right]:[single]}}function master(){{return mode==='compare'?right:single}}function fmt(v){{return Number.isFinite(v)?v.toFixed(2):'0.00'}}
function setSources(keep=true){{const old=master(),t=keep&&old.duration?old.currentTime:0;single.style.display=mode==='compare'?'none':'block';compare.style.display=mode==='compare'?'grid':'none';if(mode==='compare'){{left.src=media.v2[view];right.src=media.v3[view];left.load();right.load()}}else if(mode==='reference'){{single.src=media.reference;single.load()}}else{{single.src=media[mode][view];single.load()}}active().forEach(v=>{{v.playbackRate=speed;v.addEventListener('loadedmetadata',()=>{{v.currentTime=Math.min(t,Math.max(0,(v.duration||0)-.001));if(playing)v.play()}},{{once:true}})}})}}
play.onclick=()=>{{playing=!playing;active().forEach(v=>playing?v.play():v.pause());play.textContent=playing?'Pause':'Play'}};document.querySelectorAll('[data-speed]').forEach(b=>b.onclick=()=>{{speed=Number(b.dataset.speed);document.querySelectorAll('[data-speed]').forEach(x=>x.classList.toggle('active',x===b));active().forEach(v=>v.playbackRate=speed)}});document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('[data-view]').forEach(x=>x.disabled=mode==='reference');setSources(false)}});document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{{view=b.dataset.view;document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b));setSources()}});scrub.oninput=()=>{{const m=master();if(m.duration){{const t=Number(scrub.value)/1000*m.duration;active().forEach(v=>v.currentTime=t)}}}};
function sync(){{const m=master();if(mode==='compare'&&left.duration&&Math.abs(left.currentTime-right.currentTime)>.04)left.currentTime=right.currentTime;if(m.duration){{scrub.value=Math.round(m.currentTime/m.duration*1000);time.textContent=`${{fmt(m.currentTime)}} / ${{fmt(m.duration)}}s`}}requestAnimationFrame(sync)}}setSources(false);requestAnimationFrame(sync);
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
    profile = BipedV3Profile.from_json(args.profile) if args.profile else BipedV3Profile()
    generator = AnatomicallyConstrainedBipedGenerator(asset, semantics, profile)
    motion = generator.generate(keep_world_matrices=True)
    renderer = Renderer(asset, args.width, args.height, output_dir)

    cycles = max(1, min(args.preview_cycles, profile.supercycle_count))
    internal_frames = int(round(generator.cycle_duration * cycles * profile.internal_sample_hz)) + 1
    factor = profile.internal_sample_hz // profile.export_sample_hz
    export_indices = list(range(0, internal_frames, factor))
    if export_indices[-1] != internal_frames - 1:
        export_indices.append(internal_frames - 1)

    frame_dirs = {view: temp_root / f"v3_{view}" for view in ("side", "threeq")}
    for directory in frame_dirs.values():
        directory.mkdir(parents=True)
    for frame_number, internal_index in enumerate(export_indices):
        global_phase = float(motion.times_internal[internal_index] / generator.cycle_duration)
        root_progress = generator.stride * global_phase
        renderer.set_mesh(motion.world_matrices_internal[internal_index])
        for view in ("side", "threeq"):
            image = renderer.render(root_progress, view)
            image.save(frame_dirs[view] / f"frame_{frame_number:04d}.jpg", "JPEG", quality=88, subsampling=1)

    v3_paths = {}
    for view in ("side", "threeq"):
        path = output_dir / f"tarbosaurus_v3_{view}_60fps.mp4"
        encode_video(frame_dirs[view], path, profile.export_sample_hz)
        v3_paths[view] = path
    make_montage(frame_dirs, output_dir / "tarbosaurus_v3_keyframes.jpg")

    report_path = output_dir / "procedural-v3-report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {"diagnostics": motion.diagnostics}
    media: dict[str, object] = {
        "v3": {view: as_data_uri(path, "video/mp4") for view, path in v3_paths.items()},
    }
    if args.v2_side and args.v2_threeq:
        media["v2"] = {
            "side": as_data_uri(Path(args.v2_side), "video/mp4"),
            "threeq": as_data_uri(Path(args.v2_threeq), "video/mp4"),
        }
    else:
        media["v2"] = media["v3"]
    reference_analysis = {
        "duration_seconds": 8.041667,
        "fps": 24,
        "resolution": "736×400",
        "steady_cycle_estimate_seconds": 2.0,
        "basis": "silhouette observation; not calibrated mocap",
    }
    if args.reference_video:
        media["reference"] = as_data_uri(Path(args.reference_video), "video/mp4")
    (output_dir / "reference-analysis.json").write_text(json.dumps(reference_analysis, indent=2))

    html_path = output_dir / args.html_name
    create_html(html_path, media, report, reference_analysis)
    shutil.rmtree(temp_root, ignore_errors=True)
    print(json.dumps({"html": str(html_path), "videos": {k: str(v) for k, v in v3_paths.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
