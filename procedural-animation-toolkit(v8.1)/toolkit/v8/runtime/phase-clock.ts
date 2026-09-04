/** Distance-driven gait phase. It avoids speed/animation drift when frame rate changes. */
export class DistancePhaseClock {
  private phaseCycles = 0;
  private travelledMetres = 0;

  constructor(
    readonly strideMetres: number,
    readonly leftContactPhase = 0,
    readonly rightContactPhase = 0.5,
  ) {
    if (!(strideMetres > 0)) throw new Error("strideMetres must be positive");
  }

  reset(phaseCycles = 0): void {
    this.phaseCycles = phaseCycles;
    this.travelledMetres = phaseCycles * this.strideMetres;
  }

  advanceDistance(deltaMetres: number): number {
    this.travelledMetres += deltaMetres;
    this.phaseCycles = this.travelledMetres / this.strideMetres;
    return this.phase();
  }

  advanceSpeed(speedMps: number, dtSeconds: number): number {
    return this.advanceDistance(speedMps * dtSeconds);
  }

  phase(): number {
    return ((this.phaseCycles % 1) + 1) % 1;
  }

  cycles(): number {
    return this.phaseCycles;
  }

  /** True only when a contact marker was crossed between two absolute cycle values. */
  crossedContact(previousCycles: number, currentCycles: number, side: "left" | "right"): boolean {
    const marker = side === "left" ? this.leftContactPhase : this.rightContactPhase;
    const a = Math.floor(previousCycles - marker);
    const b = Math.floor(currentCycles - marker);
    return b > a;
  }
}

export function phaseDistance(a: number, b: number): number {
  const d = Math.abs((((a - b) % 1) + 1) % 1);
  return Math.min(d, 1 - d);
}
