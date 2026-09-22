# Kujo DocGen

- Root: `src`
- Languages: kujo
- Symbols: 71
- Gaps: 47

## main (kujo)

### main

- Kind: Function
- Visibility: Private
- Source: `main.kujo:4`
- Signature: `func()`

Native Kujo product entrypoint. Host mechanisms remain capability-gated.

## siteprobe (kujo)

### normalize

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:3`
- Signature: `func(value, base, cfg)`

COMMON
Shared deterministic transformations and bounded artifact I/O.

### origin

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:6`
- Signature: `func(url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### same_origin

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:7`
- Signature: `func(a, b)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### compact

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:8`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### fingerprint

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:9`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### unique

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:14`
- Signature: `func(values)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### words

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:19`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### directives

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:24`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### read_json

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:29`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### save_json

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:30`
- Signature: `func(path, value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### chunk

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:31`
- Signature: `func(path, offset)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### write_rows

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:32`
- Signature: `func(path, rows)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### sorted_rows

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:33`
- Signature: `func(rows, fields)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### absolute

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:43`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### user_agent

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:57`
- Signature: `func()`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### safe_text

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:58`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### report_text

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:59`
- Signature: `func(run, findings, max_tokens)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### nested_set

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:84`
- Signature: `func(object, section, key, value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### entry_exists

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:92`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### diagnostic

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:97`
- Signature: `func(message)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### terminal_text

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:98`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### robots_parse

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:103`
- Signature: `func(text)`

Merge matching robots groups and apply bounded RFC 9309 path matching.

### robots_allowed

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:159`
- Signature: `func(policy, url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### robots_path

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:175`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### percent_text

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:197`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### empty_page

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:215`
- Signature: `func(url, depth)`

PAGE

### unquote

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:218`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### parse_page_html

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:224`
- Signature: `func(body, base, cfg)`

Extract observed HTML structure from bounded standards-based tokenizer events.

### http_links

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:340`
- Signature: `func(value, base, cfg)`

Parse Link header delimiters outside quoted parameters and angle brackets.

### quoted_parts

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:376`
- Signature: `func(value, separator)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### private_reason

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:389`
- Signature: `func(url)`

NETWORK

### fetch

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:397`
- Signature: `func(url, cfg, extra_headers, maximum, policy, pacer, delay)`

GET with policy evaluated before every hop. Retries are bounded product policy.

### fetch_file

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:400`
- Signature: `func(url, cfg, maximum, pacer, delay, path, policy)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### fetch_into

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:403`
- Signature: `func(url, cfg, extra_headers, maximum, policy, pacer, delay, path, conditional_url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### decode_body

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:467`
- Signature: `func(raw, content_type)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### inspect_page

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:475`
- Signature: `func(job, cfg, sitemap_urls, policy, pacer, delay)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### looks_like_html

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:519`
- Signature: `func(raw)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### required_files

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:527`
- Signature: `func()`

ARTIFACTS

### finding

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:528`
- Signature: `func(check, target, severity, evidence)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### analyze

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:532`
- Signature: `func(pages_path, updated_path, sitemap, target, link_spool, stage, cfg)`

Analyze sorted JSONL in bounded batches, retaining only aggregate indexes.

### jsonl_array

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:611`
- Signature: `func(source, schema, name, destination)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### signing_key

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:614`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### manifest_write

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:623`
- Signature: `func(run, key)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### manifest_verify

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:633`
- Signature: `func(run, key)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_projection

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:669`
- Signature: `func(value, schema)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_check

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:680`
- Signature: `func(value, schema, label)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_batch

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:685`
- Signature: `func(value, schema, field, label)`

Batch arrays without aggregate constraints, preserving the enclosing schema.

### edge_identity

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:700`
- Signature: `func(source, target, text, rel, internal)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### validate_relationships

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:701`
- Signature: `func(run, data)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### validate_run

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:779`
- Signature: `func(run)`

Validate page schemas incrementally; whole pages.jsonl is never loaded.

### page_index

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:838`
- Signature: `func(run)`

Store bounded byte offsets instead of retaining complete baseline pages.

### indexed_page

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:853`
- Signature: `func(run, index, url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### relationship_inventory

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:857`
- Signature: `func(page, field)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### compare_runs

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:866`
- Signature: `func(old, new)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### cleanup_dir

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:901`
- Signature: `func(path)`

CRAWL

### stage_bytes

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:909`
- Signature: `func(stage)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### stage_reserve

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:917`
- Signature: `func(stage, cfg, additional)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### retained_reserve

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:921`
- Signature: `func(cfg, used)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### staged_rows

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:924`
- Signature: `func(stage, path, rows, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### staged_json

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:930`
- Signature: `func(stage, path, value, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### staged_sort

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:935`
- Signature: `func(stage, source, destination, fields, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### discover_sitemaps

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:940`
- Signature: `func(target, policy, cfg, pacer, delay, stage)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### crawl_into

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1001`
- Signature: `func(target, final_out, out, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### canonical_destination

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1131`
- Signature: `func(path)`

Canonicalize existing ancestors and normalize a not-yet-created destination.

### path_contains

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1150`
- Signature: `func(root, destination)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### validate_metrics_path

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1159`
- Signature: `func(path, output, baseline)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### crawl

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1172`
- Signature: `func(cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### usage

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1197`
- Signature: `func(command)`

CLI

### invalid

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1208`
- Signature: `func(message)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### dispatch

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1209`
- Signature: `func(argv)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

