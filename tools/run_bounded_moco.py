#!/usr/bin/env python3
"""Run one optional solve with durable timing/exit evidence and a wall-time cap."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--seconds',type=int,required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
a.directory.mkdir(parents=True,exist_ok=True)
if (a.directory/'process.json').exists():raise FileExistsError('Never overwrite a supervised run')
start=time.time();env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONPATH='src')
with (a.directory/'console.log').open('w') as log:
 child=subprocess.Popen(a.command,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 receipt=dict(command=a.command,pid=child.pid,started_unix=start,deadline_unix=start+a.seconds,status='RUNNING',cwd=os.getcwd())
 (a.directory/'process.json').write_text(json.dumps(receipt,indent=2)+'\n')
 try:
  code=child.wait(timeout=a.seconds);receipt.update(status='EXITED',exit_code=code)
 except subprocess.TimeoutExpired:
  receipt.update(status='TIME_BUDGET_EXCEEDED')
  os.killpg(child.pid,signal.SIGINT)
  try:child.wait(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=15)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  receipt['exit_code']=child.returncode
receipt.update(finished_unix=time.time(),elapsed_seconds=time.time()-start)
(a.directory/'process.json').write_text(json.dumps(receipt,indent=2)+'\n')
