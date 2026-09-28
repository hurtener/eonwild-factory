#!/usr/bin/env python3
"""Finite-horizon Moco optimization of a behaviour take (dynamics in the loop).

Seeds from a kinematic take (model.osim + solution.sto written by
sequence_moco_behavior.py) and solves the same model with explicit multibody
dynamics, contact, bounded torque actuators and activation dynamics. The take
is a soft reference (intent), not a constraint: the optimizer may change the
motion wherever physics requires. Root residuals are explicit diagnostics with
a heavy cost; their use is reported. A non-converged result stays a failure.
"""
import argparse,hashlib,json,math,os,subprocess,time
from pathlib import Path
import numpy as np

ROOT=('pitch','yaw','roll','forward','height','lateral')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--take',type=Path,required=True,help='directory with model.osim, solution.sto, model-receipt.json')
    ap.add_argument('--start',type=float,required=True);ap.add_argument('--end',type=float,required=True)
    ap.add_argument('--mesh',type=int,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--effort-weight',type=float,default=1.);ap.add_argument('--tracking-weight',type=float,default=10.)
    ap.add_argument('--root-tracking-scale',type=float,default=10.)
    ap.add_argument('--residual-weight',type=float,default=1000.);ap.add_argument('--residual-bound',type=float,default=.25)
    ap.add_argument('--max-iterations',type=int,default=3000);ap.add_argument('--tolerance',type=float,default=1e-3)
    ap.add_argument('--parallel',type=int,default=os.cpu_count());ap.add_argument('--output-interval',type=int,default=50)
    ap.add_argument('--build-only',action='store_true')
    ap.add_argument('--guess',type=Path,help='previous solution.sto of this same problem (mesh continuation)')
    a=ap.parse_args()
    import opensim as o
    a.output.mkdir(parents=True,exist_ok=False)
    o.Logger.removeFileSink();o.Logger.addFileSink(str(a.output/'opensim.log'))
    meta=json.loads((a.take/'model-receipt.json').read_text())
    model=o.Model(str(a.take/'model.osim'))
    L=sum(meta['segment_lengths_m']);bw=meta['mass_kg']*9.80665
    # Diagnostic root residuals: explicit, heavily penalized, reported.
    residuals=[]
    for n in ROOT:
        act=o.CoordinateActuator(n);act.setName('residual_'+n)
        act.setOptimalForce(bw*L if n in ('pitch','yaw','roll') else bw)
        act.setMinControl(-a.residual_bound);act.setMaxControl(a.residual_bound)
        model.addForce(act);residuals.append('/forceset/residual_'+n)
    model.finalizeConnections();model.initSystem()
    duration=a.end-a.start
    # Reference and guess from the take, shifted to start at 0.
    table=o.TimeSeriesTable(str(a.take/'solution.sto'))
    labels=list(table.getColumnLabels());times=np.array(table.getIndependentColumn())
    data=np.array([[table.getRowAtIndex(i)[j] for j in range(len(labels))] for i in range(table.getNumRows())])
    keep=(times>=a.start-1e-9)&(times<=a.end+1e-9)
    ref_t=times[keep]-a.start;ref=data[keep]
    col={l:j for j,l in enumerate(labels)}
    def at(name,t):return float(np.interp(t,ref_t,ref[:,col[name]]))
    def vec(x):
        v=o.Vector(len(x),0)
        for i,y in enumerate(x):v[i]=float(y)
        return v
    values=[l for l in labels if l.endswith('/value')]
    tracking=o.TimeSeriesTable(o.StdVectorDouble(list(map(float,ref_t))))
    for l in values:tracking.appendColumn(l,vec(ref[:,col[l]]))
    tracking.addTableMetaDataString('inDegrees','no')
    o.STOFileAdapter.write(tracking,str(a.output/'intent-reference.sto'))

    study=o.MocoStudy();study.setName('finite_behaviour');problem=study.updProblem()
    problem.setModelAsCopy(model);problem.setTimeBounds(0,duration)
    for name,info in meta['coordinates'].items():
        path=f"/jointset/{info.get('joint',name)}/{name}/value";lo,hi=info['bounds_rad']
        v0=float(np.clip(at(path,0),lo+1e-6,hi-1e-6));problem.setStateInfo(path,[lo,hi],[v0,v0])
    for n in ROOT:
        path=f'/jointset/root/{n}/value';v=ref[:,col[path]]
        span=(.6 if n in ('pitch','yaw','roll') else .5*L)
        problem.setStateInfo(path,[float(v.min()-span),float(v.max()+span)],[at(path,0)]*2)
    for l in labels:
        if l.endswith('/speed'):
            root=l.split('/')[2]=='root';lim=(3. if root and l.split('/')[3] in ('forward','height','lateral') else 20.)
            final=[-.05,.05] if root else []
            if final:problem.setStateInfo(l,[-lim,lim],[at(l,0)]*2,final)
            else:problem.setStateInfo(l,[-lim,lim],[at(l,0)]*2)
    problem.setStateInfoPattern('.*/activation',[-1,1])
    effort=o.MocoControlGoal('effort',a.effort_weight)
    for r in residuals:effort.setWeightForControl(r,a.residual_weight)
    problem.addGoal(effort)
    track=o.MocoStateTrackingGoal('intent',a.tracking_weight)
    track.setReference(o.TableProcessor(str(a.output/'intent-reference.sto')))
    track.setAllowUnusedReferences(True)
    for l in values:
        if l.split('/')[2]=='root':track.setWeightForState(l,a.root_tracking_scale)
    problem.addGoal(track)
    solver=study.initCasADiSolver()
    solver.set_num_mesh_intervals(a.mesh);solver.set_multibody_dynamics_mode('explicit')
    solver.set_optim_max_iterations(a.max_iterations)
    solver.set_optim_convergence_tolerance(a.tolerance);solver.set_optim_constraint_tolerance(a.tolerance)
    solver.set_scale_variables_using_bounds(True)
    # Dense per-point derivatives: random sparsity sampling missed contact
    # dependencies and diverged in the C66 benchmark.
    solver.set_optim_sparsity_detection('none');solver.set_optim_finite_difference_scheme('central')
    solver.set_enforce_path_constraint_mesh_interior_points(True)
    solver.set_parallel(a.parallel);solver.set_optim_ipopt_print_level(5);solver.set_output_interval(a.output_interval)
    guess=solver.createGuess();gt=np.array(guess.getTimeMat())
    for n in guess.getStateNames():
        guess.setState(n,vec(np.clip(np.interp(gt,ref_t,ref[:,col[n]]),-1,1) if n.endswith('/activation') else np.interp(gt,ref_t,ref[:,col[n]])) if n in col else vec(np.zeros_like(gt)))
    for n in guess.getControlNames():
        guess.setControl(n,vec(np.clip(np.interp(gt,ref_t,ref[:,col[n]]),-1,1)) if n in col else vec(np.zeros_like(gt)))
    if a.guess:
        # Mesh continuation: the coarser optimum, resampled; not the take.
        guess=o.MocoTrajectory(str(a.guess));guess.resample(solver.createGuess().getTime())
    solver.setGuess(guess);guess.write(str(a.output/'initial-guess.sto'))
    study.printToXML(str(a.output/'study.omoco'))
    source=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,cwd=Path(__file__).parent).stdout.strip()
    receipt=dict(schema='eonwild.motion.moco-finite-solve.v1',take=str(a.take),window_s=[a.start,a.end],mesh_intervals=a.mesh,
        arguments={k:(str(v) if isinstance(v,Path) else v) for k,v in vars(a).items()},source_commit=source,
        model_sha256=hashlib.sha256((a.take/'model.osim').read_bytes()).hexdigest(),
        classification='Direct-collocation optimization with explicit multibody dynamics, contact and bounded torque actuators; soft tracking of the kinematic take as intent',
        pid=os.getpid(),started_unix=time.time())
    (a.output/'solve-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if a.build_only:return
    os.chdir(a.output)
    solution=study.solve();success=bool(solution.success())
    if solution.isSealed():solution.unseal()
    solution.write(str(a.output/'solution.sto'))
    res={r:float(np.abs(np.asarray(solution.getControlMat(r))).max()) for r in residuals}
    receipt.update(finished_unix=time.time(),success=success,status=solution.getStatus(),iterations=solution.getNumIterations(),
        objective=solution.getObjective(),max_residual_control=res,
        claim=('Converged discretized optimum; physical replay and mesh refinement are separate checks' if success else 'NOT CONVERGED: do not present as physical motion'))
    (a.output/'solve-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('success','status','iterations','objective','max_residual_control')}),flush=True)
    if not success:raise SystemExit(2)


if __name__=='__main__':main()
