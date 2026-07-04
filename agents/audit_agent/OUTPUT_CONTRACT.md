# AuditAgent Output Contract

## Required RUN_XXX.md output
`trace/RUN_002_AUDIT.md`

## Required downstream HANDOFF_XXX.md output if applicable
`handoffs/HANDOFF_002_AUDIT_TO_CANDIDATE_BUILDER.md`

## Required artifact references
Reference every inspected file or report path used to support findings.

## Required forbidden-action confirmation
Confirm no file mutation, solver, ODB open, patch generation, environment read, or shell bypass occurred.

## Gate requirement metadata
Declare whether candidate build needs a gate before proceeding.

## Claim boundary requirement
State that audit findings are read-only observations, not final physical evidence.
