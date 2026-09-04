# V8 Design-Lab Power Attack

## Reference reading

The first approximately four seconds of the supplied video show a large theropod changing intent and mobilizing its whole mass:

1. the skull and neck lower;
2. the hindquarters compress;
3. the head changes direction before the pelvis finishes reorienting;
4. the tail sweeps opposite the turn;
5. one hindlimb releases force while the other advances;
6. the animal continues through sequential catches rather than reaching only with its neck.

V8 condenses those qualities into a gameplay-readable committed bite instead of copying the camera move or creating a miniature running loop.

## Authored phases

| Phase | Normalized window | Mechanical goal | Readable detail |
|---|---:|---|---|
| Target acquisition | 0.00–0.09 | Establish gaze and support | Head turns before body commitment; jaw remains closed |
| Coil | 0.05–0.28 | Store force in hips, knees, and ankles | Pelvis moves back/down; tail counter-preloads; neck retracts |
| Release | 0.28 onward | Convert leg extension into root travel | Pelvis rises through support instead of chest-diving |
| First catch | ~0.49 | Receive the initial drive | Lead foot advances and accepts load |
| Second drive/catch | 0.49–0.67 | Continue mass through the strike | Opposite foot advances while the first foot braces |
| Late gape | ~0.25–0.67 | Keep the mouth intentional | Wide gape arrives after commitment, not during neutral anticipation |
| Contact snap | ~0.67 | Commit damage/contact event | Jaw closes over a finite interval; skull/neck/chest brace |
| Clamp and tear | 0.67–0.80 | Show resistance after contact | Jaw remains closed; head, neck, chest, pelvis, and tail oppose the pull |
| Recoil | ~0.78–0.90 | Dissipate force | Skull retracts, tail responds, support shifts |
| Recovery | 0.84–1.00 | Return to a transition-ready body | Root keeps delivered distance; no backward teleport |

## Force path

```text
support foot
→ ankle extension
→ knee extension
→ hip/pelvis travel
→ torso transmission
→ neck thrust
→ skull contact
```

The attack should never read as:

```text
head reaches forward
→ body follows late
```

## Mirroring

V8 generates independent left- and right-lead clips. Mirroring changes:

- the first catch foot;
- support-load schedule;
- lateral foot placement;
- pelvis roll/yaw;
- contact head yaw/roll;
- tear direction;
- tail counter-shape.

It does not merely reflect a finished matrix track.

## Jaw contract

- Living neutral uses the calibrated approximately 50° closure.
- Gape develops late in the drive.
- Additive gape is approximately zero at the bite-contact marker.
- The jaw remains clamped through the tear.
- Recovery ends closed.

## Runtime integration

The action event sequence is:

```text
attack_target_locked
attack_hindlimb_release
attack_first_catch
bite_contact
bite_tear_release
recovery_start
```

Damage should be applied in the `bite_contact` window only after target-volume confirmation. Camera impulse and impact audio may begin at contact; prey drag or resistance should influence the hold/tear layer rather than moving the complete attacker root arbitrarily.
