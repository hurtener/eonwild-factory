#!/usr/bin/env python3
"""Status of finite Moco solves in a research directory: alive or dead, iteration, violation, age.

A run whose process is gone without a finished receipt is reported DEAD, so an externally killed
solve (C66: both probes killed at 10:53 with no exit line) is noticed at the next check, not hours later.
usage: moco_run_status.py <research dir>
"""
import json, os, sys, time
from pathlib import Path
from moco_iterates import best_dump, iteration_log


def alive(pid):
    try: os.kill(pid, 0); return True
    except (ProcessLookupError, TypeError): return False
    except PermissionError: return True


def main(root):
    for receipt_path in sorted(Path(root).glob('*/solve-receipt.json')):
        run = receipt_path.parent; r = json.loads(receipt_path.read_text()); out = run.with_suffix(run.suffix + '.out')
        if not out.exists(): out = Path(str(run) + '.out')
        log = iteration_log(out) if out.exists() else {}
        last = max(log) if log else None; age = time.time() - out.stat().st_mtime if out.exists() else None
        if 'finished_unix' in r: state = 'CONVERGED' if r.get('success') else f"ENDED {r.get('status')}"
        elif alive(r.get('pid')): state = 'RUNNING'
        else: state = 'DEAD (no exit recorded)'
        best = best_dump(run, out) if out.exists() else None
        print(f"{run.name:34s} {state:28s} it {last!s:>5} inf {log[last][1] if last is not None else float('nan'):9.2e}"
              f" best-saved {('%d@%.1e' % (best[0], best[2])) if best else '-':>12} updated {age/60 if age else float('nan'):6.1f} min ago")


if __name__ == '__main__':
    main(sys.argv[1])
