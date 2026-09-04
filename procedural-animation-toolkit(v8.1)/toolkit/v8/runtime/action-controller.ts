import type { AnimationBackend, AnimationHandle, RuntimeInput } from "./types";
import { phaseDistance } from "./phase-clock";

interface ActiveAction {
  kind: "eat" | "bite" | "roar";
  priority: number;
  clip: AnimationHandle;
  returnState: "idle" | "walk" | "alertIdle" | "alertWalk";
}

const priorities = { eat: 30, roar: 60, bite: 70 } as const;

/** Priority-aware one-shot/action layer. It never interrupts a bite with eating,
 * preserves the previous locomotion state, and chooses explicit V4 bridge clips.
 */
export class ActionController {
  private active?: ActiveAction;
  private previousState: ActiveAction["returnState"] = "idle";

  constructor(private readonly backend: AnimationBackend) {}

  request(
    kind: ActiveAction["kind"],
    currentState: ActiveAction["returnState"],
  ): boolean {
    const priority = priorities[kind];
    if (this.active && this.active.priority > priority) return false;
    if (this.active) this.active.clip.stop();
    const clipName = kind === "eat" ? "PROC_EAT_LOOP_V4" : kind === "bite" ? "PROC_BITE_ATTACK_V4" : "PROC_ROAR_V4";
    const clip = this.backend.getClip(clipName);
    this.previousState = currentState;
    this.active = { kind, priority, clip, returnState: currentState };
    clip.play(kind === "eat");
    return true;
  }

  cancel(): void {
    if (!this.active) return;
    this.active.clip.stop();
    this.active = undefined;
  }

  update(input: RuntimeInput): ActiveAction["returnState"] | undefined {
    if (input.cancelAction) this.cancel();
    if (!this.active) return undefined;
    if (this.active.kind !== "eat" && !this.active.clip.playing) {
      const result = this.active.returnState;
      this.active = undefined;
      return result;
    }
    return undefined;
  }

  bridgeFrom(state: string, action: ActiveAction["kind"]): string {
    if (state.includes("walk")) {
      if (action === "bite") return "PROC_WALK_TO_BITE_READY_V4";
      if (action === "roar") return "PROC_WALK_TO_ROAR_READY_V4";
      return "PROC_WALK_TO_EAT_V4";
    }
    if (action === "roar") return "PROC_IDLE_TO_ROAR_READY_V4";
    if (action === "eat") return "PROC_IDLE_TO_EAT_V4";
    return "PROC_IDLE_TO_ALERT_IDLE_V4";
  }

  /** Choose a target gait phase near a planted-foot configuration. */
  static safestActionPhase(currentPhase: number): number {
    const candidates = [0, 0.5];
    return candidates.reduce((best, candidate) =>
      phaseDistance(currentPhase, candidate) < phaseDistance(currentPhase, best) ? candidate : best,
    candidates[0]);
  }
}
