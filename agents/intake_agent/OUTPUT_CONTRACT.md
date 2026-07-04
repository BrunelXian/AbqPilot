# IntakeAgent Output Contract

## Required RUN_XXX.md output
`trace/RUN_001_INTAKE.md`

## Required downstream HANDOFF_XXX.md output if applicable
`handoffs/HANDOFF_001_INTAKE_TO_AUDIT.md`

## Required artifact references
Reference declared input paths and any intake artifact directory.

## Required forbidden-action confirmation
Confirm no solver, ODB open, model mutation, QueueRunner, Codex CLI, or environment secret read occurred.

## Gate requirement metadata
Declare whether candidate build or execution gates are expected later.

## Claim boundary requirement
State that intake does not prove physical correctness or final evidence.
