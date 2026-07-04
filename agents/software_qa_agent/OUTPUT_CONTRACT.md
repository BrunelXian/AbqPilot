# SoftwareQAAgent Output Contract

## Required RUN_XXX.md output
QA output should be recorded in a RUN report when part of a pipeline task.

## Required downstream HANDOFF_XXX.md output if applicable
Create handoff only when another station must act on QA findings.

## Required artifact references
Reference test output, audit output, and changed files reviewed.

## Required forbidden-action confirmation
Confirm no solver, ODB open, source simulation mutation, shell bypass, or secret exposure.

## Gate requirement metadata
QA can recommend blocking a gate but cannot approve high-risk execution alone.

## Claim boundary requirement
QA evidence is software evidence, not physical evidence.
