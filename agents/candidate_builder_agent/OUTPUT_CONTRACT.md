# CandidateBuilderAgent Output Contract

## Required RUN_XXX.md output
`trace/RUN_003_CANDIDATE_BUILD.md`

## Required downstream HANDOFF_XXX.md output if applicable
`handoffs/HANDOFF_003_CANDIDATE_BUILDER_TO_GUARD.md`

## Required artifact references
Reference candidate, preview, source, and target-change artifacts.

## Required forbidden-action confirmation
Confirm no source CAE/INP mutation, no solver, no ODB open, and no eligibility decision occurred.

## Gate requirement metadata
Declare that GuardAgent validation is required before execution planning.

## Claim boundary requirement
Candidate creation is not validation and is not final evidence.
