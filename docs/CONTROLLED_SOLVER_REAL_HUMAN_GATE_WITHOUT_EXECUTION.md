# Controlled Solver Real Human Gate Without Execution

Stage 5.2F creates a real human approval gate only for the dedicated smoke task.

The dedicated smoke task is `runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/`.

Arbitrary real task gate writing remains disabled. Human approval gate creation does not execute solver. No solver request files are created. No Abaqus solver command is executed. No ODB/metrics/final evidence authority is granted. Solver execution remains a future separate explicit stage. `TASK_FINAL_EVIDENCE_LEDGER.md` remains untouched.

## Gate Semantics

The Stage 5.2F gate may contain:

- `decision=APPROVED_BY_HUMAN`
- `approval_status=APPROVED_BY_HUMAN`
- `solver_approved=true`

It must also contain:

- `solver_execution_allowed=false`
- `solver_request_created=false`
- `solver_run=false`
- `queue_runner_launched=false`
- `odb_opened=false`
- `odb_metrics_approved=false`
- `final_evidence_approved=false`
- `final_verdict_frozen=false`
- `task_final_evidence_ledger_updated=false`
- `downstream_execution_stage_required=true`
- `downstream_execution_auto_start=false`

This is a human approval gate only. It is not a solver execution command, job request, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.

## Smoke Task Files

Stage 5.2F creates:

- `TASK_PLAN.md`
- `TRACE_INDEX.md`
- `trace/RUN_001_CONTROLLED_SOLVER_GATE_PRECHECK.md`
- `trace/RUN_002_CONTROLLED_SOLVER_ACTIVE_GATE_CREATION.md`
- `handoffs/HANDOFF_001_CONTROLLED_SOLVER_GATE_TO_FUTURE_EXECUTION_DESIGN.md`
- `gates/GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.md`
- `gates/GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json`
- `artifacts/candidates/candidate_controlled_solver_smoke.inp`
- `artifacts/approvals/HUMAN_APPROVAL_TOKEN_PREVIEW.json`
- `reports/CONTROLLED_SOLVER_GATE_CREATION_REPORT.md`

The handoff is design-only and contains `handoff_active_for_execution=false`, `future_stage_required=true`, `solver_auto_start=false`, and `solver_request_created=false`.

## Non-Final Reports

Stage 5.2F writes reports under `gui_high_risk_gate_ux/controlled_solver_real_gate_without_execution/` confirming no execution, no solver request, no ODB, no queue, no metrics approval, no final evidence approval, and no verdict freeze.

## Stage 5.2G Relationship

Stage 5.2G may derive a draft-only future `ExecutionAgent` handoff from this smoke gate. That draft is not an active execution handoff and still creates no solver request, job request, queue mutation, ODB, metrics approval, final evidence approval, or verdict freeze.

Stage 5.2H may derive a draft-only controlled solver request schema from the Stage 5.2G handoff draft. It does not create active `solver_request.json`, `job_request.json`, or `abaqus_job.json`.

Stage 5.2I may validate that draft schema as a preflight-only readiness report. It still does not create active request files or run solver.

Stage 5.2J preserves the same separation: the smoke human gate can feed dry-run request materialization, but the dry-run artifact is not solver execution permission and does not create active request files or output execution directories.
