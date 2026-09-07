# SiteProbe native Kujo rewrite and hardening — 2026-09-07

Status: native implementation complete. The follow-up section records the runtime, concurrency and Windows corrections; earlier measurements remain historical evidence.

## Repository

- Repository: `kujolang/siteprobe`, branch `main`.
- Starting SHA: `3acf9b21b79728013d7ad21360e41d90619a1aff`.
- Ending implementation SHA: `83e9bf2f54d9d608052a7981390de6ec899e58fa`.
- Report commit: resolve with `git log -1 --format=%H -- docs/audits/repository-hardening.md`.
- Authorized runtime dependency work: `kujolang/kujo`, starting SHA `9cedbf2f5ae5a0a9b126b055f4c9a6a58a2c23eb`, ending SHA `5dcbfcda2e48c2fe56dd2a4ecdb2d5947e18ff59` (production runtime pin `2be1f04b89dbecd591ef1af0d68974c05586900e`; later commit changes tests/CI only).

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

| SP-N11 | P1 | Runtime overhead | Imported hot helpers repeatedly copy captured environments | Same 200-page release fixture: 15.390s modular, 3.329s one core | Keep authored core together with explicit function sections | Mitigated in original rewrite; redundant return cloning fixed in SP-R03 |
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

Native execution remains slower and uses more memory than the Python oracle on this fixture. The rewrite meets the native-language requirement and preserves supported behavior; it is not presented as a speedup over Python. The final core is faster than the initial native layout, and the paired projection/grouping fixtures prove specific local improvements. The complete follow-up below now supplies the native concurrency sweep and hosted platform qualification; this paragraph records the original measurement limitations.

CPU, wall time, peak resident memory and artifact bytes are relevant. There are no model calls or tokenized schemas; no token savings are claimed. Reports retain the established conservative four-bytes-per-token budget. Production subprocess count falls from one Python process per command to zero, supported by direct dispatch and the no-process-capability crawl regression. Runtime adds pinned `html5ever` and its lockfile dependencies; SiteProbe itself adds no package dependencies.

## Security and failure semantics

Reviewed URL/CLI/config input, DNS and redirect destinations, proxy environment, robots responses, retry amplification, HTTP bodies/headers, HTML/XML, baselines/manifests, signing keys, output paths, symlinks, temporary files, parallel pacing and terminal output. Retained deny-private default, explicit private override, same-origin checks, robots checks before every hop, fail-closed robots fetches, TLS verification, finite bounds, deterministic artifacts and immutable publication. Diagnostics strip terminal controls; detailed machine artifacts preserve required evidence.

Generic runtime capabilities gate network, filesystem read/write/delete and clock effects before execution, including secondary effects. Unix regular-file reads use no-follow handles and identity checks; Windows retains documented platform limitations. The initial audit exercised macOS publication locally. Subsequent hosted matrix evidence is recorded in the follow-up; local results are not substituted for platform qualification.

## Compatibility

- Public artifact APIs and v1 schema identifiers: unchanged.
- Documented commands and flags: preserved; malformed inputs fail explicitly. Exit 0 success, 1 verification/runtime/threshold failure, 2 invocation/operator error remain the contract.
- File formats: unchanged semantic JSON/JSONL/Markdown contracts; JSON whitespace can differ.
- Config and environment: no new required environment variables; Python override is maintenance-only. Doctor adds truthful native implementation information.
- Transport: DNS-pinned requests intentionally ignore ambient proxies to preserve actual destination enforcement. Unpinned Kujo HTTP users keep proxy behavior.
- Normalization: WHATWG host/base/dot-segment handling may differ for malformed or noncanonical URLs; raw controls and credentials remain rejected. Explicit parser resource limits fail visibly.
- Consumers: no ecosystem rewrite is required. Existing fixtures and first-party examples verify supported artifact behavior.

## Cross-repository follow-ups

The necessary Kujo runtime work was explicitly authorized by the user's instruction to finish the rewrite. It is committed separately and pinned by SiteProbe. Other sibling repositories were inspected only as needed; none were modified. Runtime revision `76760c43b8cc88ac8a4c3fa800802a517c61ed3d` was the original rewrite pin; the final follow-up pin is `2be1f04b89dbecd591ef1af0d68974c05586900e`. The prior native 8 MiB blocker is resolved: 11,187,780-byte pages and 3,608,944-byte complete links stdout validate and compare successfully.

