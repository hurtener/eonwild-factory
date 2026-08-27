/** Contact-marker utilities for a two-cycle biped superloop. */
export type FootSide = "left" | "right";

export interface ContactMarker {
  foot: FootSide;
  cycle: number;
}

export interface ContactCrossing extends ContactMarker {
  absoluteCycle: number;
}

const positiveModulo = (value: number, divisor: number): number =>
  ((value % divisor) + divisor) % divisor;

/**
 * Returns every contact crossed between two unwrapped gait-cycle positions.
 * Left contacts are at integer cycles; right contacts are at half cycles.
 */
export function crossedBipedContacts(
  previousCycles: number,
  currentCycles: number,
): ContactCrossing[] {
  if (!Number.isFinite(previousCycles) || !Number.isFinite(currentCycles)) {
    throw new Error("cycle positions must be finite");
  }
  if (currentCycles === previousCycles) return [];

  const direction = Math.sign(currentCycles - previousCycles);
  const low = Math.min(previousCycles, currentCycles);
  const high = Math.max(previousCycles, currentCycles);
  const firstHalfStep = Math.floor(low * 2) + 1;
  const lastHalfStep = Math.floor(high * 2 + 1e-10);
  const events: ContactCrossing[] = [];

  for (let halfStep = firstHalfStep; halfStep <= lastHalfStep; halfStep += 1) {
    const absoluteCycle = halfStep / 2;
    const isLeft = halfStep % 2 === 0;
    events.push({
      foot: isLeft ? "left" : "right",
      cycle: positiveModulo(Math.floor(absoluteCycle), 2),
      absoluteCycle,
    });
  }
  return direction > 0 ? events : events.reverse();
}
