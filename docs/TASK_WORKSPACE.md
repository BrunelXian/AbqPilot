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

## Stage 3.9 Patched Job Intake

Patch queue workflows can be continued without starting solver execution:

- `poll-patch-queue` updates `patch_queue_status_request.json`, `patch_queue_status_result.json`, `patch_queue_output_locator_result.json`, `patch_queue_status_summary.json`, and `patch_queue_status_summary.md`.
- `intake-patched-job-output` writes `patched_job_output_intake_request.json`, `patched_job_output_intake_result.json`, `patched_job_output_intake_summary.json`, and `patched_job_output_intake_summary.md`.
- `extract-patched-job-metrics` writes `patched_job_metrics_request.json`, `patched_job_metrics_result.json`, `patched_job_metrics_summary.json`, and `patched_job_metrics_summary.md`.
- `report-patched-job` writes `patched_job_report.json` and `patched_job_report.md`.

`JOB_QUEUED` and `JOB_RUNNING` remain `WAITING_FOR_PATCHED_JOB`. `JOB_FAILED` becomes `PATCHED_JOB_FAILED`. `JOB_ODB_MISSING` becomes `WAITING_FOR_PATCHED_JOB_OUTPUTS`. `JOB_OUTPUTS_READY` or an explicitly supplied unlocked `.odb` path can be accepted by the intake gate. The intake gate does not open ODB files. Metrics extraction is blocked until accepted output exists and then uses only the existing gated ODB metrics extractor.

## Stage 3.9B Real Sanity-Base Candidate Recovery

Stage 3.7 / 3.8 / 3.8A fixture workflow evidence is workflow-only. It proves guard and queue mechanics, but it is not production solver-ready simulation evidence. Real candidate evidence must derive from the user-provided sanity base model or an INP exported from it.

Stage 3.9B writes real sanity-base-derived evidence under:

```text
runs\stage3_9b_real_sanity_base_patch_candidate\
```

Required artifacts include:

- `source_sanity_base_export.inp`
- `candidate_sanity_base_power_x2.inp`
- `source_classification_report.json`
- `real_sanity_base_patch_candidate_summary.json`
- `real_sanity_base_patch_candidate_summary.md`
- `patch_diff_report.json`
- `diff_guard_report.json`
- `static_validation_report.json`
- `physics_guard_report.json`

The source is the real Stage 1.6A exported sanity-base INP. The candidate changes only:

```text
inst_plate.set-body-1, BF, 1e+10
```

to:

```text
inst_plate.set-body-1, BF, 2e+10
```

The original source INP is copied into the evidence directory and remains unchanged. StaticValidator, DiffGuard, and PhysicsGuard must all pass before this candidate can be considered ready for later human-reviewed solver or queue workflows.

## Stage 3.9C Equivalent Real ODB Intake

Stage 3.9C writes equivalent real ODB intake, metrics, and report artifacts under:

```text
runs\stage3_9c_equivalent_real_odb_intake_metrics_report\
```

This stage uses an existing manually completed, evidence-equivalent 2x ODB as the real sanity-base-derived candidate output. This is not a new solver run. This is not a new queue job. The ODB is accepted only because Stage 3.9B established traceability and equivalence.

Required artifacts include:

- `equivalent_odb_intake_request.json`
- `equivalent_odb_intake_result.json`
- `equivalent_odb_intake_summary.json`
- `equivalent_odb_intake_summary.md`
- `equivalent_odb_metrics_request.json`
- `equivalent_odb_metrics_result.json`
- `equivalent_odb_metrics_summary.json`
- `equivalent_odb_metrics_summary.md`
- `equivalent_odb_report.json`
- `equivalent_odb_report.md`
- `stage3_9c_equivalent_real_odb_smoke_summary.json`
- `stage3_9c_equivalent_real_odb_smoke_summary.md`

