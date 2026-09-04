import type { TerrainProvider, TerrainSample, Vec3 } from "./types";

const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a: Vec3, s: number): Vec3 => [a[0] * s, a[1] * s, a[2] * s];
const norm = (a: Vec3): Vec3 => {
  const n = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / n, a[1] / n, a[2] / n];
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const expAlpha = (dt: number, halfLife: number) => 1 - Math.pow(0.5, dt / Math.max(halfLife, 1e-5));

export interface FootProbe {
  worldPosition: Vec3;
  load: number;
  phase: number;
}

export interface ContactCorrection {
  verticalOffset: number;
  normal: Vec3;
  planted: boolean;
  penetration: number;
}

/** Runtime residual correction layered over the authored terrain clips.
 * The offline V4 pack contains full contact solves; this adapter only removes
 * low-amplitude differences between authored terrain and live browser terrain.
 */
export class TerrainContactAdapter {
  private filteredRootHeight = 0;
  private filteredNormal: Vec3 = [0, 1, 0];
  private initialized = false;

  constructor(
    readonly terrain: TerrainProvider,
    readonly rootHalfLifeSeconds = 0.10,
    readonly normalHalfLifeSeconds = 0.12,
    readonly maxFootCorrectionMetres = 0.055,
  ) {}

  sampleRoot(position: Vec3, dtSeconds: number): TerrainSample {
    const raw = this.terrain.sample(position[0], position[2]);
    if (!this.initialized) {
      this.filteredRootHeight = raw.height;
      this.filteredNormal = norm(raw.normal);
      this.initialized = true;
    }
    const ah = expAlpha(dtSeconds, this.rootHalfLifeSeconds);
    const an = expAlpha(dtSeconds, this.normalHalfLifeSeconds);
    this.filteredRootHeight = lerp(this.filteredRootHeight, raw.height, ah);
    this.filteredNormal = norm(add(mul(this.filteredNormal, 1 - an), mul(norm(raw.normal), an)));
    return { ...raw, height: this.filteredRootHeight, normal: this.filteredNormal };
  }

  footCorrection(probe: FootProbe): ContactCorrection {
    const sample = this.terrain.sample(probe.worldPosition[0], probe.worldPosition[2]);
    const signed = probe.worldPosition[1] - sample.height;
    const planted = probe.load > 0.38;
    const desired = planted ? -signed : Math.max(0, -signed);
    const authority = planted ? Math.min(1, (probe.load - 0.38) / 0.42) : 0.35;
    const verticalOffset = Math.max(-this.maxFootCorrectionMetres, Math.min(this.maxFootCorrectionMetres, desired * authority));
    return {
      verticalOffset,
      normal: norm(sample.normal),
      planted,
      penetration: Math.max(0, -signed),
    };
  }
}
