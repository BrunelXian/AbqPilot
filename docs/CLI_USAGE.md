# AbqPilot CLI Usage

Stage 2.0 adds a deterministic command-line task runner for the existing staged tools. It is a software assembly layer only.

Use the project Python:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli status
```

## Commands

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli export-cae --cae D:\Projects\AbqPilot-v2\CAE_model\sanity_base\sanity_base_v01.cae --out-dir D:\Projects\AbqPilot-v2\runs\cli_export --job-name sanity_base_v01_export
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli audit-heat-x2 --source-inp D:\Projects\AbqPilot-v2\runs\stage1_6a_cae_to_inp_export\sanity_base_v01_export.inp --out-dir D:\Projects\AbqPilot-v2\runs\cli_audit_x2 --scale 2.0
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli intake-solver --search-root D:\Projects\AbqPilot-v2\CAE_model\sanity_base --out-dir D:\Projects\AbqPilot-v2\runs\cli_solver_intake
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli extract-odb-metrics --contract D:\Projects\AbqPilot-v2\runs\stage1_7_manual_solver_output_intake\odb_metrics_extraction_contract.json --out-dir D:\Projects\AbqPilot-v2\runs\cli_odb_metrics
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli compare-metrics --metrics D:\Projects\AbqPilot-v2\runs\stage1_8_gated_odb_metrics_extraction\odb_metrics_pair.json --out-dir D:\Projects\AbqPilot-v2\runs\cli_compare
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode through-comparison
```

Stage 2.1 task workspace examples:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id demo_prepare_001
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode through-comparison --task-id demo_compare_001
```

Use `--work-root PATH` to override the configured task workspace root. Use `--stop-after STEP_NAME` to stop after a specific pipeline step, such as `02_audit_heat_x2`.

Stage 2.2 resume, skip, and rerun examples:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id demo_001
```

With explicit abqjobpilot preflight preview parameters:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id demo_001 --jobpilot-cpus 14 --jobpilot-batch sanity_base_heat_x2 --jobpilot-strategy power_x2
```

With an explicit local abqjobpilot API root:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id demo_001 --abqjobpilot-root D:\Projects\abqjobpilot_dev
```

Skip the preflight preview step:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id demo_skip_001 --skip-jobpilot-preflight
```

Skip the Stage 2.4 abqjobpilot dry-run enqueue gate:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id demo_skip_dry_001 --skip-jobpilot-dry-run-enqueue
```

Stage 2.5 approval request smoke:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id stage2_5_approval_smoke --abqjobpilot-root D:\Projects\abqjobpilot_dev
```

Create a manual approval token for a future real enqueue stage:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli approve-jobpilot-enqueue --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_5_approval_smoke --approved-by human --approval-phrase I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK --expires-hours 24
```

Stage 2.6 blocked real enqueue smoke:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id stage2_6_blocked_enqueue_smoke --abqjobpilot-root D:\Projects\abqjobpilot_dev
```

Skip the real enqueue step explicitly:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --mode prepare-only --task-id stage2_6_skip_enqueue_smoke --skip-real-jobpilot-enqueue
```

Controlled real enqueue requires a valid approval token and explicit enablement:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --task-id approved_task --resume --allow-real-jobpilot-enqueue
```

Stage 2.7 read-only abqjobpilot status poll:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --task-id stage2_6a_production_queue_only_smoke --resume --abqjobpilot-root D:\Projects\abqjobpilot_dev --poll-jobpilot-status
```

Use `--jobpilot-job-id q_...` to disambiguate a job id, or `--skip-jobpilot-status-poll` to skip the read-only poll step.

Stage 2.8 completed-job intake and continuation gate:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli continue-from-job-output --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke
```

With a manually confirmed ODB path:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli continue-from-job-output --task-dir D:\Projects\AbqPilot-v2\runs\tasks\manual_task --manual-odb-path D:\Projects\AbqPilot-v2\CAE_model\sanity_base\generated_power_x2.odb
```

This command validates existing output evidence only. It rejects missing ODBs, non-`.odb` paths, and locked ODBs. It does not open ODB files and does not run Abaqus.

