# AbqPilot CLI Usage

Stage 2.0 adds a deterministic command-line task runner for the existing staged tools. It is a software assembly layer only.

Use the project Python:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli status
```

## Stage 5.0A ACOM Handoff Commands

ACOM is AbqPilot Codex Operator Mode. It is the default practical Codex-assisted mode. These commands generate and validate bounded handoff artifacts only; AbqPilot does not call Codex CLI.

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli generate-codex-handoff --task-id stage5_0a_acom_smoke --task-type model_condition_guard_review --title "ACOM MCPGuard review smoke" --objective "Generate a bounded Codex handoff package for reviewing MCPGuard artifacts without running solver or mutating model files."
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli validate-codex-handoff --handoff-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0a_acom_smoke\codex_handoff
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli intake-codex-result --handoff-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0a_acom_smoke\codex_handoff --result-json D:\Projects\AbqPilot-v2\runs\tasks\stage5_0a_acom_smoke\codex_result\structured_result.json
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-codex-handoff --handoff-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0a_acom_smoke\codex_handoff
```

NARM is Native Agent Runtime Mode. It is optional and must satisfy the same evidence and safety contracts. Codex summaries are not final evidence in ACOM; AbqPilot validates returned artifacts deterministically. MCPGuard is required when model conditions or INP patches may be affected.

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

Stage 3.9 patched job status and completed-output intake:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli poll-patch-queue --workflow-dir D:\Projects\AbqPilot-v2\runs\stage3_7_heat_flux_fixture_task\patch_queue_workflows\queue_20260630_224336_749584
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli intake-patched-job-output --workflow-dir D:\Projects\AbqPilot-v2\runs\stage3_7_heat_flux_fixture_task\patch_queue_workflows\queue_20260630_224336_749584
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli intake-patched-job-output --workflow-dir <patch_queue_workflow_dir> --manual-odb-path <existing_unlocked_patched.odb>
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli extract-patched-job-metrics --workflow-dir <patch_queue_workflow_dir>
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-patched-job --workflow-dir <patch_queue_workflow_dir>
```

`poll-patch-queue` remains read-only and normalizes patch queue status to `JOB_QUEUED`, `JOB_RUNNING`, `JOB_OUTPUTS_READY`, `JOB_ODB_MISSING`, `JOB_FAILED`, `JOB_LOCKED`, `JOB_UNKNOWN`, or `ABQJOBPILOT_UNAVAILABLE`. `intake-patched-job-output` accepts only existing unlocked `.odb` files and records evidence without opening ODB. `extract-patched-job-metrics` is blocked until the intake gate accepts an output and then uses only the existing gated metrics extractor. `report-patched-job` writes a safe report even when the job is still queued or metrics/reference data are unavailable.

Stage 3.9B real sanity-base candidate recovery:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli recover-sanity-base-patch-candidate
```

This command reclassifies the Stage 3.7/3.8/3.8A tiny patch candidate as workflow-only evidence, copies the real Stage 1.6A sanity-base exported INP into `runs\stage3_9b_real_sanity_base_patch_candidate\source_sanity_base_export.inp`, writes `candidate_sanity_base_power_x2.inp`, and changes only `inst_plate.set-body-1, BF, 1e+10` to `inst_plate.set-body-1, BF, 2e+10`. It runs StaticValidator, DiffGuard, and PhysicsGuard, writes classification and summary artifacts, and does not submit a solver, enqueue a job, launch QueueRunner, or open ODB.

Stage 3.9C equivalent real ODB intake, metrics, and report:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-stage3-9c-equivalent-odb
```

Stage 3.9C uses an existing manually completed, evidence-equivalent 2x ODB as the real sanity-base-derived candidate output. This is not a new solver run. This is not a new queue job. The ODB is accepted only because Stage 3.9B established traceability and equivalence. Metrics are extracted only through the existing gated ODB metrics extractor, and the report compares the equivalent 2x result against the existing 1x baseline when both metrics are available.

Stage 4.0 controlled single-job Abaqus solver automation:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli prepare-solver-run --candidate-inp D:\Projects\AbqPilot-v2\runs\stage3_9b_real_sanity_base_patch_candidate\candidate_sanity_base_power_x2.inp --source-inp D:\Projects\AbqPilot-v2\runs\stage3_9b_real_sanity_base_patch_candidate\source_sanity_base_export.inp --evidence-dir D:\Projects\AbqPilot-v2\runs\stage3_9b_real_sanity_base_patch_candidate --cpus 14
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli approve-solver-run --solver-run-dir <solver_run_dir> --approved-by human --approval-phrase I_APPROVE_ABQPILOT_CONTROLLED_ABAQUS_SOLVER_RUN --expires-hours 24
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-solver-approved --solver-run-dir <solver_run_dir> --approval-token <solver_run_dir>\approvals\solver_run_approval_token.json
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli monitor-solver-run --solver-run-dir <solver_run_dir>
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli intake-solver-run-output --solver-run-dir <solver_run_dir>
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-solver-run --solver-run-dir <solver_run_dir>
```