### Kujo runtime follow-ups

The original VM loop-declaration failure and redundant captured-environment copies
are corrected in the follow-up below, with parity, closure-snapshot, immutable
capture and worker-isolation regression coverage. The original one-core versus
imported-helper fixture (3.329s versus 15.390s) remains historical evidence; the
new paired imported-call and crawl measurements are recorded below. Entry
snapshots remain intentional isolation, not an unresolved request to share state.

Historical SignalBox items `cap_2d935c8e-ed86-40f9-9833-85c5c000d5e9`,
`cap_8191cde6-bacb-453c-9306-eb164ef8f897` and
`sig_7a7f9734-746a-4117-a84c-95141fcee09e` identify the original findings.
No new duplicate or completed-work capture is warranted. Their resolution evidence
belongs in this audit and the updated Strata state, without an unauthorized
SignalBox disposition change.

## Remaining work

The previously recorded source fixes and full native concurrency sweep are complete.
Final hosted qualification passed on Linux, macOS and Windows; receipts follow below.
No additional high-confidence product change is currently justified. Further
optimization must preserve capture isolation and be measured against representative
fixtures; equal performance to another language on different hosts is not a contract.
Unrelated styling and speculative architecture changes are not worth changing.

## Original rewrite verification receipt (historical)

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

The broad Rust invocation did not exit successfully as a whole: its three failing inventory targets were corrected and rerun successfully. No test was disabled or weakened. This original receipt did not qualify Linux/Windows; the final follow-up matrix below does. Incorrect exploratory formatter invocations (`fmt`, and multiple files passed to `format`) were rejected; the supported per-file format checks in the final gate pass.

[Exact SiteProbe commands and runtime log hashes](artifacts/verification.json), [test output](artifacts/native-tests.log), [validation receipt](artifacts/native-validation.log), [large-artifact evidence](artifacts/native-large-artifacts.json), [release smoke](artifacts/native-release-smoke.json). Full local development logs remain in `.siteprobe/native-audit/`, `.siteprobe/verification/` and the runtime log paths recorded in the receipt.


## Remaining-item follow-up — 2026-09-07

Starting revisions: SiteProbe `a83530a2e434d64110868db97b0e7ccb9a521a0b`,
Kujo `76760c43b8cc88ac8a4c3fa800802a517c61ed3d`. The user explicitly authorized
fixing the remaining runtime items. This section supersedes earlier open-item
status while preserving the original audit and measurements.

Final SiteProbe implementation: `83e9bf2f54d9d608052a7981390de6ec899e58fa`.
Production runtime pin: `2be1f04b89dbecd591ef1af0d68974c05586900e`.
Kujo follow-up tip: `5dcbfcda2e48c2fe56dd2a4ecdb2d5947e18ff59`; its only
additional changes are a feature-aware test, a CI check and changelog entry.
Production `src/` is identical to the pinned revision.

### Findings and implemented corrections

| ID | Priority | Area | Finding / evidence | Action | Status |
| --- | --- | --- | --- | --- | --- |
| SP-R01 | P1 | VM scope | Repeated immutable declarations fail on iteration two; root loop scopes leak; for-continue skips increment | Distinguish declaration from assignment, fresh root-loop scopes, unwind break/continue/return; preserve function-local JIT eligibility | Fixed; parity regressions |
| SP-R02 | P1 | CPU | Every regex invocation recompiles expensive Unicode classes | Bounded eight-entry compiled-program LRU, compile outside lock, skip keys over 4096 bytes | Fixed; semantics/bounds/concurrency tests |
| SP-R03 | P1 | Capture ownership | Captured calls clone again on return; worker construction duplicates builtins and loses binding metadata | Move completed environment back; construct isolated workers with their full supplied snapshot | Fixed; immutable capture and worker-isolation tests |
| SP-R04 | P1 | Concurrency | Synchronous mapper takes parallel_map's sequential branch | Native async mapper; three-request barrier proves overlap | Fixed; native fixture passes all platforms |
| SP-R05 | P0 | Windows publication | Rust rename replaces an existing empty destination directory | MoveFileExW flags zero, owned UTF-16 buffers, NUL rejection; reviewed unsafe inventory updated | Fixed; Windows boundary fixture passes |
| SP-R06 | P2 | Platform fixtures | CRLF checkout fails formatting; locale decoding corrupts UTF-8; canonical Windows source path leaks into generated reference | LF attributes, explicit UTF-8, normalize path_absolute("src") | Fixed; all platform gates and exact docs check pass |
| SP-R07 | P2 | CI hygiene | Baseline artifact guard reports seven missing ignore rules; generated TODO references drift after source edits | Synchronize canonical ignore rules and regenerate inventories | Fixed; exact gates pass |
| SP-R08 | P1 | Exceptions | Caught loop exception leaves shadowed value 1 instead of outer 99 | Save environment depth in handler frames and unwind on throw, including cross-function propagation | Fixed; 110-test parity suite |
| SP-R09 | P2 | Fixture coverage | Binary fixture's snapshot expects the old early VM failure | Avoid builtin name collisions, assert intended missing-file error, explicitly authorize intended overwrites, restore all ten successful cases | Fixed; VM/interpreter output identical, 150/150 fixtures |
| SP-R10 | P2 | Build profiles | New JIT eligibility inspection does not compile without runtime-jit | Feature-gate only JIT introspection; retain behavioral parity assertions in every profile; add non-JIT CI run | Hosted non-JIT check passes |

