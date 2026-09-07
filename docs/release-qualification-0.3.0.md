# SiteProbe 0.3.0 release qualification

Native Kujo release, 2026-09-07. This supersedes the Python-backed 0.2.0
development milestone; v0.1.0 was the previous published GitHub release.

## Implementation and compatibility

All production behavior is in `src/*.kujo`. Python is used only by maintenance
fixtures and the frozen compatibility oracle. Artifact v1 schemas, CLI commands,
exit codes and defaults remain compatible. Install the exact runtime in
`KUJO_REVISION`: `2be1f04b89dbecd591ef1af0d68974c05586900e`.
Source ZIPs do not include a runtime binary. See the README for checksum and
installation instructions.

## Verified evidence

- [Native audit](audits/repository-hardening.md): 36 fixture tests and complete
  validation passed on Linux, macOS and Windows in
  [run 34119233850](https://github.com/kujolang/siteprobe/actions/runs/34119233850).
- Native Linux release: 10,000 HTTP 200 pages at concurrency 1/4/8/16, taking
  77.123/36.325/35.695/35.925 seconds. These are fixture observations, not universal
  throughput guarantees. Exact measurements and resource costs are in the audit.
- Runtime: 2,569 Rust tests, 150 CLI fixtures and 110 parity cases, with full
  hosted release gates passing. The audit preserves baseline failures separately.
- The tag workflow reruns full validation on Linux x64, macOS Intel/ARM64 and
  Windows x64 before publishing ZIPs and SHA-256 files. It verifies extracted
  package checksums, version, native doctor output and runtime-free source layout.

## Release procedure

1. Keep VERSION, kujo.toml, kujo.lock, README and CHANGELOG aligned.
2. Run `bash scripts/validate.sh`; build and smoke-test a checksummed package.
3. Commit and push a clean main, then push the annotated `v0.3.0` tag.
4. The release workflow publishes only after all platform jobs pass. Inspect the
   published assets and verify their checksums before calling the release complete.

The macOS Intel job uses `macos-15-intel`; the old macos-13 runner has been
[retired](https://github.com/actions/runner-images/issues/13046).
