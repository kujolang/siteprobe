# SiteProbe repository hardening audit — 2026-09-07

**Status: hardening changes verified; full requested Kujo rewrite NOT complete.**
The user was asked whether necessary sibling Kujo runtime changes are authorized.
No answer was received during this pass. No sibling repository source was changed.
This report is an interim engineering handoff, not satisfaction of the complete
mission's definition of done.

## Repository and revisions

- Repository: `kujolang/siteprobe`, branch `main`.
- Starting SHA: `a7ecdb1cd6db998c58e8def42279071f01c39d18` (clean tree).
- Ending implementation SHA: `4a39969ab8b94e6250ec447eb4a90e2792acbe53`.
  This report, language corrections, and evidence are committed subsequently;
  use `git log -1 --format=%H -- docs/audits/repository-hardening.md` to resolve
  the report commit without a self-referential commit hash.
- Runtime tested: adjacent executable reporting `kujo 1.3.1`, macOS, Python 3.10.
  Its exact build-source SHA was not independently established.
- Kujo source inspected read-only: `9cedbf2f5ae5a0a9b126b055f4c9a6a58a2c23eb`.
- CI/runtime dependency pin: `510cca19cb03c2dcc5589697cdbbe0158ae15c04`.
  Source inspection confirms the added process-result fields and `eprint` exist
  at that pin; this session did not rebuild that revision or run hosted CI.

Purpose: bounded, same-origin, read-only website crawling and stable evidence
artifacts for people, agents, and CI. Dependencies are Kujo and Python's standard
library; there are no declared Kujo packages or third-party Python packages.
Integrations include ContentGraph, Eval, RunLedger, and WebOps consumers of the
versioned artifact contracts.

## Ground truth and contracts

`src/main.kujo` launches `src/siteprobe.py` for every product command and adds
native schemas to `validate`. The 1,028-line starting Python module implements
CLI parsing, crawl scheduling, HTTP, DNS filtering/pinning, HTML/XML/robots,
analysis, external sorting, artifact publication, manifests, comparison, and
reporting. The starting Kujo entrypoint was 59 lines. The README's claim that
Python was only a narrow protocol adapter was false; badges/descriptions and
the completed-native-roadmap claim are corrected.

Reviewed all source, tests, fixture/benchmark programs, launchers, package and
release configuration, workflows, schemas, generated references, examples,
security/agent instructions, release qualifications, and roadmap. Important
contracts:

- Commands: doctor, version, crawl, inspect, validate, verify, compare, report,
  links, sitemap. Bounds/options are defined in the legacy `parser()`/dispatch.
- Exit codes: 0 success, 1 verification/runtime/finding-threshold failure,
  2 invalid invocation/operator bounds/existing output. Crawl `--fail-on` may
  publish complete evidence while returning 1.
- Primary schemas: `siteprobe.run/v1`, `siteprobe.page/v1`,
  `siteprobe.findings/v1`, `siteprobe.manifest/v1`; other artifact names and
  stable finding IDs stay unchanged.
- Environment: `KUJO_BIN`, `SITEPROBE_PYTHON`; no new environment variables.
- HTTP: GET only; same origin including redirects; TLS verification; approved
  resolved address pinned to connection; explicit private-network override;
  bounded retries, timeout, body, sitemap, depth, pages and concurrency.
- Filesystem: immutable output directory, staged publication, optional baseline
  reads, optional signing-key file, manifests and offline consumers.
- State: one bounded thread pool, locked request pacing, queue deduplication,
  per-process URL query policy, immutable baseline reuse. No durable cache,
  model prompts, MCP schemas, form submissions, or provider credentials.

## Baseline

`bash scripts/validate.sh` passed before edits: **9 tests in 109.345 seconds**,
Kujo check/lint/format, package install/frozen/publish preview, schema parsing,
generated documentation and diff whitespace checks. Complete output:
[`artifacts/baseline.log`](artifacts/baseline.log).

