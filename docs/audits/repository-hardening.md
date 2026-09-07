# SiteProbe native Kujo rewrite and hardening — 2026-09-07

Status: native implementation and local verification complete; performance limitations remain explicit.

## Repository

- Repository: `kujolang/siteprobe`, branch `main`.
- Starting SHA: `3acf9b21b79728013d7ad21360e41d90619a1aff`.
- Ending implementation SHA: `84e5f2a9f509c833097072a515e02a0a82936e2e`.
- Report commit: resolve with `git log -1 --format=%H -- docs/audits/repository-hardening.md`.
- Authorized runtime dependency work: `kujolang/kujo`, starting SHA `9cedbf2f5ae5a0a9b126b055f4c9a6a58a2c23eb`, ending SHA `76760c43b8cc88ac8a4c3fa800802a517c61ed3d`.

SiteProbe crawls authorized sites with bounded, same-origin, robots-respecting GET requests and produces versioned evidence for humans, CI, ContentGraph, Eval, RunLedger and WebOps. All production behavior now lives in `src/siteprobe.kujo`, with explicit functions and labeled sections for CLI, shared transformations, robots policy, HTML projection, network orchestration, artifact analysis/verification and crawling; `src/main.kujo` is the small entrypoint. The removed Python implementation survives only as a frozen compatibility oracle under `tests/legacy/`. Python is a maintenance dependency for fixture tests and benchmarks, not a product runtime dependency.

The runtime addition provides generic parsing, bounded file/stream operations, pacing and transport mechanisms. SiteProbe policy, CLI, scheduling, analysis, comparison, reporting and artifact contracts remain Kujo source in this repository. No SiteProbe-specific implementation was hidden in Rust or another subprocess.

## Baseline and inspection

The [preceding hardening audit](2026-09-07-python-hardening.md) records the original nine-test baseline, reproduced defects and verified 24-test result (38.167 seconds). The native rewrite starts from that hardened implementation. A fresh rebaseline encountered five host process-creation errors (`EAGAIN`, macOS errno 35), distinguished from product assertion failures. No tests were disabled or timeouts increased to hide them.

Inspected all product source, launchers, schemas, examples, benchmark and test fixtures, package/release scripts, generated references, CI pins, security instructions and downstream artifact shapes. Reviewed public flags, exit codes, environment variables, deterministic serialization, conditional baselines, robots/redirect/DNS policy, retries/pacing, filesystem publication, signing, malformed external data and bounded output. There are no model prompts, MCP tools, provider credentials, persistent caches or conversational context in this product.

Kujo baseline `cargo check --locked` passed in 16.56 seconds with two existing vendored `tiny_http` warnings. Historical benchmark evidence remains labeled as Python implementation measurements. Final paired native measurements and verification receipts follow below; no speed claim is inferred from implementation language.

## Findings

| ID | Priority | Area | Finding | Evidence | Action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SP-N01 | P1 | Architecture | Every product command delegated to Python | Starting `src/main.kujo` and `src/siteprobe.py` | Implement all product behavior in Kujo; retain oracle only in tests; enforce source gate | Implemented |
| SP-N02 | P1 | Large artifacts | Existing generic whole-file reads capped valid artifacts at 8 MiB | Prior SP-A13 reproduction; new >8 MiB contract fixture | Bounded JSONL reads, streaming array projection, bounded JSON/text reads and digest handles | Implemented |
| SP-N03 | P0 | Transport | Ambient proxy resolution could bypass DNS-pinned socket routing | Local dead-proxy reproduction; runtime regression | Pinned/private-denying clients connect directly; unpinned proxy behavior unchanged | Implemented |
| SP-N04 | P0 | Crawl policy | Rewrite initially treated comment lines as robots group boundaries | Differential robots fixtures | Preserve group state across comments and decode encoded agent/rule identities | Fixed |
| SP-N05 | P1 | Validation | Large valid arrays exceeded the generic validator node budget | 20,000-finding and large-link regression fixture | Validate bounded batches with enclosing schemas; reject unsupported aggregate schema changes | Implemented |
| SP-N06 | P1 | Resources | Large sitemaps must not expand into unbounded memory or permit XML entities | Runtime gzip, DTD, namespace and malformed XML regressions | Stream compressed input with expansion/depth/text/match bounds and explicit incomplete-evidence diagnostics | Implemented |
| SP-N07 | P1 | Filesystem | Native migration must preserve hardened key, manifest and publication boundaries | Existing and new boundary fixtures | Bounded regular-file handles, no-follow reads, same-handle hashing, no-replace publication and cleanup | Implemented |
| SP-N08 | P2 | Output | Product subprocess capture capped valid large command output; check output was noisy | >1 MiB links output test; validation receipt files | Direct product stdout; full check evidence in files with concise PASS receipts | Implemented |
| SP-N10 | P1 | Performance | Duplicate grouping cloned growing nested maps | 1,000-page paired analysis benchmark | Use one map with structured composite identities | Fixed; identical result/page hashes |
| SP-N09 | P2 | Compatibility | HTML/URL edge cases can alter artifacts during parser migration | Frozen-oracle projection and full-run comparisons | Explicit compatibility transformations and negative tests | Verified |

