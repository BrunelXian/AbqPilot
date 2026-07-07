# Controlled Solver Demo Smoke Run

Stage 5.3A is the first real controlled Abaqus invocation stage.

It is limited to the dedicated task `runs/tasks/stage5_3a_controlled_solver_demo_smoke/`. This stage may create `solver_request.json` only under `artifacts/solver_requests/` in that task, and it may call `D:\ABAQUS2024\Commands\abq2024.bat` only once for the copied demo INP input.

The selected INP is copied into the Stage 5.3A task as `artifacts/solver_inputs/demo_solver_smoke.inp`. The source INP and source CAE remain untouched.

Stage 5.3A does not open ODB, does not import ODB APIs, does not extract metrics, does not approve metrics, does not approve final evidence, does not freeze verdict, and does not mutate `TASK_FINAL_EVIDENCE_LEDGER.md`. ODB and metrics preview are deferred to Stage 5.3B.

The CLI command is fixed-scope only:

```powershell
python -m abqpilot.cli run-controlled-solver-demo-smoke
```

It does not accept arbitrary task IDs, arbitrary INP paths, or arbitrary command strings.


## Stage 5.3A-v2 Retry With Workspace Guard

Stage 5.3A-v2 retries the controlled solver demo smoke run after Stage 5.3A-R workspace remediation. It uses only `runs/tasks/stage5_3a_v2_controlled_solver_demo_smoke/` and may create exactly one active `solver_request.json` under `artifacts/solver_requests/` in that task.

This is the first controlled Abaqus invocation corridor after workspace guard hardening. The runner uses the fixed command `D:\ABAQUS2024\Commands\abq2024.bat` with an argument list, `shell=False`, `cpus=4`, and job name `stage5_3a_v2_demo_solver_smoke`.

Stage 5.3A-v2 does not open ODB, import ODB APIs, call `session.openOdb`, extract metrics, write metrics.json, approve metrics, approve final evidence, freeze verdict, launch QueueRunner, mutate queue/runtime/status files, or create a generic Run Solver callback. Stage 5.3B remains responsible for any future ODB/metrics preview.

Metrics remain disabled in Stage 5.3A-v2; no metrics.json is written and no metric is approved.
