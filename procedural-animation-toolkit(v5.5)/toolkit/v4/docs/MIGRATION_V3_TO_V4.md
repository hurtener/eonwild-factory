# Migration from V3 to V4

V3 remains a valid constrained flat-ground walk baseline. V4 does not invalidate its files or clip names.

## Keep

- semantic map;
- source GLB and full rig;
- V3 signed hinge geometry;
- V3 neutral jaw calibration;
- direct GLB writer;
- V3 validation fixtures.

## Replace or extend

- replace toe-joint contact metrics with selected sole vertices;
- replace straight constant root assumptions with schedules and paths;
- add terrain height/normal surface;
- add alert/style controls;
- add action generator and transition graph;
- use manifest-driven browser playback;
- add root-motion and in-place pairs for each locomotion mode.

## Compatibility

Existing V3 consumers can continue loading `PROC_WALK_LARGE_V3_INPLACE`. V4 clients should read `animation-manifest.v4.json` rather than hard-code every clip name.
