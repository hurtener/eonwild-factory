# Adult V10 load-acceptance: root visual and browser review

Implementation: 94c81e7e3bb00e2e6057fd1babb183adb70ff9e3.
Candidate manifest: e3e9923526ced4e2fd08b5f4ffaa455edb78ce66020c3c3f369e6336d5f0aff7.
Review date: 2026-09-08.

## Coverage and identity

Inspected every V10 frame in both front-body and side-body: 74 frames each,
148 total, through all five contact sheets per view. Also opened full-size
V9/V10 side frames 4 and 23 and the actual paired browser display at those
same double-support / sole-support neighborhoods in both views.
The underlying camera locks and 74 source times match. V9 is 800x450 and
V10 is 640x360; comparison in the browser used equal displayed size.
This is a pose, silhouette and temporal-sequence comparison, not pixel parity.

Side V10 movie SHA-256: 4831727faebe39e72f8ce3e9822b1de83624690962c0a56848f53c1eda466d03.
Front V10 movie SHA-256: 3a0478e62071d0daf15e955cfc5119b9c890a650ed4a6cb38d9e8026fd6e2e75.
Comparison HTML SHA-256: 07cd3a7e4a29c083693e8e90c088e575170bd8700eab0370e9550fa09363ebb7.

## Visual judgment

The broad compression is restrained and resolves over the stride without an
obvious abrupt collapse. The torso remains oriented toward the supporting limb
in the front sequence; the support changes sides without leg crossing. The
side sequence retains the improved open recovery ankle and trailing-to-forward
foot progression. I did not find a return of the rejected hard ankle fold,
persistent recovery floor skim, upward head crane or open-jaw rest pose.

At double support the added vertical yield and small forward trunk response
are visible in the paired silhouette, but subtle. Near the sole-support
midpoint the poses converge as designed. The extra compression is a useful
controlled comparison, not sufficient evidence that the several-ton weight
impression is now solved. It does not add lateral transfer, independent tail
inertia or a force-driven body response; those remain the V9 controls.
No amplitude escalation is justified solely by this inspection.

## Actual browser verification

Chrome page 4, isolated context eonwild-v10-review-check, opened the actual
served comparison URL. All four movies had readyState 4, no media error, and
a full seekable interval 0 to 2.466667 seconds. Used the page's controls:
scrub to frame 22, forward to 23, back to 22, paired play, paired pause,
and restart through completion, independently for both views.

Both pairs advanced at playbackRate 1, paused together, and ended at
2.466667 seconds. Observed playing drift was 0.068 ms side / 0.081 ms front.
No decode or control error occurred. Raw results are retained in
root-adult-v10-browser-controls-94c81e7.json.
The end label can retain the earlier Pause paired text after completion;
this is a minor existing presentation issue, not a motion acceptance finding.

These are actual playback/control observations. The visual judgment above
comes from the full frame sequences and paired stills; it is not a claim of
continuous perceptual normal-speed playback by a human reviewer.

## Decision

Accept the unchanged implementation only as an unselected diagnostic with
no new P0/P1 visual regression found at the reviewed resolution. Keep whole-body
weight/perceptual acceptance open. Do not promote this recipe as finished.
The independently reopened package remains integrity PASS, technical BLOCKED
because its exact LINEAR local loop is 3.965012792580725 mm/s against 1 mm/s.
Unity NOT_RUN. No biological or force-simulation approval is granted.
