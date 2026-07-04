# AuditAgent Input Contract

## What the agent may receive
- Intake handoff.
- Task plan and trace index.
- Existing logs, reports, configs, or artifact references.

## Required upstream handoff
`handoffs/HANDOFF_001_INTAKE_TO_AUDIT.md`

## Required artifacts
- `trace/RUN_001_INTAKE.md`
- Declared input evidence paths.

## Required frontmatter fields
The upstream handoff must include `doc_type`, `task_id`, `handoff_id`, `from_agent`, `to_agent`, `from_run`, `target_run`, and `expected_output`.

## Input validation obligations
Confirm audit is read-only and paths are within the declared workspace.

## Missing-input behavior
Stop and write a missing-input audit status. Do not mutate files to compensate.
