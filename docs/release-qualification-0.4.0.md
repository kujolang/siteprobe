# SiteProbe 0.4.0 release qualification

Release date: September 22, 2026. Product and maintenance workflows are native
Kujo. Install the exact revision in `KUJO_REVISION`:
`2be1f04b89dbecd591ef1af0d68974c05586900e`. Source ZIPs do not bundle a runtime.

## Evidence and compatibility

The [readiness completion record](readiness-completion.md) maps all eight review
items to their implementation, tests and receipts. Final implementation source
`293a0d3998ad314763c8045066f8c74cff132ad7` passed 46 tests and extracted-package
validation on Linux, macOS and Windows in
[run 35754131008](https://github.com/kujolang/siteprobe/actions/runs/35754131008).
Linux also passed complete 10,000-page sweeps at concurrency 1/4/8/16 and dense
and multilingual workloads. Actual consumer versions and resource measurements
are recorded in the linked audit artifacts. The frozen oracle and v1 identifiers
remain unchanged. Robots corrections and stricter validation intentionally reject
previously incorrect decisions and inconsistent inputs.

The versioned release reruns the native gate and extracted-archive verification on
Linux x64, macOS Intel/ARM64 and Windows x64 before publishing ZIPs and SHA-256
files. Publication is conditional on all four jobs passing; inspect the tag's
GitHub Actions result for release-specific evidence.

## Boundaries

SiteProbe observes static/server-rendered sites within configured same-origin,
network, robots and resource policies. It does not render JavaScript. Retained-data
and staging estimates do not impose a hard RSS limit. See [security](security.md)
and [resource accounting](readiness-completion.md#resource-accounting).

## Publication verification

The annotated `v0.4.0` tag identifies the release source. Verify that the GitHub
release has four platform ZIPs and four matching `.sha256` files, and verify the
checksums of downloaded assets. Keep historical qualification records unchanged.
