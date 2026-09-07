SiteProbe is now native Kujo throughout: crawl policy, robots, extraction, analysis, validation, signing, comparison and reporting. Python is only a development/test dependency.

- Preserves the existing v1 artifact schemas, CLI commands and safe defaults.
- Adds bounded streaming for large artifacts and sitemaps, stricter trust boundaries and immutable publication.
- Performs real bounded concurrent fetching with isolated workers.
- Uses a pinned Kujo runtime with loop/exception corrections, bounded regex reuse and Windows publication fixes.
- Qualifies Linux, macOS and Windows, with complete 10,000-page native crawls at concurrency 1/4/8/16.

The archives are platform-qualified **source packages**, not standalone binaries. They require Kujo revision `2be1f04b89dbecd591ef1af0d68974c05586900e`; set `KUJO_BIN` to that runtime. Python is unnecessary for product commands. Every ZIP has a SHA-256 checksum file. On Unix, use `bash siteprobe` if extraction does not preserve executable permissions.

See the packaged README and release qualification for installation and verification. The 0.2.0 changelog section records an unpublished development milestone; this release includes all changes since v0.1.0.