A fresh temporary copy of the starting Python source was exercised with the
first seven audit regressions and the fixture additions: seven tests produced
eight failed assertions. This isolates original defects from subsequent edits;
[`artifacts/regressions-baseline.log`](artifacts/regressions-baseline.log)
preserves the failures.

The 200-page local HTTP benchmark ran before and after at concurrency 1 and 4.
It measures the Python crawler process, not Kujo launcher startup. One sample
per configuration is an observation, not a statistically controlled speed test.

## Findings

| ID | Priority | Area | Finding / evidence | Action | Status |
| --- | --- | --- | --- | --- | --- |
| SP-A01 | P1 | Language | All product commands delegate to Python; source/README disagree | Correct claims; record native prerequisites | Rewrite blocked on scope decision |
| SP-A02 | P0 | Robots | A permitted page redirects to `/private` without robots recheck; fixture observes forbidden GET | Check policy before every page hop | Fixed/tested |
| SP-A03 | P0 | Robots | Failed/denied robots responses were parsed as empty rules | Fail before page requests unless rules are 200, absent 404/410, or explicitly ignored | Fixed/tested 403/503 |
| SP-A04 | P1 | Bounds | Blocked pages increment count without stopping the inner batch | Include blocked pages and reserved batch slots in budget | Fixed/tested |
| SP-A05 | P1 | Bounds | NaN bypasses comparisons; control characters silently change normalized host | Reject nonfinite floats and URL controls at input | Fixed/tested |
| SP-A06 | P1 | Resources | Response-read and TLS-handshake failures can leave sockets open | Guaranteed response/raw-socket closure | Fixed/tested |
| SP-A07 | P1 | Integrity | Oversized manifest loaded before a bound; empty manifest can certify missing evidence | Bound manifest/referenced files; require complete artifact coverage | Fixed/tested |
| SP-A08 | P0 | Publication | Check-then-`os.replace` can replace a competing empty directory | Atomic no-replace OS operation; reject dangling destination symlink | Fixed; macOS executed, Linux/Windows CI pending |
| SP-A09 | P1 | Resources | External sort opens every chunk simultaneously | Hierarchical merge with 32 input files and one output | Fixed/tested with 1,100 chunks |
| SP-A10 | P1 | Output | Long target makes 64-token report 20,256 bytes; terminal escape retained | Bound UTF-8 bytes; remove ASCII controls; retain full JSON | Fixed/tested |
| SP-A11 | P1 | CLI | Captured output truncates at transport limit yet returns success; stderr goes to stdout | Reject truncated/incomplete process result; preserve streams; delay success until schemas pass | Fixed/tested |
| SP-A12 | P1 | Determinism | Deterministic page artifact retains elapsed time | Set elapsed_ms=0 only in deterministic mode | Fixed/tested |
| SP-A13 | P1 | Runtime | Native whole-file reads reject 8,400,000-byte JSONL | Record reproducible mismatch; requires bounded streaming migration | Open |
| SP-A14 | P2 | Verification | 100 fuzz cases each start a fresh Python process | Same CLI parser/dispatch/assertions in process; keep malformed subprocess smoke cases | Fixed/tested |
| SP-A15 | P2 | Build/docs | Runtime builtin count changes product docs; duplicate CI Python setup; stale release stage may contaminate archive | Disable builtin doc inventory; remove duplicate setup; reject existing release stage; stream archive hash; include tests | Fixed; local release smoke passed |
| SP-A16 | P1 | Keys | Path check and key open use separate identities; read can grow past checked size | Verify regular-file identity on opened handle and bound read | Fixed/tested regular/symlink/size cases |

## Changes implemented and compatibility

### Crawl policy and resource ownership

