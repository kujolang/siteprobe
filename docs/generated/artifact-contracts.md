# SiteProbe artifact contract reference

Generated from the checked-in Draft 2020-12 JSON Schemas by `scripts/generate_contract_docs.kujo`.

## run.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/run.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `run_id`, `started_at`, `completed_at`, `target`, `configuration`, `counts`

## page.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/page.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `url`, `final_url`, `status`, `depth`, `indexable`, `links`, `content_fingerprint`

## findings.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/findings.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `findings`

## manifest.schema.json

- Schema ID: `https://schemas.kujolang.ai/siteprobe/manifest.v1.json`
- Draft: `https://json-schema.org/draft/2020-12/schema`
- Required fields: `schema`, `digest_algorithm`, `artifacts`, `signature`

