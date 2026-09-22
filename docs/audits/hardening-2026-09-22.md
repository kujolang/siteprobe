# SiteProbe repository hardening — September 22, 2026

## Repository and scope

- Repository: `kujolang/siteprobe`; branch: `main`.
- Starting SHA: `a96bafa57bb5f11f58d8e2af1f1901bb17588b6f`; initial working tree clean.
- Ending implementation SHA: `6568986e406d3b2b4350d65979e2c9c22f0a63c8`.
- Report/evidence commit: `git log -1 --format=%H -- docs/audits/hardening-2026-09-22.md`.
- Purpose: bounded, read-only website observation and versioned evidence for people,
  CI, ContentGraph, Eval and RunLedger. No browser rendering or model calls.
- Dependency: Kujo `2be1f04b89dbecd591ef1af0d68974c05586900e`; zero package
  dependencies in `kujo.toml` and `kujo.lock`. Product code stays native Kujo.

This pass builds on the existing native hardening and readiness work; it does not
replace historical evidence. All current product code, launchers, maintenance,
examples, tests, schemas, workflows and agent instructions were reviewed. The
independent offline security audit covered 43 current source/configuration files.
Historical audit reproductions and inert fixture payloads were not classified as
active executable source. Frozen fixture hashes were verified by the test suite.
Sibling repositories were inspected or invoked as consumers, never edited.

## Baseline

`bash scripts/validate.sh` passed before product changes: 46 native tests,
checks, formatting, lint, frozen package installation, publish preview, generated
references, documentation links and Git whitespace checks. No failing baseline
tests were found. Lint emits existing advisory warnings; a passing exit does not
mean zero warnings. Detailed subprocess logs remain in `.siteprobe/verification/`.

The initial gate used the installed sibling executable (source checkout
`7f4a288587710003c60869c016c8f4d97ca3b8af`). Performance comparisons and final
qualification use the exact pinned runtime's existing release binary at
`/tmp/siteprobe-pinned-target/release/kujo`. Its 408 source/build-input files were
rechecked against the pinned Git blobs with zero mismatches; the binary digest and
prior successful locked-build provenance are in `runtime-provenance.json`.
No runtime was rebuilt or changed for this pass.

Two independently written regression tests demonstrated actual old behavior:

- Repeated `X-Robots-Tag: noindex` then `X-Robots-Tag: nofollow` produced only
  `nofollow` and an incorrect indexability result.
- Removing a page's internal-link partition while preserving `links` and
  regenerating its manifest still passed `validate`.

The retained red-test receipts show those failures. An initial partition-test
harness attempt incorrectly used exclusive JSONL creation on an existing file;
that harness error was corrected before reproducing the product acceptance bug.
Expected values and immutable fixtures were never regenerated from product code.

## Findings

| ID | Priority | Area | Finding and evidence | Action | Status |
| --- | --- | --- | --- | --- | --- |
| SP-H01 | P1 | HTTP evidence | `fetch_into` merged repeated Link fields but read only the final robots header; red test loses `noindex` | Merge all X-Robots-Tag values for ordinary and 304 responses | Fixed |
| SP-H02 | P1 | Artifact consistency | `validate_relationships` checked graph edges but not page link partitions consumed on baseline reuse; re-signed inconsistent run accepted | Check each present partition's type, order, multiplicity, classification and complete link values in the existing edge pass | Fixed |
| SP-H03 | P2 | Runtime work | Empty robots rules still parsed every URL and normalized every path byte | Return allow immediately for an empty parsed rule set; pacing and request checks unchanged | Fixed; fixture-qualified |
| SP-H04 | P2 | CI/DX | Validation ran 72 child commands for 69 unique commands; explicit lists could omit future modules | Discover maintained Kujo sources recursively and run each check/format/lint once; remove unused `run_quiet` wrapper | Fixed; identical command set |
| SP-H05 | P2 | Example efficiency/output | CI adapter validated both runs then called a comparison that validated them again; incomplete subprocess capture was not rejected | One comparison child, explicit 16 MiB per-stream capture, failure on truncation/cancellation/timeout and inherited-argument isolation | Fixed |
| SP-H06 | P2 | Terminal output | Three examples printed unsanitized error strings, unlike the CLI | Reuse `safe_text`, preserve stdout channel and exit 1; extend hostile-path test | Fixed |

