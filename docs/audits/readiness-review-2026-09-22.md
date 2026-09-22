# SiteProbe readiness review — September 22, 2026

## Verdict and scope

SiteProbe is useful for bounded static/server-rendered website inventories and CI
artifact comparisons. It is not yet a universally useful or universally
enterprise-qualified crawler. The prior roadmap is complete for its own scope;
that does not close newly identified correctness, policy and scale gaps.

Reviewed starting commit `0c5599c` on `main`: native product source, CLI and
launchers, schemas, tests and immutable oracle, validation, package assembly,
benchmark harness, examples, README and historical qualification. No other
repository's product code was changed. This is a source and fixture review, not
an independent penetration test or certification for arbitrary production sites.

## Improvements delivered

- Validation rejects duplicate normalized page identities before comparison can
  silently collapse records into a map.
- Finding severity totals are recomputed and checked, including unknown severity
  buckets. Link and redirect inventories must have the correct schema identifier
  and array shape. These checks also apply to legacy unsigned runs.
- A dangling `manifest.json` symlink no longer bypasses manifest checks by looking
  like an absent file. Completely absent legacy manifests remain supported.
- Self-comparison validates the run once and returns no changes without building
  duplicate full-page indexes; corrupt self-comparisons still fail validation.
- Link analysis calculates the target origin once instead of once per edge.
- Regression coverage includes corrupted unsigned inventories, matching total
  counts with duplicate pages, comparison rejection, and dangling manifests.
- README and security guidance distinguish `crawl` from `inspect`, integrity from
  authentication, the current robots implementation from full conformance, and
  historical qualification from present readiness.

No obsolete product source remains tracked at the repository root. Keep all three
launchers, package/lock files, version/runtime pin, license and contributor guidance
there: entrypoints and package tooling depend on them. `src/`, `scripts/`, and
`tests/` already separate product and maintenance code. Ignored local caches and
scratch directories are not shipped and were not deleted as user data. Immutable
compatibility fixtures were not edited or regenerated. Release assembly recursively
includes this audit and its evidence under `docs/audits/`.

## Next-session work, in priority order

### P0 — Robots matching and request-policy coverage

**Evidence:** `robots_parse` returns the first matching group; `robots_allowed`
returns the first matching literal prefix. The checked-in
[reproducer](artifacts/readiness-2026-09-22/robots-review.kujo) and
[results](artifacts/readiness-2026-09-22/robots-review.json) show three cases where
access is allowed despite a disallow rule: a more specific path, an embedded
wildcard, and a repeated matching user-agent group.

RFC 9309 requires combining matching groups and using the most specific rule;
it also defines wildcard/end-anchor handling. Use its examples as independent
expectations, including percent encoding and allow ties. [RFC 9309, sections
2.2.1–2.2.3](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.2.1).

**Acceptance:** add an independently authored conformance table, merge matching
groups, implement bounded wildcard/anchor matching and longest-match precedence,
and prove with fixture request history that denied pages and redirect targets are
never fetched. Resolve blank-line handling and empty rules explicitly. Preserve
the old oracle unchanged and document intentional policy differences separately.

`discover_sitemaps` currently calls `fetch_file` with a null policy, and `inspect`
also passes null. Decide and document the intended scope for both commands, then
cover denied sitemap URLs and redirected sitemap URLs. Keep same-origin checks
and fail-closed unavailable-policy behavior.

### P1 — Prevent metrics from modifying immutable runs

**Evidence:** CLI dispatch writes `--metrics-file` with replacement enabled after
`crawl` publishes its directory. A path such as `<out>/run.json` can therefore
replace an artifact after its digest was committed. This path collision is a
source-confirmed operator footgun; it does not establish remote exploitability.

**Acceptance:** reject metrics paths inside any protected output/baseline run,
including canonical parent aliases and Windows paths, before publication. Retain
support for replacing a separate metrics file. Test that artifact hashes and
manifest verification remain unchanged on rejected paths.

### P1 — Enforce resource budgets during work

**Evidence:** `crawl_into` checks `max_output_bytes` after artifact generation;
`page_index` loads complete page records for baseline/compare. `analyze` retains
aggregate indexes and structured-data arrays. Streaming pages does not establish
a constant-memory whole pipeline. A small publication budget does not bound peak
staging disk consumption.

**Acceptance:** measure dense-link and large-JSON-LD fixtures, then add incremental
staging accounting and bounded baseline/compare indexes. Declare overhead and
aggregate memory/disk limits. Test early termination, stage cleanup, deterministic
ordering, and artifacts above 8 MiB. Preserve full evidence within declared bounds.

### P1 — Complete secondary artifact contracts

**Evidence:** only run, page, findings and manifest have checked-in JSON Schemas.
The new link/redirect envelope checks do not validate every item or graph
relationship. Site, robots, sitemap, metadata and structured-data relationships
remain only partially validated.

**Acceptance:** add compatible schemas and negative fixtures for secondary
artifacts; verify graph endpoints, origin consistency and aggregate page counts.
Reject contradictory evidence even when an attacker regenerates an unsigned
manifest. Keep legacy fixtures as compatibility evidence rather than rewriting
expected values from the implementation.

