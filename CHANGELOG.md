# Changelog

## Unreleased

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