Stage 4.0 accepts only validated sanity-base-derived candidate INPs with StaticValidator, DiffGuard, and PhysicsGuard all passing and zero unrelated changes. The command preview is fixed to the approved Abaqus executable and exact argument shape, with `cpus` capped at 14, no arbitrary extra flags, and no `shell=True`. Solver launch requires the exact approval phrase and a token bound to the candidate hash, source hash, command preview, run directory, expected ODB, guard results, and CPU count. It does not launch QueueRunner, does not run abqjobpilot GUI, does not let an LLM execute actions, and still uses the existing gated ODB metrics extractor after a completed ODB is accepted.

Stage 4.1 planned Abaqus job/ODB failure diagnosis will use the taxonomy at `docs\diagnostics\ABQPILOT_ABAQUS_JOB_ODB_FAILURE_DIAGNOSIS_TAXONOMY.md` as its design reference for job failure modes, completion evidence, partial ODB handling, and ODB validity classification.

Stage 4.1 deterministic job/ODB diagnosis:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli diagnose-job-output --job-dir <solver_run_dir> --job-name <job_name>
```

`diagnose-job-output` reads `.sta`, `.dat`, `.msg`, `.log`, `.com`, `.prt`, `.lck`, and ODB file metadata only. It does not open ODB files. ODB existence alone is not sufficient for metrics intake; `JOB_COMPLETED_ODB_ACCEPTABLE` requires an existing ODB, no active lock, completion evidence, and no terminal failure evidence. Failed or partial ODBs are blocked from metrics extraction. `monitor-solver-run` and `intake-solver-run-output` use this diagnosis result.

Stage 4.2 deterministic solver-failure repair proposal:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli propose-solver-repair --solver-run-dir <solver_run_dir>
```

`propose-solver-repair` consumes `job_odb_diagnosis_result.json` and writes a schema-bound proposal under `<solver_run_dir>\solver_failure_repair_proposal\`. For convergence failures such as too many attempts, it may recommend solver-control repair types such as `step_increment_relaxation`, `minimum_increment_reduction`, or load-ramp smoothing for later guarded preview. It does not apply the repair, mutate INP, open ODB, enqueue jobs, run Abaqus, or use LLM execution authority.

Stage 4.1B abqjobpilot-backed diagnosis:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli list-abqjobpilot-records --abqjobpilot-runtime-dir D:\Projects\abqjobpilot_dev\runtime --max-results 20
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli diagnose-job-output --abqjobpilot-report <report_json>
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli diagnose-job-output --abqjobpilot-job-id <job_id> --abqjobpilot-runtime-dir D:\Projects\abqjobpilot_dev\runtime
```

Stage 4.1B treats abqjobpilot as the execution-record, lifecycle, and file-path authority. AbqPilot reads abqjobpilot records and referenced text logs read-only, inspects ODB existence/size/timestamps only, and then applies the deterministic Stage 4.1 ODB acceptability taxonomy. The command does not mutate `queue.json`, `live_status.json`, or `runtime\reports`, and ODB existence alone is never accepted as proof of successful completion.

Stage 4.3 guarded DFLUX deactivation preview:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli preview-dflux-deactivation-patch --source-inp <inp_path> --output-dir D:\Projects\AbqPilot-v2\runs\stage4_3_guarded_dflux_deactivation_patch_preview --scan-step step_scan_00 --cooling-step Step_cool_00 --load-name load_body_hflux_00
```

This command writes a copied preview INP and inserts explicit `*Dflux, OP=NEW` reset evidence in `Step_cool_00`. It runs StaticValidator, DFLUX lifecycle diff validation, PhysicsGuard, and a DFLUX lifecycle validator. It does not mutate the source INP, run solver, enqueue jobs, launch QueueRunner, open ODB, or apply the patch in place.

Stage 4.4 DFLUX-guarded controlled solver validation:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli prepare-dflux-guarded-solver-run --preview-inp <preview_inp> --validation-json <dflux_lifecycle_validation.json> --output-root D:\Projects\AbqPilot-v2\runs\stage4_4_dflux_deactivated_controlled_solver_validation
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli approve-dflux-guarded-solver-run --solver-run-dir <solver_run_dir> --approval-phrase I_APPROVE_ABQPILOT_DFLUX_DEACTIVATED_CONTROLLED_SOLVER_RUN
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-dflux-guarded-solver-approved --solver-run-dir <solver_run_dir>
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli monitor-dflux-guarded-solver-run --solver-run-dir <solver_run_dir>
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli intake-dflux-guarded-solver-output --solver-run-dir <solver_run_dir>
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-dflux-guarded-solver-run --solver-run-dir <solver_run_dir>
```

No INP without a passing Stage 4.3 DFLUX lifecycle validation artifact may enter this solver path. The prepare command copies the preview INP to a new Stage 4.4 run directory, writes a fixed command preview, and stops until the DFLUX-specific approval token is created. ODB metrics remain blocked unless Stage 4.1B diagnosis returns `JOB_COMPLETED_ODB_ACCEPTABLE`.

