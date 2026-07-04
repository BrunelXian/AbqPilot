# DiagnosisAgent Input Contract

## What the agent may receive
- Execution handoff.
- Job outputs, logs, status records, and ODB path references.

## Required upstream handoff
`handoffs/HANDOFF_005_EXECUTION_TO_DIAGNOSIS.md`

## Required artifacts
- Execution report.
- Job/log/status artifacts.

## Required frontmatter fields
The upstream handoff must define source run, target run, risk level, and expected output.

## Input validation obligations
Confirm execution artifacts exist and diagnosis can be performed without uncontrolled ODB open.

## Missing-input behavior
Stop and mark diagnosis incomplete.
