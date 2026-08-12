#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KUJO_RUNTIME="${KUJO_BIN:-$ROOT/../kujo/target/release/kujo}"
cd "$ROOT"
if [[ ! -x "$KUJO_RUNTIME" ]]; then
  printf 'SiteProbe validation: Kujo runtime not found. Set KUJO_BIN.\n' >&2
  exit 2
fi
exec "$KUJO_RUNTIME" run scripts/validate.kujo -- "$KUJO_RUNTIME"
