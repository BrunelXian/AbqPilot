# Task Workspace

Stage 2.1 adds a deterministic task workspace and pipeline runner around the existing CLI commands. It does not add a GUI, LLM runtime, Codex runtime, solver submission, or new Abaqus execution path.

## Structure

Each task run writes:

```text
runs/tasks/<task_id>/
|-- task_config.json
|-- task_state.json
|-- artifacts.json
|-- pipeline_trace.json
|-- final_result.json
`-- steps/
    |-- 01_export_cae/
    |   `-- step_result.json
    |-- 02_audit_heat_x2/
    |   `-- step_result.json
    |-- 03_abqjobpilot_preflight/
    |   `-- step_result.json
    |-- 04_abqjobpilot_dry_run_enqueue/
    |   `-- step_result.json
    |-- 05_jobpilot_enqueue_authorization/
    |   `-- step_result.json
    |-- 06_abqjobpilot_real_enqueue/
    |   `-- step_result.json
    |-- 07_abqjobpilot_status_poll/
    |   `-- step_result.json
    |-- 08_solver_intake/
    |   `-- step_result.json
    |-- 09_odb_metrics/
    |   `-- step_result.json
    `-- 10_compare_metrics/
        `-- step_result.json
```

Use `--task-id` for deterministic paths in tests or demonstrations. Without it, AbqPilot generates a timestamped task id from the task name.

## task_state.json

`task_state.json` records the task id, task name, timestamps, current status, current step, stop reason, completed and failed steps, skipped steps, human-action flags, safety flags, and a per-step state table. Solver submission, abqjobpilot, LLM runtime, and Codex runtime are false in Stage 2.x.

Step statuses:

- `PENDING`
- `RUNNING`
- `COMPLETED`
- `SKIPPED`
- `FAILED`
- `WAITING_FOR_MANUAL_ACTION`
- `STOPPED_BY_MODE_LIMIT`

Stop reasons:

- `STOPPED_BY_MODE_LIMIT`
- `NEED_EXPORTED_INP`
- `NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT`
- `NEED_JOBPILOT_PREFLIGHT_REQUEST`
- `NEED_JOBPILOT_AUTHORIZATION_EVIDENCE`
- `NEED_ABQJOBPILOT_JOB_ID`
- `NEED_MANUAL_SOLVER_OUTPUTS`
- `NEED_ODB_METRICS_JSON`
- `STEP_FAILED`
- `PIPELINE_COMPLETED`

## artifacts.json

`artifacts.json` is the GUI-ready artifact registry. It records generated and consumed paths, whether each file exists, and which step produced it.

## Step Directories

Each step writes `step_result.json` using the same structured result envelope as the CLI. The pipeline runner persists state and artifact updates after every step.

`03_abqjobpilot_preflight` writes:

- `abqjobpilot_job_request.json`
- `abqjobpilot_preflight_result.json`
- `abqjobpilot_command_preview.md`

This step is preflight-only. It imports only `abqjobpilot.api`. It does not open the abqjobpilot GUI, does not run `run_gui.py`, does not enqueue a job, does not mutate runtime queue/status files, and does not submit Abaqus.

`04_abqjobpilot_dry_run_enqueue` writes:

- `abqjobpilot_dry_run_request.json`
- `abqjobpilot_dry_run_enqueue_result.json`
- `abqjobpilot_dry_run_safety_report.json`
- `abqjobpilot_dry_run_preview.md`

Stage 2.4 calls abqjobpilot public enqueue API only with `dry_run=True`. It must not mutate runtime queue files or submit Abaqus jobs. The step snapshots `runtime/queue.json`, `runtime/live_status.json`, and `runtime/reports` before and after the dry-run call. If those paths change, the result is marked `ABQJOBPILOT_RUNTIME_MUTATION_DETECTED`.

`05_jobpilot_enqueue_authorization` writes:

- `jobpilot_enqueue_approval_request.json`
- `jobpilot_enqueue_authorization_report.json`
- `jobpilot_enqueue_authorization_report.md`

