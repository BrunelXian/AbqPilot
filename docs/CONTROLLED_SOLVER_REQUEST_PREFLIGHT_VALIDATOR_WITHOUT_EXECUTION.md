# Controlled Solver Request Preflight Validator Without Execution

Stage 5.2I validates the controlled solver request draft before a future execution stage.

The preflight reads the Stage 5.2F smoke human gate, Stage 5.2G execution handoff draft, Stage 5.2H request draft schema, and smoke candidate artifact. It verifies structure, policy fields, and candidate SHA256 hash binding.

## Safety Boundary

Stage 5.2I does not create active `solver_request.json`, `job_request.json`, or `abaqus_job.json`.

It does not create solver launchers, output execution directories, queue files, active execution handoffs, ODB files, metrics files, or `TASK_FINAL_EVIDENCE_LEDGER.md`.

It does not run solver, call Abaqus, open ODB, extract metrics, approve metrics, approve final evidence, or freeze verdict.

## Preflight Scope

The preflight may report:

- source gate validated
- source handoff draft validated
- request draft validated
- candidate hash verified
- solver command label validated without invocation
- output directory policy validated without directory creation
- resource policy shape validated without process execution

Preflight pass is not solver execution permission.

## Required Flags

The preflight result must keep:

- `preflight_only=true`
- `active_request_created=false`
- `request_active=false`
- `executable_request=false`
- `solver_execution_allowed=false`
- `solver_request_created=false`
- `solver_run=false`
- `downstream_execution_auto_start=false`
- `final_evidence_approved=false`
- `final_verdict_frozen=false`

Solver execution remains a future separate explicit stage.

## Stage 5.2J Relationship

Stage 5.2J may consume this preflight result to materialize a dry-run-only request artifact. That artifact is still not an active `solver_request.json`, not a job request, not queue submission, and not solver execution permission.

Stage 5.3A is the first controlled solver invocation stage, but only for the dedicated demo smoke task and copied demo INP. The preflight result is not permission for arbitrary task execution.

The Stage 5.3A demo corridor still does not open ODB, extract metrics, approve final evidence, or freeze verdict.
