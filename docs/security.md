# Security and crawl boundaries

- Only `http` and `https` targets are accepted.
- The initial origin is the allowlist. Cross-origin pages are recorded as links but never crawled.
- `robots.txt` is respected by default. `--ignore-robots` is an explicit operator override.
- Requests are GET-only, identify SiteProbe, have bounded timeouts, pages, depth, bytes, and concurrency, and never submit forms.
- Redirects that leave the origin are recorded but not enqueued for crawling.
- Output paths are resolved before writes; an existing non-directory is rejected.
- Responses are capped at 5 MiB per resource. Binary bodies are not retained.
- URLs containing user-info are rejected. Fragments are removed from normalized URLs.
- SiteProbe does not test vulnerabilities or authenticate to targets.
