# Root phase-local solver review, round 2

Exact head 79bc9f9cab6e3aebbae9e1aeb6e90324de4371e5; parent e6c0b6f6daefba490305a79722ebb1644ffd1a41. This is the second and final full review for this bounded extraction.

No P0/P1 remains. Ordinary nested role/plan/topology mappings now use detached read-only snapshots; axes/worlds/normals are copied and nonwriteable. The source snapshot contains only the topology fields used by FK and semantic resolution. The original full-clip emitter still uses the original source. Malformed required row/body-response fields now reject with ContractError, and the moved contact safeguard points to its actual code owner.

Root ran phase-local, articulated-contact-partition, and motion-performance tests: 96 passed in 19.00 seconds. This includes actual heavy-biped and renamed/frame-transformed complete output byte pins, caller-mutation and nested-write isolation, rejected-row safety, phase/order independence, and the adjacent safeguard. The extraction and postfix diffs retain operation order and existing float32 serialization. No current full-clip behavior regression was observed.

Residual P2 follow-up: the optional ArticulationProfile object is still directly aliased into context. Its support/swing mappings are mutable even though the outer dataclass is frozen; later caller mutation can change a retained row context or make effective() fail. The independent reviewer reproduced profile.support.clear() followed by KeyError. Existing immediate full-clip use is unaffected. Track this explicitly, and snapshot these guardrails before the next stage exposes retained arbitrary-time contexts. Do not describe all profile data as deeply immutable.

Stage decision: ready for integration and mandatory full-suite verification with this explicit P2 debt. No third full-branch review, no CUBICSPLINE emitter or arbitrary-time/continuous-skin/tangent authority, no threshold or approval change. Native renders need not be repeated for byte-identical output.
