# Rig-Calibrated Living-Neutral Jaw

The Tarbosaurus source model intentionally uses an open mouth for modeling the teeth and oral cavity. Its bind pose is therefore unsuitable as a default living pose.

V5 selects two vertex groups from skin weights:

- mandible witnesses influenced by the discovered five-joint jaw chain;
- upper-mouth witnesses influenced by skull, snout, and snout-tip bones.

Vertices are divided into forward mouth bins. Within each bin, upper jaw low-surface and lower jaw high-surface quantiles form a clearance witness. Candidate closure angles are evaluated from 42° through 52° in 0.25° increments.

For this rig, the selected living-neutral closure is approximately 50°. It is the closest candidate to the configured target gap while remaining collision-safe. V4's generic 33° offset left a visibly open silhouette.

Neutral clips retain only a sub-degree breathing gape. Eating boundaries, bite contact, roar recovery, and transition endpoints return to the calibrated neutral pose.