No P0 finding or confirmed security vulnerability was established. H01/H02 are
correctness issues, not claims of credential exposure or remote code execution.

## Changes and compatibility

`src/siteprobe.kujo` now consumes the runtime's complete header-value arrays for
robots directives as it already did for HTTP Link. Both normal inspection and
conditional reuse preserve all directives, including an earlier `noindex`.
The new HTTP regression covers 200 and 304 with a real loopback server.

The existing relationship pass now checks internal/external partitions without
building another copy of the graph. It rejects omitted entries, extra duplicates,
changed text, reordering, invalid types and misclassified links even when `verify` accepts regenerated
hashes. Optional absent partition fields retain the existing v1 schema policy;
present fields must agree. Immutable oracle runs remain valid. `compare` and
conditional baseline validation inherit the stronger boundary.

The robots fast path applies only when there are no rules to evaluate. Nonempty
policies, merged groups, wildcard/end-anchor matching, percent normalization,
allow-on-tie, same-origin redirects, destination checks and rate limiting still
run through their existing paths and tests.

`scripts/validate.kujo` now discovers files under `src`, `scripts`, `tests` and
`examples` in deterministic order. It preserves every previous unique command,
rejects symlinked source entries, keeps the native-source restrictions and full
command logs, and automatically covers newly added modules. No test or assertion
was removed. Existing cross-platform CI runs these checks without workflow edits.

`examples/ci_baseline.kujo` retains its two paths and optional runtime argument.
Successful output is still the complete comparison JSON. Invalid evidence now
returns the comparison's structured error envelope instead of the earlier
pre-validation diagnostic. Oversized capture fails visibly without forwarding
partial JSON; direct `siteprobe compare` remains the streaming alternative.
The other three examples preserve channels and exit codes while removing ASCII
terminal controls from errors. Tests exercise valid/invalid CI inputs and all
three examples with an escape-bearing missing path.

Files: core; validation runner; four examples and their README; readiness/unit/test
runner modules; README; security guidance; generated Kujo API line references.
The native test count grows from 46 to 49, with two existing tests extended. An isolated native CLI child that emits 32 MiB
proves the capture regression: the original example exited zero with a partial
1,048,577-byte payload (1 MiB plus newline); the corrected example exits one and forwards zero stdout bytes.

| Contract | Impact |
| --- | --- |
| Public Kujo APIs | No signatures or exports changed |
| Product CLI/options/exit codes | Unchanged; incorrect header results and contradictory-run acceptance corrected |
| JSON/JSONL/file formats and schema identifiers | Unchanged; optional page partitions checked when present |
| Configuration/environment | No new or removed configuration or environment variables; CI adapter isolates runtime-internal inherited `KUJO_SCRIPT_ARGS` |
| Manifests/signatures | Unchanged; frozen signed oracle still verifies |
| Consumers | Valid run consumers unchanged; contradictory evidence now rejected |
| CI example | One subprocess; explicit capture failure; invalid-input output now comparison error JSON |
| Agent instructions | No new prompt machinery, schemas, model calls or context-loading requirements |

## Performance and efficiency

Same pinned runtime, host, 200-page fixture and benchmark command before/after:

| Concurrency | Before wall seconds | After wall seconds | Before peak RSS bytes | After peak RSS bytes |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2.362196334 | 2.009439919 | 35,483,648 | 37,163,008 |
| 4 | 1.244837423 | 1.031014894 | 36,368,384 | 38,121,472 |

These are single-run observations, not a controlled distribution or a general
speedup/RSS claim. Both complete crawls validate all 200 successful pages. Output
size remains approximately 308 KB; changing fixture ports and timings prevent a
byte-size equivalence claim. Frozen deterministic oracle and semantic rerun tests
provide separate behavior-equivalence evidence. No cache was introduced.

| Deterministic work/output measure | Before | After |
| --- | ---: | ---: |
| Validation child commands | 72 | 69 |
| Unique validation commands | 69 | 69 (same set) |
| Gate stdout bytes, runtime path normalized to `KUJO` | 3,138 | 3,040 |
| CI comparison example child processes | 3 | 1 |
| Validation passes for two distinct CI example runs | 4 | 2 |
| Package dependencies | 0 | 0 |

