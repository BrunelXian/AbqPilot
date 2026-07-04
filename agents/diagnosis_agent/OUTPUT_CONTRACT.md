# DiagnosisAgent Output Contract

## Required RUN_XXX.md output
`trace/RUN_006_DIAGNOSIS.md`

## Required downstream HANDOFF_XXX.md output if applicable
`handoffs/HANDOFF_006_DIAGNOSIS_TO_METRICS.md`

## Required artifact references
Reference diagnosis report, job records, logs, and accepted ODB path when applicable.

## Required forbidden-action confirmation
Confirm no direct ODB open, no metrics extraction, and no acceptance by existence alone.

## Gate requirement metadata
Declare whether `GATE_003_ACCEPT_ODB_FOR_METRICS.md` is required and approved.

## Claim boundary requirement
Diagnosis acceptance only enables metrics; it does not prove final physical claims.
