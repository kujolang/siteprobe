# Security and crawl boundaries

- Only `http` and `https` targets are accepted.
- The initial origin is the allowlist. Cross-origin pages are recorded as links but never crawled.
- Non-public DNS results are blocked by default, including private, loopback, link-local, reserved, multicast, and unspecified addresses. `--allow-private-network` is an explicit authorized-use override.
- `robots.txt` is respected by default. `--ignore-robots` is an explicit operator override.
- Requests are GET-only, identify SiteProbe, have bounded timeouts, retries, pages, depth, retained page structure, bytes, and concurrency, and never submit forms.
- Redirects that leave the origin are recorded but not enqueued for crawling.
- Output paths are resolved before writes and must not exist. Runs are staged beside the destination and atomically published only after validation and budget checks.
- Validation rejects symbolic links for every required artifact before any artifact is printed or compared.
- Responses are capped at 5 MiB per resource. Binary bodies are not retained.
- URLs containing user-info are rejected. Fragments are removed from normalized URLs.
- SiteProbe does not test vulnerabilities or authenticate to targets.

The public-address preflight materially reduces accidental server-side request
forgery exposure but does not pin DNS answers to individual connections. Run
SiteProbe only against intended targets; DNS pinning is tracked in the
[next-session roadmap](next-session-roadmap.md).