Stage 2.9 deterministic evaluation and repair-plan generation:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli generate-repair-plan --task-dir D:\Projects\AbqPilot-v2\runs\tasks\completed_metrics_task
```

Or with explicit artifacts:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli generate-repair-plan --metrics D:\Projects\AbqPilot-v2\runs\stage1_8_gated_odb_metrics_extraction\odb_metrics_pair.json --comparison D:\Projects\AbqPilot-v2\runs\stage1_9_metrics_based_comparison_report\comparison_report.json --out-dir D:\Projects\AbqPilot-v2\runs\cli_repair_plan
```

The repair plan is deterministic and rule-based. It may recommend guarded future patch types, but it does not mutate INP files and does not submit solver jobs.

Stage 3.2 run report export:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli export-run-report --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke
```

Stage 3.3 alpha freeze artifact export:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli alpha-freeze --root D:\Projects\AbqPilot-v2 --test-results "pytest passed"
```

Stage 3.1 local GUI alpha:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli gui
```

Stage 3.4 GUI Beta uses standard-library `tkinter`. It loads task workspaces, renders recent tasks, module state, event stream, artifacts, workflow presets, and the current-module right panel. Dangerous execution actions are absent or disabled; there is no active path to start Abaqus, start QueueRunner, submit solver jobs, auto-repair INP, or run an LLM agent.

Export current project status files:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli export-project-status
```

Stage 3.5A optional LLM provider contract:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli llm-reason --provider mock --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke
```

Real provider test probes require explicit confirmation and send only a tiny JSON test request:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli probe-llm --provider chatanywhere --model deepseek-chat --confirm-send-test-request
```

Sending a task summary to a non-mock provider requires `--confirm-send-task-summary`. AbqPilot sends only compact sanitized JSON and never sends full INP, ODB, CAE files, full logs, or API keys.

Stage 3.5B real task-summary reasoning:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli llm-reason --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke --dry-run-input-summary
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli llm-reason --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke --provider mock
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli llm-reason --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke --provider chatanywhere --confirm-send-task-summary
```

`--dry-run-input-summary` builds the sanitized JSON and does not call any provider. `--show-sanitized-summary` may print the compact summary for inspection. Real provider output must be strict JSON and is rejected if it recommends solver submission, QueueRunner launch, direct ODB opening, direct INP editing, approval bypass, or validator bypass. Reasoning artifacts are written under `<task_dir>\llm_reasoning\`.

Stage 3.6 advisory candidate patch proposal:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli propose-patch --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke --provider mock
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli propose-patch --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke --provider chatanywhere --confirm-send-patch-context
```

`propose-patch` sends only sanitized patch context and writes artifacts under `<task_dir>\llm_patch_proposals\`. Candidate proposals are advisory only. They do not mutate INP files, do not write CAE files, do not open ODB files, do not enqueue jobs, and do not submit solver jobs.

Stage 3.7 guarded PatchBuilder application preview:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli preview-patch --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage2_6a_production_queue_only_smoke --provider-source llm
```

`preview-patch` converts a validated candidate patch proposal into a deterministic candidate INP preview only for supported patch types. Stage 3.7 supports `heat_flux_magnitude_adjustment`; unsupported allowed types are blocked. The original INP is never overwritten. StaticValidator, DiffGuard, and PhysicsGuard run before a preview is considered ready. No solver is submitted and no abqjobpilot job is enqueued.

