# SiteProbe next-session roadmap

This is the prioritized follow-up list after the August 2026 production-readiness
pass. Each item preserves the same-origin, read-only, robots-respecting, bounded
artifact contract.

## P0 — Trust boundaries

- [ ] Pin DNS resolutions to connections, then re-check every redirect hop to close the remaining DNS-rebinding window without enabling cross-origin crawling.
- [ ] Add configurable request pacing per origin, honor bounded `Crawl-delay` where practical, and record the effective rate policy in `run.json`.
- [ ] Validate artifacts against the checked-in JSON Schemas using a Kujo-native validator once the runtime exposes the required Draft 2020-12 features.
- [ ] Add signed run manifests with per-artifact SHA-256 digests so remote consumers can verify transport integrity.

## P1 — Crawl coverage and scale

- [ ] Stream page and link artifacts during large crawls while preserving deterministic final ordering through bounded external sorting.
- [ ] Support gzip-compressed sitemap indexes and URL sets with independent compressed and expanded byte limits.
- [ ] Add an operator-controlled query-parameter policy for deny lists, stable sorting, and duplicate-content crawl traps.
- [ ] Record `hreflang`, refresh directives, and HTTP `Link` header relationships in versioned artifacts.
- [ ] Add conditional-fetch support for ETag and Last-Modified baselines without turning runs into a mutable cache.
- [ ] Benchmark 10,000-page fixtures across concurrency levels and publish CPU, peak memory, wall-time, and artifact-size envelopes.

## P2 — Distribution and ecosystem

- [ ] Replace the remaining Python protocol adapter and fixture server as Kujo gains production HTTP streaming, DNS policy, HTML/XML parsing, and local test-server primitives.
- [ ] Add cross-platform launchers and qualification for Linux, macOS, and Windows.
- [ ] Publish a versioned install path and checksum-verified release artifacts through the Kujo package workflow.
- [ ] Add first-party examples for ContentGraph, Eval, RunLedger, and CI baseline promotion.
- [ ] Generate reference documentation from Kujo sources and artifact schemas through DocGen.

## Exit criteria for the next milestone

- All new behavior is opt-in or backward compatible with `siteprobe.run/v1`.
- The fixture contract, Kujo checks, lint, formatting, schema checks, and benchmark pass.
- Security-sensitive behavior has explicit negative tests and documented operator controls.
- Any schema-breaking change ships under a new schema identifier with migration notes.
