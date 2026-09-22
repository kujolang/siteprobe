# Security Review: kujolang/siteprobe

## Scope

Current product, maintenance, release, examples, schemas and executable tests reviewed offline. Historical evidence and inert compatibility fixture payloads excluded from executable-source coverage.

- Scan mode: repository
- Target kind: git_revision
- Target ID: siteprobe-a96bafa57bb5f11f58d8e2af1f1901bb17588b6f
- Revision: a96bafa57bb5f11f58d8e2af1f1901bb17588b6f
- Inventory strategy: repository
- Included paths: .
- Excluded paths: docs/audits/artifacts/, tests/fixtures/
- Runtime or test status: Not executed by security auditor; parent owns baseline and verification.
- Artifacts reviewed: .github/workflows/release.yml, .github/workflows/validate.yml, AGENTS.md, docs/security.md, examples/ci_baseline.kujo, examples/contentgraph.kujo, examples/eval.kujo, examples/runledger.kujo, kujo.lock, kujo.toml, schemas/findings.schema.json, schemas/links.schema.json, schemas/manifest.schema.json, schemas/metadata.schema.json, schemas/page.schema.json, schemas/redirects.schema.json, schemas/robots.schema.json, schemas/run.schema.json, schemas/site.schema.json, schemas/sitemap.schema.json, schemas/structured-data.schema.json, scripts/benchmark.kujo, scripts/generate_contract_docs.kujo, scripts/generate_docs.kujo, scripts/release.kujo, scripts/validate.kujo, scripts/validate.ps1, scripts/validate.sh, scripts/verify_integrations.kujo, scripts/verify_release.kujo, siteprobe, siteprobe.cmd, siteprobe.ps1, src/main.kujo, src/siteprobe.kujo, tests/contract_tests.kujo, tests/crawl_tests.kujo, tests/fixture_server.kujo, tests/native_probe.kujo, tests/readiness_tests.kujo, tests/siteprobe_tests.kujo, tests/support.kujo, tests/unit_tests.kujo

Limitations and exclusions:
- Dependency implementations outside repository not audited.
- No independent architecture subagent; delegated auditor performed source architecture review sequentially.
- Excluded docs/audits/artifacts/: Historical benchmark/source reproduction artifacts, not active product or maintenance entrypoints.
- Excluded tests/fixtures/: Inert hash-verified compatibility payloads; consuming test and product code fully reviewed.
- Excluded ../kujo/: Out-of-repository dependency implementation; current scan verifies call-site controls only.

### Scan Summary

| Field | Value |
| --- | --- |
| Scan outcome | completed |
| Reportable findings | 0 |
| Severity mix | none |
| Confidence mix | none |
| Coverage | complete |
| Validation mode | Offline static source review |

Canonical artifacts: `scan-manifest.json`, `findings.json`, and `coverage.json`. This report is a deterministic projection of those files.

## Threat Model

SiteProbe is a local native Kujo CLI crawler and artifact validator. dispatch routes operator inputs to bounded HTTP observation, staged immutable artifact publication, or offline validation/comparison (src/siteprobe.kujo:1209). No hosted service or multi-tenant deployment is established.

### Assets

- Operator network authority and private destinations
- Signing key confidentiality and run authenticity
- Immutable run contents and filesystem integrity
- Bounded crawler resource use and trustworthy terminal output

### Trust Boundaries

- Remote HTTP responses and DNS enter fetch_into: GET-only, pin_dns, no automatic redirects and deny_private by default; same-origin destination checked before next hop (src/siteprobe.kujo:403-465).
- Remote robots and sitemap data enter bounded parsing and policy checks; redirect robots enforcement occurs before each request (src/siteprobe.kujo:103-173,940-996).
- Run directories enter schema and relationship checks; required-file symlinks rejected and per-artifact reads bounded; local parent ownership required (src/siteprobe.kujo:633-836; docs/security.md:28).
- Operator signing-key reference resolves to regular-file handle read bounded to 65536 bytes and HMAC verification; no key material is serialized (src/siteprobe.kujo:614-671).
- Output uses operator-selected parent and private temporary stage, published with native no-replace primitive; metrics cannot overlap run ancestors (src/siteprobe.kujo:1131-1193).
- Release workflow runs trusted repository content on tag push; explicit argument arrays invoke runtime/package tools, with Kujo source revision pinned (.github/workflows/release.yml:1; scripts/release.kujo:35).

### Attacker Capabilities

- A crawled origin may control HTML, response headers, redirects, robots and sitemap bodies but not operator configuration or run parent directories.
- An artifact supplier may supply malformed run files; absent a trusted HMAC key verification provides integrity rather than origin authentication.
- Repository writers and runtime executable selection already have operator code authority and are not independent unprivileged attackers.

### Security Objectives

- Preserve same-origin, GET-only, robots-respecting and public-network defaults.
- Reject partial publication, symlink artifacts, malformed evidence and oversized resources without silently dropping mandatory data.
- Preserve signatures, bounded structured output and independent runtime capabilities.

### Assumptions

- Operator owns run directories and ancestors during reads/writes, as documented; concurrent hostile directory mutation is excluded.
- Native Kujo implementations of DNS pinning, XML/token parsers, regular-file reads, no-replace publication and HMAC are dependency contracts; their implementation was outside this repository-only scan.
- No application execution or network access performed; source-backed review only.
- Architecture review performed sequentially by the delegated security auditor; no additional independent architecture agent was available.

## Findings

### No findings

No reportable findings survived the canonical discovery, validation, and reportability gates.

## Reviewed Surfaces

| Surface | Risk Area | Outcome | Notes |
| --- | --- | --- | --- |
| HTTP, DNS and redirect authority | not recorded | No issue found | src/siteprobe.kujo:403-465 explicitly pins connections, disables automatic redirects, enforces same-origin before next request, bounds retries/hops/response bytes; private-network bypass requires explicit operator flag. No SSRF bypass established. |
| HTML, robots and sitemap parsing | not recorded | No issue found | src/siteprobe.kujo:103-387,940-996 use bounded native tokenization/XML and allowlisted normalized URLs. No evaluation of remote content. Parser internals remain a Kujo dependency assumption. |
| Artifacts, keys and publication | not recorded | No issue found | src/siteprobe.kujo:614-836,1131-1193 enforce regular files, HMAC, required artifacts, schema/relationship checks, private staging and no-replace publish. TOCTOU requires hostile operator-owned directory mutation explicitly outside documented boundary. |
| Resource bounds and concurrency | not recorded | No issue found | src/siteprobe.kujo:901-1128,1252 specify response/frontier/page/concurrency/retained/staging bounds and deterministic serialization. They are accounting envelopes, not hard RSS isolation; no concrete unbounded remotely induced resource path validated. |
| Human and machine output | not recorded | No issue found | Product diagnostic/report sanitize ASCII terminal controls (src/siteprobe.kujo:58,97-98,1301); exact JSON preserves data. Example error catches print raw errors: non-blocking consistency hardening candidate sent to parent, without demonstrated security-impacting privilege gain. |
| Launchers, CI, release, tests and examples | not recorded | No issue found | All current executable files reviewed. Product never shells out; maintenance passes argv arrays. Release workflows are tag-triggered and runtime revision pinned. Local fixture control server binds loopback; no production deployment. No privileged trust-boundary bypass established. |
