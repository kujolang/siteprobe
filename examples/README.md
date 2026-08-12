# SiteProbe integration examples

All examples consume a completed, validated run and remain network-free.

```bash
kujo run examples/contentgraph.kujo -- .siteprobe/run
kujo run examples/eval.kujo -- .siteprobe/run
kujo run examples/runledger.kujo -- .siteprobe/run
kujo run examples/ci_baseline.kujo -- .siteprobe/baseline .siteprobe/candidate
```

- `contentgraph.kujo` emits the normalized edge set expected by graph tooling.
- `eval.kujo` is a deterministic error-severity release gate.
- `runledger.kujo` emits a compact receipt without copying page content.
- `ci_baseline.kujo` validates and compares two immutable runs through the SiteProbe CLI.

Create a safe public fixture first when needed:

```bash
./siteprobe crawl https://example.com --max-pages 10 --max-depth 2 --out .siteprobe/example
./siteprobe validate .siteprobe/example
```
