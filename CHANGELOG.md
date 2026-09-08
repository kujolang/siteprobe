# Changelog

## Unreleased

- Move all 36 existing maintenance tests and a new bounded-fixture regression, loopback fixtures, benchmarks, schema checks and source-package verification to Kujo. Preserve frozen, signed compatibility fixtures and remove the Python CI dependency.

## 0.3.0 - 2026-09-07

- Qualify native operation on Linux, macOS and Windows, including complete
  10,000-page crawls at concurrency 1, 4, 8 and 16.
- Pin Kujo with corrected loop/exception scopes, bounded regex reuse, isolated
  worker captures and Windows no-replace publication.
- Refresh release metadata, current qualification, source-package documentation
  and supported macOS runners.

- Dispatch crawl batches through isolated async Kujo workers so configured
  concurrency performs overlapping fetches; enforce this with a barrier fixture.
- Preserve LF source checkouts and decode native test output as UTF-8 on Windows.

- Replace the Python product with Kujo CLI, crawl, robots, page extraction,
  artifact analysis/validation, comparison, signing and reporting modules.
- Stream sitemap downloads/XML projection and large JSONL transformations through
  bounded runtime mechanisms; preserve the v1 artifact schemas and CLI commands.
- Remove Python discovery from production launchers. Keep Python only for test
  servers, benchmarks and the frozen differential oracle.
- Add a source gate rejecting production Python and subprocess delegation.

- Enforce robots policy on redirects, reject unavailable rules and nonfinite
  bounds, and keep blocked pages inside the page budget.
- Publish runs with atomic no-replace rename; bound manifest/key reads and reject
  incomplete manifests; close failed HTTP/TLS connections.
- Bound external-sort fan-in and report bytes, stabilize deterministic page
  timing, and fail explicitly on truncated launcher output.
- Add adversarial regression coverage, reuse the CLI dispatch for deterministic
  fuzz samples, and remove runtime builtin inventory from generated product docs.

## 0.2.0 - 2026-08-12 (development milestone; not tagged)

- Pin DNS-approved addresses to connections and re-evaluate every redirect hop.
- Add origin pacing, bounded robots crawl delay, gzip sitemap budgets, query policies, and conditional baseline fetches.
- Stream large page/link artifacts through bounded deterministic external sorting.
- Record hreflang, refresh, HTTP Link, ETag, Last-Modified, and conditional reuse evidence.
- Add SHA-256 run manifests, optional HMAC signing, and `verify`.
- Validate primary artifacts with Kujo's native JSON Schema validator.
- Add Linux/macOS/Windows launchers and CI, Kujo release packaging, checksums, integration examples, generated references, and committed 10,000-page benchmark evidence.
- Moved the Kujo entrypoint and bounded protocol adapter into the standard `src/` layout.
- Blocked non-public network targets by default with an explicit authorized-use override.
- Added atomic run publication, immutable output paths, cross-artifact validation, severity counts, and `--fail-on` CI gates.
- Reused one bounded worker pool per crawl and capped retained page structure and sitemap members.
- Fixed nested title and heading extraction and exposed truncation evidence.
- Moved validation orchestration into Kujo and expanded CI, schemas, fixtures, and product documentation.

## 0.1.0 - 2026-08-11

- Initial deterministic SiteProbe crawler, artifact schemas, comparisons, fixtures, and validation.
- Qualified malformed URL/HTML/JSON-LD, redirect, robots/canonical conflict,
  duplicate, cycle, timeout/retry/rate-limit, huge-response, output-budget,
  cache-invalidation, offline, deterministic-rerun, and GET-only boundaries.
