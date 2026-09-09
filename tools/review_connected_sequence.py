"""Render immutable start -> steady cycles -> stop review films and receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
from connected_schedule import build_connected_schedule


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=Path, required=True)
    parser.add_argument('--steady', type=Path, required=True)
    parser.add_argument('--stop', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cycles', type=int, default=2)
    parser.add_argument('--views', nargs='+', choices=('side', 'three-quarter'),
                        default=['side', 'three-quarter'])
    parser.add_argument('--modes', nargs='+', choices=('root_motion', 'in_place'),
                        default=['root_motion', 'in_place'])
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--samples', type=int, default=8)
    parser.add_argument('--blender', default='blender')
    args = parser.parse_args(argv)
    if (len(set(args.views)) != len(args.views) or len(set(args.modes)) != len(args.modes)
            or not 12 <= args.fps <= 120 or not 320 <= args.width <= 3840
            or not 1 <= args.samples <= 256):
        parser.error('connected review needs unique views/modes and supported render settings')
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
               'schedule': schedule, 'renders': {}, 'render_status': 'PENDING',
               'visual_review': 'PENDING', 'unity_validation': 'NOT_RUN'}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    root = Path(__file__).resolve().parents[1]
    ok = True
    for mode in args.modes:
        receipt['renders'][mode] = {}
        for view in args.views:
            target = output / mode / view
            command = [args.blender, '-b', '-t', '2', '--python-exit-code', '1', '--python',
                       str(root / 'tools/render_connected_sequence.py'), '--',
                       '--schedule', str(output / 'schedule.json'), '--output', str(target),
                       '--view', view, '--mode', mode, '--fps', str(args.fps),
                       '--width', str(args.width), '--samples', str(args.samples)]
            target.parent.mkdir(parents=True, exist_ok=True)
            log_path = target.with_suffix('.render.log')
            try:
                process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         text=True, timeout=3600)
                log_path.write_text(process.stdout)
                row = {'status': 'PASS' if process.returncode == 0 else 'FAIL',
                       'exit_code': process.returncode, 'log': str(log_path),
                       'mode': mode, 'view': view}
                if process.returncode == 0:
                    row['receipt'] = json.loads((target / 'render-receipt.json').read_text())
                else:
                    row['error_tail'] = process.stdout[-5000:]
                    ok = False
            except Exception as exc:
                log_path.write_text(traceback.format_exc())
                row = {'status': 'FAIL', 'error': str(exc), 'log': str(log_path),
                       'mode': mode, 'view': view}
                ok = False
            receipt['renders'][mode][view] = row
            (output / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    receipt['render_status'] = 'PASS' if ok else 'FAIL'
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(receipt, allow_nan=False))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
