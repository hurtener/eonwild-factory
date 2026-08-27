import type { ClipContract, ClipEvent } from "./types";

export type ClipEventListener = (event: ClipEvent, clip: ClipContract) => void;

/** Emits manifest-authored contacts, hit windows, vocal peaks and transition commits.
 * It handles looping clips without double-firing the event at t=0/duration.
 */
export class ClipEventDispatcher {
  private previousSeconds = 0;
  private initialized = false;

  constructor(
    private clip: ClipContract,
    private readonly listener: ClipEventListener,
  ) {}

  setClip(clip: ClipContract, currentSeconds = 0): void {
    this.clip = clip;
    this.previousSeconds = Math.max(0, currentSeconds);
    this.initialized = true;
  }

  reset(currentSeconds = 0): void {
    this.previousSeconds = Math.max(0, currentSeconds);
    this.initialized = true;
  }

  update(currentSeconds: number): void {
    const duration = Math.max(this.clip.durationSeconds, 1e-9);
    const now = this.clip.loop
      ? ((currentSeconds % duration) + duration) % duration
      : Math.max(0, Math.min(duration, currentSeconds));
    if (!this.initialized) {
      this.previousSeconds = now;
      this.initialized = true;
      return;
    }
    const events = [...(this.clip.events ?? [])].sort((a, b) => a.timeSeconds - b.timeSeconds);
    const emitRange = (fromExclusive: number, toInclusive: number): void => {
      for (const event of events) {
        if (event.timeSeconds > fromExclusive && event.timeSeconds <= toInclusive) {
          this.listener(event, this.clip);
        }
      }
    };
    if (this.clip.loop && now + 1e-9 < this.previousSeconds) {
      emitRange(this.previousSeconds, duration);
      emitRange(-1e-9, now);
    } else {
      emitRange(this.previousSeconds, now);
    }
    this.previousSeconds = now;
  }
}
