#!/usr/bin/env python3
from pathlib import Path
import base64,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validated_result/v5'; SRC=ROOT/'toolkit/v5/browser_demo'
html=(SRC/'index.html').read_text(); js=(SRC/'v5-viewer.js').read_text(); manifest=json.loads((OUT/'animation-manifest.v5.json').read_text()); b64=base64.b64encode((OUT/'tarbosaurus_procedural_v5_animation_pack.glb').read_bytes()).decode('ascii')
embed='<script>window.__EONWILD_V5_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';window.__EONWILD_V5_GLB_BASE64="'+b64+'";</script>\n<script>'+js.replace('</script>','<\\/script>')+'</script>'
html=html.replace('<script src="v5-viewer.js"></script>',embed)
path=OUT/'OPEN_ME_tarbosaurus_v5_3d_browser.html';path.write_text(html);print(path,path.stat().st_size)
