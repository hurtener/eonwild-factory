# Game Modes, Multiplayer, and Social Play

Status: **Canonical solo-first principle**; multiplayer details are working direction.

## 1. Solo is the primary contract

Every core system must work for one player:

- ecology;
- migration;
- herds;
- predators;
- scavengers;
- progression;
- environmental events;
- replayability.

The game must not become empty or mechanically incomplete when no other humans are online.

## 2. Initial mode structure

### Solo life

The complete core experience:

- local world simulation;
- local progression;
- pause where appropriate;
- no network dependency after required assets are available;
- seeded conditions and repeatable lives.

### Private cooperative life — later working direction

Start with two players and expand toward four only after the solo game is strong.

Initial assumptions:

- invite/link or room code;
- same species or compatible social role first;
- host-authoritative simulation;
- no public ranking;
- no tradeable economy;
- partial Lineage settlement on disconnect.

### Public PvPvE — future option

Possible only after:

- movement and combat are stable;
- authority and cheating risks are acceptable;
- matchmaking population exists;
- species balance is based on ecology rather than duel parity;
- public sessions add more value than operational burden.

It is not required for product validation.

## 3. Why same-species co-op comes first

Same-species or herd-compatible co-op reduces early complexity:

- shared movement expectations;
- compatible needs;
- fewer balance permutations;
- understandable calls and social roles;
- easier testing;
- cooperation rather than instant predator/prey griefing.

Mixed species and human-controlled predator/prey interaction can come later.

## 4. Multiplayer architecture direction

Browser private sessions may use:

- one authoritative host browser;
- WebRTC data channels;
- a small Go signaling service;
- STUN and TURN fallback where required;
- state snapshots and events rather than visual-effect replication.

Wails/Steam editions may later use platform lobby/relay services or dedicated/community hosting.

This architecture is a cost-saving direction, not a promise of zero infrastructure. Signaling, relay fallback, diagnostics, and support still exist.

## 5. What synchronizes

Synchronize meaningful state:

- player input;
- position and orientation;
- movement state;
- action events;
- confirmed contact/damage;
- condition and injury;
- feeding/drinking ownership;
- important AI state;
- weather/ecology seed and events;
- Lineage event eligibility.

Recreate locally:

- footsteps;
- rain particles;
- grass movement;
- breathing;
- minor head/tail variation;
- ambient insects;
- nonessential visual effects.

## 6. Host departure

Initial direction:

- settle completed Lineage events;
- preserve an optional chapter/checkpoint state when feasible;
- end or re-host cleanly;
- do not build seamless host migration before the game proves demand.

A graceful session ending is better than an unreliable transparent migration system.

## 7. Separation and world cost

Multiple players can move apart and expand the active-world union. Early multiplayer may impose a generous but explicit separation policy or warn when players exceed supported distance.

The constraint should be presented as social/ecological cohesion where appropriate, not an invisible teleport wall. The solo world remains continuous.

## 8. Social communication

Primary in-world communication should use:

- species calls;
- body orientation;
- posture;
- movement;
- group markers only where necessary;
- limited contextual signals.

Text chat may exist in private sessions later. Built-in voice chat is not an initial requirement.

Calls must remain meaningful and readable. Cosmetic call variation cannot make critical communication ambiguous.

## 9. Cooperation examples

- shared vigilance;
- alternating attention while feeding;
- warning calls;
- protecting a vulnerable group member;
- coordinated movement through a crossing;
- pressure/flank/intercept behavior for species where the game interpretation supports it;
- guiding another player toward water or shelter;
- sharing or contesting a carcass.

Cooperation should not reduce to standing close for a passive stat buff.

## 10. PvP philosophy

When human predator/prey interaction exists:

- the world is not balanced as equal duels;
- avoidance, detection, terrain, group size, condition, and species role matter;
- spawn camping and repeated targeting need safeguards;
- death remains meaningful but session length respects the player;
- no ranked ladder or cash-valued progression should motivate cheating.

## 11. Community servers — future

A later desktop edition may provide a headless or community-hosted server executable with configurable:

- player count;
- session length;
- PvP rules;
- ecological intensity;
- species availability;
- progression policy;
- accessibility and difficulty.

Community hosting can support dedicated players without requiring Eonwild to fund every persistent server.

## 12. Not in initial multiplayer scope

- 100-player promises;
- seamless host migration;
- guilds/clans;
- global economy;
- trading;
- ranked esports;
- voice moderation infrastructure;
- persistent MMO world;
- cross-platform competitive progression;
- public matchmaking before private sessions are stable.

## 13. Multiplayer-quality questions

Multiplayer is worth expanding when:

- it adds stories unavailable in solo;
- players communicate through animal behavior;
- solo remains complete;
- host authority is stable;
- disconnection does not erase the session unfairly;
- group play does not trivialize ecological pressure;
- infrastructure and support costs remain proportionate to demand.
