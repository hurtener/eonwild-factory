# Browser Performance and Fidelity Strategy

## Two authoring profiles

The validated downloadable pack uses the browser-production profile:

```text
internal solve:               60 Hz
GLB export:                   60 Hz
selected sole witnesses:     64 per foot
bounded leg evaluations:     8 per sample
```

The toolkit also ships an optional ultra-offline profile:

```text
internal solve:               120 Hz
GLB export:                   60 Hz
selected sole witnesses:     up to 192 per foot
bounded leg evaluations:     20 per sample
```

The ultra profile is intentionally more expensive and is not required for every creature. It is useful when a difficult action or terrain contact benefits perceptibly from denser authoring evaluation.

## Browser contract

The final GLB contains standard glTF animation channels. The browser does not execute Python and does not need Blender. It receives:

- named animation clips;
- dense 60 Hz quaternion and translation tracks;
- a manifest with contact markers, state tags, recommended speed and transition metadata;
- the unchanged 75-joint source skin;
- all three joint/weight attribute sets, for twelve possible influences per vertex.

## Included dependency-free viewer

`browser_demo/` is a real WebGL2 playback implementation, not a static mockup. It:

- parses the GLB directly;
- samples skeletal animation channels;
- uploads 75 joint matrices through an RGBA32F matrix texture;
- evaluates twelve skin influences in the vertex shader;
- crossfades clips and queues complete behavior sequences;
- follows root-motion clips;
- displays flat, uneven, or sloped ground corresponding to the selected clip;
- uses no npm package, CDN, or third-party runtime library.

A separate self-contained HTML embeds the complete GLB and viewer in one file. The folder-based version is smaller and is served with the included Python helper.

## Runtime quality ladder

### Near / hero creature

- full skeletal clip at 60 Hz;
- terrain residual solve at a fixed 60 Hz tick;
- vertex-sole witness validation or a reduced representative witness set;
- full tail, neck, head and jaw secondary layers;
- action transition graph enabled.

### Mid distance

- baked clip remains full-rate;
- terrain residual solve may run at 30 Hz and interpolate;
- fewer sole witnesses or contact anchors;
- distal tail and small hand motion can update less frequently.

### Far distance

- animation remains phase-correct;
- terrain correction becomes pelvis/foot-height approximation;
- distal secondary chains may be frozen or simplified;
- behavior state continues so LOD changes do not reset the animal.

## Distance-driven phase

For in-place locomotion, rendered phase should follow traveled distance rather than only wall-clock time:

```text
phase += distance_traveled / resolved_stride
```

This preserves contact when AI steering, congestion, slopes, or network correction change actual speed.

## Profiling targets

Measure separately:

- skeleton evaluation time;
- joint-matrix upload time;
- terrain queries;
- contact residual iterations;
- tail/neck secondary overlays;
- draw calls and shadow cost;
- transition/crossfade cost;
- number of simultaneously near-quality creatures.

Do not optimize by deleting source bones from every asset. Lower runtime cost through LOD, selective residual solves, fixed-tick updates and distance-based quality policies while preserving the rich rig for close views and actions.
