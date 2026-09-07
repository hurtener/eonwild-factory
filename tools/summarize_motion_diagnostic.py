"""Compact read-only summaries of native motion diagnostics (not acceptance)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def failures(value, path=''):
    rows = []
    if isinstance(value, dict):
        if value.get('status') in ('FAIL', 'ERROR') or value.get('verdict') == 'FAIL':
            rows.append({'path': path, **{k:v for k,v in value.items() if k in ('reason','reasons','checks','values','limits','maximum_degrees_per_s','peak_witness')}})
        for key, child in value.items():
            if isinstance(child, dict):
                rows.extend(failures(child, f'{path}.{key}' if path else key))
    return rows


def summarize(report):
    result = {k:v for k,v in report.items() if k in ('error','verification','solver_summary','iteration','refinement_trace')}
    result['failures'] = failures(report.get('validation', {}))
    motion = report.get('motion', {})
    result['artifact_sha256'] = motion.get('sha256')
    result['peaks'] = [{'rate': p['rate_degrees_per_s'], 'node': p['name'],
        'times': [p['before']['time_s'], p['after']['time_s']],
        'legs': [p['before']['legs'], p['after']['legs']]} for p in motion.get('peak_rates', [])[:1]]
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = json.loads(args.report.read_text())
    result = summarize(report)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print('MOTION_SUMMARY '+json.dumps(result, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
