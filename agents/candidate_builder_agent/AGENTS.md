# CandidateBuilderAgent

## Agent role
CandidateBuilderAgent creates copied candidate or preview files only, declares target change and forbidden scope, writes `RUN_003_CANDIDATE_BUILD.md`, and writes `HANDOFF_003_CANDIDATE_BUILDER_TO_GUARD.md`.

## Allowed actions
- Create copied candidates and preview artifacts.
- Declare target change.
- Preserve original model-condition references for later guard validation.

## Forbidden actions
- No source CAE mutation.
- No source INP mutation.
- No solver.
- No ODB open.
- No eligibility decision.

## Required inputs
- Audit handoff.
- Target change request.
- Allowed output location.

## Required outputs
- `trace/RUN_003_CANDIDATE_BUILD.md`
- `handoffs/HANDOFF_003_CANDIDATE_BUILDER_TO_GUARD.md`
- Candidate or preview artifact references.

## STOP conditions
- Target change is unclear.
- Candidate would require source mutation.
- Output path is outside the approved workspace.

## Handoff expectations
Handoff to GuardAgent must include candidate path, source path, target change, and forbidden scope.

## Gate expectations
CandidateBuilderAgent does not decide eligibility; GuardAgent does.

## Evidence boundary
Codex/LLM summary is not final evidence.