| SP-N11 | P1 | Runtime overhead | Imported hot helpers repeatedly copy captured environments | Same 200-page release fixture: 15.390s modular, 3.329s one core | Keep authored core together with explicit function sections | Mitigated locally; runtime follow-up remains |
| SP-N12 | P2 | Collections | Repeated array concatenation, queue copying and closure capture do unnecessary work | Core source; stable-sort and complete-crawl regressions | Flatten sorted map values once; indexed crawl queue; one immutable mapper per crawl | Verified |
| SP-N13 | P1 | Sitemap queue | Only 50 maps were fetched but up to millions of pending entries could accumulate | Index projection limit multiplied by map fetch limit | Admit at most 50 unique same-origin maps, preserving BFS order | Verified first-50/duplicate/off-origin fixture |
| SP-N14 | P1 | Unicode compatibility | Rust regex word/space classes differ from Python | Combining mark, join-control, connector punctuation and ASCII 1c–1f oracle fixtures | Explicit letter/number/underscore words and legacy whitespace classes | Verified |

| SP-N15 | P1 | Large-page extraction | Growing text/link/image arrays copied accumulated entries | 1,000-link projection: 2.076s to 1.255s, identical output; initial 10,000-page attempt stopped during root extraction | Ordered map buffers materialized once, with 1,000-link/image ordering regression | Verified projection and complete 10,000-page crawl |

## Changes implemented

### Native product and compatibility

`src/main.kujo` dispatches directly to the native core. Launchers require only Kujo. `SITEPROBE_PYTHON` is used exclusively for development tests/benchmarks; doctor reports `implementation: kujo` and `python: null`. The frozen Python module is test-only and has just its repository-root lookup adjusted after relocation. Native tests exercise real product commands, rather than substituting oracle results.

`tests/test_native_contracts.py` compares complete deterministic run artifacts, pages and reports with the oracle and cross-verifies HMAC manifests in both directions. Additional tests cover a crawl with process execution denied, hostile proxy environment variables, large artifacts, complete large stdout, generic runtime capabilities and existing negative contracts. `tests/test_hardening.py` tests native mechanisms and policy; obsolete mocks of removed Python transport internals are replaced by native transport/file regressions.

### Bounded resource ownership

Per-page link analysis flushes records in batches of 64 instead of copying an ever-growing page-sized array. Page and link spools are externally sorted with at most 32 input files plus one output per merge. Adaptive fan-in accounts for large records; temporary runs are RAII-owned. Sitemap downloads and gzip expansion stream through bounded readers. JSONL transformations and hashes avoid whole-file buffering; validation reads page batches and retains only required aggregate indexes. Aggregate metadata, comparison indexes and findings remain bounded by explicit artifact/page limits; no unbounded cache or invalidation problem was introduced.

HTML uses a standards tokenizer with explicit input/event limits. XML rejects DTDs, unknown namespace prefixes, duplicate expanded attributes, invalid declarations and malformed root structure. Exhausted projection limits produce inspectable evidence errors. URL normalization rejects credentials and raw ASCII controls, preserves established path/query quoting, and uses a structured URL parser.

