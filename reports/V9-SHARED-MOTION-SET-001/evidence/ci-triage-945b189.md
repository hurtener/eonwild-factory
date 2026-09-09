# Published 945b189 CI triage

Captured from PR 2 and Factory verification run 34267874113. The
source-evidence run 34267874117 and contracts job 102201858594 succeeded. The
factory run was still active at capture, so this report classifies only the
requested completed jobs.

| Representative job | Job ID | Result | Actual cause |
|---|---:|---|---|
| walk.v3 candidate | 102201859278 | FAILURE | Package integrity and feasibility passed. Exact serialized LINEAR cyclic linear mismatch was 2.281509 mm/s against 1 mm/s; angular continuity passed. The command intentionally returned exit 2 for technical BLOCKED. |
| Adult fast-walk recovery v3 | 102201859202 | FAILURE | Package integrity and feasibility passed, including solved foot-pitch rate 575.599 deg/s against 600. Exact LINEAR cyclic linear mismatch was 5.406219 mm/s; angular continuity passed. Exit 2 reflects technical BLOCKED. |
| sprint.v4 candidate | 102201859340 | FAILURE | Package integrity and feasibility passed, including solved foot-pitch rate 501.148 deg/s against 600. Exact LINEAR cyclic linear mismatch was 70.389506 mm/s; angular continuity passed. Exit 2 reflects technical BLOCKED. This is the published v4 CI recipe, not the later retained v5 diagnostic. |
| Walk start/steady/stop pair | 102201858850 | CANCELLED | The job hit its declared 45-minute timeout. Steady (BLOCKED), start (PASS), and stop (PASS) packages all reopened before cancellation, but the join result was never reached. The 255,493,685-byte diagnostic artifact still uploaded as artifact 10074306535. Cancellation is not a join failure or pass. |
| First native review: adult walk v3 | 102209969265 | FAILURE | Blender setup and compile succeeded; four-view rendering completed with render_status PASS. The review command returned exit 2 because the candidate remained technically BLOCKED. This was not a native-render failure. |

The sampled locomotor failures are governed candidate outcomes with different
measured values, not infrastructure crashes. Other matrix jobs must be read
individually; this report does not infer that every failure has the same cause.
Native jobs that were queued or running at capture have no verdict here.

[receipt.json](./receipt.json) records the exact values, job IDs, run identity,
and SHA-256 hashes of the fetched job logs. The logs were fetched read-only
through the GitHub Actions job-log API and retained beside this report.
