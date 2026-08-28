from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any

from ..contracts.models import ResolvedProfile
from ..glb.container import Glb
from ..hashing import sha256_file
from .validate import artifact_difference, contact_inheritance_facts, validate_animation_contract


def _artifact(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": sha256_file(path)}


def _write_review(path: Path, *, profile_id: str, baseline: dict, candidate: dict, facts: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    baseline_relative = Path(baseline["path"]).relative_to(path.parent)
    candidate_relative = Path(candidate["path"]).relative_to(path.parent)
    facts_json = escape(json.dumps(facts, indent=2, sort_keys=True))
    html = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>{escape(profile_id)} technical comparison</title>
<style>body{{margin:0;background:#11161a;color:#eef2ed;font:15px system-ui}}main{{max-width:1200px;margin:auto;padding:28px}}h1{{font-size:24px}}.notice{{color:#f2cc7b}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0}}img{{display:block;width:100%;background:#222;border-radius:8px}}figcaption{{padding:8px 0}}pre{{white-space:pre-wrap;background:#1b2227;padding:16px;border-radius:8px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}</style></head>
<body><main><h1>{escape(profile_id)} technical comparison</h1><p class=\"notice\">Technical evidence only. This page does not grant visual approval.</p>
<div class=\"grid\"><figure><img src=\"{escape(str(baseline_relative))}\" alt=\"Baseline fixed-camera render\"><figcaption>Baseline</figcaption></figure><figure><img src=\"{escape(str(candidate_relative))}\" alt=\"Candidate fixed-camera render\"><figcaption>Candidate</figcaption></figure></div>
<h2>Machine facts</h2><pre>{facts_json}</pre></main></body></html>\n"""
    path.write_text(html)


def compare_artifacts(
    resolved: ResolvedProfile,
    baseline_path: Path,
    candidate_path: Path,
    *,
    baseline_render: dict[str, Any],
    candidate_render: dict[str, Any],
    run_id: str,
    source: dict[str, Any],
    review_path: Path,
) -> dict[str, Any]:
    baseline = Glb(baseline_path)
    candidate = Glb(candidate_path)
    accessor_contract = validate_animation_contract(candidate, resolved.rig, resolved.motion)
    difference = artifact_difference(
        baseline, candidate, resolved.rig, resolved.motion, [layer.data for layer in resolved.layers]
    )
    contact = contact_inheritance_facts(resolved)
    structural = {
        "status": "PASS",
        "jsonEquivalent": difference["jsonEquivalent"],
        "outsideDeclaredByteChanges": difference["outsideDeclaredByteChanges"],
        "changedRotationAccessors": difference["changedRotationAccessors"],
    }
    accessor = {
        "status": "PASS",
        "clips": accessor_contract,
        **resolved.rig["accessorContract"],
    }
    baseline_media = dict(baseline_render["media"])
    candidate_media = dict(candidate_render["media"])
    media = {
        "status": "PASS",
        "baseline": baseline_media,
        "candidate": candidate_media,
        "pixelContentEqual": baseline_media["pixelContentSha256"]
        == candidate_media["pixelContentSha256"],
    }
    core = {
        "schema": "eonwild.motion.comparison-report.v1",
        "status": "PASS",
        "runId": run_id,
        "profile": {
            "id": resolved.profile["id"],
            "sha256": resolved.profile_sha256,
            "lockSha256": resolved.lock_sha256,
        },
        "source": {"gitHead": source["gitHead"]},
        "baseline": _artifact(baseline_path),
        "candidate": _artifact(candidate_path),
        "structural": structural,
        "accessor": accessor,
        "staticFacts": {
            "status": "PASS",
            "fullBodyFixedCamera": True,
            "sameRenderSet": baseline_render["renderSet"] == candidate_render["renderSet"],
        },
        "contactFacts": contact,
        "media": media,
    }
    _write_review(
        review_path,
        profile_id=resolved.profile["id"],
        baseline=baseline_media,
        candidate=candidate_media,
        facts=core,
    )
    return {
        **core,
        "review": {
            "path": str(review_path),
            "sha256": sha256_file(review_path),
            "browsable": True,
            "visualApproval": False,
        },
    }
