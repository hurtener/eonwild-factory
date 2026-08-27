import type { AnimationBackend, AnimationHandle, Vec3 } from "./types";

/** Minimal structural interfaces avoid forcing one Babylon version into the toolkit. */
interface BabylonAnimatable {
  name: string;
  from: number;
  to: number;
  speedRatio: number;
  isPlaying: boolean;
  weight: number;
  play(loop?: boolean): void;
  stop(): void;
  goToFrame(frame: number): void;
  setWeightForAllAnimatables(weight: number): void;
}
interface BabylonNode {
  position: { x: number; y: number; z: number };
  rotation: { y: number };
}

class BabylonAnimationHandle implements AnimationHandle {
  constructor(private readonly group: BabylonAnimatable, readonly durationSeconds: number, readonly fps: number) {}
  get name(): string { return this.group.name; }
  get loop(): boolean { return true; }
  get playing(): boolean { return this.group.isPlaying; }
  play(loop = true): void { this.group.play(loop); }
  stop(): void { this.group.stop(); }
  setWeight(weight: number): void { this.group.setWeightForAllAnimatables(weight); }
  seekNormalized(phase: number): void {
    const p = ((phase % 1) + 1) % 1;
    this.group.goToFrame(this.group.from + (this.group.to - this.group.from) * p);
  }
  normalizedTime(): number { return 0; }
}

export class BabylonV4Backend implements AnimationBackend {
  private readonly handles = new Map<string, AnimationHandle>();
  constructor(
    private readonly root: BabylonNode,
    groups: BabylonAnimatable[],
    sampleHz = 60,
  ) {
    for (const group of groups) {
      const duration = Math.max(0, (group.to - group.from) / sampleHz);
      this.handles.set(group.name, new BabylonAnimationHandle(group, duration, sampleHz));
    }
  }
  getClip(name: string): AnimationHandle {
    const clip = this.handles.get(name);
    if (!clip) throw new Error(`AnimationGroup not found: ${name}`);
    return clip;
  }
  setActorTranslation(position: Vec3): void { [this.root.position.x, this.root.position.y, this.root.position.z] = position; }
  setActorYaw(radians: number): void { this.root.rotation.y = radians; }
  actorTranslation(): Vec3 { return [this.root.position.x, this.root.position.y, this.root.position.z]; }
  actorYaw(): number { return this.root.rotation.y; }
}
