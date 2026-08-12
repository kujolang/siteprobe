# Changelog

## 0.2.0 - 2026-08-12

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