Stage 3.8 guarded patch-to-queue workflow:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli queue-patch-preview --task-dir D:\Projects\AbqPilot-v2\runs\stage3_7_heat_flux_fixture_task --patch-preview-dir D:\Projects\AbqPilot-v2\runs\stage3_7_heat_flux_fixture_task\patch_previews\preview_20260630_183350_319742 --mode preflight-only
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli queue-patch-preview --task-dir D:\Projects\AbqPilot-v2\runs\stage3_7_heat_flux_fixture_task --patch-preview-dir D:\Projects\AbqPilot-v2\runs\stage3_7_heat_flux_fixture_task\patch_previews\preview_20260630_183350_319742 --mode dry-run-enqueue
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli approve-patch-queue --workflow-dir <patch_queue_workflow_dir> --approved-by human --approval-phrase I_APPROVE_ABQPILOT_PATCH_CANDIDATE_QUEUE_ONLY_ENQUEUE --expires-hours 24
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli queue-patch-preview --workflow-dir <patch_queue_workflow_dir> --mode real-queue-only --approval-token <token_path>
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli poll-patch-queue --workflow-dir <patch_queue_workflow_dir>
```

`queue-patch-preview` accepts only Stage 3.7 previews with `PATCH_PREVIEW_READY`, `PASS` from StaticValidator, DiffGuard, and PhysicsGuard, zero unrelated changes, an existing candidate INP, and `requires_human_review=true`. Preflight-only mode does not run dry-run enqueue. Dry-run mode creates a candidate-specific approval request but does not real enqueue. Real queue-only mode requires a patch candidate token bound to the candidate INP hash, preview directory, job request, preflight result, dry-run result, patch type, and changed-line counts. The workflow never submits a solver, never launches QueueRunner, never opens ODB, and gives the LLM no execution authority.

Stage 3.8A production patch queue smoke confirmed a controlled real queue-only enqueue for a validated heat-flux patch candidate. The result showed `queue_only=True`, `queue_file_mutated=True`, `solver_started=False`, `runner_started=False`, `gui_required=False`, and `forbidden_mutations_detected=False`. Runtime snapshots showed only `D:\Projects\abqjobpilot_dev\runtime\queue.json` changed; `live_status.json`, `runtime\reports`, and solver output files remained unchanged. Status polling returned `JOB_QUEUED` without opening ODB.

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --task-id demo_001 --resume
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-sanity-demo --config configs\sanity_demo_task.json --task-id demo_001 --force-step 02_audit_heat_x2
```

`--skip-completed` is on by default. Use `--no-skip-completed` only when intentionally rerunning completed steps; existing step directories are backed up before replacement.

The CLI exposes no solver-submit option. `03_abqjobpilot_preflight` imports only `abqjobpilot.api` and generates preview artifacts. `04_abqjobpilot_dry_run_enqueue` calls the public enqueue API only with `dry_run=True`, writes dry-run artifacts, and checks that runtime queue/status files were not mutated. `05_jobpilot_enqueue_authorization` creates an approval request and validates a token if one already exists. `approve-jobpilot-enqueue` creates the token only when the exact approval phrase is supplied. `06_abqjobpilot_real_enqueue` is disabled by default and can only call `enqueue(..., dry_run=False)` after all approval, hash, config, and queue-only proof gates pass. `07_abqjobpilot_status_poll` calls only `status()` and `locate_outputs()` and never opens ODB files. `continue-from-job-output` only validates existing output evidence. `run_gui.py` is not used.

Every command prints a human-readable summary. Add `--result-json PATH` to write the GUI-ready result envelope.

## Safety Principles

- The CLI does not call an LLM.
- The CLI does not submit solver jobs.
- Solver execution remains manual or a future approved backend.
- abqjobpilot dry-run enqueue is not real queue mutation and does not submit Abaqus.
- Stage 2.6 is queue enqueue only; solver execution remains separate.
- Stage 2.7 status polling and output discovery are read-only.
- Stage 2.8 completed-job intake is evidence validation only.
- Stage 2.9 repair planning is deterministic and does not mutate INP files.
- Stage 3.1 GUI alpha uses local task artifacts and safe internal calls only.
- Stage 3.4 GUI Beta routes safe actions through `GuiActionController`.
- Stage 3.5A LLM provider contract is optional, schema-bound, and disabled unless explicitly configured.
- Stage 3.5B real LLM reasoning is read-only advisory, requires explicit confirmation, sends only sanitized task summaries, and validates strict JSON output.
- Stage 3.6 LLM patch proposal is advisory only, requires confirmation for real providers, and cannot apply patches.
- Stage 3.7 PatchBuilder preview is deterministic, validator-gated, and cannot submit/enqueue/run solvers.
- Stage 3.8 Patch-to-queue reuses the existing guarded JobPilot adapter and requires candidate-specific approval before real queue-only enqueue.
- ODB read is gated and metrics-only.
- CAE export is allowed only through the existing writeInput gate.
- GUI and reports consume CLI/task result JSON instead of reimplementing simulation-critical workflows.
