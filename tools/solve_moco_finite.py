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
    ap.add_argument('--dynamics',choices=('explicit','implicit'),default='explicit')
    ap.add_argument('--reserve-weight',type=float,default=0.,help='0 disables joint reserves; otherwise per-control effort weight')
    ap.add_argument('--reserve-bound',type=float,default=1.)
    ap.add_argument('--settle-guess',action='store_true',help='shift each reference frame vertically so contacts carry 1 BW (no buried or floating start)')
    ap.add_argument('--weld',default='',help='comma-separated joints replaced by welds (e.g. light digit joints)')
    a=ap.parse_args()
    import opensim as o
    a.output.mkdir(parents=True,exist_ok=False)
    o.Logger.removeFileSink();o.Logger.addFileSink(str(a.output/'opensim.log'))
    meta=json.loads((a.take/'model-receipt.json').read_text())
    model=o.Model(str(a.take/'model.osim'))
    welded=[j for j in a.weld.split(',') if j]
    if welded:
        # Light distal segments (4 kg digits carrying ~1 BW through pads) make
        # explicit contact dynamics stiff; weld them into the toe and drop
        # their motors/limits/springs. Recorded in the receipt.
        coords=[c for c,v in meta['coordinates'].items() if v.get('joint',c) in welded]
        fs=model.updForceSet()
        for c in coords:
            for f in ('motor_','limit_','passive_'):
                i=fs.getIndex(f+c)
                if i>=0:fs.remove(i)
        proc=o.ModelProcessor(model);names=o.StdVectorString()
        for j in welded:names.append(j)
        proc.append(o.ModOpReplaceJointsWithWelds(names));model=proc.process()
        for c in coords:meta['coordinates'].pop(c);meta['actuators'].pop('motor_'+c,None)
    L=sum(meta['segment_lengths_m']);bw=meta['mass_kg']*9.80665
    # Diagnostic root residuals: explicit, heavily penalized, reported.
    residuals=[]
    for n in ROOT:
        act=o.CoordinateActuator(n);act.setName('residual_'+n)
        act.setOptimalForce(bw*L if n in ('pitch','yaw','roll') else bw)
        act.setMinControl(-a.residual_bound);act.setMaxControl(a.residual_bound)
        model.addForce(act);residuals.append('/forceset/residual_'+n)
    reserves=[]
    if a.reserve_weight:
        # Continuation aid: penalized reserve torque on every joint, sized to
        # the joint's own capacity. Reported; a physical result must not lean
        # on them (final stages use a large weight).
        for c,info in meta['coordinates'].items():
            if 'motor_'+c not in meta['actuators']:continue
            act=o.CoordinateActuator(c);act.setName('reserve_'+c)
            act.setOptimalForce(meta['actuators']['motor_'+c]['capacity_Nm'])
            act.setMinControl(-a.reserve_bound);act.setMaxControl(a.reserve_bound)
            model.addForce(act);reserves.append('/forceset/reserve_'+c)
    model.finalizeConnections();model.initSystem()
    duration=a.end-a.start
    # Reference and guess from the take, shifted to start at 0.
    table=o.TimeSeriesTable(str(a.take/'solution.sto'))
    labels=list(table.getColumnLabels());times=np.array(table.getIndependentColumn())
    data=np.array([[table.getRowAtIndex(i)[j] for j in range(len(labels))] for i in range(table.getNumRows())])
    keep=(times>=a.start-1e-9)&(times<=a.end+1e-9)
    ref_t=times[keep]-a.start;ref=data[keep]
    col={l:j for j,l in enumerate(labels)}
    settle_receipt=None
    if a.settle_guess:
        # A kinematic take can bury pads by centimetres (tens of BW with stiff
        # contact) or float the body. Fixing the start to such a state makes
        # the problem infeasible at t=0. Per frame, find the vertical root
        # offset at which total contact force equals body weight; smooth it
        # in time; update height and its speed. Joint angles are unchanged.
        from scipy.optimize import brentq
        from scipy.ndimage import gaussian_filter1d
        st=model.initSystem();names=[model.getStateVariableNames().get(i) for i in range(model.getNumStateVariables())]
        spheres=[f for f in model.getForceSet() if f.getConcreteClassName()=='SmoothSphereHalfSpaceForce']
        hcol=col['/jointset/root/height/value'];offsets=[]
        for k in range(len(ref_t)):
            for n in names:
                if n in col and not n.endswith(('/speed','/activation')):model.setStateVariableValue(st,n,float(ref[k,col[n]]))
                elif n.endswith('/speed'):model.setStateVariableValue(st,n,0.)
            h0=ref[k,hcol]
            def load(dy):
                model.setStateVariableValue(st,'/jointset/root/height/value',float(h0+dy));model.realizeDynamics(st)
                return sum(f.getRecordValues(st).get(1) for f in spheres)-bw
            try:offsets.append(brentq(load,-.25,.25,xtol=1e-5))
            except ValueError:offsets.append(np.nan)
        offsets=np.array(offsets);ok=np.isfinite(offsets)
        offsets=np.interp(np.arange(len(offsets)),np.flatnonzero(ok),offsets[ok])
        offsets=gaussian_filter1d(offsets,max(1,.08/np.median(np.diff(ref_t))),mode='nearest')
        ref=ref.copy();ref[:,hcol]+=offsets
        sc=col.get('/jointset/root/height/speed')
        if sc is not None:ref[:,sc]=np.gradient(ref[:,hcol],ref_t)
        settle_receipt=dict(offset_m_min=float(offsets.min()),offset_m_max=float(offsets.max()),unsolved_frames=int((~ok).sum()))
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
    states=set(model.getStateVariableNames().get(i) for i in range(model.getNumStateVariables()))
    for l in labels:
        if l.endswith('/speed') and l in states:
            root=l.split('/')[2]=='root';lim=(3. if root and l.split('/')[3] in ('forward','height','lateral') else 20.)
            final=[-.05,.05] if root else []
            if final:problem.setStateInfo(l,[-lim,lim],[at(l,0)]*2,final)
            else:problem.setStateInfo(l,[-lim,lim],[at(l,0)]*2)
    problem.setStateInfoPattern('.*/activation',[-1,1])
    effort=o.MocoControlGoal('effort',a.effort_weight)
    for r in residuals:effort.setWeightForControl(r,a.residual_weight)
    for r in reserves:effort.setWeightForControl(r,a.reserve_weight)
    problem.addGoal(effort)
    track=o.MocoStateTrackingGoal('intent',a.tracking_weight)
    track.setReference(o.TableProcessor(str(a.output/'intent-reference.sto')))
    track.setAllowUnusedReferences(True)
    for l in values:
        if l.split('/')[2]=='root':track.setWeightForState(l,a.root_tracking_scale)
    problem.addGoal(track)
    solver=study.initCasADiSolver()
    solver.set_num_mesh_intervals(a.mesh);solver.set_multibody_dynamics_mode(a.dynamics)
    if a.dynamics=='implicit':
        solver.set_minimize_implicit_multibody_accelerations(True);solver.set_implicit_multibody_accelerations_weight(1e-3)
        solver.set_implicit_multibody_acceleration_bounds(o.MocoBounds(-500,500))
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
    for n in guess.getDerivativeNames():
        # Implicit mode: accelerations from the reference speeds, not zeros.
        sp=n.removesuffix('/accel')+'/speed'
        guess.setDerivative(n,vec(np.clip(np.gradient(np.interp(gt,ref_t,ref[:,col[sp]]),gt),-500,500)) if sp in col else vec(np.zeros_like(gt)))
    if a.guess:
        # Mesh continuation: the coarser optimum, resampled; not the take.
        # Keep the template alive and copy its times: getTime() on a temporary returned a dangling
        # reference, and resample() segfaulted (exit 139) the first time a stage was warm-started.
        template=solver.createGuess();times=o.Vector(template.getTime())
        guess=o.MocoTrajectory(str(a.guess));guess.resample(times)
    solver.setGuess(guess);guess.write(str(a.output/'initial-guess.sto'))
    study.printToXML(str(a.output/'study.omoco'))
    source=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,cwd=Path(__file__).parent).stdout.strip()
    receipt=dict(schema='eonwild.motion.moco-finite-solve.v1',take=str(a.take),window_s=[a.start,a.end],mesh_intervals=a.mesh,
        arguments={k:(str(v) if isinstance(v,Path) else v) for k,v in vars(a).items()},source_commit=source,
        model_sha256=hashlib.sha256((a.take/'model.osim').read_bytes()).hexdigest(),
        classification='Direct-collocation optimization with explicit multibody dynamics, contact and bounded torque actuators; soft tracking of the kinematic take as intent',
        pid=os.getpid(),started_unix=time.time(),guess_settle=settle_receipt)
    (a.output/'solve-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if a.build_only:return
    os.chdir(a.output)
    solution=study.solve();success=bool(solution.success())
    if solution.isSealed():solution.unseal()
    solution.write(str(a.output/'solution.sto'))
    res={r:float(np.abs(np.asarray(solution.getControlMat(r))).max()) for r in residuals+reserves}
    receipt.update(finished_unix=time.time(),success=success,status=solution.getStatus(),iterations=solution.getNumIterations(),
        objective=solution.getObjective(),max_residual_control=res,
        claim=('Converged discretized optimum; physical replay and mesh refinement are separate checks' if success else 'NOT CONVERGED: do not present as physical motion'))
    (a.output/'solve-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('success','status','iterations','objective','max_residual_control')}),flush=True)
    if not success:raise SystemExit(2)


if __name__=='__main__':main()
