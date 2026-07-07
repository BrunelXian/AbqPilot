# Controlled Solver Request Draft Schema Without Execution

Stage 5.2H creates a draft schema for a future controlled solver request.

It reads the Stage 5.2F smoke human approval gate, the Stage 5.2G execution handoff draft, and the smoke candidate artifact. It verifies the candidate SHA256 hash binding before writing draft-only schema artifacts.

## Output Locations

Stage 5.2H writes only non-active draft/schema files:

- `runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/artifacts/request_drafts/CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA.json`
- `runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/artifacts/request_drafts/CONTROLLED_SOLVER_REQUEST_DRAFT_EXAMPLE.json`
- `runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/artifacts/request_drafts/CONTROLLED_SOLVER_REQUEST_DRAFT_VALIDATION.json`
- `gui_high_risk_gate_ux/controlled_solver_request_draft_schema/`

It does not create active `solver_request.json`.

## Safety Boundary

Stage 5.2H does not create `job_request.json`, `abaqus_job.json`, `.bat` or `.cmd` solver launchers, active execution handoffs, queue files, ODB files, metrics files, or `TASK_FINAL_EVIDENCE_LEDGER.md`.

It does not run solver, open ODB, extract metrics, approve metrics, approve final evidence, or freeze verdict.

## Claim Boundary

The draft may state that a future request would target `ExecutionAgent`, identify a solver command label, and preview a future output directory.

It must also state:

- `draft_only=true`
- `request_active=false`
- `executable_request=false`
- `solver_command_path_included=false`
- `solver_command_not_invoked=true`
- `output_dir_created=false`
- `solver_execution_allowed=false`
- `solver_request_created=false`
- `solver_run=false`
- `downstream_execution_auto_start=false`
- `final_evidence_approved=false`
- `final_verdict_frozen=false`

Solver execution remains a future separate explicit stage.

## Stage 5.2I Relationship

Stage 5.2I validates this request draft as a preflight-only readiness check. A preflight pass is not execution permission and does not create `solver_request.json`, output execution directories, or solver launchers.

## Stage 5.2J Relationship

Stage 5.2J adds dry-run-only request materialization from the validated draft/preflight chain. It still does not create active `solver_request.json`, `job_request.json`, `abaqus_job.json`, output execution directories, queue entries, solver execution, ODB, metrics approval, final evidence approval, or verdict freeze.