The sitemap pending queue now admits at most 50 unique eligible maps, instead of retaining every discovered index entry while processing only 50. Admission preserves the first-50 unique same-origin breadth-first traversal, including failed fetches. Crawl scheduling uses an indexed map to avoid copying a growing job array; a single mapper captures immutable crawl configuration. Sorted-row assembly flattens lexically ordered map values once, retaining stable ties. Regression tests cover ordering, duplicate map entries and off-origin entries.

HTML extraction now uses bounded insertion-order map buffers for text, links and images, then materializes arrays once. Seven-digit keys preserve source order under the one-million-event tokenizer limit. Internal/external projections use the same strategy. [Paired projection evidence](artifacts/html-buffers-benchmark.json) and [exact patch](artifacts/html-buffers-optimization.patch) record the measured improvement with identical output. The initial 10,000-page attempt was deliberately terminated after several minutes with zero emitted pages; it is not counted as a completed benchmark.

### Regression gates and developer experience

`scripts/validate.kujo` rejects production Python files and subprocess delegation, then checks/formats/lints every source module. It preserves stdout/stderr plus machine-readable receipts in `.siteprobe/verification/` and refuses truncated, cancelled or timed-out evidence. Release packaging includes all native modules and maintenance fixtures; runtime revision pins are updated together. README, security guidance, roadmap, agent instructions and generated API documentation describe actual native behavior.

## Performance and efficiency

The isolated 1,000-page analysis fixture measured **4.236s → 3.449s wall time** and **4.134s → 3.390s CPU** after replacing growing nested group maps with one map of group records. Result and rewritten-page SHA-256 hashes match exactly. This is one paired debug-build observation, not a release throughput claim. [Measurements](artifacts/native-analysis-benchmark.json), [fixture](artifacts/analysis-benchmark.kujo) and [exact optimization patch](artifacts/analysis-optimization.patch) preserve reproduction evidence. In a disposable checkout, reverse the patch to measure the earlier implementation, then reapply it; run `kujo run docs/audits/artifacts/analysis-benchmark.kujo -- <new-output-directory>` for each sample.

These are single local macOS samples from the same zero-delay HTTP fixture and runtime profile, with concurrency 4. The host was not isolated; values are observations, not statistical speed guarantees. Output sizes differ because JSON encoding and volatile run metadata differ; semantic equivalence is tested separately. The benchmark now rejects a run whose actual page count differs from the requested count.

| Implementation / stage | Pages | Wall seconds | CPU seconds | Peak RSS bytes | Artifact bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| [Python hardened oracle](artifacts/legacy-release-200.json) | 200 | 1.086 | 0.918 | 26,931,200 | 333,612 |
| [Native imported helpers](artifacts/native-modular-200.json) | 200 | 15.390 | 12.655 | 38,375,424 | 307,821 |
| [Native one core, before collection fixes](artifacts/native-core-200.json) | 200 | 3.329 | 2.693 | 35,946,496 | 307,742 |
| [Native final](artifacts/native-final-200.json) | 200 | 2.754 | 2.239 | 36,073,472 | 307,681 |
| [Python hardened oracle](artifacts/legacy-final-10000.json) | 10,000 | 41.818 | 40.579 | 70,762,496 | 16,757,193 |
| [Native before link batching](artifacts/native-unbatched-10000.json) | 10,000 | 270.912 | 223.663 | 363,913,216 | 15,463,634 |

Final bounded-batch run: **10,000 actual pages**, **173.732s wall**, **137.412s CPU**, **360,136,704 peak RSS bytes**, **15,461,256 artifact bytes**. [Receipt](artifacts/native-final-10000.json). This completed after the batch-size change; host variability prevents assigning the entire wall-time difference to that change. The deterministic resource improvement is that the per-page link spool buffer holds at most 64 rows.

Native execution remains slower and uses more memory than the Python oracle on this fixture. The rewrite meets the native-language requirement and preserves supported behavior; it is not presented as a speedup over Python. The final core is faster than the initial native layout, and the paired projection/grouping fixtures prove specific local improvements. A full native concurrency sweep and hosted performance qualification remain open.

