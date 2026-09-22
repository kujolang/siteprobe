# Qualification evidence

Runtime: Kujo revision `2be1f04b89dbecd591ef1af0d68974c05586900e`, built locally
with `cargo build --release --locked`; source revision is also pinned in CI.

- `standard-10000.json`: complete 10,000-page native sweep at concurrency 1/4/8/16.
- `dense.json`: 25 pages, 2,000 additional links and 256 KiB JSON-LD per page, concurrency 1/4.
- `multilingual.json`: 50 pages including Japanese language/text/JSON-LD, concurrency 1/4.
- `consumer-qualification.json`: actual consumer command receipts with exact revisions.
- `validation.log`: native gate, including all 46 tests, immutable oracle, package checks and generated documentation.
- `release.log`: checksummed archive and extracted native validation/doctor/version.

Workload drivers validate every produced run and assert every requested page was
successfully fetched. Measurements are observations on this machine under concurrent
host load, not controlled performance comparisons. Peak RSS includes runtime and
native-library allocations; retained-evidence estimates are not hard RSS limits.
Transient absolute paths identify original local evidence, not portable dependencies.
