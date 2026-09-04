#!/usr/bin/env python3
from pathlib import Path
import argparse,base64,json

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',required=True);ap.add_argument('--glb',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--browser-dir',default=str(Path(__file__).resolve().parents[1]/'browser_demo'));a=ap.parse_args()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);src=Path(a.browser_dir)
    html=(src/'index-v7.html').read_text();js=(src/'v7-viewer.js').read_text();manifest=json.loads(Path(a.manifest).read_text());b64=base64.b64encode(Path(a.glb).read_bytes()).decode('ascii')
    embed='<script>window.__EONWILD_V7_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';window.__EONWILD_V7_GLB_BASE64="'+b64+'";</script>\n<script>'+js.replace('</script>','<\\/script>')+'</script>'
    html=html.replace('<script src="v7-viewer.js"></script>',embed)
    path=out/'OPEN_ME_tarbosaurus_v7_3d_browser.html';path.write_text(html);print(path,path.stat().st_size)
if __name__=='__main__':main()
