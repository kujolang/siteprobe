# Agent integration

Consume `run.json` for run identity and configuration, `pages.jsonl` for
per-URL evidence, `links.json` for graph work, and `findings.json` for
deterministic observations. Agents must preserve the difference between a
locally indexable page and a provider-confirmed indexed page. SiteProbe
findings are evidence inputs, not recommendations or proof of search impact.

ContentGraph may consume the link and page artifacts. Eval and workflows
should run `siteprobe validate` before trusting a run. RunLedger should record
the run directory and command rather than copying full page text into receipts.
