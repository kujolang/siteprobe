# Kujo DocGen

- Root: `src`
- Languages: kujo
- Symbols: 57
- Gaps: 45

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

Parse robots groups without network effects. Preserve first matching-group policy.

### robots_allowed

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:146`
- Signature: `func(policy, url)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### rule_path

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:157`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### percent_text

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:167`
- Signature: `func(value)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### empty_page

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:185`
- Signature: `func(url, depth)`

PAGE

### unquote

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:188`
- Signature: `func(text)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### parse_page_html

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:194`
- Signature: `func(body, base, cfg)`

Extract observed HTML structure from bounded standards-based tokenizer events.

### http_links

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:302`
- Signature: `func(value, base, cfg)`

Parse Link header delimiters outside quoted parameters and angle brackets.

### quoted_parts

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:338`
- Signature: `func(value, separator)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### private_reason

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:351`
- Signature: `func(url)`

NETWORK

### fetch

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:359`
- Signature: `func(url, cfg, extra_headers, maximum, policy, pacer, delay)`

GET with policy evaluated before every hop. Retries are bounded product policy.

### fetch_file

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:362`
- Signature: `func(url, cfg, maximum, pacer, delay, path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### fetch_into

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:365`
- Signature: `func(url, cfg, extra_headers, maximum, policy, pacer, delay, path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### decode_body

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:426`
- Signature: `func(raw, content_type)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### inspect_page

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:434`
- Signature: `func(job, cfg, sitemap_urls, policy, pacer, delay)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### looks_like_html

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:472`
- Signature: `func(raw)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### required_files

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:480`
- Signature: `func()`

ARTIFACTS

### finding

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:481`
- Signature: `func(check, target, severity, evidence)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### analyze

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:485`
- Signature: `func(pages_path, updated_path, sitemap, target, link_spool)`

Analyze sorted JSONL in bounded batches, retaining only aggregate indexes.

### jsonl_array

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:560`
- Signature: `func(source, schema, name, destination)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### signing_key

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:563`
- Signature: `func(path)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### manifest_write

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:572`
- Signature: `func(run, key)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### manifest_verify

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:582`
- Signature: `func(run, key)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_check

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:618`
- Signature: `func(value, schema, label)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### schema_batch

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:623`
- Signature: `func(value, schema, field, label)`

Batch arrays without aggregate constraints, preserving the enclosing schema.

### validate_run

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:639`
- Signature: `func(run)`

Validate page schemas incrementally; whole pages.jsonl is never loaded.

### page_index

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:677`
- Signature: `func(run)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### compare_runs

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:687`
- Signature: `func(old, new)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### cleanup_dir

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:714`
- Signature: `func(path)`

CRAWL

### discover_sitemaps

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:722`
- Signature: `func(target, policy, cfg, pacer, delay, stage)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### crawl_into

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:761`
- Signature: `func(target, final_out, out, cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### crawl

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:866`
- Signature: `func(cfg)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### usage

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:890`
- Signature: `func(command)`

CLI

### invalid

- Kind: Function
- Visibility: Private
- Source: `siteprobe.kujo:893`
- Signature: `func(message)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

### dispatch

- Kind: Function
- Visibility: Public
- Source: `siteprobe.kujo:894`
- Signature: `func(argv)`

Documentation needed.
This symbol was discovered from the source code, but no human-authored documentation was found.