Instruction payloads remain small: `AGENTS.md` is 1,795 bytes and
`docs/agent-integration.md` is 2,084 bytes. No model-token measurements or token
savings are claimed. Full evidence remains in artifacts; report output retains
its existing four-bytes-per-token approximation and byte bound. Product JSON is
not truncated to achieve smaller output.

The full 10,000-page sweep passed at concurrency 1/4/8/16 (123.411, 55.829,
46.376, 42.839 seconds; approximately 350–358 MB peak RSS). Dense 25-page
workloads passed at 1/4 (32.322/21.637 seconds; 427/447 MB peak RSS); multilingual
50-page workloads passed at 1/4 (0.589/0.363 seconds). These qualification runs
used a shared host; some final verification overlapped them. They are not paired
speed comparisons. Every benchmark checks successful-page counts and validates
the resulting run. Machine receipts are linked below. They establish successful bounded execution, not
performance budgets. Peak RSS is an observation, not an enforced OS memory cap.

### Shared-host verification limit

After the documentation/evidence update, another local full-gate run passed 48
cases but the large-artifact case exhausted its existing 30-second subprocess
budget. A focused rerun also timed out. The preserved current-code validation
call timed out after 30,160 ms; the **unchanged starting revision `a96bafa` on the
same artifact and pinned runtime** also timed out after 30,121 ms. Concurrent
unrelated builds, benchmarks and a VM were observed on the host. This supports
shared-host load sensitivity, not a newly introduced behavioral regression.
No timeout, assertion or production code was changed to obtain a pass.

The earlier final-source local run passed all 49 cases (the complete large-artifact
case took 25,137 ms), and hosted macOS/Windows passed that complete case in
5,994/8,975 ms respectively; all three hosted full gates passed. Those are the
qualification receipts. The later local failure is explicitly preserved in
`post-doc-contention*` and `recheck-*`, rather than overwritten or counted as a
pass. A local qualification run needs available host resources; CI independently
qualifies this exact implementation and test revision.

## Security, resources and remaining review

Reviewed boundaries: CLI/config bounds; normalized URL and origin checks;
DNS-pinned public destination policy; redirect and robots policy per hop; bounded
HTTP/HTML/XML/gzip parsing; retries and pacing; signing-key reads; schema/graph
consistency; regular-file and symlink handling; private staging, cleanup and
no-replace publication; metric path separation; subprocess argument arrays;
capability denial; terminal output; release workflows and package extraction.
The independent [security report](artifacts/hardening-2026-09-22/security/report.md)
records assumptions and exclusions. Dependency implementation and a fresh
third-party CVE database audit are outside that static review's claims.

Crawl queues, page counts, response bytes, temporary disk reservations, evidence
accounting, indexes and sort fan-in already have explicit limits and tests.
Worker batches share the existing pacer; the socket-barrier test proves overlap.
There is no new shared mutable state, cache, retry path or persistent format.
Operator ownership of local run parents remains required against hostile
concurrent filesystem mutation. No additional sandbox guarantee is claimed.

Dependencies remain pinned/locked at the runtime boundary; replacing stable
parsers or introducing new packages was not justified. Existing GitHub action
major-version references and the trusted release-build model are unchanged.
Source/package ZIP size and runtime binary size were not optimization targets.

Remaining work: no unresolved P0/P1/P2 item from this pass. Needs more evidence:
broader live-site workload performance; no remote crawl was needed for this audit.
The shared-host local timeout limitation above remains applicable to both the
starting and ending source; hosted qualification is green.
Not worth changing: intentional single-module hot core, public root launchers,
frozen fixtures and historical qualification artifacts. P3 style churn deferred.
Cross-repository follow-ups: none required. Runtime internals remain separately
maintained; this pass neither changes their contracts nor requires an upgrade.

## Verification receipt

All commands ran from the repository root unless stated otherwise. Full durable
receipts are under [artifacts/hardening-2026-09-22](artifacts/hardening-2026-09-22/).

For the pinned commands below, the shell set
`export KUJO_BIN=/tmp/siteprobe-pinned-target/release/kujo`.

