# MetricsAgent Input Contract

## What the agent may receive
- Diagnosis handoff.
- Accepted ODB reference.
- Metrics extraction contract.

## Required upstream handoff
`handoffs/HANDOFF_006_DIAGNOSIS_TO_METRICS.md`

## Required artifacts
- Diagnosis report with `odb_acceptable_for_metrics`.
- Gate decision if required.

## Required frontmatter fields
Handoff frontmatter must include `task_id`, `from_agent`, `to_agent`, `from_run`, `target_run`, and `expected_output`.

## Input validation obligations
Confirm ODB acceptance came from DiagnosisAgent and extraction path is controlled.

## Missing-input behavior
Stop and do not run metrics extraction.