`src/siteprobe.py`: optional robots callback is passed through `inspect_page`
to `fetch`, covering redirect destinations before DNS/connect. Robots failures
abort explicitly. The batch reservation includes blocked records. Nonfinite
floats are rejected before network work. HTTP reads close in `finally`; failed
TLS wrapping closes the raw socket. All changes have targeted regressions in
`tests/test_hardening.py` and HTTP fixture extensions in `tests/test_siteprobe.py`.
Existing valid requests retain their options, headers, retries and output shapes.
Robots failure/redirect behavior intentionally becomes stricter because the
previous behavior violated the documented default.

### Filesystem, manifest and key boundaries

`publish_directory` uses macOS `renamex_np(RENAME_EXCL)`, Linux libc
`renameat2(RENAME_NOREPLACE)`, or Windows non-replacing `os.rename`. No unsafe
fallback is provided. Existing output remains exit 2 even if detected at
publication. Unsupported platforms/libcs return an explicit runtime failure.
The macOS constant/function contract was checked against installed SDK
`sys/stdio.h`; successful publication and existing-empty-directory rejection
were executed. Linux/Windows behavior awaits the existing CI matrix.

Manifest inputs and referenced artifacts are checked against the existing
256 MiB validation-file bound; manifests require every historical required
artifact. Signature algorithms/format remain unchanged. Signing keys are opened
with no-follow/nonblocking flags where available, checked as regular files on
the retained handle, checked for identity changes, and read with a fixed bound.
Run-directory parents must remain operator-controlled during the operation;
this is not a general sandbox against concurrent hostile directory mutation.

### Deterministic evidence and bounded receipts

External sorting keeps chunk bytes controlled by the existing option and adds
bounded fan-in with cleanup-managed descriptors and temporary directories.
The 1,100-chunk regression checks sorted output, descriptor bound and cleanup.
`--deterministic` zeros elapsed time; normal timing remains available. Reports
prioritize coverage/evidence references, omit over-budget detail, and remain
within four UTF-8 bytes per requested approximate token. JSON evidence is intact.
The Kujo launcher no longer emits malformed partial output as a successful
command. Large-output consumers should read the run artifacts directly.

### Verification, packaging and documentation

The Kujo test entrypoint now discovers all test modules. The randomized malformed
URL corpus still exercises the production argument parser and dispatch with the
same exit/output assertions, but its 100 generated cases avoid redundant process
startup. Five fixed malformed cases still run as subprocesses. `scripts/validate.kujo`
compiles the new tests, and the existing multi-platform gate runs them.

DocGen is scoped to product functions with `--no-builtins`, eliminating dependency
inventory drift without removing product API documentation. Release checks reject
stale stages and stream checksums; tests are included in ZIPs. README, security,
agent guidance, package description, changelog, and roadmap now match reality.
Development validation still requires a Git checkout with its workflows.

Public APIs, artifact filenames, schema IDs/definitions, config options and
environment names do not change. Optional Python helper parameters are additive.
CLI stderr is corrected; malformed/nonfinite inputs, failed robots policy,
truncated output, unsafe/incomplete manifests and raced destinations fail rather
than appearing successful. Human report layout changes. Deterministic elapsed
values become zero. Downstream code depending on the previous bugs may observe
these intentional corrections; semantic page/finding evidence stays compatible.

## Performance and efficiency

| Measurement | Before | After | Interpretation |
| --- | ---: | ---: | --- |
| Full test suite | 9 tests / 109.345 s | 24 tests / 38.167 s | Observed runs; 100 interpreter startups removed; not a universal speedup claim |
| 64-token adversarial report | 20,256 bytes, escape retained | 246 bytes, no escape | Meets 256-byte approximation budget; not a tokenizer measurement |
| Merge file handles | Grows with chunk count | At most 33 | Behavior tested with 1,100 chunks |
| 200 pages, concurrency 1: wall | 1.825570 s | 2.786329 s | Slower observation; noisy shared host, no speed claim |
| 200 pages, concurrency 4: wall | 1.142534 s | 1.591089 s | Slower observation; no speed claim |
| 200 pages, concurrency 1: CPU | 1.034398 s | 1.244298 s | Single observations |
| 200 pages, concurrency 4: CPU | 1.012669 s | 1.122817 s | Single observations |
| 200 pages, concurrency 1: peak RSS | 26,345,472 bytes | 26,329,088 bytes | Essentially unchanged |
| 200 pages, concurrency 4: peak RSS | 26,427,392 bytes | 26,324,992 bytes | Essentially unchanged |
| 200 pages, concurrency 1: artifacts | 333,583 bytes | 333,603 bytes | Report/layout/timing differences |
| 200 pages, concurrency 4: artifacts | 333,660 bytes | 333,671 bytes | Report/layout/timing differences |
| Third-party Python / Kujo packages | 0 / 0 | 0 / 0 | No added package dependency |

