/** Distance-driven gait phase for Eonwild procedural clips.
 *
 * Use this for the in-place clip. Advancing phase from distance rather than wall-clock
 * keeps the authored contact plan synchronized with actual creature translation.
 */
export interface GaitClockConfig {
  stridePerCycleMeters: number;
  cycleCountInClip: number;
  minimumSpeedMetersPerSecond?: number;
}

export interface GaitClockState {
  unwrappedCycles: number;
  normalizedClipTime: number;
  cyclePhase: number;
}

const positiveModulo = (value: number, divisor: number): number =>
  ((value % divisor) + divisor) % divisor;

export class DistanceGaitClock {
  private traveledMeters = 0;

  public constructor(private readonly config: GaitClockConfig) {
    if (!(config.stridePerCycleMeters > 0)) {
      throw new Error("stridePerCycleMeters must be positive");
    }
    if (!Number.isInteger(config.cycleCountInClip) || config.cycleCountInClip < 1) {
      throw new Error("cycleCountInClip must be a positive integer");
    }
  }

  public reset(cyclePhase = 0): void {
    this.traveledMeters = positiveModulo(cyclePhase, 1) * this.config.stridePerCycleMeters;
  }

  public advance(signedDistanceMeters: number): GaitClockState {
    if (!Number.isFinite(signedDistanceMeters)) {
      throw new Error("signedDistanceMeters must be finite");
    }
    this.traveledMeters += signedDistanceMeters;
    const unwrappedCycles = this.traveledMeters / this.config.stridePerCycleMeters;
    const cyclePhase = positiveModulo(unwrappedCycles, 1);
    const clipCycles = positiveModulo(unwrappedCycles, this.config.cycleCountInClip);
    return {
      unwrappedCycles,
      cyclePhase,
      normalizedClipTime: clipCycles / this.config.cycleCountInClip,
    };
  }
}
