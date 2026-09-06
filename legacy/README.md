# Historical recovery, not the active engine

`capsules/v8.2` is the byte-identical approved release capsule. Its manifest,
source base, approved output, reproduction code and media remain intact.
Active compatibility profiles were relocated and re-locked; no approval hash
was silently transferred to a new motion.

The V8 and V8.1 toolkits were removed from the active tree after checking
active source/test/profile/catalog dependencies. Recovery point:
`8c1f5c2bfea481a56916ee6e0bfa74961ca0d141`.

To inspect or recover a retired toolkit into a separate working directory:

```sh
git archive 8c1f5c2bfea481a56916ee6e0bfa74961ca0d141 \
  'procedural-animation-toolkit(v8.1)' | tar -x -C /your/recovery/directory
```

Do not restore these directories as a new development path. Recover useful
performance recipes or algorithms into tested active modules. The Git history
has not been rewritten, so removal reduces the working tree, not necessarily
a full historical clone's size.

V5/V5.5 and existing reports/build experiments remain recovery inputs in this
baseline. Their presence does not certify them as current production APIs.
