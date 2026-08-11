# Examples

Fixture-first:

```bash
python3 tests/test_siteprobe.py
```

Safe public smoke:

```bash
./siteprobe crawl https://agents.kujolang.ai --max-pages 10 --max-depth 2 --out .siteprobe/agents-smoke
./siteprobe validate .siteprobe/agents-smoke
```
