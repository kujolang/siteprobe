# SiteProbe next-session roadmap

This is the prioritized follow-up list after the August 2026 production-readiness
pass. Each item preserves the same-origin, read-only, robots-respecting, bounded
artifact contract.

## P0 — Trust boundaries

- [x] Pin DNS resolutions to connections, then re-check every redirect hop to close the remaining DNS-rebinding window without enabling cross-origin crawling. Each connection uses the exact filtered address set resolved for that hop.
- [x] Add configurable request pacing per origin, honor bounded `Crawl-delay` where practical, and record the effective rate policy in `run.json`. `--request-delay` and `--max-crawl-delay` control the recorded effective delay.
- [x] Validate artifacts against the checked-in JSON Schemas using a Kujo-native validator once the runtime exposes the required Draft 2020-12 features. SiteProbe now gates primary artifacts in the artifact section of `src/siteprobe.kujo`; Kujo was extended to accept standard Draft 2020-12 annotations and exclusive numeric bounds.
- [x] Add signed run manifests with per-artifact SHA-256 digests so remote consumers can verify transport integrity. `manifest.json` covers every run artifact and supports optional HMAC-SHA-256 signing and verification.

## P1 — Crawl coverage and scale

- [x] Stream page and link artifacts during large crawls while preserving deterministic final ordering through bounded external sorting. Pages and links spool incrementally and use bounded chunked k-way merges.
- [x] Support gzip-compressed sitemap indexes and URL sets with independent compressed and expanded byte limits.
- [x] Add an operator-controlled query-parameter policy for deny lists, stable sorting, and duplicate-content crawl traps.
- [x] Record `hreflang`, refresh directives, and HTTP `Link` header relationships in versioned artifacts.
- [x] Add conditional-fetch support for ETag and Last-Modified baselines without turning runs into a mutable cache. Immutable candidates reuse baseline evidence only on HTTP 304 and retain explicit reuse fields.
- [x] Benchmark 10,000-page fixtures across concurrency levels and publish CPU, peak memory, wall-time, and artifact-size envelopes. Evidence is committed in `benchmark-10000.json`.

## P2 — Distribution and ecosystem

- [x] Complete the Kujo-native implementation. All product behavior lives in `src/*.kujo`; Python exists only in maintenance tests and benchmarks. The pinned Kujo runtime supplies generic bounded parsing, file and transport mechanisms.
- [x] Add cross-platform launchers and qualification for Linux, macOS, and Windows.
- [x] Publish a versioned install path and checksum-verified release artifacts through the Kujo package workflow.
- [x] Add first-party examples for ContentGraph, Eval, RunLedger, and CI baseline promotion.
- [x] Generate reference documentation from Kujo sources and artifact schemas through DocGen.

## Exit criteria for the next milestone

- All new behavior is opt-in or backward compatible with `siteprobe.run/v1`.
- The fixture contract, Kujo checks, lint, formatting, schema checks, and benchmark pass.
- Security-sensitive behavior has explicit negative tests and documented operator controls.
- Any schema-breaking change ships under a new schema identifier with migration notes.

Status: native implementation completed by the September 2026 rewrite. See [the current audit](audits/repository-hardening.md) for verification, compatibility and measured performance. The 10,000-page benchmark above records the historical Python implementation; native measurements are labeled separately.

## Open after native migration

- P1, Kujo runtime: reduce captured-environment/execution overhead while preserving scope isolation and closure semantics; see the current audit for paired evidence.
- P2, Kujo runtime: fix the existing VM loop-local immutable binding defect with VM/interpreter parity coverage.
- Qualification: hosted Linux/Windows checks and a full native concurrency sweep remain unverified locally.
