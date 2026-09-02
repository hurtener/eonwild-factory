# Feeding003 — original texture presentation

Render-only companion to the frozen Feeding003 candidate. The original 4096×4096 embedded base-color image (`Image_0`, SHA256 `cd930428009d328676e9ecaadbe13f9829bf093eba28207ff124fea8faf3f7eb`) and `UVMap` are displayed under the existing studio lighting. No invented texture, motion, geometry or UV edit was made.

This is an **original-albedo preview, not full PBR**: the original normal and metallic/roughness maps remain intact in the GLB but are not evaluated by Workbench. The host approved the side proof before full rendering.

Videos: `build/V9-FEEDING-REVIEW-003/textured/feeding-side.mp4`, `feeding-front.mp4`, `feeding-rear.mp4`; complete native 24 fps, six-second, 144-frame, 960×540 views. Original clay videos remain in the parent candidate directory.

The exact same GLB is used: `8f70dcab8e8b56035ed0787ca15674166575213f098ec9c6579e6e8350b6d47b`. The textured directory's `media-verification.json` binds videos to that hash. `render/original-texture-receipt.json` records original embedded image hashes, chosen base-color binding and wrapper hash. The optional prop receipt is isolated in the textured render output; the frozen clay receipt is not rewritten.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python build/V9-FEEDING-REVIEW-003/render_textured.py -- --candidate build/V9-FEEDING-REVIEW-003/feeding.glb --clip feeding_braced_closed_grip_review --output build/V9-FEEDING-REVIEW-003/textured/render --frames 144 --fps 24 --ground-level-canonical-y 0.0008014736783756348 --view side --view front --view rear
python3 build/V9-FEEDING-REVIEW-003/make_textured_media.py
```

The existing `render_feeding.py` still defaults to the unchanged clay presentation. Textures do not add force/tissue physics or change the underlying motion's review status.
