"""Write the immutable source schedule consumed by the connected Blender review.

This tool deliberately emits no interpolated motion.  The companion Blender
renderer must render every listed source interval exactly and record its
segment receipt before a film can be considered diagnostic evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from connected_schedule import build_connected_schedule


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=Path, required=True)
    parser.add_argument('--steady', type=Path, required=True)
    parser.add_argument('--stop', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cycles', type=int, default=2)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        parser.error('connected review output must be new')
    schedule = build_connected_schedule(args.start, args.steady, args.stop, cycles=args.cycles)
    output.mkdir(parents=True)
    raw = json.dumps(schedule, indent=2, allow_nan=False) + '\n'
    (output / 'schedule.json').write_text(raw)
    receipt = {'schema': 'eonwild.motion.connected-review-request.v1',
               'schedule_sha256': hashlib.sha256(raw.encode()).hexdigest(),
               'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'schedule': schedule, 'render_status': 'NOT_RUN', 'visual_review': 'PENDING',
               'unity_validation': 'NOT_RUN'}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, allow_nan=False))


if __name__ == '__main__':
    main()
