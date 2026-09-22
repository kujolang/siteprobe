# SiteProbe artifact contract reference

Generated from the checked-in Draft 2020-12 JSON Schemas by `scripts/generate_contract_docs.kujo`.

## findings.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/findings.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `findings`

## links.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/links.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `links`

## manifest.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/manifest.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `digest_algorithm`, `artifacts`, `signature`

## metadata.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/metadata.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `titles`, `descriptions`

## page.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/page.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `url`, `final_url`, `status`, `depth`, `indexable`, `links`, `content_fingerprint`

## redirects.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/redirects.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `redirects`

## robots.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/robots.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `url`, `status`, `text_fingerprint`, `error`, `sitemaps`

## run.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/run.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `run_id`, `started_at`, `completed_at`, `target`, `configuration`, `counts`

## site.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/site.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `target`, `origin`, `robots_url`, `sitemaps`, `crawlable_pages`, `indexable_pages`

## sitemap.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/sitemap.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `sitemaps`, `urls`, `errors`

## structured-data.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/structured-data.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `pages`

