import type { AnimationBackend, AnimationManifestV4, MotionState, RuntimeInput } from "./types";
import { DistancePhaseClock } from "./phase-clock";
import { ActionController } from "./action-controller";

export interface MotionGraphConfig {
  strideMetres: number;
  walkSpeedMps: number;
  startThresholdMps?: number;
  stopThresholdMps?: number;
  turnThresholdRadS?: number;
}

/** Deterministic browser motion graph for V4. Animation time is phase driven,
 * not wall-clock driven, so locomotion remains synchronized with actor travel.
 */
export class MotionGraphV4 {
  private state: MotionState = "idle";
  private activeClipName = "PROC_IDLE_BREATH_V4";
  private phaseClock: DistancePhaseClock;
  private actions: ActionController;
  private speedMps = 0;

  constructor(
    private readonly backend: AnimationBackend,
    readonly manifest: AnimationManifestV4,
    readonly config: MotionGraphConfig,
  ) {
    this.phaseClock = new DistancePhaseClock(config.strideMetres);
    this.actions = new ActionController(backend);
    this.play(this.activeClipName, true);
  }

  currentState(): MotionState { return this.state; }
  currentPhase(): number { return this.phaseClock.phase(); }

  private play(name: string, loop: boolean, phase?: number): void {
    if (this.activeClipName === name) return;
    const previous = this.backend.getClip(this.activeClipName);
    const next = this.backend.getClip(name);
    previous.setWeight(0);
    previous.stop();
    if (phase !== undefined) next.seekNormalized(phase);
    next.setWeight(1);
    next.play(loop);
    this.activeClipName = name;
  }

  update(dtSeconds: number, input: RuntimeInput): void {
    if (!(dtSeconds > 0) || dtSeconds > 0.25) return;
    if (input.action) this.actions.request(input.action, this.state as any);
    const returned = this.actions.update(input);
    if (returned) this.state = returned;

    const accelLimit = 0.55;
    const delta = Math.max(-accelLimit * dtSeconds, Math.min(accelLimit * dtSeconds, input.desiredSpeedMps - this.speedMps));
    this.speedMps += delta;
    const phase = this.phaseClock.advanceSpeed(this.speedMps, dtSeconds);

    if (input.action) return;
    const moving = Math.abs(this.speedMps) > (this.config.stopThresholdMps ?? 0.06);
    const turning = Math.abs(input.desiredTurnRateRadS) > (this.config.turnThresholdRadS ?? 0.18);

    if (!moving) {
      const nextState: MotionState = input.alert ? "alertIdle" : "idle";
      const clip = input.alert ? "PROC_ALERT_IDLE_V4" : "PROC_IDLE_BREATH_V4";
      this.state = nextState;
      this.play(clip, true);
      return;
    }

    if (turning) {
      const left = input.desiredTurnRateRadS > 0;
      this.state = left ? "turnLeft" : "turnRight";
      this.play(left ? "PROC_TURN_LEFT_35_V4_INPLACE" : "PROC_TURN_RIGHT_35_V4_INPLACE", false, phase);
      return;
    }

    this.state = input.alert ? "alertWalk" : "walk";
    this.play(input.alert ? "PROC_ALERT_WALK_V4_INPLACE" : "PROC_WALK_RELAXED_V4_INPLACE", true, phase);
    this.backend.getClip(this.activeClipName).seekNormalized(phase);
  }
}
