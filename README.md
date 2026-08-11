# SiteProbe

[![Version](https://img.shields.io/badge/version-0.1.0-black)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![built with Kujo](https://img.shields.io/badge/built%20with-Kujo-white.svg)](https://github.com/kujolang/kujo)

SiteProbe is the deterministic website-intelligence crawler for Kujo WebOps.
Scout understands source repositories and Lens verifies rendered browser
behavior; SiteProbe models a website as a bounded, crawlable information
system. It never submits forms or mutates the target.

## Quick start

```bash
./siteprobe doctor
./siteprobe crawl https://example.com --max-pages 100 --max-depth 4
./siteprobe validate .siteprobe/<run-id>
./siteprobe report .siteprobe/<run-id>
```

## Commands

| Command | Contract |
| --- | --- |
| `doctor` | Check runtime and local write prerequisites. |
| `crawl <url>` | Crawl a bounded same-origin surface and write a run. |
| `inspect <url>` | Inspect one URL and emit JSON without persistent history. |
| `validate <run>` | Validate required versioned artifacts and references. |
| `compare <old> <new>` | Report meaningful URL, status, canonical, metadata, schema, link, and content changes. |
| `report <run>` | Print the quiet human report. |
| `links <run>` | Print the link inventory as JSON. |
| `sitemap <run>` | Print discovered sitemap evidence as JSON. |
| `version` | Print version and schema contract. |

`crawl` supports `--out`, `--max-pages`, `--max-depth`, `--concurrency`,
`--timeout`, `--respect-robots`/`--ignore-robots`, `--same-origin`, `--json`,
and `--baseline`. Same-origin and robots compliance are on by default.

## Artifacts

Every crawl writes `.siteprobe/<run-id>/` with `run.json`, `site.json`,
`pages.jsonl`, `links.json`, `redirects.json`, `metadata.json`,
`structured-data.json`, `sitemap.json`, `robots.json`, `findings.json`, and
`report.md`. Contracts use `siteprobe.run/v1` and `siteprobe.page/v1`.

## Maturity boundary

Version 0.1 is a fixture-verified, local-first crawler for static/server-rendered
HTML. It is not a JavaScript renderer, security scanner, full resource auditor,
search-engine emulator, or substitute for Lens. Near-duplicate signals use
deterministic normalized text fingerprints and title/description duplication;
they do not claim semantic equivalence.

See [security boundaries](docs/security.md) and [agent integration](docs/agent-integration.md).

## Verification

```bash
bash scripts/validate.sh
```
