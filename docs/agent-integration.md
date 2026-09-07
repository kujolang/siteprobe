# Agent integration

Consume `run.json` for run identity and configuration, `pages.jsonl` for
per-URL evidence, `links.json` for graph work, and `findings.json` for
deterministic observations. Agents must preserve the difference between a
locally indexable page and a provider-confirmed indexed page. SiteProbe
findings are evidence inputs, not recommendations or proof of search impact.

ContentGraph may consume the link and page artifacts. Eval and workflows
should run `siteprobe validate` before trusting a run. RunLedger should record
the run directory and command rather than copying full page text into receipts.

Automation should pass an explicit `--out` path, treat it as immutable, and use
`--fail-on warning` or `--fail-on error` when SiteProbe is a CI gate. A non-zero
gate exit does not discard evidence: a valid completed run is still published.
Do not add `--allow-private-network` unless the operator has authorized the
target network.

For remotely transferred evidence, run `siteprobe verify` before `validate`.
Consumers can distinguish conditional baseline reuse with `not_modified=true`
and `response_status=304`; the stable semantic `status` remains the baseline
page status. `hreflang`, meta refresh, and HTTP `Link` relationships are explicit
page fields rather than inferred recommendations.

Executable integration examples for ContentGraph, Eval, RunLedger, and CI
baseline promotion live in [`examples/`](../examples/README.md).

`--deterministic` sets per-page `elapsed_ms` to zero; ordinary runs preserve
observed timing. Treat report token counts as a four-bytes-per-token estimate,
not a model-tokenizer measurement. Native commands write complete requested JSON
straight to stdout; use artifact paths for efficient handoffs. Validation reads
pages incrementally and accepts artifacts up to the documented 256 MiB per-file
limit. Large array schemas are checked in bounded batches without weakening
required fields or uniqueness checks. See [the audit](audits/repository-hardening.md)
for native compatibility and large-artifact regression evidence.