| Change | Root cause, implementation and affected regression files |
| --- | --- |
| VM declarations/control flow | Kujo `src/{bytecode,compiler,vm,jit}.rs`: `DefineLocal` initializes a fresh binding while `StoreLocal` retains immutable assignment guards. Runtime scopes apply where function-local slots do not already encode identity. Nested execution, break/continue/return and exception frames unwind their owned scopes. `tests/vm_interpreter_parity_surfaces.rs` covers loops, snapshots, JIT eligibility and exceptions. |
| Regex reuse | Kujo `src/builtins.rs`, inline `regex_cache_regressions`, `docs/STANDARD_LIBRARY.md`: immutable Arc programs, complete pattern/flags key, negative-cache invalid patterns, concurrent-miss recheck, matching outside lock. Tests cover Unicode, flags, all four APIs, replacements, invalid/oversize patterns and concurrent churn. |
| Capture ownership/isolation | Kujo `src/interpreter/mod.rs`, `tests/interpreter_tests.rs`: private supplied-environment constructor avoids registering then replacing builtins; successful synchronous return moves the completed environment. Entry snapshot and worker binding metadata remain intact. |
| Windows publication | Kujo `src/interpreter/native_functions/web_data.rs`, existing publication tests, `tests/unsafe_inventory_contract.rs`, generated inventory: no-replace directory publication via Windows API; exact unsafe budget 66→67 with explicit safety rationale. No dependency added. |
| Native scheduling/platform behavior | SiteProbe `src/siteprobe.kujo`, `tests/test_{siteprobe,native_contracts,hardening}.py`, `tests/siteprobe_tests.kujo`, `.gitattributes`, `scripts/generate_docs.kujo`: async mapper, overlap regression, UTF-8 fixture transport and canonical path normalization. |
| Qualification | SiteProbe `scripts/benchmark_fixture.py`, `.github/workflows/{validate,release}.yml`, `KUJO_REVISION`, `README.md`; Kujo `.github/workflows/ci-release-gate.yml`, `tests/test_binary_files.{kujo,out}`: immutable runtime pins, all-platform evidence, successful-page checks, non-JIT parity and complete binary fixtures. |

### Measured impact

Same local macOS host and debug profile, 1,000 operations per focused fixture.
Before is the preserved starting-runtime binary; after includes regex and capture
ownership changes. Host load was not isolated. These are paired observations,
not statistical throughput guarantees or cross-language claims.

| Fixture | Before CPU / wall seconds | After CPU / wall seconds | Equivalent result |
| --- | --- | --- | --- |
| Unicode regex find-all | 40.708578 / 79.956073 | 1.757863 / 2.017578 | checksum 4000 |
| Imported increment function | 1.406546 / 1.414749 | 1.093009 / 1.109188 | checksum 500500 |
| Native 200-page crawl, concurrency 4 | 18.268546 / 9.957309 | 7.072499 / 5.151864 | 200 pages each; semantic contracts separately tested |

The crawl used identical async SiteProbe source on both runtimes. Peak RSS was
53,964,800→50,880,512 bytes; artifact bytes 307,853→307,820 differ because ports,
timestamps and measured metadata vary. Reproduce focused calls with
`kujo run docs/audits/artifacts/runtime-regex-benchmark.kujo` and
`kujo run docs/audits/artifacts/runtime-module-benchmark.kujo` against each runtime.
Exact data: `artifacts/runtime-{regex,module,native-200}-{before,after}.json`.

