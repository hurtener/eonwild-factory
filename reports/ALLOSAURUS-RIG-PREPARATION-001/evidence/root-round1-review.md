# Root review of Allosaurus rig preparation

Implementation inspected: f941fe9 (not promoted). Candidate GLB SHA-256: 0fe715fe38aeca125d3ecda873d4575eb151690c4b759cbfdfbaa0f0ef8ec04f.

The seven focused tests passed on this implementation. They do not close the findings below.

1. Native final jaw +8/-8 degree side renders show the upper snout and upper tooth row moving while the eye/crest remain stable. The diagnostic cranium subset was defined by head weight >=0.75 and jaw weight <=0.05, which excludes the suspected incorrectly jaw-weighted skull vertices. This is not an independent proof of skull/jaw separation. Author asked to quantify an anatomical upper skull region independently of existing weights and correct confirmed leakage.
2. The preparation rebuilds inverse binds to the stored POSITION geometry and checks only that output reconstruction. It does not check that the actual incoming neutral skinned surface is preserved. A source with every inverse bind x translation shifted by +0.01 is accepted; input bind-to-POSITION error is 0.020087094131633104 m and output reports 8.672800672062335e-7 m. See noncanonical-input-witness.json. Author asked to reject noncanonical inputs or preserve the actual input skin. Also requested an explicit supported-topology boundary for multiple skins/shared bindings.

Neutral overlays and isolated leg probes are static inspection evidence only. Front views are small in frame and are insufficient for detailed joint/skin approval. Hands/pedal digits remain unresolved. No animation onboarding, biological fit, browser playback or Unity parity is approved here.
