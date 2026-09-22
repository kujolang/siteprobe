# Readiness backlog completion — September 22, 2026

This is the implementation and qualification record for the eight items in the
[September 22 review](audits/readiness-review-2026-09-22.md). SiteProbe is a bounded,
same-origin observer, not a universal crawler or an enterprise certification.

| Review item | Delivered behavior | Regression evidence |
| --- | --- | --- |
| 1. Robots | Matching groups merge; longest matching rule wins, allow wins ties; wildcard/end anchors and percent-encoding normalization; sitemap redirect hops obey policy. Inspect remains an explicit single-resource observation. | `robots_conformance_and_sitemap_policy`, existing redirect and unavailable-robots tests |
| 2. Metrics | Canonical parents and aliases are checked before requests/publication; output and existing run directories are protected, including baseline aliases and Windows path forms. Separate metrics files remain replaceable. | `metrics_paths_preserve_immutable_runs` |
| 3. Resources | Incremental staging reservations, retained-data estimates, early page-output abort and bounded offset indexes replace whole baseline/compare page retention. | `incremental_resource_budgets_and_cleanup`, artifacts above 8 MiB, workload receipts |
| 4. Contracts | Seven secondary schemas and cross-artifact origin, edge, redirect, sitemap, metadata, structured-data and aggregate consistency checks. Re-signing an inconsistent run does not make it valid. | `secondary_contracts_reject_resigned_inconsistency`, immutable oracle/signatures |
| 5. Conditional requests | Baseline target/query compatibility is checked before requests; validators follow only their final resource; 304 metadata is incorporated and changed redirects fetch fresh content. | `conditional_resource_identity_and_metadata` |
| 6. Documents/comparison | First valid HTML base resolves document references; response origin determines classification; relationship inventories compare independently of order. | `document_base_and_relationship_comparison` |
| 7. Coverage/CLI | Explicit frontier, sitemap seed/map/URL caps; machine-readable incomplete coverage; command help; opt-in inspect error exit with JSON retained. | `coverage_limits_help_and_inspect_outcomes` |
| 8. Qualification | Pinned runtime matrix, full 10,000-page concurrency sweep, dense/multilingual workloads, extracted-package validation and real consumer integration driver. | Native gate, CI, receipts below |

## Resource accounting

`--max-output-bytes` bounds published artifacts and aborts an oversized page spool
before final analysis. `--max-staging-bytes` defaults to four times that value,
capped at 1 GiB; explicit values are supported. Writes reserve their encoded size;
external sorts reserve three times their input for scratch work. Link wrapping,
reports and manifest generation also reserve capacity. Failure cleans unpublished
staging directories. No existing run is replaced.

`--max-retained-bytes` defaults to 256 MiB. It bounds conservative serialized-data
estimates: four times analyzed page JSON, a per-page allowance of one sixteenth of
the limit, and sitemap URL bookkeeping. Baseline and comparison indexes retain
URL/byte-offset entries, with a 16 MiB estimate limit per index, and read individual
rows on demand. Validation bounds each artifact read at 256 MiB and limits distinct
edge identities to one million. Dense workload receipts measure the implemented
limits against link-heavy pages with large JSON-LD.

These are application accounting limits, **not hard process RSS limits**. Native
HTTP decoding, tokenization, JSON parsing, serialization, allocator overhead and
concurrent response buffers require additional memory. Request bodies, tokenizer
structures, XML expansion, sort chunks and merge fan-in have their own native
bounds. A deployment needing an absolute memory/disk ceiling should also use OS
resource limits. Reported peak RSS is measured evidence for the specified fixture,
not a maximum for arbitrary sites.

## Compatibility and coverage

The immutable `tests/fixtures` oracle is unchanged. Contract identifiers remain
v1, with additional secondary schema validation. Robots corrections intentionally
change previously incorrect decisions. `inspect` still reports HTTP errors with
exit zero unless `--fail-on error` is requested. Unsupported fail thresholds are
rejected. The new budgets and discovery limits appear in configuration when
non-default; incomplete discovery emits `configuration.coverage.complete=false`
and sorted reasons. Absence of coverage fields in older artifacts is not proof of
a complete crawl. Sitemap caps also record specific truncation and error evidence.