| Exact command | Result |
| --- | --- |
| `bash scripts/validate.sh` (before changes, default sibling runtime) | PASS; 46/46 tests |
| `../kujo/target/release/kujo run tests/siteprobe_tests.kujo -- repeated_robots_response` | Expected failure before fix; pinned-runtime rerun PASS after |
| `"$KUJO_BIN" run tests/siteprobe_tests.kujo -- page_link_partitions` | Expected acceptance-bug failure before fix; PASS after, including absent optional fields |
| `"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 200 --concurrency-levels 1,4 --output .siteprobe/hardening-20260922/pinned-before.json` | PASS before product changes |
| `"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 200 --concurrency-levels 1,4 --output .siteprobe/hardening-20260922/pinned-after.json` | PASS after |
| `"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16 --output .siteprobe/hardening-20260922/standard-10000.json` | PASS; 40,000/40,000 successful page observations |
| `"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 25 --workload dense --concurrency-levels 1,4 --output .siteprobe/hardening-20260922/dense.json` | PASS |
| `"$KUJO_BIN" run scripts/benchmark.kujo -- --pages 50 --workload multilingual --concurrency-levels 1,4 --output .siteprobe/hardening-20260922/multilingual.json` | PASS |
| `bash scripts/validate.sh` (pinned runtime, final source) | PASS; 49/49 tests and all 69 child commands |
| `"$KUJO_BIN" run scripts/verify_integrations.kujo -- ../contentgraph ../eval ../runledger` | PASS; ContentGraph 0.3.0, Eval 2.0.0, RunLedger 1.1.0; versions/SHAs in receipt |
| `"$KUJO_BIN" run scripts/release.kujo -- "$KUJO_BIN" hardening .siteprobe/hardening-20260922/dist` | PASS; checksummed source ZIP |
| `"$KUJO_BIN" run scripts/verify_release.kujo -- .siteprobe/hardening-20260922/dist "$KUJO_BIN"` | PASS; extraction, fixture validation, doctor and version |
| `"$KUJO_BIN" run scripts/release.kujo -- "$KUJO_BIN" hardening-final .siteprobe/hardening-20260922/dist-final` | PASS; final 49-test source and audit documentation package |
| `"$KUJO_BIN" run scripts/verify_release.kujo -- .siteprobe/hardening-20260922/dist-final "$KUJO_BIN"` | PASS |
| `"$KUJO_BIN" run tests/siteprobe_tests.kujo -- ci_example_rejects` | PASS; 32 MiB child output rejected without forwarding partial JSON |
| `bash scripts/validate.sh` (documentation-stage repeat) | 48 passed, 1 timed out under shared-host load; retained, not counted as green |
| `"$KUJO_BIN" run tests/siteprobe_tests.kujo -- artifacts_larger_than_eight_mib` (load recheck) | Timed out at existing subprocess bound |
| `"$KUJO_BIN" run .siteprobe/hardening-20260922/recheck-large.kujo` | Same preserved artifact, current source: 30-second timeout |
| `"$KUJO_BIN" run .siteprobe/hardening-20260922/recheck-baseline.kujo` | Same artifact, unchanged starting source: 30-second timeout |
| `git diff --check` | PASS |

The initial repeated-header red test used `../kujo/target/release/kujo`;
the partition acceptance reproduction and green focused tests used the pinned
runtime. Both new tests then passed in the final pinned 49-test suite.
The initial 200-page installed-runtime measurement is retained locally but is not
mixed into the pinned before/after table. Formatter changes used
`"$KUJO_BIN" format --write <changed-source>` and all formatting checks passed.
The full gate's exact child commands are in `final-validation.log`; its individual
stdout/stderr/exit receipts remain in `.siteprobe/verification/`.

Hosted qualification: [validate run 35759228954](https://github.com/kujolang/siteprobe/actions/runs/35759228954)
for ending implementation SHA `6568986e406d3b2b4350d65979e2c9c22f0a63c8`.
PASS on Linux, macOS and Windows: 49/49 native tests per platform, generated-file
checks and extracted-package verification. Linux additionally passed the complete
10,000-page sweep plus dense/multilingual workloads. `ci-qualification.json`
records exact job/artifact IDs; downloaded per-platform test receipts independently
confirm the counts. The final report commit changes documentation/evidence only.
The earlier 48-test run `35758634423` was superseded and cancelled after pushing
the added native capture regression; the final run executes the complete suite.

SignalBox: no captures warranted. Every admitted in-repository finding was
resolved; completed work and handoff belong in Strata.

