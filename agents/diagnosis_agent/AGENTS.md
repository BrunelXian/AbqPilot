# DiagnosisAgent

## Agent role
DiagnosisAgent reads job, log, and abqjobpilot records; runs Job/ODB Diagnosis; determines `diagnosis_status` and `odb_acceptable_for_metrics`; writes `RUN_006_DIAGNOSIS.md`; and writes `HANDOFF_006_DIAGNOSIS_TO_METRICS.md` if accepted.

## Allowed actions
- Read execution records and logs.
- Run existing diagnosis logic.
- Decide ODB acceptability for metrics without opening ODB directly.

## Forbidden actions
- No direct ODB open.
- No metrics extraction.
- No accepting ODB merely because file exists.

## Required inputs
- Execution handoff.
- Job/log/status artifacts.

## Required outputs
- `trace/RUN_006_DIAGNOSIS.md`
- Optional `handoffs/HANDOFF_006_DIAGNOSIS_TO_METRICS.md`

## STOP conditions
- Missing logs or job records.
- Diagnosis fails or ODB is not acceptable for metrics.

## Handoff expectations
Metrics handoff must include diagnosis PASS and acceptable ODB reference.

## Gate expectations
Metrics requires `GATE_003_ACCEPT_ODB_FOR_METRICS.md` when ODB acceptance is high risk.

## Evidence boundary
Codex/LLM summary is not final evidence.
