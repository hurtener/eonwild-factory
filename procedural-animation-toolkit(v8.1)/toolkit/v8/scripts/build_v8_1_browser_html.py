#!/usr/bin/env python3
"""Build a dependency-free self-contained V8 WebGL2 animation player."""
from pathlib import Path
import argparse,base64,json,hashlib

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',required=True);ap.add_argument('--glb',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--browser-dir',default=str(Path(__file__).resolve().parents[1]/'browser_demo'));a=ap.parse_args()
 out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);src=Path(a.browser_dir)
 html=(src/'index-v8.1.html').read_text();js=(src/'v8.1-viewer.js').read_text();manifest=json.loads(Path(a.manifest).read_text());raw=Path(a.glb).read_bytes();b64=base64.b64encode(raw).decode('ascii')
 embed='<script>window.__EONWILD_V8_1_1_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';window.__EONWILD_V8_1_1_GLB_BASE64="'+b64+'";window.__EONWILD_V8_1_1_GLB_SHA256="'+hashlib.sha256(raw).hexdigest()+'";</script>\n<script>'+js.replace('</script>','<\\/script>')+'</script>'
 html=html.replace('<script src="v8.1-viewer.js"></script>',embed)
 path=out/'OPEN_ME_tarbosaurus_v8_1_3d_browser.html';path.write_text(html,encoding='utf-8');print(path,path.stat().st_size)
if __name__=='__main__':main()
