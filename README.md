# SiteProbe

[![Version](https://img.shields.io/badge/version-0.1.0-black)](VERSION)
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

- Safe defaults: GET-only, same-origin, robots-respecting, bounded, and public-network-only.
- Reproducible evidence: versioned contracts, stable finding IDs, deterministic mode, and immutable run directories.
- CI-ready outcomes: validate artifacts, compare baselines, and fail on a chosen finding severity.
- Useful coverage: links, redirects, canonicals, metadata, headings, images, robots, sitemaps, JSON-LD, pagination, duplicates, and orphan candidates.
- Quiet by design: concise reports stay bounded while full machine evidence remains available.

## Requirements

- Kujo 1.0 or newer
- Python 3.10 or newer

Set `KUJO_BIN` when the Kujo runtime is not available at the adjacent development
path `../kujo/target/release/kujo`.

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
| `--max-links-per-page` | `10000` | Bound retained links and images per page. |
| `--max-output-bytes` | `104857600` | Bound the complete published run. |
| `--max-report-tokens` | `2000` | Bound the approximate report size. |
| `--fail-on` | `none` | Return non-zero for `info`, `warning`, or `error` findings at and above the threshold. |
| `--allow-private-network` | off | Explicitly authorize loopback or private-network targets. |
| `--ignore-robots` | off | Explicitly override robots policy. |

Private, loopback, link-local, reserved, multicast, and unspecified addresses are
blocked by default. Use `--allow-private-network` only for an authorized internal
target. Same-origin redirects and crawling remain enforced.

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

The primary contracts are `siteprobe.run/v1`, `siteprobe.page/v1`, and
`siteprobe.findings/v1`; their JSON Schemas live in [`schemas/`](schemas/).

## Architecture and Kujo boundary

`src/main.kujo` is the product entrypoint; `scripts/validate.kujo` and
`scripts/benchmark.kujo` own the verification and benchmark workflows.
`src/siteprobe.py` is a narrow standard-library adapter
for streaming HTTP, HTML, XML, DNS, and URL primitives that Kujo does not yet
provide as one complete parsing stack. It has no third-party dependencies and
does not define the product entrypoint. As Kujo gains equivalent primitives,
the adapter is designed to shrink behind the stable artifact contract.

```text
siteprobe launcher -> Kujo entrypoint -> bounded protocol adapter -> versioned artifacts
                                      -> validation / comparison / reports
```

## Development

```bash
bash scripts/validate.sh
${KUJO_BIN:-../kujo/target/release/kujo} run scripts/benchmark.kujo -- --pages 1000
```

The validation gate compiles the Python adapter and fixtures, runs the full
adversarial fixture suite through Kujo, checks and lints Kujo sources, verifies
Kujo formatting, parses every JSON Schema, and checks the Git diff. CI builds
Kujo from its source repository and runs the same gate.

See [security boundaries](docs/security.md), [agent integration](docs/agent-integration.md),
[release qualification](docs/release-qualification-0.1.0.md), and the
[next-session roadmap](docs/next-session-roadmap.md).

## Maturity boundary

SiteProbe 0.1 is a fixture-verified, local-first crawler for static and
server-rendered HTML. It is not a JavaScript renderer, browser automation tool,
security scanner, search-engine emulator, or substitute for Lens. Near-duplicate
signals use deterministic normalized-text fingerprints and metadata duplication;
they do not claim semantic equivalence.

## License

SiteProbe is available under the [MIT License](LICENSE).
