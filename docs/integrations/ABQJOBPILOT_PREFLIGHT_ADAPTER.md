# abqjobpilot Preflight and Dry-Run Adapter

Stage 2.3 adds a safe AbqPilot adapter for the public abqjobpilot API:

```python
from abqjobpilot.api import AbqJobPilotClient, JobRequest
```

The adapter uses `AbqJobPilotClient.preflight()` for preview, `AbqJobPilotClient.enqueue(request, dry_run=True)` for dry-run enqueue verification, and in Stage 2.6 may call `AbqJobPilotClient.enqueue(request, dry_run=False)` only after all approval and queue-only gates pass. Stage 2.7 calls only `AbqJobPilotClient.status()` and `AbqJobPilotClient.locate_outputs()` for read-only monitoring. It does not submit Abaqus, does not launch QueueRunner, does not open ODB files, and does not import abqjobpilot GUI modules.

Stage 2.3A uses abqjobpilot as an importable public API package for preflight only. The abqjobpilot GUI does not need to be opened.

## Local Project Root Discovery

For local development, configure:

```json
{
  "abqjobpilot": {
    "project_root": "D:\\Projects\\abqjobpilot_dev",
    "api_import_mode": "local_project_root",
    "preflight_enabled": true
  }
}
```

The adapter verifies that `project_root/abqjobpilot/api` exists, temporarily adds `project_root` to `sys.path`, and imports only `abqjobpilot.api`. It does not run `run_gui.py`, launch a GUI, start QueueRunner, or mutate runtime queue/status files.

## Stage 2.4 Dry-Run Enqueue Gate

Stage 2.4 calls abqjobpilot public enqueue API only with `dry_run=True`. It must not mutate runtime queue files or submit Abaqus jobs.

Before dry-run enqueue, AbqPilot rejects any request unless:

```json
{
  "submission_mode": "preview_only",
  "allow_solver_submit": false
}
```

The adapter snapshots these abqjobpilot runtime paths before and after the dry-run call:

- `runtime/queue.json`
- `runtime/live_status.json`
- `runtime/reports`

If existence, size, or modified time changes, the result is marked `ABQJOBPILOT_RUNTIME_MUTATION_DETECTED`.

## Stage 2.5 Human Approval Gate

Stage 2.5 does not enqueue. It creates `jobpilot_enqueue_approval_request.json` and validates `approvals/jobpilot_enqueue_approval_token.json` if a human created one with the exact phrase:

```text
I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK
```

The token is hash-bound to:

- candidate INP
- abqjobpilot job request
- preflight result
- dry-run enqueue result

Expired tokens, hash mismatches, unsafe dry-run conditions, or changed request conditions are rejected. Stage 2.6 may use a valid token to permit controlled real enqueue only when the queue-only guard also passes.

## Stage 2.6 Controlled Real Queue Enqueue

Stage 2.6 is queue enqueue only. It is disabled by default and requires `--allow-real-jobpilot-enqueue` or explicit config enablement. A valid approval token is still mandatory.

Before calling `enqueue(..., dry_run=False)`, AbqPilot verifies:

- preflight status is `PREVIEW_READY`
- dry-run enqueue status is `DRY_RUN_READY`
- dry-run runtime mutation was false
- authorization status is `APPROVAL_TOKEN_VALID`
- all approval-token hashes match current evidence
- `allow_solver_submit=false`
- `submission_mode=preview_only` or `enqueue_only`
- queue-only behavior is explicitly proven

The Stage 2.6 runtime guard allows only `runtime/queue.json` to change. Changes to `runtime/live_status.json`, `runtime/reports`, or solver output files are marked `REAL_ENQUEUE_RUNTIME_MUTATION_UNSAFE`.

## Stage 2.7 Status Poll and Output Discovery

Stage 2.7 is read-only. It calls:

```python
client.status(job_id="...")
client.locate_outputs(job_id="...")
```

It never calls enqueue, QueueRunner, Abaqus, GUI modules, subprocess launchers, or ODB-opening APIs.

Normalized status values:

- `JOB_QUEUED`
- `JOB_RUNNING`
- `JOB_COMPLETED`
- `JOB_FAILED`
- `JOB_LOCKED`
- `JOB_ODB_MISSING`
- `JOB_OUTPUTS_READY`
- `JOB_UNKNOWN`
- `ABQJOBPILOT_UNAVAILABLE`

`JOB_OUTPUTS_READY` is reported only when the public output locator confirms the expected ODB exists. The ODB is not opened.

## Stage 2.8 Completed Job Intake

Stage 2.8 consumes the status-poll evidence without adding execution authority. `continue-from-job-output` accepts `JOB_OUTPUTS_READY` or a manually supplied unlocked `.odb` path and records whether continuation into the existing gated solver-intake and ODB-metrics path is allowed.

It never starts QueueRunner, never submits Abaqus, and never opens an ODB.

## Stage 3 GUI and Reporting

The Stage 3 GUI alpha reads the same task workspace artifacts. It does not import abqjobpilot GUI modules and does not call `run_gui.py`. Its status-poll actions call AbqPilot pipeline functions, which in turn call only the public read-only abqjobpilot status/output APIs.

Run reports and alpha freeze reports summarize the adapter evidence, queue-only proof, status poll results, and safety boundary without adding new runtime authority.

## Generated Artifacts

The pipeline step `03_abqjobpilot_preflight` writes:

- `abqjobpilot_job_request.json`
- `abqjobpilot_preflight_result.json`
- `abqjobpilot_command_preview.md`

The pipeline step `04_abqjobpilot_dry_run_enqueue` writes:

- `abqjobpilot_dry_run_request.json`
- `abqjobpilot_dry_run_enqueue_result.json`
- `abqjobpilot_dry_run_safety_report.json`
- `abqjobpilot_dry_run_preview.md`

The pipeline step `06_abqjobpilot_real_enqueue` writes:

- `abqjobpilot_real_enqueue_request.json`
- `abqjobpilot_real_enqueue_result.json`
- `abqjobpilot_real_enqueue_safety_report.json`
- `abqjobpilot_real_enqueue_preview.md`

The pipeline step `07_abqjobpilot_status_poll` writes:

- `abqjobpilot_status_request.json`
- `abqjobpilot_status_result.json`
- `abqjobpilot_output_locator_result.json`
- `abqjobpilot_status_summary.json`
- `abqjobpilot_status_summary.md`

The request always contains:

```json
{
  "submission_mode": "preview_only",
  "allow_solver_submit": false
}
```

## Unavailable API

If `abqjobpilot.api` cannot be imported, the adapter returns `ABQJOBPILOT_UNAVAILABLE`, writes safe artifacts where possible, and the deterministic pipeline may continue toward solver-output intake if existing manual outputs are already present.

## Boundary

Manual solver boundary remains intact. Stage 2.6 controlled enqueue does not run the solver; Stage 2.7 only reads status and output metadata. Solver execution remains a separate future/manual action.
