#!/usr/bin/env python3
"""Render docs/ANIMATION_CATALOG.md from motions/tarbosaurus/catalog.yaml."""
from __future__ import annotations

import argparse
from pathlib import Path
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = yaml.safe_load((root / "motions/tarbosaurus/catalog.yaml").read_text(encoding="utf-8"))
    animations = catalog["animations"]

    lines: list[str] = []
    lines.append("# Tarbosaurus V9 animation catalog\n")
    lines.append("Status: **implementation specification**, not an approved V9 animation release.\n")
    lines.append("The 29 animation contracts remain semantically independent while sharing 12 reusable motion programs. Each contract defines entry/exit state, performance, support/COM/dynamics, complete phase progression, events, procedural authority, growth response, and release-blocking validation.\n")
    lines.append("## Index\n")
    lines.append("| # | Animation | Program | Priority | Loop | Root motion | Target duration |")
    lines.append("|---:|---|---|---|:---:|:---:|---:|")
    for animation in animations:
        lines.append(
            f"| {animation['number']} | {animation['display_name']} | `{animation['program']}` | "
            f"{animation['priority']} | {'yes' if animation['loop'] else 'no'} | "
            f"{'yes' if animation['root_motion'] else 'no'} | {animation['duration_s']['target']:.2f}s |"
        )
    lines.append("\n## Detailed contracts\n")

    for animation in animations:
        lines.append(f"## {animation['number']:02d} — {animation['display_name']}\n")
        lines.append(
            f"**ID:** `{animation['id']}`  \n"
            f"**Program:** `{animation['program']}`  \n"
            f"**Category / priority:** `{animation['category']}` / `{animation['priority']}`  \n"
            f"**Duration envelope:** {animation['duration_s']['min']}–{animation['duration_s']['max']} s; "
            f"target {animation['duration_s']['target']} s  \n"
            f"**Loop / root motion:** {animation['loop']} / {animation['root_motion']}\n"
        )
        lines.append(f"**Purpose.** {animation['purpose']}\n")
        lines.append(f"**Performance character.** {animation['performance']['character']}\n")
        lines.append("### Entry and exit\n")
        lines.append("```yaml")
        lines.append(yaml.safe_dump({"entry": animation["entry"], "exit": animation["exit"]}, sort_keys=False, width=100).rstrip())
        lines.append("```\n")
        lines.append("### Phase progression\n")
        for phase in animation["phases"]:
            lines.append(f"#### `{phase['id']}` — {phase['range'][0]:.2f}–{phase['range'][1]:.2f}")
            lines.append(
                f"**Goal:** {phase['goal']}  \n"
                f"**Support:** {phase['support']}  \n"
                f"**COM:** {phase['com']}  \n"
                f"**Dynamics:** {phase['dynamics']}  \n"
                f"**Interruptibility:** `{phase['interruptibility']}`"
            )
            lines.append("")
            for key, value in phase["body"].items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            lines.append("")
        lines.append("### Events\n")
        lines.append("```yaml")
        lines.append(yaml.safe_dump(animation["events"], sort_keys=False, width=100).rstrip())
        lines.append("```\n")
        lines.append("### Procedural channels\n")
        lines.append("```yaml")
        lines.append(yaml.safe_dump(animation["procedural_channels"], sort_keys=False, width=100).rstrip())
        lines.append("```\n")
        lines.append("### Growth response\n")
        for tier, description in animation["growth_response"].items():
            lines.append(f"- **{tier.replace('_', ' ').title()}:** {description}")
        lines.append("\n### Reject / release-blocking checks\n")
        for check in animation["validation"]["animation_specific"]:
            lines.append(f"- {check}")
        if animation.get("branches"):
            lines.append("\n### Branches\n")
            for branch in animation["branches"]:
                lines.append(f"- `{branch}`")
        lines.append("\n---\n")

    output = root / "docs/ANIMATION_CATALOG.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {output} ({len(animations)} animations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