Stage 2.5 creates an approval request after dry-run evidence exists. It computes hashes for the candidate INP, job request, preflight result, and dry-run enqueue result. It validates an approval token only if a human created one through the explicit CLI command. The pipeline never creates the token automatically, never enqueues a job, and never submits Abaqus.

Approval tokens are stored at:

```text
runs/tasks/<task_id>/approvals/jobpilot_enqueue_approval_token.json
```

The token is bound to the exact evidence hashes, the approval phrase `I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK`, and an expiry time. A future real enqueue stage must remain separate.

`06_abqjobpilot_real_enqueue` writes:

- `abqjobpilot_real_enqueue_request.json`
- `abqjobpilot_real_enqueue_result.json`
- `abqjobpilot_real_enqueue_safety_report.json`
- `abqjobpilot_real_enqueue_preview.md`

Stage 2.6 is controlled queue enqueue only. It is disabled by default. It requires a valid approval token, matching evidence hashes, `allow_solver_submit=false`, `submission_mode=preview_only` or `enqueue_only`, and an explicit queue-only proof before calling `enqueue(..., dry_run=False)`. The mutation guard allows only `runtime/queue.json` to change. Changes to `runtime/live_status.json`, `runtime/reports`, or solver output files are rejected.

`07_abqjobpilot_status_poll` writes:

- `abqjobpilot_status_request.json`
- `abqjobpilot_status_result.json`
- `abqjobpilot_output_locator_result.json`
- `abqjobpilot_status_summary.json`
- `abqjobpilot_status_summary.md`

Stage 2.7 is read-only monitoring. It calls only `AbqJobPilotClient.status()` and `AbqJobPilotClient.locate_outputs()` through `abqjobpilot.api`. It never calls enqueue, never launches QueueRunner, never opens the abqjobpilot GUI, never submits Abaqus, and never opens ODB files. Status is normalized to `JOB_QUEUED`, `JOB_RUNNING`, `JOB_OUTPUTS_READY`, `JOB_ODB_MISSING`, `JOB_FAILED`, `JOB_LOCKED`, `JOB_UNKNOWN`, or `ABQJOBPILOT_UNAVAILABLE`. `JOB_OUTPUTS_READY` is used only when the public output locator confirms the expected ODB exists.

Stage 2.8 completed-job intake writes:

- `stage2_8_completed_job_intake_summary.json`
- `stage2_8_completed_job_intake_summary.md`

This command-level gate validates whether an abqjobpilot status poll or a manually supplied ODB path is sufficient to continue into the existing solver-intake and gated ODB metrics path. `JOB_QUEUED` and `JOB_RUNNING` leave the task at `WAITING_FOR_ABQJOBPILOT`. `JOB_ODB_MISSING` becomes `WAITING_FOR_SOLVER_OUTPUTS`. `JOB_FAILED` becomes `SOLVER_JOB_FAILED`. A manual ODB must exist, use the `.odb` extension, and have no sibling `.lck` file. The gate records accepted evidence but does not open ODB files and does not submit solver jobs.

Stage 2.9 deterministic evaluation and repair planning writes:

- `evaluation.json`
- `repair_plan.json`
- `repair_plan.md`

The evaluator reads existing metrics and comparison JSON. It supports `PASS`, `REPAIR_RECOMMENDED`, `FAIL_STOP`, and `INSUFFICIENT_METRICS`. The repair plan is rule-based and never mutates INP files. It allows future guarded patch categories such as heat-flux magnitude adjustment, step-time adjustment, or output-request adjustment, while forbidding material, geometry, mesh, boundary-condition, and solver-submit changes.

Stage 3.0 introduces GUI-facing state projections:

- module registry
- event stream
- task view model
- right-panel current-module model

These projections read `task_state.json`, `artifacts.json`, `pipeline_trace.json`, and `steps/*/step_result.json`. They do not run pipeline steps.

Stage 3.1 adds a local `tkinter` GUI alpha. Stage 3.4 upgrades it to GUI Beta. It loads a task directory, discovers recent tasks, displays modules, event stream, artifact previews, workflow presets, and the current-module right panel. Dangerous controls such as solver submit, QueueRunner launch, abqjobpilot GUI launch, LLM agent execution, and automatic INP repair are absent or disabled.

