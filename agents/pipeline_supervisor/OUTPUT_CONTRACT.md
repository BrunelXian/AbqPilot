# PipelineSupervisor Output Contract

## Required RUN_XXX.md output
PipelineSupervisor does not normally create a pipeline station RUN file, but must record supervisor decisions in the relevant GATE or final ledger.

## Required downstream HANDOFF_XXX.md output
No downstream handoff is required. The supervisor observes, gates, and freezes.

## Required artifact references
Gate and freeze decisions must reference trace, handoff, validator, diagnosis, metrics, or ledger artifacts.

## Required forbidden-action confirmation
Confirm solver, QueueRunner, ODB, source mutation, environment-read, and shell safety flags before high-risk approval.

## Gate requirement metadata
Every high-risk transition must include a `GATE_XXX.md` decision with approver and required-condition status.

## Claim boundary requirement
Do not freeze claims from Codex/LLM summaries alone.
