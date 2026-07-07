# Controlled Solver Execution Handoff Draft Without Execution

Stage 5.2G creates a draft-only future `ExecutionAgent` handoff from the Stage 5.2F smoke human approval gate.

The draft is written only to non-active draft/report locations:

- `runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/artifacts/handoff_drafts/`
- `gui_high_risk_gate_ux/controlled_solver_execution_handoff_draft/`

It does not create an active execution handoff under task `handoffs/`.

## Safety Boundary

Stage 5.2G does not create solver request files, job request files, Abaqus job files, `.bat` or `.cmd` solver launchers, queue files, ODB files, metrics files, or `TASK_FINAL_EVIDENCE_LEDGER.md`.

It does not run solver, open ODB, extract metrics, approve metrics, approve final evidence, or freeze verdict.

## Claim Boundary

The handoff draft may state that the Stage 5.2F source gate exists, the source gate decision is `APPROVED_BY_HUMAN`, the candidate hash is verified, and a future `ExecutionAgent` stage is required.

It must also state:

- `draft_only=true`
- `active_execution_handoff=false`
- `handoff_active_for_execution=false`
- `execution_status=NOT_EXECUTABLE`
- `solver_execution_allowed=false`
- `solver_request_created=false`
- `solver_run=false`
- `downstream_execution_auto_start=false`
- `final_evidence_approved=false`
- `final_verdict_frozen=false`

Solver execution remains a future separate explicit stage.

## Stage 5.2H Relationship

Stage 5.2H may derive a controlled solver request draft schema from this handoff draft. The request draft is not an active `solver_request.json`, not a job request, not an Abaqus command, and not permission to execute solver.

Stage 5.2I may validate the request draft as preflight-only. The preflight report is not an active request and does not permit solver execution.

Stage 5.2J can materialize an inert dry-run request artifact downstream of this handoff draft. The handoff remains draft-only and the dry-run request remains non-active; no active execution handoff or solver request is created.
