#!/usr/bin/env python3
"""Fail-closed offline showcase checks."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent / "site"
    html_path = root / "index.html"
    html = html_path.read_text(encoding="utf-8")
    refs = sorted(set(re.findall(r'(?:src|poster)="(media/[^"#]+)"', html)))
    expected = refs + [f"media/films/{name}.mp4" for name in ("idle-breath", "eat-loop", "bite-attack", "roar")]
    missing = sorted(set(ref for ref in expected if not (root / ref).is_file()))
    remote = sorted(set(re.findall(r'https?://[^"\s]+', html)))
    required = {
        "hero_heading": 'id="hero-title"' in html,
        "skip_link": 'href="#study"' in html,
        "reduced_motion": "prefers-reduced-motion" in html,
        "behavior_controls": html.count('data-film=') >= 4,
        "local_only": not remote,
    }
    result = {"status": "passed" if not missing and all(required.values()) else "failed", "references": refs, "missing": missing, "remote_urls": remote, "required": required}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