Three additional alternating before/after trials used the same local 200-page
server and the final implementation. Median results (`benchmark-paired.json`):

| Measurement | Baseline median | Final median |
| --- | ---: | ---: |
| Concurrency 1 wall | 1.188096 s | 1.067370 s |
| Concurrency 4 wall | 0.858466 s | 0.712991 s |
| Concurrency 1 CPU | 0.773600 s | 0.748870 s |
| Concurrency 4 CPU | 0.829891 s | 0.722256 s |
| Concurrency 1 peak RSS | 26,157,056 bytes | 26,677,248 bytes |
| Concurrency 4 peak RSS | 26,300,416 bytes | 26,763,264 bytes |

These small-fixture observations do not establish a general speedup. They do
not reproduce the initial slower samples; memory remains approximately 26–27 MB.

Raw receipts: `artifacts/benchmark-before.json`, `benchmark-after.json`,
`benchmark-paired.json`, `efficiency.json`. The after crawl benchmark was sampled after the sort/report
fixes, before the subsequent key/no-replace/robots-failure changes; these do not
run additional network work for its successful unsigned fixture. Do not treat it
as a comprehensive final release benchmark. No binary/build-time or model-token
claims are made. Native product migration remains necessary before final runtime
performance qualification; a broad new 10,000-page sweep was not performed.

## Security review and remaining uncertainty

Reviewed user URLs, response headers/bodies, same-origin DNS-pinned transport,
redirects, robots, malformed HTML/XML/JSON-LD, query policy, gzip expansion,
subprocess argv, output paths, manifests, keys, budgets, threads, and baseline
reuse. Fixed boundaries are enumerated above; negative tests run in the standard
gate. No network credentials or model/provider capability exists here.

Needs more evidence: peak aggregate crawl memory/disk on adversarial maximum-size
pages; sitemap index queue amplification within document limits; baseline reuse
across changed crawl/query policies; Python ElementTree versus future bounded XML
DTD/encoding compatibility; concurrent hostile mutation of local artifact trees.
The total output budget remains a publication check rather than an incremental
spool quota. These are not silently declared solved by bounded merge fan-in.

## Cross-repository follow-ups and remaining work

- **P1 / Kujo, required for requested migration:** preserve tolerant HTML parsing,
  standards-based URL joining/IDNA/query handling, bounded streaming artifact
  validation, and large sitemap/gzip contracts. Current source provides pinned
  HTTP and bounded XML, unlike the pin, but XML is capped at 8 MiB and is not a
  tolerant HTML parser. `native-read-limit.json` proves the current read failure.
  Do not raise global limits or replace mature parsers with brittle regexes.
  Ask/await scope authorization, then add generic primitives and differential
  tests before moving product policy into Kujo and removing Python runtime use.
- **P1 / SiteProbe:** full native migration and final parity/performance qualification
  remain unfinished; current repository is honestly described as Python-backed.
- **P2 / CI:** run hosted Linux/Windows and the exact pinned runtime build; local
  macOS verification does not substitute for these. No runtime pin was bumped.
- **Needs more evidence:** representative repeated benchmarks on an isolated host
  before making generalized runtime speed claims. Three alternating paired trials
  below did not reproduce the initial slower observation.
