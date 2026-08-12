# SiteProbe

[![Version](https://img.shields.io/badge/version-0.2.0-black)](VERSION)
[![CI](https://github.com/kujolang/siteprobe/actions/workflows/validate.yml/badge.svg)](https://github.com/kujolang/siteprobe/actions/workflows/validate.yml)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![Built with Kujo](https://img.shields.io/badge/built%20with-Kujo-white.svg)](https://github.com/kujolang/kujo)

SiteProbe is a deterministic, read-only website-intelligence crawler built with
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

- Kujo 1.0.1 or newer, including the compatibility fixes pinned in
  [`KUJO_REVISION`](KUJO_REVISION)
- Python 3.10 or newer

Set `KUJO_BIN` when the Kujo runtime is not available at the adjacent development
path `../kujo/target/release/kujo`.
On systems where Python is not named `python3`, set `SITEPROBE_PYTHON` to the
Python 3 executable; the Windows launchers discover `python.exe` automatically.

```bash
export KUJO_BIN=/absolute/path/to/kujo
export SITEPROBE_PYTHON=/absolute/path/to/python3
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
| `--max-report-tokens` | `2000` | Bound the approximate report size. |
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

`src/main.kujo` is the product entrypoint; `scripts/validate.kujo` and
`scripts/benchmark.kujo` own the verification and benchmark workflows.
`src/siteprobe.py` is a narrow, dependency-free protocol adapter for pinned DNS
connections and tolerant HTML/XML parsing. Kujo owns product dispatch, native
schema validation, tests, benchmarks, documentation generation, release
packaging, checksums, and integrations. A replacement audit confirmed that
Kujo 1.0.1 still lacks the combined pinned-connection and tolerant streaming
parser surface needed to remove the adapter without weakening the contract.

```text
siteprobe launcher -> Kujo entrypoint -> bounded protocol adapter -> versioned artifacts
                                      -> validation / comparison / reports
```

## Development

```bash
bash scripts/validate.sh
${KUJO_BIN:-../kujo/target/release/kujo} run scripts/benchmark.kujo -- --pages 10000 --concurrency-levels 1,4,8,16
${KUJO_BIN:-../kujo/target/release/kujo} run scripts/generate_docs.kujo -- ${KUJO_BIN:-../kujo/target/release/kujo}
```

The validation gate compiles the Python adapter and fixtures, runs the full
adversarial fixture suite through Kujo, checks and lints Kujo sources, verifies
Kujo formatting, parses every JSON Schema, and checks the Git diff. CI builds
Kujo from the revision pinned in `KUJO_REVISION` and runs the same gate on
Windows. See the committed [10,000-page benchmark](docs/benchmark-10000.json),
[Kujo API reference](docs/generated/kujo-api.md), and
[artifact contract reference](docs/generated/artifact-contracts.md).

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
