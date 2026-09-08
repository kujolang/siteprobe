# Native Kujo maintenance migration — 2026-09-08

Repository: `kujolang/siteprobe`, branch `main`. Starting SHA:
`71a2071b60174cf755084e167ccc392710a104b8` (v0.3.0).
This is an unreleased maintenance change; the published v0.3.0 tag is unchanged.

## Scope and implementation

The CLI was already native Kujo. This change migrates the remaining maintenance
runner, loopback HTTP fixtures, benchmark harness, JSON schema checks and extracted
source-package verification to Kujo. Python programs and Python setup in both
workflows are removed. Public CLI behavior, schemas, runtime pin, package version
and product source remain unchanged, including the established doctor JSON fields.

| Finding | Action | Evidence |
| --- | --- | --- |
| Maintenance runner delegated to unittest | 37 native tests in unit/crawl/contract modules (36 preserved plus bounded fixture history) with concise receipts and selective execution | `tests/siteprobe_tests.kujo`, `tests/support.kujo` |
| Fixture server and benchmark required another interpreter | Loopback-only Kujo TCP task; exact routes, gzip, retries, ETags, pacing and three-socket concurrency barrier | `tests/fixture_server.kujo`, `scripts/benchmark.kujo` |
| Compatibility depended on executing the old implementation | Preserve immutable signed run, 13 parser projections, report and 100 seeded malformed URLs from the original oracle | `tests/fixtures/oracle-provenance.json` |
| Packaging depended on host ZIP libraries | Native bounded/safe unzip, digest checks and extracted doctor/version commands | `scripts/verify_release.kujo` |
| Child validator inherited its parent's script arguments | Deny `KUJO_SCRIPT_ARGS` at the process boundary | `scripts/validate.kujo` |

The fixture binds its listener before starting the worker, uses a dedicated private
loopback port, bounds request/control data, and stops through an explicit control
request. The concurrency barrier responds only after receiving all three sockets;
it cannot pass with sequential requests. Slow responses deliberately model timeout
behavior. Benchmark counts require every configured page to return HTTP 200.

Native large-fixture construction streams batches rather than repeatedly copying
large arrays. It still tests 800 pages exceeding 8 MiB, 20,000 findings, 10,000 links,
complete stdout exceeding 1 MiB, 9 MiB JSONL wrapping and no-replace collisions.
There are no relaxed assertions, reduced sample counts or raised timeout limits.

## Compatibility evidence

The original oracle is retained in git at the starting SHA. Its SHA-256, capture
origin and each immutable fixture digest are recorded in the provenance JSON.
Fixtures are byte-preserved across Git platforms through their `.gitattributes`.
The original signed run is validated and verified without modification. A new
native crawl is compared against all original artifacts, with only the dynamic
fixture origin, documented URL-derived finding IDs and robots-text fingerprint
rebased. The new signature is also checked against the HMAC contract independently
of the product verifier. Parser expectations are never generated from the code
under test.

All previous test groups are retained: fixture/integration contracts; inspect and
normalization; credentials and bounds; seeded malformed URLs; retries, cycles and
read-only requests; deterministic artifacts; output budgets; fail-on/count checks;
symlinks; signatures/query policy/pacing/conditional reuse; gzip expansion; stable
sorts and cleanup; terminal controls; nonfinite inputs; oversized/empty manifests;
atomic publication; key bounds; report budgets; charset behavior; capability
isolation; robots groups/encoding; large HTML; wide sitemaps; real concurrency;
full oracle compatibility; large artifacts; secondary capabilities; proxy-free
restricted crawling.

The documented `scripts/benchmark.kujo` interface and benchmark v2 schema remain.
The historical `--legacy` Python benchmarking mode and `.py` entrypoints are removed;
use the original release tag if reproducing historical interpreter measurements.
Tests and source ZIPs now carry frozen data instead of an executable legacy oracle.
The runtime lacks symlink creation and OS identification primitives, so the Kujo
harness retains minimal `ln`/PowerShell and `uname` calls for those platform effects.
No fixture, assertion, benchmark or archive-processing logic delegates to them.

## Verification

The unchanged baseline `bash scripts/validate.sh` passed, including all 36 original
tests, source checks/format/lint, package commands, generated docs and JSON schemas.
Its full receipt is retained under `artifacts/kujo-maintenance-2026-09-08/`.
The migrated suite also passed all 36 tests before full gate/package qualification.
The complete migrated `bash scripts/validate.sh` and native source ZIP
creation/extraction checks passed locally; receipts include all 36 tests, including
child-argument isolation. Platform CI and the complete benchmark sweep are recorded
in the final receipt after their runs complete.

No product performance improvement is claimed. Benchmark v2 preserves wall/CPU/RSS,
throughput and output-byte evidence, but changing the fixture server makes old/new
wall times unsuitable as a product speed comparison without a controlled study.

## Cross-repository follow-up

Kujo runtime `src/main.rs` only sets `KUJO_SCRIPT_ARGS` for nonempty script arguments;
`src/builtins.rs::get_args` trusts an inherited value. A nested argument-free script
can therefore see its parent's arguments. SiteProbe now denies that variable when
spawning validation steps. The runtime should clear or explicitly override it on
all script launches and regression-test parent/child argument isolation. No runtime
change is required for this repository's fix, and no sibling repository was edited.

The full 10,000-page migration attempt exposed request-history accumulation in
the new benchmark fixture: after 17,421 requests the fixture task used about 97%
of one CPU while the crawler waited. The incomplete attempt was stopped and is
not qualification evidence. Benchmark mode now keeps only a scalar request count;
small contract fixtures retain their necessary request evidence. A regression test
and benchmark assertion lock in empty path/timestamp history in benchmark mode.