### P1 — Bind conditional reuse to resource identity

**Evidence:** `inspect_page` adds baseline conditional headers before fetching and
reuses a baseline page on any 304. `fetch_into` carries those headers across
same-origin redirects. Changed redirect destinations and changed baseline target
or normalization settings need explicit compatibility checks.

**Acceptance:** fixture-test a redirect whose destination changes while validators
are present; prevent reuse from a different final resource. Specify which target,
query-policy and schema differences invalidate a baseline. Test new metadata on
304 and prove stale links cannot enter the crawl frontier through invalid reuse.

### P2 — Broaden useful extraction and comparison

**Evidence:** HTML extraction resolves references against the response URL and has
no document `<base href>` handling. Comparison detects status, canonical, title,
indexability, description and fingerprints, plus structured-data disappearance;
it does not report arbitrary outgoing-link, hreflang or HTTP-Link changes.

**Acceptance:** support the first valid document base with same-origin crawl
checks applied after resolution; cover external bases and malformed markup.
Add deterministic link/relationship changes without treating anchor ordering as
content change. Keep all added findings and artifact fields version-compatible.

### P2 — Make truncation and failures actionable

**Evidence:** sitemap traversal caps its queue at 50 and members at 100,000; only
XML projection truncation is explicitly recorded. CLI help prints crawl options
for unrelated commands. `inspect` uses exit zero even for an HTTP error record.

**Acceptance:** expose each reached frontier/sitemap cap and distinguish bounded
coverage from complete traversal. Add command-specific help and a documented,
compatible machine outcome contract; consider an opt-in inspect failure threshold.
Test invalid options, redirects, HTTP errors and each coverage limit.

### P2 — Refresh distribution and workload qualification

**Acceptance:** qualify the final commit on the pinned runtime across Linux,
macOS and Windows; keep the full 10,000-page concurrency sweep and add dense-page
and multilingual fixtures. Validate extracted archives, README links and examples.
Document supported limits and runtime installation without assuming a sibling
checkout. Re-run ecosystem adapters against their actual consumer versions before
claiming interoperability beyond the supplied projection examples.

## Verification record

Local verification details and benchmark receipts are stored beside this review
under `artifacts/readiness-2026-09-22/`. Timing samples are observations, not an SLA
or a claim of universal speedup. The immutable oracle remains the compatibility
baseline; new corruption tests intentionally reject inputs previously accepted.

Verified implementation: `d76a67527331dcdbabb270ba6e743073103ccc6c`.

- Installed Kujo 1.4.0 on macOS: unchanged baseline 37/37 passed; final 38/38
  passed with the complete validation gate (checks, lint, formatting, immutable
  oracle, schemas, package install/frozen preview, generated docs and diff checks).
- All four installed-runtime scale runs completed 10,000 HTTP-200 pages at
  concurrency 1/4/8/16. Measured wall times were 189.02/76.04/65.64/51.20 seconds;
  peak RSS was about 308–355 MB. See [raw results](artifacts/readiness-2026-09-22/installed-10000.json).
  Concurrent compiler work means these are completion/resource observations, not
  paired before/after speed claims or cross-platform envelopes.
- A first intermediate large-artifact comparison exceeded its 30-second subprocess
  limit during concurrent compilation. The targeted recheck and final full gate
  passed after eliminating redundant self-comparison work; the failed run remains
  labeled as intermediate evidence, not qualification.
- Native archive generation, SHA-256 checking, extraction, and extracted `doctor`
  and `version` passed. Local links in changed documentation resolve. The package
  is a local review artifact, not a new tagged release.
- Cross-platform CI for the implementation is
  [run 35744513824](https://github.com/kujolang/siteprobe/actions/runs/35744513824).
  Its final status must be checked before claiming new Linux/Windows qualification.

Two unresolved findings were admitted to SignalBox (robots matching and metrics
path collision); their exact Capture/Signal IDs and successful retrieval checks
are in the [receipt](artifacts/readiness-2026-09-22/signalbox-receipt.json). No
duplicates were found. Completed changes, normal test results and speculative
feature work were excluded from SignalBox.

The exact pinned Kujo revision `2be1f04b89dbecd591ef1af0d68974c05586900e`
was rebuilt with `cargo build --release --locked`. The final full gate passed
38/38 tests on that runtime as well. The pinned archive smoke and 200-page
concurrency-4 smoke also passed. See [verification receipt](artifacts/readiness-2026-09-22/verification.json),
[pinned gate](artifacts/readiness-2026-09-22/pinned-validation.log) and
[test results](artifacts/readiness-2026-09-22/pinned-tests.json).
At recording, hosted Ubuntu qualification passed; hosted macOS and Windows were
still running. No new tagged release or universal enterprise certification is
implied by these results.

The September 22 backlog implementation and qualification are tracked in the [readiness completion record](../readiness-completion.md). This document preserves the historical review.
