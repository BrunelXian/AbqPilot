# GuardAgent Output Contract

## Required RUN_XXX.md output
`trace/RUN_004_GUARD_VALIDATION.md`

## Required downstream HANDOFF_XXX.md output if applicable
`handoffs/HANDOFF_004_GUARD_TO_EXECUTION.md`

## Required artifact references
Reference StaticValidator, DiffGuard, PhysicsGuard, and MCPGuard outputs when applicable.

## Required forbidden-action confirmation
Confirm no solver, ODB open, candidate repair, or final evidence freeze occurred.

## Gate requirement metadata
If execution is recommended, require `GATE_002_ALLOW_EXECUTION.md` and human approval metadata.

## Claim boundary requirement
Guard PASS means eligibility for next stage, not physical success.