Before ODB intake, Stage 3.9C verifies that the Stage 3.9B candidate hash still matches, the source has `1e+10`, the candidate has `2e+10`, changed lines are exactly one, unrelated changes are zero, StaticValidator/DiffGuard/PhysicsGuard passed, the equivalent ODB exists, no sibling lock exists, and Stage 3.9B equivalence evidence is `YES`. Metrics are extracted only through the existing gated ODB metrics extractor.

## Stage 4.0 Controlled Solver Automation

Controlled solver run artifacts live under:

```text
runs\stage4_0_controlled_solver_automation\run_<timestamp>\
```

Required artifacts include:

- `solver_candidate_manifest.json`
- `solver_preflight_request.json`
- `solver_preflight_result.json`
- `solver_command_preview.txt`
- `solver_command_preview.json`
- `solver_approval_request.json`
- `approvals\solver_run_approval_token.json`
- `solver_run_request.json`
- `solver_run_result.json`
- `solver_monitor_result.json`
- `solver_output_intake_result.json`
- `solver_metrics_result.json`
- `solver_report.json`
- `solver_report.md`
- `stage4_0_controlled_solver_automation_summary.json`
- `stage4_0_controlled_solver_automation_summary.md`

Stage 4.0 only accepts a validated sanity-base-derived candidate INP. The preflight gate checks traceability, source and candidate hashes, exact allowed patch operation, zero unrelated changes, StaticValidator, DiffGuard, PhysicsGuard, job-name safety, CPU limit, and dedicated run-directory state. Solver launch requires `approvals\solver_run_approval_token.json`, created with the exact phrase `I_APPROVE_ABQPILOT_CONTROLLED_ABAQUS_SOLVER_RUN`. The token binds the candidate hash, source hash, command preview hash, expected ODB, run directory, guard results, and CPU count.

The runner is narrow: it invokes only the approved Abaqus executable with the fixed command shape for a single job, does not use `shell=True`, does not accept arbitrary extra flags, does not launch QueueRunner, does not run abqjobpilot GUI, and gives LLMs no execution authority. Monitoring reads `.lck`, `.sta`, `.msg`, `.dat`, `.log`, and `.odb` file state without opening ODB files. Completed ODB output is routed through the existing intake and gated metrics/report path.

Stage 4.1 planned Abaqus job/ODB failure diagnosis uses `docs\diagnostics\ABQPILOT_ABAQUS_JOB_ODB_FAILURE_DIAGNOSIS_TAXONOMY.md` as the design reference for job failure mode classification, completion evidence, partial ODB handling, and ODB acceptability gates.

Stage 4.1 writes diagnosis artifacts into the diagnosed job directory:

- `job_odb_diagnosis_request.json`
- `job_odb_diagnosis_result.json`
- `job_odb_diagnosis_summary.md`

The diagnosis module reads text logs/status files and ODB/lock metadata only. It never opens an ODB. `JOB_COMPLETED_ODB_ACCEPTABLE` is the only diagnosis status that allows solver-output intake for metrics extraction; ODB files produced by failed or incomplete jobs are treated as partial evidence and remain blocked.

Stage 4.1B can create the same diagnosis artifacts from abqjobpilot execution records. In that mode, abqjobpilot remains the job lifecycle and path authority, and AbqPilot writes its own diagnosis artifacts under `runs\abqjobpilot_diagnoses\<job_id>\` rather than mutating `runtime\queue.json`, `runtime\live_status.json`, or `runtime\reports\*.json`.

## Stage 4.2 Solver Failure Repair Proposal

Solver failure repair proposal artifacts live under:

```text
<solver_run_dir>\solver_failure_repair_proposal\
```

Required artifacts include:

- `solver_failure_repair_context.json`
- `solver_failure_repair_proposal.json`
- `solver_failure_repair_validation.json`
- `solver_failure_repair_summary.md`

Stage 4.2 consumes Stage 4.1 diagnosis evidence and produces a deterministic proposal only. It may recommend later guarded solver-control patch preview types for convergence failures, but it does not apply repairs, mutate INP files, open ODB files, enqueue jobs, run Abaqus, or use LLM execution authority.

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
