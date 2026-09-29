#!/usr/bin/env python3
"""Moco intermediate iterate dumps (solver.set_output_interval) are not physical trajectories.

Measured on C66 (OpenSim 4.6, MocoCasADiSolver, Hermite-Simpson): every state column is written at
exactly 0.5x and every control at 0.25x of its value, and the time column is all zeros. Reading them
as physical rendered animals at half height and understated help forces 4x. Always go through
read_iterate(); dump_scale() re-measures the factors against a finished solution.sto so a Moco change
cannot silently return.

usage: moco_iterates.py <solve output dir> [--write <iteration> <out.sto>]
"""
import argparse, glob, json, re
from pathlib import Path
import numpy as np

DEFAULT_SCALE = dict(states=0.5, controls=0.25)


def load(path):
    lines = Path(path).read_text().splitlines()
    end = next(k for k, l in enumerate(lines) if l.startswith('endheader'))
    header, cols = lines[:end + 1], lines[end + 1].split('\t')
    data = np.array([[float(x) for x in r.split('\t')] for r in lines[end + 2:] if r.strip()])
    counts = {k: int(v) for k, v in (l.split('=', 1) for l in header if re.match(r'num_\w+=\d+$', l))}
    return header, cols, data, counts


def _blocks(cols, counts):
    ns, nc = counts.get('num_states', 0), counts.get('num_controls', 0)
    return slice(1, 1 + ns), slice(1 + ns, 1 + ns + nc)


def dumps(run):
    found = {}
    for f in glob.glob(str(Path(run) / '*trajectory[0-9]*.sto')):
        found[int(re.search(r'trajectory(\d+)\.sto$', f).group(1))] = Path(f)
    return dict(sorted(found.items()))


def dump_scale(run, iterations):
    """Fit dump = k * solution per block, using the dump written at the final iteration (the same point as
    solution.sto). None when no dump exists at that iteration."""
    run = Path(run); d = dumps(run)
    if iterations not in d or not (run / 'solution.sto').exists(): return None
    _, sc, s, cnt = load(run / 'solution.sto'); _, dc, x, _ = load(d[iterations])
    if sc != dc or s.shape != x.shape: return dict(error='dump and solution differ in layout')
    out = {}
    for name, block in zip(('states', 'controls'), _blocks(sc, cnt)):
        a, b = s[:, block].ravel(), x[:, block].ravel(); m = np.abs(a) > 1e-6
        if not m.any(): continue
        k = float(np.dot(a[m], b[m]) / np.dot(a[m], a[m]))
        out[name] = round(k, 6); out[name + '_max_fit_error'] = float(np.abs(b[m] - k * a[m]).max())
    return out


def read_iterate(path, duration=None, time_from=None, scale=None):
    """Physical (header, cols, data) for an iterate dump. Times from `time_from` (a solution.sto on the
    same mesh) or a uniform grid over [0, duration]."""
    header, cols, data, counts = load(path); data = data.copy()
    scale = scale or DEFAULT_SCALE; st, ct = _blocks(cols, counts)
    data[:, st] /= scale['states']; data[:, ct] /= scale['controls']
    if time_from is not None:
        _, _, t, _ = load(time_from)
        if len(t) != len(data): raise ValueError('time source has a different number of mesh points')
        data[:, 0] = t[:, 0]
    elif duration is not None:
        data[:, 0] = np.linspace(0, duration, len(data))
    elif not np.any(data[:, 0]):
        raise ValueError('iterate dumps carry no time: pass duration or time_from')
    return header, cols, data


def write(path, header, cols, data):
    body = ['\t'.join(cols)] + ['\t'.join(repr(float(x)) for x in row) for row in data]
    Path(path).write_text('\n'.join(header + body) + '\n')


def iteration_log(out_file):
    """{iteration: (objective, inf_pr)} from the solver's Ipopt log."""
    it = {}
    for line in Path(out_file).read_text().splitlines():
        m = re.match(r'^\s*(\d+)r?\s+(\S+)\s+(\S+)\s', line)
        if m:
            try: it[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
            except ValueError: pass
    return it


def best_dump(run, out_file):
    """The saved iterate with the lowest constraint violation (Ipopt inf_pr)."""
    log = iteration_log(out_file); d = dumps(run)
    ranked = sorted((log[k][1], k) for k in d if k in log)
    return (ranked[0][1], d[ranked[0][1]], ranked[0][0]) if ranked else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('run', type=Path)
    ap.add_argument('--write', nargs=2, metavar=('ITERATION', 'OUT'))
    ap.add_argument('--best-physical', nargs=2, metavar=('OUT', 'MAX_INF'),
                    help='write the saved iterate with the lowest violation, if below MAX_INF (exit 3 otherwise)')
    a = ap.parse_args(); receipt = json.loads((a.run / 'solve-receipt.json').read_text())
    duration = receipt['window_s'][1] - receipt['window_s'][0]
    print('dump scale vs solution:', dump_scale(a.run, receipt.get('iterations')))
    if a.best_physical:
        out_file = Path(str(a.run) + '.out'); best = best_dump(a.run, out_file)
        if best is None or best[2] > float(a.best_physical[1]):
            print('no saved iterate below', a.best_physical[1], best and ('best %d@%.2e' % (best[0], best[2]))); raise SystemExit(3)
        header, cols, data = read_iterate(best[1], duration=duration)
        write(a.best_physical[0], header, cols, data); print('wrote best iterate %d (inf_pr %.2e) -> %s' % (best[0], best[2], a.best_physical[0]))
    if a.write:
        header, cols, data = read_iterate(dumps(a.run)[int(a.write[0])], duration=duration)
        write(a.write[1], header, cols, data); print('wrote physical iterate', a.write[0], '->', a.write[1])


if __name__ == '__main__':
    main()