Metrics destinations are compared conservatively without case sensitivity across
platforms. This may reject a distinct case-sensitive path but protects runs moved
between filesystems. Private-network crawling still requires explicit opt-in.

## Reproducible qualification

Use the exact revision in `KUJO_REVISION`, set `KUJO_BIN` to its absolute executable
path, then run:

```sh
bash scripts/validate.sh
"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16
"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 25 --workload dense --concurrency-levels 1,4
"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 50 --workload multilingual --concurrency-levels 1,4
"$KUJO_BIN" run scripts/verify_integrations.kujo -- ../contentgraph ../eval ../runledger
"$KUJO_BIN" run scripts/release.kujo -- "$KUJO_BIN" local .siteprobe/release-check
"$KUJO_BIN" run scripts/verify_release.kujo -- .siteprobe/release-check "$KUJO_BIN"
```

The integration driver executes actual ContentGraph build, Eval suite execution,
and isolated RunLedger start/note/test/finish/show operations. It records exact
consumer revisions and versions; it does not claim compatibility with untested
versions. See [integration examples](../examples/README.md) for the distinction
between custom projections and native consumer inputs.

Qualification receipts are stored in
[audit artifacts](audits/artifacts/readiness-completion-2026-09-22/).
The GitHub validation workflow qualifies the pinned runtime on Linux, macOS and
Windows, and runs the full sweep plus dense/multilingual workloads on Linux.
Timing comparisons across different machines or simultaneous jobs are not
controlled speedup measurements.

## Local results

The pinned-runtime gate passed all 46 tests, including the unchanged hash-verified
oracle. Relative documentation links, generated references, native package
checks and the extracted archive passed. Actual consumer qualification passed for
ContentGraph 0.3.0, Eval 2.0.0 and RunLedger 1.1.0 at the receipt revisions.

| Workload | Pages | Concurrency | Wall seconds | Peak RSS bytes | Published bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| standard | 10000 | 1 | 169.235 | 326025216 | 15455348 |
| standard | 10000 | 4 | 91.444 | 358789120 | 15456861 |
| standard | 10000 | 8 | 121.546 | 340807680 | 15460364 |
| standard | 10000 | 16 | 86.350 | 351866880 | 15462339 |
| dense | 25 | 1 | 42.544 | 445509632 | 25939911 |
| dense | 25 | 4 | 28.984 | 446676992 | 25939929 |
| multilingual | 50 | 1 | 1.032 | 28856320 | 92118 |
| multilingual | 50 | 4 | 1.386 | 29900800 | 92137 |

Original local workload measurement source: `5a1599be67278d64921d8a380467ab9f984d3cdf`. Final source qualification is recorded below.

The first hosted Windows run passed all 45 then-current tests but the new extracted
package check exposed a relative-path bug: canonical Windows verbatim prefixes
combined with artifact slash suffixes reported missing files. `absolute` now
normalizes those prefixes, including UNC paths. A 46th regression validates,
verifies and compares the immutable fixture using relative paths. The local gate
and extracted-package recheck pass; the replacement hosted run also passed this fix.

## Final qualification and handoff

All eight review items are complete. Final implementation commit
`293a0d3998ad314763c8045066f8c74cff132ad7` passed the pinned-runtime gate and
extracted-package validation on Linux, macOS and Windows in
[run 35754131008](https://github.com/kujolang/siteprobe/actions/runs/35754131008).
All 46 tests passed. Linux also passed the complete 10,000-page concurrency sweep
and dense/multilingual workloads. Local macOS 26.6.2 x86_64 passed the same gate
and archive checks; actual consumer integrations passed again after the path fix.
See the [qualification receipt](audits/artifacts/readiness-completion-2026-09-22/qualification.json)
and [individual local test results](audits/artifacts/readiness-completion-2026-09-22/native-tests.json).

Subsequent documentation-only commits record this evidence without changing the
qualified executable source. No backlog item remains open and no tagged release
was published. Future changes should preserve the pinned-runtime matrix, immutable
oracle, resource limits and explicit scope documented here.