## Stage 3.8 Patch Queue Workflows

Patch queue workflow artifacts live under:

```text
<task_dir>\patch_queue_workflows\queue_<timestamp>\
```

Each workflow records:

- `patch_candidate_manifest.json`
- `patch_queue_workflow_request.json`
- `patch_queue_workflow_result.json`
- `patch_queue_summary.json`
- `patch_queue_summary.md`

Preflight-only mode adds patch-prefixed JobPilot preflight request/result and command preview artifacts. Dry-run enqueue mode adds patch-prefixed dry-run request/result/safety artifacts and `patch_candidate_approval_request.json`. Real queue-only mode requires a candidate-specific token at `approvals\patch_queue_approval_token.json` and writes patch-prefixed real enqueue request/result/safety artifacts. Status polling writes patch queue status and output locator artifacts.

A preview is eligible only when Stage 3.7 reported `PATCH_PREVIEW_READY`, StaticValidator/DiffGuard/PhysicsGuard all passed, unrelated changes are zero, the candidate INP exists, the source INP exists, no solver was submitted, no job was enqueued, and human review is required.

Stage 3.2 run report export writes:

- `reports/ABQPILOT_RUN_REPORT.json`
- `reports/ABQPILOT_RUN_REPORT.md`

Stage 3.3 alpha freeze export writes:

- `ALPHA_FREEZE_REPORT.json`
- `ALPHA_FREEZE_REPORT.md`
- `test_results.txt`
- `capability_matrix.md`
- `safety_boundary_matrix.md`
- `known_limitations.md`

## Manual Solver Boundary

The runner stops at `NEED_MANUAL_SOLVER_OUTPUTS` when existing manual solver outputs are not available. It sets:

```json
{
  "status": "WAITING_FOR_MANUAL_SOLVER",
  "requires_human_action": true,
  "human_action_reason": "Manual solver outputs are required before ODB metrics extraction."
}
```

Prepare-only mode intentionally stops before ODB read with `STOPPED_BY_MODE_LIMIT` when the configured stop point is reached.

## Resume, Skip, and Rerun

`PipelineRunner.resume()` loads an existing task workspace, skips completed steps by default, and continues from the first non-completed step. If the task is waiting for manual solver outputs, resume checks the solver output intake step again. If outputs are still missing, the task remains waiting.

Completed steps with existing `step_result.json` are skipped by default. The pipeline trace records `STEP_SKIPPED` with verdict `SKIPPED_EXISTING_COMPLETED_STEP`, while the original step state remains `COMPLETED`.

Forced rerun uses `run_step(step_name, force=True)` or CLI `--force-step`. Before rerun, the previous step directory is copied to:

```text
steps/<step_name>__rerun_backup_001/
```

The rerun increments `rerun_count`, writes a new `step_result.json`, records the backup path in `artifacts.json`, and appends trace events. Previous evidence is not deleted.

## GUI Readiness

The GUI consumes `task_state.json`, `artifacts.json`, `pipeline_trace.json`, `final_result.json`, and per-step `step_result.json` files. It should not duplicate simulation-critical logic. The right panel is driven by the view model and shows the current module, status, stage, input, output, guard state, next allowed action, and active artifacts.

GUI Beta actions are routed through `GuiActionController`. Every action returns a structured dictionary, catches exceptions, and blocks dangerous requests with `ACTION_BLOCKED_BY_SAFETY_BOUNDARY`.

## Safety Policy

The task workspace does not submit solver jobs. Stage 2.6 may enqueue to abqjobpilot queue only after all gates pass, but it does not launch QueueRunner, does not call Abaqus, does not open a GUI, and does not open ODB files. Stage 2.7 reads queue/status/output metadata only. Stage 2.8 validates already-existing output evidence only. Stage 2.9 creates deterministic reports only. Stage 2.4 dry-run enqueue is preview-only and guarded against runtime mutation. Stage 2.5 creates and validates human approval artifacts. It does not call LLMs. It does not call Codex as a runtime agent. CAE export and ODB metrics extraction remain gated through the existing Stage 1 tools.
