#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
excluded={'PACKAGE_MANIFEST_V8_1.json','SHA256SUMS_V8_1.txt'}
files=[]
for path in sorted(ROOT.rglob('*')):
    rel=path.relative_to(ROOT)
    if not path.is_file() or path.name in excluded or path.name=='.DS_Store' or '__pycache__' in rel.parts or path.suffix=='.pyc':continue
    raw=path.read_bytes();files.append({'path':rel.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(ROOT/'PACKAGE_MANIFEST_V8_1.json').write_text(json.dumps({'schema':'eonwild.package-manifest.v8.1','fileCount':len(files),'files':files},indent=2)+'\n')
(ROOT/'SHA256SUMS_V8_1.txt').write_text(''.join(f"{x['sha256']}  {x['path']}\n" for x in files))
print(json.dumps({'fileCount':len(files)}))