Stage 4.5 Model Condition Preservation Guard:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli run-model-condition-guard --source-jnl <jnl> --source-inp <source_exported_inp> --candidate-inp <candidate_inp> --solver-inp <solver_inp> --target-change body_heat_flux_magnitude:load_body_hflux_00:step_scan_00:1e+10:2e+10
```

MCPGuard checks that original CAE/JNL model-condition intent is preserved in exported, patched, and solver-run INPs. Stage 4.5 implements `MCPGuard.load_lifecycle.body_heat_flux_dflux_bf` and schema hooks for boundary lifecycle, interaction lifecycle, amplitudes, step procedure, output requests, reference integrity, and target patch isolation. The command is read-only and does not run Abaqus or open ODB files.

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
- Solver execution is unavailable through the ordinary pipeline and is only available in Stage 4.0 through the solver-specific approval-token gate for one validated sanity-base-derived candidate.
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
- Stage 3.9 patched-job intake reads status/output evidence only and blocks metrics until an existing unlocked ODB is accepted.
- Stage 3.9B real candidate recovery uses the actual sanity-base export, not the toy fixture, and changes only the allowed BF heat-flux magnitude.
- Stage 3.9C equivalent ODB intake accepts the existing manually completed 2x ODB only because Stage 3.9B traceability/equivalence evidence is present.
- Stage 4.0 controlled solver automation supports one approved Abaqus job with a fixed command preview, no arbitrary flags, no QueueRunner, no LLM execution authority, and no uncontrolled ODB opening.
- Stage 4.1 job/ODB diagnosis blocks partial ODBs and requires completion evidence before metrics extraction.
- Stage 4.2 solver-failure repair proposal is advisory and deterministic; it does not apply repairs or run solvers.
- ODB read is gated and metrics-only.
- CAE export is allowed only through the existing writeInput gate.
- GUI and reports consume CLI/task result JSON instead of reimplementing simulation-critical workflows.
## Pipeline Protocol Commands

```powershell
python -m abqpilot.cli list-pipeline-agents
python -m abqpilot.cli scaffold-pipeline-task --task-id <task_id>
python -m abqpilot.cli validate-pipeline-protocol --task-dir <task_dir>
python -m abqpilot.cli report-pipeline-protocol --task-dir <task_dir>
```

These commands list bounded pipeline stations, create a flat RUN/HANDOFF/GATE scaffold, validate YAML frontmatter and required files, and write a protocol report. They do not schedule agents, call Codex CLI, run solvers, enqueue jobs, launch QueueRunner, or open ODB files.

## ACOM Template Commands

```powershell
python -m abqpilot.cli list-acom-templates
python -m abqpilot.cli describe-acom-template --template-id mcpguard_review
python -m abqpilot.cli generate-codex-handoff --task-id <task_id> --template-id mcpguard_review
python -m abqpilot.cli validate-acom-template-pack
python -m abqpilot.cli intake-codex-result --handoff-dir runs\tasks\<task_id>\codex_handoff --result-json runs\tasks\<task_id>\codex_result\structured_result.json
python -m abqpilot.cli report-acom-result-intake --task-dir runs\tasks\<task_id>
```

Template-based handoffs generate pipeline RUN/HANDOFF records plus `codex_handoff/`. Codex still runs externally and manually. AbqPilot does not call Codex CLI, and Codex summaries are not final evidence.

Stage 5.0D result intake generates pipeline RUN/HANDOFF/GATE revalidation records. `ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION` means accepted for downstream AbqPilot revalidation only, not accepted as evidence.

Stage 5.0E downstream revalidation scaffold:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli scaffold-acom-revalidation --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0d_acom_result_intake_smoke
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-acom-revalidation --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0d_acom_result_intake_smoke
```

These commands create scaffold records only. They do not run downstream agents, call Codex CLI, run solver, open ODB, or approve evidence.

Stage 5.0F non-solver revalidation executor:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli execute-non-solver-revalidation --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0f_non_solver_revalidation_smoke
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-non-solver-revalidation --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0f_non_solver_revalidation_smoke
```

Stage 5.0F executes deterministic revalidation only for DocsStatusAgent, SoftwareQAAgent, AuditAgent, EvidenceReportAgent, and PipelineSupervisor. GuardAgent, CandidateBuilderAgent, DiagnosisAgent, ExecutionAgent, and MetricsAgent are blocked. `NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR` means pending PipelineSupervisor review, not final evidence accepted.

Stage 5.0G PipelineSupervisor non-solver review:

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli supervisor-review-non-solver-revalidation --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0f_non_solver_revalidation_smoke
```

```powershell
D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe -m abqpilot.cli report-supervisor-non-solver-review --task-dir D:\Projects\AbqPilot-v2\runs\tasks\stage5_0f_non_solver_revalidation_smoke
```

Accepted review means accepted for `NON_SOLVER_EVIDENCE_LEDGER` only. It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.
