#!/usr/bin/env python3
"""Validate the standalone V8 WebGL player and embedded animation contract."""
from __future__ import annotations
import argparse, base64, hashlib, json, re, subprocess
from pathlib import Path


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--html',required=True)
    ap.add_argument('--glb',required=True)
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--viewer-js',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    html=Path(a.html).read_text(encoding='utf-8')
    manifest=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
    raw=Path(a.glb).read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    source_js=Path(a.viewer_js).read_text(encoding='utf-8')

    mhash=re.search(r'window\.__EONWILD_V8_1_1_GLB_SHA256="([0-9a-f]{64})"',html)
    mb64=re.search(r'window\.__EONWILD_V8_1_1_GLB_BASE64="([A-Za-z0-9+/=]+)"',html)
    embedded_hash=mhash.group(1) if mhash else None
    decoded_hash=None
    decoded_size=None
    if mb64:
        decoded=base64.b64decode(mb64.group(1))
        decoded_hash=hashlib.sha256(decoded).hexdigest();decoded_size=len(decoded)

    names={c['name'] for c in manifest['clips']}
    clip_refs=set(re.findall(r'data-clip="([A-Z0-9_]+)"',html))
    # Action queues are literal arrays in the viewer source.
    queue_refs=set(re.findall(r'"(PROC_[A-Z0-9_]+)"',source_js))
    missing_clip_refs=sorted(clip_refs-names)
    missing_queue_refs=sorted(queue_refs-names)
    external_urls=re.findall(r'https?://[^\s"\']+',html)
    node=subprocess.run(['node','--check',a.viewer_js],capture_output=True,text=True)
    checks={
        'embedded_glb_present':mb64 is not None,
        'embedded_hash_matches_standalone':embedded_hash==digest==decoded_hash,
        'embedded_size_matches':decoded_size==len(raw),
        'manifest_clip_count_47':len(names)==47,
        'all_html_clip_references_exist':not missing_clip_refs,
        'all_action_queue_references_exist':not missing_queue_refs,
        'no_external_urls':not external_urls,
        'viewer_javascript_syntax':node.returncode==0,
        'active_button_state_present':'aria-pressed' in source_js and 'is-active' in source_js,
        'root_cycle_accumulation_present':'rootCycleDelta' in source_js,
        'authored_handoff_without_second_crossfade':('commitQueuedClip' in source_js and 'exactHandoff' in source_js and 'this.commitClip(item.name,item.loop,true)' in source_js),
    }
    status=all(checks.values())
    out={
        'status':'PASS' if status else 'FAIL',
        'checks':checks,
        'standaloneGlbSha256':digest,
        'embeddedGlbSha256':decoded_hash,
        'embeddedGlbBytes':decoded_size,
        'clipCount':len(names),
        'htmlClipReferences':len(clip_refs),
        'queueClipReferences':len(queue_refs),
        'missingHtmlClipReferences':missing_clip_refs,
        'missingQueueClipReferences':missing_queue_refs,
        'externalUrls':external_urls,
        'nodeSyntaxStderr':node.stderr.strip(),
    }
    Path(a.output).write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
    return 0 if status else 1

if __name__=='__main__': raise SystemExit(main())