- **Not worth changing:** rewrites of working URL/HTML/XML logic merely to reduce
  dependency count; production has no third-party Python dependencies.
- No known new failing test remains. The complete user objective remains blocked.

SignalBox dedup searched `siteprobe` and `read_lines`: no equivalent item existed.
Stored capture `cap_c2998d00-7ec5-40c1-9407-236ba5f535aa` and review signal
`sig_58a6945c-4265-44a7-bc42-8fc0fd688bfe` for the native large-artifact mismatch.
Exact retrieval and the concept search `native validation` returned both stored IDs.
Existing WebOps/ContentGraph compatibility capture was not duplicated or asserted
as freshly verified. Resolved fixes, routine verification and handoff prose were
rejected as SignalBox capture candidates.

## Verification receipt

Commands executed from the SiteProbe checkout (runtime version as above):

| Command | Result |
| --- | --- |
| `bash scripts/validate.sh` before changes | PASS, 9 tests, 109.345 s; `artifacts/baseline.log` |
| `python3 -m unittest discover -s <fresh-baseline-copy>/tests -p test_hardening.py` against starting source | Expected FAIL; 7 tests, 8 failed assertions; isolated original bugs |
| `python3 -m unittest discover -s tests -p test_hardening.py` | PASS on intermediate/final regression development; final full gate covers all 15 additions |
| `bash scripts/validate.sh` after changes | PASS, 24 tests, 38.167 s; `artifacts/verification.log` |
| `python3 scripts/benchmark_fixture.py --pages 200 --concurrency-levels 1,4 --output docs/audits/artifacts/benchmark-before.json` | PASS, baseline |
| `python3 scripts/benchmark_fixture.py --pages 200 --concurrency-levels 1,4 --output docs/audits/artifacts/benchmark-after.json` | PASS, post-sort/report observation |
| `../kujo/target/release/kujo run scripts/generate_docs.kujo -- ../kujo/target/release/kujo` | PASS |
| `../kujo/target/release/kujo run scripts/release.kujo -- ../kujo/target/release/kujo audit-macos <temporary-output-dir>` | PASS; SHA-256/ZIP contents checked; repeat exits 2; `artifacts/release-check.json` |
| `../kujo/target/release/kujo run <temporary-read-limit.kujo> -- <8400000-byte-jsonl>` | Expected FAIL, exit 1, read limit 8,388,608; `artifacts/native-read-limit.json` |
| Alternating original/final Python CLI crawl, 200 pages, concurrency 1/4, three trials each | PASS, 12 crawls; `artifacts/benchmark-paired.json` |
| `git diff --check` | PASS |

The temporary read-limit script is exactly:

```kujo
try { print(len(read_lines(args()[0]))) } except err { print(to_string(err)); exit(1) }
```

Its input was `'{}\n' * 2800000`. The release ZIP was read with Python `zipfile`,
its SHA-256 recomputed with `hashlib`, and inclusion of `src/main.kujo` and the
regression tests asserted. Full logs stay in the evidence directory rather than
normal command receipts. No external website was crawled during verification.

One intermediate regression invocation overlapped other local processes and
failed with `BlockingIOError: [Errno 35] Resource temporarily unavailable` while
starting subprocesses (`artifacts/intermediate-resource-contention.log`). No
timeout was increased and no test was disabled. The subsequent full 24-test
gate passed. The final gate is the verification receipt, not that intermediate
host-resource failure.

The paired benchmark used the existing `scripts/benchmark_fixture.py` Handler on
one ephemeral loopback server. The original source was loaded using
`git show a7ecdb1:src/siteprobe.py` into a temporary `src/` beside a copied VERSION.
Each variant executed `python3 <source> crawl <fixture>/p/0 --out <unique-run>
--max-pages 200 --max-depth 2 --concurrency <1-or-4> --allow-private-network
--json --metrics-file <unique-metrics>`. Variant order reversed on the second
trial; medians were computed from three trials with Python `statistics.median`.
