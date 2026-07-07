# Controlled Solver Execution Dry-Run Request Materialization

Stage 5.2J materializes a dry-run-only controlled solver request artifact from the Stage 5.2I preflight result.

The dry-run artifact is written as `CONTROLLED_SOLVER_DRY_RUN_REQUEST.json` and `CONTROLLED_SOLVER_DRY_RUN_REQUEST.md` under the Stage 5.2F smoke task `artifacts/dry_run_requests/` directory. It is intentionally not named `solver_request.json`, `job_request.json`, or `abaqus_job.json`.

This stage does not create active `solver_request.json`, `job_request.json`, or `abaqus_job.json`. It does not create an output execution directory, run solver, call Abaqus, create queue entries, open ODB, extract metrics, approve metrics, approve final evidence, freeze verdict, or update `TASK_FINAL_EVIDENCE_LEDGER.md`.

Dry-run request materialization is not execution permission. Solver execution remains a future separate explicit stage, and any future active request must be created by a later gate with its own safety boundary.

Required safety flags remain false: `active_request_created`, `request_active`, `executable_request`, `solver_execution_allowed`, `solver_request_created`, `solver_run`, `queue_runner_launched`, `queue_entry_created`, `output_dir_created`, `odb_opened`, `odb_metrics_approved`, `final_evidence_approved`, `final_verdict_frozen`, and `task_final_evidence_ledger_updated`.

Stage 5.3A consumes this corridor design by creating one scoped demo `solver_request.json` only under `runs/tasks/stage5_3a_controlled_solver_demo_smoke/`. That later stage still does not open ODB, extract metrics, approve final evidence, or freeze verdict.
