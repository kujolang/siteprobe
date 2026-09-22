# September 22 hardening evidence

- `baseline*`: unchanged repository gate and 46-test receipt.
- `capture-regression.json`: isolated native oversized-child reproduction, previously successful partial output now rejected.
- `headers-*`, `partitions-*`: red/green behavioral reproductions; no frozen oracle edits.
- `pinned-before.json`, `pinned-after.json`: same-runtime 200-page observations.
- `standard-10000.json`, `dense.json`, `multilingual.json`: complete successful workload qualification.
- `efficiency.json`: identical unique command sets, reduced duplicate work and normalized output bytes.
- `runtime-provenance.json`: exact pin, source checks and executable digest.
- `final-validation.log`, `final-tests.json`: complete final source gate, 49 tests.
- `consumer-qualification.json`: actual external consumer commits and successful isolated integration results.
- `package*`: checksummed archive and extracted source qualification.
- `ci-qualification.json`, `verification-*-tests.json`, `ci-*.json`: hosted Linux/macOS/Windows qualification, 49 tests per platform, and Linux workloads.
- `security/`: sealed independent offline source-review artifacts, no confirmed vulnerability.

No model-token reduction or controlled statistical speedup is claimed. Historical artifacts are preserved elsewhere.

`post-doc-contention*` and `recheck-*` preserve a later overloaded local rerun failure. Both unchanged baseline and current source timed out at the same existing 30-second bound; no assertions or limits were weakened. Earlier final-source local and all hosted qualification receipts are green.
