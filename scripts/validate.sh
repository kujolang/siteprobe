#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KUJO_RUNTIME="${KUJO_BIN:-$ROOT/../kujo/target/release/kujo}"
cd "$ROOT"
python3 -m py_compile bridge/siteprobe.py tests/test_siteprobe.py
python3 tests/test_siteprobe.py
"$KUJO_RUNTIME" check siteprobe.kujo
"$KUJO_RUNTIME" run tests/siteprobe_tests.kujo
python3 -m json.tool schemas/run.schema.json >/dev/null
python3 -m json.tool schemas/page.schema.json >/dev/null
python3 -m json.tool schemas/findings.schema.json >/dev/null
git diff --check
printf 'SiteProbe validation passed.\n'
