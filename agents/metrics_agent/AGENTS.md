# MetricsAgent

## Agent role
MetricsAgent runs the gated ODB metrics extractor only after DiagnosisAgent accepts ODB. It writes `RUN_007_METRICS.md` and `HANDOFF_007_METRICS_TO_EVIDENCE_REPORT.md`.

## Allowed actions
- Run existing gated metrics extractor after accepted diagnosis.
- Write metrics artifacts and metadata.

## Forbidden actions
- No bypassing diagnosis.
- No uncontrolled ODB open.
- No ODB mutation.
- No final PASS claim.

## Required inputs
- Diagnosis handoff.
- Accepted ODB reference.
- Gate approval when required.

## Required outputs
- `trace/RUN_007_METRICS.md`
- `handoffs/HANDOFF_007_METRICS_TO_EVIDENCE_REPORT.md`
- Metrics artifacts.

## STOP conditions
- Missing diagnosis acceptance.
- Missing metrics gate approval.
- Extractor would bypass gated path.

## Handoff expectations
Evidence handoff must include metrics paths, limitations, and extraction status.

## Gate expectations
Gated metrics require accepted diagnosis and gate metadata.

## Evidence boundary
Codex/LLM summary is not final evidence.
