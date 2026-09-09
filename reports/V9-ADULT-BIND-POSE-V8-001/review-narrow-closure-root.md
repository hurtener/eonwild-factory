# Root bind-pose P1 narrow closure

Exact postfix: 2d6b5e6506c14231f2a87b593bd8897ae0143519, parent1b5a13e9c703a67470288901291aff65aa9faa4a. This is the one narrow diff/reproducer check following two full review rounds, not a third whole-branch review.

The used accessor span is now checked against its declared bufferView and the declared embedded buffer before the generic reader runs. Boolean/fractional lengths, external buffer URI, invalid stride, misalignment and out-of-range used spans reject. Root independently reran the three exact accepted corruptions from round2 plus Boolean/fractional buffer length and an external URI: all raise ContractError. All43 focused tests passed in5.57 seconds. Root regenerated the valid source and independently confirmed exact SHA2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f, identical to the frozen asset and the source of the V8 films.

Receipt: root-bind-narrow-closure-2d6b5e6.json, SHA667d9cf8abd03693cbbb8aca332946624146b94bb537717e5b8b59a992382972.

The concrete P1 accessor-range finding is closed. No root P0/P1 remains in this bounded stage. Source admission is still the supported TRS/skin recovery path, not a replacement for full Khronos validation of every glTF field. Existing generation defaults, geometry, recipe, thresholds, candidate hashes and review media are unchanged. Native V8 playback remains pending Mac unlock; no visual or production acceptance follows from this code review.
