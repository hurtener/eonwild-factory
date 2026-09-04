/** Eonwild V8 runtime contracts: contact-safe transition queues and root-loop accumulation. */
export interface V8ClipMeta {
  name: string;
  durationSeconds: number;
  loop: boolean;
  rootMotion: boolean;
  transition?: boolean;
  sourceClip?: string;
  targetClip?: string;
  sourcePhase?: number;
  targetPhase?: number;
  exactRuntimeHandoff?: boolean;
}

export interface RootCycle {
  start: readonly [number, number, number];
  end: readonly [number, number, number];
}

export function accumulatedRootTranslation(
  local: readonly [number, number, number],
  elapsedSeconds: number,
  durationSeconds: number,
  cycle: RootCycle,
): [number, number, number] {
  if (!(durationSeconds > 0) || !(elapsedSeconds > 0)) return [...local];
  const cycles = Math.floor(elapsedSeconds / durationSeconds);
  return [
    local[0] + (cycle.end[0] - cycle.start[0]) * cycles,
    local[1] + (cycle.end[1] - cycle.start[1]) * cycles,
    local[2] + (cycle.end[2] - cycle.start[2]) * cycles,
  ];
}

export function secondsUntilPhase(
  elapsedSeconds: number,
  durationSeconds: number,
  targetPhase: number,
): number {
  if (!(durationSeconds > 0)) return 0;
  const phase = ((elapsedSeconds / durationSeconds) % 1 + 1) % 1;
  const delta = ((targetPhase - phase) % 1 + 1) % 1;
  return delta * durationSeconds;
}

export function mustUseExactHandoff(clip: V8ClipMeta): boolean {
  return clip.transition === true && clip.exactRuntimeHandoff === true;
}
