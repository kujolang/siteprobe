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
The complete migrated `bash scripts/validate.sh` and native source ZIP
creation/extraction checks passed locally; receipts include all 37 tests, including
child-argument isolation and bounded benchmark history. The final successful platform receipt
is recorded below.

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

## Final implementation and local receipt

Implementation SHA: `88d007faccfa7b86bd46c96a811b0253a37d607c`.
All six tracked Python source files are removed. All 36 prior cases remain, with
one additional bounded-benchmark regression: **37 native tests pass**. Product
source and `KUJO_REVISION` are unchanged. Source package creation and native
extracted doctor/version verification passed; a bad checksum was rejected before
extraction. The source ZIP contains the complete native maintenance suite and no
Python files. The published v0.3.0 release is not retagged or replaced.

Exact local commands:

```sh
bash scripts/validate.sh
../kujo/target/release/kujo run tests/siteprobe_tests.kujo -- benchmark_fixture
../kujo/target/release/kujo run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16 --output .siteprobe/verification/kujo-maintenance-10000.json
../kujo/target/release/kujo run scripts/release.kujo -- ../kujo/target/release/kujo local-verification .siteprobe/verification/maintenance-package-portable
../kujo/target/release/kujo run scripts/verify_release.kujo -- .siteprobe/verification/maintenance-package-portable ../kujo/target/release/kujo
```

The validation gate also rejects an intentionally introduced nested
`tests/fixtures/ratchet-probe.py` with exit 1 and its exact path; the temporary file
was removed afterward. Invalid benchmark bounds, fractional page counts and
incomplete options were rejected. A concurrent local attempt encountered host
process exhaustion (errno 35); it was not counted as passing. Subsequent complete
local verification passed without changing any timeout.

Full local native fixture results (10,000 requested and 10,000 HTTP 200 pages per
row; final completed receipt, not the interrupted attempt):

| Concurrency | Wall seconds | CPU seconds | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| 1 | 110.863631 | 87.759497 | 348217344 |
| 4 | 56.146164 | 101.803370 | 352063488 |
| 8 | 46.620353 | 114.277230 | 355299328 |
| 16 | 39.149969 | 114.995030 | 359596032 |

These are completion/resource measurements of the new fixture, not a product
speed comparison against historical Python-hosted benchmarks.

## Website wording and retained follow-up

The requested maintenance-language aside was removed and deployed on both
https://kujolang.ai/ecosystem/siteprobe/ and
https://docs.kujolang.ai/tools/siteprobe/. Marketing source `3567fd8` deployed via
run `34220310866`; docs source `5630513` passed run `34220314179` and its exact
artifact published at gh-pages `6d186de` via run `34222060682`. Both live pages were
checked for the removal and retained 0.3.0 release guidance. No website templates,
URLs, images, schemas or crawler policies changed.

The runtime argument-inheritance follow-up is recorded for review in SignalBox:
Capture `cap_d80d41dd-1bd8-4670-914e-8237bb60cac8`, Signal
`sig_c6941564-5ce6-4ea3-9a34-e0da96bfed48`, project `kujo`. Exact and concept retrieval
passed; no duplicates were found. Completed migration summaries and resolved
fixture issues were not captured. SiteProbe's caller isolation is complete; the
runtime follow-up is not a blocker for this repository.

## Windows maintenance portability

Run `34223837180` passed Linux/macOS, including the full Linux sweep, but failed
32 Windows tests: Rust canonicalization returns verbatim paths (`\\?\...`),
which reject the slash suffixes used by the maintenance harness. The historical
harness supplied ordinary absolute paths. `tests/support.kujo::fixture_path` now
converts canonical drive/UNC fixture paths to their ordinary absolute equivalents;
the runner, benchmark, frozen-oracle invocation and package verifier share it.
The same complete 37-test local gate and extracted package checks passed afterward.
No assertion, product path implementation or timeout was weakened.

## Final hosted qualification and remaining work

[Run 34225149198](https://github.com/kujolang/siteprobe/actions/runs/34225149198)
passed at implementation `88d007faccfa7b86bd46c96a811b0253a37d607c`:

| Platform | Full validation | Native tests | Generated artifacts |
| --- | --- | --- | --- |
| Ubuntu | PASS | 37/37 | Current |
| macOS | PASS | 37/37 | Current |
| Windows | PASS | 37/37 | Current |

The hosted commands were `cargo build --release --manifest-path kujo/Cargo.toml`,
`bash scripts/validate.sh` (Unix), `./scripts/validate.ps1` (Windows), and
`git diff --exit-code -- kujo.lock docs/generated`. Linux additionally passed:

```sh
../kujo/target/release/kujo run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16 --output .siteprobe/verification/native-concurrency-10000.json
```

Every benchmark row recorded 10,000 pages and 10,000 successful HTTP 200 responses.
Wall seconds at concurrency 1/4/8/16 were 75.854112 / 32.766908 / 32.744080 /
33.317114. Full CPU/RSS/output metrics are retained in `ci-10000.json`; these are
qualification measurements, not an old/new product speed claim. The native test
receipts for all three platforms and compact job/step receipt are retained beside
it. Downloaded receipts were independently checked for 37 passed tests, zero
failures and all four exact benchmark counts.

No unresolved SiteProbe migration blocker remains. The Kujo runtime argument
inheritance follow-up above is independent and already isolated by SiteProbe.
Published release history remains unchanged; this migration is on unreleased main.
