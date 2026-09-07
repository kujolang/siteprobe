# Security and crawl boundaries

- Only `http` and `https` targets are accepted.
- The initial origin is the allowlist. Cross-origin pages are recorded as links but never crawled.
- Pinned requests connect directly; proxy environment variables cannot substitute a different connection or resolver.
- Every request and redirect hop resolves immediately before connection, rejects the complete answer set if any address is non-public, and pins the socket to an approved address. Private, loopback, link-local, reserved, multicast, and unspecified addresses are blocked unless `--allow-private-network` is explicit.
- Kujo process-level destination restrictions may be stricter; `--allow-private-network` does not override the runtime capability or outbound-policy boundary.
- `robots.txt` is respected by default, including every page redirect destination. Unavailable/denied robots responses abort before crawling; 404/410 mean no rules. `--ignore-robots` is an explicit operator override.
- Requests are GET-only, identify SiteProbe, have bounded timeouts, retries, pages, depth, retained page structure, bytes, and concurrency, and never submit forms.
- Redirects that leave the origin are recorded and blocked before DNS resolution or connection.
- Output uses a private staging directory under its explicit parent; existing destination entries, including dangling symlinks, are rejected. OS no-replace rename prevents publication from overwriting a competing destination. Runs are staged beside the destination and atomically published only after analysis and budget checks.
- Validation rejects symbolic links for every required artifact before any artifact is printed or compared.
- Responses are capped at 5 MiB per resource. Binary bodies are not retained.
- Gzip sitemap inputs have independent compressed and expanded limits.
- Required artifacts are covered by `manifest.json`; `verify` checks file digests and uses constant-time HMAC signature verification. HMAC signing keys are read only from regular files and are never written into runs.
- URLs containing user-info are rejected. Fragments are removed from normalized URLs.
- SiteProbe does not test vulnerabilities or authenticate to targets.

Query dropping and deny lists can merge multiple source URLs into one normalized
identity. Operators should use them only when the affected parameters are known
not to change meaningful page content.

Local run directories and their parent directories must remain under operator
control during reads and writes. Artifact validation is not a sandbox against
concurrent hostile modification of the directory tree.

Manifest input and referenced artifacts are bounded to 256 MiB per file before
loading/hashing. Empty manifests cannot certify missing required artifacts.
Signing-key reads verify regular-file identity on the opened handle and bound
the read. External sorting opens at most 32 chunk inputs and one merge output.
Human reports remove ASCII terminal controls and use a deterministic UTF-8 byte
budget; exact findings remain in JSON. Product commands run directly in Kujo, so their output is not routed through a
bounded subprocess capture that could truncate JSON. Repository orchestration
retains detailed command logs separately.

The native migration uses WHATWG URL parsing for host and dot-segment resolution.
HTML tokenization rejects inputs over 8 MiB or over 1,000,000 events explicitly.
XML projection rejects DTDs, depth over 64, and selected text over 32 MiB; expanded
sitemap bytes remain independently bounded. Compressed sitemap limits now have
an explicit 512 MiB ceiling. These limits fail visibly rather than dropping data.
Process metrics are null on platforms where the runtime cannot measure them.