The final immutable Linux release build in
[SiteProbe run 34119233850](https://github.com/kujolang/siteprobe/actions/runs/34119233850)
compiled the final pinned runtime and passed **10,000 HTTP 200 pages at every
concurrency setting**. Data: [final sweep](artifacts/runtime-final-hosted-native-10000.json),
Actions artifact `10017772091`.

| Concurrency | Wall seconds | CPU seconds | Peak RSS bytes | Pages/second |
| --- | ---: | ---: | ---: | ---: |
| 1 | 77.122579 | 75.586659 | 461074432 | 129.664 |
| 4 | 36.324985 | 109.241751 | 471027712 | 275.293 |
| 8 | 35.694520 | 113.473040 | 493051904 | 280.155 |
| 16 | 35.924900 | 118.873467 | 525721600 | 278.358 |

These compare concurrency on one immutable build, not against historical
macOS/Python measurements. More workers consume more CPU/memory; the existing
default of four is preserved. The earlier immutable 33508db sweep remains in
`runtime-hosted-native-10000.json`. The local development sweep in
`runtime-development-native-10000.json` is only functional stress evidence:
compilation replaced the debug binary between levels and the host was shared.
It is not used for an immutable-revision performance claim.

The regex cache retains at most eight keys of at most 4096 bytes, subject to the
existing compiled-program size limit; it never retains inputs or replacements.
Capture entry snapshots remain necessary isolation. No dependency was added and
no token/context savings are claimed. SiteProbe continues to emit concise
verification receipts while preserving complete logs. No speculative HTTP cache,
shared mutable closure environment or timing threshold was introduced.

### Security and compatibility

The reviewed boundaries remain URL/DNS/redirect/robots input, hostile network
content, finite resource limits, immutable filesystem publication, worker state,
CLI output and exception cleanup. Windows publication now enforces its established
no-replace contract ([Microsoft API contract](https://learn.microsoft.com/en-us/windows/win32/fileio/moving-directories)).
The three-platform native boundary fixtures include this regression.

SiteProbe public APIs, CLI flags/exit codes, file formats, schemas, config and
environment contracts are unchanged. Concurrency now honors the existing setting
while preserving result order, shared origin pacing and isolated state. Immutable
assignment still fails. The necessary Kujo runtime changes are separately committed
and pinned; no other sibling product requires modification.

Kujo's Rust-exposed `OpCode` enum gains `DefineLocal`: external exhaustive Rust
matches would need that variant. No first-party consumer outside runtime/worktrees
was found by Rust import/reference search. This source-level compatibility caveat
is explicit; no supported persisted-bytecode format is changed.

### Stable regression gates

Every platform builds the pinned runtime and runs the full native gate. Linux
also runs the 10,000-page sweep at 1/4/8/16, asserting exact page counts and HTTP
200 success for every page. The fixture's accept queue is 32 to accommodate the
supported maximum batch; it no longer artificially throttles at Python's default
five. Timings are evidence, not flaky budgets. All platforms upload receipts and
logs on both success and failure. Runtime CI covers parity with and without JIT,
immutable captures, independent workers, regex bounds/churn, generated references
and the exact unsafe-site inventory. No arbitrary sleeps, weaker assertions,
retry masking or timeout increases were added.

### Verification receipt

Environment: macOS local Rust commands use `CARGO_BUILD_JOBS=1`,
`SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`, and cargo at
`/Users/robertdevore/.cargo/bin/cargo`. SiteProbe uses the sibling release binary
and `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3` via `KUJO_BIN`
and `SITEPROBE_PYTHON`. Hosted commands and full logs are preserved in the linked
immutable Actions runs and uploaded artifacts.

| Exact command / gate | Result |
| --- | --- |
| `cargo test --locked --no-fail-fast -- --test-threads=1` at production 2be1f04 | PASS: 2,569 tests across 72 Cargo targets; zero failed, 15 existing ignored. Nested subprocess result lines are not double-counted. [Structured receipt](artifacts/remaining-rust-tests.json). |
| `cargo test --locked --test vm_interpreter_parity_surfaces --test generated_artifact_freshness_contract -- --test-threads=1` | PASS: 110 parity and three freshness tests. |
| `target/debug/kujo test` | PASS: 150/150 fixtures, six existing skipped, zero expected failures, zero interpreter fallbacks. |
| `cargo fmt --check` | PASS in final hosted runtime CI. |
| `cargo clippy --all-targets --all-features -- -D warnings` | PASS in final hosted runtime CI; existing vendored warnings unchanged. |
| `cargo test --no-default-features --features runtime-archive,runtime-image --test vm_interpreter_parity_surfaces` | PASS in final hosted parity job, including all behavioral assertions with JIT disabled. |
| `bash scripts/release_gate.sh` | PASS at production 2be1f04: [run 34118964919](https://github.com/kujolang/kujo/actions/runs/34118964919), and final tip 5dcbfcd: [run 34120679077](https://github.com/kujolang/kujo/actions/runs/34120679077). |
| `bash scripts/validate.sh` (Unix), `./scripts/validate.ps1` (Windows) at SiteProbe 83e9bf2 / pinned Kujo 2be1f04 | PASS on Linux, macOS, Windows: 36 tests respectively in 9.591s / 43.872s / 23.657s, source checks/lints/format, examples, package install/frozen install/publish preview, docs generation and four schemas. |
| `git diff --exit-code -- kujo.lock docs/generated` | PASS on all three platforms, including canonical Windows paths. |
| `python scripts/benchmark_fixture.py --pages 10000 --concurrency-levels 1,4,8,16 --output .siteprobe/verification/native-concurrency-10000.json` | PASS on final Linux build: four runs, each 10,000/10,000 successful pages. |
| `cargo build --release --locked` on local macOS | PASS: 29m 18s with normal release optimization; binary SHA-256 in provenance receipt. |
| `kujo run .siteprobe/native-audit/remaining-exception-scope.kujo` and `./siteprobe doctor` | PASS on final local release: outer value 99, implementation kujo, Python null. |
| `KUJO_BIN=... SITEPROBE_PYTHON=... bash scripts/validate.sh` on final local release | PASS: 36 tests in 33.837s and the complete native gate; [test log](artifacts/remaining-final-local-tests.log), [validation log](artifacts/remaining-final-local-validation.log). |

Final native test logs are `artifacts/remaining-final-{linux,macos,windows}-tests.log`.
[Final provenance and command receipts](artifacts/remaining-verification.json) record
all 141 hosted commands: exit zero, with no truncated, timed-out or cancelled result.
The fixture restores all ten binary-file cases in both runtimes; its output is
`artifacts/remaining-binary-fixture.log`. Full local logs are retained under
`/tmp/siteprobe-remaining-*.log`; the concise provenance receipt records hashes.

### Baseline failures and superseded attempts

Initial macOS process/link failures were host errno 35, not waived assertions.
A debug-profile SiteProbe large-artifact run exceeded the existing 120-second
fixture limit; release-profile qualification passed without increasing it.
Windows runs 34097403988 and 34112572944 exposed CRLF, no-replace and UTF-8 defects;
34114991046 passed all 36 tests but failed exact generated-doc paths. Those root
causes were fixed, and the final complete platform matrix passes.

A superseded Kujo run at 588836e hit one ETXTBSY launching an unchanged SSG shell
fixture. Later full runs passed; no retry or SSG fixture change concealed it.
33508db exposed stale generated TODO references, fixed in d6c7f36. The d6c7f36 Rust
suite passed, but its CLI phase exposed the obsolete binary-fixture snapshot.
The corrected 2be1f04 suite completes every intended fixture case and restores
exception scopes. The final test-only change 5dcbfcd fixes JIT-disabled compilation.
A separate Fence task's changes were moved to its isolated Kujo worktree and are
excluded from this implementation and performance claims. After this task pushed
5dcbfcd, that independent task advanced remote Kujo main to
3cab46ee043b0e452950d7de358487b4c4a3bde8 containing these commits. SiteProbe
retains its separately qualified 2be1f04 pin; no Fence changes are claimed here.

### Remaining work and cross-repository disposition

No unresolved P0–P2 item from this follow-up remains after final qualification.
Further hot-helper decomposition or capture optimization needs representative
measurements and must preserve entry isolation; speculative micro-optimization
and unrelated style churn are not worth changing. No external consumer change is
required by SiteProbe. Rust embedders with exhaustive opcode matches have the
explicit compatibility caveat above; none was identified in the inspected
first-party ecosystem. The authorized runtime work is complete and independently
verified. No new SignalBox capture is warranted for resolved findings.
