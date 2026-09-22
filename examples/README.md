# SiteProbe integration examples

All examples consume a completed, validated run and remain network-free.

```bash
kujo run examples/contentgraph.kujo -- .siteprobe/run
kujo run examples/eval.kujo -- .siteprobe/run
kujo run examples/runledger.kujo -- .siteprobe/run
kujo run examples/ci_baseline.kujo -- .siteprobe/baseline .siteprobe/candidate
```

- `contentgraph.kujo` emits a normalized edge projection for custom consumers.
  ContentGraph itself accepts the validated run directory via `build --siteprobe RUN`.
- `eval.kujo` is a deterministic error-severity release gate.
- `runledger.kujo` emits a compact receipt without copying page content.
- `ci_baseline.kujo` validates and compares two immutable runs through the SiteProbe CLI.

Create a safe public fixture first when needed:

```bash
./siteprobe crawl https://example.com --max-pages 10 --max-depth 2 --out .siteprobe/example
./siteprobe validate .siteprobe/example
```

## Actual consumer qualification

Run the native, local integration gate with explicit checkout paths:

```bash
"$KUJO_BIN" run scripts/verify_integrations.kujo -- /path/to/contentgraph /path/to/eval /path/to/runledger
```

It creates a fresh SiteProbe run, builds a real ContentGraph graph, executes an
Eval artifact suite, and records/reads a terminal RunLedger receipt in an isolated
ledger. The receipt at `.siteprobe/verification/consumer-qualification.json` records
actual consumer versions and source commits. The small projection examples do not
claim to be native import formats for every consumer version.
