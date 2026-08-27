export type Vec3 = readonly [number, number, number];

export interface TerrainSample {
  height: number;
  normal: Vec3;
  friction?: number;
  region?: string;
}

export interface TerrainProvider {
  sample(x: number, z: number): TerrainSample;
}

export type MotionState =
  | "idle"
  | "walk"
  | "start"
  | "stop"
  | "turnLeft"
  | "turnRight"
  | "alertIdle"
  | "alertWalk"
  | "eat"
  | "bite"
  | "roar";

export interface ClipEvent {
  timeSeconds: number;
  type: string;
  side?: "left" | "right";
  phase?: number;
  windowSeconds?: number;
  index?: number;
}

export interface ClipContract {
  name: string;
  durationSeconds: number;
  loop: boolean;
  rootMotion: boolean;
  tags: string[];
  recommendedSpeedMps?: number;
  terrain?: string;
  path?: string;
  events?: ClipEvent[];
}

export interface StateGraphManifest {
  initial: MotionState;
  states: Record<string, { clip: string; speedMps?: number }>;
  oneShots: Record<string, { clip: string; return: string; priority: number }>;
  transitions: Array<{
    from: string;
    to: string;
    clip: string;
    phaseMatched?: boolean;
  }>;
}

export interface AnimationManifestV4 {
  schema: "eonwild.animation-manifest.v4";
  version: string;
  asset: string;
  family: string;
  speciesProfile: string;
  sampleHz: number;
  clips: ClipContract[];
  stateGraph: StateGraphManifest;
  runtimeContracts: Record<string, unknown>;
}

export interface AnimationHandle {
  readonly name: string;
  readonly durationSeconds: number;
  readonly loop: boolean;
  readonly playing: boolean;
  play(loop?: boolean): void;
  stop(): void;
  setWeight(weight: number): void;
  seekNormalized(phase: number): void;
  normalizedTime(): number;
}

export interface AnimationBackend {
  getClip(name: string): AnimationHandle;
  setActorTranslation(position: Vec3): void;
  setActorYaw(radians: number): void;
  actorTranslation(): Vec3;
  actorYaw(): number;
}

export interface RuntimeInput {
  desiredSpeedMps: number;
  desiredTurnRateRadS: number;
  alert: boolean;
  action?: "eat" | "bite" | "roar";
  cancelAction?: boolean;
}
