# V2 Quality Gates

## Automated hard failures

Generation must stop when:

- a required semantic role is absent;
- a mapped source node does not exist;
- the GLB skin or inverse-bind accessor cannot be read;
- internal Hz is not an integer multiple of export Hz;
- stance fraction is outside the supported biped range;
- animation samples are non-monotonic;
- quaternion, translation, or channel dimensions disagree;
- a generated channel references an unknown node.

## Numeric acceptance targets

Targets are normalized by hip height where possible.

| Metric | Prototype | Production candidate |
|---|---:|---:|
| Loaded horizontal contact error | ≤ 1.0% hip height | ≤ 0.5% |
| Loaded toe/sole ground proxy error | ≤ 3.0% hip height | ≤ 1.5% |
| Rotation loop endpoint | exact | exact |
| Tail periodic endpoint | ≤ 0.1° | ≤ 0.03° |
| Export rate | ≥ 60 Hz | 60 Hz or validated cubic reduction |
| Internal solve rate | ≥ 120 Hz | ≥ 120 Hz |
| Ground penetration | no visible sustained penetration | vertex-level threshold |

The Tarbosaurus v2 test is within the production-candidate horizontal contact target. Toe ground is still joint-proxy based and remains a perceptual-review item.

## Mandatory perceptual review

Automated metrics cannot approve animation style. Review at real speed, half speed, and frame stepping from:

1. side camera;
2. front camera;
3. three-quarter camera;
4. normal gameplay camera and distance.

Reviewers specifically check:

- knee direction and leg compression;
- foot acceleration before contact;
- toe release and ground clearance;
- whether pelvis shift anticipates support;
- whether torso counteraction feels massive rather than rigid;
- whether the tail responds rather than waves decoratively;
- jaw clearance and neutral expression;
- loop visibility;
- asymmetric artifacts introduced by the source weights.

## Runtime gates

The in-place clip is only valid when runtime speed matches the profile’s recommended metres per second. A mismatch creates apparent sliding even if the authored contact plan is correct.

Terrain runtime must provide:

- ground height under each planned contact;
- surface normal;
- reachability result;
- collision/ledge policy;
- contact target persistence while loaded.
