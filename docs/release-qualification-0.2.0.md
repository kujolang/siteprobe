# SiteProbe 0.2.0 release qualification

Status: historical PASS for the Python-backed 0.2.0 implementation.
For the native Kujo rewrite, use [the current audit](audits/repository-hardening.md).

The fixture gate covers GET-only behavior, same-origin redirect denial,
DNS-pinned public-address policy, private-network opt-in, robots enforcement and
bounded pacing, retry and timeout limits, gzip sitemap expansion limits, query
normalization policies, conditional ETag reuse, deterministic external sorting,
artifact consistency, Kujo-native Draft 2020-12 schema validation, digest and
HMAC manifest verification, immutable atomic publication, and adversarial URL,
HTML, JSON-LD, symlink, output-budget, and tampering cases.

The 10,000-page performance matrix in `benchmark-10000.json` records wall time,
CPU time, peak RSS, artifact bytes, and throughput at concurrency 1, 4, 8, and
16. The historical Python Darwin fixture envelope peaks below 78 MiB RSS; concurrency 4
is the fastest recorded setting at 506.37 pages per second.

Linux, macOS, and Windows run the same Kujo-owned validation workflow in CI.
Tagged releases use the Kujo package preview and `scripts/release.kujo` to build
platform archives with matching SHA-256 files.

Run:

```bash
bash scripts/validate.sh
kujo run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16
```
