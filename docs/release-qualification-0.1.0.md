# SiteProbe 0.1.0 release qualification

Status: PASS for the documented bounded, read-only crawler contract.

The release gate covers deterministic URL fuzzing; malformed HTML and JSON-LD;
redirect chains and cross-origin redirect rejection; robots and canonical
conflicts; duplicate content; cyclic links; timeouts, bounded retries, 429/5xx
handling; response/page/depth/concurrency/output/report budgets; stale output
rejection; offline command boundaries; and semantic deterministic reruns.
Fixture servers record request methods and the suite fails if SiteProbe uses
anything other than GET.

The WebOps dogfood baseline is
`kujo-workflows/docs/evidence/siteprobe-live-final-2026-08-11`: 60 public pages,
1,177 links, and zero findings. Release dogfood must use the same 60-page scope
and compare the resulting run to that immutable baseline.

Run `bash scripts/validate.sh` and `python3 scripts/benchmark.py --pages 1000`.
SiteProbe has no publish, submit, or ACT command.
