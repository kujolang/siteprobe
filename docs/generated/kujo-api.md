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
- Source: `siteprobe.kujo:54`
- Signature: `func()`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### safe_text

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:55`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### report_text

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:56`
- Signature: `func(run, findings, max_tokens)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### nested_set

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:81`
- Signature: `func(object, section, key, value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### entry_exists

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:89`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### diagnostic

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:94`
- Signature: `func(message)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### terminal_text

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:95`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### robots_parse

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:100`
- Signature: `func(text)`

Merge matching robots groups and apply bounded RFC 9309 path matching.

### robots_allowed

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:156`
- Signature: `func(policy, url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### robots_path

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:172`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### percent_text

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:194`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### empty_page

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:212`
- Signature: `func(url, depth)`

PAGE

### unquote

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:215`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### parse_page_html

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:221`
- Signature: `func(body, base, cfg)`

Extract observed HTML structure from bounded standards-based tokenizer events.

### http_links

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:337`
- Signature: `func(value, base, cfg)`

Parse Link header delimiters outside quoted parameters and angle brackets.

### quoted_parts

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:373`
- Signature: `func(value, separator)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### private_reason

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:386`
- Signature: `func(url)`

NETWORK

### fetch

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:394`
- Signature: `func(url, cfg, extra_headers, maximum, policy, pacer, delay)`

GET with policy evaluated before every hop. Retries are bounded product policy.

### fetch_file

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:397`
- Signature: `func(url, cfg, maximum, pacer, delay, path, policy)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### fetch_into

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:400`
- Signature: `func(url, cfg, extra_headers, maximum, policy, pacer, delay, path, conditional_url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### decode_body

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:464`
- Signature: `func(raw, content_type)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### inspect_page

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:472`
- Signature: `func(job, cfg, sitemap_urls, policy, pacer, delay)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### looks_like_html

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:516`
- Signature: `func(raw)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### required_files

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:524`
- Signature: `func()`

ARTIFACTS

### finding

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:525`
- Signature: `func(check, target, severity, evidence)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### analyze

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:529`
- Signature: `func(pages_path, updated_path, sitemap, target, link_spool, stage, cfg)`

Analyze sorted JSONL in bounded batches, retaining only aggregate indexes.

### jsonl_array

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:608`
- Signature: `func(source, schema, name, destination)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### signing_key

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:611`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### manifest_write

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:620`
- Signature: `func(run, key)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### manifest_verify

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:630`
- Signature: `func(run, key)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_projection

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:666`
- Signature: `func(value, schema)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_check

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:677`
- Signature: `func(value, schema, label)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_batch

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:682`
- Signature: `func(value, schema, field, label)`

Batch arrays without aggregate constraints, preserving the enclosing schema.

### edge_identity

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:697`
- Signature: `func(source, target, text, rel, internal)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### validate_relationships

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:698`
- Signature: `func(run, data)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### validate_run

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:776`
- Signature: `func(run)`

Validate page schemas incrementally; whole pages.jsonl is never loaded.

### page_index

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:835`
- Signature: `func(run)`

Store bounded byte offsets instead of retaining complete baseline pages.

### indexed_page

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:850`
- Signature: `func(run, index, url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### relationship_inventory

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:854`
- Signature: `func(page, field)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### compare_runs

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:863`
- Signature: `func(old, new)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### cleanup_dir

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:898`
- Signature: `func(path)`

CRAWL

### stage_bytes

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:906`
- Signature: `func(stage)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### stage_reserve

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:914`
- Signature: `func(stage, cfg, additional)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### retained_reserve

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:918`
- Signature: `func(cfg, used)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### staged_rows

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:921`
- Signature: `func(stage, path, rows, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### staged_json

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:927`
- Signature: `func(stage, path, value, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### staged_sort

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:932`
- Signature: `func(stage, source, destination, fields, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### discover_sitemaps

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:937`
- Signature: `func(target, policy, cfg, pacer, delay, stage)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### crawl_into

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:998`
- Signature: `func(target, final_out, out, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### canonical_destination

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1128`
- Signature: `func(path)`

Canonicalize existing ancestors and normalize a not-yet-created destination.

### path_contains

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1147`
- Signature: `func(root, destination)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### validate_metrics_path

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1156`
- Signature: `func(path, output, baseline)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### crawl

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1169`
- Signature: `func(cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### usage

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1194`
- Signature: `func(command)`

CLI

### invalid

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:1205`
- Signature: `func(message)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### dispatch

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:1206`
- Signature: `func(argv)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

