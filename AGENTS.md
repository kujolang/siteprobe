# SiteProbe Agent Instructions

SiteProbe observes websites as crawlable information systems. Preserve its
same-origin, read-only, robots-respecting defaults and versioned artifact
contract. Do not turn it into browser automation, an SEO advisor, a security
scanner, a JavaScript renderer, or a search-engine emulator.

Run `bash scripts/validate.sh` before committing. Never add form submission,
credential capture, cross-origin crawling by default, or unbounded output.

Product source is native Kujo under `src/`; do not delegate product behavior to
Python or host subprocesses. `tests/legacy/siteprobe.py` is a frozen compatibility
oracle. Python is permitted for fixture servers and repository benchmarks only.
The pinned Kujo revision supplies generic bounded web-data mechanisms. Run the
fixture suite with `KUJO_BIN` pointing at that runtime. Large artifacts use
`json_file_read`/JSONL streaming, not the 8 MiB whole-file helpers.

`src/siteprobe.kujo` is the authoritative core, organized by labeled sections.
Keep function boundaries explicit. Splitting its hot helpers into imported
modules previously increased the 200-page fixture from 3.33s to 15.39s because
Kujo copies captured environments on module calls; measure before changing this
layout. `src/main.kujo` remains the small native CLI entrypoint.