CPU, wall time, peak resident memory and artifact bytes are relevant. There are no model calls or tokenized schemas; no token savings are claimed. Reports retain the established conservative four-bytes-per-token budget. Production subprocess count falls from one Python process per command to zero, supported by direct dispatch and the no-process-capability crawl regression. Runtime adds pinned `html5ever` and its lockfile dependencies; SiteProbe itself adds no package dependencies.

## Security and failure semantics

Reviewed URL/CLI/config input, DNS and redirect destinations, proxy environment, robots responses, retry amplification, HTTP bodies/headers, HTML/XML, baselines/manifests, signing keys, output paths, symlinks, temporary files, parallel pacing and terminal output. Retained deny-private default, explicit private override, same-origin checks, robots checks before every hop, fail-closed robots fetches, TLS verification, finite bounds, deterministic artifacts and immutable publication. Diagnostics strip terminal controls; detailed machine artifacts preserve required evidence.

Generic runtime capabilities gate network, filesystem read/write/delete and clock effects before execution, including secondary effects. Unix regular-file reads use no-follow handles and identity checks; Windows retains documented platform limitations. macOS publication is executed locally; Linux and Windows require the existing hosted matrix. No hosted CI result is claimed from local tests.

## Compatibility

- Public artifact APIs and v1 schema identifiers: unchanged.
- Documented commands and flags: preserved; malformed inputs fail explicitly. Exit 0 success, 1 verification/runtime/threshold failure, 2 invocation/operator error remain the contract.
- File formats: unchanged semantic JSON/JSONL/Markdown contracts; JSON whitespace can differ.
- Config and environment: no new required environment variables; Python override is maintenance-only. Doctor adds truthful native implementation information.
- Transport: DNS-pinned requests intentionally ignore ambient proxies to preserve actual destination enforcement. Unpinned Kujo HTTP users keep proxy behavior.
- Normalization: WHATWG host/base/dot-segment handling may differ for malformed or noncanonical URLs; raw controls and credentials remain rejected. Explicit parser resource limits fail visibly.
- Consumers: no ecosystem rewrite is required. Existing fixtures and first-party examples verify supported artifact behavior.

## Cross-repository follow-ups

The necessary Kujo runtime work was explicitly authorized by the user's instruction to finish the rewrite. It is committed separately and pinned by SiteProbe. Other sibling repositories were inspected only as needed; none were modified. Runtime revision `76760c43b8cc88ac8a4c3fa800802a517c61ed3d` is pushed and pinned. The prior native 8 MiB blocker is resolved: 11,187,780-byte pages and 3,608,944-byte complete links stdout validate and compare successfully.

### Existing Kujo VM loop-scope defect

A minimal function containing `for item in [1, 2] { let path := to_string(item); print(path) }` prints `1` then fails with `Cannot reassign immutable let binding: path` in the default VM; the interpreter prints `1` and `2`. This was reproduced in the inspected runtime and already exists as SignalBox capture `cap_2d935c8e-ed86-40f9-9833-85c5c000d5e9`. SiteProbe's validator uses a per-source helper function to preserve independent binding lifetimes. A compiler/runtime scope fix needs separate parity and closure-lifetime coverage; SiteProbe does not require it. No duplicate SignalBox capture was created.

### Kujo captured-environment performance

Affected repository: `kujolang/kujo`, pinned revision above. `src/module.rs` binds module exports to captured environments; `Interpreter::enter_captured_environment` clones environment maps at entry/return. A controlled same-function 200-page fixture measured 15.390s with imported helpers versus 3.329s with one core. SiteProbe mitigates this without changing public contracts. Remaining native CPU overhead is still measurable against Python; further Kujo optimization requires closure isolation, concurrency and public Rust interface compatibility tests. No speculative global HTTP cache or environment-sharing rewrite was introduced. SiteProbe does not require this follow-up to operate. The unresolved generic performance issue is recorded as SignalBox capture `cap_8191cde6-bacb-453c-9306-eb164ef8f897` and signal `sig_7a7f9734-746a-4117-a84c-95141fcee09e`; exact and conceptual retrieval passed. The existing loop-scope capture was deduplicated; completed rewrite and resolved size-limit work were not captured.

## Remaining work

