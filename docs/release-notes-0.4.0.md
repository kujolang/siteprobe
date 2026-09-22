SiteProbe 0.4.0 completes the readiness backlog and moves maintenance workflows to native Kujo.

- Correct robots group merging, longest-rule matching, wildcards and sitemap redirect policy.
- Protect immutable runs from metrics-path collisions and fix Windows relative artifact paths.
- Bound staging and retained evidence, with lightweight baseline/comparison indexes.
- Validate all secondary artifact contracts and their relationships.
- Improve conditional requests, HTML base handling, relationship comparisons and discovery-limit reporting.
- Add command-specific help and `inspect --fail-on error` while preserving default inspection behavior.

Qualification includes 46 native tests, the unchanged compatibility oracle, full 10,000-page concurrency sweeps, dense and multilingual workloads, and actual ContentGraph, Eval and RunLedger integrations. Artifact contract identifiers remain v1. This remains a bounded static/server-rendered website observer; application accounting limits are not hard process RSS limits.

Downloads are platform-qualified **source packages**, not standalone binaries. They require Kujo revision `2be1f04b89dbecd591ef1af0d68974c05586900e`; set `KUJO_BIN` to that executable. Python is unnecessary for product and maintenance commands. Each ZIP has a SHA-256 checksum file. Use `bash siteprobe` on Unix if extraction does not preserve executable permissions.

See the packaged README, `docs/release-qualification-0.4.0.md` and `docs/readiness-completion.md` for installation, evidence and supported limits.
