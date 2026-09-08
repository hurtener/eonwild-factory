# Adult V10 cubic root validation

The exact f9ca924 adult V10 package passes independent serialized world-joint and ordered foot-material loop checks, real Khronos validation, and sampled native Blender/Cycles skin parity. All 100 engine hashes and all 7 recipe input bindings match the committed generator and frozen checkpoint. Package payload hashes remain unchanged after inspection.

Maximum endpoint velocity mismatch is 0.261947 mm/s for world joints and 0.203975 mm/s for full ordered foot material, against the unchanged 1 mm/s limit. Exact motor reconstruction makes root-motion/in-place results agree below 1e-15 m/s. Khronos 2.0.0-dev.3.10 reports 0 errors and 4 warnings for each GLB.

Blender 5.2.0 LTS was checked at 18 actual source times per mode, including keys and interval interiors, against all 59169 same-index vertices. Maximum sampled error is 4.482 micrometres in-place and 4.374 micrometres root-motion. After a real Cycles render, without reapplying the intended pose to conceal reevaluation, errors are 2.316 and 2.318 micrometres. The acceptance limit remains 0.5 mm. This is sampled rendering parity, not whole-interval certification.

## Visual verdict

**REVISION_REQUIRED: body weight transfer remains insufficiently convincing.** Root viewed all 296 frames across matching-camera V9-CUBIC/V10-CUBIC side and front movies. Every frame is represented in the paired contact sheets bound by visual/inventory.json. Native-size side/front event crops additionally compare frames 4, 23, 41, 60 near the two double-support and two single-support midpoints. These crop labels use the actual 30fps source clock; the exact event midpoint need not coincide with the nearest rendered frame.

The improved leg recovery remains readable; the sampled views show no new obvious ankle collapse, head-up posture or gross foot-floor separation. This visual observation is narrower than mechanical or collision approval. Added V10 settling is slightly visible around double support, but the front body still reads too centered while legs alternate, and the torso silhouette near single support appears displaced toward the raised-foot side. Projection, yaw and surface shape could contribute, so this is a source-geometry diagnostic target, not proof of a wrong anatomical lean. Pelvis/chest/tail world motion and support relationship must be checked before changing amplitudes.

The existing authored example-video audit 002 supplies qualitative chest yield and delayed tail silhouette evidence. It does not calibrate pixels to metres, establish a Tarbosaurus center of mass, or justify blindly copying its amplitudes. Body visual approval remains open despite all technical checks above passing.

New browser control verification is NOT_RUN_POLICY_BLOCKED: an earlier enforced browser-policy denial has not been bypassed. Filesystem frame review and native Blender checks are independently available. Unity remains NOT_RUN; production approval is false.

See receipt.json for exact file hashes and the immutable package manifest identity. Heavy GLBs, expected vertex arrays and media remain on the external SSD.