P1, cross-repository: Kujo execution overhead remains a measured performance limitation; native crawling is slower than the hardened Python oracle on the local zero-delay fixture. P2, cross-repository: the existing Kujo VM loop-scope issue above remains open; it is outside the bounded runtime mechanisms needed for this migration. Platform-specific hosted checks are unexecuted locally and must not be represented as passing. Needs more evidence: further hot-path allocation and concurrency optimization, especially at the maximum crawl size. Not worth changing in this pass: unrelated styling, established v1 schemas, speculative caching or replacing proven parser dependencies. No cosmetic redesign or unrelated dependency cleanup was undertaken.

## Verification receipt

Commands below ran locally on macOS. `KUJO_BIN` is `/Users/robertdevore/2026/Kujolang/kujo-repos/kujo/target/release/kujo`; `SITEPROBE_PYTHON` is `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`. Rust commands used `CARGO_BUILD_JOBS=1` and `/Users/robertdevore/.cargo/bin/cargo`.

| Command | Result |
| --- | --- |
| `KUJO_BIN=... SITEPROBE_PYTHON=... bash scripts/validate.sh` | PASS: 35 tests in 35.658s, all source checks/lints/format checks, examples, package install/frozen install/publish preview, docs generation, four schemas and diff check |
| `kujo run scripts/release.kujo -- <runtime> macos-native-final .siteprobe/native-audit/release-complete` | PASS: archive and SHA-256 receipt |
| `KUJO_BIN=... SITEPROBE_PYTHON=/nonexistent/python bash <extracted>/siteprobe doctor` | PASS: native Kujo, Python null, zero production Python files |
| `python3 scripts/benchmark_fixture.py --pages 200 --concurrency-levels 4 --output .siteprobe/native-audit/native-final-200.json` | PASS: actual count asserted |
| `python3 scripts/benchmark_fixture.py --pages 10000 --concurrency-levels 4 --output .siteprobe/native-audit/native-final-batched-10000.json` | PASS: actual count asserted |
| `python3 scripts/benchmark_fixture.py --pages 10000 --concurrency-levels 4 --legacy --output .siteprobe/native-audit/legacy-final-10000.json` | PASS: actual count asserted |
| `kujo run docs/audits/artifacts/analysis-benchmark.kujo -- <new-directory>` | Paired before/after PASS, exact matching result/page hashes |
| `git apply --reverse --check docs/audits/artifacts/analysis-optimization.patch` and corresponding HTML-buffer patch | PASS; analysis final source hash verified |
| `cargo check --locked` | Baseline PASS, two pre-existing vendored warnings |
| `cargo test --locked --no-fail-fast -- --test-threads=1` | 2,554 passed; three inventory assertions initially failed and were fixed; 15 existing ignored tests |
| `cargo test --locked --test stdlib_reference_contract --test stdlib_reference_policy_contract --test unsafe_inventory_contract -- --test-threads=1` | All three corrected targets PASS |
| `cargo test --locked --lib interpreter::native_functions::web_data:: -- --test-threads=1` | PASS: ten boundary tests, including final malformed-pacer-state guard |
| `cargo fmt --all -- --check` | PASS |
| `cargo clippy --locked --all-targets --all-features -- -D warnings` | PASS; vendored dependency warnings remain |
| `cargo audit --json` | Zero vulnerabilities/warnings; 583 dependencies; advisory snapshot 2026-09-02 |
| `cargo build --release --locked` | PASS, 65m00s on this resource-constrained host; release build preceded the final pacer-state guard, which passed the final debug unit tests and all-feature clippy |

The broad Rust invocation did not exit successfully as a whole: its three failing inventory targets were corrected and rerun successfully. No test was disabled or weakened. Hosted Linux/Windows validation is not claimed. Incorrect exploratory formatter invocations (`fmt`, and multiple files passed to `format`) were rejected; the supported per-file format checks in the final gate pass.

[Exact SiteProbe commands and runtime log hashes](artifacts/verification.json), [test output](artifacts/native-tests.log), [validation receipt](artifacts/native-validation.log), [large-artifact evidence](artifacts/native-large-artifacts.json), [release smoke](artifacts/native-release-smoke.json). Full local development logs remain in `.siteprobe/native-audit/`, `.siteprobe/verification/` and the runtime log paths recorded in the receipt.
