"""Encode original-albedo presentation without touching the clay artifacts."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import make_media as base

HERE=Path(__file__).resolve().parent
base.HERE=HERE/'textured'

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        media=list(pool.map(base.encode,['side','front','rear']))
    receipt=json.loads((base.HERE/'render/original-texture-receipt.json').read_text())
    candidate=hashlib.sha256((HERE/'feeding.glb').read_bytes()).hexdigest()
    assert candidate==receipt['candidate_sha256']=='8f70dcab8e8b56035ed0787ca15674166575213f098ec9c6579e6e8350b6d47b'
    result={'candidate_sha256':candidate,'presentation':'Original embedded albedo and UVs under existing studio lighting; not full PBR','renderer_sha256':receipt['renderer_sha256'],'original_base_color_binding':receipt['bindings'],'media':media}
    (base.HERE/'media-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
