# SiteProbe

[![Version](https://img.shields.io/badge/version-0.2.0-black)](VERSION)
[![CI](https://github.com/kujolang/siteprobe/actions/workflows/validate.yml/badge.svg)](https://github.com/kujolang/siteprobe/actions/workflows/validate.yml)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

SiteProbe is a deterministic, read-only website-intelligence crawler written in
[Kujo](https://github.com/kujolang/kujo). It turns a bounded same-origin crawl
into stable JSON, JSONL, and Markdown artifacts that people, CI systems, and AI
agents can validate and compare without replaying network traffic.

Scout understands source repositories and Lens verifies rendered browser
behavior. SiteProbe covers the layer between them: a website as a crawlable
information system.

## Why SiteProbe

- Safe defaults: GET-only, DNS-pinned same-origin connections, robots-respecting pacing, bounded resources, and public-network-only resolution.
- Reproducible evidence: versioned contracts, stable finding IDs, deterministic mode, immutable run directories, and digest manifests with optional HMAC signatures.
- CI-ready outcomes: validate artifacts, compare baselines, and fail on a chosen finding severity.
- Useful coverage: links, redirects, canonicals, metadata, headings, images, robots, sitemaps, JSON-LD, pagination, duplicates, and orphan candidates.
- Quiet by design: concise reports stay bounded while full machine evidence remains available.

## Requirements

- The Kujo runtime revision pinned in [`KUJO_REVISION`](KUJO_REVISION), including
  the bounded web-data primitives used by this native implementation.
- Python 3.10+ is required only for repository tests and fixture benchmarks.

Set `KUJO_BIN` when the runtime is not at `../kujo/target/release/kujo`.

```bash
export KUJO_BIN=/absolute/path/to/kujo
./siteprobe doctor
```

## Quick start

```bash
./siteprobe crawl https://example.com --out .siteprobe/example
./siteprobe validate .siteprobe/example
./siteprobe report .siteprobe/example
```

Run a deterministic CI comparison and fail when a new run contains warnings or
errors:

```bash
./siteprobe crawl https://example.com \
  --out .siteprobe/candidate \
  --baseline .siteprobe/baseline \
  --deterministic \
  --fail-on warning \
  --json
```

On Linux, publication requires libc `renameat2` support; macOS uses `renamex_np`
and Windows uses no-replace rename. Unsupported systems fail closed.

Output paths are immutable: SiteProbe refuses any path that already exists. A
run is staged next to its destination and published atomically only after its
output budget and optional baseline validation pass.

## Commands

| Command | Contract |
| --- | --- |
| `doctor` | Check runtime and local write prerequisites. |
| `crawl <url>` | Crawl a bounded same-origin surface and write a run. |
| `inspect <url>` | Inspect one URL and emit JSON without persistent history. |
| `validate <run>` | Validate required artifacts, schemas, counts, IDs, and declared output budget. |
| `verify <run>` | Verify every manifest digest and an optional HMAC signature. |
| `compare <old> <new>` | Report meaningful URL, status, canonical, metadata, schema, link, and content changes. |
| `report <run>` | Print the bounded human report. |
| `links <run>` | Print the link inventory as JSON. |
| `sitemap <run>` | Print discovered sitemap evidence as JSON. |
| `version` | Print version and schema contract. |

Use `./siteprobe <command> --help` for the complete option set. Important crawl
controls include:

| Option | Default | Purpose |
| --- | ---: | --- |
| `--max-pages` | `100` | Bound fetched or robots-blocked pages. |
| `--max-depth` | `4` | Bound traversal depth. |
| `--concurrency` | `4` | Bound concurrent requests. |
| `--timeout` | `15` | Bound each request in seconds. |
| `--retries` | `2` | Retry transient HTTP and transport failures with bounded backoff. |
| `--request-delay` | `0` | Set a minimum delay between request starts for the origin. |
| `--max-crawl-delay` | `10` | Bound a robots `Crawl-delay` before applying it. |
| `--max-links-per-page` | `10000` | Bound retained links and images per page. |
| `--max-sitemap-compressed-bytes` | `5242880` | Bound compressed sitemap bytes. |
| `--max-sitemap-expanded-bytes` | `20971520` | Bound expanded sitemap bytes. |
| `--sort-buffer-bytes` | `8388608` | Bound each deterministic external-sort chunk. |
| `--query-policy` | `preserve` | Preserve, sort, or drop query parameters. |
| `--query-deny-param` | none | Remove a named parameter; repeat for multiple names. |
| `--max-output-bytes` | `104857600` | Bound the complete published run. |
| `--max-report-tokens` | `2000` | Bound report UTF-8 bytes to four times this approximate token budget. |
| `--fail-on` | `none` | Return non-zero for `info`, `warning`, or `error` findings at and above the threshold. |
| `--signing-key-file` | none | Sign the run manifest with HMAC-SHA-256 key material from a file. |
| `--allow-private-network` | off | Explicitly authorize loopback or private-network targets. |
| `--ignore-robots` | off | Explicitly override robots policy. |

Private, loopback, link-local, reserved, multicast, and unspecified addresses are
blocked by default. Use `--allow-private-network` only for an authorized internal
target. Same-origin redirects and crawling remain enforced.

Each redirect hop is normalized, checked against the initial origin, resolved
again, filtered by address policy, and connected to the exact approved address.
This closes the DNS-rebinding gap between policy validation and connection.

```bash
./siteprobe crawl https://example.com --out .siteprobe/signed --signing-key-file /secure/siteprobe.key
./siteprobe verify .siteprobe/signed --signing-key-file /secure/siteprobe.key
```

## Artifacts

Every crawl writes a run directory containing:

| Artifact | Contents |
| --- | --- |
| `run.json` | Run identity, configuration, aggregate counts, and severity counts. |
| `site.json` | Site-level origin, robots, sitemap, crawlable, and indexable summary. |
| `pages.jsonl` | One bounded page record per line. |
| `links.json` | Normalized directed link graph. |
| `redirects.json` | Same-origin redirect evidence. |
| `metadata.json` | Title and description inventories. |
| `structured-data.json` | Parsed or fingerprinted-invalid JSON-LD. |
| `sitemap.json` | Sitemap discovery, members, and errors. |
| `robots.json` | Robots retrieval evidence and fingerprint. |
| `findings.json` | Deterministic observations with stable IDs. |
| `report.md` | Bounded human-readable summary. |
| `manifest.json` | SHA-256 digest and byte count for every artifact, plus optional HMAC-SHA-256 signature. |

The primary contracts are `siteprobe.run/v1`, `siteprobe.page/v1`,
`siteprobe.findings/v1`, and `siteprobe.manifest/v1`; their JSON Schemas live in
[`schemas/`](schemas/). `siteprobe validate` invokes both structural consistency
checks and Kujo's native Draft 2020-12 subset validator.

## Architecture and Kujo boundary

`src/main.kujo` dispatches the native CLI into `src/siteprobe.kujo`. The core keeps
explicit function boundaries and labeled sections for CLI, crawl, network, robots,
page extraction, artifacts, and shared transformations. One module avoids the
measured cost of copying captured environments across frequent module calls.
Kujo owns crawl policy, per-hop robots checks, retries, extraction, analysis,
comparison, manifests, reporting, and publication. Rust runtime primitives provide
bounded I/O, HTTP/DNS, HTML tokenization, URL parsing, XML projection, cryptography,
and scheduling mechanisms. No product command starts Python or another process.

`tests/legacy/siteprobe.py` is a frozen compatibility oracle, never a runtime
fallback. The native migration and its measured verification evidence are recorded
in [the repository audit](docs/audits/repository-hardening.md).

## Development

```bash
bash scripts/validate.sh
${KUJO_BIN:-../kujo/target/release/kujo} run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16
${KUJO_BIN:-../kujo/target/release/kujo} run scripts/generate_docs.kujo -- ${KUJO_BIN:-../kujo/target/release/kujo}
```

The validation gate checks the Python test fixtures and frozen oracle, runs the full
adversarial fixture suite through Kujo, checks and lints Kujo sources, verifies
Kujo formatting, parses every JSON Schema, and checks the Git diff. CI builds
Kujo from the revision pinned in `KUJO_REVISION` and runs the same gate on
Linux, macOS, and Windows. Linux also requires a complete 10,000-page native
crawl with HTTP 200 results at concurrency 1, 4, 8 and 16. CI preserves timing,
RSS and verification logs as artifacts; timing is not a flaky pass/fail threshold.
See the historical Python [10,000-page baseline](docs/benchmark-10000.json),
the native [audit measurements](docs/audits/repository-hardening.md),
the [Kujo API reference](docs/generated/kujo-api.md), and
the [artifact contract reference](docs/generated/artifact-contracts.md).

## Install and release artifacts

Clone the repository beside Kujo, run `kujo package-install --frozen`, and use
`./siteprobe` on Unix or `siteprobe.cmd` / `siteprobe.ps1` on Windows. Tagged
releases build platform-specific ZIP archives and matching `.sha256` files via
`scripts/release.kujo`; GitHub attaches them only after the multi-platform gate
passes. `kujo package-publish` currently provides the local deterministic
publish preview; SiteProbe does not imply a hosted registry transport.

See [security boundaries](docs/security.md), [agent integration](docs/agent-integration.md),
[release qualification](docs/release-qualification-0.2.0.md), and the
[next-session roadmap](docs/next-session-roadmap.md).

## Maturity boundary

SiteProbe 0.2 is a fixture-verified, local-first crawler for static and
server-rendered HTML. It is not a JavaScript renderer, browser automation tool,
security scanner, search-engine emulator, or substitute for Lens. Near-duplicate
signals use deterministic normalized-text fingerprints and metadata duplication;
they do not claim semantic equivalence.

## License

SiteProbe is available under the [MIT License](LICENSE).
