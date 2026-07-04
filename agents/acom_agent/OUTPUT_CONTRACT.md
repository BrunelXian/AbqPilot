# ACOMAgent Output Contract

## Required RUN_XXX.md output
When used in a pipeline task, reference ACOM work from a support RUN report.

## Required downstream HANDOFF_XXX.md output if applicable
Downstream handoff must mark outputs as pending AbqPilot revalidation.

## Required artifact references
Reference handoff package, structured result, and validation report paths.

## Required forbidden-action confirmation
Confirm no automatic Codex CLI call, no solver, no ODB open, and no validation bypass.

## Gate requirement metadata
ACOM cannot satisfy high-risk gates by itself.

## Claim boundary requirement
Codex summary is not final evidence.
